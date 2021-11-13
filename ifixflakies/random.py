from ifixflakies.utils import *
from py import io
import hashlib


def random_analysis(pytest_method, target, it, nviter=2):
    task = "random"

    print("========================== RANDOM ROUND {} ==========================".format(it))
    pytestargs = ["--random-order", "--csv", CACHE_DIR + task + '/{}.csv'.format(it)]
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