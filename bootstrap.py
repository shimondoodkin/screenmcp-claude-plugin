#!/usr/bin/env python3
"""Self-installing launcher for the ScreenMCP local stdio server.

The Claude plugin's .mcp.json runs THIS file. On first launch it makes sure the
runtime dependencies are importable; if any are missing it installs them
(preferring `uv pip` when available, falling back to `python -m pip`), then hands
off to screenmcp_cli.run(). Diagnostics go to stderr so they never corrupt the
JSON-RPC stream on stdout.
"""
import importlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# (import_name, pip_requirement). pygetwindow is Windows-only.
CORE = [
    ("mss", "mss"),
    ("pynput", "pynput"),
    ("PIL", "Pillow"),
    ("pyperclip", "pyperclip"),
]
if sys.platform == "win32":
    CORE.append(("pygetwindow", "pygetwindow"))


def _log(msg):
    sys.stderr.write("[screenmcp bootstrap] " + msg + "\n")
    sys.stderr.flush()


def _missing(pkgs):
    out = []
    for import_name, requirement in pkgs:
        try:
            importlib.import_module(import_name)
        except ImportError:
            out.append(requirement)
    return out


def _install(requirements):
    """Install requirements into the running interpreter's environment."""
    # Prefer uv if it's on PATH — it's dramatically faster.
    uv = None
    for finder in ("uv",):
        from shutil import which
        uv = which(finder)
        if uv:
            break
    if uv:
        cmd = [uv, "pip", "install", "--python", sys.executable, *requirements]
    else:
        cmd = [sys.executable, "-m", "pip", "install", *requirements]
    _log("installing missing dependencies: " + " ".join(requirements))
    subprocess.check_call(cmd, stdout=sys.stderr, stderr=sys.stderr)


def main():
    missing = _missing(CORE)
    if missing:
        try:
            _install(missing)
        except Exception as e:  # noqa: BLE001 — surface any installer failure clearly
            _log("dependency install failed: %r" % (e,))
            _log("install manually: pip install " + " ".join(r for _, r in CORE))
            sys.exit(1)
        still = _missing(CORE)
        if still:
            _log("still missing after install: " + " ".join(still))
            sys.exit(1)

    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import screenmcp_cli  # noqa: E402 — imported only after deps are ensured
    screenmcp_cli.run()


if __name__ == "__main__":
    main()
