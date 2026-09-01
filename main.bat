@echo off
cd C:\Programs\proLCI
call conda activate ougl
python "check_deps.py"
if %errorlevel% neq 0 (
    echo Dependency installation failed. Exiting...
    pause
    exit /b 1
)
python "setupLCI.py"
pause