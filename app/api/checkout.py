from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..db import get_db
from ..models import Cart, CartItem, Variant, Order, OrderItem
from ..schemas import CheckoutRequest

router = APIRouter()

@router.post("", response_model=dict)
def checkout(req: CheckoutRequest, db: Session = Depends(get_db)):
    cart = db.get(Cart, req.cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    now = datetime.utcnow()

    try:
        items = (
             db.query(CartItem)
            .options(joinedload(CartItem.variant))
            .filter(CartItem.cart_id == req.cart_id)
            .all()

        )

        if not items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        order = Order(user_id=req.user_id, total_amount=Decimal("0"))
        db.add(order)
        db.flush()

        total = Decimal("0")
        for item in items:
            if item.reserved_until < now:
                raise HTTPException(status_code=400, detail="Reservation expired")

            variant = item.variant
            if variant.reserved_quantity < item.quantity:
                raise HTTPException(status_code=409, detail="Reserved mismatch")
            if variant.stock_quantity < item.quantity:
                raise HTTPException(status_code=409, detail="Insufficient stock")

            variant.stock_quantity -= item.quantity
            variant.reserved_quantity -= item.quantity

            total += Decimal(item.final_price_snapshot)

            db.add(
                OrderItem(
                    order_id=order.id,
                    variant_id=item.variant_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price_snapshot,
                    discount=item.discount_snapshot,
                    final_price=item.final_price_snapshot,
                )
            )

        order.total_amount = total
        db.query(CartItem).filter(CartItem.cart_id == req.cart_id).delete()
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"order_id": order.id, "total": str(order.total_amount)}
