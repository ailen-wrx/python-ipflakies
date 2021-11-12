#coding:utf-8

import pytest


def setup_module():
    print ("\n[ setup_module_2 ]")

def teardown_module():
    print ("\n[ teardown_module_2 ]")

def test_2a():
    print('\ntest_2a')

def test_2b():
    print('\ntest_2b')
