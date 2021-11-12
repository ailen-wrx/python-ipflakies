#coding:utf-8

import pytest


def setup_module():
    print ("\n[ setup_module_1 ]")

def teardown_module():
    print ("\n[ teardown_module_1 ]")

def test_1a():
    print('\ntest_1a')

def test_1b():
    print('\ntest_1b')
