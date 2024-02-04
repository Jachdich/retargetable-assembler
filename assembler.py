import math

def pad(bin_str, l=8):
    return "".join(["0" for i in range(l - len(bin_str))]) + bin_str

def isNumber(txt):
    return txt.isdigit() or txt.startswith("0x") or txt.startswith("0b")

class WhatException(Exception): pass

def toNumber(txt):
    if txt.isdigit(): return int(txt)
    if txt.startswith("0x"): return int(txt[2:], 16)
    if txt.startswith("0b"): return int(txt[2:], 2)
    raise WhatException("huh")

def getNumber(txt):
    if txt.isdigit():
        return int(txt)
    if txt.startswith("0x"):
        return int(txt[2:], 16)
    if txt.startswith("0b"):
        return int(txt[2:], 2)
    raise ValueError("Error converting to int")

def isValidVarName(name):
    try:
        int(name)
    except:
        try:
            int(name, 16)
        except:
            return True
        #probably refactor this later its shit
    return False

class Assembler:
    def __init__(self, code, arch):
        self.code = self.clean(code)
        self.regsets = arch.REGSETS
        self.conditions = arch.CONDITIONS
        self.opcodes = arch.OPCODES
        
    def getRegBits(self, regtype):
        return math.ceil(math.log2(len(self.regsets[regtype])))
        
    def clean(self, code):
        code = "".join(code.split("\t"))
        code = code.split("\n")
        out = ""
        for line in code:
            ln = ""
            #strip comments
            for char in line:
                if char == ";":
                    break
                ln += char
            #strip empty lines
            if not ln.strip(" ") == "":
                out += " ".join(ln.split(" ")) + "\n"
        #replace comma + space with just comma
        return out.strip().replace(", ", ",")

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
        if isNumber(text):
            p.append("*")
            canBeLabel = False
            
        if text in self.conditions:
            p.append("condition")
            canBeLabel = False
        if canBeLabel:
            p.append("*") #it's probably a label, could cause issues later
        return p
    
    def doReg(self, args, arg_pos, regtype):
        curr_item = ""
        if not regtype in self.whatis(args[arg_pos]):
            if True in [regtype in self.whatis(arg) for arg in args]:
                print("Is this actually used??!")
                #use it
                reg_pos = -1
                for index, arg in enumerate(args):
                    if regtype in self.whatis(arg):
                        reg_pos = index
                        break
                if reg_pos == -1:
                    raise SyntaxError("Expected argument type {} but got type {} ({}) instead.".format(regtype, self.whatis(args[arg_pos]), args[arg_pos]))
                curr_item += self.regsets[regtype]["values"][args[reg_pos]]
            else:
                raise SyntaxError("Expected argument type {} but got type {} ({}) instead.".format(regtype, self.whatis(args[arg_pos]), args[arg_pos]))
        else:
            curr_item += self.regsets[regtype][args[arg_pos]]
            arg_pos += 1
        return arg_pos, curr_item

    def doImmediate(self, args, arg_pos):
        if not "*" in self.whatis(args[arg_pos]):
            raise SyntaxError("Expected argument type {} but got type {} ({}) instead, at line {}".format("*", self.whatis(args[arg_pos]), args[arg_pos], ""))

        if isNumber(args[arg_pos]):
            return arg_pos + 1, bin(self.getNumber(args[arg_pos]))[2:]
        return arg_pos + 1, args[arg_pos]

    def getTemplate(self, opcode, args):
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
                    arg_type = arg.split(".")[0] # ignore the index
                    if not arg_type in types:
                        print(f"Arg {arg=} is not in {types=}")
                        add = False
                        break
                if add:
                    possible_templates.append(template)
        if len(possible_templates) > 1:
            raise Exception("Error: line matched multiple templates, this may be intentional however it is likely a bug in the processor definition.")
        if len(possible_templates) == 0:
            return None
        return possible_templates[0]
    
    def assemble(self):
        labels = {}
        interCode = [] 
        for line in self.code.split("\n"):
            # if self.isNumber(line):
            #     interCode.append(self.getNumber(line))
            #     continue
            
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
                if not self.isValidVarName(opcode):
                    raise SyntaxError("Labels cannot start with a number")
                labels[opcode[:-1]] = len(interCode)
                continue
            
            template = self.getTemplate(opcode, args)
            if template == None:
                raise SyntaxError("Invalid syntax: " + line)

            resolved_args = {}
            for supplied_arg, expected_arg in zip(args, template[1]):
                expected_arg_type = expected_arg.split(".")[0]
                if expected_arg_type == "*":
                    if isNumber(supplied_arg):
                        resolved_args[expected_arg] = toNumber(supplied_arg)
                    else:
                        raise SyntaxError(f"Expected immediate value, found '{supplied_arg}' instead")

                elif expected_arg_type in self.regsets:
                    resolved_args[expected_arg] = self.regsets[expected_arg_type][supplied_arg]

            for word_template in self.opcodes[template]:
                curr_word = ""
                for arg in word_template:
                    if arg.isdigit():
                        curr_word += arg
                        continue
                    # special case: it's an immediate, so look up only one *, because the number of *s differs from the LHS template to the RHS template
                    override_bits = None
                    if all([c == "*" for c in arg.split(".")[0]]):
                        override_bits = len(arg.split(".")[0])
                        arg = "*" + ("." + arg.split(".")[1] if "." in arg else "")

                    resolved_value = resolved_args[arg]
                    if override_bits:
                        resolved_value = pad(bin(resolved_value)[2:], override_bits)

                    curr_word += resolved_value
                interCode.append(curr_word)
            # arg_pos = 0
            # curr_item = ""
            # for byte_template in template:
            #     for arg in byte_template:
            #         if "." in arg:
            #             arg, index = arg.split(".")
            #         else:
            #             index = 0

            #         if arg.isdigit():
            #             curr_item += arg

            #         elif arg in self.regsets:
            #             arg_pos, tmp = self.doReg(args, arg_pos, arg)
            #             curr_item += tmp

            #         elif arg.count("*") == len(arg):
            #             print("curr_item", curr_item)
            #             arg_pos, tmp = self.doImmediate(args, arg_pos)
            #             if curr_item.isdigit():
            #                 interCode.append(int(curr_item, 2))
            #             else:
            #                 interCode.append(curr_item)
            #             curr_item = tmp

            #         elif arg == "condition":
            #             curr_item += self.conditions[args[arg_pos]]
            #             arg_pos += 1
            #         else:
            #             print(f"arg not recognised: {arg}")

            # if curr_item.isdigit():
            #     interCode.append(int(curr_item, 2))
            # else:
            #     interCode.append(curr_item)
            
        # out = []
        # for item in interCode:
        #     if labels.get(item, None) != None:
        #         out.append(labels[item])
        #     else:
        #         if type(item) != type(int()):
        #             raise NameError("Label '" + item + "' was not defined")
        #         out.append(item)
        # return out
        return interCode

if __name__ == "__main__":
    import definition_craftercpu as definition
    code = """
    add a, b
    ld a, 15
    lol 5, 2
    """
    a = Assembler(code, definition)
    data = a.assemble()
    # print("\n".join([pad(bin(n)[2:], 8) for n in data]))
    print(data)
