
from ifixflakies.utils import *
from py import io
import hashlib


def verify(tests, type, rounds, pytest_method):
    for i in range(rounds):
        task = "verdict_multitests"
        pytestargs = tests + ["--csv", CACHE_DIR + task + '/{}.csv'.format(i)]
        capture = io.StdCapture()
        pytest.main(pytestargs)
        std, err = capture.reset()
        try:
            paired_test = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(i))
        except:
            print("\n{}".format(std))
            continue
        status = paired_test['status']
        if status[len(status)-1] == "passed" and type == "polluter":
            return 0
        if status[len(status)-1] != "passed" and (type == "state-setter" or type == "cleaner"):
            return 0
    return 1


def find_polluter_or_state_setter(pytest_method, test_list, victim_brittle, task="polluter", scope='session', nverify=4):
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
        std, err = pytest_method([test, victim_brittle, '--csv', CACHE_DIR + task + '/{}.csv'.format(md5)])
        try:
            paired_test = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(md5))
        except:
            print("\n{}".format(std))
            continue
        status = paired_test['status']
        if task == "polluter":
            if status[len(status)-1] != "passed":
                if verify([test, victim_brittle], "polluter", nverify, pytest_method):
                    polluter_or_state_setter_list.append(test)
        elif task == "state-setter":
            if status[len(status)-1] == "passed":
                if verify([test, victim_brittle], "state-setter", nverify):
                    polluter_or_state_setter_list.append(test)
        progress.current += 1
        progress()
    print()
    return polluter_or_state_setter_list

def find_cleaner(pytest_method, test_list, polluter, victim, scope='session', nverify=4):
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
        std, err = pytest_method([polluter, test, victim, '--csv', CACHE_DIR + task + '/{}.csv'.format(md5)])
        try:
            paired_test = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(md5))
        except:
            print("\n{}".format(std))
            continue
        status = paired_test['status']
        if status[len(status)-1] == "passed":
            if verify([polluter, test, victim], "cleaner", nverify, pytest_method):
                cleaner_list.append(test)
        progress.current += 1
        progress()
    print()

    return cleaner_list
