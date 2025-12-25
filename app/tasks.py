from datetime import datetime
from sqlalchemy.orm import joinedload
from .celery_app import celery_app
from .db import SessionLocal
from .models import CartItem, Variant

@celery_app.task(name="cleanup_expired_reservations")
def cleanup_expired_reservations():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        with db.begin():
            items = (
                db.query(CartItem)
                .options(joinedload(CartItem.variant))
                .filter(CartItem.reserved_until < now)
                .with_for_update(of=Variant)
                .all()
            )
            for item in items:
                variant = item.variant
                variant.reserved_quantity -= item.quantity
                if variant.reserved_quantity < 0:
                    variant.reserved_quantity = 0
                db.delete(item)
    finally:
        db.close()
