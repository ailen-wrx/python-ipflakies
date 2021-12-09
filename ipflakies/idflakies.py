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
        
    print("============================== Result ==============================")
    print("{} flaky test(s) found in this project: ".format(len(flakies)))
    for i, key in enumerate(flakies):
        print("[{}] {} - {}".format(i+1, flakies[key]["type"], key))
    return flakies


def idflakies_exust(test_list, nround, seed, nviter, nrerun, nseq):
    results = random_test_suites(nround, seed)
    flakies = random_analysis(test_list, results, nviter, nrerun, nseq)
    return flakies


# def idflakies_dev(nrounds, nverify=5):

#     task = "idflakies"
#     pytestargs_orig = ["--csv", CACHE_DIR + task + '/{}.csv'.format("original")]
#     std, err = pytest_cmd(pytestargs_orig, stdout=False)
#     try:
#         original_order = pytestcsv(CACHE_DIR + task + '/{}.csv'.format("original"))
#     except:
#         return(0)

#     flakies = dict()

#     upper = nrounds // 3
#     no_update = 0

#     for it in range(nrounds):
#         no_update += 1
#         if no_update >= upper:
#             print("BREAK.")
#             break
#         print("----------------------- iDFlakies ROUND {}/{} -----------------------".format(it+1, nrounds))
#         pytestargs = ["--random-order", "--csv", CACHE_DIR + task + '/{}.csv'.format(it)]
#         std, err = pytest_cmd(pytestargs, stdout=False)
#         try:
#             random_order = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(it))
#         except:
#             continue

#         for i, target in enumerate(original_order['id']):
#             random_index = random_order["id"].index(target)
#             if random_order["status"][random_index] != original_order["status"][i]:
#                 flaky_sequence = random_order["id"][:random_index+1]
#                 verify_seq = []
#                 verify_od = dict()
#                 for iv in range(nverify):
#                     pytestargs = ["--csv", CACHE_DIR + task + '/{}_verify_{}.csv'.format(it, iv)] + flaky_sequence
#                     std, err = pytest_cmd(pytestargs)
#                     try:
#                         flaky_verify = pytestcsv(CACHE_DIR + task + '/{}_verify_{}.csv'.format(it, iv))
#                     except:
#                         print("\n{}".format(std))
#                         continue
#                     for key in flakies:
#                         if key not in flaky_sequence[:-1] or flakies[key]["type"] == "NOD":
#                             continue
#                         index = flaky_verify['id'].index(key)
#                         if key not in verify_od:
#                             verify_od[key] = []
#                         verify_od[key].append(flaky_verify['status'][index])
#                     verify_seq.append(flaky_verify['status'][-1])


#                 # print(verify_od)
#                 for key in verify_od:
#                     verify_set = list(set(verify_od[key]))
#                     if len(verify_set) > 1:
#                         no_update = 0
#                         nod_seq = flaky_verify['id'][:flaky_verify['id'].index(key)]
#                         print("[NOD]", "{} is Non-deterministic in a detected sequence.".format(key))
#                         flakies[key] = {"type": "NOD", 
#                                         "detected_sequence": nod_seq}

#                 verify_set = list(set(verify_seq))

#                 if target in flakies and flakies[target]["type"] == "NOD":
#                     continue

#                 if len(verify_set) > 1:
#                     no_update = 0
#                     print("[NOD]", "{} is Non-deterministic in a detected sequence.".format(target))
#                     flakies[target] = {"type": "NOD", 
#                                        "detected_sequence": random_order["id"]}
#                     continue

#                 if target in flakies and flakies[target]["type"] == feature(verify_set[0]):
#                     continue

#                 if verify_set[0] == random_order["status"][random_index]:
#                     no_update = 0
#                     print("[OD]", "{} is a {}.".format(target, feature(verify_set[0])))
#                     flakies[target] = {"type": feature(verify_set[0]), 
#                                        "detected_sequence": random_order["id"]}
#                     continue


#     print("============================== Result ==============================")
#     print("{} Order-dependency found in this project: ".format(len(flakies)))
#     for i, key in enumerate(flakies):
#         print("[{}] {} - {}".format(i+1, flakies[key]["type"], key))

#     return(flakies)

        
