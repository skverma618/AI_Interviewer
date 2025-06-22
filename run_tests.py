"""
Test runner for AI Voice Interviewer System
Run all tests with: python run_tests.py
"""
import unittest
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def run_all_tests():
    """Discover and run all tests"""
    # Discover tests in the tests directory
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

def run_specific_test(test_module):
    """Run a specific test module"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(f'tests.{test_module}')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("🧪 AI Voice Interviewer System - Test Suite")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Run specific test
        test_module = sys.argv[1]
        print(f"Running specific test: {test_module}")
        success = run_specific_test(test_module)
    else:
        # Run all tests
        print("Running all tests...")
        success = run_all_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)