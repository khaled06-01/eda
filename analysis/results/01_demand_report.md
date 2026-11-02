# Demand forecasting evaluation

Target: sum of **Ordered_Quantity_Tons**, not allocated sales. Units: tons/month. Product and product-region series are aggregated before fitting; repeated supply and price values are never summed.

Rolling-origin validation uses 12 one-month-ahead origins, July 2023–June 2024. Initial training ends June 2023 (18 months). The final holdout contains July–December 2024 (six origins). Each origin refits using all preceding actual observations. This permits earlier holdout observations for later one-step forecasts; it is not a six-month forecast issued in June.

For each series, choose the lowest validation MAPE among lag-1 naive, trailing-three-month mean, seasonal lag-12, and standardized Ridge models (alpha 1, 10, 100). Ridge uses own lags 1/2/3/12, trailing mean, calendar seasonality and time index. Training scalers and model parameters use past data only. No contemporaneous market, fulfillment, allocation, revenue or derived cost features are used.

## Product holdout results

| series | model | MAPE_pct | MAE | WAPE_pct | Bias | coverage80_pct | meets_target | naive_MAPE_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P001 | seasonal_lag12 | 7.59 | 587.33 | 7.77 | -314.67 | 66.67 | True | 10.01 |
| P002 | ridge_10 | 8.27 | 529.14 | 8.09 | 30.52 | 50.00 | False | 9.72 |
| P003 | ridge_100 | 9.02 | 273.65 | 8.39 | 206.51 | 83.33 | False | 11.90 |
| P004 | ridge_10 | 5.15 | 295.87 | 5.14 | 0.31 | 100.00 | True | 8.09 |

Targets are supplied business acceptance criteria, not guaranteed outcomes: product MAPE ≤8% (≤7% strong), product-region ≤15%. 12 of 16 selected product-region series meet the 15% target. SAP's reported 10–11% difficulty is context; the measured result above takes precedence for this dataset and protocol. Model selection can retain the naive model, and improved holdout accuracy is not guaranteed.

## Customer forecasts

Product forecasts are distributed using each customer's share of ordered volume in the last six observed months. Shares sum to one, preserving product totals. No customer-level model is independently tuned. Volume-weighted pooled customer holdout WAPE is **47.53%** across 1800 customer-product-month observations. Per customer-product metrics are in customer_demand_metrics.csv. Compare the expected 25–35% range with WAPE; it is not a universal pass/fail bound. Shares use historical customers, so new-customer demand needs an explicit onboarding assumption. Missing monthly orders within existing series are treated as zero.

## Metrics and reliability

MAPE = 100 × mean(|prediction−actual|/|actual|) over nonzero actuals; zero counts are reported. MAE = mean absolute error in tons. WAPE = 100 × sum absolute errors / sum absolute actuals. Bias = mean(prediction−actual); positive means overforecast. RMSE is provided as an additional diagnostic.

Symmetric 80% intervals use the selected model's 12 pre-holdout absolute validation errors, the finite-sample corrected 80th-percentile rank, and a zero lower bound. Calibration errors are excluded from holdout coverage measurement. These empirical intervals assume reasonably stable errors; temporal dependence, model selection on the same calibration period, and small samples limit guarantees. Six holdout observations yield coverage steps of 16.67%; 5/6 = 83.33% is closest to 80%. Customer intervals are not inferred from product intervals.

Inspect demand_cv_stability.csv for the two historical six-origin MAPE periods and demand_residual_diagnostics.csv for holdout bias and residual lag-1 correlation. Six residuals are insufficient for strong statistical claims. Predictions include all candidates and an explicit selected flag. Results under rolling_cv are model-selection diagnostics, not unbiased final performance estimates.
