# 10 · Research module (mobile-money adoption analytics)

Objectives O1 and O3 of the project: collect ≥150 valid questionnaire responses, analyse what drives willingness to adopt mobile money, and present it in a dashboard. The marketplace's own order data (simulated cash / mobile-money preference) complements the survey.

## Instrument (TAM / UTAUT inspired)
5-point Likert items (1 = strongly disagree … 5 = strongly agree), 3–4 items per construct, plus demographics.

| Code | Construct | Example item |
|---|---|---|
| PU | Perceived usefulness | "Mobile money would make my business transactions faster." |
| PEOU | Ease of use | "I find it easy to learn to use mobile money." |
| TR | Trust | "I trust mobile money providers to keep my money safe." |
| CO | Cost | "Mobile money fees are affordable for my business." |
| AC | Accessibility | "Agents and network coverage are available near me." |
| WA | Willingness to adopt (dependent variable) | "I intend to use mobile money for business within 6 months." |

Demographics (optional, coarse to protect anonymity): role (seller/buyer/other), age band, gender, district, business type, current use of mobile money.

## Data model additions
`survey_questions(id, construct, code, text_en, text_fa, position, is_reverse_scored, is_active)` ·
`survey_responses(id, submitted_at, consent, respondent_type, age_band, gender, district, business_type, uses_mobile_money, completion_seconds, is_valid, invalid_reason, created_at, updated_at)` ·
`survey_answers(id, response_id FK, question_id FK, value SMALLINT CHECK 1..5, UNIQUE(response_id, question_id))`.
No user_id, IP or phone on responses. A response is **valid** when consent is true, all items are answered, completion time ≥ 30 s and it is not straight-lining (all identical answers).

## Analysis (server side, pandas / SciPy / statsmodels)
1. **Descriptive**: n, mean, SD, median per item and construct (construct score = mean of its items, reverse items recoded); frequency tables for demographics.
2. **Reliability**: Cronbach's alpha per construct (acceptable ≥ 0.70).
3. **Association**: Pearson and Spearman correlation matrix of construct scores with p-values; Kruskal–Wallis / chi-square for WA across groups (e.g. current users vs non-users).
4. **Regression**: OLS `WA ~ PU + PEOU + TR + CO + AC`; report standardised β, p, 95 % CI, R², adjusted R², F-test, VIF for multicollinearity. Results are interpreted in plain language on the dashboard ("Trust is the strongest predictor, β = …").
5. Suppress any breakdown cell with n < 5.

## API
| Method & path | Role |
|---|---|
| GET `/survey` | public (active questionnaire) |
| POST `/survey/responses` | public, rate-limited, validated |
| GET `/admin/research/summary` (counts, valid/target, quality flags) | admin |
| GET `/admin/research/descriptives` | admin |
| GET `/admin/research/reliability` | admin |
| GET `/admin/research/correlations` | admin |
| GET `/admin/research/regression` | admin |
| GET `/admin/research/export.csv` | admin |
| GET `/admin/analytics/marketplace` | admin |

## Dashboard (admin)
Progress ring (valid / 150); bar chart of construct means; correlation heat-map; regression table + coefficient chart; preference split (Cash vs Mobile Money, provider share) from orders; filters by district and respondent type; empty state until n ≥ 30 ("Not enough responses for regression yet").

## Usability evaluation (O3)
≥10 participants (mix of sellers and buyers) perform 6 core tasks: register, create a product, find and filter a product, place an order with a payment preference, seller confirms the order, admin reads the dashboard. Record completion, time and errors; SUS questionnaire. Target: ≥75 % task completion and SUS ≥ 68. Script and results template kept in `docs/usability/` (added in Phase 5).

## Seed data
~160 synthetic responses generated with a fixed random seed and a plausible underlying model (Trust and Usefulness positively related to Willingness, Cost negatively weighted) so the dashboard is meaningful. **Clearly labelled synthetic**; real data replaces it by clearing `survey_*` tables.
