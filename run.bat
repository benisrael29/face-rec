@echo off
echo Face Detection Application
echo ========================
echo.

python setup.py
if %errorlevel% neq 0 (
    echo.
    echo Setup failed. Please check the error message above.
    pause
    exit /b %errorlevel%
)

exit /b 0 