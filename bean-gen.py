#!/usr/bin/env python3

#import os
#import re
#import sys
#import json
#import pathlib
import argparse
#import subprocess
#
from datetime import date, timedelta

# Handle command line arguments
parser = argparse.ArgumentParser(description='Beancount journal distributor')
parser.add_argument('-r', '--repo')
parser.add_argument('-m', '--mono')
parser.add_argument('-t', '--tree')
parser.add_argument('-c', '--commit', action='store_true')
parser.add_argument('-p', '--push', action='store_true')
parser.add_argument('-v', '--verbose', action='count', default=0)
parser.add_argument('-s', '--message', default='Committed by bean-gen')
parser.add_argument('--posting-indent', default=4, type=int)
parser.add_argument('--json-indent', default=4, type=int)
parser.add_argument('--metadata-indent', default=8, type=int)
parser.add_argument('--decimal-align', default=50, type=int)
args = parser.parse_args()

class BeanRequest:
    """One single beancount request.
    """
    def __init__(self, **data):
        self.__dict__.update(data)

    def __repr__(self):
        return self.__dict__.__repr__()

class BeanPosting(BeanRequest):
    """Beancount transaction posting request.
    """
    def __init__(self, **data):
        super().__init__(**data)
        self.validate()

    def validate(self):
        if not hasattr(self, 'account'):
            raise KeyError('Account required in BeanPosting.')

    def __str__(self):
        pass

class BeanTransaction(BeanRequest):
    """Beancount transaction request.
    """
    def __init__(self, **data):
        postings = data.pop('postings')
        super().__init__(**data)
        self.postings = [BeanPosting(**p) for p in postings]
        self.validate()

    def validate(self):
        if not hasattr(self, 'date'):
            self.date = date.today().isoformat()

        if not hasattr(self, 'narration'):
            self.narration = ''

        if not hasattr(self, 'postings'):
            raise KeyError('Postings not found in BeanTransaction.')

    def __str__(self):
        pass

class BeanOpen(BeanRequest):
    """One single beancount open request.
    """
    def __init__(self, **data):
        super().__init__(**data)
        self.validate()

    def validate(self):
        if not hasattr(self, 'date'):
            self.date = date.today().isoformat()

        if not hasattr(self, 'account'):
            raise KeyError('Account required in BeanOpen.')

    def journals(self):
        pass

#precision = {'ETH': 6}
#
#lowernums = re.compile(r'[0-9a-z]+')
#
#def mask_list(line, sep=' ', chunk=lowernums):
#    """Chop a string into a list and mask illegal characters.
#
#    Legal character is defined in regex `chunk`.  This function is created to
#    extract tags or links.
#    """
#    ls = line.lower().split(sep)
#    ls = ['-'.join(chunk.findall(s)) for s in ls]
#
#    return [s for s in ls if s]
#
#def tags(line):
#    """Format tags from comma separated string.
#    """
#    return ' '.join(['#' + s for s in mask_list(line)])
#
#
#def links(line):
#    """Format links from comma separated string.
#    """
#    return ' '.join(['^' + s for s in mask_list(line)])
#
#
#def metadata(adict):
#    meta = '\n'.join([' ' * args.metadata_indent + f"{k}: \"{str(v).strip()}\""
#                      for k, v in adict.items() if v])
#    return meta
#
#
#def posting(pdict, copy=True):
#    """Format posting from a posting dict.
#    """
#    pd = pdict.copy() if copy else pdict
#
#    account = pd.pop('account').strip()
#    amount = pd.pop('amount', 0)
#    currency = pd.pop('currency', '').strip()
#    cost = pd.pop('cost', '').strip()
#    price = pd.pop('price', '').strip()
#
#    line = ' ' * args.posting_indent + account
#
#    if amount:
#        p = precision.get(currency, 2)
#        amt_str = f"{amount:,.{p}f}"
#        try:
#            whole_amount_width = amt_str.index('.')
#        except ValuaError:
#            whole_amount_width = len(amt_str)
#        finally:
#            pad = ' ' * max(args.decimal_align
#                            - args.posting_indent
#                            - len(account)
#                            - whole_amount_width - 1, 2)
#        line += pad + amt_str
#
#        line += ' ' + currency if currency else ''
#        line += ' ' + cost if cost else ''
#        line += ' ' + price if price else ''
#
#    meta = metadata(pd)
#
#    if meta:
#        return line + '\n' + meta
#    else:
#        return line
#
#
#def transaction(tdict):
#    """Format transaction line from transaction dict.
#    """
#    head = tdict.pop('date') + ' ' + tdict.pop('flag', '*')
#
#    if 'payee' in tdict:
#        head += f" \"{tdict.pop('payee')}\""
#
#    head += f" \"{tdict.pop('narration', '')}\""
#
#    if 'tags' in tdict and tdict['tags']:
#        head += ' ' + tags(tdict.pop('tags'))
#
#    if 'links' in tdict and tdict['links']:
#        head += ' ' + links(tdict.pop('links'))
#
#    post = '\n'.join([posting(p) for p in tdict.pop('postings')])
#
#    meta = metadata(tdict)
#
#    if meta:
#        return [head + '\n' + meta + '\n' + post + '\n']
#    else:
#        return [head + '\n' + post + '\n']
#
#
#def is_on_schedule(req_date, schedule):
#    req_date = date.fromisoformat(req_date)
#    expire = schedule.get('expire', '').strip()
#
#    if expire and req_date >= date.fromisoformat(expire):
#        return False
#
#    if schedule['type'] == 'intervals since':
#        d0 = date.fromisoformat(schedule['since'])
#        return (True if (req_date - d0).days % schedule['interval'] == 0
#                else False)
#    elif schedule['type'] == 'day of month':
#        return True if req_date.day == schedule['day'] else False
#    elif schedule['type'] == 'end of month':
#        return True if (req_date + timedelta(days=1)).day == 1 else False
#    elif schedule['type'] == 'day of months':
#        return (True if (req_date.month in schedule['months']
#                         and req_date.day == schedule['day'])
#                else False)
#    else:
#        return False
#
#
#def noop(request):
#    """Handlbe dummy directive `noop`, no operation.
#    """
#    return []
#
#
#def txn(request):
#    """Handle directive `txn`.
#    """
#    schedule = request.pop('schedule', None)
#    req_date = request.get('date', date.today().isoformat()).strip()
#    if schedule:
#        if is_on_schedule(req_date, schedule):
#            request['date'] = req_date
#        else:
#            return []
#
#    return transaction(request)
#
#
#def balance(request):
#    """Handle directive `balance`.
#    """
#    line = request.pop('date') + ' balance ' + request.pop('account')
#    amount = request.pop('amount')
#    currency = request.pop('currency')
#    p = precision.get(currency, 2)
#    line += f" {amount:,.{p}f} {currency}\n"
#    return [line]
#
#
#def pad(request):
#    """Handle directive `pad`.
#    """
#    pass
#
#
#def gen_journal(request):
#    """Process directive and call appropriate handlers.
#    """
#    req = request.copy()
#    _ = req.pop('beancount', None)
#    _ = req.pop('message', None)
#
#    handlers = {'txn': txn,
#                'balance': balance,
#                'pad': pad,
#                'noop': noop}
#    return handlers[req.pop('directive', 'txn')](req)
#
#
#def tree_file(journal):
#    """Decide which file to write a journal entry to under tree method.
#    """
#    d = date.fromisoformat(journal[:10])
#    return os.path.join(f"{d.year:04d}", f"{d.month:02d}.bean")
#
#
#if not hasattr(sys, 'ps1'):
#    # Non-interactive run
#    request = json.loads(sys.stdin.read())
#    journals = gen_journal(request)
#
#    if args.verbose == 1:
#        _ = [sys.stdout.write(j + '\n') for j in journals]
#    elif args.verbose == 2:
#        request['beancount'] = journals
#        sys.stdout.write(json.dumps(request, indent=args.json_indent) + '\n')
#
#    if args.mono:
#        fn = args.mono if not args.repo else os.path.join(args.repo, args.mono)
#        pathlib.Path(os.path.dirname(fn)).mkdir(parents=True, exist_ok=True)
#        with open(fn, 'a') as fd:
#            _ = [fd.write('\n' + j) for j in journals]
#        if args.repo:
#            subprocess.run(['git', '-C', args.repo, 'add', args.mono])
#
#    if args.tree:
#        for j in journals:
#            subtree = tree_file(j)
#            fn = (os.path.join(args.tree, subtree) if not args.repo
#                  else os.path.join(args.repo, args.tree, subtree))
#            pathlib.Path(os.path.dirname(fn)).mkdir(parents=True,
#                                                    exist_ok=True)
#            with open(fn, 'a') as fd:
#                fd.write('\n' + j)
#            if args.repo:
#                subprocess.run(['git', '-C', args.repo, 'add',
#                                os.path.join(args.tree, subtree)])
#
#    if args.repo:
#        message = request.get('message', args.message)
#        if args.commit:
#            subprocess.run(['git', '-C', args.repo, 'commit', '-m', message])
#        if args.push:
#            subprocess.run(['git', '-C', args.repo, 'push'])
#
