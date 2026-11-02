"""Co-movement diagnostics and strictly lagged incremental forecasting experiment."""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from common import MONTHS, OUT, metrics

def run(d):
    p=d.groupby(['Month','Product_ID']).Global_Market_Price.first().unstack().reindex(MONTHS)
    p.to_csv(OUT/'monthly_global_reference_prices.csv')
    correlations=[]; forecasts=[]
    for target in ['P002','P003']:
        for driver in ['P001','P004']:
            for scope,part in [('pre_holdout',p.iloc[:30]),('full_sample_descriptive',p)]:
                correlations.append(dict(target=target,driver=driver,scope=scope,n=len(part),
                    same_month=part[target].corr(part[driver]),
                    lag1_driver=part[target].corr(part[driver].shift(1)),
                    same_month_change=part[target].diff().corr(part[driver].diff())))
        for mode in ['own_lag1','own_lag1_plus_drivers']:
            x=pd.DataFrame({'own':p[target].shift(1)})
            if mode.endswith('drivers'):
                x['GAA_lag1']=p.P001.shift(1);x['Butanol_lag1']=p.P004.shift(1)
            for t in range(18,36):
                reg=make_pipeline(StandardScaler(),Ridge(alpha=10.))
                reg.fit(x.iloc[1:t],p[target].iloc[1:t])
                forecasts.append(dict(series=target,model=mode,Month=MONTHS[t],split='rolling_cv' if t<30 else 'holdout',
                                      actual=p[target].iloc[t],prediction=max(0.,reg.predict(x.iloc[[t]])[0])))
    pd.DataFrame(correlations).to_csv(OUT/'feedstock_correlations.csv',index=False)
    f=pd.DataFrame(forecasts);f.to_csv(OUT/'feedstock_lag_experiment_predictions.csv',index=False)
    r=[]
    for (series,model,split),g in f.groupby(['series','model','split']):
        r.append(dict(series=series,model=model,split=split,**metrics(g)))
    pd.DataFrame(r).to_csv(OUT/'feedstock_lag_experiment_metrics.csv',index=False)
