# Price forecasting evaluation

Global target: Global_Market_Price (USD/ton), unique per product-month. Regional target: Final_Adjusted_Price, unique per product-region-month. These are market reference prices, not customer selling prices. Deduplication prevents high-order-count months from receiving artificial weight.

The same 12 rolling origins, untouched final six-month holdout for model selection, candidate models and past-only refitting protocol as demand are used. Main metrics: MAPE, RMSE (USD/ton), and directional accuracy; full tables retain MAE, WAPE and signed bias.

| series | model | MAPE_pct | naive_MAPE_pct | RMSE | naive_RMSE | directional_accuracy_pct | naive_directional_accuracy_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P001 | naive_lag1 | 3.43 | 3.43 | 48.11 | 48.11 | 0.00 | 0.00 |
| P002 | naive_lag1 | 3.20 | 3.20 | 42.79 | 42.79 | 0.00 | 0.00 |
| P003 | mean3 | 1.53 | 1.52 | 47.41 | 51.02 | 66.67 | 0.00 |
| P004 | naive_lag1 | 4.27 | 4.27 | 48.89 | 48.89 | 0.00 | 0.00 |

Compare every selected series with model=naive_lag1 in price_metrics.csv. Naive predicts no change: directional accuracy is the exact match of sign(prediction−previous actual) and sign(actual−previous actual). An unchanged naive forecast scores only when actual is also unchanged; this convention is explicit because other definitions can treat ties differently. Six test points are indicative, not conclusive.

Feedstock co-movement is examined separately; observed same-month GAA or Butanol prices are never supplied as known future regressors. All holdout predictions and baseline results are retained in price_predictions.csv and price_metrics.csv.
