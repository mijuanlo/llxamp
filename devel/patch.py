#!/usr/bin/env python3
import sys
import os
import time

patch_file = sys.argv[1]
PREFIX = sys.argv[2]
PREFIX = PREFIX.encode()
REPLACE = sys.argv[3]

if not os.path.exists(patch_file):
    print(f'Error "{patch_file}" not a file!')
    sys.exit(1)

size = len(PREFIX)
size2 = len(REPLACE)
padding = '/'*(size-size2)
last_slash_position = REPLACE[::-1].index('/')
last_slash_position = len(REPLACE[:-last_slash_position])
REPLACED = REPLACE[:last_slash_position] + padding + REPLACE[last_slash_position:]

buf=bytearray()
bakfile = patch_file+'.old'
content = None
new = None

with open(patch_file,'rb') as fp:
    content = fp.read()
    new = content.replace(PREFIX,REPLACED.encode())

# with open(bakfile,'wb') as fp:
#     fp.write(content)

with open(patch_file,'wb') as fp:
    fp.write(new)

# print(f'"{patch_file}" written')
sys.exit(0)
