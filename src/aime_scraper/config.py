from pathlib import Path

VSWAIT = 1
SWAIT = 3
MWAIT = 5
LWAIT = 10

URL = "https://artofproblemsolving.com/wiki/index.php/AIME_Problems_and_Solutions"

TABLE_SELECTOR = "#mw-content-text > div > table"
COLUMN_YEAR_SELECTOR = "#mw-content-text > div > table > tbody > tr > td:nth-child(1)"
LINK_SELECTOR = '#mw-content-text > div > table > tbody > tr > td > a'
CONTENT_SELECTOR = '#mw-content-text > div'

PATTERN_YEAR = r'^\d{4}$'
PATTERN_TITLE = r'(^\d{4}).*?([IVX]+)?$'
PATTERN_VERSION = r'title=\d{4}_AIME_([IVX]+)?'
PATTERN_HEADLINE_ID = r'^Problem_(\d+)$'
PATTERN_SOLUTION_ID = r'^Solution'

OUTPUT_DIR = Path(r'../data')
PROBLEMS_FULL = 'problems_full.json'
ANSWERS_FULL = 'answers_full.json'
SOLUTIONS_FULL = 'solutions_full.json'
