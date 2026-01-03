@echo off
REM Script để extract transcripts sử dụng Whisper
REM Windows batch file

echo ========================================
echo   Whisper Transcript Extraction
echo ========================================
echo.

REM Kiểm tra virtual environment
if not exist .venv\Scripts\activate.bat (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Kiểm tra whisper đã cài chưa
python -c "import whisper" 2>nul
if errorlevel 1 (
    echo [WARNING] Whisper not installed. Installing dependencies...
    pip install -r requirements.txt
)

REM Menu chọn
echo.
echo Select an option:
echo [1] Extract all transcripts (base model, auto language)
echo [2] Extract with custom settings
echo [3] Test with single video
echo [4] Extract only (no ingestion)
echo [5] Full pipeline (extract + ingest)
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo [INFO] Running with default settings...
    python -m scripts.run_whisper_pipeline
    goto :end
)

if "%choice%"=="2" (
    echo.
    set /p model="Enter model size (tiny/base/small/medium/large) [base]: "
    if "%model%"=="" set model=base
    
    set /p lang="Enter language code (en/vi/ja or leave empty for auto): "
    
    echo.
    echo [INFO] Running with: model=%model%, language=%lang%
    if "%lang%"=="" (
        python -m scripts.run_whisper_pipeline --model %model%
    ) else (
        python -m scripts.run_whisper_pipeline --model %model% --language %lang%
    )
    goto :end
)

if "%choice%"=="3" (
    echo.
    set /p video_id="Enter video ID (e.g., L01_V001): "
    
    echo.
    echo [INFO] Testing with video: %video_id%
    python -m scripts.extract_transcripts --single-video %video_id%
    goto :end
)

if "%choice%"=="4" (
    echo.
    echo [INFO] Extract only mode...
    python -m scripts.run_whisper_pipeline --extract-only
    goto :end
)

if "%choice%"=="5" (
    echo.
    echo [INFO] Full pipeline mode...
    python -m scripts.run_whisper_pipeline
    goto :end
)

echo [ERROR] Invalid choice!
pause
exit /b 1

:end
echo.
echo ========================================
echo   Process completed!
echo ========================================
pause
