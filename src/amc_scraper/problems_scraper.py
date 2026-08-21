import time

import re
import json

from itertools import batched
from tqdm import tqdm
from bs4 import Tag


from concurrent.futures import ThreadPoolExecutor

from .utils import *
from .config import *
from .scraper import *

def get_problems_from_source(s,msg = True) :
    content,problem_title,url = get_soup(s,'p',msg)

    if content is None:
        print(f"Failed to get soup: {url}")
        return None
    
    problems_by_number = {}
    current_number = None

    sol_num = 0
    for child in content.children:
        if child.name == 'h2':
            headline = child.select_one('.mw-headline')
            match = re.match(PATTERN_HEADLINE_ID, headline.get('id', '')) if headline else None
            current_number = int(match.group(1)) if match else None
            continue

        if current_number is None:
            continue

        if re.search(r'>\s?Solution<', str(child)):
            sol_num+=1
            if sol_num<15 :
                continue
            else :
                break

        if isinstance(child, Tag) :
            if child.get('class') == 'wikitable' or child.get('id') in ['See_also','See_Also'] :
                break
            (problems_by_number.setdefault(current_number, [])
                                .append(str(child))
            )
        else :
            continue
    temp = re.search(PATTERN_VERSION,url)
    vers = temp.group(1) if (temp and temp.group(1)) else 'I'

    problems = []
    for number in sorted(problems_by_number):
        prob = dict()
        prob['source'] = url
        prob['version'] = vers
        prob['problem_number'] = number
        prob['problem_statement'] = ''.join(problems_by_number[number])
        problems.append(prob)
    return problems

def get_problems_full(contest,
                    save_json = False,
                    chunk_size = 5,
                    num = 15) :
    
    _,pairs = generate_all_and_pairs('p',contest)
    pairs = pairs[:min(num,len(pairs))]
    downloaded = check_retrieved_file('p',contest)

    problems = []
    
    bar = tqdm(list(enumerate(batched(pairs,chunk_size))),
                desc = 'Progress',
                unit = 'chunk',
                position = 0,
                leave = True)
    try :
        for i,chunk in bar :
            for year,source in chunk :
                probs = get_problems_from_source(source,msg = False)
                for prob in probs :
                    prob['year'] = year
                problems+=probs
                time.sleep(VSWAIT)
            time.sleep(SWAIT)
            bar.set_postfix(downloaded = f'{len(problems)}',
                            last_year = problems[-1]['year'],
                            last_version = problems[-1]['version'])
    except Exception as e :
        print_message(f'Error : {e}')
        if len(problems) > 0 :
            last = problems[-1]
            last_year = last["year"]
            text = last["source"]
            last_source = re.search(r'(.*?)_Problems$',text).group(1)
            print_message(f'Last Retrieved Data is {last_year}: {last_source}')
        else :
            print_message('No Data Retrieved')
    merged = downloaded + problems
    
    if save_json :
        OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
        file_path = OUTPUT_DIR / contest / PROBLEMS_FULL
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent = 4)

    return pairs,merged