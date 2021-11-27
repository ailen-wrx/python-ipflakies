# coding=utf-8
import argparse

from ipflakies.detector import *
from ipflakies.initializers import *
from ipflakies.random import * 
from ipflakies.idflakies import *
from ipflakies.patcher import *
import os
import time
import json
import shutil
import hashlib
import random


data = dict()


def save_and_exit(SAVE_DIR_MD5):
    # print(data)
    with open(SAVE_DIR_MD5+'minimized.json', 'w') as f:
        json.dump(data, f)
    # shutil.rmtree(CACHE_DIR)
    print("Summary data written into {}".format(SAVE_DIR_MD5+'minimized.json'))
    exit(0)

# TODO: Change names of parameters
def parse_args():
    parser = argparse.ArgumentParser(description="""
            A framework for automatically detecting and fixing Python order-dependent flaky tests.
            """,)
    parser.add_argument("-t", "--test", dest = "target_test", required=False, default=None,
                        help="the order-dependency test to be fixed")
    parser.add_argument('-i', '--it', dest="iterations", type=int, required=False, default=100,
                        help="times of run when executing random tests")
    parser.add_argument('-pro', dest="programmatic", required=False, action="store_true",
                        help="to run pytest programmatically")
    parser.add_argument('-r', '--random', dest="random", required=False, action="store_true",
                        help="do random minimizing directly")
    parser.add_argument('-s', dest="scope", required=False, default="session",
                        help="scope of minimizer: session, module or class,\ndefault = \"session\"")
    parser.add_argument('--seed', dest="seed", required=False, default="ICSE_DEMO",
                        help="random seed used to generate randomized test suites")
    parser.add_argument('--nverify', dest="verify", type=int, required=False, default=5,
                        help="times of running when verifying the result of a test sequence,\ndefault = 5")
    parser.add_argument('--nrerun', dest="rerun", type=int, required=False, default=5,
                        help="number of passing or failing sequences to rerun when \n \
                             verifying the satbility of detected potential OD test,\ndefault = 5")
    parser.add_argument('--nseq', dest="seq", type=int, required=False, default=3,
                        help="number of passing or failing sequences to store when \n \
                             having detected a potential brittle or victim,\ndefault = 3")
    parser.add_argument('--maxp', dest="maxp", type=int, required=False, default=0,
                        help="the maximum number of polluters taken into consideration,\ndefault = 0 (no limit)")
    parser.add_argument('-all', '--all-patch', dest="all_patch", required=False, action="store_true",
                            help="to detect all possible patches for the victim instead of the first to fix all polluters")


    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    test = args.target_test

    pytest_method = pytest_pro if args.programmatic else pytest_cmd
    if args.verify <= 1:
        print("[ERROR] Rounds of verifying should be no less than 2.")

    std, err = pytest_method([], stdout=False)
    if err:
        print("Fail to run test suite. Please make sure all dependencies required are correctly installed.")
        return(0)

    test_list = collect_tests(pytest_method)

    md5 = hashlib.md5((str(test)+str(time.time())).encode(encoding='UTF-8')).hexdigest()
    SAVE_DIR_MD5 = SAVE_DIR + md5 + '/'

    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    if not test:

        print("============================= iDFlakies =============================")

        flakies = idflakies_exust(pytest_method, test_list, args.iterations, args.seed, args.verify, args.rerun, args.seq)
        # flakies = idflakies_dev(pytest_method, args.iterations)

        with open(SAVE_DIR+'flakies.json', 'w') as f:
            json.dump(flakies, f)
        print("Summary data written into {}".format(SAVE_DIR+'flakies.json'))
        exit(0)
    
    elif test not in test_list:
        print("[ERROR]","{} does not belong to the test suit.".format(test))
        exit(1)

    if not os.path.exists(SAVE_DIR_MD5):
        os.makedirs(SAVE_DIR_MD5)

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


    print("============================ iFixFlakies ============================")
    # TODO: Record Time for Minimizer

    if (args.random):
        print("---------------------- [ Minimizer: {} ] ----------------------".format("random"))
        for i in range(args.iterations):
            if random_detection(pytest_method, test, i, args.iterations):
                break
        save_and_exit(SAVE_DIR_MD5)

    verd = verdict(pytest_method, test, args.verify)
    print("{} is a {}.".format(test, verd))
    print()

    data["target"] = test
    data["type"] = verd

    if verd == VICTIM:
        task_type = "polluter"
    else:
        task_type = "state-setter"

    data[task_type] = dict()

    print("============================= {} =============================".format(task_type.upper()))
    print("---------------------- [ Minimizer: {} ] ----------------------".format(task_type))
    task_scope = args.scope
    polluter_or_state_setter = find_polluter_or_state_setter(pytest_method, test_list, test, task_type, task_scope, args.verify)

    if polluter_or_state_setter:
        print(len(polluter_or_state_setter), task_type+'(s)', "for", test, "found:")
        for i, itest in enumerate(polluter_or_state_setter):
            print("[{}]  {}".format(i+1, itest))
            data[task_type][itest] = []
    else:
        print("No", task_type, "for", test, "found.")
        if verd == VICTIM:
            print("---------------------- [ Minimizer: {} ] ----------------------".format("random"))
            for i in range(100):
                if random_detection(pytest_method, test, i, args.iterations):
                    break
        save_and_exit(SAVE_DIR_MD5)
    print()
    

    if args.maxp and args.maxp < len(polluter_or_state_setter):
        print("[MINIMIZER]", "List of polluter is truncated to size of", args.maxp)
        random.shuffle(polluter_or_state_setter)
        polluter_or_state_setter = polluter_or_state_setter[:args.maxp]


    print("----------------- [ Minimizer: cleaner & Patcher ] -----------------")
    truncate = False
    for i, pos in enumerate(polluter_or_state_setter):
        print("{} / {}  Detecting cleaners for polluter {}.".format(i+1, len(polluter_or_state_setter), pos))
        cleaner = find_cleaner(pytest_method, test_list, pos, test, "session", args.verify)
        print("{} cleaner(s) found.".format(len(cleaner)))
        # data[task_type][pos] = []
        for i, itest in enumerate(cleaner):
            print("[{}]  {}".format(i+1, itest))
            PatchInfo = fix_victim(pytest_method, pos, itest, test, polluter_or_state_setter, SAVE_DIR_MD5)
            """
            PatchInfo = dict()
            {"diff": ..., "patched_test_file": ..., "patch_file": ..., "time": ...}
            """
            data[task_type][pos].append({"cleaner": itest, "patch": PatchInfo})
            if PatchInfo and PatchInfo["fixed_polluter(s)"]:
                print("[Patcher]", "A patch is generated by Patcher: ")
                for line in PatchInfo["diff"].split("\n"): print("[Patcher]", line)
                print("[Patcher]", "The patch can fix the pollution from {}/{} polluters." \
                      .format(len(PatchInfo["fixed_polluter(s)"]), len(polluter_or_state_setter)))
                if (not args.all_patch) and len(PatchInfo["fixed_polluter(s)"]) == len(polluter_or_state_setter):
                    truncate = True
                    print("[Patcher] Found a patch to fix all polluters. Stopped.")
                    print("[Patcher] Run with parameter --all-patch to detect all possible patches.")
                    break
        if truncate:
            break

        print()
        print("-------------------------------------------------------------------")

    save_and_exit(SAVE_DIR_MD5)
