@echo off
REM ================================================================
REM Script để chạy pipeline transcript extraction và ingestion
REM ================================================================

echo.
echo ================================================================
echo TRANSCRIPT PIPELINE - Extract va Ingest Transcripts
echo ================================================================
echo.

REM Kiểm tra Python environment
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python khong duoc cai dat hoac khong co trong PATH
    pause
    exit /b 1
)

REM Chọn mode chạy
echo Chon mode chay:
echo   1. Extract va Ingest tat ca (All)
echo   2. Chi extract transcripts
echo   3. Chi ingest transcripts
echo   4. Verify setup
echo   5. Extract mot video cu the
echo.
set /p mode="Nhap lua chon (1-5): "

if "%mode%"=="1" goto RUN_ALL
if "%mode%"=="2" goto EXTRACT_ONLY
if "%mode%"=="3" goto INGEST_ONLY
if "%mode%"=="4" goto VERIFY_ONLY
if "%mode%"=="5" goto SINGLE_VIDEO
echo [ERROR] Lua chon khong hop le
pause
exit /b 1

:RUN_ALL
echo.
echo [INFO] Chay pipeline hoan chinh (Extract + Ingest)...
echo.
python scripts\run_transcript_pipeline.py --all --language vi --model base
goto END

:EXTRACT_ONLY
echo.
echo [INFO] Chi extract transcripts...
echo.
python scripts\run_transcript_pipeline.py --extract-only --language vi --model base
goto END

:INGEST_ONLY
echo.
echo [INFO] Chi ingest transcripts...
echo.
python scripts\run_transcript_pipeline.py --ingest-only
goto END

:VERIFY_ONLY
echo.
echo [INFO] Verify setup...
echo.
python scripts\run_transcript_pipeline.py --verify-only
goto END

:SINGLE_VIDEO
echo.
set /p video_id="Nhap video ID (vi du: L01_V001): "
echo.
echo [INFO] Extract transcript cho video: %video_id%
echo.
python scripts\run_transcript_pipeline.py --video %video_id% --language vi --model base
goto END

:END
echo.
echo ================================================================
echo Pipeline hoan thanh!
echo ================================================================
echo.
pause
