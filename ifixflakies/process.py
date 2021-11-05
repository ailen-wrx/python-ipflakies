# coding=utf-8
import argparse

from ifixflakies.detector import *
from py import io
import pytest
import os
import pandas as pd

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


def verdict(test):
    verdict_res = []
    capture = io.StdCapture()
    for ind in range(10):
        pytest.main([test, '--csv', CACHE_DIR+'verdict'+'/{}.csv'.format(ind)])
        verd_test = pd.read_csv(CACHE_DIR+'verdict'+'/{}.csv'.format(ind))
        verdict_res.append(verd_test['status'][0])
    capture.reset()
    verdict_res = list(set(verdict_res))
    if len(verdict_res) > 1:
        print(len(verdict_res))
        # TODO: non-deterministic test
    return VICTIM if verdict_res[0] == "passed" else BRITTLE


def parse_args():
    parser = argparse.ArgumentParser(description="""
            A tool for automatically fixing order-dependency flaky tests in python.
            """,)
    parser.add_argument("target_test", help="the target test id")
    parser.add_argument('-c', dest="collect_only", required=False, action="store_true", help="collect only")
    parser.add_argument('-v', dest="verdict_only", required=False, action="store_true", help="verdict only")
    parser.add_argument('-p', dest="polluter_only", required=False, action="store_true", help="polluter only")
    parser.add_argument('-e', dest="counting_cleaner_only", required=False, action="store_true",
                        help="only counting the number of cleaners, without printing them to the console")
    parser.add_argument('-t', dest="type", required=False, default="victim",
                        help="type of the target test: victim(default) or brittle")
    parser.add_argument('-s', dest="scope", required=False, default="session",
                        help="scope of seeking: session(default), module or class")

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    test = args.target_test
    test_list = collect_tests()

    if args.collect_only:
        print("======================= COLLECT =======================")
        for i in test_list:
            print('-', i)
        print(len(test_list), "tests collected.")
        exit(0)
    print(len(test_list), "unit tests collected.")

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    verd = verdict(test)
    if args.verdict_only:
        print("======================= VERDICT =======================")
        print(test, "is a", verd+".")
        exit(0)

    if args.type not in ["victim", "brittle"]:
        print("[ERROR]", "Cannot recognize argument TYPE: victim(default) or brittle")
        exit(2)

    if (verd == BRITTLE and args.type != 'brittle') or (verd == VICTIM and args.type != 'victim'):
        print("[ERROR]", test, "is not a", verd+",", "program exits.")
        exit(1)

    if args.scope not in ["session","module","class"]:
        print("[ERROR]", "Cannot recognize argument SCOPE: session(default), module or class")
        exit(2)

    task_type = "polluter" if args.type == "victim" else "state-setter"
    print("======================= {} =======================".format(task_type.upper()))
    task_scope = args.scope
    polluter_or_state_setter = find_polluter_or_state_setter(test_list, test, task_type, task_scope)
    if polluter_or_state_setter:
        print(len(polluter_or_state_setter), task_type+'(s)', "for", test, "found:")
        for i in polluter_or_state_setter:
            print('-', i)
    else:
        print("No", task_type, "for", test, "found.")
    input("Press Enter to continue...")


    if args.polluter_only or task_type == "state-setter":
        exit(0)
    print("======================= CLEANER =======================")
    for pos in polluter_or_state_setter:
        cleaner = find_cleaner(test_list, pos, test, "session")
        print(len(cleaner), 'cleaner(s)', "for polluter", pos, "found.")
        if not args.counting_cleaner_only:
            for i in cleaner:
                print('-', i)
