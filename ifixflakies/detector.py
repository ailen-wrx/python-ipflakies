
from ifixflakies.utils import *
from py import io
import hashlib
import pytest
import pandas as pd


def find_polluter_or_state_setter(test_list, victim_brittle, task="polluter", scope='session'):
    test_prefix = ""
    splited = split_test(victim_brittle)
    if scope == "module":
        test_prefix = splited["module"]
    elif scope == "class":
        if splited["class"]:
            test_prefix = splited = splited["module"] + "::" + splited["class"]
        else:
            test_prefix = splited = splited["module"]

    test_list = list(filter(lambda x: test_prefix in x and x != victim_brittle, test_list))

    polluter_or_state_setter_list = []

    progress = ProgressBar(len(test_list), fmt=ProgressBar.FULL)
    for test in test_list:
        md5 = hashlib.md5(test.encode(encoding='UTF-8')).hexdigest()
        capture = io.StdCapture()
        pytest.main([test, victim_brittle, '--csv', CACHE_DIR + task + '/{}.csv'.format(md5)])
        capture.reset()
        paired_test = pd.read_csv(CACHE_DIR + task + '/{}.csv'.format(md5))
        if task == "polluter":
            if paired_test['status'][1] != "passed":
                polluter_or_state_setter_list.append(test)
        elif task == "state-setter":
            if paired_test['status'][1] == "passed":
                polluter_or_state_setter_list.append(test)
        progress.current += 1
        progress()
    print()
    return polluter_or_state_setter_list

def find_cleaner(test_list, polluter, victim, scope='session'):

    task = "cleaner"

    test_prefix = ""
    splited = split_test(victim)
    if scope == "module":
        test_prefix = splited["module"]
    elif scope == "class":
        if splited["class"]:
            test_prefix = splited = splited["module"] + "::" + splited["class"]
        else:
            test_prefix = splited = splited["module"]

    test_list = list(filter(lambda x: test_prefix in x and x != victim and x != polluter, test_list))

    cleaner_list = []

    progress = ProgressBar(len(test_list), fmt=ProgressBar.FULL)
    for test in test_list:
        md5 = hashlib.md5((polluter+"-"+test).encode(encoding='UTF-8')).hexdigest()
        capture = io.StdCapture()
        pytest.main([polluter, test, victim, '--csv', CACHE_DIR + task + '/{}.csv'.format(md5)])
        capture.reset()
        paired_test = pd.read_csv(CACHE_DIR + task + '/{}.csv'.format(md5))
        if paired_test['status'][2] == "passed":
            cleaner_list.append(test)
        progress.current += 1
        progress()
    print()

    return cleaner_list