@echo off
rem Preserve the user's invocation directory for frontends (TUI/CLI)
if not defined RT_USER_CWD set "RT_USER_CWD=%CD%"
cd /d "%~dp0"
python -m rt_cli %*
