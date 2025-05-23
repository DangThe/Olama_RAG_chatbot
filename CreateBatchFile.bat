# Create-All-Batch-Files.ps1
# Script để tự động tạo tất cả file batch cho RAG Chatbot

Write-Host "========================================"
Write-Host "   Creating RAG Chatbot Batch Files"
Write-Host "========================================"
Write-Host ""

# Kiểm tra thư mục hiện tại
$currentDir = Get-Location
Write-Host "Creating files in: $currentDir"
Write-Host ""

# Đảm bảo đang ở đúng thư mục
$confirm = Read-Host "Is this your RAG Chatbot project root folder? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "Please run this script from your project root folder."
    Exit
}

# Tạo function để write file với encoding UTF-8
function Create-BatchFile {
    param(
        [string]$fileName,
        [string]$content
    )
    
    Write-Host "Creating $fileName..."
    $content | Out-File -FilePath $fileName -Encoding ASCII
}

# start.bat
$startContent = @'
@echo off
echo ========================================
echo   RAG Chatbot - Starting Services
echo ========================================
echo.

:: Kiểm tra Ollama
echo [1/4] Checking Ollama service...
ollama list >nul 2>&1
if errorlevel 1 (
    echo    - Ollama not running, starting Ollama...
    start "Ollama Service" cmd /k ollama serve
    echo    - Waiting for Ollama to start...
    timeout /t 5 /nobreak >nul
) else (
    echo    - Ollama is already running
)

:: Khởi động Backend
echo [2/4] Starting Backend Server...
cd backend
start "Backend Server" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"
cd ..
echo    - Backend starting on http://localhost:8000

:: Chờ backend khởi động
echo [3/4] Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

:: Khởi động Frontend
echo [4/4] Starting Frontend...
cd frontend
start "Frontend Server" cmd /k "npm start"
cd ..
echo    - Frontend starting on http://localhost:3000

echo.
echo ========================================
echo   All services are starting!
echo ========================================
echo.
echo Services:
echo - Ollama:   http://localhost:11434
echo - Backend:  http://localhost:8000
echo - Frontend: http://localhost:3000
echo.
echo Press any key to open the application in browser...
pause >nul

:: Mở browser
start http://localhost:3000

echo.
echo Application launched successfully!
echo Close this window when done.
pause
'@

Create-BatchFile "start.bat" $startContent

# restart.bat
$restartContent = @'
@echo off
echo ========================================
echo   RAG Chatbot - Restarting Services
echo ========================================
echo.

:: Dừng các services hiện tại
echo [1/3] Stopping current services...

:: Kill backend processes (uvicorn)
echo    - Stopping Backend...
taskkill /F /IM uvicorn.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: Kill frontend processes (node/npm)
echo    - Stopping Frontend...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Frontend Server*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: Đợi processes kết thúc
echo    - Waiting for processes to terminate...
timeout /t 3 /nobreak >nul

echo [2/3] Services stopped successfully!
echo.

:: Khởi động lại bằng cách gọi start.bat
echo [3/3] Starting services again...
echo.
call start.bat
'@

Create-BatchFile "restart.bat" $restartContent

# stop.bat
$stopContent = @'
@echo off
echo ========================================
echo   RAG Chatbot - Stopping All Services
echo ========================================
echo.

:: Dừng Backend
echo [1/4] Stopping Backend Server...
taskkill /F /IM uvicorn.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo    - Backend stopped

:: Dừng Frontend
echo [2/4] Stopping Frontend Server...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Frontend Server*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo    - Frontend stopped

:: Hỏi có muốn dừng Ollama không
echo.
echo [3/4] Ollama Service
set /p stop_ollama="Do you want to stop Ollama? (y/n): "
if /i "%stop_ollama%"=="y" (
    echo    - Stopping Ollama...
    taskkill /F /FI "WINDOWTITLE eq Ollama Service*" >nul 2>&1
    taskkill /F /IM ollama.exe >nul 2>&1
    echo    - Ollama stopped
) else (
    echo    - Keeping Ollama running
)

echo.
echo [4/4] Cleanup completed!
echo.
echo ========================================
echo   All services have been stopped
echo ========================================
echo.
pause
'@

Create-BatchFile "stop.bat" $stopContent

# quick-restart.bat
$quickRestartContent = @'
@echo off
echo ========================================
echo   RAG Chatbot - Quick Restart
echo ========================================
echo.
echo Select service to restart:
echo [1] Backend only
echo [2] Frontend only
echo [3] Both Backend and Frontend
echo [4] Cancel
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto restart_backend
if "%choice%"=="2" goto restart_frontend
if "%choice%"=="3" goto restart_both
if "%choice%"=="4" goto end

:restart_backend
echo.
echo Restarting Backend...
:: Kill backend
taskkill /F /IM uvicorn.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
:: Start backend
cd backend
start "Backend Server" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"
cd ..
echo Backend restarted successfully!
goto end

:restart_frontend
echo.
echo Restarting Frontend...
:: Kill frontend
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Frontend Server*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
:: Start frontend
cd frontend
start "Frontend Server" cmd /k "npm start"
cd ..
echo Frontend restarted successfully!
goto end

:restart_both
echo.
call restart.bat
goto end

:end
echo.
pause
'@

Create-BatchFile "quick-restart.bat" $quickRestartContent

# check-status.bat
$checkStatusContent = @'
@echo off
echo ========================================
echo   RAG Chatbot - Service Status Check
echo ========================================
echo.

:: Check Ollama
echo [1/3] Checking Ollama...
ollama list >nul 2>&1
if errorlevel 1 (
    echo    - Status: NOT RUNNING
    echo    - Run 'ollama serve' to start
) else (
    echo    - Status: RUNNING
    echo    - Available at http://localhost:11434
    echo    - Models:
    ollama list 2>nul | findstr /v "NAME" | findstr /v "^$"
)

echo.

:: Check Backend
echo [2/3] Checking Backend...
netstat -an | findstr :8000 | findstr LISTENING >nul
if errorlevel 1 (
    echo    - Status: NOT RUNNING
    echo    - Port 8000 is not listening
) else (
    echo    - Status: RUNNING
    echo    - Available at http://localhost:8000
    :: Try to check health endpoint
    curl -s http://localhost:8000/chat/health >nul 2>&1
    if not errorlevel 1 (
        echo    - API Health: OK
    ) else (
        echo    - API Health: Cannot connect
    )
)

echo.

:: Check Frontend
echo [3/3] Checking Frontend...
netstat -an | findstr :3000 | findstr LISTENING >nul
if errorlevel 1 (
    echo    - Status: NOT RUNNING
    echo    - Port 3000 is not listening
) else (
    echo    - Status: RUNNING
    echo    - Available at http://localhost:3000
)

echo.
echo ========================================
echo   Press any key to exit
echo ========================================
pause >nul
'@

Create-BatchFile "check-status.bat" $checkStatusContent

# dev-mode.bat
$devModeContent = @'
@echo off
echo ========================================
echo   RAG Chatbot - Development Mode
echo ========================================
echo.

:: Tùy chọn cho developer
echo Select development options:
echo.

:: Backend options
set /p backend_debug="Enable backend debug mode? (y/n): "
set backend_args=--reload --host 0.0.0.0 --port 8000
if /i "%backend_debug%"=="y" (
    set backend_args=%backend_args% --log-level debug
)

:: Frontend options
set /p frontend_debug="Open React DevTools? (y/n): "

:: Database reset option
set /p reset_db="Reset database? (y/n): "
if /i "%reset_db%"=="y" (
    echo.
    echo WARNING: This will delete all data!
    set /p confirm="Are you sure? Type 'yes' to confirm: "
    if /i "%confirm%"=="yes" (
        echo Resetting database...
        cd backend
        python -c "from database import reset_database; reset_database()"
        cd ..
    )
)

echo.
echo Starting services with development settings...
echo.

:: Start Ollama if needed
ollama list >nul 2>&1
if errorlevel 1 (
    start "Ollama Service" cmd /k ollama serve
    timeout /t 5 /nobreak >nul
)

:: Start Backend with options
echo Starting Backend with: %backend_args%
cd backend
start "Backend Server - DEV" cmd /k "uvicorn main:app %backend_args%"
cd ..

timeout /t 3 /nobreak >nul

:: Start Frontend
echo Starting Frontend...
cd frontend
if /i "%frontend_debug%"=="y" (
    start "Frontend Server - DEV" cmd /k "set REACT_APP_DEBUG=true && npm start"
) else (
    start "Frontend Server - DEV" cmd /k "npm start"
)
cd ..

echo.
echo ========================================
echo   Development Mode Active
echo ========================================
echo.
echo Services:
echo - Backend:  http://localhost:8000 (with auto-reload)
echo - Frontend: http://localhost:3000 (with hot-reload)
echo - API Docs: http://localhost:8000/docs
echo.
echo Useful commands:
echo - Press 'R' in backend terminal to manually reload
echo - Check http://localhost:8000/docs for API documentation
echo - Backend logs are in debug mode: %backend_debug%
echo.
pause
'@

Create-BatchFile "dev-mode.bat" $devModeContent

# Tạo thêm các file khác...
Write-Host ""
Write-Host "Basic batch files created successfully!"
Write-Host ""
Write-Host "To create all files including advanced ones,"
Write-Host "please use the content from the artifact above."
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Run 'setup.bat' for initial configuration"
Write-Host "2. Use 'start.bat' to launch the application"
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
pause