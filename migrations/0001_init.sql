CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    parent_id INTEGER REFERENCES categories(id)
);

CREATE TYPE product_status AS ENUM ('active', 'archived');

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    status product_status NOT NULL DEFAULT 'active',
    base_price NUMERIC(10,2) NOT NULL,
    category_id INTEGER REFERENCES categories(id)
);

CREATE TABLE variants (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    sku VARCHAR NOT NULL UNIQUE,
    attributes JSONB,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE carts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    variant_id INTEGER NOT NULL REFERENCES variants(id),
    quantity INTEGER NOT NULL,
    reserved_until TIMESTAMPTZ NOT NULL,
    unit_price_snapshot NUMERIC(10,2) NOT NULL,
    discount_snapshot NUMERIC(10,2) NOT NULL,
    final_price_snapshot NUMERIC(10,2) NOT NULL,
    UNIQUE (cart_id, variant_id)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    total_amount NUMERIC(10,2) NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    variant_id INTEGER NOT NULL REFERENCES variants(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    discount NUMERIC(10,2) NOT NULL,
    final_price NUMERIC(10,2) NOT NULL
);

CREATE TYPE pricing_rule_type AS ENUM (
  'bulk_quantity', 'seasonal_percentage',
  'user_tier_percentage', 'promo_code_percentage'
);

CREATE TYPE discount_type AS ENUM ('percent', 'absolute');

CREATE TABLE pricing_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    type pricing_rule_type NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 100
);

CREATE TABLE pricing_rule_conditions (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES pricing_rules(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    variant_id INTEGER REFERENCES variants(id),
    min_quantity INTEGER,
    user_tier VARCHAR,
    start_at TIMESTAMPTZ,
    end_at TIMESTAMPTZ,
    promo_code VARCHAR
);

CREATE TABLE pricing_rule_actions (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES pricing_rules(id) ON DELETE CASCADE,
    discount_type discount_type NOT NULL,
    discount_value NUMERIC(10,2) NOT NULL
);

CREATE INDEX idx_variants_product ON variants(product_id);
CREATE INDEX idx_cart_items_cart ON cart_items(cart_id);
