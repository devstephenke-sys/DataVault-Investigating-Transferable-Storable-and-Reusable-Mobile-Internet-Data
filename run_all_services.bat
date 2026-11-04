@echo off
echo Starting DataVault Services with PostgreSQL
echo ============================================

echo.
echo Starting Simulated Operator API on port 8001...
start "Operator API" cmd /k "cd mode_a_simulated_operator\operator_api && set DATABASE_URL=postgresql://datavault:datavault_operator_password@localhost:5436/datavault_operator && set JWT_SECRET_KEY=operator_secret_key_change_in_production && set JWT_ALGORITHM=HS256 && python main.py"

timeout /t 5 /nobreak

echo.
echo Starting DataVault Backend API on port 8000...
start "Backend API" cmd /k "cd backend\api && set DATABASE_URL=postgresql://datavault:datavault_backend_password@localhost:5437/datavault_backend && set REDIS_URL=redis://localhost:6381/1 && set OPERATOR_API_URL=http://localhost:8001 && set JWT_SECRET_KEY=datavault_secret_key_change_in_production && set JWT_ALGORITHM=HS256 && python main.py"

timeout /t 5 /nobreak

echo.
echo Starting Device Simulator on port 8002...
start "Device Simulator" cmd /k "cd device_simulator && set DATAVAULT_BACKEND_URL=http://localhost:8000 && set DEVICE_ID=DV-001-ABCD && python main.py"

timeout /t 5 /nobreak

echo.
echo ============================================
echo All services started!
echo ============================================
echo.
echo Services running in separate windows:
echo   - Operator API: http://localhost:8001
echo   - Backend API: http://localhost:8000
echo   - Device Simulator: http://localhost:8002
echo.
echo Press any key to run the database tests...
pause >nul

echo.
echo Running database tests...
python run_tests_with_db.py

pause
