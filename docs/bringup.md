# Bring-up notes

What Gabriel Knight's DOS CD needed, in the order it turned up. Each item says
where the fix lives: in this repository (`run_lift.py`, `src/runtime/main.c`),
or in pcrecomp (now on `main`), when another
game would hit it too.

## The copy of the game

The archive.org item `gk-1_20220905` holds `Gabriel Knight Sins Of The Fathers
(CD DOS).zip`: a file copy of the CD. At its root are the DOS interpreter
(`SIERRA.EXE`), the resources (`RESOURCE.000`, `.MAP`, `.SFX`, `.ALT`), the
drivers (`*.DRV`), `PATCHES\` and `AUD\` (speech). `SIERRAW.EXE`, `AVI\`,
`SVGA\` and `WINPATCH\` are the Windows version's and are not used. `GK1\` is
a copy of the installer's target folder. No copy protection: the interpreter
only reads its files. Nothing was run to get it: the zip unpacks with 7-Zip.

## Which base

`SIERRA.EXE` is a 32-bit Watcom C/C++ program bound to DOS/4GW (the LE image
starts at 0x25214 in the file), so it is pcrecomp's `dos32` host and LE front
end, as Theme Park and Wacky Wheels are, not the 16-bit DOS path Wing
Commander takes. The lift driver, build and host window come from Wacky
Wheels. Mode X is not needed: SCI draws in mode 13h.

## The interpreter

- **`pushf` / `popf` (16-bit).** The interpreter saves and restores the
  interrupt flag with `pushf; pop ax; cli ... push ax; popf`. The lifter only
  knew the 32-bit forms, so `pushf` did nothing and `pop ax` took the return
  address: the first run died with `Stack underflow: ..\cursord.cpp(497)`.
  Fixed in pcrecomp's lifter: both widths, and under `dos=True` the flags word
  carries IF from the host (`recomp_get_if` / `recomp_set_if`), so `popf`
  turns interrupts back on.
- **A function in a data object.** Object 2 (0x470000, 177 bytes, no execute
  flag) is code: it builds a code or data descriptor over a buffer with DPMI
  0000h/000Bh/000Ch, which is how the interpreter makes `cs` and `fs` for a
  driver. `run_lift.py` lifts it as `sub_00470000`.
- **Callbacks named only by an operand.** SCI's kernel registers handlers
  with `mov [x], offset fn`, a fixup inside an instruction. pcrecomp's
  `code_pointers` keeps only fixups in tables, so 60-odd handlers were never
  lifted (`ICALL: unresolved VA 0x00449780`). `run_lift.py` also seeds every
  such operand target that starts right after a `ret` or padding.

## Drivers loaded at run time

The sound drivers (`MIDNONE.DRV` and the rest) and the DAC drivers
(`DACNONE.DRV` and the rest) are 32-bit code the interpreter reads from a
file into its heap and calls: a DAC driver with a near call to the buffer, a
sound driver with a far call through a code selector whose base is the buffer
(`call fword ptr [...]`), running with `fs` on its own data and reading its
dispatch table through `cs:`.

They are lifted ahead of time. `run_lift.py` lifts each driver in `DRIVERS`
at a base of its own (0x60000000, 0x60100000), from its entry points (offset
0, the sound drivers' `cs:` table at 0x28) and embeds its bytes. In pcrecomp's
`dos32` (`dos32_config.modules`), a DOS read that fills a buffer with exactly
one module's bytes records where it was loaded; a call into that buffer, or to
a small offset while `cs` is that buffer, goes to the lifted copy. The lifter's
far call takes the selector's base (`CS_BASE`), and `cs:` overrides use it.

Only the silent drivers are lifted, so the game runs with no music, effects or
speech. The real ones (`SBPRO.DRV`, `DACBLAST.DRV`, ...) would lift the same
way, but they drive Sound Blaster ports that `dos32` does not emulate.

## RESOURCE.CFG

The CD's `RESOURCE.CFG` is the installer's. `tools/setup.ps1` writes the one
INSTALL would for VGA and no sound:

```
videoDrv = VGA.DRV
soundDrv = MIDNONE.DRV
audioDrv = DACNONE.DRV
joyDrv = NO
patchDir = PATCHES
```

`VGA.DRV` is a 33-byte stub: the interpreter's VGA code is built in.

## Input

The game is mouse-driven. The host feeds the window's mouse to `dos32`'s
int 33h driver, scaled to 320x200, and `--keys` takes `click@X;Y`,
`rclick@X;Y` (right button: the next cursor) and `move@X;Y` for test runs.
