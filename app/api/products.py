from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Product
from ..schemas import ProductCreate

router = APIRouter()

@router.post("", response_model=dict)
def create_product(body: ProductCreate, db: Session = Depends(get_db)):
    product = Product(
        name=body.name,
        description=body.description,
        base_price=body.base_price,
        category_id=body.category_id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"id": product.id}

@router.get("", response_model=list[dict])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "base_price": str(p.base_price),
        }
        for p in products
    ]
