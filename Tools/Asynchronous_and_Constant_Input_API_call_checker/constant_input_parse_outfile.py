import sys
import re
from utils.utils import print_writeofd

# First argument is the output file from ast_proj.py
ifd = open(sys.argv[1], 'r')

# Second argument is the output file for those projs that have constant inputs
ofd1 = open(sys.argv[2], 'w')


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
printed_ent = 0
printed_par = 0
excepted = 0

while i < len(lines):
    allfile += 1
    j = i + 1
    while j < len(lines) and lines[j] != "=================================================\n":
        j += 1
    if j == len(lines):
        break
    # Now i and j stores the start and end of one search snippet
    k = i + 1
    while i < j:
        if "Entirely Constant" in lines[i]:
            print(re.sub('\n', '', lines[i]))
            printed_ent = 1
        if "Partly Constant" in lines[i]:
            print(re.sub('\n', '', lines[i]))
            printed_par = 1
        i += 1
        if "EXCEPTION" in lines[i]:
            excepted = 1

    if printed_ent == 1 or printed_par == 1: 
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
        elif user == '1' and printed_par == 1:
            accocc_par += 1
            ofd1.write("Partly constant: ")
            ofd1.write(lines[k])
        elif user == '3' and printed_ent == 1:
            experi_ent += 1
            ofd1.write("Entirely Experimental: ")
            ofd1.write(lines[k])
        allocc += 1
        printed_ent = 0
        printed_par = 0
        print("\n\n\n\n\n\n")
    
    if excepted == 1:
        excep += 1
        ofd1.write(lines[k])
        excepted = 0
    
print_writeofd("\n\n\n\n\n", ofd1)
print_writeofd("Total file searched: {}".format(allfile), ofd1)
print_writeofd("Entirely Constants found: {}".format(accocc_ent), ofd1)
print_writeofd("Partly Constants found: {}".format(accocc_par), ofd1)
print_writeofd("Experimental Constants found: {}".format(experi_ent), ofd1)
print_writeofd("Exceptions occurred: {}".format(excep), ofd1)