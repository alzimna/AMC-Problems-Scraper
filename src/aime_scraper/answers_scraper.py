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

PATTERN_VERSION = r'title=\d{4}_AIME_([IVX]+)?'

VSWAIT = 1
SWAIT = 3
MWAIT = 5
LWAIT = 10

OUTPUT_DIR = Path(r'../data')
PROBLEMS_FULL = 'problems_full.json'
ANSWERS_FULL = 'answers_full.json'


def get_answers_from_url(s,msg = True) :
    soup,problem_title,url = get_soup(s,'a',msg)

    ol_elem = soup.find('ol')
    li_list = ol_elem.find_all('li')

    if(len(li_list)>=15 and msg):
        print_message(f"{problem_title} Answer Key Retrieved")

    temp = re.search(PATTERN_VERSION,url)
    vers = temp.group(1) if (temp and temp.group(1)) else 'I'

    answers = []
    for number,answer in enumerate(li_list):
        ans = dict()
        ans['source'] = url
        ans['version'] = vers
        ans['number'] = number+1
        ans['answer'] = answer.decode_contents()
        answers.append(ans)
    return answers 

def get_answers_full(contest_metadata,
                    save_json = False,
                    chunk_size = 2) :
    
    downloaded = check_retrieved_file('a')
    all,pairs = _generate_all_and_pairs('a',
                                    contest_metadata,
                                    downloaded)

    answers = []
    try :
        for i,chunk in enumerate(batched(pairs[:3],chunk_size)) :
            for year,source in chunk :
                anss = get_answers_from_url(source,msg = False)
                for ans in anss :
                    ans['year'] = year
                answers+=anss
            time.sleep(VSWAIT)
            print_message(f"Chunk {i+1} Retrieved")
    except :
        print_message('Error_occured')
        if len(answers) > 0 :
            last = answers[-1]
            last_year = last["year"]

            text = last["source"]
            last_source = re.search(r'(.*?)_Answer_Key$',text).group(1)
            print_message(f'Last Retrieved Data is {last_year}: {last_source}')
        else :
            print_message('No Data Retrieved')

    if save_json :
        OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
        merged = downloaded + answers
        file_path = OUTPUT_DIR / ANSWERS_FULL
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent = 4)

    return merged