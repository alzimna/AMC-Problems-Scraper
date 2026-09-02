from pathlib import Path
from tqdm import tqdm
import pandas as pd
import requests
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from .builder import *
from .config import *

def get_download_list_problem(contest) :
    fullpath = DATA_PATH / contest / FULL_NAME
    if fullpath.is_file() and fullpath.stat().st_size > 0:
        with open(fullpath,'r',encoding='utf-8') as f:
            df_full = pd.read_json(f)
    else :
        df_full = build_full(contest)

    download = []
    fig_problem = [[] for _ in range(len(df_full))]
    for i in range(len(df_full)) :
        cek = df_full.loc[i,'problem_statement']
        img_counter = 0

        cek = BeautifulSoup(cek,'html.parser')
        cekimg = cek.find_all(FIG_CONDITION)
        if len(cekimg)>0 :
            for item in cekimg:
                img_counter+=1
                id = df_full.loc[i,'id']
                src = item.get('src')
                if 'https:' not in src :
                    src = 'https:'+src

                ext = Path(src.split('/')[-1]).suffix
                if ext == '.gif':
                    ext = '.png'
                id+=f'_Problem_Figure_{img_counter}'+ext

                download.append((id,src))
                fig_problem[i].append(id)    
    return download,fig_problem

def get_download_list_solution(contest) :
    fullpath = DATA_PATH / contest / FULL_NAME
    if fullpath.is_file() and fullpath.stat().st_size > 0:
        with open(fullpath,'r',encoding='utf-8') as f:
            df_full = pd.read_json(f)
    else :
        df_full = build_full(contest)

    download = []
    fig_solution = [[] for _ in range(len(df_full))]

    for i in range(len(df_full)) :
        sols = df_full.loc[i,'solutions']
        img_counter = 0
        for record in sols.values() :
            sol = record['content']
            try :
                solsoup = BeautifulSoup(sol,'html.parser')
                cekimg = solsoup.find_all(FIG_CONDITION)
            except :
                pass
            
            if len(cekimg) > 0 :
                for item in cekimg :
                    img_counter+=1
                    id = df_full.loc[i,'id']
                    src = item.get('src')
                    if 'https:' not in src :
                        src = 'https:'+src

                    ext = Path(src.split('/')[-1]).suffix
                    id+=f'_Solution_Figure_{img_counter}'+ext

                    fig_solution[i].append(id)
                    download.append((id,src))
    return download,fig_solution

def download_figures(download, type, contest) :
    bar = tqdm(download, desc='Progress', unit='Figure',position = 0, leave=True)
    for name,url in bar:
        if type == 'p' :
            path = FIGURE_PATH / contest / 'Problem' / name
        else :
            path = FIGURE_PATH / contest / 'Solution' / name

        if path.exists() and path.stat().st_size > 0 :
            print_message(f'{name} Skipped')
            continue

        success = False
        for attempt in range(3) :
            try :
                if Path(url.split('/')[-1]).suffix == '.gif' :
                    browser = webdriver.Chrome(options=options)
                    browser.get(url)

                    img_element = browser.find_element(By.XPATH, "//img")
                    path = path.with_suffix(".png")
                    
                    img_element.screenshot(path)
                    browser.quit()
                else :
                    response = requests.get(url)
                    response.raise_for_status()
                    with open(path,'wb') as f :
                        f.write(response.content)

                if path.stat().st_size > 0 :
                    success = True
                    break
            except Exception as e :
                browser = webdriver.Chrome(options=options)
                browser.get(url)

                img_element = browser.find_element(By.XPATH, "//img")

                with open(path, "wb") as file:
                    file.write(img_element.screenshot_as_png)
                browser.quit()
                if path.stat().st_size > 0 :
                                    success = True
                                    break
                else :
                    print_message(f'Download {name} Failed with error : {e}')
                    print_message(f'Retrying to Download {name} {attempt+1}',end = '\r')

        if not success :
            print_message(f'Download {name} Failed')


def get_figures_problem(contest) :
    download,_ = get_download_list_problem(contest)
    download_figures(download,'p',contest)

def get_figures_solution(contest) :
    download,_ = get_download_list_solution(contest)
    download_figures(download,'s',contest)

def add_figure_list(contest) :
    fullpath = DATA_PATH / contest / FULL_NAME
    if fullpath.is_file() and fullpath.stat().st_size > 0:
        with open(fullpath,'r',encoding='utf-8') as f:
            df_full = pd.read_json(f)
    else :
        df_full = build_full(contest)

    if ('figures_problem' in df_full.columns) :
        return
    else :
        _,x = get_download_list_problem(contest)
        df_full['figures_problem'] = x

    if ('figures_solution' in df_full.columns) :
        return
    else :
        _,y = get_download_list_solution(contest)
        df_full['figures_solution'] = y

    fullpath = DATA_PATH / contest / FULL_NAME
    (df_full.to_json(fullpath,orient = 'records',indent=4)
        )
