import zipfile
import io
from io import TextIOWrapper
import os
import re
import pandas as pd
from typing import Tuple, List
from datetime import datetime
import calendar


def extract_group_name(file_name: str) -> str:
    """
    from zip file name extract group ID, e.g. 2025 DEC SG Mummys
    """
    match = re.search(r"WhatsApp Chat - ([\w\s]+)", file_name)
    if match:
        return match.group(1).strip()
    return file_name.replace(".zip", "")

def read_zip_and_extract_txt(zip_path: str) -> Tuple[str, str]:
    """
    unzip file, extract the first txt file content, and return (group_id, chat_text)
    """
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # find the first txt file 
        txt_files = [name for name in zip_ref.namelist() if name.endswith(".txt")]
        if not txt_files:
            raise ValueError("Zip file does not contain any .txt file.")
        first_txt = txt_files[0]
        with zip_ref.open(first_txt) as file:
            chat_text = TextIOWrapper(file,encoding='utf-8').readlines()
            #chat_text = file.read().decode("utf-8")

    group_name = extract_group_name(os.path.basename(zip_path))
    return group_name, chat_text

#--get group id
def normalize_group_id(group_name):
    """2025 DEC Mummys->202512"""
    match = re.match(r"(\d{4})\s+([A-Za-z]+)", group_name.strip())
    if not match:
        return None
    year = int(match.group(1))
    month_str = match.group(2).title() #DEC->Dec
    if month_str not in calendar.month_abbr:
        return None
    month = list(calendar.month_abbr).index(month_str)  # DEC->12
    return f"{year}{month:02d}"

def parse_txt_lines(lines, group_name):
    pattern = re.compile(r"\[(.*?)\]\s*~\s*(.*?):\s*(.*)")
    records = []
    norm_id = normalize_group_id(group_name)
    for line in lines:
        
        match = pattern.match(line)
        if match:
            dt_str, user, message = match.groups()
            dt = datetime.strptime(dt_str, "%d/%m/%y, %H:%M:%S")
            if re.search(r"your security code with .*? changed", message.lower()):
                continue 
            if str(user).strip().lower() in str(message).strip().lower():
                continue
            records.append({"datetime": dt, "user": user.strip(), "group_id":str(norm_id),
                            "text": message.strip(),"group_name":group_name})
            
    return records


def process_multiple_zips(folder_path: str) -> List[Tuple[str,str]]:
    """process all zips, return a whole dataframe"""
    all_records = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".zip"):
            path = os.path.join(folder_path,filename)
            try:
                group_id,chat_text = read_zip_and_extract_txt(path)
                records = parse_txt_lines(chat_text,group_id) 
                all_records.extend(records)
                print(f"process {filename}:{len(records)} messages")
            except Exception as e:
                print(f"Error processing {filename}:{e}")
    df = pd.DataFrame(all_records)
    df['group_id'] = df['group_id'].astype(str)
    return df

# test
if __name__ == "__main__":
    folder = "data/chat_zip"
    df_chats = process_multiple_zips(folder)
    print(f"✅ Load {len(df_chats)} chats.")
    #print("📄 Chat text preview:\n", all_chats[0][0],all_chats[0][1][:300])  

df_chats = process_multiple_zips("data/chat_zip")

output_path = "data/processing_output/structured_chat2.csv"
df_chats.to_csv(output_path,index=False)
print(f"save to {output_path}")
