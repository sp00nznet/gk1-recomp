# Contributing

Issues and pull requests are welcome.

## The one rule

**Nothing from the game goes in the repository.** No game files (`SIERRA.EXE`,
the `.DRV` drivers, `RESOURCE.*`, `AUD\`), no lifted C (`src/recomp/gen/`), no
function catalog (`analysis/`), nothing from `work/`, no disassembly listings,
nothing generated from `SIERRA.EXE`. The tool ships; its output is made on each
person's machine from their own copy. `.gitignore` covers the usual paths;
check `git status` before you commit anyway. Screenshots of the game running
are fine.

## Where your code comes from

Contributions must be your own work or MIT-compatible. In particular, nothing
from ScummVM, FreeSCI or any other SCI implementation (GPL): this project
lifts Sierra's own interpreter rather than reimplementing it, and code or
tables read out of those projects would make it theirs. If something
unusually polished came from somewhere, say where.

## Before a pull request

1. Lift and build from clean: `py -3 run_lift.py` (expected: 3,772 functions,
   0 errors), then `build.cmd`.
2. Run the headless check in [docs/testing.md](docs/testing.md) and look at the
   screenshot: the title, the opening and the walk across the bookshop must
   still work. A new behavior comes with a `--keys` run that shows it.

## Where a fix belongs

- A bug in the lifter, the LE front end or `dos32` belongs in
  [pcrecomp](https://github.com/sp00nznet/pcrecomp), not here.
- Something only this interpreter does (a seed, a lifted data-object function,
  a driver list) goes in `run_lift.py`, with a comment saying what and why.
- A wall you got past goes in `docs/bringup.md`: what it looked like, what it
  was, what moved it.
