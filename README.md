# screenmcp-claude-plugin

A [Claude Code](https://claude.ai/code) plugin that gives Claude **local desktop
vision and control** — screenshot, click, drag, type, hotkeys, window management,
and clipboard — for the machine it's running on. Windows, macOS, Linux.

It bundles the standalone single-file [ScreenMCP](https://screenmcp.com) stdio MCP
server (`screenmcp_cli.py`). No worker, relay, account, or network — it talks to the
desktop directly over stdio.

## Install

```
/plugin install screenmcp-claude-plugin@<marketplace>
```

…or add this repo to a marketplace and install it from there. Once installed, the
`screenmcp-local` MCP server registers automatically.

## Self-installing dependencies

The plugin's `.mcp.json` launches `bootstrap.py`, which on first run ensures the
Python runtime dependencies are importable and installs any that are missing
(preferring `uv pip`, falling back to `python -m pip`):

```
mss  pynput  Pillow  pyperclip  pygetwindow   # (pygetwindow: Windows only)
```

So there is normally **nothing to install by hand**. You just need Python 3.9+ on
`PATH`. Optional extras (install only if needed):

```
pip install opencv-python   # camera / list_cameras
pip install simpleaudio     # play_audio
```

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
.mcp.json                    registers the screenmcp-local server
bootstrap.py                 self-installing launcher → screenmcp_cli.run()
screenmcp_cli.py             vendored single-file stdio MCP server
pyproject.toml               dependency declarations
skills/screenmcp/SKILL.md    how/when Claude should drive the desktop
tests/                       unit + end-to-end stdio tests
```

## Platform notes

- **macOS:** grant **Screen Recording** and **Accessibility** to the launching app on
  first use, then restart it.
- **Linux:** `sudo apt install wmctrl xdotool` for window operations. Wayland is
  best-effort.
- `ui_tree` and `elevate` are not implemented in this local stdio server.

## Credits

Vendored from the `python-cli` of the [ScreenMCP](https://screenmcp.com) project.
See [`python-cli-README.md`](./python-cli-README.md) for the upstream server docs.

## License

MIT — see [LICENSE](./LICENSE).
