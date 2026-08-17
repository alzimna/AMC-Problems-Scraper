import webbrowser, requests,time

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
from itertools import batched

from .config import *
from .utils import *

def get_first_soup(contest = 'AIME') :
    URL = f"https://artofproblemsolving.com/wiki/index.php/{contest}_Problems_and_Solutions"
    browser = webdriver.Chrome(options=options)
    print_message(f"Retrieving {contest} Wiki Page Using Selenium",'\r')
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
    except Exception as e :
        print_message(f'Error : {e}')
    finally:
        browser.quit()
    return soup

def get_soup(source,
            type,
            msg = True,
            max_retries = 3,
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
        url = source
        msg = False
        match = re.search(r'title=(.*?)_Problems/(.*)',url)
        text = match.group(1)+" "+match.group(2)
        problem_title = "Solution " + text.replace('_',' ')

    if msg :
        print_message(f"Retrieving {problem_title} Using Selenium",'\r')

    if type == 'a' :
        selector = [(By.TAG_NAME, 'ol'),1]
    elif type == 'p' :
        selector = [(By.CLASS_NAME, 'mw-headline'),15]
    else :
        selector = [(By.CLASS_NAME,'wikitable'),1]

    for attempt in range(1,max_retries+1) :
        browser = webdriver.Chrome(options=options)
        wait = WebDriverWait(browser,
                            timeout=SWAIT,
                            poll_frequency=0.2,
                            ignored_exceptions=[NoSuchElementException])
        try:
            browser.get(url)
            wait.until(wait_for_visible_count(*selector))
            html_source =  browser.page_source            
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

def get_contest_metadata(contest = 'AIME',
                        save_json = False) :
    soup = get_first_soup(contest)

    tds_year = soup.select(COLUMN_YEAR_SELECTOR)
    years = [tds_year[i].text.strip() 
            for i in range(len(tds_year)) 
            if re.search(PATTERN_YEAR,tds_year[i].text)
            ]
    metadata = {}

    link_elements = soup.select(LINK_SELECTOR)

    bar = tqdm(list(enumerate(batched(link_elements,5))),
                desc = 'Progress',
                unit = 'source',
                position = 0,
                leave = True)

    success = 0
    for j,chunk in bar :
        for elem in chunk :
            record = {}
            link = rf"https://artofproblemsolving.com{elem.get('href')}"

            title = elem.get('title')
            year = re.search(PATTERN_TITLE,title).group(1)

            temp = re.search(PATTERN_VERSION,link)
            vers = temp.group(1) if (temp and temp.group(1)) else 'I'

            for attempt in range(1,4) :
                browser = webdriver.Chrome(options=options)
                wait = WebDriverWait(browser,
                                timeout=5,
                                poll_frequency=0.2, 
                                ignored_exceptions=[NoSuchElementException])
                try:
                    browser.get(link)
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
                    soup = BeautifulSoup(html_source,'html.parser')
                    element = soup.select_one(selector)

                    if (year == '2026') and (vers == 'II') :
                        condition = lambda tag : tag.name == 'a' and re.search(r'^Problem',tag.text)
                        problems_num = len(element.find_all(condition)) if element != None else 0
                    else :
                        problems_num = len(element.find_all('a')) if element != None else 0

                    if problems_num > 0 :
                        time.sleep(1)
                        success+=1
                        break
                    else :
                        print_message(f"Retrieving Failed: content selector not found, retrying...({attempt})",'\r')
                except Exception as e :
                    print_message(f"Error occured, retrying...({attempt})",'\r')
                finally:
                    browser.quit()

            if problems_num == 0 :
                print_message(f"content selector not found",'\r')

            record['contest'] = contest
            record['year'] = year
            record['version'] = vers
            record['number of problems'] = problems_num
            record['source'] = link

            id = "_".join([contest,year,vers])
            metadata[id] = record
        time.sleep(3)
        bar.set_postfix(downloaded = f"{success}",
                            last_year = f"{year}",
                            last_version = f"{vers}")
    if(len(metadata) != 0) :
        print_message("metadata retrieved")

    if save_json :
        (DATA_PATH / contest).mkdir(parents=True,exist_ok=True)
        file_path = DATA_PATH / contest / CONTEST_METADATA_NAME
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=True, indent = 4)

    return metadata