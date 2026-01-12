"""Configuration for MakeMNEE Agent"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_URL = os.getenv("MAKEMNEE_API_URL", "https://makemnee.com/api")

# Blockchain Configuration
ETHEREUM_RPC = os.getenv("ETHEREUM_RPC_URL")
CONTRACT_ADDRESS = os.getenv("BOUNTYBOARD_CONTRACT_ADDRESS")

# Agent Configuration
MY_WALLET = os.getenv("AGENT_WALLET_ADDRESS")

# Claude API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# BountyBoard Contract ABI (relevant events and functions)
BOUNTYBOARD_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "id", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "creator", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "BountyCreated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "id", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "hunter", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "BountyCompleted",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "id", "type": "bytes32"}
        ],
        "name": "BountyCancelled",
        "type": "event"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "id", "type": "bytes32"}],
        "name": "getBounty",
        "outputs": [
            {"internalType": "address", "name": "creator", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint8", "name": "status", "type": "uint8"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Validate configuration
def validate_config():
    """Validate that required configuration is set"""
    errors = []

    if not ETHEREUM_RPC:
        errors.append("ETHEREUM_RPC_URL not set")
    if not CONTRACT_ADDRESS:
        errors.append("BOUNTYBOARD_CONTRACT_ADDRESS not set")
    if not MY_WALLET:
        errors.append("AGENT_WALLET_ADDRESS not set")
    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY not set (Claude API won't work)")

    if errors:
        raise ValueError(f"Configuration errors:\n  - " + "\n  - ".join(errors))
