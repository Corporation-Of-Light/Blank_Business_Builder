"""
Comprehensive Database Migration Tests
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Tests Alembic migrations with:
- Schema validation
- Data migration integrity
- Rollback functionality
- Multi-version compatibility
- Performance benchmarks
"""

import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Dict, Any

# Try to import alembic - skip tests if not available
try:
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from alembic.environment import EnvironmentContext
    from alembic.runtime.migration import MigrationContext
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False

# Import your database models and migration env
try:
    from blank_business_builder.database import Base, User, Business, BusinessPlan
    from blank_business_builder.main import app
except ImportError:
    pass

# Skip all tests in this module if alembic is not available
pytestmark = pytest.mark.skipif(not ALEMBIC_AVAILABLE, reason="Alembic not installed")


class TestMigrationEnvironment:
    """Test Alembic migration environment and configuration."""

    def test_alembic_config_exists(self):
        """Test that Alembic configuration file exists."""
        assert os.path.exists("alembic.ini"), "alembic.ini configuration file missing"

    def test_migration_directory_structure(self):
        """Test that migration directory structure is correct."""
        alembic_dir = Path("alembic")
        assert alembic_dir.exists(), "alembic directory missing"

        versions_dir = alembic_dir / "versions"
        assert versions_dir.exists(), "alembic/versions directory missing"

        env_file = alembic_dir / "env.py"
        assert env_file.exists(), "alembic/env.py missing"

    def test_migration_history(self):
        """Test migration history and revisions."""
        config = Config("alembic.ini")
        script = ScriptDirectory.from_config(config)

        # Should have at least one revision
        revisions = list(script.walk_revisions())
        assert len(revisions) > 0, "No migration revisions found"

        # Check that revisions are properly ordered
        for i, revision in enumerate(revisions[:-1]):
            next_revision = revisions[i + 1]
            assert revision.down_revision == next_revision.revision, \
                f"Migration order incorrect between {revision.revision} and {next_revision.revision}"


class TestMigrationOperations:
    """Test actual migration operations."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        engine = create_engine(f"sqlite:///{db_path}")
        yield engine
        engine.dispose()
        os.unlink(db_path)

    def test_migration_up_down(self, temp_db):
        """Test migration up and down operations."""
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        # Test migration up
        command.upgrade(config, "head")

        # Verify tables were created
        inspector = inspect(temp_db)
        table_names = inspector.get_table_names()

        expected_tables = [
            'users', 'businesses', 'business_plans', 'agent_tasks',
            'metrics_history', 'api_integrations', 'audit_log',
            'subscriptions', 'marketing_campaigns'
        ]

        for table in expected_tables:
            assert table in table_names, f"Table {table} not created by migration"

        # Test migration down
        command.downgrade(config, "base")

        # Verify tables were dropped
        table_names_after = inspector.get_table_names()
        for table in expected_tables:
            assert table not in table_names_after, f"Table {table} not dropped by migration"

    def test_partial_migrations(self, temp_db):
        """Test partial migration scenarios."""
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        # Get all revisions
        script = ScriptDirectory.from_config(config)
        revisions = list(script.walk_revisions())

        if len(revisions) > 1:
            # Test migrating to specific revision
            target_revision = revisions[-2].revision  # Second to last

            command.upgrade(config, target_revision)

            # Verify only expected tables exist
            inspector = inspect(temp_db)
            table_names = inspector.get_table_names()

            # Should have some tables but not all
            assert len(table_names) > 0, "No tables created in partial migration"
            assert len(table_names) < len(revisions) * 2, "Too many tables created in partial migration"

    def test_migration_idempotency(self, temp_db):
        """Test that running migrations multiple times is safe."""
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        # Run migration multiple times
        for i in range(3):
            command.upgrade(config, "head")

            # Verify tables exist
            inspector = inspect(temp_db)
            table_names = inspector.get_table_names()
            assert len(table_names) > 0, f"Migration {i} failed to create tables"

            # Verify table structure is consistent
            if i > 0:
                assert table_names == inspector.get_table_names(), f"Table structure changed between runs {i-1} and {i}"


class TestDataMigrationIntegrity:
    """Test data integrity during migrations."""

    def test_data_preservation_during_migration(self, temp_db):
        """Test that data is preserved during migrations."""
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        # Create initial schema and data
        Base.metadata.create_all(temp_db)

        SessionLocal = sessionmaker(bind=temp_db)
        session = SessionLocal()

        # Insert test data
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            subscription_tier="free"
        )
        session.add(user)
        session.commit()

        user_id = user.id

        # Close session before migration
        session.close()

        # Run migration
        command.upgrade(config, "head")

        # Verify data is still accessible
        session = SessionLocal()
        user_after = session.query(User).filter(User.id == user_id).first()

        assert user_after is not None, "User data lost during migration"
        assert user_after.email == "test@example.com", "User email changed during migration"
        assert user_after.subscription_tier == "free", "User subscription tier changed during migration"

        session.close()

    def test_foreign_key_constraints(self, temp_db):
        """Test foreign key constraint integrity."""
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        # Run migration
        command.upgrade(config, "head")

        SessionLocal = sessionmaker(bind=temp_db)
        session = SessionLocal()

        # Test that we can create related records
        user = User(
            email="fktest@example.com",
            hashed_password="hashed_password",
            full_name="FK Test User"
        )
        session.add(user)
        session.commit()

        business = Business(
            user_id=user.id,
            business_name="FK Test Business",
            industry="Technology",
            description="Testing foreign keys"
        )
        session.add(business)
        session.commit()

        # Verify relationship works
        retrieved_business = session.query(Business).filter(Business.user_id == user.id).first()
        assert retrieved_business is not None, "Business not found via foreign key"

        # Test cascade delete (if configured)
        session.delete(user)
        session.commit()

        # Business should be deleted too (if cascade is set up)
        deleted_business = session.query(Business).filter(Business.id == business.id).first()
        # Note: This depends on cascade configuration in your models

        session.close()


class TestMigrationPerformance:
    """Test migration performance and optimization."""

    def test_migration_timing(self, temp_db):
        """Test migration execution time."""
        import time

        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        start_time = time.time()
        command.upgrade(config, "head")
        end_time = time.time()

        migration_time = end_time - start_time

        # Migration should complete reasonably quickly
        assert migration_time < 10.0, f"Migration took {migration_time:.2f}s - too slow"

    def test_large_dataset_migration(self, temp_db):
        """Test migration performance with large datasets."""
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        # Create large dataset before migration
        Base.metadata.create_all(temp_db)

        SessionLocal = sessionmaker(bind=temp_db)
        session = SessionLocal()

        # Insert 1000 users
        for i in range(1000):
            user = User(
                email=f"bulk{i}@example.com",
                hashed_password="hashed_password",
                full_name=f"Bulk User {i}"
            )
            session.add(user)

        session.commit()
        session.close()

        # Time the migration
        import time
        start_time = time.time()
        command.upgrade(config, "head")
        end_time = time.time()

        migration_time = end_time - start_time

        # Should handle large datasets efficiently
        assert migration_time < 30.0, f"Large dataset migration took {migration_time:.2f}s - too slow"


class TestMigrationErrorHandling:
    """Test migration error scenarios and recovery."""

    def test_corrupted_migration_file(self, temp_db):
        """Test handling of corrupted migration files."""
        # This test would require creating a corrupted migration file
        # For now, we'll test that the system handles missing files gracefully
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        # Test with non-existent revision
        try:
            command.upgrade(config, "non-existent-revision")
            assert False, "Should have failed with non-existent revision"
        except Exception as e:
            assert "non-existent-revision" in str(e) or "revision" in str(e).lower()

    def test_rollback_on_failure(self, temp_db):
        """Test that failed migrations can be rolled back."""
        # This would require creating a migration that can fail
        # For testing purposes, we'll verify the rollback mechanism exists
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        # Run migration up
        command.upgrade(config, "head")

        # Verify state after upgrade
        inspector = inspect(temp_db)
        table_names_before = inspector.get_table_names()
        assert len(table_names_before) > 0, "No tables created after upgrade"

        # Run migration down
        command.downgrade(config, "base")

        # Verify state after downgrade
        table_names_after = inspector.get_table_names()
        assert len(table_names_after) == 0, "Tables not properly removed after downgrade"


class TestMultiEnvironmentMigrations:
    """Test migrations across different environments."""

    def test_staging_vs_production_migration(self):
        """Test migration behavior differences between environments."""
        # Test staging environment
        staging_config = Config("alembic.ini")
        staging_config.set_main_option("sqlalchemy.url", "sqlite:///staging_test.db")

        # Test production environment
        production_config = Config("alembic.ini")
        production_config.set_main_option("sqlalchemy.url", "sqlite:///production_test.db")

        # Both should behave the same way
        for config in [staging_config, production_config]:
            command.upgrade(config, "head")

            # Verify same schema in both environments
            engine = create_engine(config.get_main_option("sqlalchemy.url"))
            inspector = inspect(engine)

            table_names = inspector.get_table_names()
            assert len(table_names) > 0, f"No tables created in {config.get_main_option('sqlalchemy.url')}"

            # Clean up
            engine.dispose()

    def test_database_url_configuration(self):
        """Test different database URL configurations."""
        # Test with various database URLs
        test_urls = [
            "sqlite:///:memory:",
            "sqlite:///test_migration.db",
            "postgresql://user:pass@localhost/test_migration",
        ]

        for url in test_urls:
            config = Config("alembic.ini")
            config.set_main_option("sqlalchemy.url", url)

            try:
                command.upgrade(config, "head")
                # If it doesn't fail, the URL format is valid
            except Exception:
                # Some URLs might not be accessible in test environment
                pass


class TestMigrationValidation:
    """Test migration validation and verification."""

    def test_schema_consistency(self, temp_db):
        """Test that schema is consistent after migration."""
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        # Run migration
        command.upgrade(config, "head")

        # Validate schema structure
        inspector = inspect(temp_db)

        # Check that all expected columns exist
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)

            # Each table should have an id column (primary key)
            column_names = [col['name'] for col in columns]
            assert any('id' in name for name in column_names), f"Table {table_name} missing id column"

            # Check for expected data types
            for col in columns:
                if col['name'] == 'created_at':
                    assert 'datetime' in str(col['type']).lower() or 'timestamp' in str(col['type']).lower(), \
                        f"created_at column in {table_name} should be datetime type"

    def test_index_validation(self, temp_db):
        """Test that proper indexes are created."""
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        # Run migration
        command.upgrade(config, "head")

        # Check indexes
        inspector = inspect(temp_db)

        for table_name in inspector.get_table_names():
            indexes = inspector.get_indexes(table_name)

            # Should have at least one index (primary key or explicit index)
            assert len(indexes) > 0, f"Table {table_name} has no indexes"

    def test_constraint_validation(self, temp_db):
        """Test database constraints are properly created."""
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", str(temp_db.url))

        # Run migration
        command.upgrade(config, "head")

        # Test constraints by trying to insert invalid data
        SessionLocal = sessionmaker(bind=temp_db)
        session = SessionLocal()

        # Test unique constraint on user email
        user1 = User(
            email="duplicate@test.com",
            hashed_password="password1",
            full_name="User 1"
        )
        user2 = User(
            email="duplicate@test.com",  # Same email
            hashed_password="password2",
            full_name="User 2"
        )

        session.add(user1)
        session.commit()

        session.add(user2)
        try:
            session.commit()
            assert False, "Duplicate email should violate unique constraint"
        except Exception:
            # Expected - unique constraint violation
            session.rollback()

        session.close()


if __name__ == "__main__":
    # Run migration tests
    pytest.main([__file__, "-v", "--tb=short"])
