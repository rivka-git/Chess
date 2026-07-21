@echo off
echo Starting Chess Multiplayer...

start "Chess Server" cmd /k "cd /d "%~dp0" && python -m server.server_main"

timeout /t 2 /nobreak >nul

start "Player White" cmd /k "cd /d "%~dp0" && python UI/py/network_main.py"
start "Player Black" cmd /k "cd /d "%~dp0" && python UI/py/network_main.py"
