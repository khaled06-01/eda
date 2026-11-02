"""Retrospective supply-only LP scenario. Not a certified integrated-plant plan."""
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from common import OUT

def run(d):
    monthly=[];tiers=[];allocations=[]
    for (month,pid),g in d[d.Month>='2024-07-01'].groupby(['Month','Product_ID']):
        g=g.sort_values(['Strategic_Level','Order_Date','Order_ID']).copy()
        demand=g.Ordered_Quantity_Tons.to_numpy(float)
        margin=g.Net_Profit_per_Ton.to_numpy(float)
        supply=float(g.Available_Supply_Tons.iloc[0])
        tier1=g.Strategic_Level.str.startswith('Tier 1').to_numpy()
        # Requested quantities are an explicit proxy, NOT observed contractual minima.
        lower=np.where(tier1,demand,0.)
        solution=linprog(-margin,A_ub=csr_matrix(np.ones((1,len(g)))),b_ub=[supply],
                         bounds=list(zip(lower,demand)),method='highs')
        row=dict(Month=month,Product_ID=pid,supply_tons=supply,
                 tier1_requested_tons=demand[tier1].sum(),solver_status=solution.message,
                 feasible=solution.success)
        hist=g.Allocated_Quantity_Tons.to_numpy(float)
        row['historical_profit_USD']=float(hist@margin)
        row['historical_allocated_tons']=hist.sum()
        if not solution.success:
            monthly.append(row);continue
        x=solution.x
        # Same-supply reconstructed tier-priority baseline, stable date/ID tie breaking.
        remaining=supply;greedy=np.zeros(len(g))
        for i in range(len(g)):
            greedy[i]=min(demand[i],remaining);remaining-=greedy[i]
        assert np.all(x>=lower-1e-6) and np.all(x<=demand+1e-6)
        assert x.sum()<=supply+1e-6
        assert np.allclose(x[tier1],demand[tier1],atol=1e-6)
        row.update(optimized_profit_USD=float(x@margin),tier_priority_profit_USD=float(greedy@margin),
                   optimized_allocated_tons=x.sum(),supply_constraint_pass=True,
                   order_bounds_pass=True,tier1_proxy_fulfillment_pct=100.)
        for baseline,value in [('historical',hist@margin),('tier_priority',greedy@margin)]:
            row[f'improvement_vs_{baseline}_USD']=float(x@margin-value)
            row[f'improvement_vs_{baseline}_pct']=float((x@margin-value)/abs(value)*100) if value else np.nan
        monthly.append(row)
        for tier in sorted(g.Strategic_Level.unique()):
            mask=g.Strategic_Level.eq(tier).to_numpy();ordered=demand[mask].sum()
            for name,arr in [('historical',hist),('tier_priority',greedy),('optimized',x)]:
                tiers.append(dict(Month=month,Product_ID=pid,tier=tier,method=name,
                                  ordered_tons=ordered,allocated_tons=arr[mask].sum(),
                                  fulfillment_pct=100*arr[mask].sum()/ordered if ordered else np.nan))
        for i,r in enumerate(g.itertuples()):
            allocations.append(dict(Order_ID=r.Order_ID,Month=month,Product_ID=pid,
                                    historical_tons=hist[i],tier_priority_tons=greedy[i],optimized_tons=x[i]))
    m=pd.DataFrame(monthly);m.to_csv(OUT/'optimization_monthly.csv',index=False)
    pd.DataFrame(tiers).to_csv(OUT/'optimization_tier_fulfillment.csv',index=False)
    pd.DataFrame(allocations).to_csv(OUT/'optimization_order_allocations.csv',index=False)
    return m
