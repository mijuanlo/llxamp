#!/usr/bin/env python3

import sys, os, re, glob

BASEPATH=os.path.expanduser('~')+'/llxamp'
if not os.path.exists(BASEPATH):
    print(f"Error '{BASEPATH}' not found")
    sys.exit(1)

COMMENT_PHP = ';'
CONFIG_PHP = f'{BASEPATH}/php/lib/php.ini'
COMMENT_APACHE = '#'
CONFIG_APACHE = f'{BASEPATH}/httpd/conf/httpd.conf'
COMMENT = None
CONFIG = None
TAB=' '*4



cache={}

def read_file(filename):
    if filename in cache:
        return cache.get(filename)
    if os.path.isfile(filename):
        with open(filename,'r') as fp:
            content = fp.read().splitlines()
            cache.setdefault(filename,content)
            return content
    return []

def filter_comments(txtlist):
    filtered=[]
    for line in txtlist:
        if not re.match(f'^\s*({COMMENT}|$)',line):
            filtered.append(line)
    return filtered

def filter_includes(txtlist):
    filtered=[]
    for line in txtlist:
        if not re.match(f'^\s*include',line,re.IGNORECASE):
            filtered.append(line)
    return filtered

def filter_not_includes(txtlist):
    filtered=[]
    for line in txtlist:
        if re.match(f'^\s*include',line,re.IGNORECASE):
            filtered.append(line)
    return filtered

def get_first_param(txtlist):
    params=[]
    for line in txtlist:
        params.append(line.split()[1])
    return params

def expand_includes(txtlist):
    includes=[]
    for line in txtlist:
        if os.path.exists(line):
            includes.append(line)
        else:
            if os.path.exists(os.path.realpath(f'{config_dir}/{line}')):
                includes.append(os.path.realpath(f'{config_dir}/{line}'))
            else:
                item = glob.glob(line)
                if item:
                    includes.extend(item)
                else:
                    item = glob.glob(os.path.realpath(f'{config_dir}/{line}'))
                    if item:
                        includes.extend(item)
    return includes

def process_includes(filename,hierarchy={},includes=[],content=[]):
    content.append(f'{COMMENT_LLXAMP}Content from: {filename}')
    hierarchy.setdefault(filename,{})
    
    content_for_append = read_file(filename)
    txt = filter_comments(content_for_append)
    full_newincludes = filter_not_includes(txt)
    #newincludes = expand_includes(get_first_param(full_newincludes))
    
    includes.append(filename)
    
    newincludes = []
    for line in content_for_append:
        if line not in full_newincludes:
            content.append(line)
        else:
            param = get_first_param([line])
            newincludes = expand_includes(param)
            content.append(f'{COMMENT_LLXAMP}{line}')
            for include in newincludes:
                content.append(f"{COMMENT_LLXAMP}{TAB}{param[0]} -> {include}")
            content.append(COMMENT_LLXAMP)
            for include in newincludes:
                if include not in includes:
                    process_includes(include,hierarchy[filename],includes,content)
    content.append(f'{COMMENT_LLXAMP}End content from: {filename}')
    return hierarchy,includes,content

def print_hierarchy(hierarchy={},comments=False,level=0,):
    pad=''
    txt=''
    if level:
        pad=TAB*level
    if comments:
        pad=f'{COMMENT}{pad}'
    for key,value in hierarchy.items():
        txt = f"{txt}{pad}{key}\n"
        if value:
            txt= f'{txt}{print_hierarchy(value,comments,level+1)\n}'
    return txt

def filter_generic_comments(content):
    filtered=[]
    for line in content:
        if not re.match(f'^\s*({COMMENT}|$)',line):
            filtered.append(line)
        else:
            if COMMENT_LLXAMP in line:
                filtered.append(line)
    return filtered

def filter_llxamp_comments(content):
    filtered=[]
    for line in content:
        if not re.match(f'^\s*({COMMENT}|$)',line):
            filtered.append(line)
        else:
            if not COMMENT_LLXAMP in line:
                filtered.append(line)
    return filtered

def print_content(content,comments=False,llxamp_comments=True):
    if not comments:
        content = filter_generic_comments(content)
    if not llxamp_comments:
        content = filter_llxamp_comments(content)
    return '\n'.join(content)

def help_menu():
    filename = os.path.basename(__file__)
    print(f'''{filename} usage:
{filename} [ -a [-c|-t] |-p [-c|-t] |-h ] [-r] [-i]
Options:
    -a: Select Apache mode
    -p: Select PHP mode
    -h: This help

    -c: Show configfiles content
    -t: Show include tree hierarchy

    -r: Remove comments from output
    -i: Include {filename} comments
''')

def fix_config_dir():
    global config_dir
    config_dir=os.path.dirname(os.path.realpath(CONFIG))
    if 'conf' == config_dir.split('/')[-1]:
        config_dir = '/'.join(config_dir.split('/')[:-1])

def process(params=[]):
    global COMMENT, COMMENT_LLXAMP, config_dir
    COMMENT_LLXAMP = f'{COMMENT} LLXAMP: '
    
    fix_config_dir()

    # config_text=filter_comments(read_file(CONFIG))

    hierarchy,includes,content=process_includes(CONFIG,{},[],[])
    
    if '-r' in params:
        comments = False
    else:
        comments = True
    if '-i' in params:
        llxamp_comments = True
    else:
        llxamp_comments = False

    if '-t' in params:
        print(print_hierarchy(hierarchy,llxamp_comments))
    if '-c' in params:
        print(print_content(content,comments,llxamp_comments))
    return hierarchy,includes,content

def set_mode_apache():
    global COMMENT, CONFIG, COMMENT_APACHE, CONFIG_APACHE
    COMMENT=COMMENT_APACHE
    CONFIG=CONFIG_APACHE

def set_mode_php():
    global COMMENT, CONFIG, COMMENT_PHP, CONFIG_PHP
    COMMENT=COMMENT_PHP
    CONFIG=CONFIG_PHP

if __name__ == '__main__':
    params = sys.argv
    
    if '-h' in params:
        help_menu()
        sys.exit(0)

    if '-a' in params:
        set_mode_apache()
        process(params)

    if '-p' in params:
        set_mode_php()
        process(params)

    sys.exit(0)

