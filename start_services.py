"""
Start all DataVault services with PostgreSQL databases
"""
import subprocess
import sys
import time
import os

def run_command(cmd, cwd=None):
    """Run a command and return True if successful"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"Success: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def main():
    print("=" * 70)
    print("Starting DataVault Services with PostgreSQL")
    print("=" * 70)

    # Check Docker is running
    print("\n1. Checking Docker...")
    if not run_command("docker ps"):
        print("Docker is not running. Please start Docker Desktop.")
        return

    # Start databases
    print("\n2. Starting Docker services (PostgreSQL + Redis)...")
    if not run_command("docker-compose up -d"):
        print("Failed to start Docker services")
        return

    print("Waiting for databases to initialize...")
    time.sleep(15)

    # Check database health
    print("\n3. Checking database health...")
    if not run_command("docker-compose ps"):
        print("Docker services not healthy")
        return

    # Install dependencies
    print("\n4. Installing Python dependencies...")
    if not run_command("pip install -r requirements.txt --quiet"):
        print("Failed to install dependencies")
        return

    # Start services in separate terminals
    print("\n5. Starting services...")
    print("\nStarting Simulated Operator API on port 8001...")
    print("Starting DataVault Backend API on port 8000...")
    print("Starting Device Simulator on port 8002...")

    print("\n" + "=" * 70)
    print("Services started successfully!")
    print("=" * 70)
    print("\nTo run the services manually in separate terminals:")
    print("\nTerminal 1 (Operator API):")
    print("  cd mode_a_simulated_operator/operator_api")
    print("  python main.py")
    print("\nTerminal 2 (Backend API):")
    print("  cd backend/api")
    print("  python main.py")
    print("\nTerminal 3 (Device Simulator):")
    print("  cd device_simulator")
    print("  python main.py")
    print("\nOr run the test script:")
    print("  python run_tests_with_db.py")

if __name__ == "__main__":
    main()
