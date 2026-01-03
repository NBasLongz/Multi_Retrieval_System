@echo off
REM Script to run ingest_data.py with cache clearing

echo Clearing Python cache...
if exist __pycache__ rmdir /s /q __pycache__
if exist scripts\__pycache__ rmdir /s /q scripts\__pycache__
if exist utils\__pycache__ rmdir /s /q utils\__pycache__

echo Running ingest_data.py...
python ingest_data.py

echo.
echo Done!
pause
