#!/usr/bin/python

# File name: vm_translator.py
# Description:
# A full scale VM translator
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
C_LABEL=0x63
C_GOTO=0x64
C_IF=0x65
C_FUNCTION=0x66
C_RETURN=0x67
C_CALL=0x68

# Patterns for types of commands
regex_cmd_push  = re.compile("^push\s+(\w+)\s+(\d+)$")
regex_cmd_pop   = re.compile("^pop\s+(\w+)\s+(\d+)$")
regex_mem_seg   = re.compile("(argument|local|static|constant|this|that|pointer|temp)")
regex_cmd_ari   = re.compile("(add|sub|neg|eq|gt|lt|and|or|not)")
regex_cmd_label = re.compile("label\s+([\w|\.|\$]+)")
regex_cmd_goto  = re.compile("goto\s+([\w|\.|\$]+)")
regex_cmd_if    = re.compile("if-goto\s+([\w|\.|\$]+)")
regex_cmd_func  = re.compile("function\s+([\w|\.|\$]+)\s+(\d+)")
regex_cmd_call  = re.compile("call\s+([\w|\.|\$]+)\s+(\d+)")
regex_cmd_ret   = re.compile("return")

BOOTSTRAP_CODE = [
    "@256",  # set SP to 256
    "D=A",
    "@SP",
    "M=D",
    "@FUNC_Sys.init_END",  # call Sys.init
    "D=A",
    "@SP",
    "A=M",
    "M=D",
    "@SP",
    "M=M+1",
    "@LCL",  # push LCL
    "D=M",
    "@SP",
    "A=M",
    "M=D",
    "@SP",
    "M=M+1",
    "@ARG",  # push ARG
    "D=M",
    "@SP",
    "A=M",
    "M=D",
    "@SP",
    "M=M+1",
    "@THIS",  # push THIS
    "D=M",
    "@SP",
    "A=M",
    "M=D",
    "@SP",
    "M=M+1",
    "@THAT",  # push THAT
    "D=M",
    "@SP",
    "A=M",
    "M=D",
    "@SP",
    "M=M+1",
    "@SP",    # ARG = SP - n -5
    "D=M-1",
    "D=D-1",
    "D=D-1",
    "D=D-1",
    "D=D-1",
    "@ARG",
    "M=D",
    "@SP",    # LCL = SP
    "D=M",
    "@LCL",
    "M=D",
    "@FUNC_Sys.init_START",
    "0;JMP",
    "(FUNC_Sys.init_END)"
]
# The parser
class Parser:
    '''
    Handles the parsing of a single .vm file, and encapsulates access to the input code. It
    reads VM commands, parses them, and provides convenient access to their components. In
    addition, it removes all extra white-spaces and comments.
    '''
    class Command:
        '''
        Every instance of this class corresponds to a vm command
        '''
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
            self.func_name = "Sys.init"
            self.list_ou_asm = []

        def set_func_name(self, name):
            self.func_name = name

        def get_func_name(self):
            return self.func_name

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

        def writeProgramFlow(self, cmd):
            if C_LABEL == cmd.get_type():
                asm_cmds = [
                    "(%s$%s)" % (self.get_func_name(), cmd.get_arg1(), )
                ]
            elif C_GOTO == cmd.get_type():
                asm_cmds = [
                    "@%s$%s" % (self.get_func_name(), cmd.get_arg1(), ),
                    "0;JMP"
                ]
            elif C_IF == cmd.get_type():
                asm_cmds = [
                    "@SP",
                    "AM=M-1",
                    "D=M",
                    "@%s$%s" % (self.get_func_name(), cmd.get_arg1(), ),
                    "D;JNE"
                ]

            self.list_ou_asm += asm_cmds

        def writeFunctions(self, cmd):
            '''
            write function related assembly instructions
            '''
            if C_FUNCTION == cmd.get_type():
                self.set_func_name(cmd.get_arg1())
                asm_cmds = [
                    "(FUNC_%s_START)" % (self.get_func_name(), ),
                ]
                for i in range(int(cmd.get_arg2())):
                    asm_cmds += [
                        "@SP",  # initialize all the local variables
                        "A=M",
                        "M=0",
                        "@SP",
                        "M=M+1",
                    ]
            elif C_RETURN == cmd.get_type():
                asm_cmds = [
                    "@LCL",  # FRAME = LCL
                    "D=M",
                    "@R13",  # R13 is for FRAME
                    "M=D",
                    "@5",    # RET = *(FRAME - 5)
                    "A=D-A",
                    "D=M",
                    "@R14",
                    "M=D",   # R14 is for RET
                    "@SP",   # *ARG = pop()
                    "AM=M-1",
                    "D=M",
                    "@ARG",
                    "A=M",
                    "M=D",
                    "@ARG",  # SP = ARG + 1
                    "D=M+1",
                    "@SP",
                    "M=D",
                    "@R13",  # THAT = *(FRAME - 1)
                    "AM=M-1",
                    "D=M",
                    "@THAT",
                    "M=D",
                    "@R13",  # THIS = *(FRAME - 2)
                    "AM=M-1",
                    "D=M",
                    "@THIS",
                    "M=D",
                    "@R13",  # ARG = *(FRAME - 3)
                    "AM=M-1",
                    "D=M",
                    "@ARG",
                    "M=D",
                    "@R13",  # LCL = *(FRAME - 4)
                    "AM=M-1",
                    "D=M",
                    "@LCL",
                    "M=D",
                    "@R14",  # goto RET
                    "A=M",
                    "0;JMP",
                ]

            elif C_CALL == cmd.get_type():
                asm_cmds = [
                    "@FUNC_%s_END_%d" % (cmd.get_arg1(), cmd.get_index()),  # push return-address
                    "D=A",
                    "@SP",
                    "A=M",
                    "M=D",
                    "@SP",
                    "M=M+1",
                    "@LCL",  # push LCL
                    "D=M",
                    "@SP",
                    "A=M",
                    "M=D",
                    "@SP",
                    "M=M+1",
                    "@ARG",  # push ARG
                    "D=M",
                    "@SP",
                    "A=M",
                    "M=D",
                    "@SP",
                    "M=M+1",
                    "@THIS",  # push THIS
                    "D=M",
                    "@SP",
                    "A=M",
                    "M=D",
                    "@SP",
                    "M=M+1",
                    "@THAT",  # push THAT
                    "D=M",
                    "@SP",
                    "A=M",
                    "M=D",
                    "@SP",
                    "M=M+1",
                    "@SP",    # ARG = SP - n -5
                    "D=M-1",
                    "D=D-1",
                    "D=D-1",
                    "D=D-1",
                    "D=D-1",
                ]
                for i in range(int(cmd.get_arg2())):
                    asm_cmds += [
                        "D=D-1",
                    ]
                asm_cmds += [
                    "@ARG",
                    "M=D",
                    "@SP",  # LCL = SP
                    "D=M",
                    "@LCL",
                    "M=D",
                    "@FUNC_%s_START" % (cmd.get_arg1(), ),
                    "0;JMP",
                    "(FUNC_%s_END_%d)" % (cmd.get_arg1(), cmd.get_index(), ),  # declare a label for rthe return address
                ]
            self.list_ou_asm += asm_cmds

        def genCmds(self, list_in_vm):
            if "Sys" != self.file_name:
                self.list_ou_asm += [
                    "@FILE_%s_END" % (self.file_name, ),
                    "0;JMP",
                ]
            for cmd in list_in_vm:
                if C_ARITHEMETIC == cmd.get_type():
                    self.writeArithmetic(cmd)
                elif C_POP == cmd.get_type() or C_PUSH == cmd.get_type():
                    self.writePushPop(cmd)
                elif C_LABEL == cmd.get_type() or C_GOTO == cmd.get_type() or C_IF == cmd.get_type():
                    self.writeProgramFlow(cmd)
                elif C_FUNCTION == cmd.get_type() or C_RETURN == cmd.get_type() or C_CALL == cmd.get_type():
                    self.writeFunctions(cmd)

            if "Sys" != self.file_name:
                self.list_ou_asm += [
                    "(FILE_%s_END)" % (self.file_name, ),
                ]
        def get_output(self):
            return self.list_ou_asm

    def __init__(self, file_path):
        self.list_in_vm = []      # a list of raw vm commands after pre-processing
        self.list_in_parsed = []  # a list of Command instances after vm parsing
        self.file_name = os.path.basename(file_path).split(".")[0]  # file name of the current vm file, used for static variables
        self.cw = self.CodeWriter(self.file_name)  # an instance of code writer
        self.ind_cmd = 0  # global index for vm commands in a vm file


    def set_input_str(self, str_in):
        '''
        Feed the raw vm file content to this class and do some pre-preocessing
        '''
        # get rid of the leading and trailing whitespaces
        str_in_vm = str_in.strip()
        # remove multi-lines comments. Note that the question mark(?) here indicates a non-greedy match mode
        str_in_vm = re.sub("\/\*.*?\*\/", "", str_in_vm, flags = re.DOTALL)
        # remove single line comments
        str_in_vm = re.sub("\/\/.*", "", str_in_vm)
        str_in_vm = str_in_vm.strip()
        self.list_in_vm = [i.strip() for i in str_in_vm.split("\n") if "" != i.strip()]

    def parse_vm_code(self):
        # iterate the list, parse every command, store the result into a new data structure
        for cmd in self.list_in_vm:
            self.list_in_parsed.append(self.parse_vm_command(cmd))

    def generate_asm_code(self):
        self.cw.genCmds(self.list_in_parsed)
        return self.cw.get_output()

    def parse_vm_command(self, raw_cmd):
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
        elif regex_cmd_label.match(raw_cmd):
            cmd.set_type(C_LABEL)
            obj_matched = regex_cmd_label.match(raw_cmd)
            cmd.set_arg1(obj_matched.group(1))
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
            cmd.set_type(C_CALL)
            obj_matched = regex_cmd_call.match(raw_cmd)
            cmd.set_arg1(obj_matched.group(1))
            cmd.set_arg2(obj_matched.group(2))

        return cmd


def validate_file_path(file_path):
    if False == file_path.lower().endswith(".vm"):
        return False
    return True

def path_pre_process(file_path):
    list_files = []
    # Check if the input path is valid
    if False == os.path.exists(file_path):
        print "Input path %s does not exist" % (file_path, )
        return list_files

    if True == os.path.isfile(file_path):
        if True == validate_file_path(file_path):
            list_files.append(file_path)
    elif True == os.path.isdir(file_path):
        files = os.listdir(file_path)
        for f in files:
            child_file_path = file_path + "/" + f
            if True == validate_file_path(child_file_path):
                list_files.append(child_file_path)
    else:
        print "Input path is neither a file nor a folder!"

    return list_files

def create_asm_file(file_path, list_asm_code):
    output_file_path = ""
    if os.path.isfile(file_path):
         output_file_path = file_path.split(".")[0] + ".asm"
    elif os.path.isdir(file_path):
        output_file_path = file_path + "/" + os.path.basename(file_path) + ".asm"

    try:
        fd_ou_file = open(output_file_path, "w")
    except IOError as e:
        print "I/O error: %s" % (str(e), )
        sys.exit(1)
    except Exception as e:
        print "Unexpected error: %s" % (str(e), )
        sys.exit(1)
    finally:
        for line in list_asm_code:
            fd_ou_file.write(line + "\n")
        fd_ou_file.close()
        print "%s generated " % (output_file_path, )

def main():
    # arguments pre-processing
    if len(sys.argv) <= 1:
        print "Please supply the path to the .vm file(s)"
        sys.exit(1)

    # if the system argument is a path to file, then translate this file to a single asm file
    # if the system argument is a foler, then translate all the vm files in that folder to a single asm file
    LIST_OU_ASM = []
    IN_FILES = []
    PATH_INPUT = os.path.normpath(sys.argv[1])

    IN_FILES = path_pre_process(PATH_INPUT)
    if 0 == len(IN_FILES):
        sys.exit(1)

    for vm_file in IN_FILES:
        # Open the file
        try:
            fd_in_file = open(vm_file, "r")
        except IOError as e:
            print "I/O error: %s" % (str(e), )
            sys.exit(1)
        except Exception as e:
            print "Unexpected error: %s" % (str(e), )
            sys.exit(1)

        parser = Parser(vm_file)
        parser.set_input_str(fd_in_file.read())
        # Close the files
        fd_in_file.close()
        parser.parse_vm_code()
        LIST_OU_ASM += parser.generate_asm_code()

    LIST_OU_ASM = BOOTSTRAP_CODE + LIST_OU_ASM
    create_asm_file(PATH_INPUT, LIST_OU_ASM)

if "__main__" == __name__:
    main()
