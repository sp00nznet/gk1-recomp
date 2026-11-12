# Testing: headless runs and scripted input

The mouse plays it: the left button uses the current verb, the right button
moves to the next one (walk, look, operate, ask, talk, take, ...).

```
build\gk1.exe                                                 # in a window
build\gk1.exe --headless --seconds 20 --shot 15 title.bmp
rem PLAY, wait for the opening, five right-clicks to the walk cursor, walk
build\gk1.exe --headless --seconds 228 --keys "17:click@100;163,199:rclick@150;100,200:rclick@150;100,201:rclick@150;100,202:rclick@150;100,203:rclick@150;100,206:click@60;140" --shot 214 walk.bmp
```

| Flag | |
|---|---|
| `--game DIR` | the game folder, seen by the game as `C:\` (default `game`) |
| `--headless` | no window |
| `--seconds S` | quit after S seconds |
| `--shot S FILE` | save the screen at S seconds (up to 16) |
| `--keys "S:what,..."` | at S seconds: a key (`enter`, `space`, `esc`, `up`, ..., `key+S` holds it), or the mouse in 320x200 pixels: `click@X;Y`, `rclick@X;Y`, `move@X;Y` |
| `--log` | log the DOS host's calls |

Times are real time: the opening runs at the game's own pace.


## What a check looks like

There is no conformance harness yet ([ROADMAP.md](../ROADMAP.md)). Until there
is, a change is checked by a headless run to the bookshop and a look at its
screenshot: the second command above ends with Gabriel having walked across the
shop (`docs/screenshots/walk.png` is that shot). Runs are headless, so nothing
takes over a screen.
