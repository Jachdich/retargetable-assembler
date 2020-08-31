import math

class Assembler:
    def __init__(self, code, arch):
        self.code = self.clean(code)
        self.regsets = arch.REGSETS
        self.conditions = arch.CONDITIONS
        self.opcodes = arch.OPCODES
        
    def pad(self, bin_str, l=8):
        return "".join(["0" for i in range(l - len(bin_str))]) + bin_str

    def isNumber(self, txt):
        return txt.isdigit() or txt.startswith("0x") or txt.startswith("0b")
    
    def getNumber(self, txt):
        if txt.isdigit():
            return int(txt)
        if txt.startswith("0x"):
            return int(txt[2:], 16)
        if txt.startswith("0b"):
            return int(txt[2:], 2)
        raise ValueError("Error converting to int")

    def isValidVarName(self, name):
        try:
            int(name)
        except:
            try:
                int(name, 16)
            except:
                return True
            #probably refactor this later its shit
        return False

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
        if self.isNumber(text):
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
                    raise SyntaxError("Expected argument type {} but got type {} ({}) instead, at line {}".format(regType, self.whatis(args[arg_pos]), args[arg_pos], line))
                curr_item += self.pad(bin(self.regsets[regtype][args[reg_pos]])[2:], l=self.getRegBits(regtype))
            else:
                raise SyntaxError("Expected argument type {} but got type {} ({}) instead, at line {}".format(regType, self.whatis(args[arg_pos]), args[arg_pos], line))
        else:
            curr_item += self.pad(bin(self.regsets[regtype][args[arg_pos]])[2:], l=self.getRegBits(regtype))
            arg_pos += 1
        return arg_pos, curr_item

    def doImmediate(self, args, arg_pos):
        if not "*" == self.whatis(args[arg_pos]):
            raise SyntaxError("Expected argument type {} but got type {} ({}) instead, at line {}".format(x, self.whatis(args[arg_pos]), args[arg_pos], line))

        if self.isNumber(args[arg_pos]):
            return arg_pos + 1, bin(self.getNumber(args[arg_pos]))[2:]
        return arg_pos + 1, args[arg_pos]

    def getTemplate(self, opcode, args):
        types_list = []
        possible_templates = []
        for a in args:
           types_list.append(self.whatis(a))
        for template in self.opcodes:
            if template[0] == opcode:
                t_args = template[1]
                if len(t_args) != len(types_list):
                    continue
                add = True
                for types, arg in zip(types_list, t_args):
                    if not arg in types:
                        add = False
                        break
                if add:
                    possible_templates.append(template)
        if len(possible_templates) > 1:
            raise Exception("Error: line matched multiple templates, this may be intentional however it is likely a bug in the processor definition.")
        if len(possible_templates) == 0:
            return None
        return self.opcodes[possible_templates[0]]
    
    def assemble(self):
        labels = {}
        interCode = [] 
        for line in self.code.split("\n"):
            if self.isNumber(line):
                interCode.append(self.getNumber(line))
                continue
            
            if line.strip() == "":
                continue
            
            if " " in line:
                args   = line.split(" ")[1].split(",")
                opcode = line.split(" ")[0]
            else:
                args = []
                opcode = line

            if opcode.endswith(":"):
                if not self.isValidVarName(opcode):
                    raise SyntaxError("Labels cannot be of the form 0xSomething or start with 0-9")
                labels[opcode[:-1]] = len(interCode)
                continue
            
            template = self.getTemplate(opcode, args)
            if template == None:
                raise SyntaxError("Invalid syntax - " + line)
            
            arg_pos = 0
            for byte_template in template:
                curr_item = ""
                for x in byte_template:
                    if x.isdigit():
                        curr_item += x
                        continue

                    elif x in self.regsets:
                        arg_pos, tmp = self.doReg(args, arg_pos, x)
                        curr_item += tmp

                    elif x == "*":
                        arg_pos, tmp = self.doImmediate(args, arg_pos)
                        curr_item += tmp

                    elif x == "condition":
                        curr_item += self.conditions[args[arg_pos]]
                        arg_pos += 1

                if curr_item.isdigit():
                    interCode.append(int(curr_item, 2))
                else:
                    interCode.append(curr_item)
            
        out = []
        for item in interCode:
            if labels.get(item, None) != None:
                out.append(labels[item])
            else:
                if type(item) != type(int()):
                    raise NameError("Label '" + item + "' was not defined")
                out.append(item)
        return out
