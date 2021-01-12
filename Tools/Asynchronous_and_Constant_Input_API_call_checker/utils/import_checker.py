# Written by Shicheng Liu
import ast
import sys
import os
import re

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


# Two strings as input where the first parts are the same when treated as dir
# Return the different endings
def string2difference(string1, string2):
    dir1 = string1.split('/')
    dir2 = string2.split('/')
    
    for index, _ in enumerate(dir1):
        if dir1[index] != dir2[index]:
            break
    
    ret1 = ""
    ret2 = ""
    
    for entry in dir1[index:]:
        ret1 += entry + "/"
    ret1 = ret1.rstrip("/")
    for entry in dir2[index:]:
        ret2 += entry + "/"
    ret2 = ret2.rstrip("/")

    return (ret1, ret2)


# current_file_url: currently inspecting file url
# compare_file_url: url of file to be compared of
# current_fcn_name: currently inspecting function name
# import_dir: The [*] fields in the following statements: IMPORT [*] | FROM [*] IMPORT 
# import_function: function names that appears in the FROM IMPORT statement, NONE if using a IMPORT clause, a list of AST alias objects
def import_check(current_file_url, compare_file_url, current_fcn_name, import_dir, import_function):
    # Note to users: 
    # because users can be importing a Class into the current function
    # checking the [*] clause in "from [] import [*]" can be very difficult
    # This program opts to not checking the [*] clause and in turn only checks the imported module
    # This feature is controlled by the following constant
    ONLY_CHECK_IMPORT = True
    
    # First generate a list of legal import statements
    legal_import_dir = []
    
    compare_file_dir = slice_url(compare_file_url).strip(".py")
    dot_compare_file_dir = compare_file_dir.replace("/", ".")
    # Absolute import
    legal_import_dir.append(dot_compare_file_dir)

    current_file_dir = slice_url(current_file_url).strip(".py")
    compare_diff_dir, current_diff_dir = string2difference(compare_file_dir, current_file_dir)
    compare_diff_dot = compare_diff_dir.replace("/", ".")
    
    # Different forms of relative import
    if ("/" not in compare_diff_dir) and ("/" not in current_diff_dir):
        # They are in the same directory
        legal_import_dir.append(compare_diff_dir)
        legal_import_dir.append("." + compare_diff_dir)
    elif ("/" not in current_diff_dir):
        # The imported file is in a folder
        legal_import_dir.append(compare_diff_dot)
        legal_import_dir.append("." + compare_diff_dot)
    else:
        # Contains in different paths
        # Dots that need to be placed in front
        go_back_level = len(current_diff_dir.split("/"))
        legal_import_dir.append("." * go_back_level + compare_diff_dot)
    
    # print(legal_import_dir)
    if (import_dir in legal_import_dir):
        if ONLY_CHECK_IMPORT:
            return True
        else:
            if (import_function != None):
                for alias in import_function:
                    if isinstance(alias, ast.alias) and alias.name == current_fcn_name:
                        return True
            elif (import_function == None):
                return True
    return False

def test_case(current_file_url, compare_file_url, current_fcn_name, import_dir, import_function):
    if import_check(current_file_url, compare_file_url, current_fcn_name, import_dir, import_function):
        print("True")
    else:
        print("False")

if __name__ == "__main__":
    string1 = "https://raw.githubusercontent.com/Jaecenn/audiobook-creator/2e1cdeb52d4dc6f8051eed16f2424968588300a7/alternativeSnipping.py"
    string2 = "https://raw.githubusercontent.com/Jaecenn/audiobook-creator/2e1cdeb52d4dc6f8051eed16f2424968588300a7/abcde.py"
    test_case(string1, string2, None, "abcde", None)

    string1 = "https://raw.githubusercontent.com/Jaecenn/audiobook-creator/2e1cdeb52d4dc6f8051eed16f2424968588300a7/class1/module1.py"
    string2 = "https://raw.githubusercontent.com/Jaecenn/audiobook-creator/2e1cdeb52d4dc6f8051eed16f2424968588300a7/class2/module2.py"
    test_case(string1, string2, "fct", "class2.module2", "fct")

    string1 = "https://raw.githubusercontent.com/Jaecenn/audiobook-creator/2e1cdeb52d4dc6f8051eed16f2424968588300a7/class1/module1.py"
    string2 = "https://raw.githubusercontent.com/Jaecenn/audiobook-creator/2e1cdeb52d4dc6f8051eed16f2424968588300a7/class1/sub_class/module2.py"
    test_case(string1, string2, "fct", "sub_class.module2", "fct")