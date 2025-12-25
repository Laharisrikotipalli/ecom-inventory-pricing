from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime,
    Numeric, Boolean, JSON, Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .db import Base
import enum

class ProductStatus(str, enum.Enum):
    active = "active"
    archived = "archived"

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    parent = relationship("Category", remote_side=[id])

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(Enum(ProductStatus), default=ProductStatus.active, nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category")
    variants = relationship("Variant", back_populates="product")

class Variant(Base):
    __tablename__ = "variants"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String, nullable=False, unique=True, index=True)
    attributes = Column(JSON)
    stock_quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    product = relationship("Product", back_populates="variants")

class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("CartItem", back_populates="cart")

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    reserved_until = Column(DateTime, nullable=False)
    unit_price_snapshot = Column(Numeric(10, 2), nullable=False)
    discount_snapshot = Column(Numeric(10, 2), nullable=False)
    final_price_snapshot = Column(Numeric(10, 2), nullable=False)

    cart = relationship("Cart", back_populates="items")
    variant = relationship("Variant")

    __table_args__ = (
      UniqueConstraint("cart_id", "variant_id", name="uq_cart_variant"),
    )

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, default="confirmed", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), nullable=False)
    final_price = Column(Numeric(10, 2), nullable=False)
    order = relationship("Order", back_populates="items")
    variant = relationship("Variant")

class PricingRuleType(str, enum.Enum):
    bulk_quantity = "bulk_quantity"
    seasonal_percentage = "seasonal_percentage"
    user_tier_percentage = "user_tier_percentage"
    promo_code_percentage = "promo_code_percentage"

class DiscountType(str, enum.Enum):
    percent = "percent"
    absolute = "absolute"

class PricingRule(Base):
    __tablename__ = "pricing_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(Enum(PricingRuleType), nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    conditions = relationship("PricingRuleCondition", back_populates="rule")
    actions = relationship("PricingRuleAction", back_populates="rule")

class PricingRuleCondition(Base):
    __tablename__ = "pricing_rule_conditions"
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("pricing_rules.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    variant_id = Column(Integer, ForeignKey("variants.id"))
    min_quantity = Column(Integer)
    user_tier = Column(String)
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    promo_code = Column(String)
    rule = relationship("PricingRule", back_populates="conditions")

class PricingRuleAction(Base):
    __tablename__ = "pricing_rule_actions"
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("pricing_rules.id"), nullable=False)
    discount_type = Column(Enum(DiscountType), nullable=False)
    discount_value = Column(Numeric(10, 2), nullable=False)
    rule = relationship("PricingRule", back_populates="actions")
