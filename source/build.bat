@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo  Blender Manager - single file exe build
echo ==========================================
echo.

echo [1/5] Installing runtime dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo [2/5] Installing PyInstaller...
python -m pip install "pyinstaller>=6.0"
if errorlevel 1 goto :error

echo.
echo [3/5] Fixing ttkbootstrap's import-time locale crash...
python patch_ttkbootstrap.py
if errorlevel 1 goto :error

echo.
echo [4/5] Installing the custom ttkbootstrap themes...
python sync_themes.py
if errorlevel 1 goto :error

echo.
echo [5/5] Freezing the application...
python -m PyInstaller --noconfirm --clean blender_manager.spec
if errorlevel 1 goto :error

echo.
echo ==========================================
echo  Done: "%cd%\dist\blender_manager.exe"
echo ==========================================
endlocal
exit /b 0

:error
echo.
echo ==========================================
echo  BUILD FAILED (exit code %errorlevel%)
echo ==========================================
endlocal
exit /b 1
