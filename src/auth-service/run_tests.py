#!/usr/bin/env python3
"""Test runner for the authentication service."""

import sys
import os
import subprocess
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


def run_tests():
    """Run all tests with pytest."""
    print("🧪 Running Authentication Service Unit Tests")
    print("📋 Tests now run Alembic migrations before each test")
    print("=" * 50)

    # Set environment variables for testing
    os.environ.update(
        {
            "TESTING": "true",
            "DATABASE_URL": "sqlite:///:memory:",
            "REDIS_URL": "redis://localhost:6379/1",
            "JWT_PRIVATE_KEY": "",
            "JWT_PUBLIC_KEY": "",
            "DEBUG": "true",
        }
    )

    # Run pytest with coverage
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--disable-warnings",  # Disable warnings for cleaner output
        "--color=yes",  # Colored output
        "--cov=app",  # Coverage for app directory
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html:htmlcov",  # Generate HTML coverage report
        "--cov-fail-under=80",  # Fail if coverage is below 80%
    ]

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)

        if result.returncode == 0:
            print("\n✅ All tests passed!")
            print("📊 Coverage report generated in htmlcov/")
            print("🗄️  Database schema was created using Alembic migrations")
        else:
            print("\n❌ Some tests failed!")

        return result.returncode

    except FileNotFoundError:
        print(
            "❌ pytest not found. Please install it with: pip install pytest pytest-cov"
        )
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def run_specific_test_file(test_file):
    """Run a specific test file."""
    print(f"🧪 Running {test_file}")
    print("📋 Tests run Alembic migrations before each test")
    print("=" * 50)

    # Set environment variables for testing
    os.environ.update(
        {
            "TESTING": "true",
            "DATABASE_URL": "sqlite:///:memory:",
            "REDIS_URL": "redis://localhost:6379/1",
            "JWT_PRIVATE_KEY": "",
            "JWT_PUBLIC_KEY": "",
            "DEBUG": "true",
        }
    )

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        f"tests/{test_file}",
        "-v",
        "--tb=short",
        "--disable-warnings",
        "--color=yes",
    ]

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)

        if result.returncode == 0:
            print(f"\n✅ {test_file} tests passed!")
            print("🗄️  Database schema was created using Alembic migrations")

        return result.returncode

    except FileNotFoundError:
        print("❌ pytest not found. Please install it with: pip install pytest")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        if not test_file.endswith(".py"):
            test_file += ".py"
        return run_specific_test_file(test_file)
    else:
        # Run all tests
        return run_tests()


if __name__ == "__main__":
    sys.exit(main())
