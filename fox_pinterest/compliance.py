"""Compliance checks and disclosures for Pinterest API usage.

This module provides functions to ensure the app remains compliant with
Pinterest Developer Guidelines and the Developer/API Terms of Service.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import re


# Attribution text required by Pinterest guidelines
PINTEREST_ATTRIBUTION = (
    "This application uses the Pinterest API but is not endorsed or "
    "certified by Pinterest, Inc.\n"
    "\"Pinterest\" is a trademark of Pinterest, Inc. This application is "
    "not affiliated with, endorsed by, or sponsored by Pinterest, Inc."
)


# Pinterest prohibited patterns for pin content
PROHIBITED_PATTERNS = [
    r"\bincentivize\b",  # No incentivizing engagement
    r"\brequire.*save.*pin\b",  # No requiring saves
    r"\bfollow.*for.*follow\b",  # No follow-for-follow schemes
]


@dataclass
class ComplianceResult:
    """Result of a compliance check."""
    is_compliant: bool
    issues: list[str] = None  # type: ignore[assignment]
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
    
    def add_issue(self, issue: str):
        self.issues.append(issue)
        self.is_compliant = False
    
    def __bool__(self):
        return self.is_compliant


def check_pin_content(title: str, description: str) -> ComplianceResult:
    """Check pin content for prohibited patterns.
    
    Args:
        title: The pin title.
        description: The pin description.
        
    Returns:
        ComplianceResult indicating if the content is compliant.
    """
    result = ComplianceResult(is_compliant=True)
    combined = f"{title} {description}".lower()
    
    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            result.add_issue(
                f"Pin content contains a prohibited pattern: '{pattern}'"
            )
    
    # Check title length (Pinterest max 100 chars)
    if len(title) > 100:
        result.add_issue(
            f"Title is {len(title)} characters, exceeds Pinterest's 100-char limit"
        )
    
    # Check description length (Pinterest max 500 chars)
    if len(description) > 500:
        result.add_issue(
            f"Description is {len(description)} characters, exceeds Pinterest's 500-char limit"
        )
    
    return result


def check_app_config(app_id: str, app_secret: str) -> ComplianceResult:
    """Check that the app configuration is compliant.
    
    Args:
        app_id: The Pinterest app ID.
        app_secret: The Pinterest app secret.
        
    Returns:
        ComplianceResult indicating if the configuration is compliant.
    """
    result = ComplianceResult(is_compliant=True)
    
    # Validate app_id format
    if not app_id:
        result.add_issue("App ID is empty")
    elif not re.match(r"^[A-Za-z0-9_-]+$", app_id):
        result.add_issue("App ID contains invalid characters")
    
    # Validate app_secret is not empty (but don't log the actual value)
    if not app_secret:
        result.add_issue("App secret is empty")
    
    return result


def log_compliance_action(action: str, details: str) -> str:
    """Log a compliance action for audit purposes.
    
    Args:
        action: The action being performed.
        details: Details about the action.
        
    Returns:
        A compliance log entry string (not persisted to disk).
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = f"[{timestamp}] COMPLIANCE: {action} — {details}"
    print(f"  {log_entry}")
    return log_entry


def get_attribution_text() -> str:
    """Return the required Pinterest attribution text.
    
    Returns:
        Attribution text string.
    """
    return PINTEREST_ATTRIBUTION


def validate_scopes(requested_scopes: list[str]) -> ComplianceResult:
    """Validate that only appropriate scopes are requested.
    
    Per Pinterest guidelines, only scopes that are actually needed
    should be requested. This prevents over-privileged access.
    
    Args:
        requested_scopes: List of scope strings.
        
    Returns:
        ComplianceResult with validation.
    """
    result = ComplianceResult(is_compliant=True)
    allowed_scopes = {"boards:read", "pins:read", "pins:write", "apps:read"}
    sensitive_scopes = {"ads:read", "audiences:read", "users:email:read"}
    
    for scope in requested_scopes:
        if scope not in allowed_scopes:
            result.add_issue(
                f"Scope '{scope}' is not in the approved scope list: {sorted(allowed_scopes)}"
            )
        if scope in sensitive_scopes:
            result.add_issue(
                f"Scope '{scope}' is sensitive and not required for pin scheduling"
            )
    
    return result
