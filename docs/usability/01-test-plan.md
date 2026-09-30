# Usability evaluation plan (Objective O3)

**Goal:** at least 10 participants; target >= 75 % task completion and SUS >= 68.
**Participants:** 6+ small business owners/sellers, 3+ shoppers, 1 administrator-type user. Run in person or remotely on a phone.
**Setup:** fresh seed (`python -m app.seed --reset`), each participant gets a new account or a seed account. Read the consent text; no personal data is recorded - use participant codes (P01...).

## Tasks (think aloud; do not help unless stuck for 2 minutes)
| # | Role | Task | Success when |
|---|---|---|---|
| T1 | Buyer | Create an account and sign in | Reaches the shop |
| T2 | Buyer | Find a product under 500 AFN in your district | Opens a matching product page |
| T3 | Buyer | Order 2 items and choose Mobile Money with a provider | Order confirmation shown |
| T4 | Seller | Add a new product with price and stock | Product appears in "Products" |
| T5 | Seller | Confirm and complete an incoming order | Status reaches "completed" |
| T6 | Admin | Approve a pending seller and find the regression result on the research page | Both done |

## Measures per task
Completed unaided (yes/no/with help), time in seconds, number of errors, confidence 1-5. After the session: **SUS** (10 items, 1-5) and two open questions ("what confused you?", "what would you change?").

## Reporting
Completion rate = completed-unaided tasks / all attempted tasks. SUS score = ((sum of odd items - 5) + (25 - sum of even items)) * 2.5. Use `results-template.csv`. Summarise findings and the fixes made in the capstone report.
