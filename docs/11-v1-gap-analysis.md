# 11 · Gap analysis: live v1 (bazaraf.netlify.app) vs this rebuild

v1 is a React + Firebase + Node landing site with a "Live Feed", "Post Offer" and "Research" link. Observed on the live page (30 Sep 2026): 0 listings, 0 verified businesses, 0 completed trades; dark theme; Google sign-in only; "Tazkira verification coming soon".

| Area | v1 today | Instructor requirement | Rebuild |
|---|---|---|---|
| Stack | React, Firebase, Node | PostgreSQL, FastAPI, Next.js/TypeScript | Switched, relational model with constraints |
| Content | Empty: zero listings, zero data | Realistic seed data | ~40 Kabul businesses, ~200 products, orders, ~160 synthetic survey responses |
| Roles | Unclear | Buyer, Seller, Administrator with RBAC | Server-enforced RBAC + ownership checks |
| Payments | "agree on payment" | Record simulated Cash / Mobile Money only | Preference stored; DB forbids a paid status |
| Trust claim | "Verified businesses", Tazkira ID | Secure auth, no real data handling | Admin approval of sellers; **no national-ID collection** (privacy) |
| Research | Link only | Survey + descriptive + association/regression | Full module (docs/10) |
| Quality | none visible | Unit, API, integration, E2E tests, logging, errors, pagination, audit | Built per phase |
| Delivery | none | Docker, README, diagrams, Git discipline | Per roadmap |
| Claims | "Real-time", "community ratings" not backed | Honest scope | Ratings out of scope; claims removed |

## UI direction: Apple-style (apple.com)
Same approach as the Pol connector redesign: large light hero with SF-like type (Inter fallback), generous whitespace, alternating white / #f5f5f7 sections, 18px rounded cards, pill buttons, single blue accent (#0071e3), frosted sticky nav, subtle motion respecting `prefers-reduced-motion`. Dark mode via `prefers-color-scheme`. RTL-ready spacing (logical CSS properties) for later Dari.
Applies to landing, catalogue, checkout, seller/admin dashboards and the survey.
