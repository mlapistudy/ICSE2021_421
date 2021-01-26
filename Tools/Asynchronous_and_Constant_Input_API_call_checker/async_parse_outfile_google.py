import sys
import re
from utils.utils import print_writeofd

# First argument is whether or not to proceed with manual checking:
if sys.argv[1] == '-m':
    MANUAL_CHECKING = True
elif sys.argv[1] == '-a':
    MANUAL_CHECKING = False
else:
    print("The first argument must be either -m or -a, see README.md for details")
    exit(1)

# Second argument is the output file from async_main_google.py
ifd = open(sys.argv[2], 'r')

# Third argument is the output file for a list of all repos
ofd = open(sys.argv[3], 'w')

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
    return no_async + noparrelism + nopattern + github_exception + proces_exception + no_retrieve + possible_para + det_no_pattern

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

safe_list = ["print", "try:", "ResourceExhausted", "sys.exit(1)", "time.time()", "update.message", "log.info", "time()"]

def check_safe_list(string):
    for safes in safe_list:
        if safes in string:
            return True
    return False

def judge_code(i, j, lines):
    while i < j:
        if "Nodes in between start statement and while statement" in lines[i]:
            i_copy = i + 1
            while "------" not in lines[i_copy]:
                # print(lines[i_copy])
                if lines[i_copy].isspace():
                    i_copy += 1
                    continue
                if check_safe_list(lines[i_copy]):
                    i_copy += 1
                    continue
                if "operation.done" in lines[i_copy] or "operation.result" in lines[i_copy]:
                    return True
                return False
                i_copy += 1
            return True
        i += 1
    return False
            

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

    # Judge if this is a no pattern identified case
    # If only relying on auto-tool: this should be a parallelism-used case
    if "NO PATTERN IDENTIFIED" in lines[j - 1]:
        if MANUAL_CHECKING:
            print("\n\n\n\n\n\n")
            print_writeofd("no_pattern: {}".format(lines[k].strip("\n")), ofd)
            print("Please inspect the above. Enter 1 if this is a no parallelism case, and enter 2 if this is a use-parallelism case")
            user = input()
            while user != '1' and user != '2':
                print("PRESS 1 OR 2, NOT ANYTHING ELSE!")
                user = input()
            if user == '1':
                det_no_para += 1
                print_writeofd("no_pattern (no_parallelism): {}".format(lines[k].strip("\n")), ofd)
                i = j
                continue
            elif user == '2':
                det_para += 1
                print_writeofd("no_pattern (parallelism): {}".format(lines[k].strip("\n")), ofd)
                i = j
                continue
        else:
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

    # Check if needs to prompt users on codes between start and while statement:
    if scan_block(lines, i, j, "Nodes in between start statement and while statement"):
        # If these two numbers equal then need to prompt users:
        if scan_block_numbers(lines, i, j, "Nodes in between start statement and while statement") == scan_block_numbers(lines, i, j, "Pattern identified"):
            between_code += 1
            if MANUAL_CHECKING:
                print("\n\n\n\n\n\n")
                print_code(i, j, lines)
                print("Please inspect the above. Enter 1 if can proceed, and enter 2 if this is a use_parallelism case")
                user = input()
                while user != '1' and user != '2':
                    print("PRESS 1 OR 2, NOT ANYTHING ELSE!")
                    user = input()
                if user == '1':
                    print_writeofd("code_between (proceeds): {}".format(lines[k].strip('\n')), ofd)
                elif user == '2':
                    det_para += 1
                    print_writeofd("code_between (parallelism): {}".format(lines[k].strip('\n')), ofd)
                    i = j
                    continue
            # If not manual checking, then do some ad-hoc checking and then output
            else:
                if not judge_code(i, j, lines):
                    det_no_pattern += 1
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
        raise ValueError ("Operation missing while it's neither use lambda nor no pattern identified: {}".format(lines[k]))
        exit(1)



    while i < j:
        if "***" in lines[i]:
            i_copy = i
            while i_copy < j:
                if "BOTH IDENTIFIED IN THE SAME FILE" in lines[i_copy]:
                    # Only do the following if doing manual checking
                    if MANUAL_CHECKING:
                        possible_para += 1
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
                        
                        if user == '1':
                            det_no_para += 1
                            print_writeofd("possible_parallelism (no_parallelism): {}".format(lines[k].strip("\n")), ofd)
                        elif user == '2':
                            det_para += 1
                            print_writeofd("possible_parallelism (parallelism): {}".format(lines[k].strip("\n")), ofd)
                        break
                    else:
                        i += 1
                        while i < j and "========================" not in lines[i]:
                            i += 1
                        ofd.write("possible_parallelism: {}".format(lines[k]))
                        possible_para += 1
                        break
                i_copy += 1
            if i_copy == j:
                ofd.write("no_parallelism: {}".format(lines[k]))
                noparrelism += 1
                break
        i += 1

    i = j

ofd.write("\n\n==================================================================\n")
if not MANUAL_CHECKING:
    print_writeofd("{}, Total files searched".format(allfile), ofd)
    print_writeofd("BEFORE MANUAL INSPECTION:", ofd)
    print_writeofd("{}, No use of Async".format(no_async), ofd)
    print_writeofd("{}, Github search exceptions".format(github_exception), ofd)
    print_writeofd("{}, Processing exceptions".format(proces_exception), ofd)
    print_writeofd("{}, No retrieve result".format(no_retrieve), ofd)
    print_writeofd("{}, No pattern identified".format(nopattern + det_no_pattern), ofd)
    print_writeofd("{}, No use of parallelism".format(noparrelism), ofd)
    print_writeofd("{}, Possible use of parallel cases".format(possible_para), ofd)
    print_writeofd("RELYING ON AUTO TOOL: {} NO USE OF PARALELLISM".format(noparrelism), ofd)
    print_writeofd("RELYING ON AUTO TOOL: {} PARALELLISM USED".format(possible_para + nopattern + det_no_pattern), ofd)
    print_writeofd("RELYING ON AUTO TOOL: {} RELEVANT TOTAL PROJECTS".format(noparrelism + possible_para + nopattern + det_no_pattern), ofd)

elif MANUAL_CHECKING:
    print_writeofd("", ofd)
    print_writeofd("", ofd)
    print_writeofd("After MANUAL INSPECTION:", ofd)
    print_writeofd("{}, No use of Async".format(no_async), ofd)
    print_writeofd("{}, Github search exceptions".format(github_exception), ofd)
    print_writeofd("{}, Processing exceptions".format(proces_exception), ofd)
    print_writeofd("{}, No retrieve result".format(no_retrieve), ofd)
    print_writeofd("{}, No pattern identified".format(nopattern + det_no_pattern), ofd)
    print_writeofd("{}, No use of parallelism".format(noparrelism + det_no_para), ofd)
    print_writeofd("{}, Use of parallel cases".format(det_para), ofd)
    print_writeofd("RELYING ON MANUAL CHECKING: {} NO USE OF PARALELLISM".format(noparrelism + det_no_para), ofd)
    print_writeofd("RELYING ON MANUAL CHECKING: {} PARALELLISM USED".format(det_para), ofd)
    print_writeofd("RELYING ON MANUAL CHECKING: {} RELEVANT TOTAL PROJECTS".format(noparrelism + det_no_para + det_para), ofd)

ofd.close()