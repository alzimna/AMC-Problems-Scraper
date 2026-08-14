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
import os

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument(f'--user-agent={user_agent}') 
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1420,1080')

VSWAIT = 1
SWAIT = 3
MWAIT = 5
LWAIT = 10

URL = "https://artofproblemsolving.com/wiki/index.php/AIME_Problems_and_Solutions"
TABLE_SELECTOR = "#mw-content-text > div > table"
COLUMN_YEAR_SELECTOR = "#mw-content-text > div > table > tbody > tr > td:nth-child(1)"
PATTERN_YEAR = r'^\d{4}$'
LINK_SELECTOR = '#mw-content-text > div > table > tbody > tr > td > a'
PATTERN_TITLE = r'(^\d{4}).*?([IVX]+)?$'


OUTPUT_DIR = Path(r'../data')
PROBLEMS_FULL = 'problems_full.json'

from .problems_scraper import *
from .answers_scraper import *

def print_message(msg) :
    n = len(msg)
    nsym = (98-n)//2
    print(f"{'='*nsym} {msg} {'='*nsym}")

def wait_for_visible_count(locator, min_count):
    def check(d):
        visible = [el for el in d.find_elements(*locator) if el.is_displayed()]
        return visible if len(visible) >= min_count else False
    return check

def get_first_soup() :
    soup = None
    try:
        print_message("Retrieving AIME Wiki Page")
        response = requests.get(URL, timeout=SWAIT)
        response.raise_for_status()               
        soup = BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    if soup == None :
        time.sleep(VSWAIT)
        browser = webdriver.Chrome(options=options)
        print_message("Retrieving AIME Wiki Page Using Selenium")
        try:
            browser.get(URL)
            wait = WebDriverWait(browser,
                                timeout=SWAIT,
                                poll_frequency=2, 
                                ignored_exceptions=[NoSuchElementException])
            element = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR,TABLE_SELECTOR))
                )
            html_source = browser.page_source
            soup = BeautifulSoup(html_source,'html.parser')
        finally:
            browser.quit()
    return soup

def get_soup(s,type,msg = True) :
    browser = webdriver.Chrome(options=options)
    if type == 'a' :
        temp = 'Answer_Key'
    elif type == 'p' :
        temp = 'Problems'
    url = rf"{s}_{temp}"

    problem_title = url.split('title=')[-1].replace('_',' ')
    if msg :
        print_message(f"Retrieving {problem_title} {temp} Using Selenium")

    try:
        browser.get(url)
        wait = WebDriverWait(browser,
                            timeout=MWAIT,
                            poll_frequency=2,
                            ignored_exceptions=[NoSuchElementException])
        if type == 'a' :
            selector = [(By.TAG_NAME, 'ol'),1]
        elif type == 'p' :
            selector = [(By.CLASS_NAME, 'mw-headline'),15]
        elements = wait.until(wait_for_visible_count(*selector))
        html_source = browser.page_source
        soup = BeautifulSoup(html_source,'html.parser')
    except :
        soup = None
        print_message(f"Retrieving {problem_title} {temp} Failed")
    finally:
        browser.quit()
    return soup,problem_title,url

def get_contest_metadata() :
    soup = get_first_soup()
    tds_year = soup.select(COLUMN_YEAR_SELECTOR)
    years = [tds_year[i].text.strip() 
            for i in range(len(tds_year)) 
            if re.search(PATTERN_YEAR,tds_year[i].text)
            ]

    link_elements = soup.select(LINK_SELECTOR)
    sources = dict()

    for year in years :
        sources[year] = []

    for elem in link_elements :
        link = rf"https://artofproblemsolving.com{elem.get('href')}"
        title = elem.get('title')
        res = re.search(PATTERN_TITLE,title)
        sources[res.group(1)].append(link)

    if(len(sources) != 0) :
        print_message("metadata retrieved")
    return sources

def check_retrieved_file(type) :
    if type == 'a' :
        filename = ANSWERS_FULL
    elif type == 'p' :
        filename = PROBLEMS_FULL
        
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    files = os.listdir(OUTPUT_DIR)
    if filename in files :
        file_path = OUTPUT_DIR / filename
        with open(file_path, "r",encoding='utf-8') as file:
            if file_path.stat().st_size > 0:
                return json.load(file)
            else :
                return []
    else :
        return []

def _generate_all_and_pairs(type,
                            contest_metadata,
                            downloaded) :

    all = []
    for year,sources in contest_metadata.items() :
        for source in sources :
            all.append((year,source))

    if type == 'p' :
        pattern = r'(.*?)_Problems$'
    elif type == 'a' :
        pattern = r'(.*?)_Answer_Key$'

    last_year = ''
    last_source = ''
    if(len(downloaded)>0) :
        last = downloaded[-1]
        last_year = last["year"]

        text = last["source"]
        last_source = re.search(pattern,text).group(1)

        idx = all.index((last_year,last_source))
    else :
        idx = -1

    pairs = all[idx+1:]

    return all,pairs