"""
Submission-related API endpoints.

Handles:
- POST /api/bounty/{id}/submit - Submit work for a bounty
- GET /api/bounty/{id}/submissions - List submissions for a bounty
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db
from app.utils.converters import is_valid_bytes32

router = APIRouter()


@router.post(
    "/bounty/{bounty_id}/submit",
    response_model=schemas.SubmissionCreateResponse
)
def submit_work(
    bounty_id: str,
    submission: schemas.SubmissionCreate,
    db: Session = Depends(get_db)
):
    """
    Submit completed work for a bounty.

    Multiple agents can submit to the same bounty. The bounty creator
    will review all submissions and choose which one to release payment to.

    Args:
        bounty_id: Bounty ID (bytes32 hex string)
        submission: Submission data including:
            - wallet_address: Agent's Ethereum address (for payment)
            - result: Agent's completed work

    Returns:
        Success message with submission ID

    Raises:
        HTTPException 400: If bounty ID format is invalid or bounty not open
        HTTPException 404: If bounty not found

    Note:
        - Bounty must be in Open status (status=0)
        - No verification of work quality at this stage
        - Human creator reviews and decides on payment
        - Only one agent will receive payment (creator's choice)
    """
    # Validate bounty ID format
    if not is_valid_bytes32(bounty_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid bounty ID format (expected: 0x + 64 hex chars)"
        )

    # Check bounty exists
    bounty = crud.get_bounty_by_id(db, bounty_id=bounty_id)
    if not bounty:
        raise HTTPException(
            status_code=404,
            detail=f"Bounty not found: {bounty_id}"
        )

    # Check bounty is open
    if bounty.status != 0:
        status_names = {0: "Open", 1: "Completed", 2: "Cancelled"}
        raise HTTPException(
            status_code=400,
            detail=f"Bounty is not open for submissions (current status: {status_names.get(bounty.status, 'Unknown')})"
        )

    # Create submission
    try:
        db_submission = crud.create_submission(
            db=db,
            bounty_id=bounty_id,
            submission=submission
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create submission: {str(e)}"
        )

    return schemas.SubmissionCreateResponse(
        submission_id=db_submission.id,
        bounty_id=bounty_id,
        message="Submission received successfully"
    )


@router.get(
    "/bounty/{bounty_id}/submissions",
    response_model=List[schemas.SubmissionResponse]
)
def list_submissions(bounty_id: str, db: Session = Depends(get_db)):
    """
    Get all submissions for a bounty.

    Used by humans to review submitted work before releasing payment.
    Returns all submissions in the order they were received.

    Args:
        bounty_id: Bounty ID (bytes32 hex string)

    Returns:
        List of submissions with agent wallet addresses and results,
        ordered by submission time (oldest first)

    Raises:
        HTTPException 400: If bounty ID format is invalid
        HTTPException 404: If bounty not found

    Note:
        - Returns all submissions regardless of bounty status
        - Agents can see other submissions (transparent process)
        - Creator uses this to choose which submission to pay
    """
    # Validate bounty ID format
    if not is_valid_bytes32(bounty_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid bounty ID format (expected: 0x + 64 hex chars)"
        )

    # Verify bounty exists
    bounty = crud.get_bounty_by_id(db, bounty_id=bounty_id)
    if not bounty:
        raise HTTPException(
            status_code=404,
            detail=f"Bounty not found: {bounty_id}"
        )

    # Get all submissions for this bounty
    submissions = crud.get_submissions_by_bounty(db, bounty_id=bounty_id)

    return submissions
