# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `CONTRIBUTING.md`, `CONTRIBUTORS.md`, `docs/building.md`, `docs/testing.md`.
- `setup.sh`, which says there is no Linux or macOS build yet and stops.
- An `installer` workflow for recomp-launcher, run by hand only.

### Changed
- Builds against pcrecomp main; the `pcrecomp-gk1` branch is merged.
- README in the house order (Getting Started, Status, Screenshots,
  Documentation, Contributors, License); the step-by-step build and the
  command line moved to `docs/building.md` and `docs/testing.md`.
- `NOTICE` is now `NOTICE.md`, saying what the MIT license covers and what it
  does not.

### Fixed
- `LICENSE` is plain MIT again: another project's notice had been appended to
  it.

## [0.1.0] - 2026-11-12

### Added
- `run_lift.py`: `SIERRA.EXE` (the DOS CD's SCI interpreter, Watcom, DOS/4GW)
  lifted with pcrecomp's LE front end, plus the silent sound and DAC drivers
  it loads at run time (`MIDNONE.DRV`, `DACNONE.DRV`), the function in its
  data object, and the kernel callbacks named only by instruction operands.
  3,772 functions, 0 errors.
- Host (`src/runtime/main.c`, from Wacky Wheels) on pcrecomp's `dos32`
  (branch `pcrecomp-gk1`): window with mouse, `--headless`, `--shot`, and
  `--keys` with mouse clicks (`click@X;Y`, `rclick@X;Y`, `move@X;Y`).
- It runs the title, the day 1 opening and the bookshop, where Gabriel walks
  and looks where you click.
- `Setup.cmd` (`tools/setup.ps1`), `launcher/launcher.json`, a netlab recipe
  (`gk1-recomp`), `tools/disas.py`, `docs/bringup.md`.
