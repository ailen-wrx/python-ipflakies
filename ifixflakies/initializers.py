from ifixflakies.utils import *
from py import io
import pytest
import pandas as pd
import os

ERRORS_FLAG = "= ERRORS ="
PYTEST_CO_STAT_FLAG = "tests collected in"

BRITTLE = "brittle"
VICTIM = "potential victim"


def collect_tests():
    capture = io.StdCapture()
    pytest.main(['--collect-only', '-q'])
    std, err = capture.reset()
    # TODO: improving the splitting rule to omit "ln" between "[]"
    test_list = list(filter(lambda x: x, std.split("\n")))
    err_ind = [i for i, x in enumerate(test_list) if ERRORS_FLAG in x]
    if err_ind:
        err_ind = err_ind[0]
        # TODO: print std error and exit
        exit(0)
    pytest_co_flag_ind = [i for i, x in enumerate(test_list) if PYTEST_CO_STAT_FLAG in x][0]
    del test_list[pytest_co_flag_ind]
    return test_list


def verdict(test, nverd):
    verdict_res = []
    progress = ProgressBar(nverd, fmt=ProgressBar.FULL)
    for ind in range(nverd):
        capture = io.StdCapture()
        pytest.main([test, '--csv', CACHE_DIR+'verdict'+'/{}.csv'.format(ind)])
        capture.reset()
        verd_test = pd.read_csv(CACHE_DIR+'verdict'+'/{}.csv'.format(ind))
        verdict_res.append(verd_test['status'][0])
        progress.current += 1
        progress()
    print()
    verdict_res = list(set(verdict_res))

    if len(verdict_res) > 1:
        print(len(verdict_res))
        # TODO: non-deterministic test
    return VICTIM if verdict_res[0] == "passed" else BRITTLE

