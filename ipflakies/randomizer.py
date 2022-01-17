from ipflakies.utils import *
from ipflakies.initializers import *
import shutil
import hashlib


def random_generator(seed):
    hash = seed
    while True:
        hash = hashlib.md5(str(hash).encode(encoding='UTF-8')).hexdigest()
        yield(hash)


def random_test_suites(nround, seed, log=False):
    task = "random_suite"

    results = []
    print_title("-", "Randomizer")
    print("Running randomized test suites {} times with seed \"{}\"".format(nround, seed))

    progress = ProgressBar(nround, fmt=ProgressBar.FULL)
    for _, current_seed in zip(range(nround), random_generator(seed)):
        pytestargs = ["--random-order-seed={}".format(current_seed), \
            "--csv", CACHE_DIR + task + '/{}.csv'.format(current_seed)]
    
        std, err = pytest_cmd(pytestargs)
        try:
            random_test = pytestcsv(CACHE_DIR + task + '/{}.csv'.format(current_seed))
        except:
            print("\n{}".format(std))
            exit(0)
        
        results.append(random_test)

        if log:
            if not os.path.exists(LOG_DIR + task):
                os.makedirs(LOG_DIR + task)
            shutil.copy(CACHE_DIR + task + '/{}.csv'.format(current_seed), LOG_DIR + task + '/{}.csv'.format(current_seed))
            with open(LOG_DIR + task + '/{}.log'.format(current_seed), 'w') as f:
                f.write(std)
            if err:
                with open(LOG_DIR + task + '/{}.err'.format(current_seed), 'w') as f:
                    f.write(err)

        progress.current += 1
        progress()
    
    progress.done()  
    return results



def random_detection(target, it, tot, nviter=5):
    task = "random"

    print_title("-", "RANDOM ROUND {}/{}".format(it+1, tot))
    pytestargs = ["--random-order", "--csv", CACHE_DIR + task + '/{}.csv'.format(it), "-k", "not {}".format(res_dir_name)]
    std, err = pytest_cmd(pytestargs, stdout=False)
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
        if not verify(pytest_cmd, failing_sequence, "failed"):
            # Non-deternimistic failing order
            return(0)

    # Try reverse:
    else:
        print("Not a failing sequence, trying reverse order...")
        rev_seq = list(reversed(random_order["id"]))
        pytestargs = ["--csv", CACHE_DIR + task + '/{}_rev.csv'.format(it)] + rev_seq
        std, err = pytest_cmd(pytestargs, stdout=False)
        try:
            random_order_rev = pytestcsv(CACHE_DIR + task + '/{}_rev.csv'.format(it))
        except:
            return(0)
        index = random_order_rev["id"].index(target)
        failing_sequence = random_order_rev["id"][:index+1]
        print("Test {} {} at No.{}.".format(target, random_order["status"][index], index))
        if random_order["status"][index] != "passed":
            print("Found a potential failing sequence, verifying...")
            if not verify(pytest_cmd, failing_sequence, "failed"):
                # Non-deternimistic failing order
                return(0)
        else:
            print("Not a failing sequence.")
            return(0)

    #Delta Debugging
    print("Found a failing sequence: ")
    print(failing_sequence)

    return(1)