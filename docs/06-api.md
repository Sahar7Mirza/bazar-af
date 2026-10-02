# 06 · API structure

Base path `/api/v1`. JSON only. Auth: `Authorization: Bearer <access JWT>` (the Next.js BFF keeps the refresh token in an httpOnly cookie).

## Conventions
- **Errors:** `{"error":{"code":"validation_error","message":"...","details":[...],"request_id":"..."}}`
- **Pagination:** `?page=1&page_size=20` (max 100) → `{items,page,page_size,total,pages}`; sorting via `?sort=created_at&order=desc`.
- **Timestamps:** ISO-8601 UTC; every row has `created_at`/`updated_at`.
- **Payments:** simulated only. `payment_preference` ∈ `cash | mobile_money`; `payment_status` is always `not_processed`.

## Endpoints
| Area | Method & path | Roles |
|---|---|---|
| Health | GET `/health`, `/health/ready` | public |
| Auth | POST `/auth/register` (buyer or seller) | public |
| | POST `/auth/login` | public |
| | POST `/auth/refresh` (rotates refresh token) | public (refresh token) |
| | POST `/auth/logout` | any |
| | GET `/auth/me` | any |
| Categories | GET `/categories` | public |
| | POST/PATCH `/categories` | admin |
| Seller profile | GET/PUT `/sellers/me` | seller |
| | GET `/sellers/{id}` (approved only) | public |
| Products | GET `/products` (search, category, price, pagination) | public |
| | GET `/products/{id}` | public |
| | POST `/products` | seller (approved) |
| | PATCH/DELETE `/products/{id}` (soft delete) | seller (owner) |
| | GET `/sellers/me/products` | seller |
| Orders | POST `/orders` (single seller; stock check; payment preference) | buyer |
| | GET `/orders` (own: buyer's or seller's) | buyer, seller |
| | GET `/orders/{id}` | owner buyer / owner seller / admin |
| | POST `/orders/{id}/status` (confirm, ready, complete). Confirming accepts optional `pickup_in_minutes` (5-10080, default 60) and sets `estimated_pickup_at` | seller (owner) |
| Notifications | GET `/notifications` (`?unread=true`, paginated), GET `/notifications/unread-count`, POST `/notifications/{id}/read`, POST `/notifications/read-all` | any signed-in user (own only) |
| | POST `/orders/{id}/cancel` | buyer (pending) / seller |
| Admin | GET `/admin/users`, PATCH `/admin/users/{id}` (activate/deactivate) | admin |
| | GET `/admin/sellers`, POST `/admin/sellers/{id}/approve` / `reject` | admin |
| | GET `/admin/orders`, GET `/admin/stats` | admin |
| | GET `/admin/audit` | admin |

| Survey | GET `/survey`, POST `/survey/responses` | public (rate-limited) |
| Research | GET `/admin/research/{summary,descriptives,reliability,correlations,regression,export.csv}`, GET `/admin/analytics/marketplace` | admin |

Status codes: 200/201/204; 400 validation; 401 unauthenticated; 403 forbidden; 404 (also for other users' resources); 409 conflict (email taken, insufficient stock, illegal state change); 422 schema; 429 rate limit.
Interactive docs: `/docs` (Swagger) and `/redoc`, generated from Pydantic schemas.


## Order notifications

When a seller changes an order the buyer gets an in-app notification (bell in the top bar, page `/notifications`):

| Event | Message |
|---|---|
| Seller confirms | "<shop> confirmed your order #N. Estimated time until pickup: about <duration>." (the seller picks the estimate; the order page shows the exact time) |
| Seller marks ready | "Your order #N is ready for pick up at <shop>." |
| Seller cancels | "<shop> cancelled your order #N. Reason: ..." |

Notifications are stored in the `notifications` table (migration 0003). Email delivery is not implemented yet; it can be added without changing the table.
