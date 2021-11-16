from ipflakies.utils import *
from py import io
import os

ERRORS_FLAG = "= ERRORS ="
WARNING_FLAG = "= warnings summary ="
PYTEST_CO_STAT_FLAG = ["tests collected ", "tests ran in"]

BRITTLE = "brittle"
VICTIM = "victim"


def collect_tests(pytest_method):
    std, err = pytest_method(['--collect-only', '-q', "-k", "not {}".format(res_dir_name)])
    test_list = list(filter(lambda x: x, re.split(r'\n\s*(?!\"[^()]*\))', std)))
    test_list = list(filter(lambda x: x, std.split("\n")))
    err_ind = [i for i, x in enumerate(test_list) if ERRORS_FLAG in x]
    if err_ind:
        err_ind = err_ind[0]
        # TODO: print std error and exit
        exit(0)
    for k in range(len(PYTEST_CO_STAT_FLAG)):
        pytest_co_flag_ind = [i for i, x in enumerate(test_list) if PYTEST_CO_STAT_FLAG[k] in x]
        if pytest_co_flag_ind:
            del test_list[pytest_co_flag_ind[0]]
    warn_ind = [i for i, x in enumerate(test_list) if WARNING_FLAG in x]
    if warn_ind:
        test_list = test_list[:warn_ind[0]]
    return test_list


def verdict(pytest_method, test, nverd=4):

    pytestargs_orig = ["-k", "not {}".format(res_dir_name)]
    pytest_method(pytestargs_orig, stdout=False)

    verdict_res = []
    verdict_stdout = []
    for ind in range(nverd):
        std, err = pytest_method([test, '--csv', CACHE_DIR+'verdict'+'/{}.csv'.format(ind)])
        try:
            verd_test = pytestcsv(CACHE_DIR+'verdict'+'/{}.csv'.format(ind))
        except:
            print("\n{}".format(std))
            continue
        verdict_res.append(verd_test['status'][0])
        verdict_stdout.append(std)
    verdict_res_uniq = list(set(verdict_res))

    if len(verdict_res_uniq) > 1:
        if pytest_method == pytest_pro and (verdict_res[:2] == ["passed", "failed"]):
            print("{} is likely to be a Non-Idempotent-Outcome test".format(test))
        else:
            print("{} is a Non-deterministic test.".format(test))
        for i in verdict_res_uniq:
            print("[{}]  {}\n{}".format(verdict_res.index(i), i, verdict_stdout[verdict_res.index(i)]))
        exit(0)
        # TODO: non-deterministic test
    return VICTIM if verdict_res[0] == "passed" else BRITTLE

