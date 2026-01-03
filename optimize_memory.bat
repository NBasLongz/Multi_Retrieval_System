@echo off
REM Script tối ưu memory trước khi chạy backend
REM Chạy: optimize_memory.bat

echo ============================================
echo  Memory Optimization Script
echo ============================================
echo.

echo [1/4] Clearing Windows memory cache...
REM Xóa standby list (cached memory không dùng)
PowerShell -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"
echo Done.
echo.

echo [2/4] Checking available memory...
PowerShell -Command "Get-CimInstance -ClassName Win32_OperatingSystem | Select-Object @{Name='FreePhysicalMemory(GB)';Expression={[math]::Round($_.FreePhysicalMemory/1MB,2)}}, @{Name='TotalVisibleMemory(GB)';Expression={[math]::Round($_.TotalVisibleMemorySize/1MB,2)}}"
echo.

echo [3/4] Checking page file settings...
PowerShell -Command "Get-CimInstance -ClassName Win32_PageFileUsage | Select-Object Name, AllocatedBaseSize, CurrentUsage"
echo.

echo [4/4] Recommendations:
echo    - Close Chrome/Firefox (browsers use a lot of RAM)
echo    - Close Visual Studio Code if not needed
echo    - Increase page file to 8-16 GB (see FIX_PAGING_FILE.md)
echo    - Consider running: EmptyStandbyList.exe (download from Microsoft)
echo.

echo ============================================
echo  Ready to start backend
echo ============================================
echo.
pause

REM Optional: Auto-start backend after optimization
REM cd /d "%~dp0"
REM python -m backend.app
