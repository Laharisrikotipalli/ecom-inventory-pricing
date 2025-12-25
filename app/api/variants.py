from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Variant, Product
from ..schemas import VariantCreate

router = APIRouter()

@router.post("", response_model=dict)
def create_variant(body: VariantCreate, db: Session = Depends(get_db)):
    product = db.get(Product, body.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    variant = Variant(
        product_id=body.product_id,
        sku=body.sku,
        attributes=body.attributes,
        stock_quantity=body.stock_quantity,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return {"id": variant.id}
