#!/usr/bin/env python3
import sys
import json

request = json.loads(sys.stdin.read())
_ = [print(j) for j in request.get('beancount', [])]

