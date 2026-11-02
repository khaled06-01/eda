# Allocation optimization: retrospective supply-only scenario

This experiment maximizes sum(Net_Profit_per_Ton × allocated tons) using July–December 2024 realized order demand, realized unit margins and portfolio available supply. It is an **ex-post allocation benchmark**, not a deployable forecast-driven plan or demonstrated real-world profit uplift. Continuous quantities are allowed; lot sizes and integer dispatch rules are not enforced.

Constraints tested: 0 ≤ allocation ≤ requested quantity; total monthly product allocation ≤ Available_Supply_Tons; Tier-1 allocation equals its full requested quantity as an explicit conservative proxy. Requested quantities are **not known contractual minima**. Infeasible months are retained and reported rather than relaxing constraints.

Feasible runs: 24/24. All feasible solutions passed independent numeric checks of these implemented constraints (tolerance 1e-6 tons). This does not establish 100% compliance with the missing hard constraints below.

## Same-period profit comparison (USD)

| method | profit_USD |
| --- | --- |
| historical_profit_USD | 12089280.00 |
| tier_priority_profit_USD | 12922813.77 |
| optimized_profit_USD | 15219695.13 |

Historical allocation is the actual Allocated_Quantity_Tons, described in the dictionary as tier-priority. A second, reproducible baseline allocates the same available supply in tier order, with date and order ID as tie breakers; it does not claim to reconstruct undocumented historical tie-breaking. Both baseline comparisons are in optimization_monthly.csv. When historical dispatch uses less supply, its comparison also includes a volume effect. LP versus reconstructed tier priority uses the same supply and Tier-1 proxy rule. All-in unit costs from the dataset are retained unchanged; no internal GAA/Butanol market purchase costs are added.

## Volume-weighted fulfillment by tier

| method | tier | fulfillment_pct |
| --- | --- | --- |
| historical | Tier 1 - Strategic | 82.57 |
| historical | Tier 2 - Preferred | 68.53 |
| historical | Tier 3 - Standard | 47.24 |
| historical | Tier 4 - Spot | 43.05 |
| optimized | Tier 1 - Strategic | 100.00 |
| optimized | Tier 2 - Preferred | 27.01 |
| optimized | Tier 3 - Standard | 49.15 |
| optimized | Tier 4 - Spot | 42.24 |
| tier_priority | Tier 1 - Strategic | 100.00 |
| tier_priority | Tier 2 - Preferred | 60.71 |
| tier_priority | Tier 3 - Standard | 32.67 |
| tier_priority | Tier 4 - Spot | 28.71 |

## Required inputs before operational approval

The master file omits opening inventory, safety-stock levels, nameplate capacity, binding Tier-1 contract minima, and the active allocation constraint table (export caps, margin floors, spot caps, etc.). Available supply is a realized portfolio quantity, not a substitute for production capacity. Consequently actual capacity compliance, minimum safety stock compliance, true contractual compliance and all-hard-constraint compliance are **not assessable**. The model does not assume missing values are zero.

For a complete model, obtain tables 01, 07 and 08, capacity schedules (table 05), contract quantities and effective dates, plus unit material balances/yields. Add inventory recursion I_end=I_open+portfolio production−dispatch, I_end≥safety stock, production≤effective capacity, and contract minimum allocation constraints. Protect other offtake commitments and avoid double-counting inventory and Available_Supply. Recompute both baselines under the same inventory and contract rules. For forward planning, use demand and price forecasts known at each origin, forecast costs/supply, and scenarios rather than realized margins. Full physical integration remains outside this dataset's supported scope.
