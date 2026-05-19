@echo off
echo Building ING Watch EXE...
cd /d "%~dp0"
python -m PyInstaller --onedir --windowed --name "ING Watch" --clean --noconfirm --add-data "src;src" main.py
if errorlevel 1 (
    echo BUILD FAILED
    pause
    exit /b 1
)
echo.
echo Build complete! EXE is at: dist\ING Watch\ING Watch.exe
echo.
echo Copying to Desktop...
if exist "%USERPROFILE%\Desktop\ING Watch v2" rmdir /s /q "%USERPROFILE%\Desktop\ING Watch v2"
xcopy /E /I /Q "dist\ING Watch" "%USERPROFILE%\Desktop\ING Watch v2"
echo Done! Run from Desktop\ING Watch v2\ING Watch.exe
pause
