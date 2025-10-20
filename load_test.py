#!/usr/bin/env python3
"""
Load Testing Suite with Locust - Testing 1000+ Concurrent Users
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This script performs comprehensive load testing of the BBB platform with:
- 1000+ concurrent users
- Realistic user behavior simulation
- Performance benchmarking
- Stress testing scenarios
- API endpoint load testing
"""

import random
import json
import time
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BBBApiUser(HttpUser):
    """Load testing user that simulates real BBB platform usage."""

    # Wait time between requests (realistic user behavior)
    wait_time = between(1, 5)

    # Base URL for the API
    host = "http://localhost:8000"

    def on_start(self):
        """Initialize user session."""
        self.user_id = f"user_{random.randint(1, 10000)}"
        self.token = None
        self.business_ids = []

        # Authenticate user
        self.authenticate()

    def authenticate(self):
        """Authenticate the user."""
        # Register user
        email = f"{self.user_id}@loadtest.com"
        password = "loadtestpass123"

        register_response = self.client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "full_name": f"Load Test User {self.user_id}"
        })

        if register_response.status_code == 200:
            data = register_response.json()
            self.token = data["access_token"]

            # Accept revenue share to unlock features
            self.client.post("/api/license/accept-revenue-share",
                           json={"percentage": 50.0},
                           headers={"Authorization": f"Bearer {self.token}"})

            logger.info(f"User {self.user_id} authenticated successfully")
        else:
            logger.error(f"User {self.user_id} authentication failed: {register_response.text}")

    @task(10)  # Higher weight for common operations
    def get_user_profile(self):
        """Get user profile - common operation."""
        if self.token:
            response = self.client.get("/api/auth/me",
                                     headers={"Authorization": f"Bearer {self.token}"})

            if response.status_code != 200:
                logger.warning(f"Profile request failed for user {self.user_id}: {response.status_code}")

    @task(8)
    def list_businesses(self):
        """List user's businesses."""
        if self.token:
            response = self.client.get("/api/businesses",
                                     headers={"Authorization": f"Bearer {self.token}"})

            if response.status_code == 200:
                businesses = response.json()
                self.business_ids = [b["id"] for b in businesses]

    @task(6)
    def create_business(self):
        """Create a new business."""
        if self.token:
            business_data = {
                "business_name": f"Load Test Business {random.randint(1, 100000)}",
                "industry": random.choice(["Technology", "Healthcare", "Finance", "Retail", "Education"]),
                "description": f"Business created during load testing by {self.user_id}",
                "website_url": f"https://business-{random.randint(1, 100000)}.com"
            }

            response = self.client.post("/api/businesses", json=business_data,
                                      headers={"Authorization": f"Bearer {self.token}"})

            if response.status_code == 200:
                business_data = response.json()
                self.business_ids.append(business_data["id"])
                logger.info(f"User {self.user_id} created business {business_data['id']}")
            elif response.status_code == 403:
                # Hit business limit, skip this task for a while
                logger.info(f"User {self.user_id} hit business creation limit")

    @task(5)
    def generate_business_plan(self):
        """Generate AI business plan."""
        if self.token and self.business_ids:
            business_id = random.choice(self.business_ids)

            response = self.client.post("/api/ai/generate-business-plan", json={
                "business_id": business_id,
                "target_market": random.choice([
                    "Small businesses", "Enterprise clients", "Tech startups",
                    "Healthcare providers", "Educational institutions"
                ])
            }, headers={"Authorization": f"Bearer {self.token}"})

            if response.status_code != 200:
                logger.warning(f"Business plan generation failed for user {self.user_id}: {response.status_code}")

    @task(4)
    def generate_marketing_copy(self):
        """Generate marketing copy."""
        if self.token and self.business_ids:
            business_id = random.choice(self.business_ids)

            response = self.client.post("/api/ai/generate-marketing-copy", json={
                "business_id": business_id,
                "platform": random.choice(["linkedin", "twitter", "facebook", "instagram"]),
                "campaign_goal": random.choice(["Brand awareness", "Lead generation", "Sales conversion"]),
                "target_audience": random.choice([
                    "Tech entrepreneurs", "Small business owners", "Enterprise executives",
                    "Healthcare professionals", "Students and educators"
                ]),
                "tone": random.choice(["professional", "friendly", "authoritative", "conversational"])
            }, headers={"Authorization": f"Bearer {self.token}"})

            if response.status_code != 200:
                logger.warning(f"Marketing copy generation failed for user {self.user_id}: {response.status_code}")

    @task(3)
    def create_marketing_contact(self):
        """Create marketing contact."""
        if self.token:
            contact_data = {
                "email": f"contact_{random.randint(1, 100000)}@loadtest.com",
                "name": f"Contact {random.randint(1, 100000)}",
                "phone": f"+1{random.randint(1000000000, 9999999999)}",
                "tags": random.sample(["prospect", "customer", "lead", "newsletter", "vip"], random.randint(1, 3)),
                "custom_fields": {
                    "source": random.choice(["website", "social_media", "referral", "advertising"]),
                    "company_size": random.choice(["startup", "small", "medium", "enterprise"]),
                    "industry": random.choice(["technology", "healthcare", "finance", "retail", "education"])
                }
            }

            response = self.client.post("/api/marketing/contacts", json=contact_data,
                                      headers={"Authorization": f"Bearer {self.token}"})

            if response.status_code != 200:
                logger.warning(f"Contact creation failed for user {self.user_id}: {response.status_code}")

    @task(2)
    def get_health_check(self):
        """Health check - very common operation."""
        response = self.client.get("/health")

        if response.status_code != 200:
            logger.warning(f"Health check failed for user {self.user_id}: {response.status_code}")

    @task(1)  # Lower weight for quantum features
    def access_quantum_features(self):
        """Access quantum features (requires pro tier)."""
        if self.token:
            # First upgrade to pro tier
            upgrade_response = self.client.post("/api/license/activate",
                                              json={"tier": "pro"},
                                              headers={"Authorization": f"Bearer {self.token}"})

            if upgrade_response.status_code == 200:
                # Access quantum features
                response = self.client.get("/api/quantum/status",
                                         headers={"Authorization": f"Bearer {self.token}"})

                if response.status_code != 200:
                    logger.warning(f"Quantum access failed for user {self.user_id}: {response.status_code}")
            else:
                logger.debug(f"User {self.user_id} tier upgrade failed")


class StressTestUser(HttpUser):
    """Stress testing user for extreme load scenarios."""

    wait_time = between(0.1, 0.5)  # Very aggressive timing

    def on_start(self):
        """Initialize stress test user."""
        self.user_id = f"stress_{random.randint(1, 100000)}"
        self.authenticate()

    def authenticate(self):
        """Quick authentication."""
        email = f"{self.user_id}@stress.com"
        password = "stresspass123"

        response = self.client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "full_name": f"Stress User {self.user_id}"
        })

        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(50)  # Very high frequency
    def rapid_health_checks(self):
        """Rapid health checks to test basic availability."""
        self.client.get("/health")

    @task(30)
    def rapid_authentication(self):
        """Rapid authentication attempts."""
        if not self.token:
            self.authenticate()
        else:
            self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {self.token}"})

    @task(20)
    def rapid_contact_creation(self):
        """Rapid contact creation."""
        if self.token:
            self.client.post("/api/marketing/contacts", json={
                "email": f"rapid_{random.randint(1, 1000000)}@test.com",
                "name": f"Rapid Contact {random.randint(1, 1000000)}"
            }, headers={"Authorization": f"Bearer {self.token}"})


class SpikeTestUser(HttpUser):
    """Spike testing user for sudden load increases."""

    wait_time = between(5, 15)  # Normal wait time

    def on_start(self):
        """Initialize spike test user."""
        self.user_id = f"spike_{random.randint(1, 10000)}"
        self.authenticate()

    def authenticate(self):
        """Authentication for spike testing."""
        email = f"{self.user_id}@spike.com"
        password = "spikepass123"

        response = self.client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "full_name": f"Spike User {self.user_id}"
        })

        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task
    def spike_operation(self):
        """Operation that simulates spike load."""
        if self.token:
            # Simulate complex operation that might cause spikes
            start_time = time.time()

            # Multiple rapid operations
            for _ in range(10):
                self.client.get("/health")

            # Then a complex operation
            if self.business_ids:
                self.client.post("/api/ai/generate-business-plan", json={
                    "business_id": random.choice(self.business_ids),
                    "target_market": "Spike test market"
                }, headers={"Authorization": f"Bearer {self.token}"})

            duration = time.time() - start_time
            if duration > 5.0:  # If it took more than 5 seconds
                logger.warning(f"Spike operation took {duration".2f"}s for user {self.user_id}")


class APIEndpointLoadTester(HttpUser):
    """Specific API endpoint load testing."""

    wait_time = between(0.5, 2.0)

    def on_start(self):
        """Initialize API tester."""
        self.user_id = f"api_{random.randint(1, 10000)}"
        self.authenticate()

    def authenticate(self):
        """Authentication for API testing."""
        email = f"{self.user_id}@api.com"
        password = "apipass123"

        response = self.client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "full_name": f"API User {self.user_id}"
        })

        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(40)
    def test_authentication_endpoint(self):
        """Load test authentication endpoints."""
        # Test login endpoint
        self.client.post("/api/auth/login", json={
            "email": f"{self.user_id}@api.com",
            "password": "apipass123"
        })

    @task(30)
    def test_business_endpoints(self):
        """Load test business CRUD endpoints."""
        if self.token:
            # Test business creation
            self.client.post("/api/businesses", json={
                "business_name": f"API Test Business {random.randint(1, 100000)}",
                "industry": "Technology",
                "description": "API load test business"
            }, headers={"Authorization": f"Bearer {self.token}"})

    @task(20)
    def test_ai_endpoints(self):
        """Load test AI generation endpoints."""
        if self.token:
            # First ensure we have a business
            business_response = self.client.post("/api/businesses", json={
                "business_name": f"AI Test Business {random.randint(1, 100000)}",
                "industry": "Technology",
                "description": "AI load test business"
            }, headers={"Authorization": f"Bearer {self.token}"})

            if business_response.status_code == 200:
                business_id = business_response.json()["id"]

                # Test AI endpoints
                self.client.post("/api/ai/generate-business-plan", json={
                    "business_id": business_id,
                    "target_market": "API test market"
                }, headers={"Authorization": f"Bearer {self.token}"})

    @task(10)
    def test_marketing_endpoints(self):
        """Load test marketing automation endpoints."""
        if self.token:
            # Test contact creation
            self.client.post("/api/marketing/contacts", json={
                "email": f"api_contact_{random.randint(1, 100000)}@test.com",
                "name": f"API Contact {random.randint(1, 100000)}",
                "tags": ["api_test"]
            }, headers={"Authorization": f"Bearer {self.token}"})


# ============================================================================
# LOAD TEST CONFIGURATIONS
# ============================================================================

class LoadTestScenarios:
    """Different load testing scenarios."""

    @staticmethod
    def normal_load_test():
        """Normal load test with 100 users."""
        return {
            "users": 100,
            "spawn_rate": 10,
            "test_duration": "5m",
            "user_classes": [BBBApiUser],
        }

    @staticmethod
    def stress_test():
        """Stress test with 500 users."""
        return {
            "users": 500,
            "spawn_rate": 50,
            "test_duration": "3m",
            "user_classes": [StressTestUser],
        }

    @staticmethod
    def spike_test():
        """Spike test with 1000 users."""
        return {
            "users": 1000,
            "spawn_rate": 100,
            "test_duration": "2m",
            "user_classes": [SpikeTestUser, BBBApiUser],
        }

    @staticmethod
    def api_focused_test():
        """API-focused load test."""
        return {
            "users": 200,
            "spawn_rate": 20,
            "test_duration": "4m",
            "user_classes": [APIEndpointLoadTester],
        }


# ============================================================================
# MONITORING AND REPORTING
# ============================================================================

@events.request.add_listener
def on_request_success(handler, response, **kwargs):
    """Monitor successful requests."""
    logger.debug(f"Request to {response.url} succeeded in {response.elapsed.total_seconds()".3f"}s")


@events.request.add_listener
def on_request_failure(handler, response, **kwargs):
    """Monitor failed requests."""
    logger.warning(f"Request to {response.url} failed with status {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize load test."""
    logger.info("🚀 Starting BBB Platform Load Test")
    logger.info(f"Target: {environment.parsed_options.num_users} users")
    logger.info(f"Spawn rate: {environment.parsed_options.spawn_rate} users/s")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Finalize load test."""
    logger.info("✅ BBB Platform Load Test Completed")

    # Print summary statistics
    if hasattr(environment.runner, "stats"):
        stats = environment.runner.stats
        total_requests = stats.num_requests
        total_failures = stats.num_failures
        avg_response_time = stats.avg_response_time

        logger.info(f"Total requests: {total_requests}")
        logger.info(f"Total failures: {total_failures}")
        logger.info(f"Average response time: {avg_response_time".3f"}s")
        logger.info(f"Success rate: {((total_requests - total_failures) / total_requests * 100)".2f"}%")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        scenario_name = sys.argv[1]
        scenario = getattr(LoadTestScenarios, scenario_name, LoadTestScenarios.normal_load_test)()
    else:
        scenario = LoadTestScenarios.normal_load_test()

    print(f"""
🔥 BBB Platform Load Testing Suite
==================================

Scenario: {scenario_name if len(sys.argv) > 1 else 'normal_load_test'}
Users: {scenario['users']}
Spawn Rate: {scenario['spawn_rate']} users/s
Duration: {scenario['test_duration']}

Starting load test...
    """)

    # This would be called when running with Locust
    # locust -f load_test.py --users 100 --spawn-rate 10 --run-time 5m
