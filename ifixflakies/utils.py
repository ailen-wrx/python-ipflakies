import sys
import re
import csv
import pytest
from py import io
from subprocess import Popen, PIPE

CACHE_DIR = './cache/ifixflakies/'

def split_test(test, rmpara=False):
    list = str(test).split("::")
    if len(list) == 3:
        return {"module":list[0],
                "class":list[1],
                "function":list[2] if not rmpara else
                list[2][:list[2].index('[')]}
    elif len(list) == 2:
        return {"module":list[0],
                "class": None,
                "function":list[1] if not rmpara else
                list[1][:list[1].index('[')]}
    else:
        # TODO: unexpected test id format
        return None


def pytestcsv(file):
    res = dict()
    COLUMNS = ['id','module','name','file','doc','markers','status','message','duration']
    with open(file, 'rt') as f:
        for row in csv.reader(f):
            if row[0] == 'id':
                for i in range(len(COLUMNS)):
                    res[COLUMNS[i]] = []
            else:
                for i in range(len(COLUMNS)):
                    res[COLUMNS[i]].append(row[i])
    return res


def pytest_pro(args, stdout=False):
    if stdout:
        pytest.main(args)
        return None, None
    else:
        capture = io.StdCapture()
        pytest.main(args)
        std, err = capture.reset()
        return std, err


def pytest_cmd(args, stdout=False):
    mainargs = ["python3", "-m", "pytest"] + args
    if stdout:
        process = Popen(mainargs)
        std, err = process.communicate()
        return None, None
    else:
        process = Popen(mainargs, stdout=PIPE, stderr=PIPE)
        std, err = process.communicate()
        return std.decode("utf-8"), err.decode("utf-8")


class ProgressBar(object):
    DEFAULT = 'Progress: %(bar)s %(percent)3d%%'
    FULL = '%(bar)s %(current)d/%(total)d (%(percent)3d%%) %(remaining)d to go'

    def __init__(self, total, width=40, fmt=DEFAULT, symbol='▇',
                 output=sys.stderr):
        assert len(symbol) == 1

        self.total = total
        self.width = width
        self.symbol = symbol
        self.output = output
        self.fmt = re.sub(r'(?P<name>%\(.+?\))d',
            r'\g<name>%dd' % len(str(total)), fmt)

        self.current = 0

    def __call__(self):
        percent = self.current / float(self.total)
        size = int(self.width * percent)
        remaining = self.total - self.current
        bar = '[' + self.symbol * size + ' ' * (self.width - size) + ']'

        args = {
            'total': self.total,
            'bar': bar,
            'current': self.current,
            'percent': percent * 100,
            'remaining': remaining
        }
        print('\r' + self.fmt % args, file=self.output, end='')

    def done(self):
        self.current = self.total
        self()
        print('', file=self.output)