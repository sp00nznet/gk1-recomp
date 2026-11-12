# Roadmap

## Next
- Merge pcrecomp's `pcrecomp-gk1` (drivers loaded at run time, far calls,
  `pushf`/`popf`) into `main`, and point Setup and the launcher at `main`.
- Play on through day 1: leave the bookshop, Jackson Square, the map; save and
  restore.
- A conformance harness (REPO_RULES section 9): boot, title, opening,
  bookshop, a walk, as milestones with a pass count and a baseline, in the
  shape of Theme Park's `tools/conformance.py`. Without the game it prints a
  SKIP line for netlab's `QA_SKIP`.
- Headless recording: `--headless --record out.mp4` (frames piped to ffmpeg).

## Then
- Linux and macOS: a `setup.sh` that really builds (clang-cl/lld cross
  build, or Wine), once the host is tested there.
- Sound: lift `SBPRO.DRV`/`DACBLAST.DRV` (they lift the same way) against an
  emulated Sound Blaster in dos32, or replace the drivers at their API with a
  host mixer; speech from `AUD\RESOURCE.AUD`.
- Guest-time pacing for `--keys` (a virtual clock), so test runs need not wait
  out the opening in real time.

## Out of scope
- The Windows version (`SIERRAW.EXE`) and its movies.
- Shipping any game file or generated source.
