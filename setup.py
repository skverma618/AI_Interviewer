"""
Setup script for AI Voice Interviewer System
"""
import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "logs/sessions"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")

def check_env_file():
    """Check if .env file exists and has required keys"""
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        print("Please create a .env file with your API keys:")
        print("DEEPGRAM_API_KEY=your_deepgram_api_key_here")
        print("OPENAI_API_KEY=your_openai_api_key_here")
        return False
    
    with open(".env", "r") as f:
        content = f.read()
    
    required_keys = ["DEEPGRAM_API_KEY", "OPENAI_API_KEY"]
    missing_keys = []
    
    for key in required_keys:
        if key not in content or f"{key}=your_" in content:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Missing or placeholder API keys: {', '.join(missing_keys)}")
        print("Please update your .env file with actual API keys")
        return False
    
    print("✅ .env file configured")
    return True

def run_basic_test():
    """Run basic system test"""
    print("🧪 Running basic system test...")
    try:
        # Import main modules to check for import errors
        sys.path.append('src')
        from question_manager import QuestionManager
        from config import Config
        
        # Test question manager
        qm = QuestionManager()
        if len(qm.questions) > 0:
            print("✅ Question bank loaded successfully")
        else:
            print("❌ Question bank is empty")
            return False
        
        # Test configuration
        if Config.validate_config():
            print("✅ Configuration validation passed")
        else:
            print("❌ Configuration validation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🤖 AI Voice Interviewer System - Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Check environment file
    env_ok = check_env_file()
    
    # Run basic test
    if env_ok:
        test_ok = run_basic_test()
    else:
        test_ok = False
    
    print("\n" + "=" * 50)
    print("📋 SETUP SUMMARY")
    print("=" * 50)
    
    if env_ok and test_ok:
        print("✅ Setup completed successfully!")
        print("\n🚀 You can now run the system with:")
        print("   python main.py")
        print("\n🧪 Or run tests with:")
        print("   python run_tests.py")
        return True
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        if not env_ok:
            print("\n📝 Next steps:")
            print("1. Get API keys from:")
            print("   - Deepgram: https://deepgram.com/")
            print("   - OpenAI: https://platform.openai.com/")
            print("2. Update your .env file with the actual API keys")
            print("3. Run setup.py again")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)