from ifixflakies.utils import *
from py import io
import hashlib


def random_analysis(pytest_method, target, it, nviter=2):
    task = "random"
    pytestargs = ["--random-order", "--csv", CACHE_DIR + task + '/{}.csv'.format(it)]
    std, err = pytest_method(pytestargs, stdout=True)
    try:
        random_order = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(it))
    except:
        return(0)

    # Failing sequence detected:
    index = random_order["id"].index(target)
    failing_sequence = random_order["id"][:index+1]
    if random_order["status"][index] != "passed":
        print("Found a potential failing sequence")
        for viter in range(nviter):
            pytestargs = failing_sequence + [CACHE_DIR + task + '/{}_v{}.csv'.format(it, viter)]
            std, err = pytest_method(pytestargs, stdout=True)
            try:
                test_sequence = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(it))
            except:
                continue
            status = test_sequence["status"]
            if status[len(status)-1] == "passed":
                return(0)
    else:
        return(0)

    #Delta Debugging
    print("Found a failing sequence: ")
    print(failing_sequence)

    return(1)