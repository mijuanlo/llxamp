#!/usr/bin/env python3

"""
 Copyright (C) 2023 M.Angel Juan

 This file is part of LLXAMP.

 LLXAMP is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 LLXAMP is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with LLXAMP.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys, os, re, glob

BASEPATH=os.path.expanduser('~')+'/llxamp'
if not os.path.exists(BASEPATH):
    print(f"Error '{BASEPATH}' not found")
    sys.exit(1)

COMMENT_PHP = ';'
CONFIG_PHP = f'{BASEPATH}/php/lib/php.ini'
CONF_EXT_PHP = 'ini'
COMMENT_APACHE = '#'
CONFIG_APACHE = f'{BASEPATH}/httpd/conf/httpd.conf'
CONF_EXT_APACHE = 'conf'
COMMENT_MYSQL = '#'
CONF_EXT_MYSQL = 'cnf'
LOG_PHP_REGEXP = r'^\s*error_log\s*='
INCLUDE_PHP_REGEXP = None
INCLUDE_MYSQL_REGEXP = r'^\s*!include(dir)?'
LOG_MYSQL_REGEXP = r'^\s*(log[_-]error|general[_-]log[_-]file|log[_-]slow[_-]queries)\s*='
INCLUDE_APACHE_REGEXP = r'^\s*include'
LOG_APACHE_REGEXP = r'^\s*(error|transfer|custom)log'
if os.path.exists(f'{BASEPATH}/mariadb'):
    suffix='mariadb'
else:
    suffix='mysql'
CONFIG_MYSQL = f'{BASEPATH}/{suffix}/conf/my.cnf'
COMMENT = None
CONFIG = None
CONF_EXT = None
INCLUDE_REGEXP = None
LOG_REGEXP = None
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
    if not INCLUDE_REGEXP:
        return txtlist
    for line in txtlist:
        if not re.match(INCLUDE_REGEXP,line,re.IGNORECASE):
            filtered.append(line)
    return filtered

def filter_not_includes(txtlist):
    filtered=[]
    if not INCLUDE_REGEXP:
        return []
    for line in txtlist:
        if re.match(INCLUDE_REGEXP,line,re.IGNORECASE):
            filtered.append(line)
    return filtered

def filter_not_logs(txtlist):
    filtered=[]
    for line in txtlist:
        if re.match(LOG_REGEXP,line,re.IGNORECASE):
            filtered.append(line.strip())
    return filtered

def get_first_param(txtlist):
    params=[]
    skip_separators = ['=']
    for line in txtlist:
        parts = line.split()
        for part in parts[1:]:
            param = part.replace('"','').replace("'",'')
            aborted = False
            for sep in skip_separators:
                if param == sep:
                    aborted = True
                    break
            if aborted:
                continue
            params.append(param)
            break
    return params

def expand_includes(txtlist):
    includes=[]
    for line in txtlist:
        if '*' in line:
            item = glob.glob(line.replace('*',f'*.{CONF_EXT}'))
            if item:
                includes.extend(item)
            else:
                item = glob.glob(os.path.realpath(f'{config_dir}/{line.replace("*",f"*.{CONF_EXT}")}'))
                if item:
                    includes.extend(item)
        else:
            if os.path.isdir(line):
                item = glob.glob(line+f'/*.{CONF_EXT}')
                if item:
                    includes.extend(item)
                else:
                    item = glob.glob(os.path.realpath(f'{config_dir}/{line}'+f'/*.{CONF_EXT}'))
                    if item:
                        includes.extend(item)
            else:
                # files without glob ALWAYS be included even if they do not exist yet
                if line[:1] == '/' or line[:2] == './':
                    includes.append(line)
                else:
                    includes.append(os.path.realpath(f'{config_dir}/{line}'))

    return includes

def process_includes(filename,hierarchy={},includes=[],content=[],logs=[]):
    content.append(f'{COMMENT_LLXAMP}Content from: {filename}')
    hierarchy.setdefault(filename,{})

    content_for_append = read_file(filename)
    txt = filter_comments(content_for_append)
    full_newincludes = filter_not_includes(txt)
    newlogs = filter_not_logs(txt)
    for logfile in expand_includes(get_first_param(newlogs)):
        if logfile not in logs:
            logs.append(logfile)
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
                    process_includes(include,hierarchy[filename],includes,content,logs)
    content.append(f'{COMMENT_LLXAMP}End content from: {filename}')
    return hierarchy,includes,content,logs

def print_hierarchy(hierarchy={},comments=False,level=0):
    if CONFIG == CONFIG_APACHE:
        label='CONFIG_APACHE:'
    elif CONFIG == CONFIG_PHP:
        label='CONFIG_PHP:'
    elif CONFIG == CONFIG_MYSQL:
        label='CONFIG_MYSQL:'
    pad=''
    txt=''
    if level:
        pad=TAB*level
    if comments:
        pad=f'#{label}{pad}'
    for key,value in hierarchy.items():
        txt = f"{txt}{pad}{key}\n"
        if value:
            txt= f'{txt}{print_hierarchy(value,comments,level+1)}'
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

def print_logs(loglist,comments=False):
    if CONFIG == CONFIG_APACHE:
        label='LOG_APACHE:'
    elif CONFIG == CONFIG_PHP:
        label='LOG_PHP:'
    elif CONFIG == CONFIG_MYSQL:
        label='LOG_MYSQL:'
    pad=''
    if comments:
        pad=COMMENT+label
    return '\n'.join((f'{pad}{l}' for l in loglist))

def help_menu():
    filename = os.path.basename(__file__)
    print(f'''{filename} usage:
{filename} [ -a [-c|-t] | -p [-c|-t] | -m [ -c|-t ] | -h ] [-r] [-i]
Options:
    -a: Select Apache mode
    -p: Select PHP mode
    -m: Select MySQL mode
    -h: This help

    -c: Show configfiles content
    -t: Show include tree hierarchy
    -l: Show logfiles used

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

    hierarchy,includes,content,logs=process_includes(CONFIG,{},[],[],[])

    if '-r' in params:
        comments = False
    else:
        comments = True
    if '-i' in params:
        llxamp_comments = True
    else:
        llxamp_comments = False

    if '-t' in params:
        if hierarchy:
            print(print_hierarchy(hierarchy,llxamp_comments).rstrip())
    if '-c' in params:
        if content:
            print(print_content(content,comments,llxamp_comments))
    if '-l' in params:
        if logs:
            print(print_logs(logs,llxamp_comments))
    return hierarchy,includes,content,logs

def set_mode_apache():
    global COMMENT, CONFIG, LOG_REGEXP, INCLUDE_REGEXP, CONF_EXT
    COMMENT = COMMENT_APACHE
    CONFIG = CONFIG_APACHE
    LOG_REGEXP = LOG_APACHE_REGEXP
    INCLUDE_REGEXP = INCLUDE_APACHE_REGEXP
    CONF_EXT = CONF_EXT_APACHE

def set_mode_php():
    global COMMENT, CONFIG, LOG_REGEXP, INCLUDE_REGEXP, CONF_EXT
    COMMENT = COMMENT_PHP
    CONFIG = CONFIG_PHP
    LOG_REGEXP = LOG_PHP_REGEXP
    INCLUDE_REGEXP = INCLUDE_PHP_REGEXP
    CONF_EXT = CONF_EXT_PHP

def set_mode_mysql():
    global COMMENT, CONFIG, LOG_REGEXP, INCLUDE_REGEXP, CONF_EXT
    COMMENT = COMMENT_MYSQL
    CONFIG = CONFIG_MYSQL
    LOG_REGEXP = LOG_MYSQL_REGEXP
    INCLUDE_REGEXP = INCLUDE_MYSQL_REGEXP
    CONF_EXT = CONF_EXT_MYSQL

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

    if '-m' in params:
        set_mode_mysql()
        process(params)

    sys.exit(0)

