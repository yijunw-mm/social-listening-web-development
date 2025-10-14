from fastapi import APIRouter
from collections import defaultdict
from typing import List, Optional
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

router = APIRouter()
df_cleaned = pd.read_csv("data/processing_output/cleaned_chat_dataframe2.csv",dtype={"group_id":str})

df_cat = pd.read_csv("data/other_data/newest_brand_keywords.csv")
brand_category_map = {
    str(row["brand"]).strip().lower(): str(row["category"]).strip()
    for _, row in df_cat.iterrows()
}
brand_list = list(brand_category_map.keys())


@router.get("/category/share-of-voice")
def get_share_of_voice():
    df = df_cleaned.copy()

    category_counts = defaultdict(lambda:defaultdict(int))

    for text in df["clean_text"].dropna():
        text = text.lower()
        matched_brands = set()
        for brand in brand_list:
            if brand in text:
                matched_brands.add(brand)

        for brand in matched_brands:
            category = brand_category_map[brand]
            category_counts[category][brand] += 1

    # result
    result = {}
    for category, brand_counts in category_counts.items():
        total =sum(brand_counts.values())
        brand_percentage_list=[{
            "brand":brand,"percentage": round(count/total*100,1)}
            for brand, count in brand_counts.items()
        ]
        count_list =[
            {"brand":brand,"count":count} for brand, count in brand_counts.items()
        ]

        result[category]={
            "total_mentions": total,
            "share_of_voice": brand_percentage_list,
            "original_count": count_list
        }

    return result

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

category_brand_map=defaultdict(list)
for brand, cat in brand_category_map.items():
    category_brand_map[cat].append(brand)

#-----------------------------------------

brand_keyword_dict = df_cat.groupby("brand")["keyword"].apply(list).to_dict()
@router.get("/category/consumer-perception")
def category_consumer_perception(category_name:str, top_k:int=20, group_id:Optional[str]=None):
    brand_in_category = [b for b,c in brand_category_map.items() if c==category_name]
    if not brand_in_category:
        return {"error":f"category '{category_name}' not found"}
    df = df_cleaned.copy()
    if group_id:
        df = df[df["group_id"]==group_id]
    keywords=[]
    for brand in brand_in_category:
        keywords.extend(brand_keyword_dict.get(brand,[]))
        keywords=list(set([kw.lower() for kw in keywords]))
    def contains_category_keywords(text):
        return any(kw in text.lower() for kw in keywords)
    
    relevant_texts = df[df["clean_text"].apply(lambda x: isinstance(x, str) and contains_category_keywords(x))]["clean_text"].tolist()

    if not relevant_texts:
        return {"brand": category_name, 
                "associated_words": [],
                "share-of-voice":{}
                }

    associated_words = compute_co_occurrence_matrix(relevant_texts, top_k=top_k)
    share_counts=[]
    for brand in brand_in_category:
        brand_keywords = [kw.lower() for kw in brand_keyword_dict.get(brand,[])]
        brand_texts =[t for t in relevant_texts if any(kw in t.lower() for kw in brand_keywords)]
        share_counts.append({"brand":brand,"count":len(brand_texts)})
    return {"category": category_name, 
            "associated_words": associated_words,
            "share-of-voice":share_counts}