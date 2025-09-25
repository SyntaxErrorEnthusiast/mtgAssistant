@echo off
REM MTG Chat Application Shutdown Script
REM This script stops all MTG servers by killing processes on their ports

echo Stopping MTG Chat Application servers...
echo.

REM Kill processes on port 8000 (MTG Rules MCP Server)
echo Stopping MTG Rules MCP Server (port 8000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo Killing process %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM Kill processes on port 8001 (Scryfall MCP Server)
echo Stopping Scryfall MCP Server (port 8001)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    echo Killing process %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM Kill processes on port 8008 (Main FastAPI Server)
echo Stopping Main FastAPI Server (port 8008)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8008') do (
    echo Killing process %%a
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo All MTG servers stopped.
echo Press any key to exit...
pause >nul