from ipflakies.utils import *
from ipflakies.initializers import *
import bidict
from bidict import bidict
import hashlib


def random_generator(seed):
    hash = seed
    while True:
        hash = hashlib.md5(str(hash).encode(encoding='UTF-8')).hexdigest()
        yield(hash)


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


def random_test_suites(pytest_method, nround, seed):
    task = "random_suite"

    results = []
    print("---------------------------- Randomizer ----------------------------")
    print("Running randomized test suites {} times with seed \"{}\"".format(nround, seed))

    pytestargs = ["--csv", CACHE_DIR + task + '/{}.csv'.format("normal")]

    std, err = pytest_method(pytestargs, stdout=False)
    try:
        normal_test = pytestcsv(CACHE_DIR + task + '/{}.csv'.format("normal"))
    except:
        print("\n{}".format(std))
        exit(0)
    
    results.append(normal_test)

    progress = ProgressBar(nround, fmt=ProgressBar.FULL)
    for _, current_seed in zip(range(nround), random_generator(seed)):
        pytestargs = ["--random-order-seed={}".format(current_seed), \
            "--csv", CACHE_DIR + task + '/{}.csv'.format(current_seed)]
    
        std, err = pytest_method(pytestargs)
        try:
            random_test = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(current_seed))
        except:
            print("\n{}".format(std))
            exit(0)
        
        results.append(random_test)

        progress.current += 1
        progress()
    
    progress.done()  
    return results


def random_analysis(pytest_method, test_list, results, nviter, nrerun, nseq):
    test_dict = bidict()
    flakies = dict()
    for index, test in enumerate(test_list):
        test_dict[index] = test

    passing = {}
    failing = {}
    for test in test_list:
        passing[test] = []
        failing[test] = []

    print("----------------------------- Analyzer -----------------------------")
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
                    if not verify(pytest_method, passing_seq, 'passed', rounds=nviter):
                        print("[iDFlakies] {} is Non-deterministic.".format(test))
                        flakies[test] = { "type": "NOD", 
                                       "detected_sequence": passing_seq }
                        NOD = True
                        break
                if NOD: continue
                for i2 in range(min(len(list(set_failing)), nrerun)):
                    failing_seq = seq_decoding(test_dict, list(set_failing)[i2])
                    if not verify(pytest_method, failing_seq, 'failed', rounds=nviter):
                        print("[iDFlakies] {} is Non-deterministic.".format(test))
                        flakies[test] = { "type": "NOD", 
                                       "detected_sequence": failing_seq }
                        NOD = True
                        break
                if not NOD: 
                    print("[iDFlakies] {} is order-dependent, checking whether it is a victim or a brittle...".format(test))
                    verd = verdict(pytest_method, test, nviter)
                    print("[iDFlakies] {} is a {}.".format(test, verd))
                    passing_orders = []
                    failing_orders = []
                    for i, passed in enumerate(list(set_passing)):
                        if i < nseq: passing_orders.append(seq_decoding(test_dict, passed))
                    for i, failed in enumerate(list(set_failing)):
                        if i < nseq: failing_orders.append(seq_decoding(test_dict, failed))
                    flakies[test] = { "type": verd, 
                                      "detected_sequence": passing_orders if verd == BRITTLE else failing_orders }
        
    print("============================== Result ==============================")
    print("{} flaky test(s) found in this project: ".format(len(flakies)))
    for i, key in enumerate(flakies):
        print("[{}] {} - {}".format(i+1, flakies[key]["type"], key))
    return flakies


def random_detection(pytest_method, target, it, tot, nviter=5):
    task = "random"

    print("----------------------- RANDOM ROUND {}/{} -----------------------".format(it+1, tot))
    pytestargs = ["--random-order", "--csv", CACHE_DIR + task + '/{}.csv'.format(it), "-k", "not {}".format(res_dir_name)]
    std, err = pytest_method(pytestargs, stdout=False)
    try:
        random_order = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(it))
    except:
        return(0)

    index = random_order["id"].index(target)
    failing_sequence = random_order["id"][:index+1]
    print("Test {} {} at No.{}.".format(target, random_order["status"][index], index))

    # Failing sequence detected:
    if random_order["status"][index] != "passed":
        print("Found a potential failing sequence, verifying...")
        if not verify(pytest_method, failing_sequence, "failed"):
            # Non-deternimistic failing order
            return(0)

    # Try reverse:
    else:
        print("Not a failing sequence, trying reverse order...")
        rev_seq = list(reversed(random_order["id"]))
        pytestargs = ["--csv", CACHE_DIR + task + '/{}_rev.csv'.format(it)] + rev_seq
        std, err = pytest_method(pytestargs, stdout=False)
        try:
            random_order_rev = pytestcsv(CACHE_DIR + task + '/{}_rev.csv'.format(it))
        except:
            return(0)
        index = random_order_rev["id"].index(target)
        failing_sequence = random_order_rev["id"][:index+1]
        print("Test {} {} at No.{}.".format(target, random_order["status"][index], index))
        if random_order["status"][index] != "passed":
            print("Found a potential failing sequence, verifying...")
            if not verify(pytest_method, failing_sequence, "failed"):
                # Non-deternimistic failing order
                return(0)
        else:
            print("Not a failing sequence.")
            return(0)

    #Delta Debugging
    print("Found a failing sequence: ")
    print(failing_sequence)

    return(1)