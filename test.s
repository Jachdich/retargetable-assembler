        ld a, 3
        ld b, 6
        ld h, 0
loop:   
        add h, a
        sub b, 1
        jz done
        jmp loop
done: