# Building

`Setup.cmd` runs exactly these steps; this is the same thing by hand.

## Step by step

Prerequisites: Windows 10/11, **Python 3.10+** (`py -3 --version`), **git**,
**Visual Studio 2022** (or its Build Tools) with *Desktop development with
C++* and *C++ Clang tools for Windows* (clang-cl), and the pcrecomp toolkit
cloned **beside** this repository as `pcrecomp`, on `pcrecomp-gk1`:

```
some-folder\
  pcrecomp\       <- git clone -b pcrecomp-gk1 https://github.com/sp00nznet/pcrecomp
  gk1\            <- this repository
```

1. Python packages:
   ```
   py -3 -m pip install --user pefile capstone
   ```
2. Copy the CD into `game\` (the movies and the Windows files are not needed):
   ```
   robocopy E:\ game /E /XD AVI SVGA WINPATCH
   ```
3. Replace the CD's `RESOURCE.CFG` (the installer's) with one for VGA and no
   sound, `game\RESOURCE.CFG`:
   ```
   videoDrv = VGA.DRV
   soundDrv = MIDNONE.DRV
   audioDrv = DACNONE.DRV
   joyDrv = NO
   patchDir = PATCHES
   ```
4. Lift (the first run also builds the function catalog and takes a minute):
   ```
   py -3 run_lift.py
   ```
   Expected: 3,772 functions, 0 errors, into `src\recomp\gen\`.
5. Build (clang-cl, CMake and Ninja, through the VS x64 environment):
   ```
   build.cmd
   ```
6. Run: `build\gk1.exe`.

The usual trip-ups: `python` opening the Microsoft Store (that is Windows' alias
placeholder; use `py -3`, or turn the alias off in *Settings > Apps > Advanced
app settings > App execution aliases*); a freshly installed Python not being on
`PATH` until you open a new window; and Visual Studio without the Clang tools
(`build.cmd` then fails to find `clang-cl`).

## Notes

`PCRECOMP` (Python, and `build.cmd` passes it to CMake as
`-DPCRECOMP=`) points at a toolkit checkout other than `..\pcrecomp`; the
lifter and the runtime must come from the same tree. On
[netlab](https://github.com/sp00nznet/recomp-netlab) the recipe is
`gk1-recomp`: `netlab build gk1-recomp`. `tools/disas.py ADDR [N]`
disassembles the relocated image with Capstone.

