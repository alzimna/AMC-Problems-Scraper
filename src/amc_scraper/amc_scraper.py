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

from .config import *
from .utils import *
from .problems_scraper import *
from .answers_scraper import *
from .solutions_scraper import *
from .builder import *
from .downloader import *
from .scraper import *
from .parser import *

def generate_tex_json(contest) :
    pipeline = [
        build_full,
        build_index,
        add_figure_list,
        parsing_prob_to_tex,
        parsing_sol_to_tex
    ]
    for pipe in pipeline :
        pipe(contest)

def generate_tex_folder(contest, type = 'nosol') :
    generate_tex_json(contest)

    metadatapath = DATA_PATH / contest / CONTEST_METADATA_NAME
    with open(metadatapath,'r',encoding = 'utf-8') as f :
        data = json.load(f)

    if type == 'nosol' :
        temp = 'Problem'
    elif type == 'withsolution' :
        temp = 'Problem and Solution'
    else :
        raise Exception('Type not found')
    
    folderpath = TEX_PATH / contest / temp
    folderpath.mkdir(parents = True, exist_ok = True)

    with open(folderpath / 'copas.txt','w',encoding = 'utf-8') as f :
        for rec in data[::-1]:
            if contest in ['AIME','AMC_10','AMC_12'] :
                filename = rec['year']+"_"+rec['version']+".tex"
                if type == "withsolution" :
                    filename = rec['year']+"_"+rec['version']+"_with_solution.tex"
            else :
                filename = rec['year']+".tex"
                if type == "withsolution" :
                    filename = rec['year']+"_with_solution.tex"

            output = folderpath / filename
            
            build_tex(type,contest,rec['year'],rec['version'],output)
            f.write(rf'\input{{{filename}}}'+'\n')

def generate_html_json(contest) :
    pipeline = [
        build_full,
        build_index,
        add_figure_list,
        parsing_prob_to_html,
        parsing_sol_to_html
    ]
    for pipe in pipeline :
        pipe(contest)