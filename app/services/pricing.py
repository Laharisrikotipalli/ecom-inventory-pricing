from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from ..models import (
    Variant, PricingRule, PricingRuleCondition,
    PricingRuleAction, PricingRuleType, DiscountType
)

@dataclass
class UserContext:
    tier: str | None = None

@dataclass
class PriceBreakdown:
    base_price: Decimal
    final_unit_price: Decimal
    quantity: int
    total_before_discount: Decimal
    total_discount: Decimal
    total_after_discount: Decimal
    applied_rules: list[dict]

def _load_rules(
    db: Session,
    variant: Variant,
    quantity: int,
    user_ctx: UserContext,
    promo_code: str | None,
) -> list[PricingRule]:
    now = datetime.utcnow()
    q = (
        db.query(PricingRule)
        .join(PricingRuleCondition)
        .filter(PricingRule.is_active.is_(True))
    )
    q = q.filter(
        (PricingRuleCondition.product_id == None) |
        (PricingRuleCondition.product_id == variant.product_id)
    )
    q = q.filter(
        (PricingRuleCondition.variant_id == None) |
        (PricingRuleCondition.variant_id == variant.id)
    )
    q = q.filter(
        (PricingRuleCondition.min_quantity == None) |
        (PricingRuleCondition.min_quantity <= quantity)
    )
    q = q.filter(
        (PricingRuleCondition.user_tier == None) |
        (PricingRuleCondition.user_tier == user_ctx.tier)
    )
    q = q.filter(
        (PricingRuleCondition.start_at == None) |
        (PricingRuleCondition.start_at <= now)
    )
    q = q.filter(
        (PricingRuleCondition.end_at == None) |
        (PricingRuleCondition.end_at >= now)
    )
    if promo_code:
        q = q.filter(
            (PricingRuleCondition.promo_code == None) |
            (PricingRuleCondition.promo_code == promo_code)
        )
    rules = q.distinct().all()
    return sorted(rules, key=lambda r: r.priority)

def _apply_rule(rule: PricingRule, base_price: Decimal, quantity: int) -> Decimal:
    total_base = base_price * quantity
    discount = Decimal("0")
    for action in rule.actions:
        if action.discount_type == DiscountType.percent:
            discount += total_base * (Decimal(action.discount_value) / Decimal("100"))
        else:
            discount += Decimal(action.discount_value)
    return discount

def calculate_price(
    db: Session,
    variant: Variant,
    quantity: int,
    user_ctx: UserContext,
    promo_code: str | None = None,
) -> PriceBreakdown:
    base = Decimal(variant.product.base_price)
    total_before = base * quantity
    rules = _load_rules(db, variant, quantity, user_ctx, promo_code)

    total_discount = Decimal("0")
    applied: list[dict] = []
    for rule in rules:
        discount = _apply_rule(rule, base, quantity)
        if discount <= 0:
            continue
        total_discount += discount
        applied.append({"rule_id": rule.id, "name": rule.name, "amount": str(discount)})

    if total_discount > total_before:
        total_discount = total_before

    total_after = total_before - total_discount
    final_unit = total_after / quantity

    return PriceBreakdown(
        base_price=base,
        final_unit_price=final_unit,
        quantity=quantity,
        total_before_discount=total_before,
        total_discount=total_discount,
        total_after_discount=total_after,
        applied_rules=applied,
    )
