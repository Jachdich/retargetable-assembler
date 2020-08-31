#import definition
import definition_stackvm as definition
import assembler

code = """push 0
push 1
add
out
halt"""

def pad(bin_str, l=8):
    return "0" * (l - len(bin_str)) + bin_str

asm = assembler.Assembler(code, definition)
data = asm.assemble()
dl = len(data)
len0 = (dl >> 24) & 0xFF
len1 = (dl >> 16) & 0xFF
len2 = (dl >> 8) & 0xFF
len3 = (dl >> 0) & 0xFF

lendata = chr(len0).encode("utf-8") + \
          chr(len1).encode("utf-8") + \
          chr(len2).encode("utf-8") + \
          chr(len3).encode("utf-8")
          
with open("test.vm", "wb") as f:
    f.write(lendata + b"".join(chr(x).encode("utf-8") for x in data))
#print("\n".join([pad(bin(x)[2:]) for x in asm.assemble()]))
"""
GPRs: a, b, c, d
SPRs: pc, sp

;one operand
00 prefix

00000000 nop
000001xx add
000010xx sub
000011xx ld *->r
000100xx ld [a]->r
000101xx ld r->[a]
000110xx push xx
000111xx pop xx
001000cc jp cc(ondition), *
001001rr jp r

;two operands
01 prefix

0100xxyy ld r->r
0101ccrr jp cc, r

;no operands
10 prefix

10000000 jp *

;wtf is this
11 prefix

nothing here yet


(second arg is always a)
add a
add b
add c
add d

sub a
sub b
sub c
sub d

jp *
jp z *
jp c *
jp nz *
jp nc *

ld a->a
ld a->b
ld a->c
ld a->d

ld b->a
ld b->b
ld b->c
ld b->d

ld c->a
ld c->b
ld c->c
ld c->d

ld d->a
ld d->b
ld d->c
ld d->d

ld *->a ; ld 0x55 -> a
ld *->b
ld *->c
ld *->d

ld [a]->a
ld [a]->b
ld [a]->c
ld [a]->d

ld a->[a] ;useless
ld b->[a]
ld c->[a]
ld d->[a]

push a
push b
push c
push d

pop a
pop b
pop c
pop d

push sp ; dunno about these ones
push pc
pop sp
pop pc

call * ; dunno
ret
"""
