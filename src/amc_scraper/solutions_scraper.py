import webbrowser, bs4, requests,time

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup
import re
import json

from pathlib import Path
from itertools import batched
from tqdm import tqdm

from .utils import *
from .config import *
from .scraper import *

def get_solutions_from_page(source,number) :
    s = rf"{source}_Problems/Problem_{number}"
    content = get_soup(s,'s')

    if content is None:
        print(f"Failed to get soup: {s}")
        return None

    solutions_by_number = {}
    current_number = None
    for child in content.find_all(re.compile('^h|p'), recursive=False) :
        if re.match('h',child.name) :
            next_tag = child.find_next_sibling()
            headline = child.select_one('.mw-headline')
            match = re.match(PATTERN_SOLUTION_ID, headline.get('id', '')) if headline else None

            if next_tag.name == 'p' and match :
                if current_number == None :
                    current_number = 1
                else :
                    current_number+=1
                solutions_by_number.setdefault(f"solution_{current_number}",{})
                solutions_by_number[f"solution_{current_number}"]['content'] = []
                solutions_by_number[f"solution_{current_number}"]['headline'] = headline.text
                continue
            else :
                continue

        if current_number is None:
            continue

        solutions_by_number[f"solution_{current_number}"]['content'].append(child.decode_contents())
    return solutions_by_number

def get_solutions_from_source(source) :
    solutions = []

    for i in range(15) :
        solution = dict()
        number = i+1
        s = rf"{source}_Problems/Problem_{number}"
        record = get_solutions_from_page(source,number)

        solution["problem_number"] = number
        solution["source"] = s
        solution["solutions"] = record

        solutions.append(solution)
    return solutions

def get_solutions_full(contest,
                    save_json=False,
                    chunk_size=5) :
    x = generate_all_and_pairs('s',contest)
    pairs = x[1]
    pairs = [pairs[i] for i in range(len(pairs)) if (i%10 == 0 or i%10==1)]
    downloaded = check_retrieved_file('s',contest)

    solutions = []
    bar = tqdm(list(enumerate(batched(pairs,chunk_size))),
            desc = 'Progress',
            unit = 'chunk',
            position = 0,
            leave = True)

    try :
        for i,chunk in bar :
            for year,source in chunk :
                sols = get_solutions_from_source(source)
                temp = re.search(PATTERN_VERSION,source)
                vers = temp.group(1) if (temp and temp.group(1)) else 'I'
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

