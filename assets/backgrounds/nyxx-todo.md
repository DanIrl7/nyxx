# nyxx — Comprehensive Todo List

---

## Phase 1 — Foundation & Setup
- [ ] Install `windows-curses` (`pip install windows-curses`)
- [ ] Install `pyfiglet` (`pip install pyfiglet`)
- [ ] Create `~/.nyxx/` config directory
- [ ] Create empty `~/.nyxx/jumps.json` (default `[]`)
- [ ] Create empty `~/.nyxx/memos.json` (default `[]`)
- [ ] Set up shell wrapper in `.bashrc` / `.zshrc`
- [ ] Build subcommand router in `nyxx.py` (parse `sys.argv` to dispatch `cd`, `jump`, `memo`)

---

## Phase 2 — Background System
- [ ] Refactor star generation to be density-based (% of total cells, not fixed count)
- [ ] Add more star character variety (`✦` `✧` `·` `*` `◇`)
- [ ] Add curses color pairs for multiple star brightness levels
- [ ] Add city silhouette at bottom using block characters (`█` `▄`)
- [ ] Add horizon glow effect above city using dim color gradient
- [ ] Handle terminal resize event (`curses.KEY_RESIZE`) — regenerate background to new dimensions
- [ ] Add ASCII fallback mode (replace Unicode/emoji chars for unsupported terminals)

---

## Phase 3 — Home Screen (`nyxx`)
- [ ] Generate ASCII block letter logo using `pyfiglet` (`font="banner3-D"` or similar)
- [ ] Draw centered panel box using box-drawing characters (`┌─┐│└─┘`)
- [ ] Calculate terminal center (`h//2`, `w//2`) and draw panel relative to it
- [ ] Apply color gradient to logo lines (darker top rows → brighter bottom rows)
- [ ] Display 3 module entries (`cd`, `jump`, `memo`) with emoji + description
- [ ] Highlight selected module with left accent border (`▸` indicator)
- [ ] Add keybinding footer row inside panel
- [ ] Handle `↑` `↓` to move selection
- [ ] Handle `Enter` to launch selected module
- [ ] Handle `q` / `Esc` to exit

---

## Phase 4 — CD Module (`nyxx cd`)
- [ ] List all files and directories in current working directory
- [ ] Build extension-to-emoji icon map (`.py` → 🐍, `.md` → 📝, etc.)
- [ ] Show `🔼 ..` as first entry (go up)
- [ ] Show `📁` for directories, `🔗` for symlinks, appropriate icon for files
- [ ] Display current path in panel header
- [ ] Implement scroll offset so list stays in view as selection moves
- [ ] Show target path preview line above footer
- [ ] Handle `→` / `Enter` / `l` — navigate into selected directory
- [ ] Handle `←` / `Backspace` / `h` — go up one level
- [ ] Handle `Space` — confirm jump (print `CD:/path` and exit for shell wrapper)
- [ ] Handle `.` — toggle hidden files/directories
- [ ] Handle `q` / `Esc` — quit without changing directory
- [ ] Fix emoji column-width issue (place emojis only on even columns)

---

## Phase 5 — Jump Module (`nyxx jump`)
- [ ] Load saved locations from `~/.nyxx/jumps.json`
- [ ] Display each entry: name (bold), description, path (dimmer, indented)
- [ ] Show empty state message if no locations saved yet
- [ ] Handle `↑` `↓` to move selection
- [ ] Handle `Enter` — print `CD:/saved/path` and exit for shell wrapper
- [ ] Handle `d` — delete selected entry with confirmation prompt (`y/n`)
- [ ] Handle `q` / `Esc` — quit without action
- [ ] Handle `nyxx jump <name>` (no UI) — look up name, print `CD:/path`, exit
- [ ] Handle `nyxx jump add` — save current directory, prompt for name + description, write to `jumps.json`
- [ ] Show count of saved locations in panel header

---

## Phase 6 — Memo Module (`nyxx memo`)
- [ ] Load saved commands from `~/.nyxx/memos.json`
- [ ] Display each entry: name (bold), description, command (italic/dimmer, prefixed with `$`)
- [ ] Show empty state message if no commands saved yet
- [ ] Handle `↑` `↓` to move selection
- [ ] Handle `Enter` — print `EXEC:command` and exit for shell wrapper
- [ ] Handle `d` — delete selected entry with confirmation prompt (`y/n`)
- [ ] Handle `q` / `Esc` — quit without action
- [ ] Handle `nyxx memo <name>` (no UI) — look up name, print `EXEC:command`, exit
- [ ] Handle `nyxx memo add` — prompt for name, description, command in sequence, write to `memos.json`
- [ ] Show count of saved commands in panel header

---

## Phase 7 — Shell Wrapper
- [ ] Detect user shell (bash vs zsh) in install script
- [ ] Redirect curses stdout to `/dev/tty` so `$()` capture only gets the final output
- [ ] Handle `CD:` prefix in wrapper — run `cd /path`
- [ ] Handle `EXEC:` prefix in wrapper — run `eval "command"`
- [ ] Handle empty output (user quit) — do nothing
- [ ] Test wrapper with `nyxx cd`, `nyxx jump <name>`, `nyxx memo <name>`

---

## Phase 8 — Visual Polish
- [ ] Consistent color scheme across all modules (same panel border, highlight, footer colors)
- [ ] Smooth re-draw — use `stdscr.erase()` not `stdscr.clear()` to reduce flicker
- [ ] Panel always perfectly centered regardless of terminal size
- [ ] Confirmation prompt (for delete) styled consistently with the rest of the UI
- [ ] Truncate long filenames / paths gracefully with `…` if they exceed panel width
- [ ] Add scrollbar indicator on right side of list for long directories

---

## Phase 9 — Theme System
- [ ] Define a theme data structure (background chars, colors, panel colors)
- [ ] Implement starry night theme (current default)
- [ ] Implement at least 2 more themes (e.g. vaporwave, matrix)
- [ ] Save chosen theme to `~/.nyxx/config.json`
- [ ] Allow theme selection from home screen or via `nyxx theme` command

---

## Phase 10 — Install Script (`install.sh`)
- [ ] Create `~/.nyxx/` directory if it doesn't exist
- [ ] Download `nyxx.py` from GitHub raw URL
- [ ] Create empty `jumps.json` and `memos.json`
- [ ] Detect shell and append wrapper function to correct config file
- [ ] Check Python 3 is installed, warn if not
- [ ] Check / install `windows-curses` on Windows
- [ ] Print success message with next steps

---

## Phase 11 — GitHub & README
- [ ] Write `README.md` with one-liner install command
- [ ] Add screenshot or GIF of all four screens (home, cd, jump, memo)
- [ ] Add keybinding table
- [ ] Add manual install instructions as fallback
- [ ] Add "how to add a theme" section
- [ ] Set up GitHub repo with `nyxx.py`, `install.sh`, `README.md`
- [ ] Add a LICENSE file (MIT recommended)
