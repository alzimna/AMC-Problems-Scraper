from pathlib import Path
from selenium import webdriver

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument(f'--user-agent={USER_AGENT}') 
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1420,1080')
options.page_load_strategy = 'eager'
options.add_argument("--disable-extensions")
options.add_argument("--disable-dev-shm-usage")



VSWAIT = 1
SWAIT = 3
MWAIT = 8
LWAIT = 10

TABLE_SELECTOR = {
    'AIME' : "#mw-content-text > div > table",
    'AMC_10' : "#mw-content-text > div > table",
    'AMC_12' : "#mw-content-text > div > table",
    'AMC_8' : "#mw-content-text > div > ul:nth-child(2)",
    'AHSME' : "#mw-content-text > div > ul:nth-child(2)",
    'USAMO' : "#mw-content-text > div > ul:nth-child(2)",
    'USAJMO' : "#mw-content-text > div > ul:nth-child(2)"
}

COLUMN_YEAR_SELECTOR = {
    'AIME' : "#mw-content-text > div > table > tbody > tr > td:nth-child(1)",
    'AMC_8' : "#mw-content-text > div > ul:nth-child(2) > li > a"
}


LINK_SELECTOR = {
    'AIME' : '#mw-content-text > div > table > tbody > tr > td > a',
    'AMC_10' : '#mw-content-text > div > table > tbody > tr > td > a',
    'AMC_12' : '#mw-content-text > div > table > tbody > tr > td > a',
    'AMC_8' : "#mw-content-text > div > ul:nth-child(2) > li > a",
    'AHSME' : "#mw-content-text > div > ul:nth-child(2) > li > a",
    'USAMO' : "#mw-content-text > div > ul:nth-child(2) > li > a",
    'USAJMO' : "#mw-content-text > div > ul:nth-child(2) > li > a"
}

PATTERN_TITLE = r'(^\d{4})'

PATTERN_VERSION = {
    'AIME' : r'title=\d{4}_AIME_([IVX]+)?',
    'AMC_8' : r'title=\d{4}_(.*)',
    'AMC_10' : r'title=\d{4}_(.*)',
    'AMC_12' : r'title=\d{4}_(.*)'
}

CONTENT_SELECTOR = '#mw-content-text > div'

PATTERN_YEAR = r'^\d{4}'

PATTERN_HEADLINE_ID = r'^Problem_(\d+)$'
PATTERN_SOLUTION_ID = r'^Solution'

OUTPUT_DIR = Path(r'../output/')
PROBLEMS_FULL = 'problems_full.json'
ANSWERS_FULL = 'answers_full.json'
SOLUTIONS_FULL = 'solutions_full.json'

DATA_PATH = Path(r'../data')
INDEX_NAME = 'index.json'
FULL_NAME = 'full.json'
CONTEST_METADATA_NAME = 'contest_metadata.json'

FIGURE_PATH = Path(r'../figures')
TEX_PATH = Path('../Tex')

FIG_CONDITION = lambda tag : ((tag.name == 'img') and 
                            ((tag.get('class') == ['mw-file-element']) or
                            ((tag.get('class') == ['latexcenter']) and '[asy]' in tag.get('alt')))
                            )

DIFFICULTY_LEVEL = dict()

def buildList(contest,start,end,lvl) :
    for i in range(start,end+1) :
        DIFFICULTY_LEVEL[(contest,i)] = lvl

CONTEST_DIFF = [
    ('AMC_8',1,10,1),
    ('AMC_8',11,20,1.5),
    ('AMC_8',21,25,2),
    ('AMC_10',1,5,1),
    ('AMC_10',6,20,2),
    ('AMC_10',21,25,3),
    ('AMC_12',1,10,2),
    ('AMC_12',11,20,3),    
    ('AMC_12',21,25,4),
    ('AHSME',1,10,1),
    ('AHSME',11,20,2),    
    ('AHSME',21,40,3),
    ('AHSME',31,50,4),
    ('AIME',1,5,3),
    ('AIME',6,9,4),
    ('AIME',10,12,5),
    ('AIME',13,15,6),
    ('USAMO',1,1,7),
    ('USAMO',2,2,8),
    ('USAMO',3,3,9),
    ('USAMO',4,4,7),
    ('USAMO',5,5,8),
    ('USAMO',6,6,9),
    ('USAJMO',1,1,6),
    ('USAJMO',2,2,6.5),
    ('USAJMO',3,3,7),
    ('USAJMO',4,4,6),
    ('USAJMO',5,5,6.5),
    ('USAJMO',6,6,7),
]

for p in CONTEST_DIFF :
    buildList(*p)

CONTESTS = ['AHSME', 'AIME', 'AMC_10', 'AMC_12', 'AMC_8', 'USAJMO', 'USAMO']