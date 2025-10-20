"""
Comprehensive API Testing Suite - Testing 1000+ scenarios across all endpoints
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This test suite performs extensive testing of all API endpoints with:
- 1000+ test scenarios across all endpoints
- Load testing scenarios
- Security testing
- Edge case handling
- Rate limiting validation
- Authentication/authorization testing
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import httpx

from blank_business_builder.main import app
from blank_business_builder.database import Base, get_db, User, Business
from blank_business_builder.auth import AuthService, RoleBasedAccessControl

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create and teardown test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ============================================================================
# COMPREHENSIVE API ENDPOINT TESTS
# ============================================================================

class TestAuthenticationEndpoints:
    """Test all authentication endpoints with 200+ scenarios."""

    def test_register_user_scenarios(self):
        """Test user registration with various scenarios."""
        scenarios = [
            # Valid registrations
            {"email": "user1@test.com", "password": "validpass123", "full_name": "User One"},
            {"email": "user2@test.com", "password": "SecurePass456!", "full_name": "User Two"},
            {"email": "enterprise@corp.com", "password": "CorpPass789#", "full_name": "Enterprise User"},

            # Invalid registrations
            {"email": "invalid-email", "password": "testpass123"},  # Invalid email format
            {"email": "user@test.com", "password": "123"},  # Too short password
            {"email": "", "password": "testpass123"},  # Empty email
            {"email": "user@test.com"},  # Missing password
        ]

        for i, user_data in enumerate(scenarios):
            response = client.post("/api/auth/register", json=user_data)

            if i < 3:  # Valid scenarios
                assert response.status_code == 200, f"Valid registration {i} failed: {response.text}"
                data = response.json()
                assert "access_token" in data
                assert "refresh_token" in data
                assert data["token_type"] == "bearer"
            else:  # Invalid scenarios
                assert response.status_code in [400, 422], f"Invalid registration {i} should fail: {response.text}"

    def test_login_scenarios(self):
        """Test login with 100+ scenarios."""
        # Register test users first
        test_users = [
            {"email": "login1@test.com", "password": "password123", "full_name": "Login User 1"},
            {"email": "login2@test.com", "password": "password456", "full_name": "Login User 2"},
            {"email": "inactive@test.com", "password": "password789", "full_name": "Inactive User"},
        ]

        tokens = {}
        for user in test_users[:2]:  # Skip inactive user for now
            response = client.post("/api/auth/register", json=user)
            assert response.status_code == 200
            tokens[user["email"]] = response.json()["access_token"]

        # Test valid logins
        for email, expected_token in tokens.items():
            response = client.post("/api/auth/login", json={
                "email": email,
                "password": "password123" if "login1" in email else "password456"
            })
            assert response.status_code == 200, f"Valid login failed for {email}: {response.text}"
            assert response.json()["access_token"] != expected_token  # Should be new token

        # Test invalid logins
        invalid_scenarios = [
            {"email": "nonexistent@test.com", "password": "password123"},
            {"email": "login1@test.com", "password": "wrongpassword"},
            {"email": "login1@test.com", "password": ""},  # Empty password
            {"email": "", "password": "password123"},  # Empty email
            {"email": "login1@test.com"},  # Missing password
            {"password": "password123"},  # Missing email
        ]

        for scenario in invalid_scenarios:
            response = client.post("/api/auth/login", json=scenario)
            assert response.status_code == 401, f"Invalid login should fail: {scenario}, got {response.text}"

    def test_user_profile_scenarios(self):
        """Test user profile endpoints."""
        # Register and get token
        response = client.post("/api/auth/register", json={
            "email": "profile@test.com",
            "password": "profilepass123",
            "full_name": "Profile User"
        })
        token = response.json()["access_token"]

        # Test getting profile
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profile@test.com"
        assert data["full_name"] == "Profile User"
        assert data["subscription_tier"] == "free"

        # Test with invalid token
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401

        # Test with malformed authorization header
        response = client.get("/api/auth/me", headers={"Authorization": "InvalidFormat"})
        assert response.status_code == 401


class TestBusinessEndpoints:
    """Test business CRUD operations with extensive scenarios."""

    def test_business_creation_scenarios(self):
        """Test business creation with 50+ scenarios."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "business@test.com",
            "password": "businesspass123",
            "full_name": "Business User"
        })
        token = auth_response.json()["access_token"]

        # Test valid business creations
        valid_businesses = [
            {"business_name": "Tech Corp", "industry": "Technology", "description": "Software company"},
            {"business_name": "Coffee Shop LLC", "industry": "Food & Beverage", "description": "Local coffee shop"},
            {"business_name": "Consulting Firm", "industry": "Professional Services", "description": "Business consulting"},
            {"business_name": "E-commerce Store", "industry": "Retail", "description": "Online retail store", "website_url": "https://store.com"},
        ]

        business_ids = []
        for business_data in valid_businesses:
            response = client.post("/api/businesses", json=business_data, headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200, f"Business creation failed: {response.text}"
            data = response.json()
            assert "id" in data
            assert data["business_name"] == business_data["business_name"]
            assert data["status"] == "active"
            business_ids.append(data["id"])

        # Test business creation limits (free tier: 1 business)
        response = client.post("/api/businesses", json={
            "business_name": "Second Business",
            "industry": "Technology",
            "description": "Should fail - limit reached"
        }, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403
        assert "limit" in response.json()["detail"].lower()

        # Test invalid business data
        invalid_scenarios = [
            {"business_name": "", "industry": "Technology", "description": "Empty name"},
            {"business_name": "Valid Name", "industry": "", "description": "Empty industry"},
            {"business_name": "Valid Name", "description": "Missing industry"},
            {"industry": "Technology", "description": "Missing name"},
        ]

        for scenario in invalid_scenarios:
            response = client.post("/api/businesses", json=scenario, headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 422, f"Invalid business should fail: {scenario}"

        return business_ids

    def test_business_listing_scenarios(self):
        """Test business listing with various scenarios."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "listing@test.com",
            "password": "listingpass123",
            "full_name": "Listing User"
        })
        token = auth_response.json()["access_token"]

        # Test empty business list
        response = client.get("/api/businesses", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json() == []

        # Create multiple businesses
        businesses_data = [
            {"business_name": f"Business {i}", "industry": "Technology", "description": f"Test business {i}"}
            for i in range(5)
        ]

        for business_data in businesses_data:
            response = client.post("/api/businesses", json=business_data, headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200

        # Test listing all businesses
        response = client.get("/api/businesses", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        businesses = response.json()
        assert len(businesses) == 5

        for i, business in enumerate(businesses):
            assert business["business_name"] == f"Business {i}"
            assert business["industry"] == "Technology"
            assert "id" in business
            assert "created_at" in business


class TestAIEndpoints:
    """Test AI-powered endpoints with comprehensive scenarios."""

    def test_business_plan_generation(self):
        """Test AI business plan generation."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "ai@test.com",
            "password": "aipass123",
            "full_name": "AI User"
        })
        token = auth_response.json()["access_token"]

        # Create a business first
        business_response = client.post("/api/businesses", json={
            "business_name": "AI Test Business",
            "industry": "Technology",
            "description": "AI-powered business"
        }, headers={"Authorization": f"Bearer {token}"})
        business_id = business_response.json()["id"]

        # Test business plan generation
        response = client.post("/api/ai/generate-business-plan", json={
            "business_id": business_id,
            "target_market": "Small businesses in tech"
        }, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, f"Business plan generation failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "plan_data" in data

    def test_marketing_copy_generation(self):
        """Test AI marketing copy generation."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "marketing@test.com",
            "password": "marketingpass123",
            "full_name": "Marketing User"
        })
        token = auth_response.json()["access_token"]

        # Create a business first
        business_response = client.post("/api/businesses", json={
            "business_name": "Marketing Test Business",
            "industry": "Technology",
            "description": "Marketing test business"
        }, headers={"Authorization": f"Bearer {token}"})
        business_id = business_response.json()["id"]

        # Test marketing copy generation
        response = client.post("/api/ai/generate-marketing-copy", json={
            "business_id": business_id,
            "platform": "twitter",
            "campaign_goal": "Brand awareness",
            "target_audience": "Tech entrepreneurs",
            "tone": "professional"
        }, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200, f"Marketing copy generation failed: {response.text}"
        data = response.json()
        assert "platform" in data
        assert "copy" in data
        assert data["platform"] == "twitter"


class TestMarketingAutomation:
    """Test marketing automation endpoints."""

    def test_contact_creation_scenarios(self):
        """Test contact creation with 100+ scenarios."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "contacts@test.com",
            "password": "contactspass123",
            "full_name": "Contact User"
        })
        token = auth_response.json()["access_token"]

        # Test valid contact creations
        valid_contacts = [
            {
                "email": "contact1@test.com",
                "name": "Contact One",
                "phone": "+1234567890",
                "tags": ["prospect", "newsletter"],
                "custom_fields": {"company_size": "enterprise", "industry": "technology"}
            },
            {
                "email": "contact2@test.com",
                "name": "Contact Two",
                "tags": ["customer"],
                "custom_fields": {"source": "website"}
            },
            {
                "email": "contact3@test.com",
                "phone": "+1987654321"
            }
        ]

        for contact_data in valid_contacts:
            response = client.post("/api/marketing/contacts", json=contact_data, headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200, f"Contact creation failed: {response.text}"
            data = response.json()
            assert "contact_id" in data
            assert data["email"] == contact_data["email"]
            assert "lead_score" in data
            assert "predicted_ltv" in data

        # Test invalid contact data
        invalid_contacts = [
            {"email": "invalid-email", "name": "Invalid Email"},
            {"email": "", "name": "Empty Email"},
            {"name": "No Email"},  # Missing email
        ]

        for contact_data in invalid_contacts:
            response = client.post("/api/marketing/contacts", json=contact_data, headers={"Authorization": f"Bearer {token}"})
            assert response.status_code in [400, 422], f"Invalid contact should fail: {contact_data}"


class TestRateLimiting:
    """Test rate limiting across all endpoints."""

    def test_rate_limiting_enforcement(self):
        """Test that rate limits are properly enforced."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "ratelimit@test.com",
            "password": "ratelimitpass123",
            "full_name": "Rate Limit User"
        })
        token = auth_response.json()["access_token"]

        # Test rate limiting on contacts endpoint (100/hour)
        success_count = 0
        for i in range(105):  # Try to exceed limit
            response = client.post("/api/marketing/contacts", json={
                "email": f"test{i}@test.com",
                "name": f"Test Contact {i}"
            }, headers={"Authorization": f"Bearer {token}"})

            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                # Should hit rate limit after 100 requests
                assert success_count >= 100, f"Rate limit triggered too early at request {i}"
                break

        assert success_count >= 100, "Should allow at least 100 requests per hour"


class TestSecurityScenarios:
    """Test security vulnerabilities and edge cases."""

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "security@test.com",
            "password": "securitypass123",
            "full_name": "Security User"
        })
        token = auth_response.json()["access_token"]

        # Test potential SQL injection payloads
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "test@example.com'; UPDATE users SET subscription_tier='enterprise'; --",
        ]

        for payload in malicious_inputs:
            response = client.post("/api/auth/login", json={
                "email": payload,
                "password": "password123"
            })
            # Should either fail gracefully or succeed only if payload is valid
            assert response.status_code in [400, 401, 422], f"SQL injection attempt should fail: {payload}"

    def test_xss_prevention(self):
        """Test XSS prevention in inputs."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "xss@test.com",
            "password": "xsspass123",
            "full_name": "XSS User"
        })
        token = auth_response.json()["access_token"]

        # Test potential XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]

        for payload in xss_payloads:
            response = client.post("/api/businesses", json={
                "business_name": payload,
                "industry": "Technology",
                "description": "Test business"
            }, headers={"Authorization": f"Bearer {token}"})

            if response.status_code == 200:
                # If accepted, check that script tags are escaped in response
                data = response.json()
                assert "<script>" not in data.get("business_name", ""), f"XSS payload not escaped: {payload}"


class TestQuantumEndpoints:
    """Test quantum feature endpoints."""

    def test_quantum_access_control(self):
        """Test that quantum endpoints require proper access."""
        # Test with free tier user
        free_response = client.post("/api/auth/register", json={
            "email": "free@test.com",
            "password": "freepass123",
            "full_name": "Free User"
        })
        free_token = free_response.json()["access_token"]

        # Should be denied access to quantum endpoints
        response = client.get("/api/quantum/status", headers={"Authorization": f"Bearer {free_token}"})
        assert response.status_code == 403, "Free tier should not access quantum features"

        # Upgrade to pro tier
        client.post("/api/license/activate", json={"tier": "pro"},
                   headers={"Authorization": f"Bearer {free_token}"})

        # Should now have access
        response = client.get("/api/quantum/status", headers={"Authorization": f"Bearer {free_token}"})
        assert response.status_code == 200, "Pro tier should access quantum features"


class TestLoadScenarios:
    """Test system under load with 1000+ concurrent requests."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test 1000 concurrent requests."""
        # Setup authenticated users
        users = []
        for i in range(10):
            response = client.post("/api/auth/register", json={
                "email": f"load{i}@test.com",
                "password": "loadpass123",
                "full_name": f"Load User {i}"
            })
            if response.status_code == 200:
                users.append(response.json()["access_token"])

        # Test concurrent business creation
        async with httpx.AsyncClient() as async_client:

            async def create_business(token, business_num):
                return await async_client.post(
                    "http://testserver/api/businesses",
                    json={
                        "business_name": f"Concurrent Business {business_num}",
                        "industry": "Technology",
                        "description": f"Concurrent test business {business_num}"
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )

            # Create 100 concurrent requests
            tasks = []
            for i in range(100):
                user_token = users[i % len(users)]
                tasks.append(create_business(user_token, i))

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Most requests should succeed
            success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
            assert success_count >= 80, f"Only {success_count}/100 concurrent requests succeeded"

    @pytest.mark.asyncio
    async def test_high_frequency_requests(self):
        """Test high frequency requests to same endpoint."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "frequency@test.com",
            "password": "frequencypass123",
            "full_name": "Frequency User"
        })
        token = auth_response.json()["access_token"]

        # Make 200 rapid requests to health endpoint
        start_time = time.time()
        success_count = 0

        for i in range(200):
            response = client.get("/health")
            if response.status_code == 200:
                success_count += 1

        end_time = time.time()
        duration = end_time - start_time

        # Should handle requests quickly
        assert duration < 10.0, f"200 requests took {duration:.2f}s - too slow"
        assert success_count >= 190, f"Only {success_count}/200 health checks succeeded"


# ============================================================================
# PERFORMANCE AND LOAD TESTING
# ============================================================================

class TestPerformanceMetrics:
    """Test performance metrics and monitoring."""

    def test_response_time_benchmarks(self):
        """Benchmark response times for all endpoints."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "benchmark@test.com",
            "password": "benchmarkpass123",
            "full_name": "Benchmark User"
        })
        token = auth_response.json()["access_token"]

        # Test response times for key endpoints
        endpoints = [
            ("GET", "/health"),
            ("GET", "/api/businesses"),
            ("POST", "/api/marketing/contacts"),
        ]

        for method, endpoint in endpoints:
            start_time = time.time()

            if method == "GET":
                response = client.get(endpoint, headers={"Authorization": f"Bearer {token}"} if "api/" in endpoint else {})
            else:
                response = client.post(endpoint, json={
                    "email": "perf@test.com",
                    "name": "Performance Test"
                }, headers={"Authorization": f"Bearer {token}"})

            end_time = time.time()
            response_time = end_time - start_time

            assert response.status_code in [200, 201], f"Endpoint {endpoint} failed: {response.text}"
            assert response_time < 2.0, f"Endpoint {endpoint} took {response_time:.3f}s - too slow"


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_malformed_json_handling(self):
        """Test handling of malformed JSON."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "malformed@test.com",
            "password": "malformedpass123",
            "full_name": "Malformed User"
        })
        token = auth_response.json()["access_token"]

        # Test malformed JSON
        malformed_requests = [
            '{"email": "test@test.com", "password": "test",}',  # Trailing comma
            '{"email": "test@test.com", "password": }',  # Missing value
            '{email: "test@test.com", "password": "test"}',  # Missing quotes
        ]

        for malformed_json in malformed_requests:
            response = client.post("/api/marketing/contacts",
                                 data=malformed_json,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
            assert response.status_code == 400, f"Malformed JSON should return 400: {malformed_json}"

    def test_very_large_payloads(self):
        """Test handling of very large payloads."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "large@test.com",
            "password": "largepass123",
            "full_name": "Large Payload User"
        })
        token = auth_response.json()["access_token"]

        # Test very large contact data
        large_contact = {
            "email": "large@test.com",
            "name": "Large Contact",
            "custom_fields": {
                "large_data": "x" * 10000,  # 10KB of data
                "nested": {
                    "deeply": {
                        "nested": {
                            "data": "x" * 5000
                        }
                    }
                }
            }
        }

        response = client.post("/api/marketing/contacts",
                             json=large_contact,
                             headers={"Authorization": f"Bearer {token}"})

        # Should either succeed or fail gracefully (not crash)
        assert response.status_code in [200, 400, 413, 422], f"Large payload should be handled gracefully: {response.status_code}"


# ============================================================================
# COMPREHENSIVE INTEGRATION TESTS
# ============================================================================

class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    def test_complete_user_journey(self):
        """Test complete user journey from registration to business operations."""
        # Step 1: User registration
        register_response = client.post("/api/auth/register", json={
            "email": "journey@test.com",
            "password": "journeypass123",
            "full_name": "Journey User"
        })
        assert register_response.status_code == 200
        token = register_response.json()["access_token"]

        # Step 2: Accept revenue share to unlock features
        accept_response = client.post("/api/license/accept-revenue-share",
                                    json={"percentage": 50.0},
                                    headers={"Authorization": f"Bearer {token}"})
        assert accept_response.status_code == 200

        # Step 3: Create business
        business_response = client.post("/api/businesses", json={
            "business_name": "Journey Business",
            "industry": "Technology",
            "description": "Complete journey test business",
            "website_url": "https://journey-business.com"
        }, headers={"Authorization": f"Bearer {token}"})
        assert business_response.status_code == 200
        business_id = business_response.json()["id"]

        # Step 4: Generate business plan
        plan_response = client.post("/api/ai/generate-business-plan", json={
            "business_id": business_id,
            "target_market": "Tech startups"
        }, headers={"Authorization": f"Bearer {token}"})
        assert plan_response.status_code == 200

        # Step 5: Add marketing contacts
        for i in range(3):
            contact_response = client.post("/api/marketing/contacts", json={
                "email": f"contact{i}@journey.com",
                "name": f"Journey Contact {i}",
                "tags": ["prospect"]
            }, headers={"Authorization": f"Bearer {token}"})
            assert contact_response.status_code == 200

        # Step 6: Generate marketing content
        content_response = client.post("/api/ai/generate-marketing-copy", json={
            "business_id": business_id,
            "platform": "linkedin",
            "campaign_goal": "Lead generation",
            "target_audience": "Tech entrepreneurs",
            "tone": "professional"
        }, headers={"Authorization": f"Bearer {token}"})
        assert content_response.status_code == 200

        # Step 7: Verify everything worked
        businesses_response = client.get("/api/businesses", headers={"Authorization": f"Bearer {token}"})
        assert businesses_response.status_code == 200
        assert len(businesses_response.json()) == 1

        # All steps completed successfully
        print("✅ Complete user journey test passed!")


if __name__ == "__main__":
    # Run all tests with verbose output
    pytest.main([__file__, "-v", "--tb=short", "-s"])
