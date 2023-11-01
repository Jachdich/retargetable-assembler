; takes two numbers in a, b
; returns one number in a
; modifies a, b, c
ld a, 0x2
ld b, 3
call multiply
halt

multiply:
    push a
    ld c, b
    multiply_loop:
        ld b, (sp)
        add a, b
        ld b, c
        dec b
        j nz, multiply_loop
    pop b
    ret