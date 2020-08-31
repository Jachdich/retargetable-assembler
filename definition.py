
"""
ld a, 1
ld b, [a]
"""

REGSETS = {
    "gpr": {
        "a": 0,
        "b": 1,
        "c": 2,
        "d": 3,
    },
    "addr": {
        "a": 0,
    },
    "spr": {
        "pc": 0,
        "sp": 0,
    },
}

CONDITIONS = {
    "z": "00",
    "c": "01",
    "nc": "10",
    "nz": "11",
}

OPCODES = {
    ("add", ("gpr",))           : (("000001", "gpr"),),
    ("sub", ("gpr",))           : (("000010", "gpr"),),
    ("nop", ())                 : (("00000000",),),
    ("ld", ("gpr", "*"))        : (("000011", "gpr"), ("*",)),
    ("jp", ("condition", "*"))  : (("001000", "condition"), ("*",)),
    ("jp", ("*",))              : (("10000000",), ("*",)),
    ("jp", ("gpr",))            : (("001001",   "gpr"),),
    ("jp", ("condition", "gpr")): (("0101",     "condition", "gpr"),),
    ("ld", ("gpr", "[addr]"))   : (("000100", "gpr"),),
    ("ld", ("gpr", "gpr"))      : (("0100", "gpr", "gpr"),),
}