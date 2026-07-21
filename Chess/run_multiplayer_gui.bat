@echo off
echo Starting Chess Multiplayer (GUI login)...

start "Chess Server" cmd /k "cd /d "%~dp0" && python -m server.server_main"

timeout /t 2 /nobreak >nul

start "Player 1" cmd /k "cd /d "%~dp0" && python UI/py/network_main.py --gui"
start "Player 2" cmd /k "cd /d "%~dp0" && python UI/py/network_main.py --gui"
