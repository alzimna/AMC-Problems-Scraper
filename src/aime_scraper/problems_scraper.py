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

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument(f'--user-agent={user_agent}') 
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1420,1080')

from .scraper import (print_message,
                        get_contest_metadata,
                        check_retrieved_file,
                        get_soup,
                        _generate_all_and_pairs)

CONTENT_SELECTOR = '#mw-content-text > div'
PATTERN_VERSION = r'title=\d{4}_AIME_([IVX]+)?'
PATTERN_HEADLINE_ID = r'^Problem_(\d+)$'

VSWAIT = 1
SWAIT = 3
MWAIT = 5
LWAIT = 10

OUTPUT_DIR = Path(r'../data')
PROBLEMS_FULL = 'problems_full.json'

def get_problems_from_url(s,msg = True) :
    soup,problem_title,url = get_soup(s,'p',msg)

    content = soup.select_one(CONTENT_SELECTOR)
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
        prob['number'] = number
        prob['problem'] = ''.join(problems_by_number[number])
        problems.append(prob)
    return problems    

def get_problems_full(contest_metadata,
                    save_json = False,
                    chunk_size = 2) :
    
    downloaded = check_retrieved_file('p')
    all,pairs = _generate_all_and_pairs('p',
                                        contest_metadata,
                                        downloaded)

    problems = []
    
    try :
        for i,chunk in enumerate(batched(pairs[:2],chunk_size)) :
            for year,source in chunk :
                probs = get_problems_from_url(source,msg = False)
                for prob in probs :
                    prob['year'] = year
                problems+=probs
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