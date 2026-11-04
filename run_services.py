"""
Run DataVault services with PostgreSQL databases
This script starts all services in the background
"""
import subprocess
import sys
import time
import os
import signal

def start_service(name, script_path, env_vars=None):
    """Start a service in the background"""
    print(f"Starting {name}...")
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    try:
        process = subprocess.Popen(
            [sys.executable, script_path],
            cwd=os.path.dirname(script_path),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"{name} started with PID {process.pid}")
        return process
    except Exception as e:
        print(f"Failed to start {name}: {e}")
        return None

def main():
    print("=" * 70)
    print("Starting DataVault Services")
    print("=" * 70)

    processes = []

    # Set environment variables for database connections
    operator_env = {
        "DATABASE_URL": "postgresql://datavault:datavault_operator_password@localhost:5436/datavault_operator",
        "JWT_SECRET_KEY": "operator_secret_key_change_in_production",
        "JWT_ALGORITHM": "HS256"
    }

    backend_env = {
        "DATABASE_URL": "postgresql://datavault:datavault_backend_password@localhost:5437/datavault_backend",
        "REDIS_URL": "redis://localhost:6381/1",
        "OPERATOR_API_URL": "http://localhost:8001",
        "JWT_SECRET_KEY": "datavault_secret_key_change_in_production",
        "JWT_ALGORITHM": "HS256"
    }

    device_env = {
        "DATAVAULT_BACKEND_URL": "http://localhost:8000",
        "DEVICE_ID": "DV-001-ABCD"
    }

    # Start Simulated Operator API
    operator_process = start_service(
        "Simulated Operator API",
        "mode_a_simulated_operator/operator_api/main.py",
        operator_env
    )
    if operator_process:
        processes.append(("Operator API", operator_process))

    time.sleep(3)

    # Start DataVault Backend API
    backend_process = start_service(
        "DataVault Backend API",
        "backend/api/main.py",
        backend_env
    )
    if backend_process:
        processes.append(("Backend API", backend_process))

    time.sleep(3)

    # Start Device Simulator
    device_process = start_service(
        "Device Simulator",
        "device_simulator/main.py",
        device_env
    )
    if device_process:
        processes.append(("Device Simulator", device_process))

    print("\n" + "=" * 70)
    print("All services started!")
    print("=" * 70)
    print("\nServices running:")
    for name, process in processes:
        print(f"  - {name}: PID {process.pid}")
    print("\nPress Ctrl+C to stop all services")

    try:
        # Keep script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping services...")
        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("All services stopped")

if __name__ == "__main__":
    main()
