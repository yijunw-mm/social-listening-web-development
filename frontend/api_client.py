import requests
import pandas as pd
import streamlit as st


base_api = "http://127.0.0.1:8000"

@st.cache_data()
def group_chat(params: dict = None) -> dict:
    url = f"{base_api}/chat-number"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    return resp.json()
@st.cache_data()
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
@st.cache_data()
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
@st.cache_data()
def get_sentiment_analysis(params=None):
    resp = requests.get(f"{base_api}/brand/sentiment-analysis", params=params, timeout=100)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "sentiment_percent" in data:
        return pd.DataFrame(data["sentiment_percent"])
    return pd.DataFrame(columns=["sentiment", "value"])
@st.cache_data()
def get_consumer_perception(params: dict = None) -> pd.DataFrame:
    url = f"{base_api}/brand/consumer-perception"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "associated_words" in data:
        return pd.DataFrame(data["associated_words"])
    return pd.DataFrame(columns=["word", "co_occurrence_score"])
@st.cache_data()
def get_time_compare_frequency(params: dict = None) -> pd.DataFrame:
    url = f"{base_api}/brand/time-compare/frequency"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    return resp.json()
@st.cache_data()
def get_time_compare_sentiment(params: dict = None) -> pd.DataFrame:
    url = f"{base_api}/brand/time-compare/sentiment"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    return resp.json()
@st.cache_data()
def get_time_compare_share_of_voice(params: dict = None) -> pd.DataFrame:
    url = f"{base_api}/category/time-compare/share-of-voice"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    return resp.json()
@st.cache_data()
def get_share_of_voice(params: dict = None) -> pd.DataFrame:
    """
    Get share of voice for a category.
    Backend returns: {category_name: {share_of_voice: [...], total_mentions: ...}, ...}
    We need to extract the specific category's data.
    """
    url = f"{base_api}/category/share-of-voice"
    resp = requests.get(url, params=params, timeout=100)
    resp.raise_for_status()
    data = resp.json()

    # Extract category_name from params (required)
    category_name = params.get("category_name") if params else None

    if not category_name:
        return pd.DataFrame(columns=["brand", "percentage"])

    # Backend returns data organized by category
    # Format: {category_name: {share_of_voice: [...], total_mentions: X}}
    if category_name in data:
        category_data = data[category_name]
        share_list = category_data.get("share_of_voice", [])
        return pd.DataFrame(share_list)

    # If category not found or no data
    return pd.DataFrame(columns=["brand", "percentage"])


@st.cache_data()
def get_category_consumer_perception(params: dict = None) -> pd.DataFrame:
    """
    Get consumer perception for a category.
    Backend returns: {category: str, associated_words: [{word: str, count: int}, ...]}
    """
    url = f"{base_api}/category/consumer-perception"
    resp = requests.get(url, params=params, timeout=500)
    resp.raise_for_status()
    data = resp.json()

    # Handle error responses
    if "error" in data:
        return pd.DataFrame([{"word": "Error", "count": 0, "error": data["error"]}])

    # Extract associated_words list
    if isinstance(data, dict) and "associated_words" in data:
        words_list = data["associated_words"]
        if words_list:
            return pd.DataFrame(words_list)

    # No data found
    return pd.DataFrame(columns=["word", "count"])