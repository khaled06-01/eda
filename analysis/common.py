"""Shared chronological forecasting and evaluation utilities."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
OUT.mkdir(exist_ok=True)
MONTHS = pd.date_range('2022-01-01', '2024-12-01', freq='MS')
NAMES = {'P001':'GAA', 'P002':'BA', 'P003':'SAP', 'P004':'Butanol'}
MODELS = ['naive_lag1', 'mean3', 'seasonal_lag12', 'ridge_1', 'ridge_10', 'ridge_100']

def load(path):
    d = pd.read_csv(path, parse_dates=['Month'])
    assert not d.Order_ID.duplicated().any(), 'Duplicate order IDs'
    assert d.notna().all().all(), 'Missing values require explicit handling'
    assert set(d.Month.unique()) == set(MONTHS), 'Unexpected month coverage'
    for col, keys in [('Global_Market_Price',['Month','Product_ID']),
                      ('Final_Adjusted_Price',['Month','Product_ID','Region']),
                      ('Available_Supply_Tons',['Month','Product_ID'])]:
        assert d.groupby(keys)[col].nunique().max() == 1, f'Conflicting repeated {col}'
    return d

def features(y, t):
    return [y[t-1], y[t-2], y[t-3], y[t-12], np.mean(y[t-3:t]),
            np.sin(2*np.pi*t/12), np.cos(2*np.pi*t/12), t]

def forecast(y, t, model):
    if model == 'naive_lag1': return float(y[t-1])
    if model == 'mean3': return float(np.mean(y[t-3:t]))
    if model == 'seasonal_lag12': return float(y[t-12])
    reg = make_pipeline(StandardScaler(), Ridge(alpha=float(model.split('_')[1])))
    reg.fit([features(y,i) for i in range(12,t)], y[12:t])
    return max(0., float(reg.predict([features(y,t)])[0]))

def metrics(frame):
    a = frame.actual.to_numpy(float); p = frame.prediction.to_numpy(float)
    e = p-a; nz = a != 0
    result = dict(n=len(a), zero_actuals=int((~nz).sum()),
                  MAPE_pct=float(np.mean(np.abs(e[nz]/a[nz]))*100) if nz.any() else np.nan,
                  MAE=float(np.abs(e).mean()), RMSE=float(np.sqrt(np.mean(e**2))),
                  WAPE_pct=float(np.abs(e).sum()/np.abs(a).sum()*100) if np.abs(a).sum() else np.nan,
                  Bias=float(e.mean()))
    if 'lower80' in frame:
        result['coverage80_pct'] = float(((a>=frame.lower80)&(a<=frame.upper80)).mean()*100)
        result['mean_interval_width'] = float((frame.upper80-frame.lower80).mean())
    if 'previous' in frame:
        result['directional_accuracy_pct'] = float((np.sign(p-frame.previous)==np.sign(a-frame.previous)).mean()*100)
    return result

def evaluate(y, key):
    """Model choice uses Jan-Dec 2023? No: July 2023-June 2024 (indices 18:30).
    Holdout is July-Dec 2024. At each origin, only preceding actuals are used.
    This is a sequence of one-step forecasts, not a fixed June six-step forecast.
    """
    rows=[]
    for model in MODELS:
        for t in range(18,36):
            rows.append(dict(series=key,model=model,Month=MONTHS[t],
                             split='rolling_cv' if t<30 else 'holdout',
                             actual=y[t],previous=y[t-1],prediction=forecast(y,t,model)))
    f=pd.DataFrame(rows)
    cv=f[f.split=='rolling_cv']
    scores={m:metrics(g)['MAPE_pct'] for m,g in cv.groupby('model')}
    selected=min(MODELS,key=lambda m:scores[m])
    # Finite-sample corrected symmetric empirical error intervals; holdout errors excluded.
    for model in MODELS:
        errors=np.abs(cv.loc[cv.model==model,'prediction']-cv.loc[cv.model==model,'actual']).to_numpy()
        rank=min(len(errors),int(np.ceil((len(errors)+1)*.8)))
        q=float(np.sort(errors)[rank-1])
        mask=f.model==model
        f.loc[mask,'lower80']=np.maximum(0,f.loc[mask,'prediction']-q)
        f.loc[mask,'upper80']=f.loc[mask,'prediction']+q
    # Coverage is reported on holdout only: CV residuals calibrated these intervals.
    f['selected']=f.model.eq(selected)
    return f

def summarize(f, price=False):
    rows=[]
    for (key,model,split),g in f.groupby(['series','model','split']):
        r=metrics(g if split=='holdout' else g.drop(columns=['lower80','upper80'],errors='ignore'))
        if not price: r.pop('directional_accuracy_pct',None)
        rows.append(dict(series=key,model=model,split=split,selected=bool(g.selected.iloc[0]),**r))
    return pd.DataFrame(rows)
