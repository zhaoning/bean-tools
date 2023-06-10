#!/usr/bin/env python3
import re
import sys
import argparse

parser = argparse.ArgumentParser(description='Beancount journal distributor')

# monolithic
# tree
pg_mode = parser.add_mutually_exclusive_group()
pg_mode.add_argument('-m', '--mono')
pg_mode.add_argument('-t', '--tree')

args = parser.parse_args()

print(args.tree)
print('------------')
print(args.mono)
