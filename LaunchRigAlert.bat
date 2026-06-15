@echo off
:: Launches RigAlert and immediately maximizes the window
:: Double-click this instead of RigAlert.exe

:: Kill any stale instances first
taskkill /F /IM RigAlert.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul

:: Start RigAlert
start "" "%USERPROFILE%\Desktop\RigAlert.exe"

:: Wait for the Qt window to get a handle, then maximize it
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;public class W{[DllImport(\"user32.dll\")]public static extern bool ShowWindow(IntPtr h,int n);}'; $t=0; while($t -lt 30){Start-Sleep -Milliseconds 400;$t++;$p=Get-Process -Name RigAlert -ErrorAction SilentlyContinue|Where-Object{$_.MainWindowHandle -ne 0}|Select-Object -First 1;if($p){Start-Sleep -Milliseconds 300;[W]::ShowWindow($p.MainWindowHandle,3);break}}"
