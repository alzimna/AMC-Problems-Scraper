from pathlib import Path
import json
import re
import pandas as pd
from bs4 import BeautifulSoup
import lxml.etree as ET
import re
import copy


from .config import *

ACT_PROB = {
    'figure' : lambda target,item : target.replace(str(item),item.decode_contents()),
    'figcaption' : lambda target,item : target.replace(str(item),item.decode_contents()),
    'div' : lambda target,item : target.replace(str(item),item.decode_contents()),
    'p' : lambda target,item : target.replace(str(item),item.decode_contents()+'\n\n '),
    'center' : lambda target,item : target.replace(str(item),item.decode_contents()),
    r'^h\d+' :  lambda target,item : target.replace(str(item),rf'\textbf{{{item.decode_contents()}}} '),
    'span' : lambda target,item : target.replace(str(item),item.decode_contents()),
    'a' : lambda target,item : decode_link(target,item),
    'b' : lambda target,item : target.replace(str(item),rf'\textbf{{{item.decode_contents()}}}'),
    'i' : lambda target,item : target.replace(str(item),rf'\textit{{{item.decode_contents()}}}'),
    'br': lambda target,item : target.replace(str(item),'\n'),
    'hr': lambda target,item : target.replace(str(item),''),
}

ACT_PROB_HTML = {
    'a' : lambda target,item : decode_link_html(target,item),
}

FIG_CONDITION = lambda tag : ((tag.name == 'img') and 
                            ((tag.get('class') == ['mw-file-element']) or
                            ((tag.get('class') == ['latexcenter']) and '[asy]' in tag.get('alt')))
                            )

def video_condition(tag) :
    if tag.name == 'h2' :
        if len(tag.find_all('span')) > 0 :
            for child in tag.children :
                if re.match(r'^video_solution',child.get('id','').lower()) :
                    return True
        return False
    if tag.name == 'p' :
        if tag.find_all('a') == 0 :
            return False
        
        temp =  tag.select_one(":first-child")
        if temp is None :
            return False
        
        if temp.name == 'a' and ('youtu' in temp.get('href','') or 'acad' in temp.get('href','')):
            return True
    return False

def decode_video(statement) :
    statement_soup = BeautifulSoup(statement,'html.parser')
    statement_cleaned = statement
    for child in statement_soup.find_all(video_condition) :
        statement_cleaned = statement_cleaned.replace(str(child),'')
    return statement_cleaned


MATH_MODE = [
    (r'\\\(', r'\\\)'),
    (r'\\\[', r'\\\]'),
    (r'\$\$', r'\$\$'),
    (r'\$', r'\$'),
] + [
    (rf'\\begin\{{{env}\}}', rf'\\end\{{{env}\}}')
    for env in ['align', 'align\\*', 'equation', 'equation\\*',
                'gather', 'gather\\*', 'multline', 'multline\\*', 'eqnarray', 'eqnarray\\*',
                'array']
]

MATH_PATTERN = [rf'{start}.*?{end}' for start, end in MATH_MODE]
MATH_PATTERN = '|'.join(MATH_PATTERN)
SYMBOL = {"_" : r'\_',
        "#": r'\#',
        "^": r'\textasciicircum{}',
        "%": r'\%',
        r"\bmod" : r"$\bmod"
        }


def decode_math(statement) :
    for sym in SYMBOL :
        pattern = rf'({MATH_PATTERN})|(?<!\\){re.escape(sym)}'

        temp = SYMBOL.get(sym,'')

        statement = re.sub(
            pattern,
            lambda m: m.group(1) if m.group(1) else temp,
            statement,
            flags=re.DOTALL
        )
    return statement

def decode_tag(statement) :
    statement_soup = BeautifulSoup(statement,'html.parser')
    statement_cleaned = statement
    for tag,action in ACT_PROB.items() :
        pattern = re.compile(tag)
        for item in statement_soup.find_all(lambda x: x.name and pattern.fullmatch(x.name)) :
            statement_cleaned = action(statement_cleaned,item)
    return statement_cleaned

def spaces_to_tabs(text):
    return re.sub(r'^( +)', lambda m: '\t' * (len(m.group(1)) // 4), text, flags=re.MULTILINE)

def decode_verbatim(statement):
    soup = BeautifulSoup(statement, "html.parser")

    for tag in soup.find_all("pre"):
        statement = statement.replace(
            str(tag),
            rf"\begin{{verbatim}}" + "\n"
            + spaces_to_tabs(tag.decode_contents())
            + "\n"
            + rf"\end{{verbatim}}"
        )

    return statement+"\n\n"


def decode_link(target,item) :
    if item.find('img') :
        return target.replace(str(item),item.decode_contents())
    else :
        href = item.get("href")
        temp = r"https://artofproblemsolving.com"
        if href is not None and (temp in href or "https" in href):
            temp = href
        else :
            temp = temp + href
        return target.replace(str(item),rf'\href{{{temp}}}{{{item.text}}}')


def decode_img(df,row,statement_tex,type) :
    statement_soup = BeautifulSoup(statement_tex,'html.parser')
    if type == 'p' :
        figs = df.loc[row,'figures_problem']
    elif type == 's' :
        figs = df.loc[row,'figures_solution']
    else :
        raise Exception('Type not found')

    img_counter = -1
    for tag in statement_soup.find_all('img') :
        if FIG_CONDITION(tag) :
            img_counter += 1
            figure_name = figs[img_counter]
            if type == 'p' :
                figure_name = "Problem/"+figure_name
            elif type == 's' :
                figure_name = "Solution/"+figure_name

            repl = rf'''
                    \begin{{figure}}[H]
                        \centering
                        \includegraphics[width=0.5\textwidth]{{{figure_name}}}
                    \end{{figure}}
                    '''
            statement_tex = statement_tex.replace(str(tag),repl)
        else :
            if tag.get('alt','')[:3] == r'\\[' or 'latexcenter' in tag.get('class') :
                temp = "\n "+tag.get('alt','')
            else :
                temp = tag.get('alt','')
            statement_tex = statement_tex.replace(str(tag),temp)
    return statement_tex

def decode_dldd(statement) :
    statement_soup = BeautifulSoup(statement,'html.parser')
    statement_cleaned = statement
    for item in statement_soup.find_all('dl') :
        temp = rf'''
            \begin{{enumerate}}[label=(\roman*)]
                {item.decode_contents()}
            \end{{enumerate}}
            '''
        statement_cleaned = statement_cleaned.replace(str(item),temp)

    for item in statement_soup.find_all('dd') :
        pattern = r'\((?:[ivxlcdm]+|[a-z])\)'
        text = item.decode_contents()
        text = re.sub(pattern,'',text)
        statement_cleaned = statement_cleaned.replace(str(item),rf'\item {text}')
    return statement_cleaned

def decode_list(statement) :
    statement_soup = BeautifulSoup(statement,'html.parser')
    statement_cleaned = statement
    for item in statement_soup.find_all('ol') :
        temp = rf'''
            \begin{{enumerate}}
                {item.decode_contents()}
            \end{{enumerate}}
            '''
        statement_cleaned = statement_cleaned.replace(str(item),temp)

    for item in statement_soup.find_all('ul') :
        if item.find('li') :
            temp = rf'''
                \begin{{itemize}}
                    {item.decode_contents()}
                \end{{itemize}}


                '''
            statement_cleaned = statement_cleaned.replace(str(item),temp)
        else :
            continue


    for item in statement_soup.find_all('li') :
        statement_cleaned = statement_cleaned.replace(str(item),r'\item ' + item.decode_contents())
    return statement_cleaned

def cleaning_tex(statement):
    return (
        statement
        .replace(r'\rm', r'\textrm')
        .replace(r'\tfrac', r'\frac')
        .replace(r'&lt;',r'<')
        .replace(r'&gt;',r'>')
        .replace(r'&amp;',r'&')
        .replace('\\end{align*}','\\end{align*}\n')
        .replace('（','(')
        .replace('）',')')
        .replace('\u200b', '')
        .replace('…', r'\ldots')
        .replace(r'\begin{array}{lc}\text{Least number}',r'\begin{array}{lccccc}\text{Least number}')
    )

def parsing_prob_to_tex(contest) :
    filename = DATA_PATH / contest / 'full.json'
    with open(filename,'r',encoding='utf-8') as f :
        data = json.load(f)
        
    df = pd.DataFrame(data)

    df['problem_statement_html'] = (df['problem_statement'].apply(decode_math)
                                                    .apply(decode_tag)
                                                    .apply(decode_dldd)
                                                    .apply(decode_list)
                                                    )                                                 
    
    prob_tex = []
    for i in range(len(df)) :
        prob_state = df.loc[i,'problem_statement_tex']
        prob_state_cleaned = decode_img(df,i,prob_state,'p')
        prob_state_cleaned = cleaning_tex(prob_state_cleaned)
        year = df.loc[i,'year']
        ver = df.loc[i,'version']
        header = rf'(\textit{{{contest} {ver} {year}}}) '
        prob_tex.append(header+prob_state_cleaned)

    df['problem_statement_tex'] = prob_tex
    fulltexpath = DATA_PATH / contest / 'full_tex.json'
    (df.to_json(fulltexpath,orient = 'records',indent=4))
    return df

def parsing_sol_statement_to_tex(statement) :
    pipeline = [
        decode_video,
        decode_math,
        decode_tag,
        decode_dldd,
        decode_list,
        decode_verbatim
    ]
    statement_tex = statement
    for pipe in pipeline :
        statement_tex = pipe(statement_tex)
    return statement_tex
    
def parsing_sol_to_tex(contest) :
    filename = DATA_PATH / contest / 'full_tex.json'


    if filename.is_file() and filename.stat().st_size > 0:
        with open(filename,'r',encoding='utf-8') as f :
            data = json.load(f)
        df = pd.DataFrame(data)
    else :
        df = parsing_prob_to_tex(contest)

    solutions_tex = []
    for i in range(len(df)) :
        solutions = df.loc[i,'solutions']
        res = ""
        for key,value in solutions.items() :
            headline = value['headline']
            solution = value['content']
            if len(solution) == 0 :
                continue
            solution_tex = parsing_sol_statement_to_tex(solution)
            temp = rf'''\textbf{{{headline}}}

{solution_tex}

'''
            res = res + "\n\n" + temp

        res = decode_img(df,i,res,'s')
        res = cleaning_tex(res)
        solutions_tex.append(res)

    df['solutions_statement_tex'] = solutions_tex
    fulltexpath = DATA_PATH / contest / 'full_tex.json'
    (df.to_json(fulltexpath,orient = 'records',indent=4))

    return df


def decode_img_html(df,row,statement_html,type) :
    statement_soup = BeautifulSoup(statement_html,'html.parser')
    if type == 'p' :
        figs = df.loc[row,'figures_problem']
    elif type == 's' :
        figs = df.loc[row,'figures_solution']
    else :
        raise Exception('Type not found')

    img_counter = -1
    for tag in statement_soup.find_all('img') :
        if FIG_CONDITION(tag) :
            img_counter += 1
            figure_name = figs[img_counter]
            if type == 'p' :
                figure_name = "Problem/"+figure_name
            elif type == 's' :
                figure_name = "Solution/"+figure_name
            repl = f'<img src="figure/{df.loc[row,'contest']}/{figure_name}" style="display:block; width:400px; max-width:100%; height:auto; margin:20px auto 0;"> '
            statement_html = statement_html.replace(str(tag),repl)
        else :
            temp = tag.get('alt','')+' '
            statement_html = statement_html.replace(str(tag),temp)
    return statement_html


def decode_tag_html(statement) :
    statement_soup = BeautifulSoup(statement,'html.parser')
    statement_cleaned = statement
    for tag,action in ACT_PROB_HTML.items() :
        pattern = re.compile(tag)
        for item in statement_soup.find_all(lambda x: x.name and pattern.fullmatch(x.name)) :
            statement_cleaned = action(statement_cleaned,item)
    return statement_cleaned

def decode_link_html(target,item) :
    if item.find('img') :
        return target.replace(str(item),item.decode_contents())
    else :
        href = item.get("href")        
        temp = r"https://artofproblemsolving.com"
        if href is not None and (temp in href or "https" in href):
            temp = href
        else :
            temp = temp + href
        item_cleaned = copy.copy(item)
        item_cleaned['href'] = temp
        return target.replace(str(item),str(item_cleaned))

def parsing_prob_to_html(contest) :
    filename = DATA_PATH / contest / 'full.json'
    with open(filename,'r',encoding='utf-8') as f :
        data = json.load(f)

    df = pd.DataFrame(data)
    df['problem_statement_html'] = df['problem_statement'].apply(decode_tag_html)

    prob_html = []
    for i in range(len(df)) :
        prob_state = df.loc[i,'problem_statement_html']
        prob_state_cleaned = decode_img_html(df,i,prob_state,'p')
        prob_state_cleaned = cleaning_tex(prob_state_cleaned)
        prob_html.append(prob_state_cleaned)

    df['problem_statement_html'] = prob_html
    fullhtmlpath = DATA_PATH / contest / 'full_html.json'
    (df.to_json(fullhtmlpath,orient = 'records',indent=4))
    return df

def parsing_sol_statement_to_html(statement) :
    pipeline = [
        decode_video,
        decode_tag_html,
    ]
    statement_html = statement
    for pipe in pipeline :
        statement_html = pipe(statement_html)
    return statement_html

def parsing_sol_to_html(contest) :
    filename = DATA_PATH / contest / 'full_html.json'

    if filename.is_file() and filename.stat().st_size > 0:
        with open(filename,'r',encoding='utf-8') as f :
            data = json.load(f)
        df = pd.DataFrame(data)
    else :
        df = parsing_prob_to_html(contest)

    solutions_html = []
    for i in range(len(df)) :
        solutions = df.loc[i,'solutions']
        
        res = dict()
        if len(solutions) == 0 :
            solutions_html.append(res)
            continue

        subs = 0
        for key,value in solutions.items() :
            headline = value['headline']
            solution = value['content']
            if len(solution) == 0 :
                subs+=1
                continue
            countrev = int(key.split("_")[-1])-subs
            key = f"solution_{countrev}"
            solution_html = parsing_sol_statement_to_html(solution)
            temp = rf'''<h2>{headline}</h2>{solution_html}
                        '''

            temp = decode_img_html(df,i,temp,'s')
            res[key] = cleaning_tex(temp)
        solutions_html.append(res)

    df['solutions_statement_html'] = solutions_html
    fullhtmlpath = DATA_PATH / contest / 'full_html.json'
    (df.to_json(fullhtmlpath,orient = 'records',indent=4))

    return df

