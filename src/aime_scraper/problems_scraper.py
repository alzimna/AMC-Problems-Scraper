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

from .utils import *
from .config import *

def get_problems_from_source(s,msg = True) :
    content,problem_title,url = get_soup(s,'p',msg)

    if content is None:
        print(f"Failed to get soup: {url}")
        return None
    
    problems_by_number = {}
    current_number = None

    for child in content.find_all(['h2', 'p'], recursive=False):
        if child.name == 'h2':
            headline = child.select_one('.mw-headline')
            match = re.match(PATTERN_HEADLINE_ID, headline.get('id', '')) if headline else None
            current_number = int(match.group(1)) if match else None
            continue

        if current_number is None:
            continue

        if re.search('>Solution<', str(child)):
            continue

        (problems_by_number.setdefault(current_number, [])
                            .append(child.decode_contents())
        )

    if(len(problems_by_number)>=15 and msg):
        print_message(f"{problem_title} Retrieved")

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

def get_problems_full(contest_metadata,
                    save_json = False,
                    chunk_size = 5) :
    
    downloaded = check_retrieved_file('p')
    all,pairs = generate_all_and_pairs('p',
                                        contest_metadata,
                                        downloaded)

    problems = []
    
    try :
        for i,chunk in enumerate(batched(pairs,chunk_size)) :
            for year,source in chunk :
                probs = get_problems_from_source(source,msg = False)
                for prob in probs :
                    prob['year'] = year
                problems+=probs
                time.sleep(SWAIT)
            time.sleep(VSWAIT)
            print_message(f"Chunk {i+1} Retrieved")
    except :
        print_message('Error_occured')
        if len(problems) > 0 :
            last = problems[-1]
            last_year = last["year"]

            text = last["source"]
            last_source = re.search(r'(.*?)_Problems$',text).group(1)
            print_message(f'Last Retrieved Data is {last_year}: {last_source}')
        else :
            print_message('No Data Retrieved')

    if save_json :
        OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
        merged = downloaded + problems
        file_path = OUTPUT_DIR / PROBLEMS_FULL
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent = 4)

    return merged