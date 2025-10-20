"""
BBB Security Suite - Custom OWASP-Inspired Security Framework
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Reverse-engineered from OWASP best practices with custom enhancements.
Provides enterprise-grade security features for Blank Business Builder.
"""
import re
import html
import json
import hashlib
import secrets
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from fastapi import HTTPException, status
from pydantic import BaseModel, validator


class SecurityConfig(BaseModel):
    """Security configuration for BBB Security Suite."""
    # Password policy
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    password_special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Rate limiting
    max_login_attempts: int = 5
    login_lockout_duration_minutes: int = 15
    max_api_requests_per_minute: int = 60

    # Session security
    session_timeout_minutes: int = 30
    token_expiry_minutes: int = 60

    # Input validation
    max_input_length: int = 10000
    allowed_file_extensions: Set[str] = {".jpg", ".jpeg", ".png", ".pdf", ".txt"}
    max_file_size_mb: int = 10

    # Security headers
    enable_hsts: bool = True
    enable_csp: bool = True
    enable_xframe_options: bool = True


class InjectionPrevention:
    """Prevents injection attacks (SQL, NoSQL, LDAP, Command)."""

    # Dangerous patterns that indicate injection attempts
    SQL_INJECTION_PATTERNS = [
        r"('|(\\')|(;)|(--)|(\/\*))",  # SQL metacharacters
        r"(union|select|insert|update|delete|drop|create|alter|exec|execute)\s",  # SQL keywords
        r"(xp_|sp_|sys\.)",  # SQL Server extended procedures
    ]

    NOSQL_INJECTION_PATTERNS = [
        r"\$ne",
        r"\$gt",
        r"\$lt",
        r"\$regex",
        r"\$where",
    ]

    LDAP_INJECTION_PATTERNS = [
        r"\*\)\(",
        r"\)\(",
        r"\|\(",
        r"&\(",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r";",
        r"\|",
        r"&&",
        r"\$\(",
        r"`",
        r">\s*/",
    ]

    @classmethod
    def sanitize_sql_input(cls, value: str) -> str:
        """Sanitize input to prevent SQL injection."""
        if not isinstance(value, str):
            return value

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: Potential SQL injection detected"
                )

        # Additional sanitization: escape single quotes
        return value.replace("'", "''")

    @classmethod
    def sanitize_nosql_input(cls, value: Any) -> Any:
        """Sanitize input to prevent NoSQL injection."""
        if isinstance(value, str):
            # Check for NoSQL operators
            for pattern in cls.NOSQL_INJECTION_PATTERNS:
                if re.search(pattern, value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input: Potential NoSQL injection detected"
                    )
        elif isinstance(value, dict):
            # Reject dictionaries with $ operators
            for key in value.keys():
                if key.startswith('$'):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input: NoSQL operators not allowed"
                    )
        return value

    @classmethod
    def sanitize_command_input(cls, value: str) -> str:
        """Sanitize input to prevent command injection."""
        if not isinstance(value, str):
            return value

        # Check for command injection patterns
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: Potential command injection detected"
                )
        return value


class PasswordValidator:
    """Validates password strength according to security policy."""

    @staticmethod
    def validate_password_strength(password: str, config: SecurityConfig = SecurityConfig()) -> Dict[str, Any]:
        """
        Validate password strength.

        Returns dict with 'valid' (bool) and 'errors' (list of str).
        """
        errors = []

        # Check minimum length
        if len(password) < config.min_password_length:
            errors.append(f"Password must be at least {config.min_password_length} characters")

        # Check for uppercase
        if config.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        # Check for lowercase
        if config.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        # Check for digits
        if config.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")

        # Check for special characters
        if config.require_special_chars:
            special_char_pattern = f"[{re.escape(config.password_special_chars)}]"
            if not re.search(special_char_pattern, password):
                errors.append(f"Password must contain at least one special character: {config.password_special_chars}")

        # Check for common weak passwords
        weak_passwords = ["password", "123456", "qwerty", "admin", "welcome", "letmein"]
        if password.lower() in weak_passwords:
            errors.append("Password is too common")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


class XSSPrevention:
    """Prevents Cross-Site Scripting (XSS) attacks."""

    XSS_PATTERNS = [
        r"<script",
        r"javascript:",
        r"onerror=",
        r"onload=",
        r"onclick=",
        r"<iframe",
        r"<embed",
        r"<object",
    ]

    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """Sanitize HTML to prevent XSS."""
        if not isinstance(value, str):
            return value

        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: Potential XSS detected"
                )

        # HTML escape the input
        return html.escape(value)

    @classmethod
    def sanitize_json(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize JSON data."""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_html(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_json(value)
            elif isinstance(value, list):
                sanitized[key] = [cls.sanitize_html(v) if isinstance(v, str) else v for v in value]
            else:
                sanitized[key] = value
        return sanitized


class XMLSecurityValidator:
    """Prevents XML External Entity (XXE) attacks."""

    @staticmethod
    def parse_xml_safely(xml_string: str) -> ET.Element:
        """
        Parse XML safely, preventing XXE attacks.

        Raises HTTPException if XML is potentially malicious.
        """
        # Check for entity declarations
        if "<!ENTITY" in xml_string or "<!DOCTYPE" in xml_string:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="XML entities and DOCTYPE declarations are not allowed"
            )

        # Parse with defusedxml-like restrictions
        try:
            # Disable entity resolution
            parser = ET.XMLParser()
            parser.entity = {}  # Empty entity dictionary
            root = ET.fromstring(xml_string, parser=parser)
            return root
        except ET.ParseError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid XML: {str(e)}"
            )


class DeserializationSecurity:
    """Prevents insecure deserialization attacks."""

    @staticmethod
    def safe_json_loads(json_string: str, max_depth: int = 10) -> Any:
        """
        Safely load JSON with depth and complexity limits.
        """
        try:
            data = json.loads(json_string)

            # Check depth
            def check_depth(obj, current_depth=0):
                if current_depth > max_depth:
                    raise ValueError("JSON depth exceeds maximum allowed")
                if isinstance(obj, dict):
                    for value in obj.values():
                        check_depth(value, current_depth + 1)
                elif isinstance(obj, list):
                    for item in obj:
                        check_depth(item, current_depth + 1)

            check_depth(data)
            return data

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON: {str(e)}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


class ErrorMessageSanitizer:
    """Prevents information leakage through error messages."""

    # Sensitive patterns to remove from error messages
    SENSITIVE_PATTERNS = [
        r"/[a-zA-Z0-9_\-/]+/[a-zA-Z0-9_\-\.]+\.py",  # File paths
        r"line \d+",  # Line numbers
        r"File \"[^\"]+\"",  # Full file references
        r"Traceback \(most recent call last\)",  # Stack traces
        r"sqlalchemy\.[a-zA-Z0-9_\.]+",  # SQLAlchemy internals
        r"postgresql://[^@]+@[^/]+/[^\s]+",  # Database connection strings
        r"mongodb://[^@]+@[^/]+/[^\s]+",
    ]

    @classmethod
    def sanitize_error_message(cls, error_message: str, debug_mode: bool = False) -> str:
        """
        Sanitize error message to prevent information leakage.

        In production (debug_mode=False), returns generic error message.
        In debug (debug_mode=True), returns detailed but sanitized message.
        """
        if not debug_mode:
            # Production: Generic error message
            return "An error occurred. Please contact support if the problem persists."

        # Debug mode: Sanitize sensitive information
        sanitized = error_message
        for pattern in cls.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)

        return sanitized


class InputValidator:
    """Comprehensive input validation."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[^\s]*)?$'
        return bool(re.match(url_pattern, url))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format."""
        # US phone number format
        phone_pattern = r'^\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$'
        return bool(re.match(phone_pattern, phone))

    @staticmethod
    def validate_alphanumeric(value: str, allow_spaces: bool = False) -> bool:
        """Validate alphanumeric input."""
        if allow_spaces:
            return bool(re.match(r'^[a-zA-Z0-9\s]+$', value))
        return bool(re.match(r'^[a-zA-Z0-9]+$', value))

    @staticmethod
    def validate_length(value: str, min_length: int = 0, max_length: int = 10000) -> bool:
        """Validate string length."""
        return min_length <= len(value) <= max_length


class SecurityHeaders:
    """Generate security headers for HTTP responses."""

    @staticmethod
    def get_security_headers(config: SecurityConfig = SecurityConfig()) -> Dict[str, str]:
        """
        Get recommended security headers.

        Returns dict of header name -> header value.
        """
        headers = {}

        # HTTP Strict Transport Security (HSTS)
        if config.enable_hsts:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy (CSP)
        if config.enable_csp:
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )

        # X-Frame-Options (Clickjacking protection)
        if config.enable_xframe_options:
            headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options
        headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection
        headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy
        headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return headers


# Singleton security config instance
security_config = SecurityConfig()


# Public API
__all__ = [
    'SecurityConfig',
    'InjectionPrevention',
    'PasswordValidator',
    'XSSPrevention',
    'XMLSecurityValidator',
    'DeserializationSecurity',
    'ErrorMessageSanitizer',
    'InputValidator',
    'SecurityHeaders',
    'security_config',
]
