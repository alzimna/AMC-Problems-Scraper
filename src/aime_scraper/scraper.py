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
