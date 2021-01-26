import sys
import os
import ast
import astor
import re
from anytree import Node, RenderTree, PreOrderIter, AsciiStyle
import time
from datetime import datetime, date
from utils.utils import remove_list_dup, list2treelist, slice_url, print_node_list, print_writeofd, search_tree, get_url_content, slice_list, render_beautify_tree_1
from utils.github_search import search_github
from utils.import_checker import import_check

# This is a file that checks if there is wait after the async call, and then
# search the entire repo for occurences of multi-thread, multi-process related APIs

# First input is a list of files in this format: [Repo Name]\t[URL]
# Second input is output file to write to
infd = open(sys.argv[1], 'r')
ofd = open(sys.argv[2], 'w')

PWD = os.getcwd()

ASYNC_START = "long_running_recognize"
ASYNC_GET   = "result"

# List of parallelism-related APIs
KEYWORD = ["threading", "multiprocessing", "concurrent", "asyncio", "_thread"]
# Local cache file for converting python2 to python3
CACHE_FILE_NAME = "google_stt_url_cache.py"
# Function names to be neglected if traced to
NEGLECT_FUNCTION_NAME = ["main", "__init__"]
# Parameter for class TraceAllFuncNames
MAXIMUM_SEARCH_ROUND = 5
# Sleep time between Github searches
SLEEP_TIME = 2
# Global variable to be modified by procedures
functionnames = []

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


def search_one_repo(url_list, out_fd):
    return_value = False
    for item in url_list:
        urlcontent = get_url_content(item, out_fd)
        if urlcontent == None:
            continue
        v = ast_processs_one_file(urlcontent, out_fd, item)
        if v == None:
            continue
        # If found one occurence of the anti-pattern, set return value to True, meaning that there is at least
        # one occurence where we see a seemingly async use of API
        if v:
            return_value = True
    return return_value

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


def ast_processs_one_file(content, outfile, url):
    p = add_backward_links(content)
    if p == None:
        return None
    v = AnalysisNodeVisitor()
    v.ofd = outfile
    v.url = url
    v.entire_tree = p

    ret = v.main_fct()

    global functionnames
    functionnames.extend(v.fct)

    return ret


# transcribe.start_transcription_job                                                    -> Line 1
# while True:
#   status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
#   if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
#       break
#   print("Not ready yet...")
#   time.sleep(60)                                                                      -> Block 1

class AnalysisNodeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.ofd = None
        self.url = None
        self.entire_tree = None

        # Stage one: check for the start clause and the long_running clause
        self.call_lineno = []
        self.l1 = False
        self.l1v = []
        self.l2 = False
        self.get_lineno = []
        
        self.fct = []
        self.identifed = False

        # Stage two: check for things between start clause and while clause 
        self.safe_fct_list = ["print", "sleep"]
        self.not_safe_list = []

    def identify_pattern(self, node):
        print_writeofd("Pattern identified", self.ofd)
        self.identifed = True

        # Now check to see if this API pattern is defined in a function
        while isinstance(node.parent, ast.Module) == False:
            if isinstance(node.parent, ast.FunctionDef):
                print_writeofd("Note: The API call is defined in function: {}".format(node.parent.name), self.ofd)
                self.fct.append((node.parent.name, self.url, []))
                break
            node = node.parent

    def check_instance_name(self, node):
        if not isinstance(node, ast.Name):
            print_writeofd("Node supposed to be name but not name: {}".format(ast.dump(node)), self.ofd)
            return False
        return True

    def visit_Attribute(self, node):
        if self.l1 and node.attr == ASYNC_START:
            if isinstance(node.parent, ast.Call) and isinstance(node.parent.parent, ast.Assign):
                for name in node.parent.parent.targets:
                    if self.check_instance_name(name):
                            self.l1v.append(name.id)
                            self.call_lineno.append(node.lineno)
            elif isinstance(node.parent, ast.Call) and isinstance(node.parent.parent, ast.Attribute):
                if node.parent.parent.attr == ASYNC_GET:
                    self.call_lineno.append(node.lineno)
                    self.get_lineno.append(node.lineno)
                    self.identify_pattern(node.parent.parent)
        elif self.l2:
            if isinstance(node.value, ast.Name) and node.value.id in self.l1v:
                if node.attr == ASYNC_GET:
                    self.get_lineno.append(node.lineno)
                    self.identify_pattern(node)
        self.generic_visit(node)

    def visit_Call(self, node):
        if self.l1 and isinstance(node.func, ast.Name) and node.func.id == ASYNC_START:
            self.call_lineno.append(node.lineno)
        self.generic_visit(node)

    # Helpful function for stage2, check if the given node is actually a childern of certain parent nodes
    def check_parent_node(self, node):
        while isinstance(node.parent, ast.Module) == False:
            node = node.parent
            if self.check_node_safe(node):
                return True
            if issubclass(node.__class__, ast.stmt) or issubclass(node.__class__, ast.expr):                    
                if node.lineno in self.call_lineno:
                    return True
            if node in self.not_safe_list:
                return True
        return False

    def check_node_safe(self, node):
        # If it is in the safe_fct_list, neglect
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in self.safe_fct_list:
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in self.safe_fct_list:
            return True
        # If it is an assignment clause with constant values
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            return True
        # If it is in an Expr class
        elif isinstance(node, ast.Expr) and self.check_node_safe(node.value):
            return True
        return False

    # For stage 2
    def stage2(self, call_lineno, get_lineno):
        for node in ast.walk(self.entire_tree):
            if issubclass(node.__class__, ast.stmt) or issubclass(node.__class__, ast.expr):
                if node.lineno < get_lineno and node.lineno > call_lineno:
                    if self.check_node_safe(node):
                        continue
                    # Append to non-safe node list
                    else:
                        self.not_safe_list.append(node)
        # Now check to see if any of the traced node is childern of nodes in the safe list
        remove_list = []
        for node in self.not_safe_list:
            if self.check_parent_node(node):
                remove_list.append(node)
        for node in remove_list:
            self.not_safe_list.remove(node)
    
    def main_fct(self):
        self.l1 = True
        self.generic_visit(self.entire_tree)
        self.l1 = False
        self.l2 = True
        self.generic_visit(self.entire_tree)
        if self.call_lineno == [] and self.get_lineno != []:
            print_writeofd("Start operation missing", self.ofd)
            return False
        if self.get_lineno == [] and self.call_lineno != []:
            print_writeofd("While loop operating missing", self.ofd)
            return False
        if self.get_lineno == [] and self.call_lineno == []:
            print_writeofd("Both start and loop operations missing", self.ofd)
            return False
        if len(self.get_lineno) != len(self.call_lineno):
            print_writeofd("Start and loop instance numbers do not match up", self.ofd)
            return False
        self.get_lineno.sort()
        self.call_lineno.sort()
        for call_lineno, get_lineno in zip(self.call_lineno, self.get_lineno):
            self.stage2(call_lineno, get_lineno)
        if self.not_safe_list != []:
            print_writeofd("------", self.ofd)
            print_writeofd("Nodes in between start statement and while statement", self.ofd)
            for node in self.not_safe_list:
                print_writeofd(astor.to_source(node), self.ofd)
            print_writeofd("------", self.ofd)
        return True
        

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
                
                
def remove_tuple_list_dup(l):
    i = 0
    to_delet_list = []
    while i < len(l):
        j = i + 1
        while j < len(l):
            if l[i] == l[j]:
                to_delet_list.append(l[j])
                break
            j += 1
        i += 1
    for i in to_delet_list:
        l.remove(i)
    return l
    
def tree2list(tree):
    return [node.name for node in PreOrderIter(tree)]

def treelist2list(treelist):
    rl = []
    for i in treelist:
        rl.extend(tree2list(i))
    return remove_tuple_list_dup(rl)

def beautify_tree(tree):
    copy = tree
    for elements in PreOrderIter(copy):
        new_name = (elements.name[0], slice_url(elements.name[1]))
        elements.name = new_name
    return copy 

def render_beautify_tree(tree, ofd):
    tree = beautify_tree(tree)
    for pre, _, node in RenderTree(tree, style = AsciiStyle()):
        print_writeofd("%s%s" % (pre, node.name), ofd)

# This function searchs a tuple list to see if a given element occurs in it
def search_tuple_list(tl, element):
    for i in tl:
        if i[0] == element:
            return True
    return False


if __name__ == "__main__":
    for line in infd.readlines():
        functionnames = []
        print("=================================================")
        ofd.write("=================================================\n")
        url = line.split()[1]
        repo = re.sub('https://github.com/', '', url)
        repo = re.sub('\n', '', repo)
        print(url)
        ofd.write("{}\n".format(url))
        
        url_list = search_github(ASYNC_START, repo, ofd)

        if url_list == None or url_list == []:
            print_writeofd("No use of async", ofd)
            continue

        v = search_one_repo(remove_list_dup(url_list), ofd)

        if v:
            if functionnames == []:
                print_writeofd("No use of parallelism - no function", ofd)
                continue
            # total_url_list contains the urls to the keywords searched regarding parallel APIs
            total_url_list = []
            for key in KEYWORD:
                url_list_2 = search_github(key, repo, ofd)
                time.sleep(SLEEP_TIME)
                for item in url_list_2:
                    print_writeofd("{} occurs in {}".format(key, item), ofd)
                total_url_list.extend(url_list_2)
        
            if len(total_url_list) > 0:
                total_url_list = remove_list_dup(total_url_list)
                v = TraceAllFuncNames()
                v.all_fct_name = remove_tuple_list_dup(functionnames)
                v.manual_control_import = True
                v.repo = repo
                v.ofd = ofd
                v.search_multi()
                all_fct_name = treelist2list(v.all_fct_name)
                print_writeofd("Now searching to see if parallel API takes place in the same file as function traced", ofd)
                for item in total_url_list:
                    for fct in all_fct_name:
                        if item in fct[2]:
                            print_writeofd("BOTH IDENTIFIED IN THE SAME FILE: [function: {}] [url: {}".format(fct, item), ofd)
                functionnames = []
            elif len(total_url_list) == 0:
                print_writeofd("No use of parallelism", ofd)
        else:
            print_writeofd("NO PATTERN IDENTIFIED", ofd)
    ofd.close()



        
