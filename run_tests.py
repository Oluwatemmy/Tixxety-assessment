"""
Simple test runner for Tixxety API tests.
"""
import subprocess
import sys

def main():
    """Run all tests."""
    print("Running Tixxety API Tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/"], capture_output=False)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
