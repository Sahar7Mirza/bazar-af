# 4. ER diagram

```mermaid
erDiagram
  USERS ||--o| SELLER_PROFILES : "has (role=seller)"
  USERS ||--o{ ORDERS : "places (buyer)"
  USERS ||--o{ REFRESH_TOKENS : owns
  USERS ||--o{ AUDIT_LOG : "acts in"
  CATEGORIES ||--o{ SELLER_PROFILES : classifies
  CATEGORIES ||--o{ PRODUCTS : classifies
  SELLER_PROFILES ||--o{ PRODUCTS : lists
  SELLER_PROFILES ||--o{ ORDERS : receives
  ORDERS ||--|{ ORDER_ITEMS : contains
  PRODUCTS ||--o{ ORDER_ITEMS : "snapshotted in"

  USERS {
    bigint id PK
    text email UK
    text password_hash
    text full_name
    text phone
    enum role "buyer|seller|admin"
    text district
    bool is_active
    int failed_logins
    timestamptz locked_until
    timestamptz last_login_at
    timestamptz created_at
    timestamptz updated_at
  }
  REFRESH_TOKENS {
    bigint id PK
    bigint user_id FK
    uuid family_id
    text token_hash UK
    timestamptz expires_at
    timestamptz used_at
    timestamptz revoked_at
    timestamptz created_at
  }
  SELLER_PROFILES {
    bigint id PK
    bigint user_id FK,UK
    text business_name
    bigint category_id FK
    text description
    text district
    text address_note
    text phone
    text opening_hours
    enum status "pending|approved|rejected|suspended"
    text review_note
    bigint reviewed_by FK
    timestamptz reviewed_at
    timestamptz created_at
    timestamptz updated_at
  }
  CATEGORIES {
    bigint id PK
    text name UK
    text slug UK
    bool is_active
    timestamptz created_at
    timestamptz updated_at
  }
  PRODUCTS {
    bigint id PK
    bigint seller_id FK
    bigint category_id FK
    text name
    text description
    numeric price_afn "12,2 >= 0"
    text unit
    int stock_qty ">= 0"
    enum status "active|hidden"
    bool hidden_by_admin
    timestamptz deleted_at "soft delete"
    timestamptz created_at
    timestamptz updated_at
  }
  ORDERS {
    bigint id PK
    text order_no UK
    bigint buyer_id FK
    bigint seller_id FK
    enum status "pending|confirmed|ready|completed|cancelled"
    enum payment_preference "cash|mobile_money"
    enum mobile_money_provider "m_paisa|hesabpay|other (nullable)"
    enum payment_status "not_processed (constant)"
    numeric total_afn
    text note
    text cancel_reason
    bigint cancelled_by FK
    timestamptz created_at
    timestamptz updated_at
  }
  ORDER_ITEMS {
    bigint id PK
    bigint order_id FK
    bigint product_id FK
    text product_name "snapshot"
    numeric unit_price_afn "snapshot"
    int quantity "> 0"
    numeric line_total_afn
    timestamptz created_at
    timestamptz updated_at
  }
  AUDIT_LOG {
    bigint id PK
    bigint actor_id FK "nullable"
    text actor_role
    text action
    text entity_type
    text entity_id
    jsonb detail
    text ip
    text request_id
    timestamptz created_at
  }
```

## Integrity rules
- `orders.payment_status` has `CHECK (payment_status = 'not_processed')` — the database itself refuses anything that would imply a real payment.
- `orders.mobile_money_provider` must be `NULL` when `payment_preference = 'cash'` (CHECK).
- A buyer cannot be the seller of their own order (service rule + test).
- `order_items.line_total_afn = unit_price_afn * quantity` (CHECK). `orders.total_afn` equals the sum of its lines (service rule + integration test).
- Products referenced by orders are soft-deleted (`deleted_at`), never removed.
