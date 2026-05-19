@echo off
echo Building RigAlert by ING Mining (single EXE)...
cd /d "%~dp0"
python -m PyInstaller RigAlert.spec --clean --noconfirm
if errorlevel 1 (
    echo BUILD FAILED
    pause
    exit /b 1
)
echo.
echo Build complete! EXE is at: dist\RigAlert.exe
echo.
echo Copying to Desktop...
copy /Y "dist\RigAlert.exe" "%USERPROFILE%\Desktop\RigAlert.exe"
echo Done! Run RigAlert.exe from your Desktop.
pause
