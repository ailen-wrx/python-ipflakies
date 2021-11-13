# coding=utf-8
import argparse

from ifixflakies.detector import *
from ifixflakies.initializers import *
from ifixflakies.random import * 
from ifixflakies.idflakies import *
from ifixflakies.patcher import *
import os
import json
import shutil
import random


data = dict()


def save_and_exit():
    # print(data)
    with open(SAVE_DIR+'Minimized.json', 'w') as f:
        json.dump(data, f)
    shutil.rmtree(CACHE_DIR)
    print("Result data written into {}.".format(SAVE_DIR))
    exit(0)


def parse_args():
    parser = argparse.ArgumentParser(description="""
            A tool for automatically fixing order-dependency flaky tests in python.
            """,)
    parser.add_argument("-f", "--fix", dest = "target_test", required=False, default=None,
                        help="the order-dependency test to be fixed")
    parser.add_argument('-i', '--it', dest="iterations", type=int, required=False, default=100,
                        help="times of run when executing random tests")
    parser.add_argument('-co', '--collect', dest="collect", required=False, action="store_true"
                        , help="collect and print all tests")
    parser.add_argument('-po', '--polluter', dest="polluter", required=False, action="store_true"
                        , help="only detect polluters without cleaners")
    parser.add_argument('-t', '--time', dest="time_count", required=False, action="store_true",
                        help="run the entire test suite and record the time")
    parser.add_argument('-p', dest="programmatic", required=False, action="store_true",
                        help="to run pytest programmatically")
    parser.add_argument('-r', '--random', dest="random", required=False, action="store_true",
                        help="do random analysis directly")
    parser.add_argument('-s', dest="scope", required=False, default="session",
                        help="scope of seeking: session(default), module or class")
    parser.add_argument('--nverdict', dest="verdict", type=int, required=False, default=10,
                        help="times of run when verdicting a single test")
    parser.add_argument('--nverify', dest="verify", type=int, required=False, default=4,
                        help="times of run when verifying a polluter, state-setter, or cleaner")
    parser.add_argument('--maxp', dest="maxp", type=int, required=False, default=0,
                        help="the maximum number of polluters taken into consideration")


    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    test = args.target_test

    pytest_method = pytest_pro if args.programmatic else pytest_cmd
    if args.verdict <= 1:
        print("[ERROR] Rounds of verdicting should be no less than 2.")

    test_list = collect_tests(pytest_method)

    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    if not test:
        flakies = idflakies(pytest_method, args.iterations)
        with open(SAVE_DIR+'Flakies.json', 'w') as f:
            json.dump(flakies, f)
        print("Result data written into {}.".format(SAVE_DIR))
        exit(0)
    elif test not in test_list:
        exit(1)

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


    print("============================ iFixFlakies ============================")

    if args.time_count:
        print("============================= TIME =============================")
        os.system("python3 -m pytest --cache-clear")
        # pytest.main([])

    if args.collect:
        print("============================= COLLECT =============================")
        for i, test in enumerate(test_list):
            print("[{}]  {}".format(i+1, test))
    print(len(test_list), "unit tests collected.")



    if (args.random):
        print("============================= RANDOM =============================")
        for i in range(args.iterations):
            if random_analysis(pytest_method, test, i, args.iterations):
                break
        save_and_exit()

    verd = verdict(pytest_method, test, args.verdict)
    print("{} is a potential {}.".format(test, verd))
    print()

    data["type"] = verd

    if verd == VICTIM:
        task_type = "polluter"
        data["polluter"] = []
    else:
        task_type = "state-setter"
        data["state-setter"] = []

    print("============================= {} =============================".format(task_type.upper()))
    task_scope = args.scope
    polluter_or_state_setter = find_polluter_or_state_setter(pytest_method, test_list, test, task_type, task_scope, args.verify)

    if polluter_or_state_setter:
        print(len(polluter_or_state_setter), task_type+'(s)', "for", test, "found:")
        for i, itest in enumerate(polluter_or_state_setter):
            print("[{}]  {}".format(i+1, itest))
            data[task_type].append(itest)
    else:
        print("No", task_type, "for", test, "found.")
        if verd == VICTIM:
            print("============================= RANDOM =============================")
            for i in range(100):
                if random_analysis(pytest_method, test, i):
                    break
        save_and_exit()
    print()


    if args.polluter or task_type == "state-setter":
        save_and_exit()
    
    data["cleaner"] = dict()
    data["patch"] = dict()

    if args.maxp and args.maxp < len(polluter_or_state_setter):
        print("List of polluter is truncated to size of", args.maxp)
        random.shuffle(polluter_or_state_setter)
        polluter_or_state_setter = polluter_or_state_setter[:args.maxp]


    print("========================== CLEANER & PATCH ==========================")
    for i, pos in enumerate(polluter_or_state_setter):
        print("{} / {}  Detecting cleaners for polluter {}.".format(i+1, len(polluter_or_state_setter), pos))
        cleaner = find_cleaner(pytest_method, test_list, pos, test, "session", args.verify)
        print("{} cleaner(s) for polluter {} found.".format(len(cleaner), pos))
        data["cleaner"][pos] = []
        data["patch"][pos] = []
        for i, itest in enumerate(cleaner):
            print("[{}]  {}".format(i+1, itest))
            data["cleaner"][pos].append(itest)
            patch, patchfile = fix_victim(pytest_method, pos, itest, test)
            if patch:
                print("[PATCH {}]".format(i+1))
                print(patch)
                data["patch"][pos].append({"diff": patch, "file": patchfile})
        print()
        print("-------------------------------------------------------------------")

    save_and_exit()
