#!/usr/bin/env python3
import re
import sys
import json
from datetime import date, timedelta

posting_indent = 4
metadata_indent = 8
decimal_align = 50

precision = {'ETH': 6}


lowernums = re.compile(r'[0-9a-z]+')

def mask_list(line, sep=' ', chunk=lowernums):
    """Chop a string into a list and mask illegal characters.

    Legal character is defined in regex `chunk`.  This function is created to
    extract tags or links.
    """
    ls = line.lower().split(sep)
    ls = ['-'.join(chunk.findall(s)) for s in ls]

    return [s for s in ls if s]

def tags(line):
    """Format tags from comma separated string.
    """
    return ' '.join(['#' + s for s in mask_list(line)])


def links(line):
    """Format links from comma separated string.
    """
    return ' '.join(['^' + s for s in mask_list(line)])


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


def is_on_schedule(req_date, schedule):
    req_date = date.fromisoformat(req_date)
    expire = schedule.get('expire', '').strip()

    if expire and req_date >= date.fromisoformat(expire):
        return False

    if schedule['type'] == 'intervals since':
        d0 = date.fromisoformat(schedule['since'])
        return (True if (req_date - d0).days % schedule['interval'] == 0
                else False)
    elif schedule['type'] == 'day of month':
        return True if req_date.day == schedule['day'] else False
    elif schedule['type'] == 'end of month':
        return True if (req_date + timedelta(days=1)).day == 1 else False
    elif schedule['type'] == 'day of months':
        return (True if (req_date.month in schedule['months']
                         and req_date.day == schedule['day'])
                else False)
    else:
        return False


def noop(request):
    """Handlbe dummy directive `noop`, no operation.
    """
    return []


def txn(request):
    """Handle directive `txn`.
    """
    req = request.copy()

    schedule = req.pop('schedule', None)
    req_date = req.get('date', date.today().isoformat()).strip()
    if schedule:
        if is_on_schedule(req_date, schedule):
            req['date'] = req_date
        else:
            return []

    return transaction(req, copy=True)


def balance(request):
    """Handle directive `balance`.
    """
    pass


def pad(request):
    """Handle directive `pad`.
    """
    pass


def triage(request):
    """Process directive and call appropriate handlers.
    """
    handlers = {'txn': txn,
                'balance': balance,
                'pad': pad,
                'noop': noop}
    return handlers[request.pop('directive', 'txn')](request)


if not hasattr(sys, 'ps1'):
    # Non-interactive run
    request = json.loads(sys.stdin.read())
    request['beancount'] = triage(request)
    sys.stdout.write(json.dumps(request, indent=4))
    sys.stdout.write('\n')

