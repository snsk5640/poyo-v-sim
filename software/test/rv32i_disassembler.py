#!/usr/bin/env python3
"""
RV32I .hex disassembler

- Input: text file where each line is a 32-bit instruction in hex (e.g., 0080006f) with or without 0x prefix
- Output: CSV with columns: pc, word, asm

Usage:
  python rv32i_hex_disassembler.py input.hex -o out.csv --start-addr 0x0

Notes:
- Supports RV32I base ISA (LUI, AUIPC, JAL, JALR, BRANCH, LOAD, STORE, OP-IMM, OP, FENCE, SYSTEM incl. ECALL/EBREAK, simple CSR ops)
- Register names are in the RISC-V ABI form (zero, ra, sp, ...)
"""
import argparse
import csv
from typing import Tuple

ABI_NAMES = [
    "zero","ra","sp","gp","tp","t0","t1","t2",
    "s0","s1","a0","a1","a2","a3","a4","a5",
    "a6","a7","s2","s3","s4","s5","s6","s7",
    "s8","s9","s10","s11","t3","t4","t5","t6",
]

MASK32 = 0xFFFF_FFFF

def sext(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value & ((1 << bits) - 1)) - (1 << bits) if (value & sign) else (value & ((1 << bits) - 1))

def get_bits(x, hi, lo):
    return (x >> lo) & ((1 << (hi - lo + 1)) - 1)

# Immediate constructors per RISC-V encodings

def imm_i(instr):
    return sext(get_bits(instr,31,20), 12)

def imm_s(instr):
    imm = (get_bits(instr,31,25) << 5) | get_bits(instr,11,7)
    return sext(imm, 12)

def imm_b(instr):
    # [12|10:5|4:1|11] << 1
    imm = ((get_bits(instr,31,31) << 12) |
           (get_bits(instr,30,25) << 5)  |
           (get_bits(instr,11,8)  << 1)  |
           (get_bits(instr,7,7)   << 11))
    return sext(imm, 13)

def imm_u(instr):
    return instr & 0xFFFFF000

def imm_j(instr):
    # [20|10:1|11|19:12] << 1
    imm = ((get_bits(instr,31,31) << 20) |
           (get_bits(instr,30,21) << 1)  |
           (get_bits(instr,20,20) << 11) |
           (get_bits(instr,19,12) << 12))
    return sext(imm, 21)

# Format helpers

def reg(idx):
    return ABI_NAMES[idx & 31]


def fmt_mem(offset, base):
    return f"{offset}({base})"


def decode(instr: int, pc: int) -> str:
    opcode = instr & 0x7F
    rd = (instr >> 7) & 0x1F
    funct3 = (instr >> 12) & 0x7
    rs1 = (instr >> 15) & 0x1F
    rs2 = (instr >> 20) & 0x1F
    funct7 = (instr >> 25) & 0x7F

    if opcode == 0b0110111:  # LUI
        return f"lui {reg(rd)},{imm_u(instr)}"
    if opcode == 0b0010111:  # AUIPC
        return f"auipc {reg(rd)},{imm_u(instr)}"
    if opcode == 0b1101111:  # JAL
        target = (pc + imm_j(instr)) & MASK32
        return f"jal {reg(rd)},0x{target:08x}"
    if opcode == 0b1100111:  # JALR
        if funct3 == 0b000:
            off = imm_i(instr)
            target = (pc + off) & MASK32  # compute for display; real target is (rs1+off)&~1
            return f"jalr {reg(rd)},{fmt_mem(off, reg(rs1))}"
    if opcode == 0b1100011:  # BRANCH
        off = imm_b(instr)
        target = (pc + off) & MASK32
        m = {
            0b000: "beq",
            0b001: "bne",
            0b100: "blt",
            0b101: "bge",
            0b110: "bltu",
            0b111: "bgeu",
        }.get(funct3)
        if m:
            return f"{m} {reg(rs1)},{reg(rs2)},0x{target:08x}"
    if opcode == 0b0000011:  # LOAD
        off = imm_i(instr)
        m = {
            0b000: "lb",
            0b001: "lh",
            0b010: "lw",
            0b100: "lbu",
            0b101: "lhu",
        }.get(funct3)
        if m:
            return f"{m} {reg(rd)},{fmt_mem(off, reg(rs1))}"
    if opcode == 0b0100011:  # STORE
        off = imm_s(instr)
        m = {
            0b000: "sb",
            0b001: "sh",
            0b010: "sw",
        }.get(funct3)
        if m:
            return f"{m} {reg(rs2)},{fmt_mem(off, reg(rs1))}"
    if opcode == 0b0010011:  # OP-IMM
        imm = imm_i(instr)
        if funct3 == 0b001:  # SLLI
            shamt = (instr >> 20) & 0x1F
            return f"slli {reg(rd)},{reg(rs1)},{shamt}"
        if funct3 == 0b101:
            shamt = (instr >> 20) & 0x1F
            if funct7 == 0b0000000:
                return f"srli {reg(rd)},{reg(rs1)},{shamt}"
            if funct7 == 0b0100000:
                return f"srai {reg(rd)},{reg(rs1)},{shamt}"
        m = {
            0b000: "addi",
            0b010: "slti",
            0b011: "sltiu",
            0b100: "xori",
            0b110: "ori",
            0b111: "andi",
        }.get(funct3)
        if m:
            return f"{m} {reg(rd)},{reg(rs1)},{imm}"
    if opcode == 0b0110011:  # OP
        key = (funct7, funct3)
        m = {
            (0b0000000,0b000): "add",
            (0b0100000,0b000): "sub",
            (0b0000000,0b001): "sll",
            (0b0000000,0b010): "slt",
            (0b0000000,0b011): "sltu",
            (0b0000000,0b100): "xor",
            (0b0000000,0b101): "srl",
            (0b0100000,0b101): "sra",
            (0b0000000,0b110): "or",
            (0b0000000,0b111): "and",
        }.get(key)
        if m:
            return f"{m} {reg(rd)},{reg(rs1)},{reg(rs2)}"
    if opcode == 0b0001111:  # FENCE
        if funct3 == 0b000:
            pred = get_bits(instr,27,24)
            succ = get_bits(instr,23,20)
            if rd == 0 and rs1 == 0 and pred == 0 and succ == 0:
                return "fence"
            return f"fence pred={pred},succ={succ}"
    if opcode == 0b1110011:  # SYSTEM
        if funct3 == 0:
            if get_bits(instr,31,7) == 0:
                return "ecall"
            if get_bits(instr,31,7) == 0x001000:
                return "ebreak"
        # CSR (basic pretty-print)
        csr = get_bits(instr,31,20)
        if funct3 in (0b001,0b010,0b011):
            m = {0b001:"csrrw",0b010:"csrrs",0b011:"csrrc"}[funct3]
            return f"{m} {reg(rd)},{csr:#x},{reg(rs1)}"
        if funct3 in (0b101,0b110,0b111):
            zimm = rs1
            m = {0b101:"csrrwi",0b110:"csrrsi",0b111:"csrrci"}[funct3]
            return f"{m} {reg(rd)},{csr:#x},{zimm}"

    # Unknown / unimplemented
    return f".word 0x{instr:08x}"


def parse_hex_line(line: str) -> int:
    s = line.strip().lower()
    if not s:
        raise ValueError("empty line")
    if s.startswith("0x"):
        s = s[2:]
    return int(s, 16) & MASK32


def disassemble_lines(lines, start_addr: int):
    pc = start_addr & MASK32
    for line in lines:
        s = line.strip()
        if not s:
            continue
        instr = parse_hex_line(s)
        asm = decode(instr, pc)
        yield pc, instr, asm
        pc = (pc + 4) & MASK32


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help=".hex file with one 32-bit instruction per line")
    ap.add_argument("-o","--output", help="output CSV path (default: stdout)")
    ap.add_argument("--start-addr", default="0x0", help="starting PC address (default: 0x0)")
    args = ap.parse_args()

    start_addr = int(str(args.start_addr), 0)
    with open(args.input, "r", encoding="utf-8") as f:
        rows = list(disassemble_lines(f, start_addr))

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as fo:
            w = csv.writer(fo)
            w.writerow(["pc","word","asm"])  # headers
            for pc, instr, asm in rows:
                w.writerow([f"0x{pc:08x}", f"0x{instr:08x}", asm])
    else:
        w = csv.writer(sys.stdout)
        w.writerow(["pc","word","asm"])  # headers
        for pc, instr, asm in rows:
            w.writerow([f"0x{pc:08x}", f"0x{instr:08x}", asm])

if __name__ == "__main__":
    main()
