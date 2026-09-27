@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not "%~1"=="" goto exchange
python scripts\export\yandex_oauth.py auth-url
echo.
echo Skopiruyte kod so stranitsy i zapustite:
echo   yandex_setup.bat KOD
echo.
pause
exit /b 2
:exchange
python scripts\export\yandex_oauth.py exchange %1
if errorlevel 1 goto fail
python scripts\export\yandex_oauth.py test
if errorlevel 1 goto fail
python scripts\export\metrica_api_export.py
if errorlevel 1 goto fail
python scripts\export\yw_api_export.py
if errorlevel 1 goto fail
echo.
echo GOTOVO.
pause
exit /b 0
:fail
echo.
echo OSHIBKA, smotrite soobshchenie vyshe.
pause
exit /b 1
