import re
from datetime import date
from argparse import ArgumentParser, Namespace

conf = Namespace(
        posting_indent=4,
        metadata_indent=8,
        decimal_align=50,
        precision={'ETH': 6},
        hashtag_chunk=re.compile(r'[0-9a-z]+')
        )

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

class BeanOpen(Namespace):
    def __init__(self, **data):
        super().__init__()
        self.date = data.pop('date', date.today().isoformat()).strip()
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
        return line

class BeanSchedule(Namespace):
    pass

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
        self.date = data.pop('date', date.today().isoformat()).strip()
        self.flag = data.pop('flag', '*').strip()
        self.payee = data.pop('payee', '').strip()
        self.narration = data.pop('narration', '').strip()
        self.tags = format_hashtags(data.pop('tags', ''), prefix='#')
        self.links = format_hashtags(data.pop('links', ''), prefix='^')
        self.postings = [BeanPosting(**p) for p in data.pop('postings')]
        self.meta = BeanMeta(**data)

    def __str__(self):
        text = self.date + ' ' + self.flag
        text += ' "' + self.payee + '"' if self.payee else ''
        text += ' "' + self.narration + '"'
        text += ' ' + self.tags if self.tags else ''
        text += ' ' + self.links if self.links else ''

        meta = str(self.meta)
        text += '\n' + meta if meta else ''

        for p in self.postings:
            text += '\n' + str(p)

        return text

a = {
        'date': '2021-11-17\n',
        'flag': ' *',
        'narration': 'Internal transfer',
        'tags': '&beijing+2008   %###tokYO.2020   ',
        'links': '^band-21t4',
        'note': ' Make sure I am trimmed   ',
        'postings': [
            {'account': ' Assets:Cash  ',
             'amount': 123.45,
             'currency': 'AUD ',
             'note': '!@#$%^&*()_'
            },
            {'account': 'Assets:CBA-Offset'}
            ]
        }

