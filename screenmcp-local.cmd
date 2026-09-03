@echo off
rem Launcher for the screenmcp-local MCP server on Windows.
rem (macOS and Linux use the extension-less "screenmcp-local" sh script next to this file.)
rem
rem Finds a Python 3.9+ interpreter - python, then the py launcher, then python3 -
rem and hands off to bootstrap.py, which installs the runtime dependencies into a
rem private venv on first run. Set SCREENMCP_PYTHON to force a specific interpreter.
setlocal
set "HERE=%~dp0"
if defined SCREENMCP_PYTHON (
  set "PY="%SCREENMCP_PYTHON%""
  goto :run
)
for %%P in (python "py -3" python3) do (
  call %%~P -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
  if not errorlevel 1 (
    set "PY=%%~P"
    goto :run
  )
)
echo [screenmcp] Python 3.9+ not found (tried python, py -3, python3). Install Python 3 or set SCREENMCP_PYTHON. 1>&2
exit /b 1
:run
%PY% "%HERE%bootstrap.py" %*
exit /b %ERRORLEVEL%
