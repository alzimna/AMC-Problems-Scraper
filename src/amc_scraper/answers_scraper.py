import time

import re
import json

from itertools import batched
from tqdm import tqdm

from concurrent.futures import ThreadPoolExecutor

from .utils import *
from .config import *
from .scraper import *

def get_answers_from_url(s,vers,numprob,msg = True) :
    content,problem_title,url = get_soup(s,'a',msg)
    
    if content is None:
        print(f"Failed to get soup: {url}")
        return None
    
    ol_elem = content.find('ol')
    li_list = ol_elem.find_all('li')


    if(len(li_list)>=numprob and msg):
        print_message(f"{problem_title} Answer Key Retrieved")

    answers = []
    for number,answer in enumerate(li_list):
        ans = dict()
        ans['source'] = url
        ans['version'] = vers
        ans['problem_number'] = number+1
        ans['answer'] = answer.decode_contents()
        answers.append(ans)
    return answers 

def get_answers_full(contest,
                    save_json = False,
                    chunk_size = 5) :
    _,pairs = generate_all_and_pairs('a',contest)
    downloaded = check_retrieved_file('a',contest)
    answers = []

    bar = tqdm(list(enumerate(batched(pairs,chunk_size))),
                desc = 'Progress',
                unit = 'chunk',
                position = 0,
                leave = True)
    try :
        for i,chunk in bar :
            with ThreadPoolExecutor(max_workers=chunk_size) as pool:
                records = pool.map(lambda p : get_answers_from_url(p[1],p[2],p[3],msg = False), chunk)
                for p,l in zip(chunk,records) :
                    for ans in l :
                        ans['year'] = p[0]
                    answers+=l
            time.sleep(SWAIT)
            bar.set_postfix(downloaded = f'{len(answers)}',
                            last_year = answers[-1]['year'],
                            last_version = answers[-1]['version'])
    except Exception as e :
        print_message(f'Error : {e}')
        if len(answers) > 0 :
            last = answers[-1]
            last_year = last["year"]

            text = last["source"]
            last_source = re.search(r'(.*?)_Answer_Key$',text).group(1)
            print_message(f'Last Retrieved Data is {last_year}: {last_source}')
        else :
            print_message('No Data Retrieved')

    merged = downloaded + answers
    if save_json :
        OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
        file_path = OUTPUT_DIR / contest / ANSWERS_FULL
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=True, indent = 4)

    return pairs,merged