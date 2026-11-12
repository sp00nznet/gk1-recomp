#!/usr/bin/env python3
"""Gabriel Knight: Sins of the Fathers (DOS CD, Sierra 1993) lift driver.

SIERRA.EXE, Sierra's SCI interpreter, is a Watcom C/C++ 32-bit program bound to DOS/4GW: an MZ stub, the extender, and
an LE image. pcrecomp's LE front end (tools/le/le_parse.py) lays the objects
out at LOAD_BASE with every fixup applied, and the rest is the 32-bit pipeline:
disasm32 finds the functions, lift32 lifts them with dos=True (int, port I/O,
cli/sti and segment loads call the DOS host, runtime/dos32), and generate.py
writes the chunks. This is Wacky Wheels' driver (from Theme Park's), plus the
sound drivers the interpreter loads from files and one function in a data
object.

Output goes to src/recomp/gen/, which is gitignored: it is derived from the
game binary and never distributed. image_data.c there carries the relocated
image the host copies into guest memory at start-up.

    py -3 run_lift.py [--exe game/SIERRA.EXE]
"""
import argparse
import bisect
import hashlib
import json
import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PC = os.path.join(os.environ.get('PCRECOMP') or os.path.join(_HERE, '..', 'pcrecomp'), 'tools')
sys.path.insert(0, os.path.join(_PC, 'lift'))
sys.path.insert(0, os.path.join(_PC, 'le'))

from capstone import Cs, CS_ARCH_X86, CS_MODE_32            # noqa: E402
from generate import (LinearInstruction,                     # noqa: E402
                      linear_disassemble_function, lift_function_linear, write_chunk)
from le_parse import LEImage, code_pointers, to_pe          # noqa: E402
from lift32 import Lifter                                   # noqa: E402
from recover import recover_functions                       # noqa: E402

# Where the LE objects go in guest memory: above conventional memory and the
# VGA window, as in Theme Park.
LOAD_BASE = 0x400000

# The SIERRA.EXE this lift knows: the DOS CD's (dated 1996-12-24 on the disc).
SIERRA_SHA1 = '66c8fe86a81ef1d3233c6959bcec543f2e70e7dc'


def head_disassemble_function(md, code, cs, start, end, heads):
    """Decode only at disasm32's instruction heads in [start, end): Watcom
    keeps switch tables in the code object, which a linear sweep would decode."""
    lo, hi = bisect.bisect_left(heads, start), bisect.bisect_left(heads, end)
    insns, leaders = [], {start}
    for h in heads[lo:hi]:
        i = next(md.disasm(code[h - cs:h - cs + 16], h, count=1), None)
        if i is None:
            continue
        li = LinearInstruction(i)
        if insns and insns[-1].end_address != h:
            leaders.add(h)
        insns.append(li)
        if li.is_cond_jump or li.is_uncond_jump:
            t = li.get_branch_target()
            if t and start <= t < end:
                leaders.add(t)
            leaders.add(li.end_address)
    return insns, leaders


def bound_le(data):
    """SIERRA.EXE is DOS/4GW with the program bound in after it: the outer MZ is the
    extender, and the program's own MZ + LE (whose offsets count from that MZ)
    follow its image. Returns the program's file."""
    import struct
    lfa = struct.unpack_from('<I', data, 0x3C)[0]
    if data[lfa:lfa + 2] in (b'LE', b'LX'):
        return data
    at = data.find(b'MZ', 2)
    while at >= 0:
        inner = struct.unpack_from('<I', data, at + 0x3C)[0]
        if data[at + inner:at + inner + 2] in (b'LE', b'LX'):
            print('[*] bound program at 0x%X (LE at 0x%X)' % (at, at + inner))
            return data[at:]
        at = data.find(b'MZ', at + 2)
    sys.exit('run_lift: no LE program in %d bytes' % len(data))


# Drivers SIERRA.EXE loads from files at run time and calls: lifted ahead of
# time, each at a base of its own. pcrecomp's dos32 maps a call into the buffer
# the file was read into (or a cs-relative offset while cs is that buffer) to
# the lifted copy. Only the silent ones: the build runs muted.
DRIVERS = [('MIDNONE.DRV', 0x60000000), ('DACNONE.DRV', 0x60100000)]


def driver_entries(d):
    """A Sierra driver's entry points. Sound drivers (a short jmp) dispatch
    through `mov ebp, cs:[ebp+TABLE]`; DAC drivers start at 0x28."""
    import struct
    if d[:2] == bytes([0xEB, 0x1D]):
        ents, tab = [0, 0x1F], struct.unpack_from('<I', d, 0x28)[0]
        while tab + 4 <= len(d) and struct.unpack_from('<I', d, tab)[0] < len(d):
            ents.append(struct.unpack_from('<I', d, tab)[0])
            tab += 4
        return sorted(set(ents))
    return [0, 0x28]


def lift_drivers(game, md):
    """[(addr, end, code, base)] per driver function, and the module table."""
    fns, mods = [], []
    for name, base in DRIVERS:
        d = open(os.path.join(game, name), 'rb').read()
        for a, e in recover_functions(d, 0, len(d), [], forced=driver_entries(d)):
            fns.append((base + a, base + e, d, base))
        mods.append((name, base, d))
    return fns, mods


def write_image(path, img, base, entry, stack, mods=()):
    with open(path, 'w', newline='\n') as f:
        f.write('/* Gabriel Knight recomp - AUTO-GENERATED from SIERRA.EXE: never distribute */\n'
                '#include <stdint.h>\n'
                'const uint32_t recomp_image_base = 0x%08Xu;\n'
                'const uint32_t recomp_image_size = %du;\n'
                'const uint32_t recomp_image_stack = 0x%08Xu;\n'
                'const uint8_t recomp_image[] = {\n' % (base, len(img), stack))
        for i in range(0, len(img), 32):
            f.write(','.join(str(b) for b in img[i:i + 32]) + ',\n')
        f.write('};\n#include "dos32.h"\n')
        for name, vb, d in mods:
            f.write('static const uint8_t drv_%08X[] = { /* %s */\n' % (vb, name))
            for i in range(0, len(d), 32):
                f.write(','.join(str(b) for b in d[i:i + 32]) + ',\n')
            f.write('};\n')
        f.write('const dos32_module recomp_modules[] = {\n')
        for name, vb, d in mods:
            f.write('    { 0x%08Xu, %du, drv_%08X },\n' % (vb, len(d), vb))
        f.write('    { 0, 0, 0 } };\nconst int recomp_module_count = %d;\n' % len(mods))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exe', default=os.path.join(_HERE, 'game', 'SIERRA.EXE'))
    ap.add_argument('--catalog', default=os.path.join(_HERE, 'analysis', 'd32_funcs.json'))
    ap.add_argument('--out', default=os.path.join(_HERE, 'src', 'recomp', 'gen'))
    ap.add_argument('--split', type=int, default=400)
    args = ap.parse_args()

    data = open(args.exe, 'rb').read()
    sha = hashlib.sha1(data).hexdigest()
    print('[*] %s: SHA-1 %s' % (os.path.basename(args.exe), sha))
    if SIERRA_SHA1 and sha != SIERRA_SHA1:
        sys.exit('run_lift: this is not the SIERRA.EXE this lift knows (%s)' % SIERRA_SHA1)
    le = LEImage(bound_le(data))
    img, lo, objs, relocs = le.build(LOAD_BASE)
    entry, stack = le.entry(objs), le.stack(objs)
    code_obj = next(o for o in objs if o['flags'] & 0x4)
    cs, ce = code_obj['addr'], code_obj['addr'] + code_obj['vsize']
    code = bytes(img[cs - lo:ce - lo])
    seeds = code_pointers(objs, relocs, img, lo)
    print('[*] LE: %d objects, %d fixups, code 0x%08X-0x%08X, entry 0x%08X, %d code pointers'
          % (len(objs), len(relocs), cs, ce, entry, len(seeds)))

    os.makedirs(os.path.dirname(args.catalog), exist_ok=True)
    if not os.path.exists(args.catalog):
        print('[*] no catalog yet: running disasm32')
        work = os.path.join(_HERE, 'work')
        os.makedirs(work, exist_ok=True)
        pe_path, seed_path = os.path.join(work, 'gk_pe.exe'), os.path.join(work, 'gk_seeds.json')
        open(pe_path, 'wb').write(to_pe(img, lo, objs, relocs, entry))
        json.dump(['0x%x' % s for s in seeds], open(seed_path, 'w'))
        subprocess.run([sys.executable, os.path.join(_PC, 'disasm', 'disasm32.py'), pe_path,
                        '--full', '--seed-functions', seed_path, '--output', args.catalog], check=True)
    cat = json.load(open(args.catalog, encoding='utf-8'))
    fns = sorted((f['address'], min(f['end'], ce)) for f in cat['functions'] if cs <= f['address'] < ce)
    heads = sorted({i['address'] for f in cat['functions'] for b in f['blocks'] for i in b['instructions']})
    del cat
    print('[*] disasm32: %d functions, %d instruction heads' % (len(fns), len(heads)))
    starts = {a for a, _ in fns}
    # code_pointers keeps only fixups in tables; SCI's kernel registers its
    # callbacks with `mov [x], offset fn` operands, which it leaves out. Take an
    # operand's target too when it starts right after a ret or padding.
    imms = {r['target'] for r in relocs if r['type'] == 7 and cs <= r['at'] < ce and cs < r['target'] < ce
            and code[r['target'] - cs - 1] in (0xC3, 0x90, 0x00, 0xCB)}
    extra = recover_functions(code, cs, ce, fns, forced=sorted(s for s in set(seeds) | imms if s not in starts))
    md1 = Cs(CS_ARCH_X86, CS_MODE_32)
    interior = set()
    for h in heads:
        i = next(md1.disasm(code[h - cs:h - cs + 16], h, count=1), None)
        if i is not None:
            interior.update(range(h + 1, h + i.size))
    extra = [e for e in extra if e[0] not in interior]
    print('[*] recovered %d more entries' % len(extra))
    fns = sorted(set(fns) | set(extra))
    known = {a for a, _ in fns}

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    call_pop = {a for a in known if 0x58 <= code[a - cs] <= 0x5F}
    lifter = Lifter(lifted=known, dos=True, call_pop=call_pop)
    os.makedirs(args.out, exist_ok=True)
    for fn in os.listdir(args.out):
        if fn.startswith('recomp_') and fn.endswith('.c'):
            os.remove(os.path.join(args.out, fn))
    entries, chunk, idx, errors, t0 = [], [], 0, 0, time.time()
    seen = set()
    for addr, end in fns:
        if addr in seen:
            continue
        seen.add(addr)
        name = 'sub_%08X' % addr
        try:
            insns, leaders = head_disassemble_function(md, code, cs, addr, end, heads)
            if not insns:
                insns, leaders = linear_disassemble_function(md, code, cs, addr, end)
            body = (lift_function_linear(lifter, name, insns, leaders, addr) if insns
                    else 'void %s(void) { }\n' % name)
            chunk.append((body, addr, name))
        except Exception as e:                              # noqa: BLE001 -- counted
            chunk.append(('/* ERROR %s: %s */\nvoid %s(void) {}\n' % (name, e, name), addr, name))
            errors += 1
        entries.append((addr, name))
        if len(chunk) >= args.split:
            write_chunk(args.out, idx, chunk)
            idx += 1
            chunk = []
    dfns, mods = lift_drivers(os.path.dirname(args.exe), md)
    dl = Lifter(lifted={a for a, _, _, _ in dfns}, dos=True)
    for addr, end, d, base in dfns:
        name = 'sub_%08X' % addr
        insns, leaders = linear_disassemble_function(md, d, base, addr, end)
        chunk.append((lift_function_linear(dl, name, insns, leaders, addr), addr, name))
        entries.append((addr, name))
    print('[*] drivers: %d functions in %d' % (len(dfns), len(mods)))
    # Object 2 is one function in a data object (no exec flag): it builds a
    # code or data descriptor over a buffer, for calling a loaded driver.
    o2 = next(o for o in objs if o['addr'] == 0x470000)
    insns, leaders = linear_disassemble_function(md, bytes(img[o2['addr'] - lo:o2['addr'] - lo + o2['vsize']]),
                                                 o2['addr'], o2['addr'], o2['addr'] + o2['vsize'])
    chunk.append((lift_function_linear(lifter, 'sub_00470000', insns, leaders, 0x470000), 0x470000, 'sub_00470000'))
    entries.append((0x470000, 'sub_00470000'))
    if chunk:
        write_chunk(args.out, idx, chunk)
        idx += 1

    with open(os.path.join(args.out, 'recomp_funcs.h'), 'w', newline='\n') as f:
        f.write('/* Gabriel Knight recomp - AUTO-GENERATED */\n#pragma once\n#include <stdint.h>\n\n')
        for a, n in entries:
            f.write('void %s(void);  /* 0x%08X */\n' % (n, a))
    with open(os.path.join(args.out, 'recomp_dispatch.c'), 'w', newline='\n') as f:
        f.write('/* Gabriel Knight recomp - AUTO-GENERATED */\n'
                '#include "recomp_types.h"\n#include "recomp_funcs.h"\n\n'
                'const recomp_dispatch_entry_t recomp_dispatch_table[] = {\n')
        for a, n in sorted(entries):
            f.write('    { 0x%08Xu, %s },\n' % (a, n))
        f.write('};\nconst uint32_t recomp_dispatch_count = %d;\n' % len(entries))
        f.write('const uint32_t recomp_entry_va = 0x%08Xu;\n' % entry)
    write_image(os.path.join(args.out, 'image_data.c'), img, lo, entry, stack, mods)

    lines = sum(sum(1 for _ in open(os.path.join(args.out, fn), encoding='utf-8', errors='replace'))
                for fn in os.listdir(args.out) if fn.startswith('recomp_'))
    print('=' * 60)
    print('  functions %d   errors %d   files %d   lines %s   %.1fs'
          % (len(entries), errors, idx, format(lines, ','), time.time() - t0))
    print('=' * 60)


if __name__ == '__main__':
    main()
