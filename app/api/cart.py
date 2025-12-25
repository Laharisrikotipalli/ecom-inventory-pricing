from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import get_db
from ..models import Cart, CartItem, Variant
from ..schemas import CartCreateResponse, AddItemRequest
from ..services.pricing import calculate_price, UserContext

RESERVATION_MINUTES = 15

router = APIRouter()

@router.post("", response_model=CartCreateResponse)
def create_cart(db: Session = Depends(get_db)):
    cart = Cart()
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return CartCreateResponse(cart_id=cart.id)

@router.post("/{cart_id}/items", response_model=dict)
def add_or_update_item(
    cart_id: int,
    req: AddItemRequest,
    db: Session = Depends(get_db),
):
    if req.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    cart = db.get(Cart, cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    try:
        variant = (
            db.execute(
                select(Variant)
                .where(Variant.id == req.variant_id)
                .with_for_update()
            )
            .scalars()
            .one_or_none()
        )
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")

        existing = (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart_id, CartItem.variant_id == req.variant_id)
            .one_or_none()
        )

        available = variant.stock_quantity - variant.reserved_quantity
        delta = req.quantity if not existing else req.quantity - existing.quantity
        if available < delta:
            raise HTTPException(status_code=400, detail="Insufficient stock")

        price = calculate_price(
            db=db,
            variant=variant,
            quantity=req.quantity,
            user_ctx=UserContext(tier=req.user_tier),
            promo_code=req.promo_code,
        )

        reserved_until = datetime.utcnow() + timedelta(minutes=RESERVATION_MINUTES)

        if existing:
            existing.quantity = req.quantity
            existing.reserved_until = reserved_until
            existing.unit_price_snapshot = Decimal(price.final_unit_price)
            existing.discount_snapshot = Decimal(price.total_discount)
            existing.final_price_snapshot = Decimal(price.total_after_discount)
            variant.reserved_quantity += delta
        else:
            item = CartItem(
                cart_id=cart_id,
                variant_id=req.variant_id,
                quantity=req.quantity,
                reserved_until=reserved_until,
                unit_price_snapshot=Decimal(price.final_unit_price),
                discount_snapshot=Decimal(price.total_discount),
                final_price_snapshot=Decimal(price.total_after_discount),
            )
            db.add(item)
            variant.reserved_quantity += req.quantity

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"cart_id": cart_id}
