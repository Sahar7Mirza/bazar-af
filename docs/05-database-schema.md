# 5. Database schema (PostgreSQL 16)

The authoritative schema is the Alembic migration `backend/alembic/versions/0001_initial.py`; the SQL below is the reviewed design it implements.

```sql
CREATE TYPE user_role AS ENUM ('buyer','seller','admin');
CREATE TYPE seller_status AS ENUM ('pending','approved','rejected','suspended');
CREATE TYPE product_status AS ENUM ('active','hidden');
CREATE TYPE order_status AS ENUM ('pending','confirmed','ready','completed','cancelled');
CREATE TYPE payment_preference AS ENUM ('cash','mobile_money');
CREATE TYPE mm_provider AS ENUM ('m_paisa','hesabpay','other');

CREATE TABLE users (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email TEXT NOT NULL, password_hash TEXT NOT NULL,
  full_name TEXT NOT NULL, phone TEXT NOT NULL, role user_role NOT NULL DEFAULT 'buyer',
  district TEXT, is_active BOOLEAN NOT NULL DEFAULT TRUE,
  failed_logins INT NOT NULL DEFAULT 0, locked_until TIMESTAMPTZ, last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE UNIQUE INDEX uq_users_email ON users (lower(email));

CREATE TABLE refresh_tokens (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  family_id UUID NOT NULL, token_hash TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMPTZ NOT NULL, used_at TIMESTAMPTZ, revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX ix_refresh_user ON refresh_tokens (user_id); CREATE INDEX ix_refresh_family ON refresh_tokens (family_id);

CREATE TABLE categories (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name TEXT NOT NULL UNIQUE, slug TEXT NOT NULL UNIQUE, is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now());

CREATE TABLE seller_profiles (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT NOT NULL UNIQUE REFERENCES users(id),
  business_name TEXT NOT NULL, category_id BIGINT REFERENCES categories(id),
  description TEXT, district TEXT NOT NULL, address_note TEXT, phone TEXT NOT NULL, opening_hours TEXT,
  status seller_status NOT NULL DEFAULT 'pending', review_note TEXT,
  reviewed_by BIGINT REFERENCES users(id), reviewed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX ix_seller_status ON seller_profiles (status, district);

CREATE TABLE products (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  seller_id BIGINT NOT NULL REFERENCES seller_profiles(id), category_id BIGINT REFERENCES categories(id),
  name TEXT NOT NULL, description TEXT, price_afn NUMERIC(12,2) NOT NULL CHECK (price_afn >= 0),
  unit TEXT NOT NULL DEFAULT 'piece', stock_qty INT NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
  status product_status NOT NULL DEFAULT 'active', hidden_by_admin BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX ix_products_browse ON products (status, category_id, price_afn) WHERE deleted_at IS NULL;
CREATE INDEX ix_products_seller ON products (seller_id) WHERE deleted_at IS NULL;

CREATE TABLE orders (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  order_no TEXT NOT NULL UNIQUE,
  buyer_id BIGINT NOT NULL REFERENCES users(id), seller_id BIGINT NOT NULL REFERENCES seller_profiles(id),
  status order_status NOT NULL DEFAULT 'pending',
  payment_preference payment_preference NOT NULL, mobile_money_provider mm_provider,
  payment_status TEXT NOT NULL DEFAULT 'not_processed' CHECK (payment_status = 'not_processed'),
  total_afn NUMERIC(12,2) NOT NULL CHECK (total_afn >= 0), note TEXT, cancel_reason TEXT,
  cancelled_by BIGINT REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (payment_preference = 'mobile_money' OR mobile_money_provider IS NULL));
CREATE INDEX ix_orders_buyer ON orders (buyer_id, created_at DESC);
CREATE INDEX ix_orders_seller ON orders (seller_id, status, created_at DESC);

CREATE TABLE order_items (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE, product_id BIGINT NOT NULL REFERENCES products(id),
  product_name TEXT NOT NULL, unit_price_afn NUMERIC(12,2) NOT NULL, quantity INT NOT NULL CHECK (quantity > 0),
  line_total_afn NUMERIC(12,2) NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (line_total_afn = unit_price_afn * quantity));
CREATE INDEX ix_items_order ON order_items (order_id);

CREATE TABLE audit_log (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  actor_id BIGINT REFERENCES users(id), actor_role TEXT, action TEXT NOT NULL,
  entity_type TEXT, entity_id TEXT, detail JSONB, ip TEXT, request_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX ix_audit_time ON audit_log (created_at DESC); CREATE INDEX ix_audit_actor ON audit_log (actor_id, created_at DESC);
```

`updated_at` is maintained by the ORM (`onupdate`). Indexes follow the list endpoints: browse (status/category/price), seller inbox (seller/status/time), buyer history (buyer/time).

The former survey tables were dropped in migration 0005. Research figures are computed from `orders` (see [10](10-research-module.md)).

