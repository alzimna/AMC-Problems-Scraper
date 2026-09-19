import time

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup, Tag
import re

import json
from itertools import batched

from concurrent.futures import ThreadPoolExecutor


from .config import *
from .utils import *


def get_first_soup(contest = 'AIME') :
    URL = f"https://artofproblemsolving.com/wiki/index.php/{contest}_Problems_and_Solutions"
    browser = webdriver.Chrome(options=options)
    selector = TABLE_SELECTOR[contest]
    
    print_message(f"Retrieving {contest} Wiki Page Using Selenium",'\r')
    try:
        browser.get(URL)
        wait = WebDriverWait(browser,
                            timeout=SWAIT,
                            poll_frequency=2, 
                            ignored_exceptions=[NoSuchElementException])
        element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR,selector))
            )
        html_source = browser.page_source
        soup = BeautifulSoup(html_source,'html.parser')
    except Exception as e :
        print_message(f'Error : {e}')
    finally:
        browser.quit()
    return soup

def get_soup(source,
            type,
            numprob = 15,
            msg = True,
            max_retries = 5,
            contest = 'AIME') :
    
    if type == 'a' :
        temp = 'Answer_Key'
        url = rf"{source}_{temp}"
        problem_title = url.split('title=')[-1].replace('_',' ')
    elif type == 'p' :
        temp = 'Problems'
        url = rf"{source}_{temp}"
        problem_title = url.split('title=')[-1].replace('_',' ')
    else :
        url = "view-source:"+source
        msg = False
        match = re.search(r'title=(.*?)_Problems/(.*)',url)
        text = match.group(1)+" "+match.group(2)
        problem_title = "Solution " + text.replace('_',' ')

    if msg :
        print_message(f"Retrieving {problem_title} Using Selenium",'\r')

    if type == 'a' :
        selector = [(By.TAG_NAME, 'ol'),1]
    elif type == 'p' :
        selector = [(By.CLASS_NAME, 'mw-headline'),numprob]
    else :
        selector = [(By.CLASS_NAME,'wikitable'),1]

    for attempt in range(1,max_retries+1) :
        browser = webdriver.Chrome(options=options)
        wait = WebDriverWait(browser,
                            timeout= MWAIT,
                            poll_frequency=1,
                            ignored_exceptions=[NoSuchElementException])
        try:
            browser.get(url)
            if type != 's' :
                wait.until(wait_for_visible_count(*selector))
                html_source =  browser.page_source
            else :
                html_source = browser.execute_script("return document.body.textContent")
            soup = BeautifulSoup(html_source,'html.parser')

            content = soup.select_one(CONTENT_SELECTOR) if soup is not None else None
            if content is not None :
                if type != 's' :
                    return content,problem_title,url
                else :
                    return content
            else :
                print_message(f"Retrieving {problem_title} Failed: content selector not found, retrying...({attempt})",'\r')
                
        except Exception as e :
            print_message(f"Retrieving {problem_title} Failed Retrying...({attempt})",'\r')
            soup = None
        finally:
            browser.quit()
    
    print_message(f"Max-Retries Achieved, {problem_title} Failed to Retrieve")
    return None


def get_contest_metadata_from_link(contest,elem) :
    link = rf"https://artofproblemsolving.com{elem.get('href')}"
    problems_num = 0

    title = elem.get('title')
    year = re.search(PATTERN_TITLE[contest],title).group(1)

    if contest == 'AIME' :
        temp = re.search(PATTERN_VERSION[contest],link)
        vers = temp.group(1) if (temp and temp.group(1)) else 'I'
    elif contest == 'AMC_8' :
        temp = re.search(PATTERN_VERSION[contest],link)
        vers = temp.group(1).split('_')[0]
    else :
        vers = 'I'

    for attempt in range(1,4) :
        browser = webdriver.Chrome(options=options)
        wait = WebDriverWait(browser,
                        timeout=5,
                        poll_frequency=1, 
                        ignored_exceptions=[NoSuchElementException])
        try:
            browser.get(link)
            if contest == 'AIME' :
                if (year == "2026") and (vers == 'II') :
                    wait.until(
                            EC.visibility_of_element_located((By.ID,'mw-content-text'))
                            )
                    selector = '#mw-content-text > div > ul > li:nth-child(2) > ul'
                else :
                    wait.until(
                        EC.visibility_of_element_located((By.CLASS_NAME,'wikitable'))
                        )
                    selector = '#mw-content-text > div > table > tbody > tr:nth-child(3) > td'
                html_source = browser.page_source
            else :
                wait.until(
                        EC.visibility_of_element_located((By.ID,'mw-content-text'))
                        )
                html_source = browser.page_source
                selector = "#mw-content-text > div > ul"
            soup = BeautifulSoup(html_source,'html.parser')
            element = soup.select_one(selector)

            if contest == 'AIME' :
                if (year == '2026') and (vers == 'II') :
                    condition = lambda tag : tag.name == 'a' and re.search(r'^Problem',tag.text)
                    problems_num = len(element.find_all(condition)) if element != None else 0
                else :
                    problems_num = len(element.find_all('a')) if element != None else 0
            else :
                condition = lambda tag : tag.name == 'a' and re.search(r'Problem\s+',tag.text)
                problems_num = len(element.find_all(condition)) if element != None else 0

            if problems_num > 0 :
                break
            else :
                print_message(f"Retrieving {elem} Failed: content selector not found, retrying...({attempt})",'\r')
        except Exception as e :
            print_message(f"Error occured, retrying...({attempt})",'\r')
        finally:
            browser.quit()

    if problems_num == 0 :
        print_message(f"content selector not found",'\r')

    record = {}       
    record['id'] = " ".join([contest.replace('_',' '),vers,year])
    record['contest'] = contest.replace('_',' ')
    record['year'] = year
    record['version'] = vers
    record['number of problems'] = problems_num
    record['source'] = link

    return record
    
def get_contest_metadata(contest = 'AIME',
                        save_json = False,
                        chunk_size = 3) :
    soup = get_first_soup(contest)
    metadata = []
    link_elements = soup.select(LINK_SELECTOR[contest])
    bar = tqdm(list(enumerate(batched(link_elements,chunk_size))),
                desc = 'Progress',
                unit = 'source',
                position = 0,
                leave = True)

    metadata = []
    for j,chunk in bar :
        with ThreadPoolExecutor(max_workers=chunk_size) as pool:
            records = pool.map(lambda elem : get_contest_metadata_from_link(contest,elem), chunk)
            for rec in records :
                metadata.append(rec)
        time.sleep(SWAIT)
        bar.set_postfix(downloaded = f"{len(metadata)}",
                        last_year = metadata[-1]['year'],
                        last_version = metadata[-1]['version'])

    if(len(metadata) != 0) :
        print_message("metadata retrieved")

    if save_json :
        (DATA_PATH / contest).mkdir(parents=True,exist_ok=True)
        file_path = DATA_PATH / contest / CONTEST_METADATA_NAME
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=True, indent = 4)

    return metadata