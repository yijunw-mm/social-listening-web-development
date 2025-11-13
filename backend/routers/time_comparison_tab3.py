from fastapi import APIRouter, Query
from typing import List, Optional,Literal
import pandas as pd
from collections import Counter, defaultdict
import json
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from backend.data_loader import load_chat_data

router = APIRouter()
#df_cleaned = pd.read_csv("data/processing_output/clean_chat_df/2025/cleaned_chat_dataframe.csv",dtype={"group_id":str})
df_cleaned = load_chat_data()
df_cleaned['clean_text']=(df_cleaned['clean_text'].str.replace(r"\s+'s","'s",regex=True))
# load brand keywrod
brand_keyword_df = pd.read_csv("data/other_data/newest_brand_keywords.csv",keep_default_na=False,na_values=[""])  
brand_keyword_dict = brand_keyword_df.groupby("brand")["keyword"].apply(list).to_dict()

analyzer = SentimentIntensityAnalyzer()

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

@router.get("/brand/time-compare/frequency")
def compare_keyword_frequency(
    brand_name: str,
    granularity: Literal["year", "month", "quarter"],
    time1: int,
    time2: int,
    group_id: Optional[List[str]] = Query(None),
    window_size: int =6,
    merge_overlap:bool=True
):
    df = df_cleaned.copy()
    if group_id:
        df = df[df["group_id"].isin(group_id)]

    if brand_name not in brand_keyword_dict:
        return {"error": f"Brand '{brand_name}' not found."}
    keywords = brand_keyword_dict[brand_name]

    def filter_df(df: pd.DataFrame, time: int):
        if granularity == "year":
            return df[df["year"] == time]
        elif granularity == "month":
            y, m = divmod(time, 100)
            return df[(df["year"] == y) & (df["month"] == m)]
        elif granularity == "quarter":
            y, q = divmod(time, 10)
            return df[(df["year"] == y) & (df["quarter"] == q)]



    def count_keywords(df_subset):
        #texts = df_subset["clean_text"].dropna().tolist()
        contexts = extract_brand_context(
            df_subset,
            brand=brand_name,
            brand_keyword_map=brand_keyword_dict,
            window_size=window_size,
            merge_overlap=merge_overlap
        )
        if not contexts:
            return {"error":f"No mention about brand {brand_name}"}
        
        context_texts = []
        for c in contexts:
            context_texts.extend(t for t in c["context"] if isinstance(t,str))
        #counter = Counter()
        freq_counter = Counter()

        for text in context_texts:
            words = re.findall(r"\w+",text.lower())
            if not isinstance(text, str):
                return {}
            for kw in keywords:
                if kw.lower() in words:
                    freq_counter[kw] += 1
        if not freq_counter:
            all_words = " ".join(context_texts).split()
            filtered_words = [w for w in all_words if w.isalpha() and len(w)>2]
            counter = Counter(filtered_words)
            top_fallback = [{"keyword":w, "count":c} for w, c in counter.most_common(5)]
            return top_fallback
        #convert to list
        #return dict(counter)
        return [{"keyword":k,"count":v} for k,v in freq_counter.items()]

    return {
        "brand": brand_name,
        "granularity": granularity,
        "compare": {
            str(time1): count_keywords(filter_df(df, time1)),
            str(time2): count_keywords(filter_df(df, time2))
        }
    }

#-------sentiment analysis------
with open ("data/other_data/rule.json","r",encoding="utf-8") as f:
    CONFIG =json.load(f)['rules']
analyzer = SentimentIntensityAnalyzer()

def custom_rules(text, base_score):
    compound = base_score["compound"]
    t = text.lower()
    applied = None

    for rule in CONFIG:
        for pattern in rule["patterns"]:
            if re.search(pattern, t,re.IGNORECASE):
                compound = max(-1.0, min(1.0, compound + rule["adjustment"]))
                applied =rule['name']
                break  # stop at first match
        if applied: 
            break

    if compound >= 0.05:
        sentiment = "positive"
    elif compound <= -0.05:
        sentiment = "negative"
    else:
        sentiment = "neutral"


    return {"compound": compound, "sentiment": sentiment, "rule":applied}

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

    return {"positives": positives, "negatives": negatives}

@router.get("/brand/time-compare/sentiment")
def keyword_frequency(
    brand_name: str,
    granularity:Literal["year","month","quarter"],
    time1:int,
    time2:int,
    group_id: Optional[List[str]]=Query(None),
):
    df = df_cleaned.copy()
    if group_id:
        df = df[df["group_id"].isin(group_id)]
    if brand_name not in brand_keyword_dict:
        return {"error": f"Brand '{brand_name}' not found."}
    #keywords = brand_keyword_dict[brand_name]


    # 4. compute sentiment analysis
    def analyze_sentiment(texts):
        sentiment_result = {"positive": 0, "neutral": 0, "negative": 0}
        detailed_examples= []
        for text in texts:
            base = analyzer.polarity_scores(text)
            adjusted = custom_rules(text,base)
            sentiment_result[adjusted["sentiment"]]+=1
            
            # 4.5 explain the contribution
            explanation = explain_sentiment(text, top_n=5)
            detailed_examples.append({
                "text": text,
                "sentiment_score": adjusted["compound"],
                "sentiment":adjusted["sentiment"],
                "rule_applied":adjusted["rule"],
                "top_positive_words": explanation["positives"],
                "top_negative_words": explanation["negatives"]
            })
        return sentiment_result,detailed_examples


    def filter_df(df: pd.DataFrame, time: int, granularity: str):
        if granularity == "year":
            return df[df["year"] == time]
        elif granularity == "month":
            year, month = divmod(time, 100)  # 202508 → 2025, 8
            return df[(df["year"] == year) & (df["month"] == month)]
        elif granularity == "quarter":
            year, q = divmod(time, 10)       # 20252 → 2025, Q2
            return df[(df["year"] == year) & (df["quarter"] == q)]
        else:
            raise ValueError("Invalid granularity")
        
        #anlyze one subset
    df1 = filter_df(df, time1, granularity)
    df2 = filter_df(df, time2, granularity)
    # 3. get the message containing brand name
    pattern = re.compile(rf"\b{re.escape(brand_name)}\b",re.IGNORECASE)
    text1 = [t for t in df1["clean_text"].dropna() if pattern.search(t)]
    text2 = [t for t in df2["clean_text"].dropna() if pattern.search(t)]
    sentiment_result1, detailed_examples1 = analyze_sentiment(text1)
    sentiment_result2, detailed_examples2 = analyze_sentiment(text2)

    total_mentions1 = len(text1)
    total_mentions2 = len(text2)

    sentiment_percent_list1 = [{
        "sentiment":k,"value": round(v / total_mentions1 * 100, 1)} for k, v in sentiment_result1.items()
    ]
    sentiment_count_list1 =[
        {"sentiment":k, "value":v} for k,v in sentiment_result1.items()
    ]

    sentiment_percent_list2 = [{
        "sentiment":k,"value": round(v / total_mentions2 * 100, 1)} for k, v in sentiment_result2.items()
    ]
    sentiment_count_list2 =[
        {"sentiment":k, "value":v} for k,v in sentiment_result2.items()
    ]
    return {
        "brand": brand_name,
        "granularity": granularity,
        "compare": {
            str(time1): {
                "total_mentions": total_mentions1,
                "sentiment_percent": sentiment_percent_list1,
                "sentiment_count": sentiment_count_list1,
                "examples": detailed_examples1[:5]
            },
            str(time2): {
                "total_mentions": total_mentions2,
                "sentiment_percent": sentiment_percent_list2,
                "sentiment_count": sentiment_count_list2,
                "examples": detailed_examples2[:5]
            }
        }

    }


def _normalize_quotes(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return (
        s.replace("’", "'")
         .replace("‘", "'")
         .replace("`", "'")
         .lower()
         .replace("'", "")
         .strip()
    )


def _build_keyword_pattern(kw: str) -> re.Pattern:
    k = _normalize_quotes(kw)
    k = re.escape(k)
    
    k = k.replace(r"\-", r"(?:-|\\s)")
    
    k = k.replace(r"\ ", r"\s+")
    return re.compile(rf"(?<!\w){k}(?!\w)", flags=re.IGNORECASE)


def count_kw(context_texts, keywords):
    patterns = {kw: _build_keyword_pattern(kw) for kw in keywords}
    cnt = Counter()
    for text in context_texts:
        t = _normalize_quotes(text)
        for kw, patt in patterns.items():
            if patt.search(t):
                cnt[kw] += 1
    return cnt


#------share of voice--------
@router.get("/category/time-compare/share-of-voice")
def category_share_of_voice_compare(
    category_name: str,
    granularity: Literal["year", "month", "quarter"],
    time1: int,
    time2: int,
    group_id: Optional[List[str]]=Query(None),
):
    #find the category
    df_cat = pd.read_csv("data/other_data/newest_brand_keywords.csv")
    brand_category_map = {
    str(row["brand"]).strip().lower(): str(row["category"]).strip()
    for _, row in df_cat.iterrows()
    }

    brand_in_category = [b for b, c in brand_category_map.items() if c == category_name]
    if not brand_in_category:
        return {"error": f"category '{category_name}' not found"}

    df = df_cleaned.copy()
    if group_id:
        df = df[df["group_id"].isin(group_id)]


    def filter_df(df: pd.DataFrame, time: int):
        if granularity == "year":
            return df[df["year"] == time]
        elif granularity == "month":
            y, m = divmod(time, 100)   # 202508 → 2025, 8
            return df[(df["year"] == y) & (df["month"] == m)]
        elif granularity == "quarter":
            y, q = divmod(time, 10)    # 20252 → 2025, Q2
            return df[(df["year"] == y) & (df["quarter"] == q)]
        else:
            raise ValueError("Invalid granularity")


    # --- count share of voice ---
    def compute_share(df_subset):
        if df_subset.empty:
            return {"total_mentions": 0, "share_of_voice": []}
        counts = count_kw(df_subset["clean_text"].dropna(), brand_in_category)

        total = sum(counts.values())
        share_list = [
            {"brand": b, "count": c, "percent": round(c / total * 100, 1) if total > 0 else 0}
            for b, c in counts.items()
        ]
        return {"total_mentions": total, "share_of_voice": share_list}



    #analyze two time periods
    df1 = filter_df(df, time1)
    df2 = filter_df(df, time2)


    result = {
        "category": category_name,
        "granularity": granularity,
        "compare": {
            str(time1): compute_share(df1),
            str(time2): compute_share(df2)
        }
    }
    return result
