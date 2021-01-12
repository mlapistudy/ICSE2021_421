import sys
import re
from utils.utils import print_writeofd

# First argument is the output file from async_main_aws.py
ifd = open(sys.argv[1], 'r')

# Second argument is the output file for a list of all repos
ofd = open(sys.argv[2], 'w')


# All files number
allfile = 0
# All occurences of found 0 files 
no_async = 0
# Determined cases of no parallelism
noparrelism = 0
# Determined cases of no pattern:
nopattern = 0
# Number of exception cases - repo no longer exist
github_exception = 0
# Number of exception cases - processing error
proces_exception = 0
# No retrieve result files
no_retrieve = 0
# Use Lambda function
use_lambda = 0 

# Possible parallelism
possible_para = 0
# Determined no parallelism
det_no_para = 0
# Determined parallelism
det_para = 0

# There exists code in between start clause and while clause
between_code = 0
# Determined to be no pattern
det_no_pattern = 0


def get_all_add_up():
    return no_async + noparrelism + nopattern + github_exception + proces_exception + no_retrieve + use_lambda + possible_para + det_no_pattern

def scan_block(lines, i, j, keyword):
    while i < j:
        if keyword in lines[i]:
            return True
        i += 1
    return False

def scan_block_numbers(lines, i, j, keyword):
    ret = 0
    while i < j:
        if keyword in lines[i]:
            ret += 1
        i += 1
    return ret

def print_code(i, j, lines):
    while i < j:
        if "Nodes in between start statement and while statement" in lines[i]:
            i_copy = i
            while "------" not in lines[i_copy]:
                print(lines[i_copy])
                i_copy += 1
            break
        i += 1

lines = ifd.readlines()
i = 0
while i < len(lines):
    begin = get_all_add_up()
    allfile += 1
    j = i + 1
    while j < len(lines) and lines[j] != "=================================================\n":
        j += 1
    if j > len(lines):
        break
    # Now i and j stores the start and end of one search snippet
    k = i + 1

    # Judge if there is any github exception triggered
    if scan_block(lines, i, j, "Other Github Exceptions occurred"):
        github_exception += 1
        ofd.write("github_exception: {}".format(lines[k]))
        i = j
        continue

    # Judge if there is any other exception triggered
    if scan_block(lines, i, j, "EXCEPTION OCCURS"):
        proces_exception += 1
        ofd.write("process_exception: {}".format(lines[k]))
        i = j
        continue

    # Judge if this is a use lambda function case
    # If only relying on auto-tool: this should be a parallelism-used case
    if "Use Lambda Function" in lines[j - 1]:
        use_lambda += 1
        ofd.write("use_lambda: {}".format(lines[k]))
        i = j
        continue

    # Judge if this is a no pattern identified case
    # If only relying on auto-tool: this should be a parallelism-used case
    if "NO PATTERN IDENTIFIED" in lines[j - 1]:
        nopattern += 1
        ofd.write("no_pattern: {}".format(lines[k]))
        i = j
        continue

    # Judge if this is a no use of async case
    # Such project should not be counted towards the total count of projects
    if "No use of async" in lines[j - 1]:
        no_async += 1
        ofd.write("no_async: {}".format(lines[k]))
        i = j
        continue

    # Judge if this is a no retrieve result case
    # Such project should not be counted towards the total count of projects
    if "No retrieve result" in lines[j - 1]:
        no_retrieve += 1
        ofd.write("no_retrieve: {}".format(lines[k]))
        i = j
        continue

    # Judge if this is a no use of parallelism case
    if "No use of parallelism" in lines[j - 1]:
        noparrelism += 1
        ofd.write("no_parallelism: {}".format(lines[k]))
        i = j
        continue

    # At this point there shouldn't be any "operating missing", sanity check:
    if scan_block(lines, i, j, "operation") and scan_block(lines, i, j, "missing") and (not scan_block(lines, i, j, "Pattern identified")):
        print("Operation missing while it's neither use lambda nor no pattern identified: {}".format(lines[k]))
        exit(1)

    # Check if needs to prompt users on codes between start and while statement:
    if scan_block(lines, i, j, "Nodes in between start statement and while statement"):
        # If these two numbers equal then need to prompt users:
        if scan_block_numbers(lines, i, j, "Nodes in between start statement and while statement") == scan_block_numbers(lines, i, j, "Pattern identified"):
            print("\n\n\n\n\n\n")
            print_code(i, j, lines)
            between_code += 1
            print("Please inspect the above. Enter 1 if this is a no pattern case, and enter 2 if we can proceed")
            user = input()
            while user != '1' and user != '2':
                print("PRESS 1 OR 2, NOT ANYTHING ELSE!")
                user = input()
            if user == '1':
                det_no_pattern += 1
                print_writeofd("code_between (no_pattern): {}".format(lines[k]), ofd)
                i = j
                continue
            elif user == '2':
                print_writeofd("code_between (proceeds): {}".format(lines[k]), ofd)


    while i < j:
        if "***" in lines[i]:
            i_copy = i
            while i_copy < j:
                if "BOTH IDENTIFIED IN THE SAME FILE" in lines[i_copy]:
                    print("\n\n\n\n\n\n")
                    print(lines[i])
                    i += 1
                    while i < j and "========================" not in lines[i]:
                        print(lines[i])
                        i += 1
                    if i != j:
                        print(lines[i])
                    print("Please inspect the above. Enter 1 if this is a no parallelism case, and enter 2 if this is a use-parallelism case")
                    user = input()
                    while user != '1' and user != '2':
                        print("PRESS 1 OR 2, NOT ANYTHING ELSE!")
                        user = input()
                    possible_para += 1
                    if user == '1':
                        det_no_para += 1
                        print_writeofd("possible_parallelism (no_parallelism): {}".format(lines[k]), ofd)
                    elif user == '2':
                        det_para += 1
                        print_writeofd("possible_parallelism (parallelism): {}".format(lines[k]), ofd)
                    break
                i_copy += 1
            if i_copy == j:
                ofd.write("no_parallelism: {}".format(lines[k]))
                noparrelism += 1
                break
        i += 1
            

            
            


    # while i < j:
    #     if "***" in lines[i]:
    #         i_copy = i
    #         while i < j:
    #             if "BOTH IDENTIFIED IN THE SAME FILE" in lines[i]:
    #                 ofd.write("parallel: {}".format(lines[k]))
    #                 parallel += 1
    #                 break
    #             i += 1
    #         if i != j:
    #             i = i_copy
    #             while i < j:
    #                 ofd2.write(lines[i])
    #                 i += 1
    #         elif i == j:
    #             ofd.write("no_parallelism: {}".format(lines[k]))
    #             noparrelism += 1
    #     if i >= len(lines):
    #         break     
    #     i += 1

    after = get_all_add_up()
    if begin == after or after != allfile:
        print("There is one not accounted for: {}".format(lines[k]))
        exit(1)
    i = j

ofd.write("\n\n==================================================================\n")
print_writeofd("{}, Total files searched".format(allfile), ofd)
print_writeofd("BEFORE MANUAL INSPECTION:", ofd)
print_writeofd("{}, No use of Async".format(no_async), ofd)
print_writeofd("{}, Github search exceptions".format(github_exception), ofd)
print_writeofd("{}, Processing exceptions".format(proces_exception), ofd)
print_writeofd("{}, Use of Lambda Function".format(use_lambda), ofd)
print_writeofd("{}, No retrieve result".format(no_retrieve), ofd)
print_writeofd("{}, No pattern identified".format(nopattern + det_no_pattern), ofd)
print_writeofd("{}, No use of parallelism".format(noparrelism), ofd)
print_writeofd("{}, Possible use of parallel cases".format(possible_para), ofd)
print_writeofd("{}, Codes in between (not counted towards the final count below)".format(between_code), ofd)
all_above = get_all_add_up()
print_writeofd("", ofd)
print_writeofd("{}, Adding all above together".format(all_above), ofd)
print_writeofd("", ofd)
print_writeofd("", ofd)
print_writeofd("After MANUAL INSPECTION:", ofd)
print_writeofd("{}, No use of Async".format(no_async), ofd)
print_writeofd("{}, Github search exceptions".format(github_exception), ofd)
print_writeofd("{}, Processing exceptions".format(proces_exception), ofd)
print_writeofd("{}, Use of Lambda Function".format(use_lambda), ofd)
print_writeofd("{}, No retrieve result".format(no_retrieve), ofd)
print_writeofd("{}, No pattern identified".format(nopattern + det_no_pattern), ofd)
print_writeofd("{}, No use of parallelism".format(noparrelism + det_no_para), ofd)
print_writeofd("{}, Use of parallel cases".format(det_para), ofd)

ofd.close()