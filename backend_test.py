#!/usr/bin/env python3
"""
TalentScout AI Chatbot Backend API Testing
Tests all endpoints and conversation flow functionality
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

class TalentScoutAPITester:
    def __init__(self, base_url="https://techscreener.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {name}")
        if details:
            print(f"    Details: {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append({"test": name, "details": details})
        print()

    def test_api_root(self) -> bool:
        """Test GET /api/ endpoint"""
        try:
            response = self.session.get(f"{self.api_url}/")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "message" in data and "TalentScout" in data["message"]
                details = f"Status: {response.status_code}, Response: {data}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("API Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("API Root Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_create_session(self) -> bool:
        """Test POST /api/chat/session endpoint"""
        try:
            response = self.session.post(f"{self.api_url}/chat/session")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["id", "candidate_info", "messages", "current_step", "created_at"]
                success = all(field in data for field in required_fields)
                
                if success:
                    self.session_id = data["id"]
                    # Check if greeting message exists
                    success = len(data["messages"]) > 0 and data["messages"][0]["role"] == "bot"
                    details = f"Session ID: {self.session_id}, Step: {data['current_step']}, Messages: {len(data['messages'])}"
                else:
                    details = f"Missing required fields. Got: {list(data.keys())}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Create Chat Session", success, details)
            return success
        except Exception as e:
            self.log_test("Create Chat Session", False, f"Exception: {str(e)}")
            return False

    def test_get_session(self) -> bool:
        """Test GET /api/chat/session/{session_id} endpoint"""
        if not self.session_id:
            self.log_test("Get Chat Session", False, "No session ID available")
            return False
        
        try:
            response = self.session.get(f"{self.api_url}/chat/session/{self.session_id}")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = data["id"] == self.session_id
                details = f"Retrieved session: {self.session_id}, Step: {data.get('current_step')}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Chat Session", success, details)
            return success
        except Exception as e:
            self.log_test("Get Chat Session", False, f"Exception: {str(e)}")
            return False

    def test_send_message(self, message: str, expected_step: str = None) -> Dict[str, Any]:
        """Test POST /api/chat/send endpoint"""
        if not self.session_id:
            self.log_test(f"Send Message: '{message}'", False, "No session ID available")
            return {}
        
        try:
            payload = {
                "session_id": self.session_id,
                "message": message
            }
            response = self.session.post(f"{self.api_url}/chat/send", json=payload)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["session_id", "bot_messages", "current_step", "candidate_info"]
                success = all(field in data for field in required_fields)
                
                if success and expected_step:
                    success = data["current_step"] == expected_step
                
                details = f"Step: {data.get('current_step')}, Bot messages: {len(data.get('bot_messages', []))}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
                data = {}
            
            self.log_test(f"Send Message: '{message}'", success, details)
            return data if success else {}
        except Exception as e:
            self.log_test(f"Send Message: '{message}'", False, f"Exception: {str(e)}")
            return {}

    def test_email_validation(self) -> bool:
        """Test email validation"""
        # Test invalid email
        invalid_response = self.test_send_message("invalid-email")
        if not invalid_response:
            return False
        
        # Should stay on email step with validation error
        invalid_success = invalid_response.get("current_step") == "email"
        
        # Test valid email
        valid_response = self.test_send_message("test@example.com", "phone")
        valid_success = bool(valid_response)
        
        overall_success = invalid_success and valid_success
        details = f"Invalid email rejected: {invalid_success}, Valid email accepted: {valid_success}"
        self.log_test("Email Validation", overall_success, details)
        return overall_success

    def test_phone_validation(self) -> bool:
        """Test phone validation"""
        # Test invalid phone
        invalid_response = self.test_send_message("123")
        if not invalid_response:
            return False
        
        # Should stay on phone step with validation error
        invalid_success = invalid_response.get("current_step") == "phone"
        
        # Test valid phone
        valid_response = self.test_send_message("1234567890", "experience")
        valid_success = bool(valid_response)
        
        overall_success = invalid_success and valid_success
        details = f"Invalid phone rejected: {invalid_success}, Valid phone accepted: {valid_success}"
        self.log_test("Phone Validation", overall_success, details)
        return overall_success

    def test_conversation_flow(self) -> bool:
        """Test complete conversation flow"""
        if not self.session_id:
            return False
        
        # Test name step
        name_response = self.test_send_message("John Doe", "email")
        if not name_response:
            return False
        
        # Email validation already tested above
        # Phone validation already tested above
        
        # Test experience step
        exp_response = self.test_send_message("3-5 years", "position")
        if not exp_response:
            return False
        
        # Test position step
        pos_response = self.test_send_message("Software Engineer, Full Stack Developer", "location")
        if not pos_response:
            return False
        
        # Test location step
        loc_response = self.test_send_message("San Francisco, USA", "tech_stack")
        if not loc_response:
            return False
        
        # Test tech stack step
        tech_response = self.test_send_message("Python, JavaScript, React, FastAPI, PostgreSQL", "questions")
        if not tech_response:
            return False
        
        # Test questions step - answer a few questions
        q1_response = self.test_send_message("Python uses dynamic typing and has excellent readability.")
        if not q1_response:
            return False
        
        q2_response = self.test_send_message("I would use proper error handling and logging.")
        if not q2_response:
            return False
        
        q3_response = self.test_send_message("RESTful APIs should be stateless and use proper HTTP methods.")
        if not q3_response:
            return False
        
        q4_response = self.test_send_message("I use unit tests, integration tests, and end-to-end testing.")
        if not q4_response:
            return False
        
        # Should move to summary after answering questions
        summary_success = q4_response.get("current_step") in ["summary", "questions"]
        
        self.log_test("Complete Conversation Flow", summary_success, f"Final step: {q4_response.get('current_step')}")
        return summary_success

    def test_exit_handling(self) -> bool:
        """Test exit keyword handling"""
        # Create new session for exit test
        create_response = self.session.post(f"{self.api_url}/chat/session")
        if create_response.status_code != 200:
            self.log_test("Exit Handling", False, "Could not create session for exit test")
            return False
        
        temp_session_id = create_response.json()["id"]
        
        # Test exit keyword
        payload = {
            "session_id": temp_session_id,
            "message": "goodbye"
        }
        response = self.session.post(f"{self.api_url}/chat/send", json=payload)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            success = data.get("current_step") == "ended"
            details = f"Step after 'goodbye': {data.get('current_step')}"
        else:
            details = f"Status: {response.status_code}, Error: {response.text}"
        
        self.log_test("Exit Handling", success, details)
        return success

    def test_get_candidates(self) -> bool:
        """Test GET /api/candidates endpoint"""
        try:
            response = self.session.get(f"{self.api_url}/candidates")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                details = f"Status: {response.status_code}, Candidates count: {len(data)}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.log_test("Get Candidates", success, details)
            return success
        except Exception as e:
            self.log_test("Get Candidates", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests"""
        print("🚀 Starting TalentScout AI Backend API Tests")
        print(f"🔗 Testing API: {self.api_url}")
        print("=" * 60)
        
        # Basic API tests
        self.test_api_root()
        self.test_create_session()
        self.test_get_session()
        
        # Conversation flow tests
        if self.session_id:
            # Start with name step (session already created)
            self.test_send_message("John Doe", "email")
            self.test_email_validation()
            self.test_phone_validation()
            
            # Continue with remaining steps
            self.test_send_message("3-5 years", "position")
            self.test_send_message("Software Engineer", "location")
            self.test_send_message("San Francisco, USA", "tech_stack")
            self.test_send_message("Python, JavaScript, React", "questions")
            
            # Answer some questions
            self.test_send_message("Python is a high-level programming language.")
            self.test_send_message("I use proper error handling and testing.")
        
        # Other functionality tests
        self.test_exit_handling()
        self.test_get_candidates()
        
        # Print summary
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": len(self.failed_tests),
            "success_rate": success_rate,
            "failures": self.failed_tests
        }

def main():
    """Main test execution"""
    tester = TalentScoutAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["failed_tests"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())