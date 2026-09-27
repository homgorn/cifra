@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem ---------------------------------------------------------------------
rem Weekly refresh, run locally. Replaces the GitHub Actions job, which
rem cannot run on this account (verified 2026-09-27: even a two-line
rem workflow gets no runner, so it is not a problem in the yml).
rem
rem   refresh_all.bat            full cycle
rem   refresh_all.bat --data     only re-export Yandex APIs and rebuild
rem   refresh_all.bat --site     only validate and redeploy the site
rem --------------------------------------------------------------------

if /i "%~1"=="--data" goto data
if /i "%~1"=="--site" goto site
if not "%~1"=="" goto usage

echo [1/5] Yandex Webmaster API
python scripts\export\yw_api_export.py
if errorlevel 1 goto warn

echo.
echo [1b/5] Yearly query stats (beta tool, quota 100 URL-days per day)
python scripts\export\yw_serp_export.py status
if errorlevel 1 echo Task is still being prepared by Yandex, this is normal.

echo.
echo [2/5] Yandex Metrika API
python scripts\export\metrica_api_export.py
if errorlevel 1 goto warn

echo.
echo [2b/5] Metrika cuts, site and Maps card
python scripts\export\metrica_cuts_export.py
if errorlevel 1 goto warn

echo.
echo [3/5] Rebuild report data
python scripts\export\build_wm_data.py
python scripts\export\build_metrika_site_exports.py
python scripts\export\build_site_data.py
python scripts\export\build_dashboard_data.py
if errorlevel 1 goto fail

echo.
echo [3b/5] Client report from data
python scripts\export\build_client_report.py
if errorlevel 1 goto fail
goto validate

:data
echo [1/3] Yandex APIs
python scripts\export\yw_api_export.py
python scripts\export\metrica_api_export.py
python scripts\export\metrica_cuts_export.py
echo [2/3] Rebuild data
python scripts\export\build_wm_data.py
python scripts\export\build_metrika_site_exports.py
python scripts\export\build_site_data.py
python scripts\export\build_dashboard_data.py
if errorlevel 1 goto fail
echo [3/3] Client report from data
python scripts\export\build_client_report.py
if errorlevel 1 goto fail
goto done

:site
:validate
echo.
echo [4/5] Validate
python scripts\export\validate_report.py
if errorlevel 1 goto fail

echo.
echo [5/5] Deploy
call deploy_github_pages.bat
goto done

:warn
echo.
echo WARNING: an export failed above. Continuing, check the message.

:done
echo.
echo Refresh finished. Review with: git status
echo.
pause
exit /b 0

:usage
echo.
echo Usage: refresh_all.bat [--data|--site]
echo.
pause
exit /b 2

:fail
echo.
echo FAILED. See the message above, nothing was deployed.
echo.
pause
exit /b 1
