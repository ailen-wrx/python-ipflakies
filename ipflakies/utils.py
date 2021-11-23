import sys
import re
import csv
import pytest
import hashlib
from py import io
from func_timeout import func_set_timeout
from subprocess import Popen, PIPE

CACHE_DIR = 'cache/ipflakies/'
res_dir_name = 'ipflakies_result'
SAVE_DIR = '{}/'.format(res_dir_name)
TIME_OUT = 864

def split_test(test, rmpara=False):
    list = str(test).split("::")
    if len(list) == 3 or len(list) == 2:
        index = list[len(list)-1].index('[') if "[" in list[len(list)-1] \
            else len(list[len(list)-1])
        if index:
            para = list[len(list)-1][index:]
            func = list[len(list)-1][:index]
        return {"module":list[0],
                "class":list[1] if len(list)==3 else None,
                "function":func,
                "para": para if para else None}
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


@func_set_timeout(TIME_OUT)
def pytest_pro(args, stdout=False):
    if stdout:
        pytest.main(args)
        return None, None
    else:
        capture = io.StdCapture()
        pytest.main(args)
        std, err = capture.reset()
        return std, err


@func_set_timeout(TIME_OUT)
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


def verify(pytest_method, tests, assume, rounds=3):
    task = "verify"
    for i in range(rounds):
        md5 = hashlib.md5((",".join(tests)).encode(encoding='UTF-8')).hexdigest()
        pytestargs = ["--csv", CACHE_DIR + task + '/{}.csv'.format(md5)] + tests
        std, err = pytest_method(pytestargs)
        try:
            paired_test = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(md5))
        except:
            print("\n{}".format(std))
            continue
        status = paired_test['status']
        if status[len(status)-1] == "passed" and assume != "passed":
            return 0
        if status[len(status)-1] != "passed" and assume == "passed":
            return 0
    return 1


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
        print('\rComplete.                                                            ', file=self.output)