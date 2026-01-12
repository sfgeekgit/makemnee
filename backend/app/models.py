"""
SQLAlchemy ORM models for MakeMNEE Bounty Board.

Defines the database schema for bounties and submissions.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Bounty(Base):
    """
    Bounty model - stores metadata for bounties posted on-chain.

    Fields:
        id: Bounty ID from blockchain (bytes32 as hex string)
        title: Short title for the bounty
        description: Detailed description of what needs to be done
        creator_address: Ethereum address of bounty creator
        amount: Amount in wei (stored as string to avoid precision loss)
        amount_mnee: Amount in MNEE tokens (for display convenience)
        status: Bounty status (0=Open, 1=Completed, 2=Cancelled)
        created_at: When bounty metadata was created
        updated_at: When bounty was last updated
        completed_at: When bounty was completed (nullable)
        cancelled_at: When bounty was cancelled (nullable)
        hunter_address: Address of agent who completed the bounty (nullable)
    """
    __tablename__ = "bounties"

    # Primary key: bytes32 as hex string (66 characters: "0x" + 64 hex)
    id = Column(String(66), primary_key=True, index=True)

    # Bounty metadata
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # On-chain data
    creator_address = Column(String(42), nullable=False, index=True)
    amount = Column(String(78), nullable=False)  # Max uint256 string length
    amount_mnee = Column(Float, nullable=False)

    # Status: 0=Open, 1=Completed, 2=Cancelled (matches Solidity enum)
    status = Column(Integer, nullable=False, default=0, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Winner information
    hunter_address = Column(String(42), nullable=True)

    # Relationships
    submissions = relationship("Submission", back_populates="bounty", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Bounty {self.id[:10]}... {self.title}>"


class Submission(Base):
    """
    Submission model - stores agent submissions for bounties.

    Fields:
        id: Auto-incrementing submission ID
        bounty_id: Foreign key to bounties.id
        agent_wallet: Ethereum address of submitting agent
        result: Agent's submitted work/result
        submitted_at: When submission was made
    """
    __tablename__ = "submissions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to bounty
    bounty_id = Column(String(66), ForeignKey("bounties.id"), nullable=False, index=True)

    # Submission data
    agent_wallet = Column(String(42), nullable=False, index=True)
    result = Column(Text, nullable=False)

    # Timestamp
    submitted_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    # Relationships
    bounty = relationship("Bounty", back_populates="submissions")

    def __repr__(self):
        return f"<Submission {self.id} for Bounty {self.bounty_id[:10]}... by {self.agent_wallet[:10]}...>"


# Create indexes for common queries
Index('idx_bounty_status_created', Bounty.status, Bounty.created_at)
Index('idx_submission_bounty_time', Submission.bounty_id, Submission.submitted_at)
