@echo off
setlocal enabledelayedexpansion

echo.
echo === Git Status ===
git status

echo.
for /f "tokens=*" %%a in ('git branch --show-current') do set "BRANCH=%%a"
echo Active branch: !BRANCH!

echo.
set /p CONFIRM="Continue with add/commit/push? (y/n): "
if /i "!CONFIRM!" neq "y" (
    echo Cancelled.
    exit /b 0
)

echo.
echo Adding all changes...
git add .

echo.
set /p COMMENT="Enter commit message: "
if "!COMMENT!" == "" (
    echo No commit message provided. Aborting.
    exit /b 1
)

echo.
echo Committing...
git commit -m "!COMMENT!"
if errorlevel 1 (
    echo Commit failed.
    exit /b 1
)

echo.
echo Pushing to origin/!BRANCH!...
git push origin !BRANCH!
if errorlevel 1 (
    echo Push failed.
    exit /b 1
)

echo.
echo Done! Changes pushed to origin/!BRANCH!.
