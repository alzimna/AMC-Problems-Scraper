from pathlib import Path
from tqdm import tqdm
import pandas as pd
import requests
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

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
    condition = lambda tag : ((tag.name == 'img') and 
                                ((tag.get('class') == ['mw-file-element']) or
                                (tag.get('class') == ['latexcenter']) and '[asy]' in tag.get('alt'))
                                )

    for i in range(len(df_full)) :
        cek = df_full.iloc[i,5]
        img_counter = 0

        cek = BeautifulSoup(cek,'html.parser')
        cekimg = cek.find_all(condition)

        if len(cekimg)>0 :
            for item in cekimg:
                img_counter+=1
                id = df_full.loc[i,'id']
                src = item.get('src')
                if 'https:' not in src :
                    src = 'https:'+src

                ext = Path(src.split('/')[-1]).suffix
                id+=f'_Problem_Figure_{img_counter}'+ext
                download.append((id,src))
    return download

def get_download_list_solution(contest) :
    fullpath = DATA_PATH / contest / FULL_NAME
    if fullpath.is_file() and fullpath.stat().st_size > 0:
        with open(fullpath,'r',encoding='utf-8') as f:
            df_full = pd.read_json(f)
    else :
        df_full = build_full(contest)

    condition = lambda tag : ((tag.name == 'img') and 
                                ((tag.get('class') == ['mw-file-element']) or
                                (tag.get('class') == ['latexcenter']) and '[asy]' in tag.get('alt'))
                                )
    download = []
    for i in range(len(df_full)) :
        cek = df_full.iloc[i,7]
        img_counter = 0
        for key,record in cek.items() :
            content = record['content']
            for paragraph in content :
                try :
                    paragraph = BeautifulSoup(paragraph,'html.parser')
                    cekimg = paragraph.find_all(condition)
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
                        download.append((id,src))
    return download


def download_figures(download, type) :
    bar = tqdm(download, desc='Progress', unit='Figure',position = 0, leave=True)
    for name,url in bar:
        if type == 'p' :
            path = FIGURE_PATH / 'Problem' / name
        else :
            path = FIGURE_PATH / 'Solution' / name

        if path.exists() and path.stat().st_size > 0 :
            print_message(f'{name} Skipped')
            continue

        success = False
        for attempt in range(3) :
            try :
                response = requests.get(url)
                response.raise_for_status()
                with open(path,'wb') as f :
                    f.write(response.content)
                if path.stat().st_size > 0 :
                    success = True
                    break
            except Exception as e :
                print_message(f'Download {name} Failed with error : {e}')
                print_message(f'Retrying to Download {name} {attempt+1}',end = '\r')

        if not success :
            print_message(f'Download {name} Failed')


def get_figures_problem(contest) :
    download = get_download_list_problem(contest)
    download_figures(download,'p')

def get_figures_solution(contest) :
    download = get_download_list_solution(contest)
    path = FIGURE_PATH / 'Solution'
    download_figures(download,'s')
