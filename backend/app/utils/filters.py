"""
Utility functions for filtering bounties.

Implements the 15-minute delay filter to encourage agents
to use blockchain event listeners instead of polling the API.
"""
from datetime import datetime, timedelta


def is_older_than_one_hour(created_at: datetime) -> bool:
    """
    Check if a timestamp is older than 15 minutes from now.

    Args:
        created_at: Timestamp to check

    Returns:
        True if older than 15 minutes, False otherwise

    Example:
        If current time is 10:00 AM:
        - is_older_than_one_hour(9:00 AM) -> True (60 minutes old)
        - is_older_than_one_hour(9:50 AM) -> False (10 minutes old)
    """
    fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
    return created_at < fifteen_minutes_ago


def get_one_hour_ago_timestamp() -> datetime:
    """
    Get the timestamp for exactly 15 minutes ago from now.

    Returns:
        datetime: Timestamp for 15 minutes ago (UTC)

    Used for database queries to filter bounties.

    Example:
        Current time: 2026-01-12 10:00:00 UTC
        Returns: 2026-01-12 09:45:00 UTC
    """
    return datetime.utcnow() - timedelta(minutes=15)


def get_time_until_visible(created_at: datetime) -> timedelta:
    """
    Calculate how much time until a bounty becomes visible in /api/bounties.

    Args:
        created_at: When the bounty was created

    Returns:
        timedelta: Time remaining until visible (0 if already visible)

    Example:
        If bounty was created 5 minutes ago, returns 10 minutes.
        If bounty was created 20 minutes ago, returns 0 (already visible).
    """
    fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
    if created_at >= fifteen_minutes_ago:
        # Not visible yet
        time_until_visible = created_at - fifteen_minutes_ago
        return time_until_visible
    else:
        # Already visible
        return timedelta(0)
