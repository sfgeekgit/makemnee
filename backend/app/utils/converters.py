"""
Utility functions for data validation and conversion.

Handles:
- bytes32 ID validation
- Ethereum address validation
- uint256 validation
- Wei to MNEE conversion
"""
import re
from decimal import Decimal
from typing import Optional

# Constants
WEI_PER_MNEE = 10 ** 18


def is_valid_bytes32(value: str) -> bool:
    """
    Validate bytes32 hex string format.

    Args:
        value: String to validate

    Returns:
        True if valid bytes32 format, False otherwise

    Expected format: "0x" + 64 hex characters
    Example: "0x7a3b9c2d..." (66 characters total)
    """
    if not isinstance(value, str):
        return False
    pattern = r'^0x[0-9a-fA-F]{64}$'
    return bool(re.match(pattern, value))


def is_valid_address(value: str) -> bool:
    """
    Validate Ethereum address format.

    Args:
        value: String to validate

    Returns:
        True if valid Ethereum address, False otherwise

    Expected format: "0x" + 40 hex characters
    Example: "0xABC..." (42 characters total)
    """
    if not isinstance(value, str):
        return False
    pattern = r'^0x[0-9a-fA-F]{40}$'
    return bool(re.match(pattern, value))


def is_valid_uint256(value: str) -> bool:
    """
    Validate that a string represents a valid uint256.

    Args:
        value: String to validate

    Returns:
        True if valid uint256, False otherwise

    Must be numeric and within uint256 range (0 to 2^256 - 1)
    """
    try:
        num = int(value)
        return 0 <= num <= (2 ** 256 - 1)
    except (ValueError, TypeError):
        return False


def wei_to_mnee(wei_amount: str) -> float:
    """
    Convert wei (as string) to MNEE tokens.

    Uses Decimal for precision to avoid floating-point errors.

    Args:
        wei_amount: Amount in wei as string (e.g., "100000000000000000000")

    Returns:
        Amount in MNEE as float (e.g., 100.0)

    Example:
        wei_to_mnee("100000000000000000000") -> 100.0
        wei_to_mnee("1000000000000000000") -> 1.0
    """
    try:
        wei = Decimal(wei_amount)
        mnee = wei / Decimal(WEI_PER_MNEE)
        return float(mnee)
    except (ValueError, TypeError):
        return 0.0


def mnee_to_wei(mnee_amount: float) -> str:
    """
    Convert MNEE tokens to wei.

    Uses Decimal for precision to avoid floating-point errors.

    Args:
        mnee_amount: Amount in MNEE (e.g., 100.0)

    Returns:
        Amount in wei as string (e.g., "100000000000000000000")

    Example:
        mnee_to_wei(100.0) -> "100000000000000000000"
        mnee_to_wei(1.0) -> "1000000000000000000"
    """
    try:
        wei = Decimal(str(mnee_amount)) * Decimal(WEI_PER_MNEE)
        return str(int(wei))
    except (ValueError, TypeError):
        return "0"


def normalize_hex_string(value: str) -> str:
    """
    Normalize a hex string to lowercase.

    Args:
        value: Hex string (e.g., "0xABC123...")

    Returns:
        Lowercase hex string (e.g., "0xabc123...")

    Ethereum addresses and bytes32 values are case-insensitive,
    but we store them lowercase for consistency.
    """
    if isinstance(value, str) and value.startswith("0x"):
        return value.lower()
    return value
