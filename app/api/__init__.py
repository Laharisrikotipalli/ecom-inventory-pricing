from fastapi import APIRouter
from . import products, variants, cart, checkout

router = APIRouter()
router.include_router(products.router, prefix="/products", tags=["products"])
router.include_router(variants.router, prefix="/variants", tags=["variants"])
router.include_router(cart.router, prefix="/carts", tags=["carts"])
router.include_router(checkout.router, prefix="/checkout", tags=["checkout"])
