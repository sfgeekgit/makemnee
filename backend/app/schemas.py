"""
Pydantic models for request/response validation.

Defines the API contract for all endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class BountyCreate(BaseModel):
    """
    Request model for creating a bounty.

    Used by POST /api/bounty endpoint.
    """
    id: str = Field(..., min_length=66, max_length=66, description="bytes32 bounty ID from blockchain")
    title: str = Field(..., min_length=1, max_length=200, description="Short title for the bounty")
    description: str = Field(..., min_length=1, description="Detailed description of the work")
    creator_address: str = Field(..., min_length=42, max_length=42, description="Ethereum address of creator")
    amount: str = Field(..., min_length=1, description="Amount in wei as string")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate and normalize bytes32 ID format"""
        if not v.startswith('0x') or len(v) != 66:
            raise ValueError('Invalid bytes32 format (must be 0x + 64 hex chars)')
        try:
            int(v, 16)  # Verify it's valid hex
        except ValueError:
            raise ValueError('Invalid hex string')
        return v.lower()

    @field_validator('creator_address')
    @classmethod
    def validate_creator_address(cls, v: str) -> str:
        """Validate and normalize Ethereum address"""
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid Ethereum address (must be 0x + 40 hex chars)')
        try:
            int(v, 16)  # Verify it's valid hex
        except ValueError:
            raise ValueError('Invalid hex string')
        return v.lower()

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: str) -> str:
        """Validate amount is a valid uint256"""
        try:
            num = int(v)
            if num < 0:
                raise ValueError('Amount must be non-negative')
            if num > (2 ** 256 - 1):
                raise ValueError('Amount exceeds uint256 maximum')
        except ValueError as e:
            if "non-negative" in str(e) or "exceeds" in str(e):
                raise
            raise ValueError('Amount must be a valid integer string')
        return v


class BountyResponse(BaseModel):
    """
    Response model for bounty data.

    Used by GET /api/bounty/{id} and GET /api/bounties endpoints.
    """
    id: str
    title: str
    description: str
    creator_address: str
    amount: str
    amount_mnee: float
    status: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    hunter_address: Optional[str] = None

    model_config = {"from_attributes": True}


class BountyCreateResponse(BaseModel):
    """
    Response model for successful bounty creation.

    Used by POST /api/bounty endpoint.
    """
    id: str
    message: str


class SubmissionCreate(BaseModel):
    """
    Request model for submitting work to a bounty.

    Used by POST /api/bounty/{id}/submit endpoint.
    """
    wallet_address: str = Field(..., min_length=42, max_length=42, description="Agent's Ethereum address")
    result: str = Field(..., min_length=1, description="Agent's submitted work/result")

    @field_validator('wallet_address')
    @classmethod
    def validate_wallet(cls, v: str) -> str:
        """Validate and normalize Ethereum address"""
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid Ethereum address (must be 0x + 40 hex chars)')
        try:
            int(v, 16)  # Verify it's valid hex
        except ValueError:
            raise ValueError('Invalid hex string')
        return v.lower()


class SubmissionResponse(BaseModel):
    """
    Response model for submission data.

    Used by GET /api/bounty/{id}/submissions endpoint.
    """
    id: int
    bounty_id: str
    agent_wallet: str
    result: str
    submitted_at: datetime

    model_config = {"from_attributes": True}


class SubmissionCreateResponse(BaseModel):
    """
    Response model for successful submission creation.

    Used by POST /api/bounty/{id}/submit endpoint.
    """
    submission_id: int
    bounty_id: str
    message: str


class ErrorResponse(BaseModel):
    """
    Standard error response model.

    Used for all error responses across the API.
    """
    error: str
