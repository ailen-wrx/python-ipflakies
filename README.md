# iPFlakies
A tool for automatically detecting and fixing order-dependent Python flaky tests.

## Environment
 - Python 3.8 or higher

## Install
```bash
pip install ipflakies

python -m ipflakies -h
```

## Run
 - Be sure to first properly setup and install the dependencies required by your project and that you are able to run the project's test suite using `python3 -m pytest`.

### iDFlakies
```bash
python3 -m ipflakies -i {iteration}
```

### iPFlakies
```bash
python3 -m ipflakies -t {target OD-test}
```

## Parameters
```
$ python3 -m ipflakies -h                                                                  ✭
usage: __main__.py [-h] [-t TARGET_TEST] [-i ITERATIONS] [-r] [-s SCOPE] [--seed SEED] [--nverify VERIFY] [--nrerun RERUN]
                   [--nseq SEQ] [--maxp MAXP] [--patch-mode PATCH_MODE]

A framework for automatically detecting and fixing Python order-dependent flaky tests.

optional arguments:
  -h, --help            show this help message and exit
  -t TARGET_TEST, --test TARGET_TEST
                        the order-dependency test to be fixed
  -i ITERATIONS, --it ITERATIONS
                        times of run when executing random tests
  -r, --random          do random minimizing directly
  -s SCOPE              scope of minimizer: session, module or class, default = "session"
  --seed SEED           random seed used to generate randomized test suites
  --nverify VERIFY      times of running when verifying the result of a test sequence, default = 5
  --nrerun RERUN        number of passing or failing sequences to rerun when verifying the satbility of detected potential OD
                        test, default = 5
  --nseq SEQ            number of passing or failing sequences to store when having detected a potential brittle or victim,
                        default = 3
  --maxp MAXP           the maximum number of polluters taken into consideration, default = 0 (no limit)
  --patch-mode PATCH_MODE
                        all: to detect all possible patches for the victim, (default) fisrt: to detect the first to fix all
                        polluters
```
