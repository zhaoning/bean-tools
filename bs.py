import datetime

from beancount.core.amount import A
from beancount.core.data import Transaction, Posting

from beancount.parser import printer

def posting_from_dict(params: dict) -> Posting:
    """Create posting object from a dictionary"""

    p = {k: params.get(k, None)
         for k in Posting._fields
         if k != 'meta'}

    p['meta'] = {k: v
                 for k, v in params.items()
                 if k not in Posting._fields or k == 'meta'}

    if type(p['units']) is str:
        p['units'] = A(p['units'])

    return Posting(**p)

def transaction_from_dict(params: dict) -> Transaction:
    """Create transaction object from a dictionary"""

    t = {k: params.get(k, None)
         for k in Transaction._fields
         if k != 'meta' and k != 'postings'}

    t['postings'] = ([posting_from_dict(p) for p in params['postings']]
                     if 'postings' in params
                     else None)

    t['meta'] = {k: v
                 for k, v in params.items()
                 if k not in Transaction._fields or k == 'meta'}

    if type(t['date']) is str:
        t['date'] = datetime.datetime.strptime(t['date'], r'%Y-%m-%d').date()

    return Transaction(**t)

p1 = dict(account='Expenses:Dining-Out',
          units='5.00 AUD')
p2 = dict(account='Liabilities:Credit:AMEX-Pt')

t1 = dict(date='2024-02-11',
          flag='*',
          payee='Leible',
          comment='Price rise',
          postings=[p1, p2],
          meta='Nah')
