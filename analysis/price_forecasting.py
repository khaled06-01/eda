"""Forecast global benchmarks and regional adjusted reference prices, USD/ton."""
import pandas as pd
from common import MONTHS, OUT, evaluate, summarize

def run(d):
    frames=[]
    for keys,col,level in [(['Product_ID'],'Global_Market_Price','global'),
                            (['Product_ID','Region'],'Final_Adjusted_Price','regional')]:
        for key,g in d.groupby(keys):
            key=key if isinstance(key,tuple) else (key,)
            y=g.groupby('Month')[col].first().reindex(MONTHS).to_numpy(float)
            f=evaluate(y,'|'.join(key));f['level']=level;frames.append(f)
    f=pd.concat(frames,ignore_index=True);f.to_csv(OUT/'price_predictions.csv',index=False)
    s=summarize(f,price=True);s.to_csv(OUT/'price_metrics.csv',index=False)
    return s
