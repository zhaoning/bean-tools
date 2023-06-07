#!/usr/bin/env python3
import re
import sys
import json

posting_indent = 4
metadata_indent = 8
decimal_align = 50
txn_reserve_keys = ['date', 'directive', 'flag', 'payee', 'narration',
                    'tags', 'links', 'beancount']

precision = {'ETH': 6}


alnums = re.compile(r'[0-9a-z]+')

def comma_list(line):
    """Parse comma-separated list and format for use as tags or links.
    """
    ls = line.lower().split(',')
    ls = ['-'.join(alnums.findall(s)) for s in ls]

    return [s for s in ls if s]

def tags(line):
    """Format tags from comma separated string.
    """
    return ' '.join(['#' + s for s in comma_list(line)])


def links(line):
    """Format links from comma separated string.
    """
    return ' '.join(['^' + s for s in comma_list(line)])


def metadata(adict):
    meta = '\n'.join([' ' * metadata_indent + f"{k}: \"{str(v).strip()}\""
                      for k, v in adict.items()])
    return meta


def posting(pdict, copy=False):
    """Format posting from a posting dict.
    """
    pd = pdict.copy() if copy else pdict

    account = pd.pop('account').strip()
    amount = pd.pop('amount', 0)
    currency = pd.pop('currency', '').strip()
    cost = pd.pop('cost', '').strip()
    price = pd.pop('price', '').strip()

    line = ' ' * posting_indent + account

    if amount:
        p = precision.get(currency, 2)
        amt_str = f"{amount:,.{p}f}"
        try:
            whole_amount_width = amt_str.index('.')
        except ValuaError:
            whole_amount_width = len(amt_str)
        finally:
            pad = ' ' * max(decimal_align
                            - posting_indent
                            - len(account)
                            - whole_amount_width - 1, 2)
        line += pad + amt_str

        line += ' ' + currency if currency else ''
        line += ' ' + cost if cost else ''
        line += ' ' + price if price else ''

    meta = metadata(pd)

    if meta:
        return line + '\n' + meta
    else:
        return line


def transaction(tdict, copy=False):
    """Format transaction header line from transaction dict.
    """
    td = tdict.copy() if copy else tdict
    _ = td.pop('beancount', None)
    _ = td.pop('schedule', None)

    head = td.pop('date') + ' ' + td.pop('flag', '*')

    if 'payee' in td:
        head += f" \"{td.pop('payee')}\""

    head += f" \"{td.pop('narration', '')}\""

    if 'tags' in td:
        head += ' ' + tags(td.pop('tags'))

    if 'links' in td:
        head += ' ' + links(td.pop('links'))

    post = '\n'.join([posting(p, copy=copy) for p in td.pop('postings')])

    meta = metadata(td)

    if meta:
        return [head + '\n' + meta + '\n' + post + '\n']
    else:
        return [head + '\n' + post + '\n']


if hasattr(sys, 'ps1'):
    # Interactive debugging
    tdict = {'date': '2021-07-28',
             'flag': '*',
             'payee': 'KFC',
             'narration': '',
             'note': 'I love Macca\'s',
             'postings': [{'account': 'Expenses:Dining-Out  ',
                           'amount': 2.99,
                           'note': 'Just kidding...\n',
                           'currency': ' AUD  '},
                          {'account': 'Assets:Checking:Virgin-Go '}],
             'tags': 'beijing.2012, ,,   #annual/leave  ',
             'links': 'ha^.^ha, hoho, ^proper-link'}
else:
    # Non-interactive run
    tdict = json.loads(sys.stdin.read())
    tdict['beancount'] = transaction(tdict, copy=True)
    print(json.dumps(tdict))

