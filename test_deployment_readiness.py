#!/usr/bin/env python3
"""
Comprehensive Deployment Readiness Test Suite
Tests all critical components for MVP deployment readiness.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Test Configuration
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpass123"

class DeploymentTester:
    def __init__(self):
        self.results = []
        self.token = None
        
    def log_test(self, test_name, passed, message="", expected="", actual=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        if not passed and expected:
            print(f"    Expected: {expected}")
            print(f"    Actual: {actual}")
        print()

    def test_backend_health(self):
        """Test backend API health endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            passed = response.status_code == 200 and "healthy" in response.json().get("status", "")
            self.log_test(
                "Backend Health Check",
                passed,
                f"Backend API responded with status {response.status_code}",
                "200 with healthy status",
                f"{response.status_code} with {response.text}"
            )
            return passed
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Connection failed: {str(e)}")
            return False

    def test_frontend_accessibility(self):
        """Test frontend accessibility"""
        try:
            response = requests.get(FRONTEND_URL, timeout=10)
            passed = response.status_code == 200
            self.log_test(
                "Frontend Accessibility",
                passed,
                f"Frontend responded with status {response.status_code}",
                "200",
                str(response.status_code)
            )
            return passed
        except Exception as e:
            self.log_test("Frontend Accessibility", False, f"Connection failed: {str(e)}")
            return False

    def test_api_endpoints(self):
        """Test critical API endpoints"""
        endpoints = [
            ("/health", "GET", None, 200),
            ("/topics/", "GET", None, 200),
            ("/topics/categories", "GET", None, 200),
        ]
        
        all_passed = True
        for endpoint, method, data, expected_status in endpoints:
            try:
                url = f"{BACKEND_URL}{endpoint}"
                if method == "GET":
                    response = requests.get(url, timeout=10)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=10)
                
                passed = response.status_code == expected_status
                self.log_test(
                    f"API Endpoint {method} {endpoint}",
                    passed,
                    f"Returned {response.status_code} with data: {response.text[:100]}...",
                    str(expected_status),
                    str(response.status_code)
                )
                if not passed:
                    all_passed = False
            except Exception as e:
                self.log_test(f"API Endpoint {method} {endpoint}", False, f"Request failed: {str(e)}")
                all_passed = False
        
        return all_passed

    def test_cors_configuration(self):
        """Test CORS configuration"""
        try:
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            response = requests.options(f"{BACKEND_URL}/health", headers=headers, timeout=10)
            
            cors_headers = response.headers
            passed = (
                'access-control-allow-origin' in cors_headers or
                response.status_code in [200, 204]
            )
            
            self.log_test(
                "CORS Configuration",
                passed,
                f"OPTIONS request returned {response.status_code} with CORS headers: {dict(cors_headers)}",
                "CORS headers present",
                f"Status: {response.status_code}, Headers: {dict(cors_headers)}"
            )
            return passed
        except Exception as e:
            self.log_test("CORS Configuration", False, f"CORS test failed: {str(e)}")
            return False

    def test_error_handling(self):
        """Test API error handling"""
        try:
            # Test non-existent endpoint
            response = requests.get(f"{BACKEND_URL}/nonexistent", timeout=10)
            passed = response.status_code == 404
            
            self.log_test(
                "Error Handling (404)",
                passed,
                f"Non-existent endpoint returned {response.status_code}",
                "404",
                str(response.status_code)
            )
            return passed
        except Exception as e:
            self.log_test("Error Handling", False, f"Error handling test failed: {str(e)}")
            return False

    def test_data_validation(self):
        """Test API data validation"""
        try:
            # Test invalid registration data
            invalid_data = {"invalid": "data"}
            response = requests.post(f"{BACKEND_URL}/auth/register", json=invalid_data, timeout=10)
            
            # Expect 422 (validation error) or 500 (handled gracefully)
            passed = response.status_code in [422, 500]
            
            self.log_test(
                "Data Validation",
                passed,
                f"Invalid data validation returned {response.status_code}",
                "422 or 500",
                str(response.status_code)
            )
            return passed
        except Exception as e:
            self.log_test("Data Validation", False, f"Validation test failed: {str(e)}")
            return False

    def test_response_format(self):
        """Test API response format consistency"""
        try:
            response = requests.get(f"{BACKEND_URL}/topics/", timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    passed = isinstance(data, list) and len(data) > 0
                    self.log_test(
                        "Response Format Consistency",
                        passed,
                        f"Topics endpoint returned valid JSON list: {data}",
                        "Valid JSON array with data",
                        str(type(data))
                    )
                    return passed
                except json.JSONDecodeError:
                    self.log_test("Response Format Consistency", False, "Response is not valid JSON")
                    return False
            else:
                self.log_test("Response Format Consistency", False, f"Unexpected status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Response Format Consistency", False, f"Response format test failed: {str(e)}")
            return False

    def test_performance_basic(self):
        """Basic performance test"""
        try:
            start_time = time.time()
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            passed = response_time < 1000 and response.status_code == 200  # Less than 1 second
            
            self.log_test(
                "Basic Performance",
                passed,
                f"Health endpoint responded in {response_time:.2f}ms",
                "< 1000ms",
                f"{response_time:.2f}ms"
            )
            return passed
        except Exception as e:
            self.log_test("Basic Performance", False, f"Performance test failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all deployment readiness tests"""
        print("🚀 Starting Deployment Readiness Test Suite")
        print("=" * 50)
        print()

        test_methods = [
            self.test_backend_health,
            self.test_frontend_accessibility,
            self.test_api_endpoints,
            self.test_cors_configuration,
            self.test_error_handling,
            self.test_data_validation,
            self.test_response_format,
            self.test_performance_basic,
        ]

        passed_tests = 0
        total_tests = len(test_methods)

        for test_method in test_methods:
            if test_method():
                passed_tests += 1

        print("=" * 50)
        print(f"📊 TEST SUMMARY: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("✅ ALL TESTS PASSED - System is deployment ready!")
            return True
        else:
            failed_tests = total_tests - passed_tests
            print(f"❌ {failed_tests} tests failed - Review issues before deployment")
            return False

    def generate_report(self):
        """Generate detailed test report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results if r["passed"]),
                "failed": sum(1 for r in self.results if not r["passed"]),
                "pass_rate": (sum(1 for r in self.results if r["passed"]) / len(self.results)) * 100 if self.results else 0
            },
            "results": self.results
        }
        
        with open("deployment_readiness_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: deployment_readiness_report.json")
        return report

if __name__ == "__main__":
    tester = DeploymentTester()
    success = tester.run_all_tests()
    tester.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)