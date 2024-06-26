#!/usr/bin/env python3
import os
import re
import sys
import json
import pathlib
import datetime
import itertools
import subprocess
from datetime import date, timedelta
from argparse import ArgumentParser, Namespace

# Name of this script
script_name = sys.argv[0]

# Configurations
conf = Namespace(
        posting_indent=4,
        metadata_indent=8,
        decimal_align=50,
        precision={'ETH': 6},
        hashtag_chunk=re.compile(r'[0-9a-z]+')
        )

# Handle command line arguments
ap = ArgumentParser(description='Beancount journal distributor')
ap.add_argument('-f', '--files', nargs='*')
ap.add_argument('-r', '--repo')
ap.add_argument('-d', '--date')
ap.add_argument('-m', '--mono')
ap.add_argument('-t', '--tree')
ap.add_argument('-c', '--commit', action='store_true')
ap.add_argument('-p', '--push', action='store_true')
ap.add_argument('-v', '--verbose', action='count', default=0)
ap.add_argument('-s', '--message', default=f'Committed by {script_name}')
args = ap.parse_args()

def format_hashtags(line, sep=' ', prefix='#', chunk=conf.hashtag_chunk):
    """Re-format a string masking illegal characters.

    - All letters are converted to lowercase.
    - Tags are separated by `sep`.
    - Within each tag, chunks of legal characters are joined with '-'.
    - Legal character is defined in regex `chunk`.
    - Prefix of resulting hashtags can be customised through `prefix`.
    - This function is created to extract tags or links.
    """
    ls = line.lower().split(sep)
    ls = ['-'.join(chunk.findall(s)) for s in ls]

    return sep.join([f"{prefix}{s}" for s in ls if s])

class BeanMeta(Namespace):
    def __init__(self, **data):
        super().__init__(**data)
        for k, v in self.__dict__.items():
            if type(v) is str:
                self.__dict__[k] = v.strip()

    def __str__(self):
        return '\n'.join([' ' * conf.metadata_indent
                          + f"{k}: "
                          + (f'"{v.strip()}"' if type(v) is str else str(v))
                          for k, v in self.__dict__.items() if v])

class BeanSchedule(Namespace):
    def __init__(self, **data):
        super().__init__(**data)
        for k, v in self.__dict__.items():
            if v and type(v) is str:
                try:
                    self.__dict__[k] = date.fromisoformat(v.strip())
                except:
                    pass

        if not hasattr(self, 'expire'):
            self.expire = None

        if not hasattr(self, 'effective'):
            self.effective = None

    def check(self, d):
        """Check if date `d` is on the schedule.

        - `d` can be string or `datetime.date`.
        """
        if type(d) is str:
            d = date.fromisoformat(d.strip())
        elif type(d) is date:
            pass
        else:
            raise TypeError(f"Illegal type: {type(d)}.")

        if self.expire and d >= self.expire:
            return False

        if self.effective and d < self.effective:
            return False

        if self.type == 'intervals since':
            return (True if (d - self.since).days % self.interval == 0
                    else False)
        elif self.type == 'day of month':
            return True if d.day == self.day else False
        elif self.type == 'end of month':
            return True if (d + timedelta(days=1)).day == 1 else False
        elif self.type == 'day of months':
            return (True if d.month in self.months and d.day == self.day
                    else False)
        elif self.type == 'end of months':
            return (True if ((d + timedelta(days=1)).day == 1
                             and d.month in self.months)
                    else False)
        else:
            raise ValueError(f"Unexpected schedule type: {self.type}.")

class BeanPosting(Namespace):
    def __init__(self, **data):
        super().__init__()
        self.account = data.pop('account').strip()
        self.amount = data.pop('amount', 0)
        self.currency = data.pop('currency', '').strip()
        self.cost = data.pop('cost', '').strip()
        self.price = data.pop('price', '').strip()
        self.meta = BeanMeta(**data)

    def __str__(self):
        line = ' ' * conf.posting_indent + self.account

        if self.amount:
            p = conf.precision.get(self.currency, 2)
            amt_str = f"{self.amount:,.{p}f}"
            try:
                whole_amount_width = amt_str.index('.')
            except ValueError:
                whole_amount_width = len(amt_str)
            finally:
                pad = ' ' * max(conf.decimal_align
                                - conf.posting_indent
                                - len(self.account)
                                - whole_amount_width - 1, 2)
            line += pad + amt_str

            line += ' ' + self.currency if self.currency else ''
            line += ' ' + self.cost if self.cost else ''
            line += ' ' + self.price if self.price else ''

        meta = str(self.meta)
        line += '\n' + meta if meta else ''
        return line

class BeanTransaction(Namespace):
    def __init__(self, **data):
        super().__init__()
        self.date = data.pop('date', date_str).strip()
        self.flag = data.pop('flag', '*').strip()
        self.payee = data.pop('payee', '').strip()
        self.narration = data.pop('narration', '').strip()
        self.tags = format_hashtags(data.pop('tags', ''), prefix='#')
        self.links = format_hashtags(data.pop('links', ''), prefix='^')
        self.postings = [BeanPosting(**p) for p in data.pop('postings')]
        self.schedule = (BeanSchedule(**data.pop('schedule'))
                         if 'schedule' in data else None)
        self.meta = BeanMeta(**data)

    def __str__(self):
        if self.schedule and not self.schedule.check(self.date):
            return ''

        text = self.date + ' ' + self.flag
        text += ' "' + self.payee + '"' if self.payee else ''
        text += ' "' + self.narration + '"'
        text += ' ' + self.tags if self.tags else ''
        text += ' ' + self.links if self.links else ''

        meta = str(self.meta)
        text += '\n' + meta if meta else ''

        for p in self.postings:
            text += '\n' + str(p)

        return text + '\n'

class BeanOpen(Namespace):
    def __init__(self, **data):
        super().__init__()
        self.date = data.pop('date', date_str).strip()
        self.account = data.pop('account').strip()
        self.currencies = data.pop('currencies', '').strip()
        self.method = data.pop('method', '').strip()
        self.meta = BeanMeta(**data)

    def __str__(self):
        line = self.date + ' open ' + self.account
        line += ' ' + self.currencies if self.currencies else ''
        line += ' "' + self.method + '"' if self.method else ''
        meta = str(self.meta)
        line += '\n' + meta if meta else ''
        return line + '\n'

class BeanBalance(Namespace):
    def __init__(self, **data):
        super().__init__()
        self.date = data.pop('date', date_str).strip()
        self.account = data.pop('account').strip()
        self.amount = data.pop('amount')
        self.currency = data.pop('currency', '').strip()
        self.schedule = (BeanSchedule(**data.pop('schedule'))
                         if 'schedule' in data else None)
        self.meta = BeanMeta(**data)

    def __str__(self):
        if self.schedule and not self.schedule.check(self.date):
            return ''

        p = conf.precision.get(self.currency, 2)
        amt_str = f"{self.amount:,.{p}f}"
        meta = str(self.meta)
        line = f"{self.date} balance {self.account} {amt_str} {self.currency}"
        line += '\n' + meta if meta else ''
        return line + '\n'

class BeanPad(Namespace):
    def __init__(self, **data):
        super().__init__()
        self.date = data.pop('date', date_str).strip()
        self.account = data.pop('account').strip()
        self.pad = data.pop('pad').strip()
        self.schedule = (BeanSchedule(**data.pop('schedule'))
                         if 'schedule' in data else None)
        self.meta = BeanMeta(**data)

    def __str__(self):
        if self.schedule and not self.schedule.check(self.date):
            return ''

        meta = str(self.meta)
        line = f"{self.date} pad {self.account} {self.pad}"
        line += '\n' + meta if meta else ''
        return line + '\n'

request_handlers = {'txn': BeanTransaction,
                    'open': BeanOpen,
                    'pad': BeanPad,
                    'balance': BeanBalance}

def triage(**kwargs):
    cls = request_handlers[kwargs.pop('directive', 'txn')]
    return cls(**kwargs)

def parse_request_text(req_text):
    data = json.loads(req_text)

    if type(data) is dict:
        return [triage(**data)]
    elif type(data) is list:
        return [triage(**d) for d in data]
    else:
        raise TypeError(f'Unexpected data type: {type(data)}.')

def parse_request_file(filename):
    with open(filename, 'r') as f:
        try:
            return parse_request_text(f.read())
        except json.decoder.JSONDecodeError:
            raise ValueError(f"Bad JSON file: {f}")

if not hasattr(sys, 'ps1'):
    if args.date:
        date_str = args.date
    else:
        date_str = date.today().isoformat()

    # Non-interactive run
    if args.files:
        requests = itertools.chain.from_iterable(
                [parse_request_file(f) for f in args.files]
                )
    else:
        requests = parse_request_text(sys.stdin.read())

    journals = [str(r) for r in requests]

    if args.verbose >= 1:
        _ = [sys.stdout.write(j + '\n') for j in journals if j]

    if args.mono:
        fn = args.mono if not args.repo else os.path.join(args.repo, args.mono)
        pathlib.Path(os.path.dirname(fn)).mkdir(parents=True, exist_ok=True)
        with open(fn, 'a') as fd:
            _ = [fd.write('\n' + j) for j in journals if j]
        if args.repo:
            subprocess.run(['git', '-C', args.repo, 'add', args.mono])

    if args.tree:
        for j in journals:
            if not j:
                continue

            d = date.fromisoformat(j[:10])
            subtree = os.path.join(f"{d.year:04d}", f"{d.month:02d}.bean")
            fn = (os.path.join(args.tree, subtree) if not args.repo
                  else os.path.join(args.repo, args.tree, subtree))
            pathlib.Path(os.path.dirname(fn)).mkdir(parents=True,
                                                    exist_ok=True)
            with open(fn, 'a') as fd:
                fd.write('\n' + j)
            if args.repo:
                subprocess.run(['git', '-C', args.repo, 'add',
                                os.path.join(args.tree, subtree)])

    if args.repo:
        if args.commit:
            subprocess.run(['git', '-C', args.repo,
                            'commit', '-m', args.message])
        if args.push:
            subprocess.run(['git', '-C', args.repo, 'push'])

