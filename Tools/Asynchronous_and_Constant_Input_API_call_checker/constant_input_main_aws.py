import sys
import os
import ast
import re
from anytree import Node, PreOrderIter
import time
from datetime import datetime, date
from utils.import_checker import import_check
from utils.github_search import search_github
from utils.utils import *

# NOTE TO MYSELF:
# Difference between this file and constant_input_main_aws.py is that:
# There are two keywords to seach in constant_input_main_aws.py and only one in this file

# NOTE to users:
# ast.generic_visit only visits the immediate childern of a node: to visit all sub-childern of that node,
# the childern of that node need to call generic_visit themselves

# TTS API name -- In Google TTS, this is "synthesize_speech"
KEYWORD1 = ["synthesize_speech", "start_speech_synthesis_task"]
# Keyword name if input is passed-in by keyword -- In AWS TTS, this is "Text"
KEYWORD2 = "Text"
# Parameter for class RetraceFixedInput
MAXIMUM_INPUT_SEARCH_ROUND = 5
# Parameter for class TraceAllFuncNames
MAXIMUM_SEARCH_ROUND = 5
# Function names to be neglected if traced to
NEGLECT_FUNCTION_NAME = ["main", "__init__"]
# Sleep time between Github searches
SLEEP_TIME = 2
# Local cache file for converting python2 to python3
CACHE_FILE_NAME = "tts_fixed_input.py"

PWD = os.getcwd()

# File Descriptor for input file
infd = open(sys.argv[1], "r")
# File Descriptor for output file
ofd  = open(sys.argv[2], "w")

# Tracing back fixed input in one file
class RetraceFixedInput(ast.NodeVisitor):
    def __init__(self):
        self.ofd = None
        self.entire_tree = None
        self.url = None
        self.intermediate_traced = []
        # Stores the function names where rootnode is defined in
        self.fctname = []
        
        # Stage 1: trace rootnode
        self.tracing_rootnode = False
        # Rootnode can only store Ast.Name or Ast.Constant
        self.rootnode = []
        # Other types are stored here
        self.other_rootnode = []

        # Stage 2: trace inputs
        self.traceinput = False
        self.current_tracing_node = None
        self.current_round = 0
        self.identified = False
        # If it is not searching for input, do not check the parent function again
        self.searching_for_input = False

        self.search_fcn_keyword = None

    def get_desired_arguments(self, ls):
        for element in ls:
            if element.arg == KEYWORD2:
                return element.value
        print_writeofd("Expected to have one arg field {}, but none in list {}".format(KEYWORD2, ls), self.ofd)

    def get_current_tracing_node(self):
        if isinstance(self.current_tracing_node, ast.Constant):
            return self.current_tracing_node.value
        elif isinstance(self.current_tracing_node, ast.Name):
            return self.current_tracing_node.id
        else:
            print_writeofd("Expected to have current tracing node to be either CONSTANT or NAME, but neither", self.ofd)

    # This function takes a node as input and outputs the first argument in its parent Call node
    # Used to extract the API call argument
    def get_arguments(self, node):
        node_copy = node
        while not isinstance(node, ast.Call):
            node = node.parent
            if isinstance(node, ast.Module):
                print_writeofd("Node not defined in Ast.Call class: {}".format(ast.dump(node_copy)), self.ofd)
                return None
        if node.args != []:
            return node.args[0]
        elif node.keywords != []:
            return self.get_desired_arguments(node.keywords)
        
    def visit_Call(self, node):
        if self.tracing_rootnode:
            if isinstance(node.func, ast.Name) and node.func.id == self.search_fcn_keyword:
                intermediate = self.get_arguments(node)
                if isinstance(intermediate, ast.Name) or isinstance(intermediate, ast.Constant):
                    self.rootnode.append(Node(intermediate))
                else:
                    self.other_rootnode.append(Node(intermediate))
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if self.tracing_rootnode:
            if node.attr == self.search_fcn_keyword:
                intermediate = self.get_arguments(node)
                if isinstance(intermediate, ast.Name) or isinstance(intermediate, ast.Constant):
                    self.rootnode.append(Node(intermediate))
                else:
                    self.other_rootnode.append(Node(intermediate))
        self.generic_visit(node)

    def visit_Assign(self, node):
        if self.traceinput:
            for target_node in node.targets:
                if isinstance(target_node, ast.Name) and (target_node.id == self.get_current_tracing_node()):
                    self.check_append(node)
                elif isinstance(target_node, ast.Tuple):
                    for tuple_node in target_node.elts:
                        if isinstance(tuple_node, ast.Name) and (tuple_node.id == self.get_current_tracing_node()):
                            self.check_append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if self.traceinput:
            for arg_nodes in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                if arg_nodes.arg == self.get_current_tracing_node():
                    self.check_append(node)
        self.generic_visit(node)

    # Checks if the node appears prior than the current tracing node
    def check_append(self, node):
        if self.check_order(node, self.current_tracing_node):
            self.intermediate_traced.append(node)

    # Determine if node1 appears prior to node2
    def check_order(self, node1, node2):
        if node1.lineno < node2.lineno:
            return True
        elif node1.lineno == node2.lineno and node1.col_offset < node2.col_offset:
            return True
        return False

    def insertion_sort(self, nums):
        # Start on the second element as we assume the first element is sorted
        for i in range(1, len(nums)):
            item_to_insert = nums[i]
            # And keep a reference of the index of the previous element
            j = i - 1
            # Move all items of the sorted segment forward if they are smaller than
            # the item to insert
            while j >= 0 and self.check_order(nums[j], item_to_insert):
                nums[j + 1] = nums[j]
                j -= 1
            # Insert the item
            nums[j + 1] = item_to_insert
        return nums

    def get_last_assignment(self, ls):
        if ls == []:
            return []
        return self.insertion_sort(ls)[0]

    def get_variable(self, node):
        if node == []:
            return []
        all_variable = []
        # If it is wrappered in a Call node, recursively output the arguments to the Call node
        if isinstance(node, ast.Call):
            for element in node.args:
                all_variable.extend(self.get_variable(element))
            for element in node.keywords:
                all_variable.extend(self.get_variable(element.value))
        # If it is not, simply append all Name nodes
        else:
            for element in ast.walk(node):
                if isinstance(element, ast.Name) or isinstance(element, ast.Constant):
                    all_variable.append(element)
        return all_variable
            
    # This function traces the last line where the given node appears in the target of an assignment clause
    def trace_one_node(self, node):
        self.intermediate_traced = []
        self.current_tracing_node = node.name
        self.generic_visit(self.entire_tree)
        last_node = self.get_last_assignment(self.intermediate_traced)

        # If the last item traced is a functionDef, then return immediately
        if isinstance(last_node, ast.FunctionDef) or last_node == []:
            return False

        last_node_variables = self.get_variable(last_node.value)
        for variable in last_node_variables:
            Node(variable, parent = node)
    
    def check_all_Constants(self, nodelist):
        for node in nodelist:
            if not isinstance(node.name, ast.Constant):
                return False
            else:
                if not isinstance(node.name.value, str):
                    return False
        # At this point, all node.name.value should be str constants
        # Now, delete some common mis-traced constant inputs
        common_mistrace = ["utf-8", "text"]
        all_mistrace = True
        for node in nodelist:
            if (not node.name.value.isspace()) and (not (node.name.value in common_mistrace)):
                all_mistrace = False
        if all_mistrace:
            return False
        return True

    def trace_once(self, tree):
        end = [tree]
        search_round = 0 
        while search_round < self.current_round:
            intermediate = []
            for elements in end:
                # If one of the node does not have a childern and yet it is not a Constant node, return False
                if elements.children == ():
                    if not isinstance(elements.name, ast.Constant):
                        return False
                for children in elements.children:
                    intermediate.append(children)
            end = intermediate
            search_round += 1
        
        render_beautify_tree(tree, self.ofd)
        
        if end == []:
            print_writeofd("No constant tree traced", self.ofd)
            return False
        if self.check_all_Constants(end):
            print_writeofd("Traced fixed input tree", self.ofd)
            print_writeofd("***", self.ofd)
            render_beautify_tree(tree, self.ofd)
            print_writeofd("***", self.ofd)
            print_writeofd("Entirely Constant: {}".format(print_on_one_line(end)), self.ofd)
            return True
        for node in end:
            self.trace_one_node(node)

    def trace_multi(self):
        self.tracing_rootnode = True
        self.generic_visit(self.entire_tree)
        self.tracing_rootnode = False
        self.traceinput = True
        for tree in self.rootnode:
            self.current_round = 0
            self.identified = False
            marker = False
            while self.current_round < MAXIMUM_INPUT_SEARCH_ROUND:
                print("Searching round {}".format(self.current_round))
                v = self.trace_once(tree)
                if v == False:
                    marker = False
                    break
                elif v == True:
                    marker = True
                    break
                self.current_round += 1
            if marker == False:
                continue
            elif marker == True:
                self.identified = True

        if self.identified == False and self.searching_for_input:
            # This means none of the searches have returned positive results. Now search for where the rootnode is defined in functions
            for node in self.rootnode + self.other_rootnode:
                node = node.name
                while node != None and isinstance(node.parent, ast.Module) == False :
                    if isinstance(node.parent, ast.FunctionDef):
                        print_writeofd("The keyword [{}] is defined in function [{}]".format(self.search_fcn_keyword, node.parent.name), self.ofd)
                        self.fctname.append((node.parent.name, self.url, []))
                        break
                    node = node.parent

# Trace back function calls in the repository
class TraceAllFuncNames(ast.NodeVisitor):
    # A 3-tuple
    # First element is the function's name
    # Second element is where the function is defined in
    # Third element is where the function is called in
    
    def __init__(self):
        # Stores all function names traced
        # The data in all_fct_name is a list of tree roots, where subsequent nodes will be appended to
        self.all_fct_name = []
        # Intermediate variable
        self.fctname_thisround = []

        self.fct_inspect = None
        self.fct_inspect_url = None
        self.url_inspect = None
        self.repo = None
        self.ofd = None

        # Controls whether or not one wants to turn the check for import option on
        self.manual_control_import = False
        # Stage of checking for import
        self.checking_import = False
        # Whether we found import to be true or not
        self.import_true = False

        self._round = 0

    def search_multi(self):
        self.all_fct_name = list2treelist(self.all_fct_name)
        start = datetime.now().time()
        end = datetime.now().time()
        time_elapsed = (datetime.combine(date.min, end) - datetime.combine(date.min, start)).total_seconds() 
        # If a particular project takes more than 20 minutes, flag it and move on
        while self._round < MAXIMUM_SEARCH_ROUND:
            end = datetime.now().time()
            time_elapsed = (datetime.combine(date.min, end) - datetime.combine(date.min, start)).total_seconds() 
            self.retrieve_and_search()
            self._round += 1
            if time_elapsed > 20 * 60:
                print_writeofd("This project took more than 20 minutes, jumping over for now", self.ofd)
                break
        # Print tree searched:
        print_writeofd("***", self.ofd)
        print_counter = 1
        for elements in self.all_fct_name:
            print_writeofd("Tree Number {}".format(print_counter), self.ofd)
            render_beautify_tree_1(elements, self.ofd)
            print_counter += 1
        print_writeofd("***", self.ofd)

    def retrieve_and_search(self):
        search_round = 0
        end = self.all_fct_name
        while search_round < self._round:
            intmediate = []
            for elements in end:
                for children in elements.children:
                    intmediate.append(children)
            search_round += 1
            end = intmediate
        print_writeofd("Round {}, beginning tracing functions: ".format(self._round) + print_node_list(end), self.ofd)
        for elements in end:
            self.fctname_thisround = []
            self.fct_inspect = elements.name[0]
            self.fct_inspect_url = elements.name[1]
            url_list = search_github(self.fct_inspect, self.repo, self.ofd)
            time.sleep(SLEEP_TIME)
            appear_url_list = url_list
            to_delete_list = []
            for item in url_list:
                urlcontent = get_url_content(item, self.ofd)
                if urlcontent == None:
                    continue
                p = add_backward_links(urlcontent)
                if p == None:
                    continue    
                self.url_inspect = item
                if (item == self.fct_inspect_url) and self.manual_control_import:
                    print_writeofd("Info: importation file and to be imported function in the same file, importation check fulfilled", self.ofd)
                elif (item != self.fct_inspect_url) and self.manual_control_import:
                    # Now checks for import
                    self.checking_import = True
                    self.import_true = False
                    self.generic_visit(p)
                    self.checking_import = False                
                    if self.import_true == False:
                        print_writeofd("Info: Importation check failed: function [{}] at url [{}], importation occurs in [{}]".format(self.fct_inspect, slice_url(self.fct_inspect_url), slice_url(item)), self.ofd)
                        to_delete_list.append(item)
                        continue
                    else:
                        print_writeofd("Info: Importation check succeeded", self.ofd)
                self.generic_visit(p)
            for searched in self.fctname_thisround:
                node = Node((searched[0], searched[1], []), parent = elements)
            print_writeofd("Traced functions {} based on [{}]".format(self.fctname_thisround, self.fct_inspect), self.ofd)
            for i in to_delete_list:
                appear_url_list.remove(i)
            print_writeofd("This function [{}] appears in {}".format(self.fct_inspect, slice_list(appear_url_list)), self.ofd)
            for tree in self.all_fct_name:
                for members in PreOrderIter(tree):
                    if members.name == (elements.name[0], elements.name[1], []):
                        members.name = (elements.name[0], elements.name[1], appear_url_list)

    # Check if the node is in a function
    def check_recursion(self, node):
        while isinstance(node.parent, ast.Module) == False:
            if isinstance(node.parent, ast.FunctionDef):
                inspect_tuple =  (node.parent.name, self.url_inspect)
                if node.parent.name in NEGLECT_FUNCTION_NAME:
                    print_writeofd("The function call [{}] is defined in function [{}], NEGLECTED".format(self.fct_inspect, node.parent.name), self.ofd)
                    break
                # This case below is also ruled out because such tracing will make the graph very complicated and difficult to understand
                elif node.parent.name == self.fct_inspect:
                    print_writeofd("The function call [{}] is defined in function [{}], SAME ONE, NEGLECTED".format(self.fct_inspect, node.parent.name), self.ofd)
                # If function of the same name is already traced either in the current round or in the tree, also neglect
                elif search_tuple_list(self.fctname_thisround, inspect_tuple) or search_tree(self.all_fct_name, inspect_tuple):
                    print_writeofd("The function call [{}] is defined in function [{}], ALREADY SEARCHED, NEGLECTED".format(self.fct_inspect, node.parent.name), self.ofd)
                else:
                    print_writeofd("The function call [{}] is defined in function [{}]".format(self.fct_inspect, node.parent.name), self.ofd)
                    self.fctname_thisround.append((node.parent.name, self.url_inspect))
                    break
            node = node.parent

    def visit_Call(self, node):
        if self.checking_import == False and isinstance(node.func, ast.Name) and node.func.id == self.fct_inspect:
            self.check_recursion(node)
        else:
            self.generic_visit(node)

    def visit_Attribute(self, node):
        if self.checking_import == False and node.attr == self.fct_inspect:
            self.check_recursion(node)
        else:
            self.generic_visit(node)

    def visit_Import(self, node):
        if self.checking_import:
            for name in node.names:
                if isinstance(name, ast.alias) and import_check(self.url_inspect, self.fct_inspect_url, self.fct_inspect, name.name, None):
                    self.import_true = True
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if self.checking_import:
            if import_check(self.url_inspect, self.fct_inspect_url, self.fct_inspect, node.module, node.names):
                self.import_true = True
        self.generic_visit(node)
                

def add_backward_links(content):
    try:
        p = ast.parse(content)
    except SyntaxError:
        try:
            content = use_2to3(content)
            p = ast.parse(content)
        except Exception as e:
            print_writeofd("EXCEPTION OCCURS: {}".format(e), ofd)
            return None
    except Exception as e:
        print_writeofd("EXCEPTION OCCURS: {}".format(e), ofd)
        return None
    # Traverse the tree to add links from child to parent, making it a doubly-linked tree
    for node in ast.walk(p):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    return p

 
def use_2to3(content):
    fd = open(CACHE_FILE_NAME, "wb")
    fd.write(content)
    fd.close()
    os.system("2to3 -w {}".format(CACHE_FILE_NAME))
    fd = open(CACHE_FILE_NAME, "r", encoding = "latin-1")
    content = fd.read()
    fd.close()
    os.remove(os.path.join(PWD, CACHE_FILE_NAME))
    return content


if __name__ == "__main__":
    for line in infd.readlines():
        try:
            print_writeofd("=================================================", ofd)
            url = line.split()[1]
            repo = re.sub('https://github.com/', '', url)
            repo = re.sub('\n', '', repo)
            print_writeofd(url, ofd)
            
            url_list = []
            for keyword in KEYWORD1:
                int_url_list = search_github(keyword, repo, ofd)
                if int_url_list != None:
                    url_list.extend(int_url_list)
            if url_list == None or url_list == []:
                continue

            at_least_one_file = False
            w_all_fct_name = []
            for url in url_list:
                urlcontent = get_url_content(url, ofd)
                if urlcontent == None:
                    continue
                p = add_backward_links(urlcontent)
                if p == None:
                    continue
                for keyword in KEYWORD1:
                    v = RetraceFixedInput()
                    v.ofd = ofd
                    v.entire_tree = p
                    v.search_fcn_keyword = keyword
                    v.url = url
                    v.searching_for_input = True
                    v.trace_multi()

                    if v.identified:
                        at_least_one_file = True
                    else:
                        w_all_fct_name.extend(v.fctname)
            
            if at_least_one_file:
                continue

            # If to this step, it means that none of the url contain the fixed input pattern
            # We are searching for occurences of this function in the repo
            w = TraceAllFuncNames()
            w.all_fct_name = w_all_fct_name
            w.manual_control_import = True
            w.ofd = ofd
            w.repo = repo
            w.search_multi()

            for tree in w.all_fct_name:
                for elements in PreOrderIter(tree):
                    for url in elements.name[2]:
                        urlcontent = get_url_content(url, ofd)
                        p = add_backward_links(urlcontent)
                        if p == None:
                            continue
                        v = RetraceFixedInput()
                        v.ofd = ofd
                        v.entire_tree = p
                        v.search_fcn_keyword = elements.name[0]
                        v.trace_multi()
        except UnicodeEncodeError as e:
            print_writeofd("e", ofd)