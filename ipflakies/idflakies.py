from ipflakies.randomizer import *
import bidict
from bidict import bidict


def feature(passed_or_failed):
    return "victim" if passed_or_failed == "failed" else "brittle"


def seq_encoding(test_dict, seq):
    encoded = []
    for test in seq:
        encoded.append(str(test_dict.inverse[test]))
    return ",".join(encoded)

def seq_decoding(test_dict, list):
    decoded = []
    for index in list.split(","):
        decoded.append(str(test_dict[int(index)]))
    return decoded


def random_analysis(test_list, results, nviter, nrerun, nseq):
    test_dict = bidict()
    flakies = dict()
    for index, test in enumerate(test_list):
        test_dict[index] = test

    passing = {}
    failing = {}
    for test in test_list:
        passing[test] = []
        failing[test] = []
    
    print_title("-", "Analyzer")
    for random_suite in results:
        for index, testid in enumerate(random_suite['id']):
            if random_suite['status'][index] == 'passed':
                passing[testid].append(seq_encoding(test_dict, random_suite['id'][:index+1]))
            else:
                failing[testid].append(seq_encoding(test_dict, random_suite['id'][:index+1]))

    for test in test_list:
        set_passing = set(passing[test])
        set_failing = set(failing[test])
        intersection = set_passing.intersection(set_failing)
        NOD = False
        if intersection:
            NOD = True
            failing_seq = []
            for i in list(intersection):
                failing_seq.append(seq_decoding(test_dict, i))
            print("[iDFlakies] {} is Non-deterministic.".format(test))
            flakies[test] = { "type": "NOD", 
                            "detected_sequence": failing_seq }
            continue
        else:
            if set_passing and set_failing:
                print("[iDFlakies] {} is a flaky test, checking whether it is non-deterministic or order-dependent...".format(test))
                for i1 in range(min(len(list(set_passing)), nrerun)):
                    passing_seq = seq_decoding(test_dict, list(set_passing)[i1])
                    if not verify(passing_seq, 'passed', rounds=nviter):
                        print("[iDFlakies] {} is Non-deterministic.".format(test))
                        flakies[test] = { "type": "NOD", 
                                       "detected_sequence": passing_seq }
                        NOD = True
                        break
                if NOD: continue
                for i2 in range(min(len(list(set_failing)), nrerun)):
                    failing_seq = seq_decoding(test_dict, list(set_failing)[i2])
                    if not verify(failing_seq, 'failed', rounds=nviter):
                        print("[iDFlakies] {} is Non-deterministic.".format(test))
                        flakies[test] = { "type": "NOD", 
                                       "detected_sequence": failing_seq }
                        NOD = True
                        break
                if not NOD: 
                    print("[iDFlakies] {} is order-dependent, checking whether it is a victim or a brittle...".format(test))
                    verd = verdict(test, nviter)
                    print("[iDFlakies] {} is a {}.".format(test, verd))
                    passing_orders = []
                    failing_orders = []
                    for i, passed in enumerate(list(set_passing)):
                        if i < nseq: passing_orders.append(seq_decoding(test_dict, passed))
                    for i, failed in enumerate(list(set_failing)):
                        if i < nseq: failing_orders.append(seq_decoding(test_dict, failed))
                    flakies[test] = { "type": verd, 
                                      "detected_sequence": passing_orders if verd == BRITTLE else failing_orders }
    
    print_title("=", "Result")
    print("{} flaky test(s) found in this project: ".format(len(flakies)))
    for i, key in enumerate(flakies):
        print("[{}] {}{}  {}".format(i+1, flakies[key]["type"], " " if flakies[key]['type']=="victim" else "" , key))
    return flakies


def idflakies_exust(test_list, nround, seed, nviter, nrerun, nseq, log):
    results = random_test_suites(nround, seed, log)
    flakies = random_analysis(test_list, results, nviter, nrerun, nseq)
    return flakies

