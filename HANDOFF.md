# Pebbles — handover

Written for whoever (human or Claude Code) picks this up next. Pebbles was designed in a long back-and-forth with James Morton; this file records what it does, why, and the rules that were settled. **Read it before changing behaviour.** If a change would break one of these rules, ask James first.

## What it is, and who for

A personal day planner for someone with ADHD-style time management needs. The core ideas:

- A **horizontal** day timeline. Time blocks are "pebbles": soft key-like objects you drag, stretch, join and flick away.
- **Transitions** between work are real, visible objects (dotted, 5 minutes per dot), plus a **wrap-up** buffer at the end of each pebble. The gaps between tasks are where days fall apart, so they're designed, not left blank.
- A **countdown panel** that runs the day: what you're in, how long is left, what's next.
- **Channels** (e.g. TARRMACstudio, Jon, Graphic design, Personal) contain **projects**, each with a task list. A pebble books a project; its **session** is the subset of that project's tasks you mean to do in that block.
- **Activities** (Break, Exercise, user-added groups) are a separate kind of pebble with set lengths and a hatch fill, and no transitions by default.

Look and feel: minimal, inspired by seventhgallery.org, jamesmorton.com.au, Teenage Engineering and Nothing. Space Mono throughout, dot-matrix countdown, warm grey page on a dot grid, black screen panel. No hint text in the interface. No green hover highlights (hover = thin outline). Channel swatches are circles; activity swatches are squares showing their hatch. Smooth, interruptible motion (see "Motion").

### Things James explicitly does not want

- **No AI features** in the app.
- **Google Calendar is read-only.** Never write to it.
- No hint/placeholder text explaining the UI; no streaks/gamification; no per-task icons.
- The word "master" is not used; it's "channels".
- No big tick when ticking a task. The big tick only appears when you press **finish**.
- Plain mouse wheel must not scroll the timeline (it scrolls the page). Ctrl+wheel scrolls the timeline sideways, Alt+wheel zooms. There's a thin draggable scroll bar under the timeline instead.

## Files

- `index.html` — the whole app (HTML, CSS, JS in one file, ~2,400 lines). One IIFE.
- `sw.js` — offline worker. `tools/bump.py` updates its version + file list; run it before publishing.
- `manifest.webmanifest`, `icons/` — install metadata. `sounds/*.mp3` — notification sounds (Pixabay, Soundshelf Studio).
- `tests/` — Playwright checks (see bottom).
- The app also ran as a Claude artifact during design. Code paths that use `window.claude` (account sync, Google Calendar via Claude's connector, downloads) are **only active when `window.claude` exists**; `STANDALONE` is true otherwise and those features hide. The test harness mocks `window.claude` so those paths stay tested.

## Data

State object `S` (saved as JSON in `localStorage['pebble-planner-v1']`, mirrored to the backup folder):

```
{ v, savedAt, projects:{id:{id,kind,name,group,tasks:[{id,text,done,doneAt,due,rs}],dflt,lastPomo}},
  pebbles:[{id,pid,gid,date,start,dur,pomo,intent,trans,tlen,session:[taskIds],rep,plan}],
  groups:[{id,name,color}], types:[{id,name,sty,rest,dur}], notes:[{id,date,text,pid,at,origin}],
  templates:[...], repeats:[{id,pid,start,dur,days,from,pomo,trans,made:[dates]}],
  settings:{...}, last:{}, lastG:{}, openCards:[], histMonths:[] }
```

- Times are **minutes from midnight** of `date` (YYYY-MM-DD, local). A day may run to **29:00 (5am next morning)** — `DAYMAX = 1740`.
- `kind` is `'work'` for projects or an activity-group id (`'break'`, `'move'`, or a user group id).
- A pebble with `pid:null` and a `gid` is an **unset** pebble (channel chosen, project not yet).
- `trans`: `true` (default transition), `false` (none), `'on'` (forced on for activity neighbours). `tlen` is the frozen transition length.
- `rs` on a task = how many times it's been sent on from the morning review. `plan` on a pebble = its length when it started (for "usually runs X% over").
- History (completed tasks, cleared notes) is stored per month separately: `localStorage['pebble-planner-v1-h-YYYY-MM']` and `history/hist-YYYY-MM.json`.

### Update safety (do not skip)

- `SCHEMA` (currently 8) is the data version. **Bump it whenever the saved shape changes**, and add a step in `migrate()`. Never remove fields; old saves must upgrade.
- Before migrating, a copy of the old save is kept (`...-pre-v<N>`).
- If a save is from a *newer* version than the code, the app refuses to write (`tooNew`) so an old copy can't clobber new data.
- A daily backup is kept in the browser (last 7) and in the backup folder (last 14).
- Saving is debounced 600 ms but **flushes immediately when the window is hidden or closed**.
- Sync merge (`merge3`) is three-way against the last agreed `base` — used by the Claude-account sync; keep it when phone sync arrives.

## Behaviour rules (settled)

### Adding pebbles
- Channel chip click → new pebble after the last one (or now), picker opens to choose/create the project. Activity chip → the group's most recent activity.
- Hover a chip ~0.75 s → its projects (most recently used first) or activities pop out above it; click one to add, or **drag it onto the timeline**. While a pop-out is open, sliding to the next chip switches instantly.
- Drag a chip onto the timeline to place it; an outline shows where it will land.
- **Drag a task** from any project list onto the timeline → pebble for that project with the task in its session.
- Picker accepts quick text: `jon call 45m 4pm` → name + length + start (simple parser, no AI). A preview line shows the parsed time/length.
- New pebbles remember each project's last Pomodoro setting.
- Gaps under 10 minutes close themselves (magnet). No slivers.

### Dragging
- Pebbles follow the pointer 1:1; a dashed outline shows the snapped (5 min) landing spot; the dragged pebble shrinks to ~84% (around the grab point) so the outline is visible. Shrink only applies to moving, not resizing.
- Soft edges: dragging past the day's start or 5am limit rubber-bands back.
- Drag off the timeline (vertically) → remove (undo toast). Fast vertical flick also removes. Drop on a day in the week strip → move to that day.
- **Joined chains**: pebbles that touch, or are linked by a transition, form a chain. Moving or stretching (right edge) a pebble carries everything joined after it. If the chain reaches a later pebble, that pebble is pushed on (and joins). **Alt+drag** moves/stretches just that one pebble.
- Moving a pebble that hangs off a transition stretches/shrinks that transition (5–60 min); pulling it right up removes the transition; beyond 60 min it detaches.
- Left edge resizes that pebble only (end fixed), stopping at its neighbour.
- Box-select: drag on empty timeline (mouse) → rounded marquee; shift-click toggles. Move the selection as a group; Delete removes it; Esc clears.
- The **+** to add a transition appears only when hovering just **above** the joint between touching pebbles.

### Transitions
- Default length set by settings (5 min, or 10 min after pebbles ≥60 min) but **frozen when first created** (`tlen`), so stretching a pebble never changes it.
- Only drawn (and only counted as "transition" in the countdown) when the next pebble follows straight on. Otherwise it's free time.
- Click a transition → −/+/remove pop. The pop stays still so you can tap repeatedly; only joined pebbles after it move.
- Not added between a project and an activity unless forced (`'on'`).

### The countdown panel
- Left: channel/label, pebble name, "then …" line. Right: phase tag (focus / break / **wrap up** in red) spanning the timer width, dot-matrix countdown below it with its bottom on the "then" line. Bottom row: progress dots, then −5+ and **finish**, together exactly as wide as the timer.
- **finish**: pebble ends now; the gap to the next 5-minute mark becomes a transition (at least the usual length); joined pebbles after it move up; big tick shows.
- Free time: offers the most urgent due-but-unbooked task ("book …").
- Window title shows `mm:ss · name`; taskbar badge shows minutes left.
- **pop out** → mini timer (Document Picture-in-Picture, Chrome/Edge desktop): name, countdown, next session task with a tick box, −5+, finish.

### Days and time
- Week strip: weekday + date, hours booked; red hours = planned past day end. Month shown as a small vertical boxed tag on the first day of the week and on the 1st. Home button (right) jumps to today.
- After midnight, if yesterday's pebbles run past 12am, the app stays on yesterday ("· late") until they end or 5am, then rolls to the new day.
- Morning review box: session tasks not ticked in the last week → today / done / later. "moved on N times" from 2; ↻3 badge on the task from 3.
- Repeating pebbles: drawer → repeat off/weekly/weekdays. Copies appear as you look ahead; a deleted or moved copy never comes back.
- Drawer shows "usually runs X% over / done X% early" after 3+ finished pebbles of a project.

### Drawer
- Opens under the timeline and docks to it (no gap, shared dark line); the selected pebble stretches to the timeline's bottom edge and reads as a tab on the drawer. **No separately positioned connector piece** — an earlier JS-positioned "stem" was janky and was removed on purpose.
- Activities: compact one-line buttons (name + minutes).

### Motion
- Springs/eased transitions, interruptible. FLIP animation for task rows. View switches slide in the tab direction; keyboard switches are instant (frequent actions shouldn't animate). Pressed feedback on everything clickable. Respects reduced-motion.
- Custom dot cursors (black dot, ring on clickables, red dot on pebbles); text cursor in inputs, resize arrows on pebble edges.

## Not done yet (in rough order)

1. **Bundle the font locally** (Space Mono, OFL) instead of Google Fonts, so first launch offline looks right.
2. ~~Google Calendar~~ done another way: the standalone app reads calendars from a Google Apps Script the user deploys in their own account (settings → calendars → copy script / copy appsscript.json, deploy as web app, paste the link). The manifest limits the script to `calendar.readonly`. Requests carry a random key stored in `settings.calKey`; `settings.calUrl` holds the link. One request per date range covers every calendar. James's calendars: james@jamesmorton.com.au (main), jamesmorton@tarrmacstudio.com and jamesofthemonth@gmail.com (both shared to the main account).
3. **Phone + laptop sync** (keep the three-way merge; needs a backend or a shared file).
4. Optional: Tauri wrapper for a global hotkey, tray icon and true background notifications.

Known gap: the sync merge skips merging while you're typing or mid-drag (that one save is last-write-wins).

## Tests

`tests/harness.py` builds a test copy of `index.html` with a fake clock (`window.__setNow`), a fake account database in localStorage and fake calendar events; `tests/run.py` is the simulated five-week run (Mon studio day, template day, due-task alerts, midnight rollover, copy/clear day, month-later pruning, update safety, phone width). Feature tests: `t45` (chip pop, late nights, edges, chapter marks), `t46` (elastic transitions, drawer, wrap tag), `t47` (stretch chains), `t48` (move chains, transition pop), `t52` (frozen transitions, Alt, wheel, two-device merge), `t56` (drag to book, review, repeats, quick typing, free-time booking), `t57` (fresh start), `t58_standalone` (offline worker, folder backup, export, mini timer), `t59_pip` (mini timer screenshot), `t60_gcal_link` (calendar via Apps Script link, faked). Run the full set before publishing.
