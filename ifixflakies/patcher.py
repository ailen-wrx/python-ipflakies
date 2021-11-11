import ast
import csv
import difflib
from py import io
import re
import os
import shutil
import sys
from ifixflakies.utils.py import *
from ifixflakies.unparse import Unparser

class get_origin_astInfo(ast.NodeVisitor):
    def __init__(self,node):
        self.import_num = 0
        self.body = node.body

    def get_import_num(self):
        for object in self.body:
            if type(object) == ast.Import or type(object) == ast.ImportFrom:
                self.import_num += 1
        return self.import_num

def fix_victim(pytest_method, polluter, cleaner, victim, fixed):
    task = "patcher"

    victim_test = split_test(victim rmpara=True)
    cleaner_test = split_test(cleaner, rmpara=True)

    with open(victim_test["module"]) as f_victim:
        tree_victim = ast.parse(victim.read())
    with open(cleaner_test["module"]) as f_cleaner:
        tree_cleaner = ast.parse(cleaner.read())
        cleaner_info = get_origin_astInfo(tree_cleaner)
        cleaner_import_num = cleaner_info.get_import_num()

    minimal_patch_file=None
    patch_time_1st = None
    patch_time_all = None
    can_copy_work = None

    if verify(pytest_method, [polluter, cleaner, victim], "cleaner") \
        and verify(pytest_method, [polluter, victim], "polluter"):

        for import_obj in [module for module in ast.walk(tree_cleaner) if
                           isinstance(module, ast.Import) or isinstance(module, ast.ImportFrom)]:
            if ast.dump(import_obj) not in [ast.dump(module) for module in ast.walk(tree_victim) if
                                            isinstance(module, ast.Import) or isinstance(module, ast.ImportFrom)]:
                tree_victim.body.insert(0, import_obj)

        # get helper code from cleaner, handle setup, body and teardown 'module, method, class, function'
        # setup_module,setup_class,setup_function,setup_method,test_body,teardown_method,teardown_function,teardown_class,teardown_module

        name_node_dict = {'setup_module': None, 'setup_class': None, 'setup_function': None, 'setup_method': None,
                          cleaner_test["function"]: None,
                          'teardown_method': None, 'teardown_function': None, 'teardown_class': None, 'teardown_module': None}

        # get cleaner test body
        