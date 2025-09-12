#!/usr/bin/env python3
"""
Integration Test Runner for Employee Check-in System

This script runs the comprehensive integration tests that validate:
- Complete user workflow from login to check-out
- Mock Google OAuth responses for testing authentication flow
- Database transaction testing with rollback scenarios
- End-to-end tests for attendance history display and data consistency
- Session persistence across browser refresh and navigation
- Validation of all error scenarios with proper user feedback

Usage:
    python run_integration_tests.py
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0, result.stdout, result.stderr
    
    except subprocess.TimeoutExpired:
        print("ERROR: Test execution timed out after 5 minutes")
        return False, "", "Timeout"
    except Exception as e:
        print(f"ERROR: Failed to run command: {e}")
        return False, "", str(e)

def main():
    """Main test runner function"""
    print("Employee Check-in System - Integration Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Check if pytest is available
    success, _, _ = run_command("python -m pytest --version", "Checking pytest availability")
    if not success:
        print("ERROR: pytest is not available. Please install it with: pip install pytest")
        return 1
    
    # Test categories to run
    test_categories = [
        {
            'name': 'Complete User Workflow Tests',
            'command': 'python -m pytest test_integration_end_to_end.py::TestCompleteUserWorkflow -v',
            'description': 'Tests complete user journey from login through check-in to check-out'
        },
        {
            'name': 'OAuth Integration Tests',
            'command': 'python -m pytest test_integration_end_to_end.py::TestMockGoogleOAuthResponses -v',
            'description': 'Tests Google OAuth authentication flow with various scenarios'
        },
        {
            'name': 'Database Transaction Tests',
            'command': 'python -m pytest test_integration_end_to_end.py::TestDatabaseTransactionTesting -v',
            'description': 'Tests database consistency and rollback scenarios'
        },
        {
            'name': 'Session Persistence Tests',
            'command': 'python -m pytest test_integration_end_to_end.py::TestSessionPersistence -v',
            'description': 'Tests session management across browser interactions'
        },
        {
            'name': 'Error Scenario Validation Tests',
            'command': 'python -m pytest test_integration_end_to_end.py::TestErrorScenarioValidation -v',
            'description': 'Tests error handling and user feedback scenarios'
        },
        {
            'name': 'Data Consistency Tests',
            'command': 'python -m pytest test_integration_end_to_end.py::TestDataConsistencyValidation -v',
            'description': 'Tests data integrity and consistency validation'
        }
    ]
    
    # Run all test categories
    results = []
    total_tests = 0
    passed_tests = 0
    
    for category in test_categories:
        success, stdout, stderr = run_command(category['command'], category['description'])
        results.append({
            'name': category['name'],
            'success': success,
            'stdout': stdout,
            'stderr': stderr
        })
        
        # Parse test results from pytest output
        if success and 'passed' in stdout:
            try:
                # Extract test counts from pytest output
                lines = stdout.split('\n')
                for line in lines:
                    if 'passed' in line and ('failed' in line or 'error' in line or line.strip().endswith('passed')):
                        # Parse line like "6 passed in 1.23s" or "5 passed, 1 failed in 2.34s"
                        parts = line.strip().split()
                        for i, part in enumerate(parts):
                            if part == 'passed':
                                if i > 0 and parts[i-1].isdigit():
                                    passed_tests += int(parts[i-1])
                            elif 'passed' in part and part != 'passed':
                                # Handle cases like "20 passed"
                                num = ''.join(filter(str.isdigit, part))
                                if num:
                                    passed_tests += int(num)
                        break
            except:
                pass  # If parsing fails, continue
    
    # Run complete test suite
    print(f"\n{'='*80}")
    print("Running Complete Integration Test Suite")
    print(f"{'='*80}")
    
    success, stdout, stderr = run_command(
        'python -m pytest test_integration_end_to_end.py -v --tb=short',
        'Complete integration test suite'
    )
    
    # Parse final results
    if success and stdout:
        lines = stdout.split('\n')
        for line in lines:
            if 'passed' in line and 'in' in line:
                try:
                    parts = line.strip().split()
                    for i, part in enumerate(parts):
                        if part == 'passed':
                            if i > 0 and parts[i-1].isdigit():
                                total_tests = int(parts[i-1])
                                break
                except:
                    pass
                break
    
    # Print summary
    print(f"\n{'='*80}")
    print("INTEGRATION TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Execution completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for result in results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"{status} - {result['name']}")
    
    print()
    print(f"Total Integration Tests: {total_tests}")
    print(f"Overall Status: {'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
    
    if success:
        print()
        print("🎉 Integration test validation complete!")
        print("All requirements have been validated:")
        print("  ✅ Complete user workflow from login to check-out")
        print("  ✅ Mock Google OAuth responses for authentication testing")
        print("  ✅ Database transaction testing with rollback scenarios")
        print("  ✅ End-to-end attendance history display and data consistency")
        print("  ✅ Session persistence across browser refresh and navigation")
        print("  ✅ Error scenario validation with proper user feedback")
        return 0
    else:
        print()
        print("❌ Some integration tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())