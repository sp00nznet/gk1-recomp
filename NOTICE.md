# Notice

The MIT license in [LICENSE](LICENSE) covers what is ours in this repository:
the lift driver (`run_lift.py`), the host window (`src/runtime/main.c`), the
build and setup scripts, the tools and the documentation. It does not cover
the game.

*Gabriel Knight: Sins of the Fathers* is © 1993 Sierra On-Line, and is not
ours to license. Its interpreter, drivers, resources, speech and movies are not
in this repository and are excluded by `.gitignore`.

- You need your own copy of the game to use any of this. Setup copies your CD
  (or an image or folder copy of it) into `game/`; the pipeline reads it from
  there.
- Lifted code is a derivative work of the binary it came from. Anything the
  pipeline writes into `work/`, `analysis/` or `src/recomp/gen*/` carries
  whatever license the original carries, not this one. The MIT grant stops at
  our own work.

## Where the code comes from

| Path | From | License |
|---|---|---|
| `run_lift.py`, `build.cmd`, `Setup.cmd`, `tools/setup.ps1`, `src/runtime/main.c` | our [Wacky Wheels recomp](https://github.com/sp00nznet/wackywheels-recomp), itself from the Theme Park recomp | MIT (ours) |
| the DOS/4GW host and the LE lifter (not vendored; built from a checkout beside this one) | [pcrecomp](https://github.com/sp00nznet/pcrecomp), branch `pcrecomp-gk1` | MIT (ours) |

There is no third-party code in this repository. The interpreter is lifted
from the game's own `SIERRA.EXE`, not reimplemented: nothing here is taken from
an SCI implementation such as ScummVM (GPL), and the repository holds no SCI
opcode, kernel or resource-format tables.
