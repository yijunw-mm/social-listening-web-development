from fastapi import APIRouter, Query
from typing import Optional
import pandas as pd
from keybert import KeyBERT
from collections import Counter

router = APIRouter()
kw_model = KeyBERT(model='all-MiniLM-L6-v2')

# load data
df_chat = pd.read_csv("data/processing_output/cleaned_chat_df_dec.csv")
df_kw = pd.read_csv("data/other_data/general_kw_list.csv")
keyword_list = df_kw['keywords'].tolist()


@router.get("/keyword-frequency")
def keyword_frequency(group_id: Optional[str] = None,
                      year: Optional[int] = None,
                      month: Optional[int] = None,
                      quarter: Optional[int] = None):
    df = df_chat
    if group_id:
        df = df[df["group_id"] == group_id]
    if year:
        df = df[df["year"]== year]
    if month:
        df = df[df["month"]== month]
    if quarter:
        df = df[df["quarter"]== quarter]
    
    all_text = " ".join(df["clean_text"].dropna().astype(str).tolist())
    word_list = all_text.split()
    keyword_counts = Counter([word for word in word_list if word in keyword_list])
    
    return [{"keyword": k, "count": v} for k, v in keyword_counts.items()]


@router.get("/new-keyword-prediction")
def new_keyword_prediction(group_id: Optional[str] = None,
                           year: Optional[int]=None,
                           month: Optional[int] = None,
                           quarter: Optional[int] = None,
                           top_k: int = 20):
    batch_size =200
    df = df_chat
    if group_id:
        df = df[df["group_id"] == group_id]
    if year:
        df = df[df["year"]== year]
    if month:
        df = df[df["month"]== month]
    if quarter:
        df = df[df["quarter"]== quarter]

    texts = df["clean_text"].dropna().astype(str).tolist()
    all_keywords=[]
    for i in range(0,len(texts),batch_size):
        chunk = texts[i:i+batch_size]
        chunk_text =" ".join(chunk)
        try:
            keywords = kw_model.extract_keywords(chunk_text, keyphrase_ngram_range=(1, 2),
                                                 stop_words='english', top_n=15,
                                                 use_mmr=True, diversity=0.6)
            
            all_keywords.extend(keywords)
        except Exception as e:
            print(f"error in batch {i//batch_size}:{e}")

    keyword_score_map={}
    for kw,score in all_keywords:
        if kw not in keyword_list:
            if kw not in keyword_score_map or score >keyword_score_map[kw]:
                keyword_score_map[kw]=score
    new_keywords_sorted = sorted(keyword_score_map.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    return [{"keyword": kw, "score": score} for kw, score in new_keywords_sorted]



