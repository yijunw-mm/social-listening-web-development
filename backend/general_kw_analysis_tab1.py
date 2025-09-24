import pandas as pd
from collections import Counter
from typing import Dict, List,Optional
import matplotlib.pyplot as plt
from keybert import KeyBERT


def keyword_frequency(df: pd.DataFrame, 
                      keyword_list: List[str], 
                      group_id: Optional[str] = None,
                      month: Optional[int] = None,
                      quarter: Optional[int] = None) -> pd.DataFrame:
    """
    Compute frequency of predefined general keywords from group_id,month or quarter
    """
    if group_id:
        df = df[df["group_id"] == group_id]
    if month:
        df = df[df["month"]== month]
    if quarter:
        df = df[df["quarter"]== quarter]
    all_text = " ".join(df["clean_text"].dropna().astype(str).tolist())
    word_list = all_text.split()

    keyword_counts = Counter([word for word in word_list if word in keyword_list])
    freq_df = pd.DataFrame(keyword_counts.items(), columns=["keyword", "count"]).sort_values(by="count", ascending=False)

    return freq_df

# predict new keyword
kw_model = KeyBERT(model='all-MiniLM-L6-v2')

def new_keyword_prediction(df: pd.DataFrame, keyword_list: List[str], 
                           group_id: Optional[str] = None,
                           month: Optional[int] = None,
                           quarter: Optional[int] = None,
                            top_k: int = 20) -> pd.DataFrame:
    """
    Predict new keywords using KeyBERT that are not in the existing keyword_list.
    """
    if group_id:
        df = df[df["group_id"] == group_id]
    if month:
        df = df[df["month"]== month]
    if quarter:
        df = df[df["quarter"]== quarter]

    all_text = " ".join(df["clean_text"].dropna().astype(str).tolist())

    # extract keyword using keybert
    keywords = kw_model.extract_keywords(all_text, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=20,
                                         use_mmr=True, diversity=0.6)


    # keep the new keywords that are not in original list
    new_keywords = [(kw, score) for kw, score in keywords if kw not in keyword_list]
    new_df = pd.DataFrame(new_keywords, columns=["keyword", "score"]).sort_values(by="score",ascending=False).head(top_k)

    return new_df

def plot_keyword_bar(freq_df:pd.DataFrame, title:str="Keyword Frequency"):
    """plot a bar chart"""
    if freq_df.empty:
        print("No data to plot!")
        return
    plt.bar(freq_df['keyword'],freq_df['count'])
    plt.xticks(ticks=range(len(freq_df['count'])),labels=freq_df['keyword'],rotation=45,ha='right')
    plt.title(title)
    #plt.gca().set_facecolor('#111111')
    plt.xlabel("Keyword")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.show() 

def plot_new_keyword_bar(new_keyword_df:pd.DataFrame, top_k=20, title:str="New Keyword Distribution"):
    """plot a bar chart of new keyword"""
    df_top = new_keyword_df.sort_values("score",ascending=False).head(top_k)
    plt.bar(df_top['keyword'],df_top['score'])
    plt.xticks(ticks=range(len(df_top)),labels=df_top['keyword'],rotation=45,ha='right')
    plt.title(title)
    #plt.gca().set_facecolor('#111111')
    plt.xlabel("Keyword")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.show() 

if __name__ =="__main__":
    df_chat= pd.read_csv("data/processing_output/cleaned_chat_df_dec.csv")
    df_kw = pd.read_csv("data/other_data/general_kw_list.csv")

    keyword_list = df_kw['keywords'].tolist()

    general_freq_df = keyword_frequency(df_chat,keyword_list)
    plot_keyword_bar(general_freq_df)
    new_kw_df=new_keyword_prediction(df_chat, keyword_list, top_k=20)
    plot_new_keyword_bar(new_kw_df)
    print(new_kw_df)