from fastapi import APIRouter, Query
from collections import defaultdict,Counter
from typing import List, Optional
import pandas as pd
import re
from sklearn.feature_extraction.text import CountVectorizer
from keybert import KeyBERT
from backend.model_loader import kw_model,encoder
from sentence_transformers import SentenceTransformer, util 
import spacy
from backend.data_loader import load_chat_data

router = APIRouter()
df_cleaned = load_chat_data()
df_cleaned['clean_text']=(df_cleaned['clean_text'].str.replace(r"\s+'s","'s",regex=True))
df_cat = pd.read_csv("data/other_data/newest_brand_keywords.csv")
brand_category_map = defaultdict(list)
for _,row in df_cat.iterrows():
    brand = str(row["brand"]).strip().lower()
    category = str(row["category"]).split(",")[0].strip().lower()
    brand_category_map[brand].append(category)

brand_list = list(brand_category_map.keys())


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


# ---------------- share of voice API ----------------
@router.get("/category/share-of-voice")
def get_share_of_voice(group_id:Optional[List[str]]=Query(None)):
    df = df_cleaned.copy()
    if group_id:
        df = df[df["group_id"].isin(group_id)]

    # 1. count brand frequency
    counts = count_kw(df["clean_text"].dropna(), brand_list)

    # 2.map to category
    category_counts = defaultdict(dict)
    for brand, count in counts.items():
        categories = brand_category_map.get(brand, [])
        for category in categories:
            category_counts[category][brand] = count


    result = {}
    for category, brand_counts in category_counts.items():
        total = sum(brand_counts.values())
        result[category] = {
            "total_mentions": total,
            "share_of_voice": [
                {"brand": b, "percentage": round(c / total * 100, 1)}
                for b, c in brand_counts.items()
            ],
            "original_count": [
                {"brand": b, "count": c} for b, c in brand_counts.items()
            ]
        }


    return result

#-------consumer perception----------

nlp = spacy.load("en_core_web_sm")
#semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
#kw_model = KeyBERT(model='all-MiniLM-L6-v2')

def _overlap_fraction(a, b):
    """calculate the overlap percentage between two phrases token"""
    set_a, set_b = set(a.split()), set(b.split())
    if not set_a or not set_b:
        return 0
    return len(set_a & set_b) / min(len(set_a), len(set_b))

def remove_overlapping_phrases(keywords, overlap_ratio=0.6):
    """
    remove the overlap part（like "sensitive skin" vs "kids sensitive skin"）。
    overlap_ratio: 0.6。
    """
    cleaned = []
    for kw in sorted(keywords, key=len, reverse=True):  # from long to short
        if not any(_overlap_fraction(kw, c) > overlap_ratio for c in cleaned):
            cleaned.append(kw)
    return cleaned[::-1]  # keep the original order

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

    docs = list(nlp.pipe(keywords, disable=["ner"]))
    keywords = [kw for kw, doc in zip(keywords, docs)
                if any(t.pos_ in ["ADJ", "NOUN"] for t in doc)]

    if not keywords:
        return []

    kw_emb = encoder.encode(keywords, convert_to_tensor=True)
    centroid = kw_emb.mean(dim=0, keepdim=True)
    sims = util.cos_sim(kw_emb, centroid).flatten()
    filtered_keywords = [kw for kw, sim in zip(keywords, sims) if sim > 0.3]
    filtered_keywords = remove_overlapping_phrases(filtered_keywords, overlap_ratio=0.5)

    counts = Counter()
    for text in texts:
        t = text.lower()
        for kw in filtered_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", t):
                counts[kw] += 1

    results = [{"word": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)]
    return results



category_brand_map=defaultdict(list)
for brand, cats in brand_category_map.items():
    for cat in cats:
        category_brand_map[cat].append(brand)

#-----------------------------------------

brand_keyword_dict = df_cat.groupby("brand")["keyword"].apply(list).to_dict()
@router.get("/category/consumer-perception")
def category_consumer_perception(category_name:str, 
                                 top_k:int=20, 
                                 group_id:Optional[List[str]]=Query(None)):
    brand_in_category = [b for b,cats in brand_category_map.items() if category_name in cats]
    if not brand_in_category:
        return {"error":f"category '{category_name}' not found"}
    
    df = df_cleaned
    if group_id:
        df = df[df["group_id"].isin(group_id)]
    df = df_cleaned.copy()
    #  extract brand name relevant text
    pattern = "|".join([rf"\b{re.escape(b)}\b" for b in brand_in_category])
    relevant_texts = (
        df["clean_text"]
        .dropna()
        .astype(str)
        .loc[lambda s: s.str.contains(pattern, case=False, na=False)]
        .tolist()
    )

    if not relevant_texts:
        return {
            "category": category_name,
            "associated_words": []
        }

    # Step 4️⃣ extract keyword
    associated_words = extract_clean_brand_keywords_auto(
        relevant_texts,
        brand_name="",  
        top_k=top_k
    )

    # Step 6️⃣ print result
    return {
        "category": category_name,
        "associated_words": associated_words
    }
