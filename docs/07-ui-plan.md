# 07 · UI plan (Next.js App Router, TypeScript)

Design: clean, mobile-first (MSE owners use phones), light theme, large tap targets, English UI with RTL-ready layout tokens (Dari later).

| Route | Role | Screen |
|---|---|---|
| `/` | public | Landing + featured products |
| `/login`, `/register` | public | Forms with inline validation (zod) |
| `/products`, `/products/[id]` | public | Search, category filter, pagination, detail |
| `/cart`, `/checkout` | buyer | Cart (single seller), payment preference: Cash / Mobile Money (+ provider), clear "no payment is processed" notice |
| `/orders`, `/orders/[id]` | buyer | History, status timeline, cancel |
| `/seller` | seller | Dashboard (orders to action, low stock) |
| `/seller/products` (+ `/new`, `/[id]/edit`) | seller | CRUD |
| `/seller/orders` | seller | Confirm / ready / complete |
| `/seller/profile` | seller | Shop details (pending/approved banner) |
| `/admin` | admin | Stats |
| `/admin/users`, `/admin/sellers`, `/admin/orders`, `/admin/audit` | admin | Paginated tables, approve/reject, deactivate |

Shared: typed API client, BFF route handlers (`/api/auth/*`) holding the refresh cookie, middleware route guards by role, toast + error boundary, loading skeletons, accessible forms.
