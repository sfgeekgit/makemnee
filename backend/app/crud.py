"""
CRUD (Create, Read, Update, Delete) operations for database.

All database interaction logic is centralized here.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app import models, schemas
from app.utils.converters import wei_to_mnee


# Bounty CRUD operations

def create_bounty(db: Session, bounty: schemas.BountyCreate) -> models.Bounty:
    """
    Create a new bounty with metadata.

    Args:
        db: Database session
        bounty: Bounty creation data

    Returns:
        Created bounty model

    Raises:
        IntegrityError: If bounty ID already exists
    """
    db_bounty = models.Bounty(
        id=bounty.id.lower(),
        title=bounty.title,
        description=bounty.description,
        creator_address=bounty.creator_address.lower(),
        amount=bounty.amount,
        amount_mnee=wei_to_mnee(bounty.amount),
        status=0  # Open
    )
    db.add(db_bounty)
    db.commit()
    db.refresh(db_bounty)
    return db_bounty


def get_bounty_by_id(db: Session, bounty_id: str) -> Optional[models.Bounty]:
    """
    Get a bounty by its ID.

    Args:
        db: Database session
        bounty_id: Bounty ID (bytes32 hex string)

    Returns:
        Bounty model if found, None otherwise
    """
    return db.query(models.Bounty).filter(
        models.Bounty.id == bounty_id.lower()
    ).first()


def get_bounties_before_time(
    db: Session,
    status: int,
    before_time: datetime
) -> List[models.Bounty]:
    """
    Get bounties with specific status created before a certain time.

    This is used for the 15-minute delay filter.

    Args:
        db: Database session
        status: Bounty status (0=Open, 1=Completed, 2=Cancelled)
        before_time: Only return bounties created before this time

    Returns:
        List of bounty models, ordered by creation time (newest first)

    Example:
        Get open bounties older than 15 minutes:
        >>> one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        >>> bounties = get_bounties_before_time(db, status=0, before_time=one_hour_ago)
    """
    return db.query(models.Bounty).filter(
        models.Bounty.status == status,
        models.Bounty.created_at < before_time
    ).order_by(models.Bounty.created_at.desc()).all()


def get_all_bounties(db: Session, status: Optional[int] = None) -> List[models.Bounty]:
    """
    Get all bounties, optionally filtered by status.

    Args:
        db: Database session
        status: Optional status filter (0=Open, 1=Completed, 2=Cancelled)

    Returns:
        List of bounty models, ordered by creation time (newest first)
    """
    query = db.query(models.Bounty)
    if status is not None:
        query = query.filter(models.Bounty.status == status)
    return query.order_by(models.Bounty.created_at.desc()).all()


def get_bounties_by_creator(db: Session, creator_address: str) -> List[models.Bounty]:
    """
    Get all bounties created by a specific address (no time filter).

    Args:
        db: Database session
        creator_address: Ethereum address of bounty creator (lowercase)

    Returns:
        List of bounty models, ordered by creation time (newest first)
    """
    return db.query(models.Bounty).filter(
        models.Bounty.creator_address == creator_address.lower()
    ).order_by(models.Bounty.created_at.desc()).all()


def update_bounty_status(
    db: Session,
    bounty_id: str,
    new_status: int,
    hunter_address: Optional[str] = None
) -> Optional[models.Bounty]:
    """
    Update bounty status (used for completion or cancellation).

    Args:
        db: Database session
        bounty_id: Bounty ID
        new_status: New status (1=Completed, 2=Cancelled)
        hunter_address: Optional hunter address (for completed bounties)

    Returns:
        Updated bounty model if found, None otherwise
    """
    bounty = get_bounty_by_id(db, bounty_id)
    if bounty:
        bounty.status = new_status
        bounty.updated_at = datetime.utcnow()

        if new_status == 1:  # Completed
            bounty.completed_at = datetime.utcnow()
            if hunter_address:
                bounty.hunter_address = hunter_address.lower()
        elif new_status == 2:  # Cancelled
            bounty.cancelled_at = datetime.utcnow()

        db.commit()
        db.refresh(bounty)
    return bounty


# Submission CRUD operations

def create_submission(
    db: Session,
    bounty_id: str,
    submission: schemas.SubmissionCreate
) -> models.Submission:
    """
    Create a new submission for a bounty.

    Args:
        db: Database session
        bounty_id: Bounty ID
        submission: Submission data

    Returns:
        Created submission model

    Raises:
        IntegrityError: If bounty doesn't exist
    """
    db_submission = models.Submission(
        bounty_id=bounty_id.lower(),
        agent_wallet=submission.wallet_address.lower(),
        result=submission.result
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission


def get_submissions_by_bounty(
    db: Session,
    bounty_id: str
) -> List[models.Submission]:
    """
    Get all submissions for a bounty.

    Args:
        db: Database session
        bounty_id: Bounty ID

    Returns:
        List of submission models, ordered by submission time (oldest first)
    """
    return db.query(models.Submission).filter(
        models.Submission.bounty_id == bounty_id.lower()
    ).order_by(models.Submission.submitted_at.asc()).all()


def get_submission_by_id(
    db: Session,
    submission_id: int
) -> Optional[models.Submission]:
    """
    Get a submission by its ID.

    Args:
        db: Database session
        submission_id: Submission ID

    Returns:
        Submission model if found, None otherwise
    """
    return db.query(models.Submission).filter(
        models.Submission.id == submission_id
    ).first()


def count_submissions_for_bounty(
    db: Session,
    bounty_id: str
) -> int:
    """
    Count number of submissions for a bounty.

    Args:
        db: Database session
        bounty_id: Bounty ID

    Returns:
        Number of submissions
    """
    return db.query(models.Submission).filter(
        models.Submission.bounty_id == bounty_id.lower()
    ).count()
