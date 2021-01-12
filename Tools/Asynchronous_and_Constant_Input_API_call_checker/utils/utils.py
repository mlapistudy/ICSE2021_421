import sys
import os
import copy
import ast
import re
from anytree import Node, RenderTree, PreOrderIter, AsciiStyle
import urllib.request

def remove_list_dup(l):
    rl = list(set(l))
    return rl
    
def list2treelist(l):
    i = 0
    while i < len(l):
        l[i] = Node(l[i])
        i += 1
    return l

# Chunks url to delete the first couple of fields
def slice_url(url):
    # print(url)
    url = re.sub("https://raw.githubusercontent.com/", "", url)
    url = url.split('/')[3:]
    string = ""
    i = 0
    while i < len(url) - 1:
        string += url[i] + "/"
        i += 1
    string += url[i]
    return string

def slice_list(l):
    rl = []
    for i in l:
        rl.append(slice_url(i))
    return rl

def print_node_list(l):
    string = ""
    for elements in l:
        string += elements.name[0]
        string += ", "
    return string 

def beautify_tree_1(tree):
    cp = copy.deepcopy(tree)
    for elements in PreOrderIter(cp):
        new_name = (elements.name[0], slice_url(elements.name[1]), slice_list(elements.name[2]))
        elements.name = new_name
    return cp

def render_beautify_tree_1(tree, ofd):
    tree = beautify_tree_1(tree)
    for pre, _, node in RenderTree(tree, style = AsciiStyle()):
        print_writeofd("%s%s" % (pre, node.name), ofd)


def beautify_tree(tree):
    cp = copy.deepcopy(tree)
    for elements in PreOrderIter(cp):
        new_name = (ast.dump(elements.name), elements.name.lineno)
        elements.name = new_name
    return cp 

def render_beautify_tree(tree, ofd):
    tree = beautify_tree(tree)
    for pre, _, node in RenderTree(tree, style = AsciiStyle()):
        print_writeofd("%s%s" % (pre, node.name), ofd)

# Searchs a tuple list to see if a given element occurs in it
def search_tuple_list(tl, element):
    for i in tl:
        if i == element:
            return True
    return False

# Searches if value appears in trees
def search_tree(trees, value):
    for tree in trees:
        for element in PreOrderIter(tree):
            if element.name[0] == value[0] and element.name[1] == value[1]:
                return True
    return False

# Print to stdout and write to output file 
def print_writeofd(string, ofd):
    print(string)
    ofd.write(string + "\n")

#  Prints all strings on one line
def print_on_one_line(ls):
    string = ""
    for element in ls:
        string += element.name.value
        string += "||"
    return string

# This file takes a url as input, and outputs a string containing information on that url
def get_url_content(url, ofd):
    print_writeofd("Inspecting: {}".format(url), ofd)
    try:
        urlfd = urllib.request.urlopen(url)
        urlcontent = urlfd.read()
        return urlcontent
    except urllib.error.URLError as e:
        print_writeofd("NETWORK EXCEPTION: {}".format(e), ofd)
        return None