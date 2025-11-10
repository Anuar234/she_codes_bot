"""Script to test configuration and setup."""

import sys
from pathlib import Path


def check_env_file():
    """Check if .env file exists and has required variables."""
    env_file = Path(".env")

    if not env_file.exists():
        print("❌ .env file not found!")
        print("   Please copy .env.example to .env and fill in your values")
        return False

    required_vars = ["BOT_TOKEN", "CHAT_ID", "OPERATOR_IDS"]
    placeholder_values = ["YOUR_BOT_TOKEN_HERE", "YOUR_CHAT_ID_HERE", "YOUR_OPERATOR_ID_HERE"]

    with open(env_file, "r") as f:
        content = f.read()

    missing = []
    not_configured = []

    for var in required_vars:
        if var not in content:
            missing.append(var)
        else:
            # Check if still has placeholder
            for line in content.split("\n"):
                if line.startswith(var):
                    value = line.split("=", 1)[1].strip()
                    if any(placeholder in value for placeholder in placeholder_values):
                        not_configured.append(var)

    if missing:
        print(f"❌ Missing variables in .env: {', '.join(missing)}")
        return False

    if not_configured:
        print(f"⚠️  Please configure these variables in .env: {', '.join(not_configured)}")
        return False

    print("✅ .env file is properly configured")
    return True


def check_data_directory():
    """Check if data directory exists."""
    data_dir = Path("data")

    if not data_dir.exists():
        print("⚠️  data/ directory not found, creating...")
        data_dir.mkdir()
        print("✅ data/ directory created")
    else:
        print("✅ data/ directory exists")

    tasks_file = data_dir / "tasks.json"
    if not tasks_file.exists():
        print("❌ data/tasks.json not found!")
        return False

    print("✅ data/tasks.json exists")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    required_packages = ["aiogram", "dotenv", "apscheduler"]
    missing = []

    for package in required_packages:
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} is not installed")

    if missing:
        print("\n⚠️  Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False

    return True


def test_config_import():
    """Test if config can be imported."""
    try:
        from config import Config
        Config.validate()
        print("✅ Configuration loaded and validated successfully")
        print(f"   Bot will send tasks at: {', '.join(Config.TASK_SCHEDULE_TIMES)}")
        print(f"   Week ends on day {Config.WEEK_END_DAY} at {Config.WEEK_END_TIME}")
        return True
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False


def main():
    """Run all checks."""
    print("🔍 Checking ChatQuestBot configuration...\n")

    checks = [
        ("Environment file", check_env_file),
        ("Data directory", check_data_directory),
        ("Dependencies", check_dependencies),
        ("Configuration", test_config_import),
    ]

    all_passed = True

    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        if not check_func():
            all_passed = False

    print("\n" + "="*50)

    if all_passed:
        print("✅ All checks passed! You can now run:")
        print("   python main.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()