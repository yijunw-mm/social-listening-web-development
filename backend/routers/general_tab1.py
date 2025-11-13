from fastapi import APIRouter, Query
from typing import Optional, List 
import pandas as pd
from keybert import KeyBERT
from collections import Counter
import sys 
sys.path.append("..")
from backend.model_loader import kw_model,encoder
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from backend.data_loader import load_chat_data

router = APIRouter()
#kw_model = KeyBERT(model='all-MiniLM-L6-v2')

# load data
#df_chat = pd.read_csv("data/processing_output/clean_chat_df/2025/cleaned_chat_dataframe.csv",dtype={"group_id":str})
df_chat= load_chat_data()
df_kw = pd.read_csv("data/other_data/general_kw_list.csv")
keyword_list = df_kw['keywords'].tolist()
df_stage= pd.read_csv("data/processing_output/groups.csv",dtype={"group_id":str})

@router.get("/keyword-frequency")
def keyword_frequency(group_id: Optional[List[str]] = Query(None),
                      stage: Optional[str]=None,
                      year: Optional[int] = None,
                      month: Optional[List[int]] = Query(None),
                      quarter: Optional[int] = None):
    df = df_chat
    if group_id:
        df = df[df["group_id"].isin(group_id)]
    if stage:
        stage_group_ids= df_stage[df_stage['stage']==stage]["group_id"].tolist()
        df = df[df["group_id"].isin(stage_group_ids)]
    if year:
        df = df[df["year"]== year]
    if month:
        df = df[df["month"].isin(month)]
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
                           top_k: int = 10):
    batch_size =100
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
    max_docs = 5000
    if len(texts)>max_docs:
        random.seed(42)
        texts = random.sample(texts,max_docs)
    encoder.encode(["warmup"], show_progress_bar=False)
    all_keywords=[]
    def process_chunk(start):
        chunk_text =" ".join(texts[start:start+batch_size])
        try:
            keywords = kw_model.extract_keywords(chunk_text, keyphrase_ngram_range=(1, 2),
                                                 stop_words='english', top_n=10,
                                                 use_mmr=True, diversity=0.6)
            return keywords
        except Exception as e:
            print(f"error in batch {start//batch_size}: {e}")
            return []

    with ThreadPoolExecutor(max_workers=4) as executor:  # 🚀 并行4线程
        futures = [executor.submit(process_chunk, i) for i in range(0, len(texts), batch_size)]
        for f in as_completed(futures):
            all_keywords.extend(f.result())

            

    keyword_score_map={}
    for kw,score in all_keywords:
        if kw not in keyword_list:
            if kw not in keyword_score_map or score >keyword_score_map[kw]:
                keyword_score_map[kw]=score
    new_keywords_sorted = sorted(keyword_score_map.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    return [{"keyword": kw, "score": score} for kw, score in new_keywords_sorted]



@router.get("/chat-number")
def get_groups():
    groups = df_stage['group_id'].unique().tolist()
    result = [{'id':gid} for gid in groups]
    return{
        "total":len(groups),
        "groups":result
    }
