import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    spec = importlib.util.spec_from_file_location("bootstrap", os.path.join(HERE, "bootstrap.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bootstrap = _load()


def test_data_dir_prefers_claude_plugin_data():
    env = {"CLAUDE_PLUGIN_DATA": "/persist/screenmcp", "XDG_CACHE_HOME": "/xdg"}
    assert bootstrap.data_dir(env, "darwin") == "/persist/screenmcp"
    assert bootstrap.data_dir(env, "win32") == "/persist/screenmcp"


def test_data_dir_falls_back_to_cache_dirs():
    posix = bootstrap.data_dir({"XDG_CACHE_HOME": "/xdg"}, "linux")
    assert posix == os.path.join("/xdg", "screenmcp-claude-plugin")
    win = bootstrap.data_dir({"LOCALAPPDATA": r"C:\Users\me\AppData\Local"}, "win32")
    assert win == os.path.join(r"C:\Users\me\AppData\Local", "screenmcp-claude-plugin")
    home = bootstrap.data_dir({}, "linux")
    assert home.startswith(os.path.expanduser("~"))


def test_venv_dir_is_keyed_by_python_minor_version():
    env = {"CLAUDE_PLUGIN_DATA": "/persist"}
    assert bootstrap.venv_dir(env, "linux", (3, 12)) == os.path.join("/persist", "venv-py3.12")
    assert bootstrap.venv_dir(env, "linux") == bootstrap.venv_dir(env, "linux", sys.version_info[:2])


def test_venv_python_layout_per_platform():
    assert bootstrap.venv_python("/v", "win32") == os.path.join("/v", "Scripts", "python.exe")
    assert bootstrap.venv_python("/v", "darwin") == os.path.join("/v", "bin", "python")
    assert bootstrap.venv_python("/v", "linux") == os.path.join("/v", "bin", "python")


def test_missing_reports_only_unimportable_packages():
    assert bootstrap._missing([("sys", "sys"), ("no_such_module_xyz", "no-such-dist")]) == ["no-such-dist"]


def test_parse_extras_accepts_names_and_all():
    assert bootstrap._parse_extras([]) == []
    assert bootstrap._parse_extras(["--extras", "camera", "audio"]) == ["camera", "audio"]
    assert bootstrap._parse_extras(["--extras", "all"]) == list(bootstrap.EXTRAS)


def test_parse_extras_rejects_unknown_names():
    try:
        bootstrap._parse_extras(["--extras", "teleport"])
    except SystemExit as e:
        assert e.code == 2
    else:
        raise AssertionError("expected SystemExit")
