#!/usr/bin/python

# File name: assembler.py
# Description:
# The assembler which is able to translate programs written in Hack
# assembly language into the binary code understood by the Hack
# hardware platform
#
# Input: .asm file
# Output: .hack file


import sys
import os
import re


A_COMMAND = "A-instruction"
C_COMMAND = "C-instruction"
L_COMMAND = "Label"

# Patterns for types of commands
regex_cmd_A = re.compile("^@(.+)")
regex_cmd_L = re.compile("^\((.+)\)$")
regex_cmd_C = re.compile(".*(=|;).*")
regex_cmd_C_dest = re.compile("(.+)=.*")
regex_cmd_C_comp = re.compile("(.*=|^)(.+?)(;.*|$)")
regex_cmd_C_jump = re.compile(".*;(.+)")
regex_isnum = re.compile("\d+")

# A map for the comp part of machine language
# comp || a c1 c2 c3 c4 c5 c6
dict_comp = {
    "0":   "0101010",
    "1":   "0111111",
    "-1":  "0111010",
    "D":   "0001100",
    "A":   "0110000",
    "M":   "1110000",
    "!D":  "0001101",
    "!A":  "0110001",
    "!M":  "1110001",
    "-D":  "0001111",
    "-A":  "0110011",
    "-M":  "1110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "M+1": "1110111",
    "1+A": "0110111",
    "1+M": "1110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "M-1": "1110010",
    "D+A": "0000010",
    "D+M": "1000010",
    "A+D": "0000010",
    "M+D": "1000010",
    "D-A": "0010011",
    "D-M": "1010011",
    "A-D": "0000111",
    "M-D": "1000111",
    "D&A": "0000000",
    "D&M": "1000000",
    "A&D": "0000000",
    "M&D": "1000000",
    "D|A": "0010101",
    "D|M": "1010101",
    "A|D": "0010101",
    "M|D": "1010101"
}

# A map for the dest
# dest || d1 d2 d3
dict_dest = {
    "null": "000",
    "M":    "001",
    "D":    "010",
    "MD":   "011",
    "DM":   "011",
    "A":    "100",
    "AM":   "101",
    "MA":   "101",
    "AD":   "110",
    "DA":   "110",
    "AMD":  "111",
    "DAM":  "111",
    "MDA":  "111",
    "ADM":  "111",
    "DMA":  "111",
    "MAD":  "111",
}

# A map for the jump
# jump || j1 j2 j3
dict_jump = {
    "null": "000",
    "JGT":  "001",
    "JEQ":  "010",
    "JGE":  "011",
    "JLT":  "100",
    "JNE":  "101",
    "JLE":  "110",
    "JMP":  "111"
}

# Any Hack assembly program is aloowed to use the following predefined symbols
dict_predefined_symbol = {
    "SP":   0,
    "LCL":  1,
    "ARG":  2,
    "THIS": 3,
    "THAT": 4,
    "R0":   0,
    "R1":   1,
    "R2":   2,
    "R3":   3,
    "R4":   4,
    "R5":   5,
    "R6":   6,
    "R7":   7,
    "R8":   8,
    "R9":   9,
    "R10":  10,
    "R11":  11,
    "R12":  12,
    "R13":  13,
    "R14":  14,
    "R15":  15,
    "SCREEN": 16384,
    "KBD":    24576
}


# The parser
class Parser:
    '''
    Encapsulates access to the input code.
    Reads an assembly language command, parse it and provides convenient access
    to the command's components. In addition, removes all white space and comments
    '''
    class Instruction:
        def __init__(self):
            # Common attribute
            self.raw_cmd_str = ""
            self.type = ""
            self.addr_rom = 0
            # A instruction: address
            self.addr = ""
            # C instruction: dest, comp and jump
            self.dest = "null"
            self.comp = "0"
            self.jump = "null"
            # Label: symbol
            self.symbol = ""

        def set_type(self, type_ins):
            self.type = type_ins

        def set_addr(self, addr):
            if A_COMMAND == self.type:
                self.addr = addr

        def set_dest(self, dest):
            if C_COMMAND == self.type:
                self.dest = dest

        def set_comp(self, comp):
            if C_COMMAND == self.type:
                self.comp = comp

        def set_jump(self, jump):
            if C_COMMAND == self.type:
                self.jump = jump

        def set_symbol(self, symbol):
            if L_COMMAND == self.type:
                self.symbol = symbol

    class Symbol_table:
        '''
        A symbol table taht keeps a correspondence between symbolic labels
        and numeric addresses
        '''
        def __init__(self):
            # Any symbol xxx appearing in an assembly program that is not predefined
            # and is not defined elsewhere using the (xxx) command is treated as a variable.
            # Variables are mapped to consecutive memory locations as they are first encountered,
            # starting at RAM address 16(0x0010)
            self.ind_var = 16
            self.dict_entries = dict_predefined_symbol

        def add_entry(self, key, value):
            self.dict_entries[key] = value

        def contains(self, key):
            if key in self.dict_entries.keys():
                return True
            else:
                return False

        def get_addr(self, key):
            if True == self.contains(key):
                return self.dict_entries[key]
            else:
                return None

    def __init__(self, str_in):
        # Get rid of the leading and trailing whitespaces
        str_in_asm = str_in.strip()
        # Remove multi-lines comments
        str_in_asm = re.sub("\/\*.*?\*\/", "", str_in_asm, flags = re.DOTALL)
        # Remove single line comments
        str_in_asm = re.sub("\/\/.*", "", str_in_asm)
        str_in_asm = str_in_asm.strip()
        self.list_in_asm = [i.strip() for i in str_in_asm.split("\n") if "" != i.strip()]

        # Initialize member variables
        self.ind_cmd = 0
        self.st = self.Symbol_table()

        # Iterate the list, parse every command, store the result into a new data structure
        list_temp = [self.first_parse(cmd) for cmd in self.list_in_asm]
        self.list_in_parsed = [self.second_parse(ins) for ins in list_temp if None != ins]
        self.len_cmd = len(self.list_in_parsed)
        self.ind_cmd = 0
        self.cmd_cur = self.list_in_parsed[self.ind_cmd]

    def first_parse(self, cmd):
        ins = self.Instruction()
        if regex_cmd_A.match(cmd):
            ins.set_type(A_COMMAND)
            ins.addr_rom = self.ind_cmd
            self.ind_cmd += 1
            ins.raw_cmd_str = cmd
            return ins

        elif regex_cmd_L.match(cmd):
            str_mth = regex_cmd_L.match(cmd).group(1)
            # The addr is a variable, look up the symbol table
            if False == self.st.contains(str_mth):
                self.st.add_entry(str_mth, self.ind_cmd)
            return None

        elif regex_cmd_C.match(cmd):
            ins.set_type(C_COMMAND)
            ins.addr_rom = self.ind_cmd
            self.ind_cmd += 1
            ins.raw_cmd_str = cmd
            return ins

    def second_parse(self, ins):
        cmd = ins.raw_cmd_str
        if A_COMMAND == ins.type:
            str_mth = regex_cmd_A.match(cmd).group(1)
            if regex_isnum.match(str_mth):
                ins.set_addr(str_mth)
            else:
                # The addr is a variable, look up the symbol table
                if self.st.contains(str_mth):
                    ins.set_addr(str(self.st.get_addr(str_mth)))
                else:
                    # The symbol table does not contain this varible, create a new varible
                    self.st.add_entry(str_mth, self.st.ind_var)
                    ins.set_addr(str(self.st.ind_var))
                    self.st.ind_var += 1

        elif C_COMMAND == ins.type:
            obj_mth_dest = regex_cmd_C_dest.match(cmd)
            obj_mth_comp = regex_cmd_C_comp.match(cmd)
            obj_mth_jump = regex_cmd_C_jump.match(cmd)

            if obj_mth_dest:
                ins.set_dest(obj_mth_dest.group(1))
            if obj_mth_comp:
                ins.set_comp(obj_mth_comp.group(2))
            if obj_mth_jump:
                ins.set_jump(obj_mth_jump.group(1))

        return ins

    def has_more_cmd(self):
        return self.ind_cmd < self.len_cmd - 1

    def advance(self):
        if True == self.has_more_cmd():
            self.ind_cmd += 1
            self.cmd_cur = self.list_in_parsed[self.ind_cmd]
            return True
        else:
            return False

    def get_command_type(self):
        return self.cmd_cur.type

    def get_symbol(self):
        if A_COMMAND == self.cmd_cur.type:
            return self.cmd_cur.addr
        elif L_COMMAND == self.cmd_cur.type:
            return self.cmd_cur.symbol
        else:
            return None

    def get_dest(self):
        if C_COMMAND == self.cmd_cur.type:
            return self.cmd_cur.dest
        else:
            return None

    def get_comp(self):
        if C_COMMAND == self.cmd_cur.type:
            return self.cmd_cur.comp
        else:
            return None

    def get_jump(self):
        if C_COMMAND == self.cmd_cur.type:
            return self.cmd_cur.jump
        else:
            return None


def validate_file_path(file_path):
    # Check if the input path is valid
    if False == os.path.exists(file_path):
        print "Input file %s does not exist" % (file_path, )
        sys.exit(1)

    if False == os.path.isfile(PATH_IN_FILE):
        print "Input %s is not a file" % (file_path, )
        sys.exit(1)

    if False == file_path.lower().endswith(".asm"):
        print "Input file %s does not have a valid extension" % (file_path, )
        sys.exit(1)


# Execution actually starts here
# Arguments pre-processing
if len(sys.argv) <= 1:
    print "Please supply the path to the .asm file"
    sys.exit(1)

for i in range(1, len(sys.argv)):
    PATH_IN_FILE = sys.argv[i]
    LIST_OU_BIN = []
    # Open the file
    try:
        fd_in_file = open(PATH_IN_FILE, "r")
    except IOError as e:
        print "I/O error: %s" % (str(e), )
    except Exception as e:
        print "Unexpected error: %s" % (str(e), )
    finally:
        parser = Parser(fd_in_file.read())
        # Close the files
        fd_in_file.close()

    flag_finish = True
    while flag_finish:
        if A_COMMAND == parser.get_command_type():
            LIST_OU_BIN.append("0%s" % (format(int(parser.cmd_cur.addr), "015b"), ))
        elif C_COMMAND == parser.get_command_type():
            LIST_OU_BIN.append("111%s%s%s" % (dict_comp[parser.cmd_cur.comp], dict_dest[parser.cmd_cur.dest], dict_jump[parser.cmd_cur.jump], ))

        flag_finish = parser.advance()

    # Write the translated program to an output file in the same folder with the input file
    PATH_OU_FILE = PATH_IN_FILE.split(".")[0] + ".hack"
    try:
        fd_ou_file = open(PATH_OU_FILE, "w+")
    except IOError as e:
        print "I/O error: %s" % (str(e), )
    except Exception as e:
        print "Unexpected error: %s" % (str(e), )
    finally:
        for line in LIST_OU_BIN:
            fd_ou_file.write(line + "\n")
        fd_ou_file.close()
        print "%s generated " % (PATH_OU_FILE, )
