# 10 · Research module (mobile-money adoption from checkout choices)

Objective: measure how many Bazar.af customers choose Mobile Money instead of Cash, and where. The questionnaire/survey was removed; the data is now the choice every buyer makes at checkout. No money moves, so these are **stated preferences**.

## What is measured
Each non-cancelled order carries `payment_preference` (cash | mobile_money) and, for mobile money, a provider. From that:

| Measure | How |
|---|---|
| Share of orders using mobile money | mobile-money orders ÷ all orders, with a **95 % Wilson confidence interval** |
| Share of buyers using it | buyers with ≥ 1 mobile-money order ÷ buyers with orders |
| Provider mix | orders per provider |
| Trend | share per week, last 12 weeks; week-on-week change only when both weeks have ≥ 5 orders |
| Segments | share by seller district and by product category (a group counts only with enough orders) |
| Basket size | average order value for cash vs mobile money |
| Are segments different? | chi-square test of independence (cash/mobile × district, × category) with p-value and Cramér's V as effect size; shown only with ≥ 20 orders and ≥ 2 groups |

## Who sees what
| Page | Who | Content |
|---|---|---|
| `/research` | everyone, no login | the figures above; groups with fewer than 5 orders hidden; no names, IDs or phone numbers |
| `/admin/research` | admin | the same, every group visible, plus **Download anonymised orders (CSV)** |

Why public: it shows sellers and researchers evidence of real adoption and invites others to take part. The page contains only aggregates, so it is safe to open. The page states plainly that the sample is Bazar.af users and that demo data is synthetic.

## API
| Endpoint | Access |
|---|---|
| GET `/research/summary` | public (cached 30 s) |
| GET `/admin/research/summary` | admin |
| GET `/admin/research/export.csv` | admin |

CSV columns: `order_id, week, district, category, payment_preference, mobile_money_provider, total_afn, status, lines`. No buyer, seller or name fields.

## Using it in the paper
Report the share with its confidence interval and n, quote the chi-square result for any segment claim, and state the limits: preferences not payments, self-selected users, early/demo data. Export the CSV for further analysis in Excel, SPSS or R.

## Testing
Unit tests check the Wilson interval and the chi-square p-value against reference values; API tests check public access, small-group hiding, admin-only routes and that the CSV carries no personal data.
