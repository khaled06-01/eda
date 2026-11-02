"""Independent cross-file checks of reported metrics, reconciliation and LP constraints."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from common import OUT

parser=argparse.ArgumentParser();parser.add_argument('--data',required=True)
a=parser.parse_args();source=pd.read_csv(a.data,parse_dates=['Month'])
for topic in ['demand','price']:
    pred=pd.read_csv(OUT/f'{topic}_predictions.csv',parse_dates=['Month'])
    scores=pd.read_csv(OUT/f'{topic}_metrics.csv')
    for key,g in pred.groupby(['series','model','split']):
        r=scores[(scores.series==key[0])&(scores.model==key[1])&(scores.split==key[2])].iloc[0]
        err=g.prediction-g.actual
        assert np.isclose(r.MAE,err.abs().mean())
        nonzero=g.actual!=0
        assert np.isclose(r.MAPE_pct,100*(err[nonzero]/g.actual[nonzero]).abs().mean())
        if key[2]=='holdout':
            assert set(g.Month)==set(pd.date_range('2024-07-01','2024-12-01',freq='MS'))
            coverage=100*((g.actual>=g.lower80)&(g.actual<=g.upper80)).mean()
            assert np.isclose(r.coverage80_pct,coverage)
    for series,g in scores[scores.split=='rolling_cv'].groupby('series'):
        selected=g[g.selected]
        assert len(selected)==1
        assert np.isclose(selected.MAPE_pct.iloc[0],g.MAPE_pct.min())
    assert np.all(pred.lower80<=pred.upper80)

customers=pd.read_csv(OUT/'customer_demand_predictions.csv',parse_dates=['Month'])
pred=pd.read_csv(OUT/'demand_predictions.csv',parse_dates=['Month'])
selected=pred[(pred.level=='product')&pred.selected]
for (pid,month),g in customers.groupby(['Product_ID','Month']):
    r=selected[(selected.series==pid)&(selected.Month==month)].iloc[0]
    assert np.isclose(g.prediction.sum(),r.prediction)
    actual=source[(source.Product_ID==pid)&(source.Month==month)].Ordered_Quantity_Tons.sum()
    assert np.isclose(g.actual.sum(),actual)

alloc=pd.read_csv(OUT/'optimization_order_allocations.csv',parse_dates=['Month'])
joined=alloc.merge(source[['Order_ID','Ordered_Quantity_Tons','Net_Profit_per_Ton','Strategic_Level']],on='Order_ID',validate='one_to_one')
monthly=pd.read_csv(OUT/'optimization_monthly.csv',parse_dates=['Month'])
for (month,pid),g in joined.groupby(['Month','Product_ID']):
    r=monthly[(monthly.Month==month)&(monthly.Product_ID==pid)].iloc[0]
    assert g.optimized_tons.sum()<=r.supply_tons+1e-6
    assert (g.optimized_tons>=-1e-6).all()
    assert (g.optimized_tons<=g.Ordered_Quantity_Tons+1e-6).all()
    mask=g.Strategic_Level.str.startswith('Tier 1')
    assert np.allclose(g.loc[mask,'optimized_tons'],g.loc[mask,'Ordered_Quantity_Tons'])
    for name in ['historical','tier_priority','optimized']:
        assert np.isclose((g[f'{name}_tons']*g.Net_Profit_per_Ton).sum(),r[f'{name}_profit_USD'])
    assert r.optimized_profit_USD>=r.tier_priority_profit_USD-1e-4
message='PASS: forecast metrics, holdout dates, CV selection, customer reconciliation, allocation bounds, Tier-1 proxy and profit arithmetic.\n'
(OUT/'validation.txt').write_text(message)
print(message)
