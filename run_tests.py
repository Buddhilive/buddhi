#!/usr/bin/env python3
"""
Test runner script for Buddhi AI FastAPI backend
"""
import subprocess
import sys
import os
from pathlib import Path


def run_tests():
    """Run the test suite"""
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🧪 Running Buddhi AI Backend Tests")
    print("=" * 50)
    
    # Use the virtual environment python
    python_exe = project_root / ".venv" / "Scripts" / "python.exe"
    cmd = [str(python_exe), "-m", "pytest", "tests/", "-v"]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Please install testing dependencies:")
        print("pip install pytest pytest-asyncio httpx")
        return 1


def run_tests_with_coverage():
    """Run tests with coverage report"""
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🧪 Running Tests with Coverage")
    print("=" * 50)
    
    # Use the virtual environment python
    python_exe = project_root / ".venv" / "Scripts" / "python.exe"
    
    # Install pytest-cov if needed
    try:
        import pytest_cov  # type: ignore
    except ImportError:
        print("Installing pytest-cov...")
        subprocess.run([str(python_exe), "-m", "pip", "install", "pytest-cov"])
    
    cmd = [
        str(python_exe), "-m", "pytest", 
        "tests/", 
        "-v",
        "--cov=backend",
        "--cov-report=html",
        "--cov-report=term-missing"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print("\n✅ Coverage report generated in htmlcov/index.html")
        return result.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Please install testing dependencies.")
        return 1


def run_specific_test_category(category):
    """Run specific category of tests"""
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"🧪 Running {category} tests")
    print("=" * 50)
    
    # Use the virtual environment python
    python_exe = project_root / ".venv" / "Scripts" / "python.exe"
    cmd = [str(python_exe), "-m", "pytest", "tests/", "-v", "-m", category]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("❌ pytest not found.")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "coverage":
            exit_code = run_tests_with_coverage()
        elif sys.argv[1] in ["auth", "database", "integration", "unit"]:
            exit_code = run_specific_test_category(sys.argv[1])
        else:
            print("Usage: python run_tests.py [coverage|auth|database|integration|unit]")
            exit_code = 1
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)
