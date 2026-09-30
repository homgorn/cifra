@echo off
REM Yandex access and data export for Cifra18.
REM ASCII only on purpose: cmd decodes non-ASCII comments by the code page.
REM
REM What changed and why. This file used to print an authorize URL with a
REM confirmation code step, then exchange that code for a token. That flow
REM is dead. Yandex refused every scope value on it with invalid_scope, and
REM the Metrika documentation says to obtain the token with
REM response_type=token instead, where no scope is requested at all. There
REM is no code to exchange any more, so the whole step is gone.
REM
REM   yandex_setup.bat              log in, verify, then export
REM   yandex_setup.bat --token      log in and verify only
REM   yandex_setup.bat --data       export only, no login
REM   yandex_setup.bat --check      verify the token already in .env, export nothing
REM
REM The login step opens a browser and waits for a token pasted back in.
REM Sign in as the account added to the Webmaster panel and to the Metrika
REM counter, not as the site owner account.
REM
REM Note on syntax. Every set uses quoted form: set "VAR=value". The bare
REM form set VAR=value & ... stores a trailing space in the value, because
REM the space before & is part of it, and then if "%VAR%"=="0" never
REM matches. That silently ignored the command line and ran the login step
REM even when --check was given.
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "DO_LOGIN=1"
set "DO_DATA=1"

:parse
if "%~1"=="" goto run
if /i "%~1"=="--token"  set "DO_DATA=0"  & shift & goto parse
if /i "%~1"=="--data"   set "DO_LOGIN=0" & shift & goto parse
if /i "%~1"=="--check"  set "DO_LOGIN=0" & set "DO_DATA=0" & shift & goto parse
if /i "%~1"=="--help"   goto usage
if /i "%~1"=="/?"       goto usage
echo.
echo Neizvestnyi argument: %~1
echo.
:usage
echo Ispolzovanie:
echo   yandex_setup.bat              vhod, proverka, potom vygruzka
echo   yandex_setup.bat --token      tolko vhod i proverka
echo   yandex_setup.bat --data       tolko vygruzka, bez vhoda
echo   yandex_setup.bat --check      proverka tokena iz .env, nichego ne pishet
echo.
pause
exit /b 2

:run
where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo Python ne n nayden. Install Python 3.10 or newer from python.org
  echo and run this file again.
  echo.
  pause
  exit /b 1
)

if "%DO_LOGIN%"=="1" (
  echo.
  echo ============================================================
  echo  SHAG 1. Otkroyetsya brauzer, voydite pod SVOIM akkountom.
  echo  Ne pod akkuntom vladeltsa saita.
  echo ============================================================
  echo.
  python scripts\export\yandex_oauth.py login
  if errorlevel 1 goto fail
)

if "%DO_LOGIN%"=="0" (
  echo.
  echo Proverka tokena iz .env ...
  echo.
  python scripts\export\yandex_oauth.py test
  if errorlevel 1 goto fail
)

if "%DO_DATA%"=="0" (
  echo.
  echo GOTOVO: token proveren, vygruzka ne zapuskalas.
  pause
  exit /b 0
)

echo.
echo ============================================================
echo  VYGRUZKA DANNYH
echo ============================================================
echo.
python scripts\export\metrica_cuts_export.py
if errorlevel 1 goto fail
python scripts\export\yw_api_export.py
if errorlevel 1 goto fail
python scripts\export\fetch_robots_state.py
if errorlevel 1 goto fail
python scripts\export\build_nav.py
if errorlevel 1 goto fail
python scripts\export\validate_report.py
if errorlevel 1 goto fail

echo.
echo ============================================================
echo  GOTOVO. Vse proverki proshli.
echo ============================================================
echo.
pause
exit /b 0

:fail
echo.
echo ============================================================
echo  NE GOTOVO. Smotrite soobshenie vyshe.
echo  Nichego ne zapisano, predydushchie vygruzki ne tronuty.
echo ============================================================
echo.
pause
exit /b 1
