# coding=utf-8
import argparse

from ifixflakies.detector import *
from ifixflakies.initializers import *
from py import io
import pytest
import os
import pandas as pd
import shutil
import random

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
    parser.add_argument('-q', dest="time_count", required=False, action="store_true",
                        help="counting the time for entire test suite")
    parser.add_argument('-t', dest="type", required=False, default="victim",
                        help="type of the target test: victim(default) or brittle")
    parser.add_argument('-s', dest="scope", required=False, default="session",
                        help="scope of seeking: session(default), module or class")
    parser.add_argument('--nverd', dest="nverd", type=int, required=False, default=10,
                        help="times of run when verdicting a single test")
    parser.add_argument('--maxp', dest="maxp", type=int, required=False, default=0,
                        help="the maximum number of polluters taken into consideration")


    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    test = args.target_test
    test_list = collect_tests()

    if args.time_count:
        print("============================= TIME =============================")
        pytest.main([])
        exit(0)


    if args.collect_only:
        print("============================= COLLECT =============================")
        for i, test in enumerate(test_list):
            print("[{}]  {}".format(i+1, test))
        print(len(test_list), "tests collected.")
        exit(0)
    print(len(test_list), "unit tests collected.")
    print()

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    print("============================= VERDICT =============================")
    verd = verdict(test, args.nverd)
    print(test, "is a", verd+".")
    if args.verdict_only:
        exit(0)
    print()

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
    print("============================= {} =============================".format(task_type.upper()))
    task_scope = args.scope
    polluter_or_state_setter = find_polluter_or_state_setter(test_list, test, task_type, task_scope)
    if polluter_or_state_setter:
        print(len(polluter_or_state_setter), task_type+'(s)', "for", test, "found:")
        for i, itest in enumerate(polluter_or_state_setter):
            print("[{}]  {}".format(i+1, itest))
    else:
        print("No", task_type, "for", test, "found.")
    print()
    # input("Press Enter to continue...")


    if args.polluter_only or task_type == "state-setter":
        exit(0)

    if args.maxp and args.maxp < len(polluter_or_state_setter):
        print("List of polluter is truncated to size of", args.maxp)
        random.shuffle(polluter_or_state_setter)
        polluter_or_state_setter = polluter_or_state_setter[:args.maxp]


    print("============================= CLEANER =============================")
    for i, pos in enumerate(polluter_or_state_setter):
        print("{} / {}  Detecting cleaners for polluter {}.".format(i+1, len(polluter_or_state_setter), pos))
        cleaner = find_cleaner(test_list, pos, test, "session")
        print("{} cleaner(s) for polluter {} found.".format(len(cleaner), pos))
        if not args.counting_cleaner_only:
            for i, itest in enumerate(cleaner):
                print("[{}]  {}".format(i+1, itest))
    print("-------------------------------------------------------------------")

    shutil.rmtree(CACHE_DIR)
