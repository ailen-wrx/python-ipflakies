from ifixflakies.utils import *
from ifixflakies.initializers import verdict
from py import io
import hashlib


def idflakies(pytest_method, nrounds, nverify=5):
    print("============================= iDFlakies =============================")

    task = "idflakies"
    pytestargs = ["--csv", CACHE_DIR + task + '/{}.csv'.format("original")]
    std, err = pytest_method(pytestargs, stdout=False)
    try:
        original_order = pytestcsv(CACHE_DIR + task + '/{}.csv'.format("original"))
    except:
        return(0)

    flakies = dict()

    for it in range(nrounds):
        print("========================= iDFlakies ROUND {} =========================".format(it))
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
                if verify(pytest_method, flaky_sequence, "failed", nverify):
                    verd = verdict(pytest_method, target)
                    print("[FLAKY]", "{} is a {}.".format(target, verd))
                    flakies[target] = {"type": verd, "sequence": random_order["id"]}

    print("============================== Result ==============================")
    print("{} Order-dependency found in this project: ".format(len(flakies)))
    for i, key in enumerate(flakies):
        print("[{}] {} - {}".format(i+1, flakies[key]["type"], key))

    return(flakies)

        
