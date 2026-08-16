from pathlib import Path
import json
import re
import time
from tqdm import tqdm

import pandas as pd
import re
import json

from pathlib import Path
from itertools import batched
from tqdm import tqdm

from .utils import *
from .config import *

def build_index() :  
    DATA_PATH.mkdir(parents=True,exist_ok=True)

    with open(PROBLEM_PATH,'r',encoding = 'utf-8') as file :
        data = json.load(file)
        
    df_index = pd.DataFrame(data)[['year','version','problem_number']]
    df_index['contest'] = 'AIME'
    df_index['id']=(df_index['contest']+"_"+
                    df_index['year'].astype(str)+"_"+
                    df_index['version'].astype(str)+"_"+
                    df_index['problem_number'].astype(str))
    (df_index.set_index('id')
            .to_json(INDEX_PATH,orient = 'index',indent=4)
            )
    
    return df_index

def build_full() :
    output = [PROBLEM_PATH, ANSWER_PATH, SOLUTION_PATH ]
    df_full = build_index()

    for path in output :
        with open(path,'r',encoding='utf-8') as f :
            data = json.load(f)
            df = pd.DataFrame(data).drop(columns=['source'])
        df_full = (pd.merge(df_full,df,
                            how = 'left',
                            on = ['year','version','problem_number']))

        (df_full.to_json(FULL_PATH,orient = 'records',indent=4)
            )
        
    return df_full