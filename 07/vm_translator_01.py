#!/usr/bin/python

# File name: vm_translator_01.py
# Description:
# The vm translator is able to translate the intermediate language
# into assembly language
#
# Input: .vm file(s)
# Output: .asm file


import sys
import os
import re


# command type, described by hex codes starting from 0x60
C_ARITHEMETIC=0x60
C_PUSH=0x61
C_POP=0x62
C_GOTO=0x63
C_IF=0x64
C_FUNCTION=0x65
C_RETURN=0x66
C_CALL=0x67

# Patterns for types of commands
regex_cmd_push = re.compile("^push\s+(\w+)\s+(\d+)$")
regex_cmd_pop  = re.compile("^pop\s+(\w+)\s+(\d+)$")
regex_mem_seg  = re.compile("(argument|local|static|constant|this|that|pointer|temp)")
regex_cmd_ari  = re.compile("(add|sub|neg|eq|gt|lt|and|or|not)")
regex_cmd_goto = re.compile("goto\s+(\w+)")
regex_cmd_if   = re.compile("if-goto\s+(\w+)")
regex_cmd_func = re.compile("function\s+(\w+)\s+(\d+)")
regex_cmd_call = re.compile("call\s+(\w+)\s+(\d+)")
regex_cmd_ret  = re.compile("return")


# The parser
class Parser:
    '''
    Handles the parsing of a single .vm file, and encapsulates access to the input code. It
    reads VM commands, parses them, and provides convenient access to their components. In
    addition, it removes all extra white-spaces and comments.
    '''
    class Command:
        def __init__(self):
            # Common attribute
            self.raw_str = ""
            self.type  = ""
            self.arg1  = ""
            self.arg2  = ""
            self.index = 0

        def set_type(self, type):
            self.type = type

        def set_arg1(self, arg):
            self.arg1 = arg

        def set_arg2(self, arg):
            self.arg2 = arg

        def set_index(self, ind):
            self.index = ind

        def get_type(self):
            return self.type

        def get_arg1(self):
            if C_RETURN == self.type:
                return None
            elif C_ARITHEMETIC == self.type:
                return self.raw_str
            else:
                return self.arg1

        def get_arg2(self):
            if C_PUSH == self.type or \
               C_POP == self.type or \
               C_FUNCTION == self.type or \
               C_CALL == self.type:
                return self.arg2
            else:
                return None

        def get_index(self):
            return self.index

    class CodeWriter:
        def __init__(self, file_name):
            self.file_name = file_name
            self.list_ou_asm = []

        def writeArithmetic(self, cmd):
            asm_cmds = []
            # arithmetic commands
            if "add" == cmd.get_arg1():
                asm_cmds = [
                    "@SP",
                    "AM=M-1",
                    "D=M",
                    "A=A-1",
                    "M=M+D"
                ]
            elif "sub" == cmd.get_arg1():
                asm_cmds = [
                    "@SP",
                    "AM=M-1",
                    "D=M",
                    "A=A-1",
                    "M=M-D"
                ]
            elif "neg" == cmd.get_arg1():
                asm_cmds = [
                    "@SP",
                    "A=M-1",
                    "M=-M",
                ]
            elif "and" == cmd.get_arg1():
                asm_cmds = [
                    "@SP",
                    "AM=M-1",
                    "D=M",
                    "A=A-1",
                    "M=M&D"
                ]
            elif "or" == cmd.get_arg1():
                asm_cmds = [
                    "@SP",
                    "AM=M-1",
                    "D=M",
                    "A=A-1",
                    "M=M|D"
                ]
            elif "not" == cmd.get_arg1():
                asm_cmds = [
                    "@SP",
                    "A=M-1",
                    "M=!M",
                ]
            # logical commands
            elif "eq" == cmd.get_arg1():
                asm_cmds = [
                    "@SP",
                    "AM=M-1",
                    "D=M",
                    "A=A-1",
                    "D=M-D",
                    "@TRUE.%d" % (cmd.index, ),
                    "D;JEQ",
                    "@FALSE.%d" % (cmd.index, ),
                    "D;JNE",
                    "(TRUE.%d)" % (cmd.index, ),
                    "D=-1",
                    "@END.%d" % (cmd.index, ),
                    "0;JMP",
                    "(FALSE.%d)" % (cmd.index, ),
                    "D=0",
                    "@END.%d" % (cmd.index, ),
                    "0;JMP",
                    "(END.%d)" % (cmd.index, ),
                    "@SP",
                    "A=M-1",
                    "M=D",
                ]
            elif "gt" == cmd.get_arg1():
                asm_cmds = [
                    "@SP",
                    "AM=M-1",
                    "D=M",
                    "A=A-1",
                    "D=M-D",
                    "@TRUE.%d" % (cmd.index, ),
                    "D;JGT",
                    "@FALSE.%d" % (cmd.index, ),
                    "D;JLE",
                    "(TRUE.%d)" % (cmd.index, ),
                    "D=-1",
                    "@END.%d" % (cmd.index, ),
                    "0;JMP",
                    "(FALSE.%d)" % (cmd.index, ),
                    "D=0",
                    "@END.%d" % (cmd.index, ),
                    "0;JMP",
                    "(END.%d)" % (cmd.index, ),
                    "@SP",
                    "A=M-1",
                    "M=D",
                ]
            elif "lt" == cmd.get_arg1():
                asm_cmds = [
                    "@SP",
                    "AM=M-1",
                    "D=M",
                    "A=A-1",
                    "D=M-D",
                    "@TRUE.%d" % (cmd.index, ),
                    "D;JLT",
                    "@FALSE.%d" % (cmd.index, ),
                    "D;JGE",
                    "(TRUE.%d)" % (cmd.index, ),
                    "D=-1",
                    "@END.%d" % (cmd.index, ),
                    "0;JMP",
                    "(FALSE.%d)" % (cmd.index, ),
                    "D=0",
                    "@END.%d" % (cmd.index, ),
                    "0;JMP",
                    "(END.%d)" % (cmd.index, ),
                    "@SP",
                    "A=M-1",
                    "M=D",
                ]
            self.list_ou_asm += asm_cmds

        def writePushPop(self, cmd):
            if "constant" == cmd.get_arg1():
                asm_cmds = [
                    "@%s" % (cmd.get_arg2(),),
                    "D=A",
                    "@SP",
                    "A=M",
                    "M=D",
                    "@SP",
                    "M=M+1"
                ]

            elif C_PUSH == cmd.get_type():
                if "local" == cmd.get_arg1():
                    asm_cmds = [
                        "@LCL",
                        "D=M",
                        "@%s" % (cmd.get_arg2(), ),
                        "A=D+A",
                        "D=M",
                        "@SP",
                        "A=M",
                        "M=D",
                        "@SP",
                        "M=M+1"
                    ]
                elif "argument" == cmd.get_arg1():
                    asm_cmds = [
                        "@ARG",
                        "D=M",
                        "@%s" % (cmd.get_arg2(), ),
                        "A=D+A",
                        "D=M",
                        "@SP",
                        "A=M",
                        "M=D",
                        "@SP",
                        "M=M+1"
                    ]
                elif "pointer" == cmd.get_arg1():
                    asm_cmds = [
                        "@%s" % (cmd.get_arg2(), ),
                        "D=A",
                        "@R3",
                        "A=D+A",
                        "D=M",
                        "@SP",
                        "A=M",
                        "M=D",
                        "@SP",
                        "M=M+1"
                    ]
                elif "this" == cmd.get_arg1():
                    asm_cmds = [
                        "@THIS",
                        "D=M",
                        "@%s" % (cmd.get_arg2(), ),
                        "A=D+A",
                        "D=M",
                        "@SP",
                        "A=M",
                        "M=D",
                        "@SP",
                        "M=M+1"
                    ]
                elif "that" == cmd.get_arg1():
                    asm_cmds = [
                        "@THAT",
                        "D=M",
                        "@%s" % (cmd.get_arg2(), ),
                        "A=D+A",
                        "D=M",
                        "@SP",
                        "A=M",
                        "M=D",
                        "@SP",
                        "M=M+1"
                    ]
                elif "temp" == cmd.get_arg1():
                    asm_cmds = [
                        "@%s" % (cmd.get_arg2(), ),
                        "D=A",
                        "@R5",
                        "A=D+A",
                        "D=M",
                        "@SP",
                        "A=M",
                        "M=D",
                        "@SP",
                        "M=M+1"
                    ]
                elif "static" == cmd.get_arg1():
                    asm_cmds = [
                        "@%s.%s" % (self.file_name, cmd.get_arg2(), ),
                        "D=M",
                        "@SP",
                        "A=M",
                        "M=D",
                        "@SP",
                        "M=M+1"
                    ]

            elif C_POP == cmd.get_type():
                if "local" == cmd.get_arg1():
                    asm_cmds = [
                        "@SP",
                        "AM=M-1",
                        "D=M",
                        "@LCL",
                        "A=M"
                    ]
                    for i in range(int(cmd.get_arg2())):
                        asm_cmds.append("A=A+1")
                    asm_cmds.append("M=D")
                elif "argument" == cmd.get_arg1():
                    asm_cmds = [
                        "@SP",
                        "AM=M-1",
                        "D=M",
                        "@ARG",
                        "A=M"
                    ]
                    for i in range(int(cmd.get_arg2())):
                        asm_cmds.append("A=A+1")
                    asm_cmds.append("M=D")
                elif "pointer" == cmd.get_arg1():
                    asm_cmds = [
                        "@SP",
                        "AM=M-1",
                        "D=M",
                        "@R3",
                    ]
                    for i in range(int(cmd.get_arg2())):
                        asm_cmds.append("A=A+1")
                    asm_cmds.append("M=D")
                elif "this" == cmd.get_arg1():
                    asm_cmds = [
                        "@SP",
                        "AM=M-1",
                        "D=M",
                        "@THIS",
                        "A=M"
                    ]
                    for i in range(int(cmd.get_arg2())):
                        asm_cmds.append("A=A+1")
                    asm_cmds.append("M=D")
                elif "that" == cmd.get_arg1():
                    asm_cmds = [
                        "@SP",
                        "AM=M-1",
                        "D=M",
                        "@THAT",
                        "A=M"
                    ]
                    for i in range(int(cmd.get_arg2())):
                        asm_cmds.append("A=A+1")
                    asm_cmds.append("M=D")
                elif "temp" == cmd.get_arg1():
                    asm_cmds = [
                        "@SP",
                        "AM=M-1",
                        "D=M",
                        "@R5",
                    ]
                    for i in range(int(cmd.get_arg2())):
                        asm_cmds.append("A=A+1")
                    asm_cmds.append("M=D")
                elif "static" == cmd.get_arg1():
                    asm_cmds = [
                        "@SP",
                        "AM=M-1",
                        "D=M",
                        "@%s.%s" % (self.file_name, cmd.get_arg2(), ),
                        "M=D",
                    ]

            self.list_ou_asm += asm_cmds

        def genCmds(self, list_in_vm):
            for cmd in list_in_vm:
                if C_ARITHEMETIC == cmd.get_type():
                    self.writeArithmetic(cmd)
                elif C_POP == cmd.get_type() or C_PUSH == cmd.get_type():
                    self.writePushPop(cmd)

            # this is a normal way to end a asm file
            asm_cmds = [
                "(END_OF_FILE)",
                "@END_OF_FILE",
                "0;JMP"
            ]
            self.list_ou_asm += asm_cmds

        def get_output(self):
            return self.list_ou_asm

    def __init__(self, str_in, file_path):
        # get rid of the leading and trailing whitespaces
        str_in_vm = str_in.strip()
        # remove multi-lines comments. Note that the question mark(?) here indicates a non-greedy match mode
        str_in_vm = re.sub("\/\*.*?\*\/", "", str_in_vm, flags = re.DOTALL)
        # remove single line comments
        str_in_vm = re.sub("\/\/.*", "", str_in_vm)
        str_in_vm = str_in_vm.strip()
        self.list_in_vm = [i.strip() for i in str_in_vm.split("\n") if "" != i.strip()]
        self.list_in_parsed = []
        self.file_name = file_path.split("/")[-1].split(".")[0]
        self.cw = self.CodeWriter(self.file_name)

    def parse_vm_code(self):
        self.ind_cmd = 0
        # iterate the list, parse every command, store the result into a new data structure
        self.list_in_parsed = [self.parse_command(cmd) for cmd in self.list_in_vm]
        self.len_cmd = len(self.list_in_parsed)
        self.ind_cmd = -1  # according the description in the book, there is no current command initially
        self.cmd_cur = None

    def generate_asm_code(self):
        self.cw.genCmds(self.list_in_parsed)
        return self.cw.get_output()

    def parse_command(self, raw_cmd):
        cmd = self.Command()
        cmd.set_index(self.ind_cmd)
        self.ind_cmd += 1
        cmd.raw_str = raw_cmd

        if regex_cmd_ari.match(raw_cmd):
            cmd.set_type(C_ARITHEMETIC)
        elif regex_cmd_push.match(raw_cmd):
            cmd.set_type(C_PUSH)
            obj_matched = regex_cmd_push.match(raw_cmd)
            cmd.set_arg1(obj_matched.group(1))
            cmd.set_arg2(obj_matched.group(2))
        elif regex_cmd_pop.match(raw_cmd):
            cmd.set_type(C_POP)
            obj_matched = regex_cmd_pop.match(raw_cmd)
            cmd.set_arg1(obj_matched.group(1))
            cmd.set_arg2(obj_matched.group(2))
        elif regex_cmd_goto.match(raw_cmd):
            cmd.set_type(C_GOTO)
            obj_matched = regex_cmd_goto.match(raw_cmd)
            cmd.set_arg1(obj_matched.group(1))
        elif regex_cmd_if.match(raw_cmd):
            cmd.set_type(C_IF)
            obj_matched = regex_cmd_if.match(raw_cmd)
            cmd.set_arg1(obj_matched.group(1))
        elif regex_cmd_func.match(raw_cmd):
            cmd.set_type(C_FUNCTION)
            obj_matched = regex_cmd_func.match(raw_cmd)
            cmd.set_arg1(obj_matched.group(1))
            cmd.set_arg2(obj_matched.group(2))
        elif regex_cmd_ret.match(raw_cmd):
            cmd.set_type(C_RETURN)
        elif regex_cmd_call.match(raw_cmd):
            cmd.set_type(C_call)
            obj_matched = regex_cmd_call.match(raw_cmd)
            cmd.set_arg1(obj_matched.group(1))
            cmd.set_arg2(obj_matched.group(2))

        return cmd


def validate_file_path(file_path):
    # Check if the input path is valid
    if False == os.path.exists(file_path):
        print "Input file %s does not exist" % (file_path, )
        return False

    if False == os.path.isfile(file_path):
        print "Input %s is not a file" % (file_path, )
        return False

    if False == file_path.lower().endswith(".vm"):
        print "Input file %s does not have a valid extension" % (file_path, )
        return False


def main():
    # arguments pre-processing
    if len(sys.argv) <= 1:
        print "Please supply the path to the .vm file(s)"
        sys.exit(1)

    for i in range(1, len(sys.argv)):
        PATH_IN_FILE = sys.argv[i]
        if False == validate_file_path(PATH_IN_FILE):
            sys.exit(1)

        LIST_OU_ASM = []
        # Open the file
        try:
            fd_in_file = open(PATH_IN_FILE, "r")
        except IOError as e:
            print "I/O error: %s" % (str(e), )
            sys.exit(1)
        except Exception as e:
            print "Unexpected error: %s" % (str(e), )
            sys.exit(1)

        parser = Parser(fd_in_file.read(), PATH_IN_FILE)
        # Close the files
        fd_in_file.close()
        parser.parse_vm_code()
        LIST_OU_ASM = parser.generate_asm_code()

        # write the translated program to an output file in the same folder
        PATH_OU_FILE = PATH_IN_FILE.split(".")[0] + ".asm"
        try:
            fd_ou_file = open(PATH_OU_FILE, "w")
        except IOError as e:
            print "I/O error: %s" % (str(e), )
        except Exception as e:
            print "Unexpected error: %s" % (str(e), )
        finally:
            for line in LIST_OU_ASM:
                fd_ou_file.write(line + "\n")
            fd_ou_file.close()
            print "%s generated " % (PATH_OU_FILE, )

if "__main__" == __name__:
    main()
