# Demo accounts

Live demo: https://bazar-af-eta.vercel.app

All demo accounts share one password, chosen by whoever runs the seed script
(`SEED_PASSWORD`, see `docs/13-deployment.md`). The password is never stored in
this repository.

| Role | Email | Range |
|---|---|---|
| Admin | `admin@demo.bazar.af` | one account |
| Seller | `seller01@demo.bazar.af`, `seller02@demo.bazar.af`, `seller03@demo.bazar.af` | `seller01` to `seller40` |
| Buyer | `buyer01@demo.bazar.af`, `buyer02@demo.bazar.af`, `buyer03@demo.bazar.af` | `buyer01` to `buyer30` |

## Seller statuses in the seed data

- `seller01` to `seller34`: approved (can list products and handle orders)
- `seller35` to `seller38`: pending (shows "Your seller account is not approved yet" until an admin approves)
- `seller39`: rejected
- `seller40`: suspended

## Who can do what

- Buyer: browse, cart, checkout (simulated Cash or Mobile Money preference), view own orders, cancel pending orders.
- Seller: manage own products; open an order's detail page to confirm, mark ready, mark completed or cancel.
- Admin: approve, reject or suspend sellers; view orders, audit log and research results. Admins cannot confirm orders.
