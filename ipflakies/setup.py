import os
from setuptools import setup, find_packages

def _process_requirements():
    packages = open('requirements.txt').read().strip().split('\n')
    requires = []
    for pkg in packages:
        if pkg.startswith('git+ssh'):
            return_code = os.system('pip install {}'.format(pkg))
            assert return_code == 0, 'error, status_code is: {}, exit!'.format(return_code)
        else:
            requires.append(pkg)
    return requires

setup(
    name='ipflakies',
    version='0.1.1',
    description='A tool for automatically fixing order-dependency flaky tests in python.',
    author='Ruixin Wang, Yang Chen',
    url='https://github.com/ailen-wrx/python-ifixflakies',
    packages=find_packages(),
    install_requires=_process_requirements()
)
