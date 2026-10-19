"""
Module: security_utils.py
Provides utility functions for input sanitization, data validation, and security headers.
"""

import html
import re
from typing import Dict, Any


def sanitize_input(value: str) -> str:
    """
    Sanitizes string inputs by stripping outer whitespace and HTML-escaping entities.
    Mitigates Cross-Site Scripting (XSS) in returned representations.
    """
    if not isinstance(value, str):
        return ""
    clean_val = value.strip()
    return html.escape(clean_val)


def is_valid_username(username: str) -> bool:
    """
    Validates username format using a strict alphanumeric pattern (length 3 to 20).
    """
    if not username or not isinstance(username, str):
        return False
    pattern = r"^[a-zA-Z0-9_]{3,20}$"
    return bool(re.match(pattern, username))


def generate_security_headers() -> Dict[str, str]:
    """
    Generates standard HTTP response headers recommended by OWASP.
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Content-Security-Policy": "default-src 'self'",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }
