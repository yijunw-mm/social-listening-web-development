from fastapi import APIRouter, Query
from typing import List, Optional
import pandas as pd
from collections import Counter
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import re
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util 
import spacy

router = APIRouter()
df_cleaned = pd.read_csv("data/processing_output/clean_chat_df/2025/cleaned_chat_dataframe.csv",dtype={"group_id":str})
df_cleaned['clean_text']=(df_cleaned['clean_text'].str.replace(r"\s+'s","'s",regex=True))
# load brand keywrod
brand_keyword_df = pd.read_csv("data/other_data/newest_brand_keywords.csv",keep_default_na=False,na_values=[""])  
brand_keyword_dict = brand_keyword_df.groupby("brand")["keyword"].apply(lambda x:list(x)).to_dict()

# temporary store user-add keywords
custom_keywords_dict = {brand: set() for brand in brand_keyword_dict}


def extract_brand_context(df: pd.DataFrame, brand: str, brand_keyword_map: dict,
                          window_size: int = 6, merge_overlap: bool = True):


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
    window_size:int=6,
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
        words = re.findall(r"\w+",text.lower())
        for kw in all_keywords:
            if kw.lower() in words:
                freq_counter[kw] += 1
    if not freq_counter:
        all_words = " ".join(context_texts).split()
        filtered_words = [w for w in all_words if w.isalpha() and len(w)>2]
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

def explain_sentiment(text, top_n=5):
    """return the contribution"""
    words = re.findall(r"\b\w+\b", text.lower())
    scored_words = []
    for w in words:
        if w in analyzer.lexicon:  # there is a score in VADER dictionary
            score = analyzer.lexicon[w]
            scored_words.append((w, score))

    positives = sorted([x for x in scored_words if x[1] > 0], key=lambda x: -x[1])[:top_n]
    negatives = sorted([x for x in scored_words if x[1] < 0], key=lambda x: x[1])[:top_n]

    return {
        "positives": positives,
        "negatives": negatives
    }


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
    #keywords = brand_keyword_dict[brand_name]

    # 3. get the message containing brand name
    matched_texts = [
        text for text in df["clean_text"].dropna()
        if re.search(rf"\b{re.escape(brand_name)}\b",text.lower())
    ]

    # 4. compute sentiment analysis
    sentiment_result = {"positive": 0, "neutral": 0, "negative": 0}
    detailed_examples= []
    for text in matched_texts:
        score = analyzer.polarity_scores(text)
        compound = score["compound"]
        if compound >= 0.05:
            sentiment_result["positive"] += 1
        elif compound <= -0.05:
            sentiment_result["negative"] += 1
        else:
            sentiment_result["neutral"] += 1
        
        # 4.5 explain the contribution
        explanation = explain_sentiment(text, top_n=5)
        detailed_examples.append({
            "text": text,
            "sentiment_score": score,
            "top_positive_words": explanation["positives"],
            "top_negative_words": explanation["negatives"]
        })

    # 5. output
    total = len(matched_texts)
    if total == 0:
        return {
            "brand": brand_name,
            "total_mentions": 0,
            "sentiment_percent": {},
            "sentiment_count": {},
            "examples": []
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
        "sentiment_count": sentiment_count_list,
        "examples":detailed_examples[:5]
    }

nlp = spacy.load("en_core_web_sm")
semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
kw_model = KeyBERT(model='all-MiniLM-L6-v2')

def _overlap_fraction(a, b):
    """计算两个短语之间的token重叠比例"""
    set_a, set_b = set(a.split()), set(b.split())
    if not set_a or not set_b:
        return 0
    return len(set_a & set_b) / min(len(set_a), len(set_b))




def remove_overlapping_phrases(keywords, overlap_ratio=0.6):
    """
    去除短语之间过度重叠的部分（如 "sensitive skin" vs "kids sensitive skin"）。
    overlap_ratio: 超过多少比例认为是重叠，默认 0.6。
    """
    cleaned = []
    for kw in sorted(keywords, key=len, reverse=True):  # 从长到短检查
        if not any(_overlap_fraction(kw, c) > overlap_ratio for c in cleaned):
            cleaned.append(kw)
    return cleaned[::-1]  # 保持原顺序输出


def extract_clean_brand_keywords_auto(texts, brand_name, top_k=15):
    """
    extract meaningful word
    """
    if not texts:
        return []

    # Step 1️⃣ remove the brand name itself
    cleaned_texts = [re.sub(rf"\b{re.escape(brand_name)}\b", "", t.lower()) for t in texts]
    joined_text = " ".join(cleaned_texts)

    # Step 2️⃣ KeyBERT extrat keyword
    keywords = [kw for kw, _ in kw_model.extract_keywords(
        joined_text,
        keyphrase_ngram_range=(1, 3),
        use_mmr=True,
        diversity=0.7,
        top_n=top_k*5,
        stop_words='english'
    )]

    # Step 3️⃣ POS keep noun, adj
    def is_meaningful(phrase):
        doc = nlp(phrase)
        return any(t.pos_ in ["ADJ", "NOUN"] for t in doc)
    keywords = [kw for kw in keywords if is_meaningful(kw)]

    # Step 4️⃣ calculate semantic centre
    if not keywords:
        return []
    kw_emb = semantic_model.encode(keywords, convert_to_tensor=True)
    centroid = kw_emb.mean(dim=0, keepdim=True)

    # Step 5️⃣ calculate similarity of each word and the centre
    sims = util.cos_sim(kw_emb, centroid).flatten()
    filtered_keywords = [kw for kw, sim in zip(keywords, sims) if sim > 0.3]
    #new_add
    filtered_keywords = remove_overlapping_phrases(filtered_keywords,overlap_ratio=0.5)

    # Step 6️⃣ count the frequency in original text
    counts = Counter()
    for text in texts:
        t = text.lower()
        for kw in filtered_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", t):
                counts[kw] += 1

    results = [{"word": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)]
    return results


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

    
    relevant_texts = (
        df["clean_text"].dropna().astype(str)
        .loc[lambda s:s.str.contains(rf"\b{re.escape(brand_name)}\b",case=False,na=False)].tolist())

    if not relevant_texts:
        return {"brand": brand_name, "associated_words": []}

    associated_words = extract_clean_brand_keywords_auto(relevant_texts,brand_name, top_k=top_k)
    return {"brand": brand_name, "associated_words": associated_words}

