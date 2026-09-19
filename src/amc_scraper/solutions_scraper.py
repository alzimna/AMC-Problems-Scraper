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

def video_condition(tag) :
    if tag.name in ['h2','h3'] :
        if len(tag.find_all('span')) > 0 :
            for child in tag.children :
                x = child.get('id','').lower()
                cek = ['video','mathtalks','megamath']
                for c in cek :
                    if c in x :
                        return True
        return False
    
    if tag.name in ['p','ul'] :
        if tag.find_all('a') == 0 :
            return False

        links = tag.find_all('a')
        for temp in links :            
            if temp.name == 'a' :
                cek = ['youtu','acad','bilibili','euclideanmathcircle']
                x = temp.get('href','')
                for c in cek :
                    if c in x :
                        return True
    return False


def get_solutions_from_page(source,numprob,number) :
    s = rf"{source}_Problems/Problem_{number}"
    content = get_soup(s,'s',numprob)

    if content is None:
        raise Exception(f'Failed to get soup: {s}')

    solutions_by_number = {}
    current_number = None
    for child in content.children :
        if child.name is None :
            continue

        if re.match('^h',child.name) :
            headline = child.select_one('.mw-headline')
            match = re.match(PATTERN_SOLUTION_ID, headline.get('id', '')) if headline else None
            if match :
                if current_number == None :
                        current_number = 1
                else :
                    current_number+=1
                solutions_by_number.setdefault(f"solution_{current_number}",{})
                solutions_by_number[f"solution_{current_number}"]['content'] = ""
                solutions_by_number[f"solution_{current_number}"]['headline'] = headline.text
                continue
            
        if current_number is None:
            continue

        if not isinstance(child, Tag):
            continue

        if re.match(r'^~',child.text) :
            continue

        if video_condition(child) :
            break
        
        if "wikitable" in (child.get("class") or []):
            break

        span = child.find("span")
        if span is not None and span.get("id", "").lower() == "see_also":
            break

        solutions_by_number[f"solution_{current_number}"]["content"] += str(child)
    return solutions_by_number

def get_solutions_from_source(source, numprob, workers = 3) :
    solutions = []

    numbers = range(1, numprob+1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        records = pool.map(lambda n: get_solutions_from_page(source, numprob, n), numbers)

    for n,rec in zip(numbers,records) :
        solution = dict()
        solution["problem_number"] = n
        solution["source"] = rf"{source}_Problems/Problem_{n}"
        solution["solutions"] = rec

        solutions.append(solution)
    return solutions

def get_solutions_full(contest,
                    save_json=False,
                    chunk_size=3,
                    num = 15) :
    
    _,pairs = generate_all_and_pairs('s',contest)
    pairs = pairs[:min(num,len(pairs))]
    downloaded = check_retrieved_file('s',contest)

    solutions = []
    bar = tqdm(list(enumerate(batched(pairs,chunk_size))),
            desc = 'Progress',
            unit = 'chunk',
            position = 0,
            leave = True)

    try :
        for i,chunk in bar :
            for year,source,vers,numprob in chunk :
                sols = get_solutions_from_source(source,numprob,chunk_size)
                for sol in sols :
                    sol['year'] = year
                    sol['version'] = vers
                solutions+=sols
            time.sleep(VSWAIT)
            bar.set_postfix(downloaded = f'{len(solutions)}',
                last_year = solutions[-1]['year'],
                last_version = solutions[-1]['version'])
    except Exception as e :
        print_message(f'Error : {e}')
        if len(solutions) > 0 :
            last = solutions[-1]
            last_year = last["year"]
            last_source = last["source"]
            print_message(f'Last Retrieved Data is {last_year}: {last_source}')
        else :
            print_message('No Data Retrieved')

    merged = downloaded + solutions
    if save_json :
        OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
        file_path = OUTPUT_DIR / contest / SOLUTIONS_FULL
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent = 4)

    return pairs,merged

