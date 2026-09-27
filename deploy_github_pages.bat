@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem ---------------------------------------------------------------------
rem Push audit code + report site to GitHub. One deploy path: GitHub
rem Actions publishes Pages from branch main, so this script only pushes.
rem
rem   deploy_github_pages.bat                        (remote already set)
rem   deploy_github_pages.bat <repo-url>             (set or change remote)
rem   deploy_github_pages.bat --login                (re-login browser)
rem ----------------------------------------------------------------------

if /i "%~1"=="--login" goto login
if not "%~1"=="" goto setremote
rem Fail fast instead of waiting on a hidden credential dialog.
set GIT_TERMINAL_PROMPT=0
set GCM_INTERACTIVE=never
git remote get-url origin >nul 2>&1
if errorlevel 1 goto noremote

:checkclean
git status --porcelain | findstr . >nul
if not errorlevel 1 goto dirty
echo Tree is clean.
goto fetch

:dirty
echo.
echo ERROR: uncommitted changes. Commit them first, or run:
echo   git add -A
echo   git commit -m "wip"
echo.
pause
exit /b 4

:setremote
git remote remove origin >nul 2>&1
git remote add origin %~1
echo Remote set to %~1

:fetch
git fetch origin
if errorlevel 1 goto authfail

:rebase
git merge-base HEAD origin/main >nul 2>&1
if not errorlevel 1 goto push
echo No shared history with origin/main. Rebasing local commits on top...
git rebase --root --onto origin/main
if errorlevel 1 goto fail

:push
git push origin main
if errorlevel 1 goto authfail

echo.
echo DONE. Code pushed. Pages deploys by Actions (Settings - Pages
echo Source: GitHub Actions). Watch the run on the Actions tab.
echo Site: https://homgorn.github.io/cifra/
echo.
pause
exit /b 0

:login
echo Re-login: GitHub opens a browser window, no token copy-paste needed.
echo.
(echo protocol=https& echo host=github.com& echo.) | git credential reject
git fetch origin
if errorlevel 1 goto authfail
echo Login OK. Run deploy_github_pages.bat again to push.
echo.
pause
exit /b 0

:noremote
echo.
echo No remote origin. Usage:
echo   deploy_github_pages.bat https://github.com/homgorn/cifra.git
echo   deploy_github_pages.bat --login
echo.
pause
exit /b 2

:authfail
echo.
echo AUTH FAILED. Options:
echo   1) deploy_github_pages.bat --login   (browser, recommended)
echo   2) create a classic PAT with repo + workflow, then send it once
echo.
pause
exit /b 3
:fail
echo.
echo FAILED above. Read the message, fix, run again.
echo.
pause
exit /b 1
