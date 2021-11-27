from ipflakies.utils import *
from ipflakies.random import *


def feature(passed_or_failed):
    return "victim" if passed_or_failed == "failed" else "brittle"


def idflakies_exust(pytest_method, test_list, nround, seed, nviter, nrerun, nseq):
    results = random_test_suites(pytest_method, nround, seed)
    flakies = random_analysis(pytest_method, test_list, results, nviter, nrerun, nseq)
    return flakies


def idflakies_dev(pytest_method, nrounds, nverify=5):

    task = "idflakies"
    pytestargs_orig = ["--csv", CACHE_DIR + task + '/{}.csv'.format("original")]
    std, err = pytest_method(pytestargs_orig, stdout=False)
    try:
        original_order = pytestcsv(CACHE_DIR + task + '/{}.csv'.format("original"))
    except:
        return(0)

    flakies = dict()

    upper = nrounds // 3
    no_update = 0

    for it in range(nrounds):
        no_update += 1
        if no_update >= upper:
            print("BREAK.")
            break
        print("----------------------- iDFlakies ROUND {}/{} -----------------------".format(it+1, nrounds))
        pytestargs = ["--random-order", "--csv", CACHE_DIR + task + '/{}.csv'.format(it)]
        std, err = pytest_method(pytestargs, stdout=False)
        try:
            random_order = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(it))
        except:
            continue

        for i, target in enumerate(original_order['id']):
            random_index = random_order["id"].index(target)
            if random_order["status"][random_index] != original_order["status"][i]:
                flaky_sequence = random_order["id"][:random_index+1]
                verify_seq = []
                verify_od = dict()
                for iv in range(nverify):
                    pytestargs = ["--csv", CACHE_DIR + task + '/{}_verify_{}.csv'.format(it, iv)] + flaky_sequence
                    std, err = pytest_method(pytestargs)
                    try:
                        flaky_verify = pytestcsv(CACHE_DIR + task + '/{}_verify_{}.csv'.format(it, iv))
                    except:
                        print("\n{}".format(std))
                        continue
                    for key in flakies:
                        if key not in flaky_sequence[:-1] or flakies[key]["type"] == "NOD":
                            continue
                        index = flaky_verify['id'].index(key)
                        if key not in verify_od:
                            verify_od[key] = []
                        verify_od[key].append(flaky_verify['status'][index])
                    verify_seq.append(flaky_verify['status'][-1])


                # print(verify_od)
                for key in verify_od:
                    verify_set = list(set(verify_od[key]))
                    if len(verify_set) > 1:
                        no_update = 0
                        nod_seq = flaky_verify['id'][:flaky_verify['id'].index(key)]
                        print("[NOD]", "{} is Non-deterministic in a detected sequence.".format(key))
                        flakies[key] = {"type": "NOD", 
                                        "detected_sequence": nod_seq}

                verify_set = list(set(verify_seq))

                if target in flakies and flakies[target]["type"] == "NOD":
                    continue

                if len(verify_set) > 1:
                    no_update = 0
                    print("[NOD]", "{} is Non-deterministic in a detected sequence.".format(target))
                    flakies[target] = {"type": "NOD", 
                                       "detected_sequence": random_order["id"]}
                    continue

                if target in flakies and flakies[target]["type"] == feature(verify_set[0]):
                    continue

                if verify_set[0] == random_order["status"][random_index]:
                    no_update = 0
                    print("[OD]", "{} is a {}.".format(target, feature(verify_set[0])))
                    flakies[target] = {"type": feature(verify_set[0]), 
                                       "detected_sequence": random_order["id"]}
                    continue


    print("============================== Result ==============================")
    print("{} Order-dependency found in this project: ".format(len(flakies)))
    for i, key in enumerate(flakies):
        print("[{}] {} - {}".format(i+1, flakies[key]["type"], key))

    return(flakies)

        
