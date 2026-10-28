# Pebbles

A day planner built around a horizontal timeline of draggable "pebbles" (time blocks), with transitions between them, a countdown for the pebble you're in, and task lists per project. Installable web app, works offline, keeps its data on your computer.

## Run it locally

Any static web server works. From this folder:

```
python -m http.server 8000
```

then open http://localhost:8000 in Chrome or Edge. (Opening `index.html` straight from disk won't install or work offline; it needs to be served.)

## Publish on GitHub Pages

1. Push this folder to a GitHub repository.
2. Repository → Settings → Pages → Build and deployment → Source: "Deploy from a branch", Branch: `main`, folder `/ (root)`.
3. The app appears at `https://<your-username>.github.io/<repo-name>/`.

Before each publish, bump the version so installed copies pick up the new files:

```
python tools/bump.py
```

## Install on Windows

1. Open the GitHub Pages address in Chrome or Edge.
2. Click the install icon at the right of the address bar (or menu → "Install Pebbles").
3. Pin it to the taskbar if you like. It opens in its own window and works offline.

### Open it with a key or a mouse button

- Start menu → find Pebbles → right-click → Open file location → right-click the shortcut → Properties → **Shortcut key** → press e.g. `Ctrl+Alt+P`.
- In your mouse software (e.g. Logitech Options+), map a button to that key combination.

### Turn on "start when I sign in" (optional)

Chrome: open `chrome://apps`, right-click Pebbles → "Start app when you sign in". Edge: `edge://apps` → the app's details.

## Your data

- Saved in the browser as you go, and (once you choose one) in a **backup folder** on your computer: Settings → data → backup folder → choose folder.
  - `pebbles-plan.json` – always the latest plan
  - `backups/pebbles-YYYY-MM-DD.json` – one per day, last 14 kept
  - `history/hist-YYYY-MM.json` – completed tasks and cleared notes
- If browser storage is ever cleared, Pebbles reloads from the folder (after you reconnect it with one click).
- Settings → data → export / import also works with any backup file.
- Updates never touch your data: the plan carries a version number and old saves are upgraded step by step, with a copy kept first. See HANDOFF.md → "Data".

## Mini timer

On the countdown panel, **pop out** opens a small window that stays on top of other programs: current pebble, countdown, the next session task with a tick box, −5+, finish. Chrome/Edge on desktop only; needs a click to open each time.

The window title (and the taskbar label, if Windows shows labels) reads like `23:41 · Call with Jon`, and the taskbar icon shows minutes left as a badge.

## Tests

Headless browser checks (Python + Playwright):

```
pip install playwright pillow
python -m playwright install chromium
python tests/run.py            # a simulated five-week run through every feature (56 checks)
python tests/t58_standalone.py # the installed-app specifics: offline worker, folder backup, export, mini timer
```

The other `tests/t*.py` files each check one area (see HANDOFF.md).
