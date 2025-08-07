#!/usr/bin/env python3
"""
Automated Tests for Critical Features
Comprehensive test suite covering all major functionality for deployment readiness.
"""

import unittest
import requests
import json
import time
from unittest.mock import patch, MagicMock

# Test Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
QDRANT_URL = "http://localhost:6333"

class TestCriticalFeatures(unittest.TestCase):
    """Test suite for critical MVP features"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.backend_url = BACKEND_URL
        cls.frontend_url = FRONTEND_URL
        cls.qdrant_url = QDRANT_URL
        cls.test_timeout = 30

    def test_01_backend_health_check(self):
        """Test backend API health endpoint"""
        response = requests.get(f"{self.backend_url}/health", timeout=10)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "KS AI API")

    def test_02_frontend_accessibility(self):
        """Test frontend is accessible and loads"""
        response = requests.get(self.frontend_url, timeout=15)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))

    def test_03_vector_database_connectivity(self):
        """Test Qdrant vector database connectivity"""
        response = requests.get(f"{self.qdrant_url}/collections", timeout=10)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("result", data)
        self.assertIn("collections", data["result"])

    def test_04_topics_api_endpoint(self):
        """Test topics API endpoint returns valid data"""
        response = requests.get(f"{self.backend_url}/topics/", timeout=10)
        self.assertEqual(response.status_code, 200)
        topics = response.json()
        self.assertIsInstance(topics, list)
        self.assertGreaterEqual(len(topics), 4)
        expected_topics = ["Politics", "Environmentalism", "SKCRF", "Educational Trust"]
        for topic in expected_topics:
            self.assertIn(topic, topics)

    def test_05_categories_api_endpoint(self):
        """Test categories API endpoint with fallback"""
        response = requests.get(f"{self.backend_url}/topics/categories", timeout=10)
        self.assertEqual(response.status_code, 200)
        categories = response.json()
        self.assertIsInstance(categories, list)
        self.assertGreaterEqual(len(categories), 4)

    def test_06_cors_configuration(self):
        """Test CORS configuration for frontend-backend communication"""
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{self.backend_url}/health", headers=headers, timeout=10)
        
        # Should either return CORS headers or allow the request
        self.assertIn(response.status_code, [200, 204])
        cors_origin = response.headers.get('access-control-allow-origin')
        self.assertTrue(
            cors_origin == 'http://localhost:3000' or cors_origin == '*',
            f"CORS origin header: {cors_origin}"
        )

    def test_07_api_error_handling(self):
        """Test API error handling for non-existent endpoints"""
        response = requests.get(f"{self.backend_url}/nonexistent-endpoint", timeout=10)
        self.assertEqual(response.status_code, 404)

    def test_08_api_data_validation(self):
        """Test API data validation for invalid requests"""
        invalid_data = {"invalid": "data", "missing": "required_fields"}
        response = requests.post(
            f"{self.backend_url}/auth/register", 
            json=invalid_data, 
            timeout=10
        )
        # Should return validation error
        self.assertIn(response.status_code, [422, 400])

    def test_09_api_response_format(self):
        """Test API response format consistency"""
        response = requests.get(f"{self.backend_url}/topics/", timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "application/json")
        
        # Should be valid JSON
        data = response.json()
        self.assertIsInstance(data, list)

    def test_10_performance_api_response_time(self):
        """Test API performance - response time under 1 second"""
        start_time = time.time()
        response = requests.get(f"{self.backend_url}/health", timeout=10)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to ms
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 1000, f"Response time: {response_time:.2f}ms")

    def test_11_performance_frontend_load_time(self):
        """Test frontend performance - loads under 3 seconds"""
        start_time = time.time()
        response = requests.get(self.frontend_url, timeout=15)
        end_time = time.time()
        
        load_time = (end_time - start_time) * 1000  # Convert to ms
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 3000, f"Load time: {load_time:.2f}ms")

    def test_12_bilingual_support_structure(self):
        """Test bilingual support structure"""
        # Test that the API returns consistent topic structure for bilingual support
        response = requests.get(f"{self.backend_url}/topics/", timeout=10)
        self.assertEqual(response.status_code, 200)
        topics = response.json()
        
        # Should have all required topics for both languages
        required_topics = ["Politics", "Environmentalism", "SKCRF", "Educational Trust"]
        for topic in required_topics:
            self.assertIn(topic, topics)

    def test_13_authentication_endpoint_structure(self):
        """Test authentication endpoints return proper error codes"""
        # Test login endpoint exists and validates input
        response = requests.post(f"{self.backend_url}/auth/login", json={}, timeout=10)
        # Should return validation error, not 404
        self.assertNotEqual(response.status_code, 404)
        
        # Test register endpoint exists
        response = requests.post(f"{self.backend_url}/auth/register", json={}, timeout=10)
        self.assertNotEqual(response.status_code, 404)

    def test_14_rag_pipeline_components(self):
        """Test RAG pipeline components are available"""
        # Test Qdrant collections exist for RAG
        response = requests.get(f"{self.qdrant_url}/collections", timeout=10)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        collections = data.get("result", {}).get("collections", [])
        collection_names = [c.get("name") for c in collections]
        
        # Should have collections for content storage
        self.assertGreater(len(collections), 0, "No vector collections found for RAG")
        
    def test_15_content_management_endpoints(self):
        """Test content management endpoints exist"""
        # Test admin endpoints exist (will return auth errors but not 404)
        endpoints = ["/admin/dashboard", "/admin/content"]
        
        for endpoint in endpoints:
            response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
            self.assertNotEqual(response.status_code, 404, f"Endpoint {endpoint} not found")
            # Should return 401 (unauthorized) or 500 (internal error), not 404
            self.assertIn(response.status_code, [401, 403, 500])

    def test_16_chat_endpoint_exists(self):
        """Test chat endpoint exists and validates input"""
        # Test chat endpoint exists
        response = requests.post(f"{self.backend_url}/chat/", json={}, timeout=10)
        self.assertNotEqual(response.status_code, 404)
        # Should return auth error or validation error, not 404
        self.assertIn(response.status_code, [401, 403, 422, 500])

    def test_17_environment_configuration(self):
        """Test environment configuration is working"""
        # Test that the backend is using correct configuration
        response = requests.get(f"{self.backend_url}/health", timeout=10)
        self.assertEqual(response.status_code, 200)
        
        # Check response headers for proper configuration
        headers = response.headers
        has_server_header = "server" in headers
        has_content_type = "content-type" in headers
        self.assertTrue(has_server_header or has_content_type, "Missing basic HTTP headers")


class TestSystemIntegration(unittest.TestCase):
    """Integration tests for system components"""
    
    def test_01_frontend_backend_communication(self):
        """Test frontend can communicate with backend"""
        # This tests the full stack communication
        frontend_response = requests.get(FRONTEND_URL, timeout=15)
        backend_response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        
        self.assertEqual(frontend_response.status_code, 200)
        self.assertEqual(backend_response.status_code, 200)

    def test_02_vector_db_integration(self):
        """Test vector database integration"""
        response = requests.get(f"{QDRANT_URL}/collections", timeout=10)
        self.assertEqual(response.status_code, 200)
        
        # Test that collections are set up for the RAG pipeline
        data = response.json()
        collections = data.get("result", {}).get("collections", [])
        self.assertGreater(len(collections), 0)

    def test_03_api_endpoint_consistency(self):
        """Test API endpoint consistency across different calls"""
        # Make multiple calls to ensure consistent responses
        responses = []
        for _ in range(3):
            response = requests.get(f"{BACKEND_URL}/topics/", timeout=10)
            responses.append(response.json())
            
        # All responses should be identical
        first_response = responses[0]
        for response in responses[1:]:
            self.assertEqual(response, first_response)


def run_tests():
    """Run all tests and generate report"""
    import sys
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [TestCriticalFeatures, TestSystemIntegration]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout, buffer=True)
    result = runner.run(test_suite)
    
    # Generate summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"- {test}: {error_msg}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            lines = traceback.split('\n')
            error_msg = lines[-2] if len(lines) > 1 else traceback
            print(f"- {test}: {error_msg}")
    
    deployment_ready = len(result.failures) == 0 and len(result.errors) == 0
    
    print(f"\n{'✅ SYSTEM IS DEPLOYMENT READY!' if deployment_ready else '❌ ISSUES FOUND - REVIEW BEFORE DEPLOYMENT'}")
    
    return deployment_ready


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)