import json
import pandas as pd
import json

from .utils import *
from .config import *

def build_full(contest = 'AIME') :
    DATA_PATH.mkdir(parents=True,exist_ok=True)
    PROBLEM_PATH = OUTPUT_DIR / contest / PROBLEMS_FULL
    ANSWER_PATH = OUTPUT_DIR / contest / ANSWERS_FULL
    SOLUTION_PATH = OUTPUT_DIR / contest / SOLUTIONS_FULL

    if contest not in ["USAMO","USAJMO"] :
        output = [ANSWER_PATH, SOLUTION_PATH]
    else :
        output = [SOLUTION_PATH]

    with open(PROBLEM_PATH,'r',encoding='utf-8') as f :
        data = json.load(f)
        df_full = pd.DataFrame(data).drop(columns=['source'])

    df_full['contest'] = contest
    df_full['id']=(df_full['contest']+"_"+
                    df_full['version'].astype(str)+"_"+
                    df_full['year'].astype(str)+"_"+
                    df_full['problem_number'].astype(str))

    for path in output :
        with open(path,'r',encoding='utf-8') as f :
            data = json.load(f)
            df = pd.DataFrame(data).drop(columns=['source'])
        df_full = (pd.merge(df_full,df,
                            how = 'left',
                            on = ['year','version','problem_number']))

    for i in range(len(df_full)) :
        p = (df_full.loc[i,'contest'],df_full.loc[i,'problem_number'])
        lvl = DIFFICULTY_LEVEL[p]
        df_full.loc[i,'difficulty'] = lvl

    fullpath = DATA_PATH / contest / FULL_NAME
    (df_full.to_json(fullpath,orient = 'records',indent=4)
        )
        
    return df_full

def build_index(contest = 'AIME') :  
    fullpath = DATA_PATH / contest / 'full.json'

    with open(fullpath,'r',encoding = 'utf-8') as file :
        data = json.load(file)
        
    df_index = pd.DataFrame(data)[['id','year','version','problem_number']]
    indexpath = DATA_PATH / contest / INDEX_NAME
    (df_index.set_index('id')
            .to_json(indexpath,orient = 'index',indent=4)
            )
    return df_index

def check_missing(contest,type = 's') :
    build_full(contest)
    if type == 'a' :
        temp1,temp2='answers','answer'
    elif type == 'p' :
        temp1,temp2='problems','problem_statement'
    else :
        temp1,temp2='solutions','solutions'

    filepath = DATA_PATH / contest / 'full.json'
    with open(filepath,'r',encoding='utf-8') as f :
        data = json.load(f)
    df = pd.DataFrame(data).reset_index(drop = True)
    if type == 'a' or type == 'p' :
        idx = df.index[df[temp2].isna() | (df[temp2].str.len() == 0)].tolist()
    else :
        idx = df.index[df[temp2].isna() | (df[temp2].map(len) == 0)].tolist()
    return idx

def delete_missing(contest,type = 's') :
    before = build_full('AIME')
    mis = before.loc[check_missing('s','AIME')]
    mis = mis.drop_duplicates(subset=['year','version'])

    if type == 'a' :
        temp = 'answers'
    elif type == 'p' :
        temp ='problems'
    else :
        temp='solutions'
    
    filepath = OUTPUT_DIR / 'AIME' / f'{temp}_full.json'
    with open(filepath, 'r',encoding= 'utf-8') as f :
        records = json.load(f)
        
    updated_records = [record for record in records if (record['year'],record['version']) not in zip(mis['year'],mis['version'])]

    with open('x.json', "w",encoding= 'utf-8') as file:
        json.dump(updated_records, file, ensure_ascii=False, indent = 4)


def build_tex(type,contest,year,version,output) :    
    filejson = DATA_PATH / contest / 'full_tex.json'
    with open(filejson,'r',encoding = 'utf-8') as f :
        data = json.load(f)
    df = pd.DataFrame(data)

    df = df[(df['contest'] == contest)  & (df['year'] == int(year)) & (df['version'] == version)].reset_index(drop = True)
    
    if contest in ['AIME','AMC_10','AMC_12'] :
        section_name = " ".join([contest.replace("_"," "),version.replace("_"," "),str(year)])
    else :
        section_name = " ".join([contest.replace("_"," "),str(year)])

    with open(output,'w',encoding = 'utf-8') as file :
        file.write(
        rf'''\section{{{section_name}}}
        \begin{{enumerate}}
        '''
        )
        for i in range(len(df)) :
            item = df.loc[i,'problem_statement_tex']
            sols = df.loc[i,'solutions_statement_tex']

            if contest not in ['USAMO','USAJMO'] :
                ans = "\n" + r" \textbf{Answer: }"+ df.loc[i,'answer']
            else :
                ans = ""

            if type == 'withsolution' :
                item = r'\item '+ item+ans+"\n\n"+sols+"\n"
            elif type == 'nosol' :
                item = r'\item '+ item + "\n\n"
            else :
                raise Exception('Type not found')

            file.write(f'\t{item}')
        file.write(
        r'\end{enumerate}'
        )