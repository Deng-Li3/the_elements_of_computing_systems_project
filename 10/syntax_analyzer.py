#!/usr/bin/python

# File name: syntax_analyzer.py
# Description:
# The first half of the Jack compiler
#
# Input: .jack file(s)
# Output: .xml file(s)


import sys
import os
import re

import xml.etree.ElementTree as ET
import xml.dom.minidom as md

class Token:
    '''
    one single token
    '''
    def __init__(self, token_type, raw_str, match_str):
        self.token_type = token_type
        self.raw_str = raw_str
        self.match_str = match_str

    def get_type(self):
        return self.token_type

    def get_raw_str(self):
        return self.raw_str

    def get_mth_str(self):
        return self.match_str


class Regex:
    '''
    specific regex expression object with a name
    '''
    def __init__(self, reg_name, pattern):
        self.reg_name = reg_name
        self.reg_obj  = re.compile(pattern)

    def get_name(self):
        return self.reg_name

    def match(self, string):
        return self.reg_obj.match(string)


lex_ele_regex_list = [
    # lexical elements, please note the order of items in this list is important.
    Regex("keyword", "^(class|constructor|function|method|field|static|var|int|char|boolean|void|true|false|null|this|let|do|if|else|while|return)[\W]+"),
    Regex("symbol", "^(>=|<=|[{}()\[\]\.,;\+\-\*\/\&\|<>=~])"),
    Regex("integerConstant", "^(\d+)"),
    Regex("stringConstant", "^\"(.*?)\""),
    Regex("identifier", "^([a-zA-Z|\d]\w*)")
]

class JackAnalyzer:
    '''
    top level module that sets up and invokes other sub-modules
    '''
    class JackTokenizer:
        '''
        Remove all comments and white space from the input stream and breaks it
        into Jack lanaguage tokens, as specified by the Jack grammar
        '''
        def __init__(self, file_path):
            self.in_file_path = file_path
            self.fd_in_file = None
            # read the file and sanitize the content
            try:
                self.fd_in_file = open(file_path, "r")
            except IOError as e:
                print "I/O error: %s" % (str(e), )
                sys.exit(1)
            except Exception as e:
                print "Unexpected error: %s" % (str(e), )
                sys.exit(1)
            self.file_content = self.fd_in_file.read()
            self.file_content_list = self.input_sanitize(self.file_content)
            self.tok_list = []

            # the first step in the syntax analysis of a program is to group the characters into tokens
            self.tokenize()

            # prepare for the next steps
            self.tok_len = len(self.tok_list)
            self.token_index = -1
            self.current_token = None # there is no current token initially

        def advance(self):
            '''
            API function
            Gets the next token from the input and makes it the current token.
            This method should only be called if hasMoreTokens() is True. Initialy,
            there is no current token
            '''
            if True == self.hasMoreTokens():
                self.token_index += 1
                self.current_token = self.tok_list[self.token_index]
                return self.current_token
            else:
                return None

        def rollBack(self):
            if self.token_index > 0:
                self.token_index -= 1
                self.current_token = self.tok_list[self.token_index]
                return self.current_token
            else:
                return None

        def hasMoreTokens(self):
            '''
            API function
            Do we have more tokens in the input
            '''
            if self.token_index < (self.tok_len - 1):
                return True
            else:
                return False

        def tokenType(self):
            '''
            API function
            Returns the type of the current token
            '''
            return self.current_token.get_type()

        def keyWord(self):
            '''
            API function
            Returns the keyword which is the current token. Should be called only
            when tokenType() is KEYWORD
            '''
            if "keyword" == self.tokenType():
                return self.current_token.get_mth_str()
            else:
                return None

        def symbol(self):
            '''
            API function
            Returns the character which is the current token. Should be called only
            when tokenType() is SYMBOL
            '''
            if "symbol" == self.tokenType():
                return self.current_token.get_mth_str()
            else:
                return None

        def identifier(self):
            '''
            API function
            Returns the identifier which is the current token. Should be called only
            when tokenType() is IDENTIFIER
            '''
            if "identifier" == self.tokenType():
                return self.current_token.get_mth_str()
            else:
                return None

        def intVal(self):
           '''
            API function
            Returns the integer values of the current token. Should be called only
            when tokenType() is INT_CONST
           '''
           if "integerConstant" == self.tokenType():
               return int(self.current_token.get_mth_str())
           else:
               return None

        def stringVal(self):
           '''
            API function
            Returns the integer values of the current token. Should be called only
            when tokenType() is INT_CONST
           '''
           if "stringConstant" == self.tokenType():
               return self.current_token.get_mth_str()
           else:
               return None

        def input_sanitize(self, input_content):
            '''
            remove all the comments
            '''
            # get rid of the leading and trailing whitespaces
            temp = input_content.strip()
            # remove multi-lines comments. Note that the question mark(?) here indicates a non-greedy match mode
            temp = re.sub("\/\*.*?\*\/", "", temp, flags = re.DOTALL)
            # remove single line comments
            temp = re.sub("\/\/.*", "", temp)
            sanitized_content = temp.strip()
            return [l.strip() for l in sanitized_content.split("\n") if "" != l.strip()]

        def process_single_line(self, line_str):
            '''
            tokenize one line of code
            '''
            obj_mth = None
            list_obj_tok = []
            try_time = 0
            while "" != line_str:
                try_time += 1
                obj_tok = None
                token_type = ""
                # try to match the first token against the line string from left to right
                for regex in lex_ele_regex_list:
                    obj_mth = regex.match(line_str)
                    if None != obj_mth:
                        obj_tok = Token(regex.get_name(), obj_mth.group(0), obj_mth.group(1))
                        list_obj_tok.append(obj_tok)
                        token_type = regex.get_name()
                        break

                if None == obj_tok:
                    print "No regex matched this line: %s at %d try" % (line_str, try_time, )
                    sys.exit(1)
                # remove the matched part from line string
                if "keyword" == token_type:
                    entire_match = obj_tok.get_mth_str()
                else:
                    entire_match = obj_tok.get_raw_str()
                len_mth = len(entire_match)
                start  = line_str.find(entire_match)
                line_str = line_str[start + len_mth:].strip()

            return list_obj_tok

        def tokenize(self):
            for line in self.file_content_list:
                tok_list_single_line = self.process_single_line(line)
                self.tok_list += tok_list_single_line


    class CompilationEngine:
        '''
        Gets input from a JackTokenizer and emits parsed structure into an output file / stream.
        The output is generated by a series of compilexxx() routines, one for every syntactic element
        xxx of the Jack grammar.
        '''
        def __init__(self, jt):
            self.tokenizer = jt
            self.root = None    # the root element of the parse tree

        def CompileNow(self):
            # the first program structure in a file is always class
            # and this function will recursively call other compile functions
            self.CompileClass()
            self.CreateOutputFile()

        def CreateOutputFile(self):
            file_path = self.tokenizer.in_file_path

            # you don't need to worry about special characters like: <>&", they will be dealt by this function below
            xml_content = ET.tostring(self.root)
            # add indents to the output
            pretty_xml_content =  md.parseString(xml_content).toprettyxml(indent = "  ")
            output_file_path = ""
            if os.path.isfile(file_path):
                output_file_path = file_path.split(".")[0] + "fromSyntaxAnalyzer.xml"
            else:
                print "Error: cannot create output file for %s" % (file_path, )

            try:
                fd_ou_file = open(output_file_path, "w")
            except IOError as e:
                print "I/O error: %s" % (str(e), )
                sys.exit(1)
            except Exception as e:
                print "Unexpected error: %s" % (str(e), )
                sys.exit(1)
            finally:
                for line in pretty_xml_content.splitlines():
                    if "<pad/>" in line:
                        continue
                    else:
                        fd_ou_file.write(line + "\n")
                fd_ou_file.close()
                print "%s generated " % (output_file_path, )

        def CompileClass(self):
            '''
            Compile a complete class
            '''
            if None == self.tokenizer.current_token:
                self.tokenizer.advance()

            if "class" == self.tokenizer.keyWord():
                self.root = ET.Element("class")
                item = ET.SubElement(self.root, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )
            else:
                print "Failed to compile class"
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # className
            if self.tokenizer.identifier():
                item = ET.SubElement(self.root, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.identifier(), )
            else:
                print "Failed to match the identifier in %s" % (sys._getframe().f_code.co_name, )

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # symbol '{'
            if '{' == self.tokenizer.symbol():
                item = ET.SubElement(self.root, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
            else:
                print "Failed to match the '{' in %s" % (sys._getframe().f_code.co_name, )
                return False

            # classVarDec*
            while self.CompileClassVarDec(self.root):
                pass

            # subroutineDec*
            while self.CompileSubroutineDec(self.root):
                pass

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # symbol '}'
            if '}' == self.tokenizer.symbol():
                item = ET.SubElement(self.root, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

            else:
                print "Failed to match the '}' in %s, we got a %s" % (sys._getframe().f_code.co_name, self.tokenizer.keyWord(), )
                return False

            return True

        def CompileClassVarDec(self, parent):
            '''
            Compile a static declaration or a field declaration

            Arg:
                parent: the parent node which the tree nodes created in this function are attached to
            '''
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # (static | field)
            if "static" == self.tokenizer.keyWord() or "field" == self.tokenizer.keyWord():
                # since we know this is a classVarDec program structure
                parent = ET.SubElement(parent, "classVarDec")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )

            else:
                self.tokenizer.rollBack()
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # type
            if "int" == self.tokenizer.keyWord() or \
               "char" == self.tokenizer.keyWord() or \
               "boolean" == self.tokenizer.keyWord():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )

            elif self.tokenizer.identifier():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.identifier())

            else:
                print "Failed to match the 'type' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # varName
            if self.tokenizer.identifier():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.identifier(), )

            else:
                print "Failed to match the 'varName' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # (, varName)*
            while "," == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )


                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if self.tokenizer.identifier():
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.identifier(), )

                else:
                    print "Failed to match the 'varName' in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

            if ";" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

                return True
            else:
                print "Failed to match the ';' in %s" % (sys._getframe().f_code.co_name, )
                return False

        def CompileSubroutineDec(self, parent):
            '''
            Compile a complete method, function or constructor
            '''
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # (constructor | function | method)
            if "constructor" == self.tokenizer.keyWord() or \
               "function" == self.tokenizer.keyWord() or \
               "method" == self.tokenizer.keyWord():
                # since we know this is a subroutineDec program structure
                parent = ET.SubElement(parent, "subroutineDec")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )

            else:
                self.tokenizer.rollBack()
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # void or type
            if "void" == self.tokenizer.keyWord():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )

            elif "int" == self.tokenizer.keyWord() or \
               "char" == self.tokenizer.keyWord() or \
               "boolean" == self.tokenizer.keyWord():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )

            elif self.tokenizer.identifier():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.identifier())

            else:
                print "Failed to match the '(void | type)' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # subroutineName
            if self.tokenizer.identifier():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.identifier())

            else:
                print "Failed to match the 'subroutineName' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if "(" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol())

            else:
                print "Failed to match the '(' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if False == self.CompileParameterList(parent):
                print "Failed to match the parameterList in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if ")" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol())

            else:
                print "Failedf to match the ')' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if False == self.CompileSubroutineBody(parent):
                print "Failed to match the subroutineBody in %s" % (sys._getframe().f_code.co_name, )
                return False

            return True

        def CompileParameterList(self, parent):
            '''
            Compile a (possibly empty) parameter list, not including the enclosing"()".
            '''
            parent = ET.SubElement(parent, "parameterList")
            ET.SubElement(parent, "pad")
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # type
            if "int" == self.tokenizer.keyWord() or \
               "char" == self.tokenizer.keyWord() or \
               "boolean" == self.tokenizer.keyWord():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )

            elif self.tokenizer.identifier():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.identifier())

            else:
                # the whole parameterList structure is optional
                self.tokenizer.rollBack()
                return True

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # varName
            if self.tokenizer.identifier():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.identifier(), )

            else:
                print "Failed to match the 'varName' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # (, type varName)*
            while "," == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )


                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

                # type
                if "int" == self.tokenizer.keyWord() or \
                   "char" == self.tokenizer.keyWord() or \
                   "boolean" == self.tokenizer.keyWord():
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.keyWord(), )

                elif self.tokenizer.identifier():
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.identifier())

                else:
                    print "Failed to match 'type' in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

                # varName
                if self.tokenizer.identifier():
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.identifier(), )

                else:
                    print "Failed to match the 'varName' in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

            self.tokenizer.rollBack()
            return True

        def CompileSubroutineBody(self, parent):
            '''
            Compile the body of a subroutine in a class
            '''
            parent = ET.SubElement(parent, "subroutineBody")
            ET.SubElement(parent, "pad")
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # '{'
            if "{" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
            else:
                print "Failed to match the '{' in %s" % (sys._getframe().f_code.co_name, )
                return False

            while self.CompileVarDec(parent):
                pass

            while self.CompileStatements(parent):
                pass

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # '}'
            if "}" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

            else:
                print "Failed to match the '}' in %s" % (sys._getframe().f_code.co_name, )
                return False

            return True

        def CompileVarDec(self, parent):
            '''
            Compile a var declaration
            '''
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # 'var'
            if "var" == self.tokenizer.keyWord():
                # since we know this is a varDec program structure
                parent = ET.SubElement(parent, "varDec")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )

            else:
                self.tokenizer.rollBack()
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # type
            if "int" == self.tokenizer.keyWord() or \
               "char" == self.tokenizer.keyWord() or \
               "boolean" == self.tokenizer.keyWord():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )

            elif self.tokenizer.identifier():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.identifier())

            else:
                print "Failed to match the 'type' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # varName
            if self.tokenizer.identifier():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.identifier(), )

            else:
                print "Failed to match the 'varName' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # (, varName)*
            while "," == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )


                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

                # varName
                if self.tokenizer.identifier():
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.identifier(), )

                else:
                    print "Failed to match the 'varName' in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

            if ";" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

            else:
                print "Failed to match the ';' in %s" % (sys._getframe().f_code.co_name, )
                return False

            return True

        def CompileStatements(self, parent):
            '''
            Compile a sequence of statements, not inclduing the enclosing "{}".
            '''
            parent = ET.SubElement(parent, "statements")
            ET.SubElement(parent, "pad")
            while self.CompileDo(parent) or \
                  self.CompileLet(parent) or \
                  self.CompileWhile(parent) or \
                  self.CompileReturn(parent) or \
                  self.CompileIf(parent):
                pass
            return False

        def CompileDo(self, parent):
            '''
            Compile a do statement
            '''
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # 'do'
            if "do" == self.tokenizer.keyWord():
                # since we know this is a doStatement program structure
                parent = ET.SubElement(parent, "doStatement")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )
            else:
                self.tokenizer.rollBack()
                return False

            # subroutineCall
            if False == self.CompileSubroutineCall(parent):
                print "Failed to match the 'subroutineCall' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if ";" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
            else:
                print "Failed to match the ';' in %s" % (sys._getframe().f_code.co_name, )
                return False

            return True

        def CompileSubroutineCall(self, parent):
            '''
            Note that subroutineCall is not a non-terminal structure
            '''
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # (subroutineName | className)
            if self.tokenizer.identifier():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.identifier(), )
            else:
                print "Failed to match the 'subroutineName' in %s" % (sys._getframe().f_code.co_name, )
                self.tokenizer.rollBack()
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if "." == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )


                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

                # subroutineName
                if self.tokenizer.identifier():
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.identifier(), )

                else:
                    print "Failed to match 'subroutineName' in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

            if "(" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
            else:
                print "Failed to match the '(' in %s" % (sys._getframe().f_code.co_name, )
                return False

            self.CompileExpressionList(parent)

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if ")" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
            else:
                print "Failed to match the ')' in %s" % (sys._getframe().f_code.co_name, )
                return False

            return True

        def CompileLet(self, parent):
            '''
            Compile a let statement
            '''
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # 'let'
            if "let" == self.tokenizer.keyWord():
                # since we know this is a letStatement program structure
                parent = ET.SubElement(parent, "letStatement")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )

            else:
                self.tokenizer.rollBack()
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # varName
            if self.tokenizer.identifier():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.identifier(), )

            else:
                print "Failed to match the 'varName' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # ([expression])?
            if "[" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

                if False == self.CompileExpression(parent):
                    print "Failed to match the [expression] in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if "]" == self.tokenizer.symbol():
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.symbol(), )
                else:
                    print "Failed to match the ']' in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

            if "=" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
            else:
                print "Failed to match the '=' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if False == self.CompileExpression(parent):
                print "Failed to match the expression in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if ";" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
            else:
                print "Failed to match the ';' in %s" % (sys._getframe().f_code.co_name, )
                return False

            return True

        def CompileWhile(self, parent):
            '''
            Compile a while statement
            '''
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # 'while'
            if "while" == self.tokenizer.keyWord():
                # since we know this is a whileStatement program structure
                parent = ET.SubElement(parent, "whileStatement")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )

            else:
                self.tokenizer.rollBack()
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if "(" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

            else:
                print "Failed to match the '(' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if False == self.CompileExpression(parent):
                print "Failed to match the expression in %s" % (sys._getframe().f_code.co_name, )

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if ")" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

            else:
                print "Failed to match the ')' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if "{" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

            else:
                print "Failed to match the '{' in %s" % (sys._getframe().f_code.co_name, )
                return False

            while self.CompileStatements(parent):
                pass

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if "}" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

            else:
                print "Failed to match the '{' in %s" % (sys._getframe().f_code.co_name, )
                return False

            return True

        def CompileReturn(self, parent):
            '''
            Compile a return statement
            '''
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # 'return'
            if "return" == self.tokenizer.keyWord():
                # since we know this is a returnStatement program structure
                parent = ET.SubElement(parent, "returnStatement")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )
            else:
                self.tokenizer.rollBack()
                return False

            self.CompileExpression(parent)

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False
            if ";" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
            else:
                print "Failed to match the ';' in %s" % (sys._getframe().f_code.co_name, )
                return False

            return True

        def CompileIf(self, parent):
            '''
            Compilea if statement, possibly witha trailing else clause
            '''
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # 'if'
            if "if" == self.tokenizer.keyWord():
                # since we know this is a ifStatement program structure
                parent = ET.SubElement(parent, "ifStatement")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )
            else:
                self.tokenizer.rollBack()
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if "(" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
            else:
                print "Failed to match the '(' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if False == self.CompileExpression(parent):
                print "Failed to match the expression in %s" % (sys._getframe().f_code.co_name, )

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if ")" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

            else:
                print "Failed to match the ')' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if "{" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
            else:
                print "Failed to match the '{' in %s" % (sys._getframe().f_code.co_name, )
                return False

            while self.CompileStatements(parent):
                pass

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if "}" == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
            else:
                print "Failed to match the '{' in %s" % (sys._getframe().f_code.co_name, )
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if "else" == self.tokenizer.keyWord():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )


                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if "{" == self.tokenizer.symbol():
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.symbol(), )

                else:
                    print "Failed to match the '{' in %s" % (sys._getframe().f_code.co_name, )
                    return False

                while self.CompileStatements(parent):
                    pass

                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if "}" == self.tokenizer.symbol():
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.symbol(), )
                else:
                    print "Failed to match the '}' in %s" % (sys._getframe().f_code.co_name, )
                    return False
            else:
                self.tokenizer.rollBack()

            return True

        def CompileExpression(self, parent):
            '''
            Compile an expression
            '''
            # take a peek if the next token is a term
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if self.tokenizer.identifier() or \
               "integerConstant" == self.tokenizer.tokenType() or \
               "stringConstant" == self.tokenizer.tokenType() or \
               "-" == self.tokenizer.symbol() or "~" == self.tokenizer.symbol() or \
               "(" == self.tokenizer.symbol() or \
               "true" == self.tokenizer.keyWord() or \
               "false" == self.tokenizer.keyWord() or \
               "null" == self.tokenizer.keyWord() or \
               "this" == self.tokenizer.keyWord():
                parent = ET.SubElement(parent, "expression")

            self.tokenizer.rollBack()

            if False == self.CompileTerm(parent):
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            while ('+' == self.tokenizer.symbol() or \
                   '-' == self.tokenizer.symbol() or \
                   '*' == self.tokenizer.symbol() or \
                   '/' == self.tokenizer.symbol() or \
                   '&' == self.tokenizer.symbol() or \
                   '|' == self.tokenizer.symbol() or \
                   '<' == self.tokenizer.symbol() or \
                   '>' == self.tokenizer.symbol() or \
                   '=' == self.tokenizer.symbol()):
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

                if False == self.CompileTerm(parent):
                    print "Failed to match 'term' in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

            self.tokenizer.rollBack()
            return True

        def CompileTerm(self, parent):
            '''
            Compile a term. This routine is faced with a slight diffculty when trying
            to decide between some of the alternative parsing rules.
            '''
            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            if "integerConstant" == self.tokenizer.tokenType():  # integerConstant
                parent = ET.SubElement(parent, "term")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.intVal(), )
            elif "stringConstant" == self.tokenizer.tokenType():  # stringConstant
                parent = ET.SubElement(parent, "term")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.stringVal(), )
            elif "true" == self.tokenizer.keyWord() or \
                 "false" == self.tokenizer.keyWord() or \
                 "null" == self.tokenizer.keyWord() or \
                 "this" == self.tokenizer.keyWord():  # keyWord constant
                parent = ET.SubElement(parent, "term")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.keyWord(), )
            elif self.tokenizer.identifier():  # a variable name or an array element or a subroutineCall
                parent = ET.SubElement(parent, "term")
                # check if it is subroutineCall
                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False
                if "(" == self.tokenizer.symbol() or \
                   "." == self.tokenizer.symbol():
                    # now, it must be a subroutineCall structure
                    self.tokenizer.rollBack()
                    self.tokenizer.rollBack()

                    if False == self.CompileSubroutineCall(parent):
                        print "Failed to match the 'subroutineCall' in %s" % (sys._getframe().f_code.co_name, )
                        return False
                elif "[" == self.tokenizer.symbol():
                    self.tokenizer.rollBack()
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.identifier(), )

                    if None == self.tokenizer.advance():
                        print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                        return False

                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.symbol(), )

                    if False == self.CompileExpression(parent):
                        print "Failed to match the expression in %s" % (sys._getframe().f_code.co_name, )
                        return False

                    if None == self.tokenizer.advance():
                        print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                        return False

                    if "]" == self.tokenizer.symbol():
                        item = ET.SubElement(parent, self.tokenizer.tokenType())
                        item.text = " %s " % (self.tokenizer.symbol(), )
                    else:
                        print "Failed to match the ']' in %s" % (sys._getframe().f_code.co_name, )
                        return False
                else:
                    self.tokenizer.rollBack()
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.identifier(), )

            elif "(" == self.tokenizer.symbol():  # an expression in parentheses
                parent = ET.SubElement(parent, "term")
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

                if False == self.CompileExpression(parent):
                    print "Failed to match the expression in %s" % (sys._getframe().f_code.co_name, )

                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if ")" == self.tokenizer.symbol():
                    item = ET.SubElement(parent, self.tokenizer.tokenType())
                    item.text = " %s " % (self.tokenizer.symbol(), )
                else:
                    print "Failed to match the ) in %s" % (sys._getframe().f_code.co_name, )
                    return False

            elif "-" == self.tokenizer.symbol() or "~" == self.tokenizer.symbol():  # an expression prefixed by unary operators
                parent = ET.SubElement(parent, "term")

                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )
                if False == self.CompileTerm(parent):
                    print "Failed to match 'term' in %s" % (sys._getframe().f_code.co_name, )
                    return False
            else:
                self.tokenizer.rollBack()
                return False

            return True

        def CompileExpressionList(self, parent):
            '''
            Compile a (possibly empty) comma-separated list of expressions
            '''
            parent = ET.SubElement(parent, "expressionList")
            ET.SubElement(parent, "pad")
            if False == self.CompileExpression(parent):
                return False

            if None == self.tokenizer.advance():
                print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                return False

            # (, expression)*
            while "," == self.tokenizer.symbol():
                item = ET.SubElement(parent, self.tokenizer.tokenType())
                item.text = " %s " % (self.tokenizer.symbol(), )

                if False == self.CompileExpression(parent):
                    print "Failed to match the 'expression' in %s" % (sys._getframe().f_code.co_name, )
                    return False

                if None == self.tokenizer.advance():
                    print "Run out of tokens in %s" % (sys._getframe().f_code.co_name, )
                    return False

            self.tokenizer.rollBack()
            return True


    def __init__(self, path):
        self.list_input_files = self.path_pre_process(path)
        self.list_jt = []
        self.list_ce = []

        if 0 == len(self.list_input_files):
            print "Error: no input files"
            sys.exit(1)

        # create tokenizers
        for f in self.list_input_files:
            print "Input file %s found" % (f, )
            jt = self.JackTokenizer(f)
            self.list_jt.append(jt)

        # create compilation engines
        for jt in self.list_jt:
            # avoid emptyfiles
            if jt.tok_len > 0:
                ce = self.CompilationEngine(jt)
                self.list_ce.append(ce)

    def compile(self):
        # call the compile command on all CompilationEngine instances
        for ce in self.list_ce:
            ce.CompileNow()

    def validate_file_path(self, file_path):
        if False == file_path.lower().endswith(".jack"):
            return False
        return True

    def path_pre_process(self, target_path):
        '''
        if the system argument is a path to file, then translate this file to a single xml file
        if the system argument is a foler, then translate all the jack files in that folder to xml files
        '''
        list_files = []
        # Check if the input path is valid
        if False == os.path.exists(target_path):
            print "Input path %s does not exist" % (target_path, )
            return list_files

        if True == os.path.isfile(target_path):
            if True == self.validate_file_path(target_path):
                list_files.append(target_path)
        elif True == os.path.isdir(target_path):
            files = os.listdir(target_path)
            for f in files:
                file_path = target_path + "/" + f
                if True == self.validate_file_path(file_path):
                    list_files.append(file_path)
        else:
            print "Input path is neither a file nor a folder!"

        return list_files


def main():
    # arguments pre-processing
    if len(sys.argv) <= 1:
        print "Please supply the path to the .jack file(s)"
        sys.exit(1)

    INPUT_PATH = os.path.normpath(sys.argv[1])

    ja = JackAnalyzer(INPUT_PATH)
    ja.compile()

if "__main__" == __name__:
    main()
