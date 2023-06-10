#!/usr/bin/env python3
import re
import sys
import argparse

parser = argparse.ArgumentParser(description='Beancount journal distributor')

pg_mode = parser.add_mutually_exclusive_group()
pg_mode.add_argument('-m', '--mono')
pg_mode.add_argument('-t', '--tree')

parser.add_argument('--posting-indent')

args = parser.parse_args()

print(args.tree)
print('------------')
print(args.mono)
print(args.posting_indent)

#stdin = sys.stdin.read()

if args.mono:
    pass
elif args.tree:
    pass
else:
    pass

