#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
from setuptools import setup

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
    name = "ipflakies",
    version = "0.0.8",
    keywords = ["pip", "flaky_test","flaky"],
    description = "A tool for automatically detecting and fixing OD tests.",
    long_description = "A tool for automatically detecting and fixing order-dependency python flaky tests developed in python.",
    license = "MIT Licence",

    url = "https://github.com/ailen-wrx/python-ipflakies",
    author = "Ruixin Wang, Yang Chen",
    author_email = "wangrx1999@outlook.com, sunniercy@gmial.com",

    packages = ['ipflakies'],
    include_package_data = True,
    platforms = "Linux, MacOS",
    install_requires = _process_requirements()
)