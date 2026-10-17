"""Offline example using the public implementation; see README for evidence scope."""
import sys,json,pathlib,os
repo=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(repo));sys.path.insert(0,str(repo/'src'));os.chdir(repo)
import pandas as pd
from mobility_customers.analysis import prepare_trips,daily_bootstrap_gap
raw=pd.DataFrame([{'start_time':f'2019-02-{d:02} 08:00:00','end_time':f'2019-02-{d:02} 08:{minutes:02}:00','duration_sec':minutes*60,'user_type':user} for d in [1,2,3] for user,minutes in [('Subscriber',5),('Customer',15)]])
data,audit=prepare_trips(raw)
print(json.dumps({"fixture":"six generated trips, not historical estimate","audit":audit,"gap":daily_bootstrap_gap(data,draws=100)}))
