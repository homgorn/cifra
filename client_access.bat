@echo off
REM Client-side token helper for Yandex Direct / Webmaster / Metrika.
REM ASCII only on purpose: this file is read by Windows cmd, which
REM decodes non-ASCII comments wrongly depending on the code page.
REM
REM What it does: runs the one-step login, opens the browser, and
REM verifies the result. The token stays in .env on this machine and
REM is never printed.
REM
REM What it does NOT do, and why there is no alternative: the code
REM cannot be received automatically. Yandex locks redirect_uri for
REM applications of the "API access" type to
REM https://oauth.yandex.ru/verification_code, so a local server that
REM would catch the code is not possible. This is the service design,
REM not a limitation of this script.
REM
REM If you only need to grant access, do NOT run this file.
REM Adding the contractor as a user in Webmaster and Metrika, and as a
REM read-only representative in Direct, is enough and needs no code,
REM no token and no password. See CLIENT_ACCESS.md.
setlocal
chcp 65001 >nul
cd /d "%~dp0\..\.."

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo Python ne n nayden. Install Python 3.10 or newer from python.org
  echo and run this file again.
  echo.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo  Yandex access: one step. Browser will open, paste the code.
echo  Do NOT send the token to anyone. It stays in .env here.
echo ============================================================
echo.

python scripts\export\yandex_oauth.py login
if errorlevel 1 goto fail

echo.
echo Proverka ne proshla, smotrite soobshenie vyshe.
echo.
pause
exit /b 1

:fail
echo.
echo Oshibka, smotrite soobshenie vyshe.
echo.
pause
exit /b 1
