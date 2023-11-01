
const MEMSIZE: u8 = 32;

struct CPU {
    a: u8,
    b: u8,
    c: u8,
    d: u8,
    pc: u8,
    sp: u8,
    t: u8,
    mem: [u8; MEMSIZE as usize],
}

impl CPU {
    fn new(prog: &[u8]) -> Self {
        let mut mem = [0 as u8; MEMSIZE as usize];
        for i in 0..prog.len() {
            mem[i] = prog[i];
        }
        CPU {
            a: 0,
            b: 0,
            c: 0,
            d: 0,
            pc: 0,
            sp: MEMSIZE - 1,
            t: 0,
            mem,
        }
    }
    
    fn clock_high(&mut self) {
        
    }

    fn clock_low(&mut self) {
        self.t += 1;
        if self.t > 3 { self.t = 0; }
    }

    fn print(&self) {
        println!("A: {}  B: {}  C: {}  D: {}    PC: {}  SP: {}   Tstate: {}  mem: {:?}", self.a, self.b, self.c, self.d, self.pc, self.sp, self.t, self.mem);
    }
}

fn main() {
    let mut cpu = CPU::new(&[0x54, 0x02, 0x55, 0x03, 0x46, 0x07, 0x58, 0x40, 0x19, 0x51, 0x21, 0x16, 0x4d, 0x45, 0x09, 0x45, 0x48]);
    for _ in 0..64 {
        cpu.clock_high();
        print!("After clock high: ");
        cpu.print();
        cpu.clock_low();
        print!("After clock low:  ");
        cpu.print();
    }
}