# screenmcp-claude-plugin

A [Claude Code](https://claude.ai/code) plugin that gives Claude **local desktop
vision and control** — screenshot, click, drag, type, hotkeys, window management,
and clipboard — for the machine it's running on. Windows, macOS, Linux.

It bundles the standalone single-file [ScreenMCP](https://screenmcp.com) stdio MCP
server (`screenmcp_cli.py`). No worker, relay, account, or network — it talks to the
desktop directly over stdio.

## Install

This repo doubles as its own Claude Code marketplace. In Claude Code:

```
/plugin marketplace add shimondoodkin/screenmcp-claude-plugin
/plugin install screenmcp-claude-plugin@screenmcp-claude-plugin
```

Once installed, the `screenmcp-local` MCP server registers automatically.

## Self-installing dependencies

The plugin's `.mcp.json` runs the `screenmcp-local` launcher (a `sh` script on
macOS/Linux, `screenmcp-local.cmd` on Windows). It finds a **Python 3.9+**
interpreter — `python3` first on macOS/Linux, `python` / `py -3` first on
Windows — and hands off to `bootstrap.py`. On first run `bootstrap.py` creates a
private virtual environment and installs the runtime dependencies into it
(preferring `uv`, falling back to `python -m pip`):

```
mss  pynput  Pillow  pyperclip  pygetwindow   # (pygetwindow: Windows only)
```

The venv is kept in `$CLAUDE_PLUGIN_DATA` (persistent across plugin updates) or,
outside Claude Code, in `~/.cache/screenmcp-claude-plugin` (`%LOCALAPPDATA%` on
Windows). Nothing is installed into your system or global Python, and it works
with "externally managed" interpreters (Homebrew, Debian/Ubuntu) that refuse
plain `pip install`.

So there is normally **nothing to install by hand**. You just need Python 3.9+
on `PATH` (on macOS the `python3` that comes with the Xcode Command Line Tools is
enough). Optional extras (install only if needed):

```
python3 bootstrap.py --extras camera   # camera / list_cameras  (opencv-python)
python3 bootstrap.py --extras audio    # play_audio             (simpleaudio)
python3 bootstrap.py --extras all
```

(`python bootstrap.py ...` on Windows.) Run `bootstrap.py --check` to see which
interpreter and venv the server uses. Set `SCREENMCP_PYTHON=/path/to/python` to
force a specific interpreter.

## What Claude can do

After install, Claude has tools like `screenshot`, `click`, `double_click`, `drag`,
`scroll`, `type`, `hotkey`, `list_windows`, `focus_window`, `copy`/`paste`, and more.
The bundled **skill** (`skills/screenmcp`) teaches Claude when and how to use them —
including the 1456×819 coordinate space and the `model` sizing argument.

## Coordinates

Screenshots default to **1456×819**; click/drag/scroll coordinates are in that space
and auto-scale to your real screen. Pass `model: "claude"` to size the screenshot and
click space to Claude's vision limits. Override with `max_width`/`max_height`
(`0` = native pixels).

## Layout

```
.claude-plugin/plugin.json   plugin manifest
.claude-plugin/marketplace.json  makes this repo installable as a marketplace
.mcp.json                    registers the screenmcp-local server
screenmcp-local              launcher (macOS/Linux): finds python3 → bootstrap.py
screenmcp-local.cmd          launcher (Windows): finds python / py -3 → bootstrap.py
bootstrap.py                 creates a private venv, installs deps → screenmcp_cli.run()
screenmcp_cli.py             vendored single-file stdio MCP server
pyproject.toml               dependency declarations
skills/screenmcp/SKILL.md    how/when Claude should drive the desktop
tests/                       unit + end-to-end stdio tests
```

## Platform notes

- **macOS:** no `python` command exists by default (only `python3`) — the launcher
  handles that. Grant **Screen Recording** and **Accessibility** to the launching
  app (Terminal, the Claude app, your IDE) on first use, then restart it.
- **Linux:** `sudo apt install wmctrl xdotool` for window operations. Wayland is
  best-effort. If venv creation fails: `sudo apt install python3-venv` (or install
  [uv](https://docs.astral.sh/uv/)).
- **Windows:** `python` from python.org or the Microsoft Store both work; the
  launcher also tries the `py -3` launcher and `python3`.
- `ui_tree` and `elevate` are not implemented in this local stdio server.

## Credits

Vendored from the `python-cli` of the [ScreenMCP](https://screenmcp.com) project.
See [`python-cli-README.md`](./python-cli-README.md) for the upstream server docs.

## License

MIT — see [LICENSE](./LICENSE).
