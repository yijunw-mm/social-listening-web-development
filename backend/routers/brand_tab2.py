from fastapi import APIRouter, Query
from typing import List, Optional
import pandas as pd
from collections import Counter
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import re

router = APIRouter()
df_cleaned = pd.read_csv("data/processing_output/cleaned_chat_dataframe2.csv",dtype={"group_id":str})
df_cleaned['clean_text']=(df_cleaned['clean_text'].str.replace(r"\s+'s","'s",regex=True))
# load brand keywrod
brand_keyword_df = pd.read_csv("data/other_data/newest_brand_keywords.csv",keep_default_na=False,na_values=[""])  
brand_keyword_dict = brand_keyword_df.groupby("brand")["keyword"].apply(list).to_dict()

# temporary store user-add keywords
custom_keywords_dict = {brand: set() for brand in brand_keyword_dict}


def extract_brand_context(df: pd.DataFrame, brand: str, brand_keyword_map: dict,
                          window_size: int = 3, merge_overlap: bool = True):


    indices = []
    for i, text in enumerate(df["clean_text"].dropna()):
        if any(alias in text for alias in brand_keyword_map.get(brand, [])):
            start = max(0, i - window_size)
            end = min(len(df), i + window_size + 1)
            indices.append((start, end))


    if not indices:
        return []


    # combine overlap window
    if merge_overlap:
        merged = []
        current_start, current_end = indices[0]
        for s, e in indices[1:]:
            if s <= current_end:  # if there is overlap
                current_end = max(current_end, e)
            else:
                merged.append((current_start, current_end))
                current_start, current_end = s, e
        merged.append((current_start, current_end))
        indices = merged


    # collect corpus
    contexts = []
    for s, e in indices:
        subset = df.iloc[s:e]
        contexts.append({
            "start_idx": s,
            "end_idx": e,
            "context": subset["clean_text"].tolist()
        })


    return contexts


@router.get("/brand/keyword-frequency")
def keyword_frequency(
    brand_name: str,
    group_id:Optional[List[str]]=Query(None),
    year: Optional[int] = None,
    month: Optional[List[int]] = Query(None),
    quarter: Optional[int] = None,
    window_size:int=3,
    merge_overlap:bool =True
):
    # Step 1 filter dataframe
    df = df_cleaned.copy()
    if group_id:
        df = df[df["group_id"].isin(group_id)]
    if year:
        df = df[df["year"]==year]
    if month:
        df = df[df["month"].isin(month)]
    if quarter:
        df = df[df["quarter"] == quarter]

    # Step 2: get brand keyword list
    if brand_name not in brand_keyword_dict:
        return {"error": f"Brand '{brand_name}' not found in keyword dictionary."}
    base_keywords = set(brand_keyword_dict[brand_name])
    custom_keywords = custom_keywords_dict.get(brand_name, set())
    all_keywords = list(base_keywords.union(custom_keywords))

    # New step 3 extract the window message
    contexts = extract_brand_context(
        df,
        brand=brand_name,
        brand_keyword_map = brand_keyword_dict,
        window_size=window_size,
        merge_overlap=merge_overlap
    )
    if not contexts:
        return {"error":f"No mention about brand {brand_name}"}
    
    # step 4 combine
    context_texts=[]
    for c in contexts:
        context_texts.extend(c["context"])

    # Step 5: count keyword frequency
    freq_counter = Counter()
    for text in context_texts:
        words = re.findall("r\w+",text.lower())
        for kw in all_keywords:
            if kw.lower() in words:
                freq_counter[kw] += 1
    if not freq_counter:
        all_words = " ".join(context_texts).split()
        filtered_words = [w for w in all_keywords if w.isalpha() and len(w)>2]
        counter = Counter(filtered_words)
        top_fallback = [{"keyword":w, "count":c} for w, c in counter.most_common(5)]
        return top_fallback

    # Step 4: return output
    result = [{"keyword": kw, "count": freq} for kw, freq in freq_counter.items()]
    result.sort(key=lambda x: x["count"], reverse=True)
    return result

@router.post("/brand/add-keyword")
def add_keyword(brand_name:str,keyword:str):
    if brand_name not in custom_keywords_dict:
        custom_keywords_dict[brand_name]=set()
    custom_keywords_dict[brand_name].add(keyword)
    return {"message":f"keyword '{keyword}' added for brand '{brand_name}'."}

@router.post("/brand/remove-keyword")
def remove_keyword(brand_name:str, keyword:str):
    if brand_name in custom_keywords_dict and keyword in custom_keywords_dict[brand_name]:
        custom_keywords_dict[brand_name].remove(keyword)
        return {"message":f"keyword '{keyword}' removed from brand '{brand_name}'."}
    else:
        return {"message":f"keyword '{keyword}' not found in brand '{brand_name}'."}
    
analyzer = SentimentIntensityAnalyzer()

@router.get("/brand/sentiment-analysis")
def brand_sentiment_analysis_vader(
    brand_name: str,
    group_id: Optional[List[str]] = Query(None),
    year: Optional[int] =None,
    month: Optional[List[int]] = Query(None),
    quarter: Optional[int] = None
):
    # 1. get data
    df = df_cleaned.copy()
    if group_id:
        df = df[df["group_id"].isin(group_id)]
    if year:
        df = df[df["year"] == year]
    if month:
        df = df[df["month"].isin(month)]
    if quarter:
        df = df[df["quarter"] == quarter]

    # 2. get brand name
    if brand_name not in brand_keyword_dict:
        return {"error": f"Brand '{brand_name}' not found."}
    keywords = brand_keyword_dict[brand_name]

    # 3. get the message containing brand name
    matched_texts = [
        text for text in df["clean_text"].dropna()
        if any(kw.lower() in text.lower() for kw in keywords)
    ]

    # 4. compute sentiment analysis
    sentiment_result = {"positive": 0, "neutral": 0, "negative": 0}
    for text in matched_texts:
        score = analyzer.polarity_scores(text)
        compound = score["compound"]
        if compound >= 0.05:
            sentiment_result["positive"] += 1
        elif compound <= -0.05:
            sentiment_result["negative"] += 1
        else:
            sentiment_result["neutral"] += 1

    # 5. output
    total = len(matched_texts)
    if total == 0:
        return {
            "brand": brand_name,
            "total_mentions": 0,
            "sentiment_percent": {},
            "sentiment_count": {}
        }

    sentiment_percent_list = [{
        "sentiment":k,"value": round(v / total * 100, 1)} for k, v in sentiment_result.items()
    ]
    sentiment_count_list =[
        {"sentiment":k, "value":v} for k,v in sentiment_result.items()
    ]
    return {
        "brand": brand_name,
        "total_mentions": total,
        "sentiment_percent": sentiment_percent_list,
        "sentiment_count": sentiment_count_list
    }

def compute_co_occurrence_matrix(texts, top_k=20):
    vectorizer = CountVectorizer(stop_words='english', ngram_range=(1, 3), min_df=2)
    X = vectorizer.fit_transform(texts)
    Xc = (X.T * X)
    Xc.setdiag(0)
    vocab = vectorizer.get_feature_names_out()
    co_occurrence_df = pd.DataFrame(data=Xc.toarray(), index=vocab, columns=vocab)
    word_scores = co_occurrence_df.sum(axis=1).sort_values(ascending=False)
    candidates = list(word_scores.head(top_k*2).index)
    def filter_redundant_ngrams(ngrams:List[str])->List[str]:
        filtered=[]
        for phrase in ngrams:
            if not any(phrase in longer for longer in filtered if phrase!=longer):
                filtered.append(phrase)
        return filtered
    filtered_words = filter_redundant_ngrams(candidates)[:top_k]
    result = [{"word": word, "co_occurrence_score": int(word_scores[word])} for word in filtered_words]
    return result

@router.get("/brand/consumer-perception")
def consumer_perception(brand_name: str, 
                        group_id:Optional[List[str]]=Query(None),
                        year: Optional[int] = None,
                        month: Optional[int] = None,
                        quarter: Optional[int] = None,
                        top_k: int = 20):
    df = df_cleaned.copy()
    if group_id:
        df = df[df["group_id"].isin(group_id)]
    if year:
        df = df[df["year"] == year]
    if month:
        df = df[df["month"] == month]
    if quarter:
        df = df[df["quarter"] == quarter]

    if brand_name not in brand_keyword_dict:
        return {"error": f"Brand '{brand_name}' not found."}
    
    keywords = brand_keyword_dict[brand_name]

    def contains_brand_keywords(text):
        return any(kw.lower() in text.lower() for kw in keywords)
    
    relevant_texts = df_cleaned[df_cleaned["clean_text"].apply(lambda x: isinstance(x, str) and contains_brand_keywords(x))]["clean_text"].tolist()

    if not relevant_texts:
        return {"brand": brand_name, "associated_words": []}

    associated_words = compute_co_occurrence_matrix(relevant_texts, top_k=top_k)
    return {"brand": brand_name, "associated_words": associated_words}

