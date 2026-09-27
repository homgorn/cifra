@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Deploy report site to GitHub Pages, branch gh-pages.
rem First run once: deploy_github_pages.bat https://github.com/USER/REPO.git
rem Next runs: no arguments, remote is remembered.
if not "%~1"=="" git remote remove origin 2>nul & git remote add origin %~1
git remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo No remote origin. Create empty repo on GitHub, then run:
  echo   deploy_github_pages.bat https://github.com/USER/REPO.git
  echo.
  pause
  exit /b 2
)
git push origin main
if errorlevel 1 goto fail
git subtree push --prefix reports/cifra18-audit origin gh-pages
if errorlevel 1 goto fail
echo.
echo DONE. Enable Pages: Settings - Pages - Deploy from branch - gh-pages.
echo URL: https://USER.github.io/REPO/
echo.
pause
exit /b 0
:fail
echo.
echo PUSH FAILED. Check access, use token as password when asked.
echo.
pause
exit /b 1
