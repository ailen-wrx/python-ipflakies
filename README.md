# python-ifixflakies
A tool for automatically detecting and fixing order-dependency python flaky tests developed in python.

## Environment
 - python 3.8 or higher

## Install
 - ( Make sure that the project is able to install dependencies required and run its pytest suite in a virtual environment )
  - Steps ( Before launching to pip )
    ```bash
    git clone https://github.com/ailen-wrx/python-ifixflakies

    git clone $project_url

    cd $project

    {python3.x} -m venv venv

    source venv/bin/activate

    # install all dependencies required for the current project
    pip install -r {requirements.txt}

    # make a soft link of the ifixflakies package to the library of the virtual environment
    ln -s python-ifixflakies/ifixflakies venv/lib/{python3.x}/site-packages/ifixflakies

    # install dependencies for ifixflakies
    pip install -r venv/lib/{python3.x}/site-packages/ifixflakies/requirements.txt

    python -m ifixflakies -h
    ```

## Run
### iDFlakies
```bash
python3 -m ifixflakies -i {iteration}
```

### iFixFlakies
```bash
python3 -m ifixflakies -f {target OD-test}
```

## Parameters
```
> python3 -m ifixflakies -h
usage: __main__.py [-h] [-f TARGET_TEST] [-i ITERATIONS] [-pro] [-r] [-s SCOPE] [--seed SEED] [--nverify VERIFY] [--nrerun RERUN] [--nseq SEQ] [--maxp MAXP]

A tool for automatically fixing order-dependency flaky tests in python.

optional arguments:
  -h, --help            show this help message and exit
  -f TARGET_TEST, --fix TARGET_TEST
                        the order-dependency test to be fixed
  -i ITERATIONS, --it ITERATIONS
                        times of run when executing random tests
  -pro                  to run pytest programmatically
  -r, --random          do random minimizing directly
  -s SCOPE              scope of minimizer: session, module or class, default = "session"
  --seed SEED           random seed used to generate randomized test suites
  --nverify VERIFY      times of running when verifying the result of a test sequence, default = 5
  --nrerun RERUN        number of passing or failing sequences to rerun when verifying the satbility of detected potential OD test, default = 5
  --nseq SEQ            number of passing or failing sequences to store when having detected a potential brittle or victim, default = 3
  --maxp MAXP           the maximum number of polluters taken into consideration, default = 0 (no limit)
```
 
