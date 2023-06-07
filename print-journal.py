#!/usr/bin/env python3
import sys
import json

tdict = json.loads(sys.stdin.read())
_ = [print(j) for j in tdict['beancount']]

