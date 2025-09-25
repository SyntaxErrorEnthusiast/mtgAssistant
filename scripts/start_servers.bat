@echo off
REM MTG Chat Application Startup Script
REM This script starts all required servers in the correct order

echo Starting MTG Chat Application...
echo.

REM Kill any existing processes on our ports to prevent conflicts
echo Cleaning up any existing processes on ports 8000, 8001, and 8008...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8008') do taskkill /PID %%a /F >nul 2>&1
echo Cleanup complete.
echo.

REM Change to parent directory where the Python files are located
cd /d "%~dp0.."

REM Start MTG Rules MCP Server (port 8000)
echo Starting MTG Rules MCP Server on port 8000...
start "MTG Rules Server" cmd /k "python mcp/mtg_rules_mcp_server.py"
timeout /t 3 >nul

REM Start Scryfall MCP Server (port 8001)
echo Starting Scryfall MCP Server on port 8001...
start "Scryfall Server" cmd /k "python mcp/scryfall_mcp_server.py"
timeout /t 3 >nul

REM Start Main FastAPI Server (port 8008)
echo Starting Main FastAPI Server on port 8008...
start "Main MTG Server" cmd /k "python agents/mtg_server.py"
timeout /t 3 >nul

echo.
echo All servers started successfully!
echo.
echo Server URLs:
echo - MTG Rules MCP: http://127.0.0.1:8000/mcp
echo - Scryfall MCP:  http://127.0.0.1:8001/mcp
echo - Main API:      http://127.0.0.1:8008
echo.
echo Press any key to exit this window (servers will continue running)...
pause >nul