"""
Utility functions for filtering bounties.

Implements the 1-hour delay filter to encourage agents
to use blockchain event listeners instead of polling the API.
"""
from datetime import datetime, timedelta


def is_older_than_one_hour(created_at: datetime) -> bool:
    """
    Check if a timestamp is older than 1 hour from now.

    Args:
        created_at: Timestamp to check

    Returns:
        True if older than 1 hour, False otherwise

    Example:
        If current time is 10:00 AM:
        - is_older_than_one_hour(8:00 AM) -> True (2 hours old)
        - is_older_than_one_hour(9:30 AM) -> False (30 minutes old)
    """
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    return created_at < one_hour_ago


def get_one_hour_ago_timestamp() -> datetime:
    """
    Get the timestamp for exactly 1 hour ago from now.

    Returns:
        datetime: Timestamp for 1 hour ago (UTC)

    Used for database queries to filter bounties.

    Example:
        Current time: 2026-01-12 10:00:00 UTC
        Returns: 2026-01-12 09:00:00 UTC
    """
    return datetime.utcnow() - timedelta(hours=1)


def get_time_until_visible(created_at: datetime) -> timedelta:
    """
    Calculate how much time until a bounty becomes visible in /api/bounties.

    Args:
        created_at: When the bounty was created

    Returns:
        timedelta: Time remaining until visible (0 if already visible)

    Example:
        If bounty was created 30 minutes ago, returns 30 minutes.
        If bounty was created 2 hours ago, returns 0 (already visible).
    """
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    if created_at >= one_hour_ago:
        # Not visible yet
        time_until_visible = created_at - one_hour_ago
        return time_until_visible
    else:
        # Already visible
        return timedelta(0)
