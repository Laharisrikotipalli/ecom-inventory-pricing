# E‑Commerce Inventory & Pricing Service – Documentation

This document explains the core design of the E‑Commerce Inventory & Pricing Service built with FastAPI, PostgreSQL, Redis, Celery, and Docker.[file:200]

---

## 1. Domain Model

### Products and Variants

- **Product**
  - Business entity with `name`, `description`, and `base_price`.
- **Variant**
  - Concrete sellable unit of a product (for example, size/color).
  - Fields:
    - `product_id`
    - `sku`
    - `price_adjustment`
    - `stock_quantity`
    - `reserved_quantity`.[file:200]

`stock_quantity` is total physical stock; `reserved_quantity` tracks units currently held in carts but not yet purchased.[file:200]

### Carts and Orders

- **Cart**
  - Temporary container for a user’s shopping session.
- **CartItem**
  - Links a cart with a specific variant and quantity.
  - Stores `reserved_until` and **price snapshots** (unit price, discount, final price).[file:200]
- **Order / OrderItem**
  - Created at checkout.
  - Copies all price information from the cart to keep order totals stable.[file:200]

### Pricing Rules

Pricing rules live in dedicated tables (for example `pricing_rules` and related tables) and are applied when a cart item is created or updated.[file:200]

Typical rule types:

- Bulk quantity discount
- User tier discount
- Promo code discount.[file:200]

---

## 2. Reservation Strategy

The service uses **reserved inventory** instead of immediately decrementing stock when users add items to carts.[file:200]

1. When a cart item is added:
   - Compute `available = stock_quantity - reserved_quantity`.
   - If `available` is insufficient, reject the request.
   - Increase `reserved_quantity` and set `reserved_until` for the cart item.[file:200]

2. At checkout:
   - For each cart item:
     - Ensure `reserved_until` has not expired.
     - Recheck `stock_quantity` and `reserved_quantity`.
   - On success:
     - Decrease `stock_quantity` by purchased quantity.
     - Decrease `reserved_quantity` accordingly.
     - Create `order` and `order_items`.[file:200]

This model reduces overselling risk under concurrent traffic.[file:200]

---

## 3. Background Worker

A Celery worker, using Redis as broker, runs periodic tasks to keep reservations clean.[file:200]

Responsibilities:

- Find all `cart_items` where `reserved_until` is in the past.
- For each expired item:
  - Decrease `reserved_quantity` on the associated variant (not below zero).
  - Remove the expired `cart_item`.[file:200]

The worker prevents “dead” carts from locking inventory indefinitely.[file:200]

---

## 4. Dynamic Pricing Engine

The pricing service calculates final prices for cart items by combining product base price, variant adjustment, and matching rules.[file:200]

Steps:

1. Start with `base_price` of the product.
2. Apply variant `price_adjustment` to get a raw unit price.
3. Load all active pricing rules relevant for:
   - Product / variant
   - Quantity
   - User tier
   - Promo code
   - Time window (if configured).[file:200]
4. Compute discount(s) from rules.
5. Produce:
   - `unit_price`
   - `total_price`
   - `applied_rules` list.
6. Store these values as snapshots on `cart_items` and later copy them to `order_items`.[file:200]

Snapshots guarantee that even if rules change later, existing orders retain their original prices.[file:200]

---

## 5. API Surfaces

High‑level endpoints (see `api.md` for full request/response examples):[file:200]

- `/api/v1/products` – create and fetch products.
- `/api/v1/variants` – create variants.
- `/api/v1/products/{product_id}/price` – calculate price for product/variant/quantity.
- `/api/v1/carts` – create carts.
- `/api/v1/carts/{cart_id}/items` – add/update cart items and reserve stock.
- `/api/v1/checkout` – finalize orders.[file:200]

All endpoints return JSON and use standard HTTP status codes for errors (`400`, `404`, `409`, `500`).[file:200]

---

## 6. Concurrency & Safety

- All inventory mutations run inside database transactions.
- Row‑level locking (for example, `SELECT ... FOR UPDATE`) is used when updating variants to avoid race conditions.
- The combination of transactional updates, reserved quantities, and background cleanup keeps inventory consistent.[file:200]
