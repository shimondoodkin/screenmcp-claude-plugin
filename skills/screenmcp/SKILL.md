---
name: screenmcp
description: Use when the user wants to see or control THIS computer's desktop — take a screenshot, click/drag/scroll, type text, press keys/hotkeys, manage windows, or read/set the clipboard. Drives the local machine directly over the bundled screenmcp-local MCP server.
---

# ScreenMCP — Local Desktop Control

This plugin bundles a standalone stdio MCP server (`screenmcp-local`) that controls
**the computer Claude Code is running on** — Windows, macOS, or Linux. No worker,
relay, account, or network. Use it whenever the task means looking at or operating
the real desktop GUI.

## Setup (automatic)

The server's Python dependencies install themselves on first launch via
`bootstrap.py` (`mss`, `pynput`, `Pillow`, `pyperclip`, and `pygetwindow` on
Windows). You don't normally do anything.

If the `mcp__screenmcp-local__*` tools aren't available, the server failed to
start — usually no Python on PATH, or a sandboxed install. Check its stderr, or
install the deps manually:

```
pip install mss pynput Pillow pyperclip pygetwindow
```

Optional extras (only if the user needs them):

```
pip install opencv-python   # camera / list_cameras
pip install simpleaudio     # play_audio
```

## Core loop: look, then act

1. **`screenshot`** to see the screen before acting. Re-screenshot after actions
   that change the UI.
2. Act with **`click`**, **`double_click`**, **`right_click`**, **`drag`**,
   **`scroll`**, **`type`**, **`press_key`**, **`hotkey`** (e.g. `[ctrl, c]`).
3. Verify by screenshotting again.

When unsure where a click will land, use **`screenshot`** with the `dots` argument
to paint estimated click positions and confirm before committing.

## Coordinate space (important)

Screenshots default to **1456×819**. All click/drag/scroll/move coordinates are in
that same space and auto-scale to the real screen — so read positions off the
screenshot you just took and pass them straight through. Override per call with
`max_width`/`max_height` (`0` = native pixels).

### Model-aware sizing

Coordinate-bearing tools accept an optional `model` arg: `claude` | `gemini` |
`chatgpt`. With no explicit `max_width`/`max_height`, it sizes the screenshot **and**
the click space to that model's vision limits so the image and the clicks share one
space. Since you are Claude, pass `model: "claude"` for best alignment. Explicit
`max_width`/`max_height` always wins.

## Tool groups

- **See:** `screenshot`, `screenshot_region`, `screenshot_window`, `get_screen_size`,
  `active_window`, `list_windows`
- **Mouse:** `click`, `right_click`, `double_click`, `middle_click`, `long_click`,
  `mouse_move`, `drag`, `scroll`, `mouse_scroll`
- **Keyboard:** `type`, `press_key`, `hold_key`, `release_key`, `hotkey`
- **Text / clipboard:** `get_text`, `select_all`, `copy`, `paste`, `get_clipboard`,
  `set_clipboard`
- **Windows / nav:** `focus_window`, `back`, `home`, `recents`
- **System:** `is_elevated`, `elevate` (elevate is unsupported in stdio mode)
- **Optional extras:** `camera`, `list_cameras` (`[camera]`), `play_audio` (`[audio]`)

## Platform notes

- **macOS:** first screenshot prompts for **Screen Recording**; first click/keypress
  prompts for **Accessibility**. Grant both, then restart the launching app. Denied
  permissions return an `isError` result naming the missing permission.
- **Linux:** window ops need `wmctrl` (and `xdotool` for active window):
  `sudo apt install wmctrl xdotool`. Wayland is best-effort.
- **`ui_tree`** is not implemented in this local server.

## Safety

You are operating the user's real machine. Be conservative: don't click destructive
controls, send keystrokes into the wrong window, or trigger confirmation dialogs
without the user's intent. Screenshot to confirm the active window before typing.
