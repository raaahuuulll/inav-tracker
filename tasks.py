import pandas as pd
from utils import fetch_and_update_aum_and_inav, fetch_and_update_ltp

def dummy_task():
    import time
    print("Dummy task executed time:", time.strftime("%Y-%m-%d %H:%M:%S"))

def task_update_ltp_and_discount():
    df = pd.read_csv('etfs.csv')
    df = fetch_and_update_ltp(df)
    df.to_csv('etfs.csv', index=False)
    print("Updated LTP and discount for ETFs.")

def task_update_aum_and_inav():
    df = pd.read_csv('etfs.csv')
    df = fetch_and_update_aum_and_inav(df)
    df.to_csv('etfs.csv', index=False)
    print("Updated AUM and iNAV for ETFs.")