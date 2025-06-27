"""
Timestamp utilities for consistent datetime handling across the repository.

This module provides centralized timestamp functions to ensure consistency
in timezone handling, formatting, and datetime operations throughout the codebase.
"""

from datetime import UTC, datetime


def get_current_timestamp() -> datetime:
    """
    Get current UTC timestamp consistently across the repository.

    Returns:
        datetime: Current datetime in UTC timezone
    """
    return datetime.now(UTC)


def get_current_timestamp_iso() -> str:
    """
    Get current UTC timestamp as ISO string consistently.

    Returns:
        str: Current datetime in UTC as ISO 8601 string
    """
    return get_current_timestamp().isoformat()


def get_timestamp_iso(dt: datetime) -> str:
    """
    Convert datetime to ISO string consistently.

    Args:
        dt: Datetime object to convert

    Returns:
        str: Datetime as ISO 8601 string
    """
    return dt.isoformat()


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is in UTC timezone.

    Args:
        dt: Datetime object to check/convert

    Returns:
        datetime: Datetime in UTC timezone
    """
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        return dt.replace(tzinfo=UTC)
    elif dt.tzinfo != UTC:
        # Convert to UTC if in different timezone
        return dt.astimezone(UTC)
    else:
        # Already UTC
        return dt
