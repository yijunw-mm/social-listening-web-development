import requests
import pandas as pd
import streamlit as st


base_api = "http://127.0.0.1:8000"

def group_chat(params: dict = None) -> dict:
    url = f"{base_api}/chat-number"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    return resp.json()
def get_keyword_frequency(params:dict = None) -> pd.DataFrame:
    url = f"{base_api}/keyword-frequency"
    resp = requests.get(url,params=params,timeout=100)
    resp.raise_for_status()
    return pd.DataFrame(resp.json())
@st.cache_data()
def new_keywords(params:dict = None) -> pd.DataFrame:
    url = f"{base_api}/new-keyword-prediction"
    resp = requests.get(url,params =params, timeout=3000)
    resp.raise_for_status()
    return pd.DataFrame(resp.json())
def get_brand_keyword(params: dict = None) -> pd.DataFrame:
    url = f"{base_api}/brand/keyword-frequency"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        data = [data]  
    return pd.DataFrame(data)
def add_keyword(params:dict = None) -> pd.DataFrame:
    url = f"{base_api}/brand/add-keyword"
    resp = requests.post(url,params= params,timeout=100)
    resp.raise_for_status()
    return resp.json()
def remove_keyword(params:dict = None) -> pd.DataFrame:
    url = f"{base_api}/brand/remove-keyword"
    resp = requests.post(url,params= params,timeout=100)
    resp.raise_for_status()
    return resp.json()
def get_sentiment_analysis(params=None):
    resp = requests.get(f"{base_api}/brand/sentiment-analysis", params=params, timeout=100)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "sentiment_percent" in data:
        return pd.DataFrame(data["sentiment_percent"])
    return pd.DataFrame(columns=["sentiment", "value"])
def get_consumer_perception(params: dict = None) -> pd.DataFrame:
    url = f"{base_api}/brand/consumer-perception"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "associated_words" in data:
        return pd.DataFrame(data["associated_words"])
    return pd.DataFrame(columns=["word", "co_occurrence_score"])
def get_time_compare_frequency(params: dict = None) -> pd.DataFrame:
    url = f"{base_api}/brand/time-compare/frequency"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    return resp.json()
def get_time_compare_sentiment(params: dict = None) -> pd.DataFrame:
    url = f"{base_api}/brand/time-compare/sentiment"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    return resp.json()
def get_time_compare_share_of_voice(params: dict = None) -> pd.DataFrame:
    url = f"{base_api}/category/time-compare/share-of-voice"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    return resp.json()
def get_share_of_voice(params: dict = None) -> pd.DataFrame:
    url = f"{base_api}/category/share-of-voice"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    data = resp.json()

    if "compare" not in data:
        return pd.DataFrame(columns=["brand", "percent", "time_period"])

    rows = []
    compare = data["compare"]

    for period, info in compare.items():
        share_items = info.get("share_of_voice", [])
        for entry in share_items:
            rows.append({
                "time_period": period,
                "brand": entry.get("brand", "Unknown"),
                "percent": entry.get("percent", 0)
            })

    return pd.DataFrame(rows)
def get_category_consumer_perception(params: dict = None) -> pd.DataFrame:
    url = f"{base_api}/category/consumer-perception"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, dict) and "associated_words" in data:
        return pd.DataFrame(data["associated_words"])

    return pd.DataFrame(columns=["word", "count"])

