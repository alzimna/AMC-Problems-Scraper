from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup
import pandas as pd
import requests

from .builder import *

figure_path = Path(r'../figures')

def get_download_list() :
    df_full = build_full()

    val = set()
    download = []
    condition = lambda tag : ((tag.name == 'img') and 
                                ((tag.get('class') == ['mw-file-element']) or
                                (tag.get('class') == ['latexcenter']) and '[asy]' in tag.get('alt'))
                                )

    for i in range(len(df_full)) :
        cek = df_full.iloc[i,5]
        id = df_full.loc[i,'id']
        cek = BeautifulSoup(cek,'html.parser')
        cekimg = cek.find_all(condition)

        if cekimg :
            for i,item in enumerate(cekimg) :
                src = item.get('src')
                if 'https:' not in src :
                    src = 'https:'+src

                ext = Path(src.split('/')[-1]).suffix
                id+=f'_Problem_Figure_{i+1}'+ext
                download.append((id,src))
    return download

def get_figures() :
    download = get_download_list()
    for name,url in download:
        path = figure_path / name

        if path.exists() :
            print_message(f'{name} Skipped')
        else :
            for attempt in range(5) :
                try :
                    response = requests.get(url)

                    with open(path,'wb') as f :
                        f.write(response.content)
                except Exception as e :
                    print_message(f'Download {name} Failed with error : {e}')
                    print_message(f'Retrying to Download {name} {attempt+1}',end = '\r')
            if path.stat().st_size == 0 :
                print_message(f'Download {name} Failed')