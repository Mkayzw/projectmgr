from datetime import datetime, timezone
from typing import Any, Dict, Optional

import re


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_username(username: str) -> bool:
    """Validate username format (alphanumeric and underscores, 3-30 chars)."""
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return re.match(pattern, username) is not None


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def sanitize_string(text: Optional[str], max_length: int = 255) -> Optional[str]:
    """Sanitize and truncate string input."""
    if not text:
        return text
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    return text if text else None


def format_error_response(message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format error response for API."""
    response = {
        "error": True,
        "message": message,
        "timestamp": utc_now().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response


def format_success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """Format success response for API."""
    response = {
        "success": True,
        "data": data,
        "timestamp": utc_now().isoformat()
    }
    
    if message:
        response["message"] = message
    
    return response


def paginate_query_params(skip: int = 0, limit: int = 100) -> tuple[int, int]:
    """Validate and normalize pagination parameters."""
    # Ensure skip is non-negative
    skip = max(0, skip)
    
    # Ensure limit is within reasonable bounds
    limit = max(1, min(limit, 1000))
    
    return skip, limit


def generate_slug(text: str) -> str:
    """Generate a URL-friendly slug from text."""
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Limit length
    return text[:50] if text else 'untitled'