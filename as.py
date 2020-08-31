regsets = {
    "gpr": {"a": "00", "b": "01"},
    "addr": {"a": "00"}}

templates = {
    ("push", ("gpr",)) : (("000001", "gpr"),),
    ("ld",   ("[addr]", "gpr")) : (("0001", "gpr", "addr"),),
    ("ld",   ("gpr", "gpr"))   : (("10001", "addr", "gpr"),),
}

def whatis(thing):
    p = []
    for regtype in regsets:
        if thing in regsets[regtype]:
            p.append(regtype)

    if thing.isdigit():
        p.append("*")

    if thing.startswith("[") and thing.endswith("]"):
        p.extend(["[" + a + "]" for a in whatis(thing[1:-1])])

    return p

def getTemplate(opcode, args):
    types_list = []
    possible_templates = []
    for a in args:
       types_list.append(whatis(a))
    for template in templates:
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
    return possible_templates[0]


print(getTemplate("ld", ["a", "a"]))
