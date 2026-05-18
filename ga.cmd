@echo off
rem Preserve the user's invocation directory for frontends (TUI/CLI)
if not defined GA_USER_CWD set "GA_USER_CWD=%CD%"
cd /d "%~dp0"
python -m ga_cli %*
