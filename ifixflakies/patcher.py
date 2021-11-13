import linecache
import ast
import csv
import difflib
from py import io
import re
import os
import shutil
import sys
import time
import pytest
import pandas as pd
from ifixflakies.main import main
from unparse import Unparser
from io import StringIO
import hashlib, binascii
from ifixflakies.utils.py import *
from ifixflakies.detector import verify
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

def sequence(pytest_method, polluter,cleaner_list,victim):
    whether_fixed = False
    for each in cleaner_list:
        if fix_victim(pytest_method,polluter,each,victim):
            whether_fixed = True
            break
    #verify if other polluter can be fixed
    
def get_cleaner_import_list(tree_cleaner,tree_victim):
    cleaner_import_list=[]
    
    for import_obj in [cle_obj for cle_obj in ast.walk(tree_cleaner) if isinstance(cle_obj, ast.Import) or isinstance(cle_obj, ast.ImportFrom)]:
        if ast.dump(import_obj) not in [ast.dump(vic_obj) for vic_obj in ast.walk(tree_victim) if isinstance(vic_obj, ast.Import) or isinstance(vic_obj, ast.ImportFrom)]:
            cleaner_import_list.append(import_obj)
    
    return cleaner_import_list


def get_cleaner_helper_node(tree_cleaner,cleaner_test): #cleaner_test["class"],cleaner_tree,cleaner_test

    # get helper code from cleaner, handle setup, body and teardown 'module, method, class, function'
    # setup_module,setup_class,setup_function,setup_method,test_body,teardown_method,teardown_function,teardown_class,teardown_module
    
    name_node_dict = {'setup_module': None, 'setup_class': None, 'setup_function': None, 'setup_method': None,
                          cleaner_test["function"]: None,
                          'teardown_method': None, 'teardown_function': None, 'teardown_class': None, 'teardown_module': None}
    
    
    if cleaner_test["class"]:
        for clean_class in [node for node in ast.walk(tree_cleaner) if isinstance(node, ast.ClassDef)]:
            if clean_class.name == cleaner_test["class"]:
                for clean_obj in [func for func in ast.iter_child_nodes(clean_class) if isinstance(func, ast.FunctionDef)]:                     
                    if clean_obj.name in name_node_dict:
                        name_node_dict[clean_obj.name] = clean_obj.body
                break


        insert_nodes_keys = [key for key in name_node_dict if name_node_dict[key] != None]
        pre_node_key = insert_nodes_keys[0]
        pre_node = name_node_dict[pre_node_key]

        if len(insert_nodes_keys) > 1:
            for key in insert_nodes_keys[1:]:
                name_node_dict[key].insert(0, pre_node)
                pre_node = name_node_dict[key]
        insert_node = pre_node

    else:
        for eachfunc in [func for func in ast.walk(tree_cleaner) if isinstance(func, ast.FunctionDef)]:
            if eachfunc.name in name_node_dict:
                name_node_dict[eachfunc.name] = eachfunc.body

        insert_nodes_keys = [key for key in name_node_dict if name_node_dict[key] != None]

        pre_node_key = insert_nodes_keys[0]
        pre_node = name_node_dict[pre_node_key]

        if len(insert_nodes_keys) > 1:
            for key in insert_nodes_keys[1:]:
                pre_node = name_node_dict[key].insert(0, pre_node)
        insert_node = pre_node

    return insert_node


def get_victim_test_node(tree_victim,victim_test):

    if victim_test["class"]:
        for vic_class in [node for node in ast.walk(tree_victim) if isinstance(node,ast.ClassDef)]:
            if vic_class.name == victim_test["class"]:
                for victim_obj in [func for func in ast.iter_child_nodes(vic_class) if isinstance(func,ast.FunctionDef)]:
                    #print(victim_obj)             
                    if victim_obj.name == victim_test["function"]:
                        victim_node = victim_obj
                        break

    else:
        for victim_obj in [func for func in ast.walk(tree_victim) if isinstance(func, ast.FunctionDef)]:
            if victim_obj.name == victim_test["function"]:
                victim_node = victim_obj
                break
    
    return victim_node



def fix_victim(pytest_method, polluter, cleaner, victim):#, fixed):

    task = "patcher"

    victim_test = split_test(victim, rmpara=True)
    cleaner_test = split_test(cleaner, rmpara=True)

    with open(victim_test["module"]) as f_victim:
        victim_tree = ast.parse(victim.read())

    with open(cleaner_test["module"]) as f_cleaner:
        cleaner_tree = ast.parse(cleaner.read())
        cleaner_info = get_origin_astInfo(cleaner_tree)
        cleaner_import_num = cleaner_info.get_import_num()

    index = victim.index('.')
    fixed_file = victim["module"].insert(index,'patch')

    diff=None
    minimal_patch_file=None
    patch_time_1st = None
    patch_time_all = None
    can_copy_work = None
    import_obj_list=[]
    cache_in_tests=[]
    patch_list=[]
    final_patch_content=''

    
    if verify(pytest_method, [polluter, cleaner, victim], "cleaner") and verify(pytest_method, [polluter, victim], "polluter"):
        
        can_copy_work = False

        # get import module from cleaner test
        cleaner_import_objs = get_cleaner_import_list(cleaner_tree,victim_tree)
        for each_obj in cleaner_import_objs:
            victim_tree.body.insert(0,each_obj)

        # get helper code from cleaner test body
        helper_node_body = get_cleaner_helper_node(cleaner_tree,cleaner_test).body

        # get victim body
        victim_node_body = get_victim_test_node(victim_tree,victim_test).body

        origin_victim_offset=0
        for each in victim_node_body:
            origin_victim_offset+=each.col_offset

        victim_start_lineno = victim_node_body[0].lineno

        #backup_victim_tree = victim_tree
        #backup_cleaner_tree = cleaner_tree
        #backup_helper_node_body = helper_node_body
        #backup_victim_node_body = victim_node_body

        victim_node_body.insert(0, helper_node_body)
        ast.fix_missing_locations(victim_tree)

        # test if can be unparsed correctly
        try:
            buf = StringIO()
            Unparser(victim_tree, buf)
            buf.seek(0)
            edited_content = buf.read()
        except IndentationError:
            can_copy_work=False

        with open(fixed_file, "w") as combination:
            combination.write(edited_content)

        tmp_fixed_victim=fixed_file + '::' + '::'.join(victim_test[1:])
        result =  verify(pytest_method, [polluter, tmp_fixed_victim], "polluter")
        victim_tree.remove(helper_node_body)

        if result:
            can_copy_work = True

        # minimize code by delta debugging
        n = 2
        start_time = time.perf_counter()
        patch_num = 0
        patch_time_1st = None
        patch_time_all = None
        roundnum=0
        minimal_patch_file= None
        insert_node_list = helper_node_body
        while len(insert_node_list) >= 2:
            start = 0
            subset_length = len(insert_node_list) // n
            pollution_is_cleaned = False
            while start < len(insert_node_list):

                this_round_insert_node = insert_node_list[:start] + insert_node_list[start+subset_length:]
                tmp_victim_tree = victim_tree
                tmp_victim_node_body = victim_node_body

                try:
                    tmp_victim_tree.insert(0, this_round_insert_node)
                    ast.fix_missing_locations(tmp_victim_tree)
                    can_be_inserted=True

                except:# IndentationError:
                    can_be_inserted=False

                tmp_buf = StringIO()
                Unparser(this_round_insert_node, tmp_buf)
                tmp_buf.seek(0)
                tmp_content = tmp_buf.read()

                buf = StringIO()
                Unparser(tmp_victim_tree, buf)
                buf.seek(0)
                edited_content = buf.read()

                combination_path = combination_path.replace('patch', 'patch'+str(roundnum))
                roundnum+=1
                with open(combination_path, "w") as combination:
                    combination.write(edited_content)

                if can_be_inserted:
                    tmp_victim_tree.remove(this_round_insert_node)
                
                if victim_test["class"]:
                    tmp_fixed_victim=combination_path + '::'+victim_test["class"]+'::'+victim_test["test"]
                else:
                    tmp_fixed_victim=combination_path +'::'+victim_test["test"]

                can_patch_work =  verify(pytest_method, [polluter, tmp_fixed_victim], "polluter")
                cache_in_tests.append(combination_path)

                if can_patch_work:
                    patch_time = time.perf_counter()
                    patch_num += 1
                    if patch_num == 1:
                        patch_time_1st = patch_time - start_time
                    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~CAN BE A PATCH~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n',
                          tmp_content)
                    minimal_patch_file=combination_path
                    patch_list.append(tmp_content)
                    final_patch_content=tmp_content
                    insert_node_list = this_round_insert_node
                    n = max(n - 1, 2)
                    pollution_is_cleaned = True
#                    print(edited_content)
                    break
                start = start + subset_length
            if not pollution_is_cleaned:
                n = min(n * 2, len(insert_node_list))
                if n == len(insert_node_list):
                    break
        end_time = time.perf_counter()
        if patch_time_1st:
            patch_time_all = end_time - start_time
            offset = 0
            for each in this_round_insert_node.body:
                offset+=each.col_offset  

        # already got minimize patch
        if minimal_patch_file:

            insert_patch_to = victim_start_lineno-1
            processed_patch_file = minimal_patch_file.replace('patch','processedpatch')
            with open(victim_test["module"], "r") as f:
                org_contents = f.readlines()

            with open(minimal_patch_file, "r") as patch:
                tree_patch = ast.parse(patch.read())
            patched_victim_node=get_victim_test_node(tree_patch,victim_test)

            final_patch=[]


            tmp_content=final_patch_content
            patch_offset=0
            for each in tmp_content.split('\n'):
                if each !='':
                    patch_offset+=1
                    print(patch_offset,each)
        
            print(final_patch_content)
            for num in range(1,patch_offset+1):#len(tmp_insert_node.body)+1):#patched_victim_offset+len(patched_victim_node.body)-origin_victim_offset-victim_length):
                result =linecache.getline(minimal_patch_file,patched_victim_node.lineno+num)
                final_patch.append(result)


            org_contents.insert(insert_patch_to,''.join(final_patch))
            buf =  StringIO()
            if len(import_obj_list):
                for each in import_obj_list:
                    Unparser(each,buf)
                    buf.seek(0)
                    org_contents.insert(0,buf.read())

            contents = "".join(org_contents)
            with open(processed_patch_file, "w") as fnew:
                fnew.write(contents)

            diff=os.popen('diff '+victim_test["module"]+' '+processed_patch_file).read()
            print(diff)
        
      
    for each in cache_in_tests:
        if each != minimal_patch_file:
            os.remove(each)

    if diff:
        return 0


def main():
    pytest_method= 'pytest_cmd'
    polluter = 'cynergy/tests/test_register_multiple.py::test_multiple_list_arguments'
    cleaner = 'cynergy/tests/test_class_mapping.py::test_class_mapping_from_init'
    victim = 'cynergy/tests/test_register_multiple.py::test_register_multiple'

    fix_victim(pytest_method,polluter,cleaner,victim)
