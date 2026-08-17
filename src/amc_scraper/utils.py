import re
import json
from pathlib import Path
import os
from tqdm import tqdm
import pandas as pd

from .config import *

def print_message(msg, end = '\n') :
    n = len(msg)
    nsym = (98-n)//2
    print(f"{'='*nsym} {msg} {'='*nsym}",end = end)

def wait_for_visible_count(locator, min_count):
    def check(d):
        visible = [el for el in d.find_elements(*locator) if el.is_displayed()]
        return visible if len(visible) >= min_count else False
    return check

def check_retrieved_file(type,contest) :
    if type == 'a' :
        filename = ANSWERS_FULL
    elif type == 'p' :
        filename = PROBLEMS_FULL
    else :
        filename = SOLUTIONS_FULL
        
    (OUTPUT_DIR / contest).mkdir(parents=True,exist_ok=True)
    files = os.listdir(OUTPUT_DIR / contest)
    if filename in files :
        file_path = OUTPUT_DIR / contest / filename
        with open(file_path, "r",encoding='utf-8') as file:
            if file_path.stat().st_size > 0:
                return json.load(file)
            else :
                return []
    else :
        return []

def generate_all_and_pairs(type,contest) :
    filepath = DATA_PATH / contest / CONTEST_METADATA_NAME
    if filepath.is_file() and filepath.stat().st_size > 0:
        with open(filepath, 'r', encoding = 'utf-8') as f :
            contest_metadata = json.load(f)
    else :
        print_message("Metadata Not Retrieved Yet")

    all = []
    for id,record in contest_metadata.items() :
        all.append((record['year'],record['source']))

    if type == 'p' :
        pattern = r'(.*?)_Problems$'
    elif type == 'a' :
        pattern = r'(.*?)_Answer_Key$'
    else :
        pattern = r'(.*?)_Problems/'

    downloaded = check_retrieved_file(type,contest)
    if len(downloaded) == 0 :
        pairs = all
    else :
        df = pd.DataFrame(downloaded)[['year','source']]
        df['source'] = df['source'].map(lambda x:re.search(pattern,x).group(1))
        df = df.drop_duplicates(ignore_index=True)
        d = set()
        for i in range(len(df)) :
            d.add((df.loc[i,'year'],df.loc[i,'source']))

        pairs = list(set(all)-set(d))
    return all,pairs