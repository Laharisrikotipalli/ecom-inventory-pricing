from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import List, Optional

class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    base_price: Decimal
    category_id: int | None = None

class VariantCreate(BaseModel):
    product_id: int
    sku: str
    attributes: dict | None = None
    stock_quantity: int

class CartCreateResponse(BaseModel):
    cart_id: int

class AddItemRequest(BaseModel):
    variant_id: int
    quantity: int
    user_tier: str | None = None
    promo_code: str | None = None

class CheckoutRequest(BaseModel):
    cart_id: int
    user_id: int | None = None

class PriceBreakdownResponse(BaseModel):
    base_price: Decimal
    final_unit_price: Decimal
    quantity: int
    total_before_discount: Decimal
    total_discount: Decimal
    total_after_discount: Decimal
    applied_rules: list[dict]
