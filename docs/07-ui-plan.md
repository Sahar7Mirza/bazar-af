# 07 · UI plan (Next.js App Router, TypeScript)

Design: **Apple.com-style** (see docs/11): large light hero, whitespace, #f5f5f7 sections, 18px cards, pill buttons, blue accent #0071e3, frosted nav, dark mode; mobile-first (MSE owners use phones), RTL-ready logical CSS.

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

| `/research` | public | Open, anonymous adoption figures: share with 95% CI, provider, week, district, category, plain-language tests |
| `/admin/research` | admin | Same analysis with every group visible and an anonymised CSV download |

Every data view has four states: **loading** (skeleton), **error** (message + retry + request id), **empty** (explanation + next action) and **content**. Accessibility: semantic landmarks, labelled inputs, visible focus, colour-contrast AA, charts with text tables as alternatives, `prefers-reduced-motion`.

Shared: typed API client, BFF route handlers (`/api/auth/*`) holding the refresh cookie, middleware route guards by role, toast + error boundary, loading skeletons, accessible forms.
