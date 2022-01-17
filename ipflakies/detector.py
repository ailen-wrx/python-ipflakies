from ipflakies.utils import *
from py import io
import shutil
import hashlib


def find_polluter_or_state_setter(md5_t, test_list, victim_brittle, task="polluter", scope='session', nverify=4, log=False):
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
        std, err = pytest_cmd([test, victim_brittle, '--csv', CACHE_DIR + task + '/{}.csv'.format(md5)])
        try:
            paired_test = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(md5))
        except:
            print("\n{}".format(std))
            continue
        status = paired_test['status']
        if task == "polluter":
            if status[len(status)-1] != "passed":
                if verify([test, victim_brittle], "failed", nverify):
                    polluter_or_state_setter_list.append(test)
        elif task == "state-setter":
            if status[len(status)-1] == "passed":
                if verify([test, victim_brittle], "passed", nverify):
                    polluter_or_state_setter_list.append(test)

        if log:
            if not os.path.exists(LOG_DIR + md5_t + '/' + task):
                os.makedirs(LOG_DIR + md5_t + '/' + task)
            shutil.copy(CACHE_DIR + task + '/{}.csv'.format(md5), LOG_DIR + md5_t + '/' + task + '/{}.csv'.format(md5))
            with open(LOG_DIR + md5_t + '/' + task + '/{}.log'.format(md5), 'w') as f:
                f.write(std)
            if err:
                with open(LOG_DIR + md5_t + '/' + task + '/{}.err'.format(md5), 'w') as f:
                    f.write(err)

        progress.current += 1
        progress()
    progress.done()
    return polluter_or_state_setter_list

def find_cleaner(md5_t, test_list, polluter, victim, scope='session', nverify=4, log=False):
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
        std, err = pytest_cmd([polluter, test, victim, '--csv', CACHE_DIR + task + '/{}.csv'.format(md5)])
        try:
            paired_test = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(md5))
        except:
            print("\n{}".format(std))
            continue
        status = paired_test['status']
        if status[len(status)-1] == "passed":
            if verify([polluter, test, victim], "passed", nverify):
                cleaner_list.append(test)

        if log:
            if not os.path.exists(LOG_DIR + md5_t + '/' + task):
                os.makedirs(LOG_DIR + md5_t + '/' + task)
            shutil.copy(CACHE_DIR + task + '/{}.csv'.format(md5), LOG_DIR + md5_t + '/' + task + '/{}.csv'.format(md5))
            with open(LOG_DIR + md5_t + '/' + task + '/{}.log'.format(md5), 'w') as f:
                f.write(std)
            if err:
                with open(LOG_DIR + md5_t + '/' + task + '/{}.err'.format(md5), 'w') as f:
                    f.write(err)

        progress.current += 1
        progress()
    progress.done()
    return cleaner_list
