"""Product, product-region and customer demand evaluation in tons."""
import numpy as np
import pandas as pd
from common import MONTHS, OUT, evaluate, metrics, summarize

def run(d):
    frames=[]
    for keys,level in [(['Product_ID'],'product'),(['Product_ID','Region'],'product_region')]:
        for key,g in d.groupby(keys):
            key=key if isinstance(key,tuple) else (key,)
            y=g.groupby('Month').Ordered_Quantity_Tons.sum().reindex(MONTHS,fill_value=0).to_numpy(float)
            f=evaluate(y,'|'.join(key)); f['level']=level; frames.append(f)
    f=pd.concat(frames,ignore_index=True)
    f.to_csv(OUT/'demand_predictions.csv',index=False)
    summary=summarize(f)
    summary['level']=summary.series.map(f.drop_duplicates('series').set_index('series').level)
    summary['target_MAPE_pct']=summary.level.map({'product':8,'product_region':15})
    summary['meets_target']=summary.MAPE_pct<=summary.target_MAPE_pct
    summary.to_csv(OUT/'demand_metrics.csv',index=False)
    # Disaggregate each product forecast using customer shares from the last six observed months.
    rows=[]
    products=f[(f.level=='product') & f.selected]
    for pid,g in d.groupby('Product_ID'):
        panel=g.groupby(['Month','Customer_ID']).Ordered_Quantity_Tons.sum().unstack(fill_value=0).reindex(MONTHS,fill_value=0)
        for row in products[products.series==pid].itertuples():
            t=MONTHS.get_loc(row.Month); hist=panel.iloc[t-6:t].sum()
            shares=hist/hist.sum() if hist.sum()>0 else hist*0+1/len(hist)
            for cid in panel.columns:
                rows.append(dict(Product_ID=pid,Customer_ID=cid,Month=row.Month,split=row.split,
                                 actual=panel.loc[row.Month,cid],prediction=row.prediction*shares[cid]))
    c=pd.DataFrame(rows); c.to_csv(OUT/'customer_demand_predictions.csv',index=False)
    cr=[]
    for (pid,cid,split),g in c.groupby(['Product_ID','Customer_ID','split']):
        cr.append(dict(Product_ID=pid,Customer_ID=cid,split=split,**metrics(g)))
    pd.DataFrame(cr).to_csv(OUT/'customer_demand_metrics.csv',index=False)
    # Genuine two nonoverlapping six-origin historical periods for stability.
    folds=[]
    for (series,model),g in f[f.split=='rolling_cv'].groupby(['series','model']):
        for fold,part in [('2023-H2',g[g.Month<'2024-01-01']),('2024-H1',g[g.Month>='2024-01-01'])]:
            folds.append(dict(series=series,model=model,fold=fold,**metrics(part.drop(columns=['lower80','upper80']))))
    pd.DataFrame(folds).to_csv(OUT/'demand_cv_stability.csv',index=False)
    res=[]
    for series,g in f[(f.split=='holdout')&f.selected].groupby('series'):
        e=(g.sort_values('Month').prediction-g.sort_values('Month').actual)
        res.append(dict(series=series,n=len(e),Bias=e.mean(),residual_lag1_correlation=e.autocorr(1)))
    pd.DataFrame(res).to_csv(OUT/'demand_residual_diagnostics.csv',index=False)
    return summary,c
