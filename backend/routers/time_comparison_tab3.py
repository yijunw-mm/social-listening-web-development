from fastapi import APIRouter, Query
from typing import List, Optional,Literal
import pandas as pd
from collections import Counter, defaultdict
import json
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

router = APIRouter()
df_cleaned = pd.read_csv("data/processing_output/cleaned_chat_dataframe2.csv",dtype={"group_id":str})
df_cleaned['clean_text']=(df_cleaned['clean_text'].str.replace(r"\s+'s","'s",regex=True))
# load brand keywrod
brand_keyword_df = pd.read_csv("data/other_data/newest_brand_keywords.csv")  
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
    window_size: int =3,
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
            context_texts.extend(c["context"])
        counter = Counter()
        freq_counter = Counter()

        for text in context_texts:
            words = re.findall(r"\w+",text.lower())
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
        return [{"keyword":k,"count":v} for k,v in counter.items()]

    return {
        "brand": brand_name,
        "granularity": granularity,
        "compare": {
            str(time1): count_keywords(filter_df(df, time1)),
            str(time2): count_keywords(filter_df(df, time2))
        }
    }


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
        return {"error": f"Brand '{brand_name}' not found in keyword dictionary."}
    keywords = brand_keyword_dict[brand_name]

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
    def analyze_sentiment(df_subset: pd.DataFrame, keywords: list):
        texts = df_subset["clean_text"].dropna().tolist()
        matched = [t for t in texts if any(kw.lower() in t.lower() for kw in keywords)]
        counts = {"positive": 0, "neutral": 0, "negative": 0}
        for text in matched:
            score = analyzer.polarity_scores(text)["compound"]
            if score >= 0.05:
                counts["positive"] += 1
            elif score <= -0.05:
                counts["negative"] += 1
            else:
                counts["neutral"] += 1
        total = sum(counts.values())
        percent = {k: round(v / total * 100, 1) if total > 0 else 0 for k, v in counts.items()}
        count_list=[{"sentiment":k,"count":v,"percentage":percent[k]} for k,v in counts.items()]
        return {
            "total_mentions": total,
            "sentiment_detail":count_list
        }

    # 5. analyze two time periods
    df1 = filter_df(df, time1, granularity)
    df2 = filter_df(df, time2, granularity)

    result = {
        str(time1): analyze_sentiment(df1, keywords),
        str(time2): analyze_sentiment(df2, keywords)
    }

    return {
        "brand": brand_name,
        "granularity": granularity,
        "compare": result
    }

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
        category_counts = defaultdict(lambda: defaultdict(int))
        for text in df_subset["clean_text"].dropna():
            text = text.lower()
            matched_brands = set()
            for brand in brand_in_category:
                pattern = re.compile(rf"\b{re.escape(brand)}\b")  # 避免 nan 命中 nanny
                if pattern.search(text):
                    matched_brands.add(brand)
            for brand in matched_brands:
                category = brand_category_map[brand]
                category_counts[category][brand] += 1

        result = {}
        for category, brand_counts in category_counts.items():
            total = sum(brand_counts.values())
            share_list = [
                {"brand": b, "count": c, "percent": round(c / total * 100, 1) if total > 0 else 0}
                for b, c in brand_counts.items()
            ]
            result[category] = {"total_mentions": total, "share_of_voice": share_list}
        return result.get(category_name, {"total_mentions": 0, "share_of_voice": []})


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
