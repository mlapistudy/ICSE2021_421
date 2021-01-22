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

# Second argument is the output file from ast_proj.py
ifd = open(sys.argv[2], 'r')

# Third argument is the output file for those projs that have constant inputs
ofd1 = open(sys.argv[3], 'w')


# All files number
allfile = 0
# Actual determined occurence of Constant, entirely or partly:
accocc_ent = 0
accocc_par = 0
experi_ent = 0
# Number of exception:
excep = 0

lines = ifd.readlines()
i = 0
j = 0
printed_ent_count = 0
# printed_par_count = 0
excepted = 0


# Ad-hoc take care of some cases where the traced line because
# a library call with constant parameters can actually return non-constant results
def auto_exclude_cases(line):
    exclusion = ["Entirely Constant: ||\n", "Entirely Constant: string||\n", "Entirely Constant:\n",
                 "Entirely Constant: Hello, World!||\n", "Entirely Constant: hello world||\n", "Entirely Constant: ?||\n",
                 "Entirely Constant: polly||\n", "Entirely Constant: texttospeech||\n", "Entirely Constant: utf8||\n",
                 "Entirely Constant: ap-south-1||\n", "Entirely Constant: txt||\n", "Entirely Constant: mp3||\n", 
                 "Entirely Constant: Message||||\n", "Entirely Constant: Text:||\n", "Entirely Constant: test1234||\n",
                 "Entirely Constant: Enter something : ||\n", "Entirely Constant: AWSPollyIMGSpeech||\n",
                 "Entirely Constant: TranslatedText||\n", "Entirely Constant: <speak>||\n", "Entirely Constant: w||\n",
                 "Entirely Constant: :||\n", "Entirely Constant: Hello World!||\n", "Entirely Constant: Hello world!||\n",
                 "Entirely Constant:\n"]
    for exc in exclusion:
        if (line == exc):
            return True

    inclusion = [".wav||\n", ".txt||\n", ".jpg||\n", ".png||\n"]

    for inc in inclusion:
        if inc in line:
            return True

    return False

while i < len(lines):
    printed_ent = 0
    experi = 0
    allfile += 1
    j = i + 1
    while j < len(lines) and lines[j] != "=================================================\n":
        j += 1
    if j == len(lines):
        break
    # Now i and j stores the start and end of one search snippet
    k = i + 1
    while i < j:
        if auto_exclude_cases(lines[i]):
            i += 1
            continue
        if "Entirely Constant" in lines[i]:
            if MANUAL_CHECKING:
                print(re.sub('\n', '', lines[i]))
            printed_ent = 1
        i += 1
        if "EXCEPTION" in lines[i]:
            excepted = 1

    # if printed_ent or experi:
    #     printed_ent_count += 1
    # if printed_par:
    #     printed_par_count += 1
 
    if MANUAL_CHECKING:
        if printed_ent == 1: #or printed_par == 1: 
            print("Does the above snippet contains an actual string constant? If constant, press 1, if not, press 2, if looks like for experimental purpose, press 3")
            user = input()
            while user != '1' and user != '2' and user != '3':
                print("PRESS 1 OR 2 OR 3, NOT ANYTHING ELSE!")
                user = input()
            # If one of these is entirely constant, treat the entire project as entirely constant
            if user == '1' and printed_ent == 1:
                accocc_ent += 1
                ofd1.write("Entirely constant: ")
                ofd1.write(lines[k])
            elif user == '2' and printed_ent == 1:
                ofd1.write("Auto tool wrong detection: ")
                ofd1.write(lines[k])
            elif user == '3' and printed_ent == 1:
                experi_ent += 1
                ofd1.write("Entirely Experimental: ")
                ofd1.write(lines[k])
            printed_ent = 0
            printed_par = 0
            print("\n\n\n\n\n\n")
    else:
        if printed_ent == 1:
            ofd1.write("Entirely constant: ")
            ofd1.write(lines[k])
            accocc_ent += 1

        
    if excepted == 1:
        excep += 1
        ofd1.write(lines[k])
        excepted = 0
    
print_writeofd("\n\n\n\n\n", ofd1)
print_writeofd("Total file searched: {}".format(allfile), ofd1)
print_writeofd("Entirely Constants found: {}".format(accocc_ent), ofd1)
# print_writeofd("Partly Constants found: {}".format(accocc_par), ofd1)
print_writeofd("Experimental Constants found: {}".format(experi_ent), ofd1)
print_writeofd("Exceptions occurred: {}".format(excep), ofd1)

if MANUAL_CHECKING:
    print_writeofd("RELYING ON MANUAL CHECKING: {} CONSTANT INPUTS".format(accocc_ent), ofd1)
    print_writeofd("RELYING ON MANUAL CHECKING: {} RELEVANT TOTAL PROJECTS".format(allfile - excep), ofd1)
else:
    print_writeofd("RELYING ON AUTO TOOL: {} CONSTANT INPUTS".format(accocc_ent), ofd1)
    print_writeofd("RELYING ON AUTO TOOL: {} RELEVANT TOTAL PROJECTS".format(allfile - excep), ofd1)