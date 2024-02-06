#!/usr/bin/env python3
import math

def pad(bin_str, l=8, c='0'):
    return c * (l - len(bin_str)) + bin_str

def is_number(txt):
    return txt.isdigit() or txt.startswith("0x") or txt.startswith("0b")

class WhatException(Exception): pass

def to_number(txt):
    if txt.isdigit(): return int(txt)
    if txt.startswith("0x"): return int(txt[2:], 16)
    if txt.startswith("0b"): return int(txt[2:], 2)
    raise WhatException("huh")

def get_nymber(txt):
    if txt.isdigit():
        return int(txt)
    if txt.startswith("0x"):
        return int(txt[2:], 16)
    if txt.startswith("0b"):
        return int(txt[2:], 2)
    raise ValueError("Error converting to int")

def is_valid_var_name(name):
    try:
        int(name)
    except:
        try:
            int(name, 16)
        except:
            return True
        #probably refactor this later its shit
    return False

class Literal:
    """Value of these bits are known"""
    def __init__(self, value, num_bits=None):
        self.value = value
        self.num_bits = num_bits

    def with_bits(self, bits):
        return Literal(self.value, bits)

class Label:
    """Value of these bits depends on the position of a label"""
    def __init__(self, value, num_bits=None):
        self.value = value
        self.num_bits = num_bits

    def with_bits(self, bits):
        return Label(self.value, bits)


def without_index(arg):
    """Remove the .xyz from things like 'reg.0' and '[reg.0]' without getting rid of the []"""
    deref = False
    if arg.startswith("[") and arg.endswith("]"):
        arg = arg[1:-1]
        deref = True
    arg = arg.split(".")[0]
    if deref:
        arg = "[" + arg + "]"
    return arg

def without_deref(arg):
    if arg.startswith("[") and arg.endswith("]"):
        return arg[1:-1]
    return arg

class Assembler:
    def __init__(self, code, arch):
        self.code = self.clean(code)
        self.regsets = arch.REGSETS
        self.opcodes = arch.OPCODES
        
    def get_reg_bits(self, regtype):
        return math.ceil(math.log2(len(self.regsets[regtype])))
        
    def clean(self, code):
        code = "".join(code.split("\t"))
        code = code.split("\n")
        out = []
        for line_number, line in enumerate(code):
            ln = ""
            #strip comments
            for char in line:
                if char == ";":
                    break
                ln += char
            #strip empty lines
            if not ln.strip(" ") == "":
                ln = " ".join(ln.split(" "))
                out.append((line_number, ln.replace(", ", ",")))
        #replace comma + space with just comma
        return out

    def whatis(self, text):
        p = []
        canBeLabel = True
        if text.startswith("[") and text.endswith("]"):
            p.extend(["[" + a + "]" for a in self.whatis(text[1:-1])])
            canBeLabel = False

        for regtype in self.regsets:
            if text in self.regsets[regtype]:
                p.append(regtype)
                canBeLabel = False
        if is_number(text):
            p.append("*")
            canBeLabel = False
            
        if canBeLabel:
            p.append("*") #it's probably a label, could cause issues later
        return p

    def get_template(self, opcode, args):
        types_list = []
        possible_templates = []
        for a in args:
           types_list.append(self.whatis(a))
        for template in self.opcodes:
            if template[0] == opcode:
                t_args = template[1] if len(template) > 1 else []
                if len(t_args) != len(types_list):
                    continue
                add = True
                for types, arg in zip(types_list, t_args):
                    arg_type = without_index(arg)
                    if not arg_type in types:
                        add = False
                        break
                if add:
                    possible_templates.append(template)
        if len(possible_templates) > 1:
            raise Exception("Error: line matched multiple templates, this may be intentional however it is likely a bug in the processor definition.")
        if len(possible_templates) == 0:
            return None
        return possible_templates[0]

    def format_error(self, text, line_index, char_position):
        LINE_NUMBER_LENGTH = len(str(self.code[line_index][0])) # number of chars we need to show the full line number
        CONTEXT_LENGTH = 3 # number of lines to show as context to the error
        if line_index < CONTEXT_LENGTH: # if there's not enough to show the desired context length
            CONTEXT_LENGTH = 1 # use the minimum number of lines (just show current line)
        context = self.code[line_index - CONTEXT_LENGTH + 1:line_index + 1]
        last_ln = context[0][0]
        for ln, line in context:
            while last_ln < ln - 2: # some line was skipped (assume it was empty)
                last_ln += 1
                print(f"{pad(str(last_ln + 2), LINE_NUMBER_LENGTH, ' ')}│")
            print(f"{pad(str(ln + 1), LINE_NUMBER_LENGTH, ' ')}│{line}")

        prefix_spaces = 0
        while context[-1][1][prefix_spaces].isspace():
            prefix_spaces += 1
        print(" " * (LINE_NUMBER_LENGTH + 1 + prefix_spaces) + "^" * len(context[-1][1].strip()))
        print(text)
        exit(1)
    
    def assemble(self):
        labels = {}
        interCode = [] 
        for line_index, line_info in enumerate(self.code):
            line_number, line = line_info

            if line.strip() == "":
                continue

            while line.startswith(" "): line = line[1:]
            
            if " " in line:
                args   = line.split(" ")[1].split(",")
                opcode = line.split(" ")[0]
            else:
                args = []
                opcode = line

            if opcode.endswith(":"):
                if not is_valid_var_name(opcode):
                    self.format_error("Syntax Error: Labels cannot start with a number", line_index, 0)
                labels[opcode[:-1]] = len(interCode)
                continue

            if opcode.split(" ")[0] in [".d8", ".d16", ".d32"]:
                if len(args) != 1:
                    self.format_error("Syntax Error: Expected exactly one number after " + opcode.split(" ")[0], line_index, 0)

                bits = int(opcode.split(" ")[0][2:]) # just extract the suffix from the .d
                number = args[0].strip()
                if not is_number(number):
                    self.format_error(f"Syntax Error: Expected a number, got '{number}' instead", line_index, 0)
                interCode.append([Literal(to_number(number), bits)])
                continue
            
            template = self.get_template(opcode, args)
            if template == None:
                self.format_error("Syntax Error: Invalid syntax", line_index, 0)

            resolved_args = {}
            for supplied_arg, expected_arg in zip(args, template[1]):
                # remove the [], if it exists, because it's not relevant rn
                expected_arg = without_deref(expected_arg)
                expected_arg_type = without_index(expected_arg)
                supplied_arg = without_deref(supplied_arg)
                if expected_arg_type == "*":
                    if is_number(supplied_arg):
                        resolved_args[expected_arg] = Literal(to_number(supplied_arg))
                    elif "*" in self.whatis(supplied_arg): # probably a label?
                        resolved_args[expected_arg] = Label(supplied_arg)
                    else:
                        self.format_error(f"Syntax Error: Expected immediate value, found '{supplied_arg}' instead", line_index, 0)

                elif expected_arg_type in self.regsets:
                    if not supplied_arg in self.regsets[expected_arg_type]:
                        self.format_error(f"Syntax Error: Expected a register of {self.regsets[expected_arg_type]}, got '{supplied_arg}' instead.", line_index, 0)
                    resolved_args[expected_arg] = Literal(self.regsets[expected_arg_type][supplied_arg])

            for word_template in self.opcodes[template]:
                curr_word = []
                for arg in word_template:
                    if arg.isdigit():
                        curr_word.append(Literal(arg, None))
                        continue
                    # special case: it's an immediate, so look up only one *, because the number of *s differs from the LHS template to the RHS template
                    override_bits = None
                    if all([c == "*" for c in arg.split(".")[0]]): # check that all chars of the name are *, except for the index (after the .)
                        override_bits = len(arg.split(".")[0])
                        arg = "*" + ("." + arg.split(".")[1] if "." in arg else "")

                    resolved_value = resolved_args[arg]
                    curr_word.append(resolved_value.with_bits(override_bits))
                    
                interCode.append(curr_word)

        out = []
        for item in interCode:
            word = ""
            for section in item:
                if type(section) == Literal:
                    if type(section.value) == str:
                        word += section.value
                    else:
                        word += pad(bin(section.value)[2:], section.num_bits)
                else:
                    if labels.get(section.value, None) != None:
                        word += pad(bin(labels[section.value])[2:], section.num_bits)
                    else:
                        self.format_error("Name Error: Label '" + section.value + "' was not defined", 0, 0)
            out.append(word)
        return out

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="CrafterCPU Assembler")
    parser.add_argument("asmfile", help="The input file to assemble")
    parser.add_argument("-o", "--outfile", default="-", help="The file to write output to. Defaults to stdout")
    parser.add_argument("-b", "--bin", action="store_true", help="Whether to output in human-readable ascii (strings of 1s and 0s, default) or as a binary file.")
    args = parser.parse_args()
    
    REGSETS = {
        "reg": {
            "a": "000",
            "b": "001",
            "c": "010",
            "h": "011",
            "l": "100",
            "pc": "101",
            "sp": "110",
            "bp": "111",
        },
    }

    OPCODES = {
        ("add",  ("reg.0", "reg.1"))   : (("00000", "reg.0", "reg.1", "00000"),),
        ("sub",  ("reg.0", "reg.1"))   : (("00001", "reg.0", "reg.1", "00000"),),
        ("shr",  ("reg",))             : (("00010", "reg",   "000",   "00000"),),
        ("cmp",  ("reg.0", "reg.1"))   : (("00011", "reg.0", "reg.1", "00000"),),
        ("adc",  ("reg.0", "reg.1"))   : (("00100", "reg.0", "reg.1", "00000"),),
        ("sbc",  ("reg.0", "reg.1"))   : (("00101", "reg.0", "reg.1", "00000"),),
        ("nand", ("reg.0", "reg.1"))   : (("00110", "reg.0", "reg.1", "00000"),),
        ("xor",  ("reg.0", "reg.1"))   : (("00111", "reg.0", "reg.1", "00000"),),

        ("add",  ("reg", "*"))         : (("01000", "reg", "********"),),
        ("sub",  ("reg", "*"))         : (("01001", "reg", "********"),),

        ("cmp",  ("reg", "*"))         : (("01011", "reg", "********"),),
        ("adc",  ("reg", "*"))         : (("01100", "reg", "********"),),
        ("sbc",  ("reg", "*"))         : (("01101", "reg", "********"),),
        ("nand", ("reg", "*"))         : (("01110", "reg", "********"),),
        ("xor",  ("reg", "*"))         : (("01111", "reg", "********"),),

        ("jmp",  ("*",))               : (("10000", "***********"),),
        ("jz",   ("*",))               : (("10001", "***********"),),
        ("jn",   ("*",))               : (("10010", "***********"),),
        ("jp",   ("*",))               : (("10011", "***********"),),
        ("ld",   ("reg", "*"))         : (("10100", "reg", "********"),),
        ("ld",   ("reg.0", "reg.1"))   : (("10101", "reg.0", "reg.1", "00000"),),
        ("ld",   ("reg.0", "[reg.1]")) : (("10110", "reg.0", "reg.1", "00000"),),
        ("ld",   ("[reg.0]", "reg.1")) : (("10111", "reg.0", "reg.1", "00000"),),

        ("push", ("reg",))             : (("11010", "reg", "00000000"),),
        ("pop",  ("reg",))             : (("11011", "reg", "00000000"),),
        ("scf", ())                    : (("1110000000000000"),),
        ("rcf", ())                    : (("1110000000000000"),),
        ("call", ("*",))               : (("11110", "***********"),),
        ("nop", ())                    : (("1111111111111111")),
    }

    class Definition:
        def __init__(self, REGSETS, OPCODES):
            self.REGSETS = REGSETS
            self.OPCODES = OPCODES

    with open(args.asmfile, "r") as f:
        code = f.read()

    a = Assembler(code, Definition(REGSETS, OPCODES))
    data = a.assemble()
    if args.bin:
        out = ""# "".join(data) TODO
    else:
        out = "\n".join(data).encode("utf-8")
    if args.outfile == "-":
        print(out.decode("utf-8"))
    else:
        with open(args.outfile, "wb") as f:
            f.write(out)

