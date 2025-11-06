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
def get_share_of_voice() -> pd.DataFrame:
    """Fetch share of voice across all categories, flattened into DataFrame."""
    url = f"{base_api}/category/share-of-voice"
    resp = requests.get(url, timeout=100)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for category, info in data.items():
        for entry in info["share_of_voice"]:
            rows.append({
                "category": category,
                "brand": entry["brand"],
                "percentage": entry["percentage"]
            })
    return pd.DataFrame(rows)
def get_category_consumer_perception(params: dict = None) -> pd.DataFrame:
    """Fetch consumer perception data for a specific category."""
    url = f"{base_api}/category/consumer-perception"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, dict) and "share-of-voice" in data:
        return pd.DataFrame(data["share-of-voice"])
    return pd.DataFrame(columns=["brand", "count"])
