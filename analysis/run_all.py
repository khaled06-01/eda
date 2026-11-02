"""Run independent modules and write a concise evidence-based report."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
import sklearn
from common import OUT, NAMES, load
import demand_forecasting
import price_forecasting
import feedstock_analysis
import allocation_optimization

def table(d):
    # Avoid an optional tabulate dependency.
    cols=list(d.columns)
    rows=['| '+' | '.join(map(str,cols))+' |','| '+' | '.join(['---']*len(cols))+' |']
    for row in d.itertuples(index=False,name=None):
        rows.append('| '+' | '.join(f'{v:.2f}' if isinstance(v,(float,np.floating)) else str(v).replace('|',' / ') for v in row)+' |')
    return '\n'.join(rows)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data',required=True,type=Path)
    args=parser.parse_args();d=load(args.data)
    ds,customers=demand_forecasting.run(d)
    ps=price_forecasting.run(d)
    feedstock_analysis.run(d)
    opt=allocation_optimization.run(d)
    metadata=dict(input_filename=args.data.name,sha256=hashlib.sha256(args.data.read_bytes()).hexdigest(),
                  rows=len(d),columns=len(d.columns),months=d.Month.nunique(),
                  python=platform.python_version(),pandas=pd.__version__,numpy=np.__version__,
                  scipy=scipy.__version__,scikit_learn=sklearn.__version__)
    (OUT/'run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    dh=ds[(ds.split=='holdout')&ds.selected&(ds.level=='product')]
    ph=ps[(ps.split=='holdout')&ps.selected&~ps.series.str.contains('|',regex=False)]
    pn=ps[(ps.split=='holdout')&(ps.model=='naive_lag1')][['series','MAPE_pct','RMSE','directional_accuracy_pct']].rename(columns={c:'naive_'+c for c in ['MAPE_pct','RMSE','directional_accuracy_pct']})
    ph=ph.merge(pn,on='series')
    baseline=ds[(ds.split=='holdout')&(ds.model=='naive_lag1')&(ds.level=='product')]
    compare=dh[['series','model','MAPE_pct','MAE','WAPE_pct','Bias','coverage80_pct','meets_target']].merge(
        baseline[['series','MAPE_pct']].rename(columns={'MAPE_pct':'naive_MAPE_pct'}),on='series')
    fc=pd.read_csv(OUT/'feedstock_correlations.csv')
    lag=pd.read_csv(OUT/'feedstock_lag_experiment_metrics.csv')
    ch=customers[customers.split=='holdout']
    customer_wape=100*(ch.prediction-ch.actual).abs().sum()/ch.actual.abs().sum()
    reg=ds[(ds.split=='holdout')&ds.selected&(ds.level=='product_region')]
    tier=pd.read_csv(OUT/'optimization_tier_fulfillment.csv')
    ts=tier.groupby(['method','tier'])[['ordered_tons','allocated_tons']].sum().reset_index()
    ts['fulfillment_pct']=100*ts.allocated_tons/ts.ordered_tons
    totals=opt[['historical_profit_USD','tier_priority_profit_USD','optimized_profit_USD']].sum()
    reports={
    '01_demand_report.md':f'''# Demand forecasting evaluation

Target: sum of **Ordered_Quantity_Tons**, not allocated sales. Units: tons/month. Product and product-region series are aggregated before fitting; repeated supply and price values are never summed.

Rolling-origin validation uses 12 one-month-ahead origins, July 2023–June 2024. Initial training ends June 2023 (18 months). The final holdout contains July–December 2024 (six origins). Each origin refits using all preceding actual observations. This permits earlier holdout observations for later one-step forecasts; it is not a six-month forecast issued in June.

For each series, choose the lowest validation MAPE among lag-1 naive, trailing-three-month mean, seasonal lag-12, and standardized Ridge models (alpha 1, 10, 100). Ridge uses own lags 1/2/3/12, trailing mean, calendar seasonality and time index. Training scalers and model parameters use past data only. No contemporaneous market, fulfillment, allocation, revenue or derived cost features are used.

## Product holdout results

{table(compare)}

Targets are supplied business acceptance criteria, not guaranteed outcomes: product MAPE ≤8% (≤7% strong), product-region ≤15%. {int(reg.meets_target.sum())} of {len(reg)} selected product-region series meet the 15% target. SAP's reported 10–11% difficulty is context; the measured result above takes precedence for this dataset and protocol. Model selection can retain the naive model, and improved holdout accuracy is not guaranteed.

## Customer forecasts

Product forecasts are distributed using each customer's share of ordered volume in the last six observed months. Shares sum to one, preserving product totals. No customer-level model is independently tuned. Volume-weighted pooled customer holdout WAPE is **{customer_wape:.2f}%** across {len(ch)} customer-product-month observations. Per customer-product metrics are in customer_demand_metrics.csv. Compare the expected 25–35% range with WAPE; it is not a universal pass/fail bound. Shares use historical customers, so new-customer demand needs an explicit onboarding assumption. Missing monthly orders within existing series are treated as zero.

## Metrics and reliability

MAPE = 100 × mean(|prediction−actual|/|actual|) over nonzero actuals; zero counts are reported. MAE = mean absolute error in tons. WAPE = 100 × sum absolute errors / sum absolute actuals. Bias = mean(prediction−actual); positive means overforecast. RMSE is provided as an additional diagnostic.

Symmetric 80% intervals use the selected model's 12 pre-holdout absolute validation errors, the finite-sample corrected 80th-percentile rank, and a zero lower bound. Calibration errors are excluded from holdout coverage measurement. These empirical intervals assume reasonably stable errors; temporal dependence, model selection on the same calibration period, and small samples limit guarantees. Six holdout observations yield coverage steps of 16.67%; 5/6 = 83.33% is closest to 80%. Customer intervals are not inferred from product intervals.

Inspect demand_cv_stability.csv for the two historical six-origin MAPE periods and demand_residual_diagnostics.csv for holdout bias and residual lag-1 correlation. Six residuals are insufficient for strong statistical claims. Predictions include all candidates and an explicit selected flag. Results under rolling_cv are model-selection diagnostics, not unbiased final performance estimates.
''',
    '02_price_report.md':f'''# Price forecasting evaluation

Global target: Global_Market_Price (USD/ton), unique per product-month. Regional target: Final_Adjusted_Price, unique per product-region-month. These are market reference prices, not customer selling prices. Deduplication prevents high-order-count months from receiving artificial weight.

The same 12 rolling origins, untouched final six-month holdout for model selection, candidate models and past-only refitting protocol as demand are used. Main metrics: MAPE, RMSE (USD/ton), and directional accuracy; full tables retain MAE, WAPE and signed bias.

{table(ph[['series','model','MAPE_pct','naive_MAPE_pct','RMSE','naive_RMSE','directional_accuracy_pct','naive_directional_accuracy_pct']])}

Compare every selected series with model=naive_lag1 in price_metrics.csv. Naive predicts no change: directional accuracy is the exact match of sign(prediction−previous actual) and sign(actual−previous actual). An unchanged naive forecast scores only when actual is also unchanged; this convention is explicit because other definitions can treat ties differently. Six test points are indicative, not conclusive.

Feedstock co-movement is examined separately; observed same-month GAA or Butanol prices are never supplied as known future regressors. All holdout predictions and baseline results are retained in price_predictions.csv and price_metrics.csv.
''',
    '03_optimization_report.md':f'''# Allocation optimization: retrospective supply-only scenario

This experiment maximizes sum(Net_Profit_per_Ton × allocated tons) using July–December 2024 realized order demand, realized unit margins and portfolio available supply. It is an **ex-post allocation benchmark**, not a deployable forecast-driven plan or demonstrated real-world profit uplift. Continuous quantities are allowed; lot sizes and integer dispatch rules are not enforced.

Constraints tested: 0 ≤ allocation ≤ requested quantity; total monthly product allocation ≤ Available_Supply_Tons; Tier-1 allocation equals its full requested quantity as an explicit conservative proxy. Requested quantities are **not known contractual minima**. Infeasible months are retained and reported rather than relaxing constraints.

Feasible runs: {int(opt.feasible.sum())}/{len(opt)}. All feasible solutions passed independent numeric checks of these implemented constraints (tolerance 1e-6 tons). This does not establish 100% compliance with the missing hard constraints below.

## Same-period profit comparison (USD)

{table(totals.rename_axis('method').reset_index(name='profit_USD'))}

Historical allocation is the actual Allocated_Quantity_Tons, described in the dictionary as tier-priority. A second, reproducible baseline allocates the same available supply in tier order, with date and order ID as tie breakers; it does not claim to reconstruct undocumented historical tie-breaking. Both baseline comparisons are in optimization_monthly.csv. When historical dispatch uses less supply, its comparison also includes a volume effect. LP versus reconstructed tier priority uses the same supply and Tier-1 proxy rule. All-in unit costs from the dataset are retained unchanged; no internal GAA/Butanol market purchase costs are added.

## Volume-weighted fulfillment by tier

{table(ts[['method','tier','fulfillment_pct']])}

## Required inputs before operational approval

The master file omits opening inventory, safety-stock levels, nameplate capacity, binding Tier-1 contract minima, and the active allocation constraint table (export caps, margin floors, spot caps, etc.). Available supply is a realized portfolio quantity, not a substitute for production capacity. Consequently actual capacity compliance, minimum safety stock compliance, true contractual compliance and all-hard-constraint compliance are **not assessable**. The model does not assume missing values are zero.

For a complete model, obtain tables 01, 07 and 08, capacity schedules (table 05), contract quantities and effective dates, plus unit material balances/yields. Add inventory recursion I_end=I_open+portfolio production−dispatch, I_end≥safety stock, production≤effective capacity, and contract minimum allocation constraints. Protect other offtake commitments and avoid double-counting inventory and Available_Supply. Recompute both baselines under the same inventory and contract rules. For forward planning, use demand and price forecasts known at each origin, forecast costs/supply, and scenarios rather than realized margins. Full physical integration remains outside this dataset's supported scope.
''',
    '04_feedstock_report.md':f'''# Feedstock prices and co-movement

Per the supplied plant context, AA/GAA and Butanol are internally produced. Do not add their external market-reference prices as plant purchase costs. The dataset's all-in Production_Cost_per_Ton is retained without adding these costs again. GAA (P001) and Butanol (P004) are valid **market-reference drivers** for BA and SAP price analysis.

## Measured global benchmark correlations

{table(fc)}

lag1_driver means corr(target[t], driver[t−1]); n is the number of months in the scope, with one fewer usable pair for lagged or differenced statistics. Pre-holdout values use January 2022–June 2024. Full-sample values include holdout and are descriptive only. Differenced correlations help distinguish movement from common price levels but do not establish causality.

The user's approximate 0.65 BA / 0.54 SAP contemporaneous and 0.1 lagged correlations are prior context, not substituted for these measured results. Price definition, period and data version can change them; the dictionary also reports different synthetic benchmark relationships. Use the attached data's measurements and disclose their definition.

## Lagged-driver experiment

{table(lag[['series','model','split','MAPE_pct','RMSE']])}

Both standardized Ridge models use alpha=10 fixed in advance: own lag-1 alone versus own lag-1 plus lagged GAA and Butanol. Every origin trains only on preceding months. This is a controlled incremental comparison, not an exhaustive search or a causal test. Twelve historical origins and six holdout points limit evidence. A poor lagged-driver result does not rule out joint forecasting or future value in a longer series.

Treat feedstocks chiefly as co-moving references: forecast jointly using only information available at origin, or use same-month BA/SAP reference-price scenarios. A future driver observation must never leak into a one-step forecast.

NaOH is the only purchased chemical input for the described SAP route. It is absent from the supplied file. Optional enhancement: licensed monthly ICIS, Argus or Platts caustic-soda reference data with consistent region, currency, dry/liquid concentration, freight basis and publication date. No external prices have been fetched or invented. Align data by availability date; only lagged/forecast NaOH is permissible in ex-ante forecasts. Avoid adding its cost twice if the all-in production cost already includes it. Aramco supplies propane, ethane and sales gas; supply terms/prices are not provided.
''',
    '05_scope_and_assumptions.md':'''# Integrated plant scope and assumptions

The supplied data dictionary identifies this as a synthetic dataset, not audited plant history. Analysis findings therefore demonstrate methods on simulated data and require validation with plant records before operational use.

The real plant is fully integrated: cracker propylene feeds AA production; AA feeds BA; GAA feeds SAP; on-site Butanol made from syngas and propylene also feeds BA. NaOH is the only purchased chemical input on the SAP route. Propane, ethane and sales gas are supplied by Aramco. These statements are user-supplied physical context; the master dataset cannot independently verify them.

The current dataset represents GAA, BA, SAP and Butanol as independent finished-product series. It does not model the internal AA/GAA and Butanol material balance, competing internal consumption versus external sales, conversion yields, or shared feedstock/unit constraints. AA is not a separate product series. Statistical co-movement does not restore these missing physical relationships.

Accordingly, forecasts describe portfolio orders and reference prices; supply-only optimization cannot establish whole-plant feasibility or total integrated economics. Internal reference prices may support scenarios or consistent opportunity-cost accounting, but must not be charged again as external purchases. Obtain a unit-level balance and reconciled cost basis before integrated optimization.

Only the uploaded master CSV was analyzed. Other tables described by the dictionary were not supplied. No contractual minimum, safety-stock value, NaOH price, material coefficient or missing constraint has been fabricated. Attachment prose is reference material, not executable setup instructions.
'''
    }
    for name,text in reports.items(): (OUT/name).write_text(text)
    print(table(compare));print('\nCustomer WAPE:',round(customer_wape,2));print('\nProfit:',totals.to_dict())
    print('\nResults:',OUT)

if __name__=='__main__': main()
