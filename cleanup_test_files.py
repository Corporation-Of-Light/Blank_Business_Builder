"""
Automated Test File Cleanup Script
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This script removes duplicate database setup from test files and migrates them
to use the centralized conftest.py configuration.
"""
import re
import os

# Test files that need cleanup
TEST_FILES = [
    "tests/test_businesses.py",
    "tests/test_comprehensive_bbb.py",
    "tests/test_disaster_recovery.py",
    "tests/test_integration.py",
    "tests/test_multi_channel_marketing.py",
    "tests/test_smart_lead_nurturing.py",
    "tests/test_security_owasp.py",
]

# Pattern to match the duplicate database setup section
DUPLICATE_SETUP_PATTERN = re.compile(
    r'# Test database setup.*?'
    r'@pytest\.fixture\(autouse=True\)\s*\n'
    r'def setup_database\(\):.*?'
    r'Base\.metadata\.drop_all\(bind=engine\)',
    re.DOTALL
)

# Alternative pattern for files with slightly different structure
ALT_SETUP_PATTERN = re.compile(
    r'SQLALCHEMY_DATABASE_URL = "sqlite.*?'
    r'Base\.metadata\.drop_all\(bind=engine\)',
    re.DOTALL
)

def backup_file(filepath):
    """Create a backup of the original file."""
    backup_path = filepath + '.backup'
    with open(filepath, 'r') as f:
        content = f.read()
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"  📦 Created backup: {backup_path}")

def remove_duplicate_imports(content):
    """Remove duplicate SQLAlchemy imports that are now in conftest."""
    # Remove duplicate engine/sessionmaker imports
    content = re.sub(r'from sqlalchemy import create_engine\n', '', content)
    content = re.sub(r'from sqlalchemy\.orm import sessionmaker\n', '', content)
    content = re.sub(r'from sqlalchemy\.pool import StaticPool\n', '', content)

    # Remove duplicate TestClient import (will use from conftest)
    # Keep it if the file doesn't import from conftest yet
    return content

def add_conftest_import(content):
    """Add import from conftest.py if not already present."""
    if 'from .conftest import client' in content or 'from conftest import client' in content:
        print("  ✅ Already imports from conftest")
        return content

    # Find the import section (after docstring, before first class/function)
    import_section_end = 0
    lines = content.split('\n')

    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            import_section_end = i + 1
        elif line.strip() and not line.startswith('#') and not line.startswith('"""') and not line.startswith("'''"):
            if import_section_end > 0:
                break

    # Insert the import
    if import_section_end > 0:
        lines.insert(import_section_end, '\n# Import centralized test fixtures from conftest.py')
        lines.insert(import_section_end + 1, 'from .conftest import client')
        content = '\n'.join(lines)
        print("  ✅ Added conftest import")

    return content

def remove_duplicate_client_definition(content):
    """Remove standalone client = TestClient(app) definitions."""
    # Remove lines like: client = TestClient(app)
    content = re.sub(r'\nclient = TestClient\(app\)\n', '\n', content)
    return content

def cleanup_test_file(filepath):
    """Clean up a single test file."""
    print(f"\n🔧 Processing: {filepath}")

    if not os.path.exists(filepath):
        print(f"  ❌ File not found: {filepath}")
        return False

    # Backup original file
    backup_file(filepath)

    # Read file content
    with open(filepath, 'r') as f:
        content = f.read()

    original_length = len(content)

    # Remove duplicate database setup
    if DUPLICATE_SETUP_PATTERN.search(content):
        content = DUPLICATE_SETUP_PATTERN.sub('', content)
        print("  ✅ Removed duplicate database setup (pattern 1)")
    elif ALT_SETUP_PATTERN.search(content):
        content = ALT_SETUP_PATTERN.sub('', content)
        print("  ✅ Removed duplicate database setup (pattern 2)")
    else:
        print("  ⚠️  No duplicate setup found (may already be clean)")

    # Remove duplicate imports
    content = remove_duplicate_imports(content)

    # Remove duplicate client definition
    content = remove_duplicate_client_definition(content)

    # Add conftest import
    content = add_conftest_import(content)

    # Clean up excessive blank lines (more than 2 consecutive)
    content = re.sub(r'\n\n\n+', '\n\n', content)

    # Write cleaned content
    with open(filepath, 'w') as f:
        f.write(content)

    reduction = original_length - len(content)
    print(f"  📉 Reduced file size by {reduction} characters ({reduction / original_length * 100:.1f}%)")
    print(f"  ✅ Cleanup complete!")

    return True

def verify_cleanup():
    """Verify that all files were cleaned successfully."""
    print("\n\n📊 Verification Report:")
    print("=" * 60)

    all_clean = True
    for filepath in TEST_FILES:
        with open(filepath, 'r') as f:
            content = f.read()

        has_duplicate = bool(DUPLICATE_SETUP_PATTERN.search(content) or ALT_SETUP_PATTERN.search(content))
        has_conftest_import = 'from .conftest import client' in content or 'from conftest import client' in content

        status = "✅ CLEAN" if not has_duplicate and has_conftest_import else "❌ NEEDS WORK"
        print(f"{status}: {filepath}")

        if not has_conftest_import:
            print(f"  ⚠️  Missing conftest import")
            all_clean = False
        if has_duplicate:
            print(f"  ⚠️  Still has duplicate setup")
            all_clean = False

    print("=" * 60)
    if all_clean:
        print("✅ All files successfully cleaned!")
    else:
        print("⚠️  Some files need manual review")

    return all_clean

def main():
    """Main cleanup function."""
    print("🧹 Test File Cleanup Script")
    print("=" * 60)
    print(f"Files to process: {len(TEST_FILES)}")
    print("=" * 60)

    success_count = 0
    for filepath in TEST_FILES:
        if cleanup_test_file(filepath):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"✅ Successfully processed {success_count}/{len(TEST_FILES)} files")
    print("=" * 60)

    # Verify cleanup
    verify_cleanup()

    print("\n📝 Next Steps:")
    print("1. Run: python -m pytest tests/test_auth.py -v")
    print("   → Should show: 22 passed")
    print("\n2. Run: python -m pytest tests/ --ignore=tests/test_comprehensive_api.py --ignore=tests/test_database_migrations.py -v")
    print("   → Expected: ~195 passed, ~11 failed (only OWASP security)")
    print("\n3. If tests pass, delete backup files:")
    print("   rm tests/*.backup")

if __name__ == "__main__":
    main()
