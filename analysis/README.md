# Petrochemical forecasting and allocation analysis

Separate executable modules and separate reports cover the requested topics:

- `demand_forecasting.py`: demand metrics, naive comparison, rolling validation, prediction intervals, customer disaggregation and residuals.
- `price_forecasting.py`: global and regional price metrics and directional accuracy.
- `feedstock_analysis.py`: GAA/Butanol correlations and past-only lagged-driver experiment.
- `allocation_optimization.py`: retrospective supply-only LP and two baseline comparisons.
- `common.py`: shared past-only modeling and metric definitions.
- `run_all.py`: orchestrator, data checks, provenance and report generation.
- `results/01_demand_report.md` through `05_scope_and_assumptions.md`: reports with results, definitions and limitations.

Run from any directory using the supplied master dataset:

```bash
python3 /workspace/eda/analysis/run_all.py --data /path/to/10_ML_Master_Dataset.csv
```

Dependencies and tested versions are pinned in `requirements.txt`. The current environment already provided them. To install elsewhere, use a virtual environment and `python -m pip install -r requirements.txt`. Outputs overwrite only this analysis's named files under `results/`. Source inputs are read-only; they are neither modified nor copied into the repository.

All forecasts are monthly, rolling one-step-ahead. July–December 2024 is used only for final evaluation, never candidate selection. Model fitting at later holdout origins incorporates earlier observed holdout months. The original holdout is now examined and should not be repeatedly tuned against; reserve new future observations for any further model development.

Demand targets are customer ordered volume, not unconstrained total regional market demand. Missing inputs prevent certification of whole-plant allocation feasibility. Read the scope and optimization reports before interpreting profit results.

CSV metrics preserve all candidates, including lag-1 naive. `selected=True` identifies the model chosen independently per series on historical validation MAPE. Percent metrics are percentages; demand errors are tons; price errors are USD/ton. Order-level allocation results retain source Order_ID for traceability. `run_metadata.json` records the input hash and runtime package versions.

Verify saved outputs with:

```bash
python3 /workspace/eda/analysis/validate_results.py --data /path/to/10_ML_Master_Dataset.csv
```
