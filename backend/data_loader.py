import pandas as pd
from functools import lru_cache

@lru_cache(maxsize=1)
def load_chat_data():
    print("load data into memory...")
    df=pd.read_parquet("data/processing_output/clean_chat_df/2025/cleaned_chat_dataframe.parquet")
    df["clean_text"] = df["clean_text"].fillna("").astype(str)
    return df 