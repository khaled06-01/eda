# Feedstock prices and co-movement

Per the supplied plant context, AA/GAA and Butanol are internally produced. Do not add their external market-reference prices as plant purchase costs. The dataset's all-in Production_Cost_per_Ton is retained without adding these costs again. GAA (P001) and Butanol (P004) are valid **market-reference drivers** for BA and SAP price analysis.

## Measured global benchmark correlations

| target | driver | scope | n | same_month | lag1_driver | same_month_change |
| --- | --- | --- | --- | --- | --- | --- |
| P002 | P001 | pre_holdout | 30 | 0.97 | 0.91 | 0.68 |
| P002 | P001 | full_sample_descriptive | 36 | 0.97 | 0.91 | 0.67 |
| P002 | P004 | pre_holdout | 30 | 0.95 | 0.91 | 0.77 |
| P002 | P004 | full_sample_descriptive | 36 | 0.94 | 0.91 | 0.68 |
| P003 | P001 | pre_holdout | 30 | 0.68 | 0.56 | 0.54 |
| P003 | P001 | full_sample_descriptive | 36 | 0.52 | 0.43 | 0.54 |
| P003 | P004 | pre_holdout | 30 | 0.61 | 0.51 | 0.60 |
| P003 | P004 | full_sample_descriptive | 36 | 0.43 | 0.35 | 0.51 |

lag1_driver means corr(target[t], driver[t−1]); n is the number of months in the scope, with one fewer usable pair for lagged or differenced statistics. Pre-holdout values use January 2022–June 2024. Full-sample values include holdout and are descriptive only. Differenced correlations help distinguish movement from common price levels but do not establish causality.

The user's approximate 0.65 BA / 0.54 SAP contemporaneous and 0.1 lagged correlations are prior context, not substituted for these measured results. Price definition, period and data version can change them; the dictionary also reports different synthetic benchmark relationships. Use the attached data's measurements and disclose their definition.

## Lagged-driver experiment

| series | model | split | MAPE_pct | RMSE |
| --- | --- | --- | --- | --- |
| P002 | own_lag1 | holdout | 4.11 | 52.34 |
| P002 | own_lag1 | rolling_cv | 5.10 | 73.58 |
| P002 | own_lag1_plus_drivers | holdout | 2.03 | 28.84 |
| P002 | own_lag1_plus_drivers | rolling_cv | 4.57 | 57.83 |
| P003 | own_lag1 | holdout | 1.63 | 58.15 |
| P003 | own_lag1 | rolling_cv | 2.37 | 67.64 |
| P003 | own_lag1_plus_drivers | holdout | 2.10 | 66.26 |
| P003 | own_lag1_plus_drivers | rolling_cv | 2.91 | 77.04 |

Both standardized Ridge models use alpha=10 fixed in advance: own lag-1 alone versus own lag-1 plus lagged GAA and Butanol. Every origin trains only on preceding months. This is a controlled incremental comparison, not an exhaustive search or a causal test. Twelve historical origins and six holdout points limit evidence. A poor lagged-driver result does not rule out joint forecasting or future value in a longer series.

Treat feedstocks chiefly as co-moving references: forecast jointly using only information available at origin, or use same-month BA/SAP reference-price scenarios. A future driver observation must never leak into a one-step forecast.

NaOH is the only purchased chemical input for the described SAP route. It is absent from the supplied file. Optional enhancement: licensed monthly ICIS, Argus or Platts caustic-soda reference data with consistent region, currency, dry/liquid concentration, freight basis and publication date. No external prices have been fetched or invented. Align data by availability date; only lagged/forecast NaOH is permissible in ex-ante forecasts. Avoid adding its cost twice if the all-in production cost already includes it. Aramco supplies propane, ethane and sales gas; supply terms/prices are not provided.
