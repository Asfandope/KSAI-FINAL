#!/usr/bin/env python3
"""
Final MVP Deployment Readiness Audit
Comprehensive assessment of system readiness for production deployment.
"""

import requests
import json
import sys
import subprocess
import os
from datetime import datetime
from pathlib import Path

# Test Configuration
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
PROJECT_ROOT = "/Users/asfandope/ks-ai-final/ks-ai-platform"

class DeploymentAuditor:
    def __init__(self):
        self.results = []
        self.critical_issues = []
        self.warnings = []
        self.recommendations = []
        
    def log_test(self, category, test_name, passed, message="", expected="", actual="", critical=False):
        status = "✅ PASS" if passed else ("🔥 CRITICAL" if critical else "❌ FAIL")
        result = {
            "category": category,
            "test": test_name,
            "passed": passed,
            "critical": critical,
            "message": message,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        print(f"{status}: [{category}] {test_name}")
        if message:
            print(f"    {message}")
        if not passed and expected:
            print(f"    Expected: {expected}")
            print(f"    Actual: {actual}")
        print()
        
        if not passed:
            if critical:
                self.critical_issues.append(result)
            else:
                self.warnings.append(result)

    def test_core_infrastructure(self):
        """Test core infrastructure components"""
        print("🏗️  Testing Core Infrastructure")
        print("-" * 40)
        
        # Test backend health
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            passed = response.status_code == 200 and "healthy" in response.json().get("status", "")
            self.log_test(
                "Infrastructure", 
                "Backend API Health",
                passed,
                f"API health endpoint returned: {response.text}",
                "200 with healthy status",
                f"{response.status_code} with {response.text}",
                critical=True
            )
        except Exception as e:
            self.log_test("Infrastructure", "Backend API Health", False, f"Failed: {str(e)}", critical=True)

        # Test frontend accessibility
        try:
            response = requests.get(FRONTEND_URL, timeout=10)
            passed = response.status_code == 200
            self.log_test(
                "Infrastructure",
                "Frontend Accessibility",
                passed,
                f"Frontend UI is accessible at {FRONTEND_URL}",
                "200",
                str(response.status_code),
                critical=True
            )
        except Exception as e:
            self.log_test("Infrastructure", "Frontend Accessibility", False, f"Failed: {str(e)}", critical=True)

        # Test Qdrant vector database
        try:
            response = requests.get("http://localhost:6333/collections", timeout=10)
            if response.status_code == 200:
                collections = response.json().get("result", {}).get("collections", [])
                passed = True
                self.log_test(
                    "Infrastructure",
                    "Vector Database (Qdrant)",
                    passed,
                    f"Qdrant is running with {len(collections)} collections: {[c.get('name') for c in collections]}",
                    "Qdrant accessible",
                    f"200 with {len(collections)} collections"
                )
            else:
                self.log_test("Infrastructure", "Vector Database (Qdrant)", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Infrastructure", "Vector Database (Qdrant)", False, f"Failed: {str(e)}")

    def test_api_functionality(self):
        """Test API endpoints and functionality"""
        print("🔌 Testing API Functionality")
        print("-" * 40)
        
        # Test core API endpoints
        endpoints = [
            ("/health", "Health Check", True),
            ("/topics/", "Topic List", True),
            ("/topics/categories", "Category List", True),
        ]
        
        for endpoint, name, critical in endpoints:
            try:
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                passed = response.status_code == 200
                
                if passed and endpoint in ["/topics/", "/topics/categories"]:
                    data = response.json()
                    passed = isinstance(data, list) and len(data) > 0
                    
                self.log_test(
                    "API",
                    name,
                    passed,
                    f"Endpoint {endpoint} returned: {response.text[:100]}...",
                    "200 with valid data",
                    f"{response.status_code}",
                    critical=critical
                )
            except Exception as e:
                self.log_test("API", name, False, f"Failed: {str(e)}", critical=critical)

        # Test CORS configuration
        try:
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            response = requests.options(f"{BACKEND_URL}/health", headers=headers, timeout=10)
            passed = 'access-control-allow-origin' in response.headers or response.status_code in [200, 204]
            
            self.log_test(
                "API",
                "CORS Configuration",
                passed,
                f"CORS headers present: {response.headers.get('access-control-allow-origin', 'None')}",
                "CORS properly configured",
                f"Status {response.status_code}"
            )
        except Exception as e:
            self.log_test("API", "CORS Configuration", False, f"Failed: {str(e)}")

    def test_frontend_build(self):
        """Test frontend build system"""
        print("🎨 Testing Frontend Build System")
        print("-" * 40)
        
        try:
            # Test if we can build the frontend
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=f"{PROJECT_ROOT}/apps/web",
                capture_output=True,
                text=True,
                timeout=120
            )
            
            passed = result.returncode == 0
            message = "Frontend builds successfully for production" if passed else f"Build failed: {result.stderr[:200]}..."
            
            self.log_test(
                "Frontend",
                "Production Build",
                passed,
                message,
                "Build succeeds",
                f"Exit code: {result.returncode}",
                critical=True
            )
            
        except subprocess.TimeoutExpired:
            self.log_test("Frontend", "Production Build", False, "Build timed out after 2 minutes", critical=True)
        except Exception as e:
            self.log_test("Frontend", "Production Build", False, f"Build test failed: {str(e)}", critical=True)

    def test_code_quality(self):
        """Test code quality metrics"""
        print("📋 Testing Code Quality")
        print("-" * 40)
        
        # Test frontend linting
        try:
            result = subprocess.run(
                ["npm", "run", "lint"],
                cwd=f"{PROJECT_ROOT}/apps/web",
                capture_output=True,
                text=True,
                timeout=60
            )
            
            passed = result.returncode == 0
            self.log_test(
                "Code Quality",
                "Frontend Linting",
                passed,
                "ESLint passes without errors" if passed else f"Linting issues: {result.stdout[:200]}",
                "No lint errors",
                f"Exit code: {result.returncode}"
            )
            
        except Exception as e:
            self.log_test("Code Quality", "Frontend Linting", False, f"Lint test failed: {str(e)}")

        # Test backend linting (Python)
        try:
            result = subprocess.run(
                ["flake8", "."],
                cwd=f"{PROJECT_ROOT}/apps/api",
                capture_output=True,
                text=True,
                timeout=60
            )
            
            passed = result.returncode == 0
            self.log_test(
                "Code Quality",
                "Backend Linting (Python)",
                passed,
                "Python code passes flake8 checks" if passed else f"Linting issues: {result.stdout[:200]}",
                "No lint errors",
                f"Exit code: {result.returncode}"
            )
            
        except Exception as e:
            self.log_test("Code Quality", "Backend Linting (Python)", False, f"Lint test failed: {str(e)}")

    def test_configuration_readiness(self):
        """Test configuration and deployment readiness"""
        print("⚙️  Testing Configuration Readiness")
        print("-" * 40)
        
        # Check if necessary config files exist
        config_files = [
            ("Frontend", "package.json", f"{PROJECT_ROOT}/apps/web/package.json"),
            ("Frontend", "Next Config", f"{PROJECT_ROOT}/apps/web/next.config.js"),
            ("Backend", "Requirements", f"{PROJECT_ROOT}/apps/api/requirements.txt"),
            ("Docker", "Compose Config", f"{PROJECT_ROOT}/docker-compose.yml"),
            ("Database", "Init Script", f"{PROJECT_ROOT}/scripts/init.sql"),
        ]
        
        for category, name, file_path in config_files:
            exists = os.path.exists(file_path)
            self.log_test(
                "Configuration",
                f"{name} File",
                exists,
                f"Configuration file exists: {file_path}" if exists else f"Missing: {file_path}",
                "File exists",
                "File exists" if exists else "File missing"
            )

        # Check environment configuration
        env_files = [
            ("Backend", f"{PROJECT_ROOT}/apps/api/.env"),
        ]
        
        for name, env_path in env_files:
            exists = os.path.exists(env_path)
            self.log_test(
                "Configuration",
                f"{name} Environment Config",
                exists,
                f"Environment file configured: {env_path}" if exists else f"Consider creating: {env_path}",
                "Environment configured",
                "Present" if exists else "Missing (fallback config used)"
            )

    def test_performance_basic(self):
        """Basic performance tests"""
        print("⚡ Testing Basic Performance")
        print("-" * 40)
        
        import time
        
        # Test API response time
        try:
            start_time = time.time()
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            passed = response_time < 1000 and response.status_code == 200
            
            self.log_test(
                "Performance",
                "API Response Time",
                passed,
                f"Health endpoint responds in {response_time:.2f}ms",
                "< 1000ms",
                f"{response_time:.2f}ms"
            )
        except Exception as e:
            self.log_test("Performance", "API Response Time", False, f"Performance test failed: {str(e)}")

        # Test frontend load time
        try:
            start_time = time.time()
            response = requests.get(FRONTEND_URL, timeout=10)
            end_time = time.time()
            
            load_time = (end_time - start_time) * 1000
            passed = load_time < 3000 and response.status_code == 200
            
            self.log_test(
                "Performance",
                "Frontend Load Time",
                passed,
                f"Frontend loads in {load_time:.2f}ms",
                "< 3000ms",
                f"{load_time:.2f}ms"
            )
        except Exception as e:
            self.log_test("Performance", "Frontend Load Time", False, f"Load test failed: {str(e)}")

    def generate_deployment_recommendations(self):
        """Generate deployment recommendations"""
        print("📝 Generating Deployment Recommendations")
        print("-" * 50)
        
        # Based on the test results, generate recommendations
        if len(self.critical_issues) == 0:
            print("✅ SYSTEM IS DEPLOYMENT READY!")
            print()
            print("🚀 Recommended Next Steps:")
            print("1. Deploy frontend to Vercel")
            print("2. Deploy backend to AWS EC2")
            print("3. Set up AWS RDS for PostgreSQL")
            print("4. Deploy Qdrant to cloud or self-hosted")
            print("5. Configure environment variables for production")
            print("6. Set up monitoring and logging")
            print()
        else:
            print("⚠️  CRITICAL ISSUES FOUND - MUST BE RESOLVED BEFORE DEPLOYMENT")
            print()
            for issue in self.critical_issues:
                print(f"🔥 {issue['test']}: {issue['message']}")
            print()

        if len(self.warnings) > 0:
            print("⚠️  Warnings (Recommended to address):")
            for warning in self.warnings:
                print(f"⚠️  {warning['test']}: {warning['message']}")
            print()

        # Additional recommendations
        print("💡 Additional Recommendations:")
        print("1. Set up proper environment variables for production (OPENAI_API_KEY, etc.)")
        print("2. Configure production database with proper authentication")
        print("3. Set up SSL/TLS certificates for HTTPS")
        print("4. Implement monitoring with services like Sentry or DataDog")
        print("5. Set up automated backups for databases")
        print("6. Configure CDN for static assets")
        print("7. Implement rate limiting and security headers")
        print("8. Set up CI/CD pipelines")

    def run_full_audit(self):
        """Run complete deployment readiness audit"""
        print("🔍 STARTING COMPREHENSIVE MVP DEPLOYMENT AUDIT")
        print("=" * 60)
        print()
        
        # Run all test categories
        self.test_core_infrastructure()
        self.test_api_functionality()
        self.test_frontend_build()
        self.test_code_quality()
        self.test_configuration_readiness()
        self.test_performance_basic()
        
        # Generate summary
        print("📊 AUDIT SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        critical_failures = len(self.critical_issues)
        warnings = len(self.warnings)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Critical Issues: {critical_failures}")
        print(f"Warnings: {warnings}")
        print(f"Pass Rate: {(passed_tests / total_tests) * 100:.1f}%")
        print()
        
        self.generate_deployment_recommendations()
        
        # Save detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "critical_issues": critical_failures,
                "warnings": warnings,
                "pass_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "deployment_ready": critical_failures == 0
            },
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "all_results": self.results
        }
        
        with open("final_deployment_audit.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Complete audit report saved to: final_deployment_audit.json")
        
        return critical_failures == 0

if __name__ == "__main__":
    auditor = DeploymentAuditor()
    deployment_ready = auditor.run_full_audit()
    
    # Exit with appropriate code
    sys.exit(0 if deployment_ready else 1)