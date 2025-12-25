from app.db import SessionLocal, engine
from app.models import Base, Product, Variant

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(Product).first():
            p = Product(name="T-Shirt", description="Basic tee", base_price=10.00)
            db.add(p)
            db.flush()
            v = Variant(product_id=p.id, sku="TS-RED-M", stock_quantity=100)
            db.add(v)
            db.commit()
        print("Seeded")
    finally:
        db.close()

if __name__ == "__main__":
    main()
