@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo  Blender Manager - DEBUG build (console)
echo ==========================================
echo.
echo Produces dist\blender_manager_debug.exe, which keeps a console window
echo open so startup errors are visible instead of failing silently.
echo.

set BM_DEBUG_CONSOLE=1

python -m PyInstaller --noconfirm --clean blender_manager.spec
if errorlevel 1 goto :error

echo.
echo ==========================================
echo  Done: "%cd%\dist\blender_manager_debug.exe"
echo  Run it from a terminal and read the output.
echo ==========================================
endlocal
exit /b 0

:error
echo.
echo  BUILD FAILED (exit code %errorlevel%)
endlocal
exit /b 1
