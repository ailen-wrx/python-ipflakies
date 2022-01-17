# coding=utf-8
import argparse

from ipflakies.detector import *
from ipflakies.initializers import *
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
    shutil.rmtree(CACHE_DIR)
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
    parser.add_argument('-r', '--rep', dest="reproduce", required=False, action="store_true",
                        help="rerun a test sequence in which the OD test is detected")
    parser.add_argument('-ls', '--list', dest="list", required=False, action="store_true",
                        help="list all flaky tests detected")
    parser.add_argument('--log', dest="log", required=False, action="store_true",
                        help="save the log files")
    parser.add_argument('-s', dest="scope", required=False, default="session",
                        help="scope of minimizer: session, module or class,\ndefault = \"session\"")
    parser.add_argument('--seed', dest="seed", required=False, default="ICSE_DEMO",
                        help="random seed used to generate randomized test suites")
    parser.add_argument('-v', '--verify', dest="verify", type=int, required=False, default=3,
                        help="times of running when verifying the result of a test sequence,\ndefault = 3")
    parser.add_argument('--rerun', dest="rerun", type=int, required=False, default=5,
                        help="number of passing or failing sequences to rerun when \n \
                             verifying the satbility of detected potential OD test,\ndefault = 5")
    parser.add_argument('--seq', dest="seq", type=int, required=False, default=3,
                        help="number of passing or failing sequences to store when \n \
                             having detected a potential brittle or victim,\ndefault = 3")
    parser.add_argument('--max-polluter', dest="maxp", type=int, required=False, default=0,
                        help="the maximum number of polluters taken into consideration,\ndefault = 0 (no limit)")
    parser.add_argument('--patch-mode', dest="patch_mode", required=False, default="first",
                            help="all: to detect all possible patches for the victim, \n \
                                (default) fisrt: to detect the first to fix all polluters")


    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    test = args.target_test
    repro = args.reproduce
    listonly = args.list
    log = args.log

    if args.verify <= 1:
        print("[ERROR] Rounds of verifying should be no less than 2.")
        exit(1)

    if not os.path.exists(SAVE_DIR+'flakies.json'):
        std, err = pytest_cmd([], stdout=True)
        if err:
            print("Fail to run test suite. Please make sure all dependencies required are correctly installed.")
            exit(1)

    test_list = collect_tests()

    md5 = hashlib.md5((str(test)+str(time.time())).encode(encoding='UTF-8')).hexdigest()[:8]
    SAVE_DIR_MD5 = SAVE_DIR + md5 + '/'

    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    if repro or listonly:
        if os.path.exists(SAVE_DIR+'flakies.json'):
            with open(SAVE_DIR+'flakies.json','r') as load_f:
                load_dict = json.load(load_f)
            
            print_title("=", "OD TESTS")
            keylist = [_ for _ in load_dict][:-1]
            for i, key in enumerate(keylist):
                print(" [{}] {}{}  {}".format(i+1, load_dict[key]['type'], " " if load_dict[key]['type']=="victim" else "" , key))
            
            if listonly:
                exit(0)

            key = int(input("Input the index of target OD test: "))
            seqs = load_dict[keylist[key-1]]
            print("{} is a {}.".format(keylist[key-1], seqs["type"]))
            print("{} {} in the following test sequences:".format(keylist[key-1], "passes" if seqs["type"]=="brittle" else "fails"))
            seqlist = [_ for _ in seqs["detected_sequence"]]
            for i, seq in enumerate(seqlist):
                print(" [{}]".format(i+1))
                for test in seq:
                    print("    {}".format(test))
            seq = int(input("Input the index of the test sequence to rerun: "))
            rerun = seqs["detected_sequence"][seq-1]
            pytest_cmd(rerun + ["-v", "--tb=no"], True)

            exit(0)
        else:
            print("File {} not found. Please run  python -m ipflakies  first.".format(SAVE_DIR+'flakies.json'))
            exit(1)


    if not test:
        time0 = time.time()
        print_title("=", "iDFlakies")
        flakies = idflakies_exust(test_list, args.iterations, args.seed, args.verify, args.rerun, args.seq, log)
        flakies["time"] = time.time() - time0
        with open(SAVE_DIR+'flakies.json', 'w') as f:
            json.dump(flakies, f)
        print("Summary data written into {}".format(SAVE_DIR+'flakies.json'))
        shutil.rmtree(CACHE_DIR)
        exit(0)
    
    elif test not in test_list:
        print("[ERROR]","{} does not belong to the test suit.".format(test))
        exit(1)

    if not os.path.exists(SAVE_DIR_MD5):
        os.makedirs(SAVE_DIR_MD5)

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


    print_title("=", "iFixFlakies")
    time1 = time.time()

    verd = verdict(test, args.verify)
    print("{} is a {}.".format(test, verd))
    print()

    data["target"] = test
    data["type"] = verd
    data["patch"] = False

    if verd == VICTIM:
        task_type = "polluter"
    else:
        task_type = "state-setter"

    data[task_type] = dict()

    print_title("=", task_type.upper())
    print_title("-", "[ Minimizer ]")

    task_scope = args.scope
    polluter_or_state_setter = find_polluter_or_state_setter(md5, test_list, test, task_type, task_scope, args.verify, log)

    if polluter_or_state_setter:
        print(len(polluter_or_state_setter), task_type+'(s)', "for", test, "found:")
        for i, itest in enumerate(polluter_or_state_setter):
            print("[{}]  {}".format(i+1, itest))
            data[task_type][itest] = []
    else:
        print("No", task_type, "for", test, "found.")
        # if verd == VICTIM:
        #     print_title("-", "[ Minimizer: random ]")
        #     for i in range(100):
        #         if random_detection(test, i, args.iterations):
        #             break
        save_and_exit(SAVE_DIR_MD5)
    print()
    

    if args.maxp and args.maxp < len(polluter_or_state_setter):
        print("[MINIMIZER]", "List of polluter is truncated to size of", args.maxp)
        random.shuffle(polluter_or_state_setter)
        polluter_or_state_setter = polluter_or_state_setter[:args.maxp]


    print_title("-", "[ Patcher ]")

    if verd==VICTIM:
        truncate = False
        for i, pos in enumerate(polluter_or_state_setter):
            print("{} / {}  Detecting cleaners for polluter {}.".format(i+1, len(polluter_or_state_setter), pos))
            cleaner = find_cleaner(md5, test_list, pos, test, "session", args.verify, log)
            print("{} cleaner(s) found.".format(len(cleaner)))
            # data[task_type][pos] = []
            for i, itest in enumerate(cleaner):
                print("[{}]  {}".format(i+1, itest))
                PatchInfo = fix_victim(pos, itest, test, polluter_or_state_setter, SAVE_DIR_MD5)
                """
                PatchInfo = dict()
                {"diff": ..., "patched_test_file": ..., "patch_file": ..., "time": ...}
                """
                data[task_type][pos].append({"cleaner": itest, "patch": PatchInfo})
                if PatchInfo and PatchInfo["fixed_polluter(s)"]:
                    data["patch"] = True
                    print("[Patcher]", "A patch is generated by Patcher: ")
                    for line in PatchInfo["diff"].split("\n"): print("[Patcher]", line)
                    print("[Patcher]", "The patch can fix the pollution from {}/{} polluters." \
                        .format(len(PatchInfo["fixed_polluter(s)"]), len(polluter_or_state_setter)))
                    if (args.patch_mode != 'all') and len(PatchInfo["fixed_polluter(s)"]) == len(polluter_or_state_setter):
                        truncate = True
                        print("[Patcher] Found a patch to fix all polluters. Stopped.")
                        print("[Patcher] Run with parameter --patch-mode=all to detect all possible patches.")
                        break
            if truncate:
                break

            print()
        print_title("=", "END")
        
    else:
        truncate = False
        for i, pos in enumerate(polluter_or_state_setter):
            print("[{}]  {}".format(i+1, pos))
            PatchInfo = fix_brittle(pos, test, SAVE_DIR_MD5)
            """
            PatchInfo = dict()
            {"diff": ..., "patched_test_file": ..., "patch_file": ..., "time": ...}
            """
            data[task_type][pos].append({"state-setter": pos, "patch": PatchInfo})
            if PatchInfo:
                data["patch"] = True
                print("[Patcher]", "A patch is generated by Patcher: ")
                for line in PatchInfo["diff"].split("\n"): print("[Patcher]", line)
                if (args.patch_mode != 'all'):
                    truncate = True
                    print("[Patcher] Found a patch to fix the brittle. Stopped.")
                    print("[Patcher] Run with parameter --patch-mode=all to detect all possible patches.")
                    break
            if truncate:
                break

            print()
        print_title("=", "END")


    data["time"] = time.time() - time1

    save_and_exit(SAVE_DIR_MD5)
