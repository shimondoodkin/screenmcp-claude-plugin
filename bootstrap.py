#!/usr/bin/env python3
"""Self-installing launcher for the ScreenMCP local stdio server.

The plugin's .mcp.json runs the ``screenmcp-local`` launcher next to this file
(a POSIX sh script on macOS/Linux, ``screenmcp-local.cmd`` on Windows). The
launcher finds a Python 3.9+ interpreter and hands off to THIS file.

On first launch this file makes sure the runtime dependencies are importable.
If they are not, it creates a private virtual environment, installs the
dependencies there and re-executes itself with the venv interpreter. Using a
venv means it works with interpreters that refuse ``pip install`` into the
system site-packages (Homebrew and Debian/Ubuntu "externally managed"
Pythons, PEP 668) and never touches the user's global packages. It prefers
``uv`` when available and falls back to ``python -m pip``.

The venv lives in ``$CLAUDE_PLUGIN_DATA`` (persistent across plugin updates)
when Claude Code provides it, otherwise in the user's cache directory.

    bootstrap.py                         run the server (install deps if needed)
    bootstrap.py --extras camera audio   install optional extras (or "all")
    bootstrap.py --check                 show which interpreter/venv is used

Diagnostics go to stderr so they never corrupt the JSON-RPC stream on stdout.
"""
import importlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REEXEC_FLAG = "SCREENMCP_BOOTSTRAP_REEXEC"

# (import_name, pip_requirement). pygetwindow is Windows-only.
CORE = [
    ("mss", "mss"),
    ("pynput", "pynput"),
    ("PIL", "Pillow"),
    ("pyperclip", "pyperclip"),
]
if sys.platform == "win32":
    CORE.append(("pygetwindow", "pygetwindow"))

# Optional features and the packages they need (see pyproject.toml extras).
EXTRAS = {
    "camera": ["opencv-python"],   # camera / list_cameras
    "audio": ["simpleaudio"],      # play_audio
}


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


# --- locations -----------------------------------------------------------------

def data_dir(env=None, platform=None):
    """Persistent directory for the plugin's private venv."""
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    plugin_data = env.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        return os.path.abspath(plugin_data)
    if platform == "win32":
        base = env.get("LOCALAPPDATA") or os.path.expanduser("~")
    else:
        base = env.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "screenmcp-claude-plugin")


def venv_dir(env=None, platform=None, version=None):
    """One venv per interpreter minor version, so switching Pythons never breaks it."""
    version = tuple(sys.version_info[:2]) if version is None else tuple(version)
    return os.path.join(data_dir(env, platform), "venv-py%d.%d" % version)


def venv_python(venv, platform=None):
    platform = sys.platform if platform is None else platform
    if platform == "win32":
        return os.path.join(venv, "Scripts", "python.exe")
    return os.path.join(venv, "bin", "python")


def _same_path(a, b):
    try:
        return os.path.realpath(a) == os.path.realpath(b)
    except OSError:
        return False


def in_own_venv():
    return _same_path(sys.prefix, venv_dir())


# --- installing ----------------------------------------------------------------

def _run(cmd):
    _log("$ " + " ".join(cmd))
    subprocess.check_call(cmd, stdout=sys.stderr, stderr=sys.stderr)


def _pip_install(python, requirements):
    """Install requirements into the environment of the given interpreter."""
    uv = shutil.which("uv")
    if uv:
        cmd = [uv, "pip", "install", "--python", python] + list(requirements)
    else:
        cmd = [python, "-m", "pip", "install", "--disable-pip-version-check"] + list(requirements)
    _log("installing: " + " ".join(requirements))
    _run(cmd)


def ensure_venv():
    """Create the private venv if it does not exist yet; return its interpreter."""
    venv = venv_dir()
    python = venv_python(venv)
    if os.path.exists(python):
        return python
    os.makedirs(os.path.dirname(venv), exist_ok=True)
    _log("creating virtual environment: " + venv)
    uv = shutil.which("uv")
    try:
        if uv:
            _run([uv, "venv", "--seed", "--python", sys.executable, venv])
        else:
            _run([sys.executable, "-m", "venv", venv])
            # The pip bundled with older interpreters (macOS's Python 3.9 ships
            # pip 21) cannot resolve current binary wheels such as pyobjc, so
            # refresh it before installing anything.
            _run([python, "-m", "pip", "install", "--disable-pip-version-check",
                  "--quiet", "--upgrade", "pip"])
    except Exception as e:  # noqa: BLE001 — surface any failure clearly
        _log("could not create a virtual environment: %r" % (e,))
        if sys.platform.startswith("linux"):
            _log("Debian/Ubuntu: sudo apt install python3-venv  (or install uv)")
        raise
    return python


def _reexec(python, argv):
    """Replace this process with the venv interpreter running this file."""
    env = dict(os.environ)
    env[REEXEC_FLAG] = "1"
    cmd = [python, os.path.abspath(__file__)] + list(argv)
    sys.stdout.flush()
    sys.stderr.flush()
    if sys.platform == "win32":
        # os.exec* on Windows spawns a new process and returns immediately,
        # which would close the MCP stdio pipes. Run it as a child instead.
        sys.exit(subprocess.call(cmd, env=env))
    os.execve(python, cmd, env)


# --- entry points --------------------------------------------------------------

def _serve():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import screenmcp_cli  # noqa: E402 — imported only after deps are ensured
    screenmcp_cli.run()


def _parse_extras(argv):
    if "--extras" not in argv:
        return []
    names = [a for a in argv[argv.index("--extras") + 1:] if not a.startswith("-")]
    if not names:
        _log("--extras needs at least one of: " + ", ".join(list(EXTRAS) + ["all"]))
        sys.exit(2)
    if "all" in names:
        names = list(EXTRAS)
    unknown = [n for n in names if n not in EXTRAS]
    if unknown:
        _log("unknown extras: %s (available: %s)" % (", ".join(unknown), ", ".join(EXTRAS)))
        sys.exit(2)
    return names


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    extras = _parse_extras(argv)
    missing = _missing(CORE)
    own = in_own_venv()
    venv_exists = os.path.exists(venv_python(venv_dir()))

    if "--check" in argv:
        if venv_exists and not own and not os.environ.get(REEXEC_FLAG):
            _reexec(venv_python(venv_dir()), argv)   # report the venv the server runs in
        print("interpreter: " + sys.executable)
        print("python: " + sys.version.split()[0])
        print("venv: %s (%s)" % (venv_dir(), "exists" if venv_exists else "not created"))
        print("running inside venv: " + ("yes" if own else "no"))
        print("launched via: " + (os.environ.get("SCREENMCP_PYTHON") or "PATH lookup"))
        print("missing core deps: " + (" ".join(missing) or "none"))
        return

    if extras:
        requirements = [r for name in extras for r in EXTRAS[name]]
        if own or (not missing and not venv_exists):
            target = sys.executable       # the server runs here — install here
        else:
            target = ensure_venv()
            requirements = [r for _, r in CORE] + requirements
        _pip_install(target, requirements)
        _log("extras installed: " + ", ".join(extras))
        return

    # Fast path: everything importable, and no private venv that should win.
    if not missing and (own or not venv_exists):
        return _serve()

    if own:
        # We are the venv interpreter: install straight into it and run.
        try:
            _pip_install(sys.executable, missing)
        except Exception as e:  # noqa: BLE001
            _log("dependency install failed: %r" % (e,))
            _log("install manually: %s -m pip install %s"
                 % (sys.executable, " ".join(r for _, r in CORE)))
            sys.exit(1)
        still = _missing(CORE)
        if still:
            _log("still missing after install: " + " ".join(still))
            sys.exit(1)
        return _serve()

    if os.environ.get(REEXEC_FLAG):
        _log("re-exec did not land in the venv (%s) — giving up" % venv_dir())
        sys.exit(1)

    try:
        python = ensure_venv()
    except Exception:
        # Last resort: the original behaviour — install into this interpreter.
        _log("falling back to installing into " + sys.executable)
        try:
            _pip_install(sys.executable, missing)
        except Exception as e:  # noqa: BLE001
            _log("dependency install failed: %r" % (e,))
            sys.exit(1)
        if _missing(CORE):
            sys.exit(1)
        return _serve()
    _reexec(python, argv)


if __name__ == "__main__":
    main()
