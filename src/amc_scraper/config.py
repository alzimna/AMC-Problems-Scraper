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
    'AMC_8' : "#mw-content-text > div > ul:nth-child(2)",
    'AHSME' : "#mw-content-text > div > ul:nth-child(2)"
}

COLUMN_YEAR_SELECTOR = {
    'AIME' : "#mw-content-text > div > table > tbody > tr > td:nth-child(1)",
    'AMC_8' : "#mw-content-text > div > ul:nth-child(2) > li > a"
}


LINK_SELECTOR = {
    'AIME' : '#mw-content-text > div > table > tbody > tr > td > a',
    'AMC_8' : "#mw-content-text > div > ul:nth-child(2) > li > a",
    'AHSME' : "#mw-content-text > div > ul:nth-child(2) > li > a"
}

PATTERN_TITLE = {
    'AIME' : r'(^\d{4}).*?([IVX]+)?$',
    'AMC_8' : r'(^\d{4})',
    'AHSME' : r'(^\d{4})'
    }

PATTERN_VERSION = {
    'AIME' : r'title=\d{4}_AIME_([IVX]+)?',
    'AMC_8' : r'title=\d{4}_(.*)'
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