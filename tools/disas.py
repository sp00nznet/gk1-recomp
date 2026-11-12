#!/usr/bin/env python3
"""Disassemble SIERRA.EXE's lifted image: dis.py ADDR [COUNT]  (or dis.py --file F.DRV)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
if sys.argv[1] == '--file':
    code, base, a = open(sys.argv[2], 'rb').read(), 0, int(sys.argv[3], 16) if len(sys.argv) > 3 else 0
else:
    import run_lift
    le = run_lift.LEImage(run_lift.bound_le(open(os.path.join(os.path.dirname(run_lift.__file__), 'game', 'SIERRA.EXE'), 'rb').read()))
    img, base, objs, _ = le.build(run_lift.LOAD_BASE)
    code, a = bytes(img), int(sys.argv[1], 16)
n = int(sys.argv[-1]) if len(sys.argv) > 2 and sys.argv[-1].isdigit() else 40
for i in Cs(CS_ARCH_X86, CS_MODE_32).disasm(code[a - base:], a, count=n):
    print('%08X  %-24s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
