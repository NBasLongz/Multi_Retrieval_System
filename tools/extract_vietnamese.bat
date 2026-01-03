@echo off
REM Quick script để extract transcripts tiếng Việt

echo ========================================
echo   Extract Transcripts - Tieng Viet
echo ========================================
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found. Using system Python.
)

echo [INFO] Language: Vietnamese (vi)
echo [INFO] Model: base
echo.

set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" exit /b 0

echo.
echo [INFO] Starting extraction...
echo.

python -m scripts.run_whisper_pipeline --model base --language vi

echo.
echo ========================================
echo   Done! Check data/transcripts/
echo ========================================
pause
