@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem ---------------------------------------------------------------------
rem Push audit code + report site to GitHub. GitHub Actions publishes
rem Pages from branch main, so this script only pushes.
rem
rem   deploy_github_pages.bat                 push (signs in on first run)
rem   deploy_github_pages.bat <repo-url>      set or change remote
rem   deploy_github_pages.bat --login         force a fresh browser sign-in
rem
rem No token copy-paste needed: Git Credential Manager opens a browser
rem and stores the account for every repo on this machine.
rem ----------------------------------------------------------------------

if /i "%~1"=="--login" goto login
if not "%~1"=="" goto setremote
set GIT_TERMINAL_PROMPT=0

:checkclean
git status --porcelain | findstr . >nul
if not errorlevel 1 goto dirty
git remote get-url origin >nul 2>&1
if errorlevel 1 goto noremote
echo Tree is clean, remote OK.
goto fetch

:dirty
echo.
echo ERROR: uncommitted changes. Commit first:
echo   git add -A
echo   git commit -m "wip"
echo.
pause
exit /b 4

:noremote
echo.
echo No remote origin. Usage:
echo   deploy_github_pages.bat https://github.com/homgorn/cifra.git
echo   deploy_github_pages.bat --login
echo.
pause
exit /b 2

:setremote
git remote remove origin >nul 2>&1
git remote add origin %~1
echo Remote set to %~1
goto checkclean

:login
echo Forcing a fresh GitHub sign-in. A browser window will open.
powershell -NoProfile -Command "'protocol=https','host=github.com','username=homgorn','' | git credential reject" >nul 2>&1
goto fetch

:fetch
git fetch origin
if not errorlevel 1 goto rebase
echo.
echo Not signed in yet. Opening a browser window, finish the login there.
powershell -NoProfile -Command "'protocol=https','host=github.com','username=homgorn','' | git credential reject" >nul 2>&1
git fetch origin
if errorlevel 1 goto authfail

:rebase
git merge-base HEAD origin/main >nul 2>&1
if not errorlevel 1 goto push
for /f "delims=" %%h in ('git rev-parse HEAD') do set "HEADBEFORE=%%h"
if exist ".git\rebase-merge" goto stalerebase
if exist ".git\rebase-apply" goto stalerebase
echo No shared history with origin/main. Rebasing local commits on top...
rem The wrangler cache is gitignored, so a rebase that restores its old
rem copy aborts. Drop the cache; it regenerates. Never use git clean -X here:
rem that would delete .env with the Yandex token.
if exist "reports\cifra18-audit\.wrangler" rmdir /s /q "reports\cifra18-audit\.wrangler"
git rebase --root --onto origin/main
if errorlevel 1 goto rebasefail

:stalerebase
echo Stale rebase directory found. Clearing it.
git rebase --abort >nul 2>&1
if exist ".git\rebase-merge" rmdir /s /q ".git\rebase-merge"
if exist ".git\rebase-apply" rmdir /s /q ".git\rebase-apply"
goto rebase

:rebasefail
rem A stale rebase dir makes "git rebase --abort" move HEAD back further than
rem where we started. Undo that, otherwise local commits vanish silently.
git rebase --abort >nul 2>&1
for /f "delims=" %%h in ('git rev-parse HEAD') do set "HEADNOW=%%h"
if "%HEADBEFORE%"=="%HEADNOW%" goto rebasefailmsg
echo Restoring HEAD, the abort moved it to an older commit.
git reset --hard "%HEADBEFORE%"
:rebasefailmsg
echo.
echo REBASE CONFLICT, aborted, repo left intact.
echo Remote main and local history diverged. Resolve it by hand:
echo   git fetch origin
echo   git rebase --root --onto origin/main
echo resolve conflicts, then: git rebase --continue
echo.
pause
exit /b 5

:push
git push origin main
if errorlevel 1 goto fail
git subtree push --prefix reports/cifra18-audit origin gh-pages
if errorlevel 1 goto fail

echo.
echo DONE. Code on main, site on gh-pages.
echo Site: https://homgorn.github.io/cifra/
echo Note: the weekly refresh is local, see refresh_all.bat
echo (Actions cannot run jobs on this account, diagnosed 2026-09-27).
echo.
pause
exit /b 0

:rebasefail
git rebase --abort >nul 2>&1
echo.
echo REBASE CONFLICT, aborted, repo left intact.
echo Remote main and local history diverged. Resolve it by hand:
echo   git fetch origin
echo   git rebase --root --onto origin/main
echo resolve conflicts, then: git rebase --continue
echo.
pause
exit /b 5

:authfail
echo.
echo AUTH FAILED after a browser sign-in. Check the GitHub account:
echo   - repo homgorn/cifra exists and this account has access
echo   - https://github.com/settings/tokens has no half-created token
echo Then run: deploy_github_pages.bat --login
echo.
pause
exit /b 3

:fail
echo.
echo FAILED above. Read the message, fix, run again.
echo.
pause
exit /b 1
