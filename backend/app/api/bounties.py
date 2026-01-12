"""
Bounty-related API endpoints.

Handles:
- GET /api/bounties - List open bounties (with 15-minute delay)
- GET /api/bounty/{id} - Get specific bounty
- POST /api/bounty - Create bounty metadata
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db
from app.utils.converters import is_valid_bytes32
from app.utils.filters import get_one_hour_ago_timestamp

router = APIRouter()


@router.get("/bounties", response_model=List[schemas.BountyResponse])
def list_bounties(db: Session = Depends(get_db)):
    """
    List all OPEN bounties that are older than 15 minutes.

    This 15-minute delay is intentional to encourage agents to use
    blockchain event listeners for real-time discovery instead of
    polling this API endpoint.

    Returns:
        List of open bounties created more than 15 minutes ago,
        ordered by creation time (newest first)

    Note:
        - Only returns bounties with status=0 (Open)
        - Bounties less than 15 minutes old are excluded
        - Use blockchain event listeners for real-time discovery
        - Call this endpoint once on startup, then rely on events
    """
    one_hour_ago = get_one_hour_ago_timestamp()

    bounties = crud.get_bounties_before_time(
        db=db,
        status=0,  # Open only
        before_time=one_hour_ago
    )

    return bounties


@router.get("/my-bounties/{creator_address}", response_model=List[schemas.BountyResponse])
def get_my_bounties(creator_address: str, db: Session = Depends(get_db)):
    """
    Get all OPEN bounties created by a specific address (no time delay).

    This endpoint allows users to immediately see their own bounties
    without waiting for the 15-minute delay. Prevents scraping since
    it requires knowing the specific address.

    Args:
        creator_address: Ethereum address of bounty creator

    Returns:
        List of open bounties created by this address,
        ordered by creation time (newest first)

    Raises:
        HTTPException 400: If address format is invalid

    Note:
        - Only returns bounties with status=0 (Open)
        - Cancelled and completed bounties are excluded
    """
    # Validate ethereum address format
    if not creator_address.startswith('0x') or len(creator_address) != 42:
        raise HTTPException(
            status_code=400,
            detail="Invalid Ethereum address format"
        )

    # Get bounties by creator
    bounties = crud.get_bounties_by_creator(
        db=db,
        creator_address=creator_address.lower()
    )

    # Filter to only show Open bounties (status=0)
    open_bounties = [b for b in bounties if b.status == 0]

    return open_bounties


@router.get("/bounty/{bounty_id}", response_model=schemas.BountyResponse)
def get_bounty(bounty_id: str, db: Session = Depends(get_db)):
    """
    Get details for a specific bounty by ID.

    No time restrictions - returns any bounty regardless of age.
    This endpoint is used to fetch metadata after discovering a
    bounty via blockchain events.

    Args:
        bounty_id: Bounty ID (bytes32 hex string, e.g., "0x7a3b...")

    Returns:
        Bounty details including metadata and current status

    Raises:
        HTTPException 400: If bounty ID format is invalid
        HTTPException 404: If bounty not found
    """
    # Validate bytes32 format
    if not is_valid_bytes32(bounty_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid bounty ID format (expected: 0x + 64 hex chars)"
        )

    # Get bounty from database
    bounty = crud.get_bounty_by_id(db, bounty_id=bounty_id)

    if bounty is None:
        raise HTTPException(
            status_code=404,
            detail=f"Bounty not found: {bounty_id}"
        )

    return bounty


@router.post("/bounty", response_model=schemas.BountyCreateResponse)
def create_bounty(
    bounty: schemas.BountyCreate,
    db: Session = Depends(get_db)
):
    """
    Store bounty metadata after on-chain transaction.

    This endpoint is called by the frontend after a successful
    createBounty() transaction on the blockchain. It stores the
    bounty metadata (title, description) that's too expensive
    to store on-chain.

    Args:
        bounty: Bounty creation data including:
            - id: Bounty ID from blockchain event
            - title: Bounty title
            - description: Detailed description
            - creator_address: Creator's Ethereum address
            - amount: Amount in wei (as string)

    Returns:
        Success message with bounty ID

    Raises:
        HTTPException 400: If bounty already exists or data is invalid

    Note:
        - The bounty must already exist on-chain
        - This only stores metadata, not the actual MNEE tokens
        - Bounty ID comes from BountyCreated event
    """
    # Check if bounty already exists
    existing = crud.get_bounty_by_id(db, bounty_id=bounty.id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Bounty with ID {bounty.id} already exists"
        )

    # Create bounty metadata
    try:
        db_bounty = crud.create_bounty(db=db, bounty=bounty)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create bounty: {str(e)}"
        )

    return schemas.BountyCreateResponse(
        id=db_bounty.id,
        message="Bounty metadata created successfully"
    )


@router.patch("/bounty/{bounty_id}/status", response_model=schemas.BountyResponse)
def update_bounty_status(
    bounty_id: str,
    status_update: schemas.BountyStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update bounty status after on-chain transaction.

    This endpoint is called by the frontend after a successful
    cancelBounty() or releaseBounty() transaction on the blockchain.
    It updates the bounty status in the database to match the on-chain state.

    Args:
        bounty_id: Bounty ID (bytes32 hex string)
        status_update: Status update data including:
            - status: New status (0=Open, 1=Completed, 2=Cancelled)
            - hunter_address: Hunter address (required for status=1)

    Returns:
        Updated bounty data

    Raises:
        HTTPException 400: If bounty ID format is invalid or update fails
        HTTPException 404: If bounty not found

    Note:
        - This only updates the database, not the blockchain
        - The blockchain transaction must complete before calling this
        - For status=1 (Completed), hunter_address is required
    """
    # Validate bytes32 format
    if not is_valid_bytes32(bounty_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid bounty ID format (expected: 0x + 64 hex chars)"
        )

    # Validate status=1 requires hunter_address
    if status_update.status == 1 and not status_update.hunter_address:
        raise HTTPException(
            status_code=400,
            detail="hunter_address is required for completed bounties"
        )

    # Update bounty status
    updated_bounty = crud.update_bounty_status(
        db=db,
        bounty_id=bounty_id,
        new_status=status_update.status,
        hunter_address=status_update.hunter_address
    )

    if updated_bounty is None:
        raise HTTPException(
            status_code=404,
            detail=f"Bounty not found: {bounty_id}"
        )

    return updated_bounty
