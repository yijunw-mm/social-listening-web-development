import requests
import pandas as pd


base_api = "http://127.0.0.1:8000"


def get_keyword_frequency(params:dict = None) -> pd.DataFrame:
    url = f"{base_api}/keyword-frequency"
    resp = requests.get(url,params = params,timeout=100)
    resp.raise_for_status()
    return pd.DataFrame(resp.json())

def new_keywords(top_k:dict = None) -> pd.DataFrame:
    url = f"{base_api}/new-keyword-prediction"
    resp = requests.get(url,params ={"top_k":top_k}, timeout=3000)
    resp.raise_for_status()
    return pd.DataFrame(resp.json())
def 

# def add_keyword(keyword: str) -> pd.DataFrame:
#     return fetch_data(f"add-keyword/{keyword}")

# def get_trend_analysis() -> pd.DataFrame:
#     return fetch_data("trend-analysis")

# def get_sentiment_analysis() -> pd.DataFrame:
#     return fetch_data("sentiment-analysis")

