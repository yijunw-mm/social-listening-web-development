from fastapi import APIRouter, Query
from typing import List, Optional,Literal
import pandas as pd
from collections import Counter
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

router = APIRouter()
df_cleaned = pd.read_csv("data/processing_output/cleaned_chat_nov_new.csv")

# load brand keywrod
brand_keyword_df = pd.read_csv("data/other_data/newest_brand_keywords.csv")  
brand_keyword_dict = brand_keyword_df.groupby("brand")["keyword"].apply(list).to_dict()

analyzer = SentimentIntensityAnalyzer()

@router.get("/brand/time-compare/frequency")
def compare_keyword_frequency(
    #group_id: Optional[str] = None,
    brand_name: str,
    granularity: Literal["year", "month", "quarter"],
    time1: int,
    time2: int
):
    df = df_cleaned.copy()
    #df = df[df["group_id"] == group_id]

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
        texts = df_subset["clean_text"].dropna().tolist()
        counter = Counter()
        for text in texts:
            for kw in keywords:
                if kw.lower() in text.lower():
                    counter[kw] += 1
        return dict(counter)

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
    time2:int
):
    df = df_cleaned.copy()
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
        return {
            "total_mentions": total,
            "sentiment_count": counts,
            "sentiment_percent": percent
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

