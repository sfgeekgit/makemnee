#!/usr/bin/env python3
"""Generate a new Ethereum wallet for your agent"""

try:
    from eth_account import Account
except ImportError:
    print("❌ Error: eth_account not installed")
    print("Install it with: pip install eth_account")
    exit(1)

# Generate new account
account = Account.create()

print("\n" + "="*60)
print("🔐 New Ethereum Wallet Generated")
print("="*60)
print(f"\nAddress (public):")
print(f"  {account.address}")
print(f"\nPrivate Key (keep this secret!):")
print(f"  {account.key.hex()}")
print("\n" + "="*60)
print("\n⚠️  IMPORTANT:")
print("  - Save both values securely")
print("  - Never share your private key")
print("  - The agent only needs the ADDRESS (not the private key)")
print("  - Add the address to your .env file as AGENT_WALLET_ADDRESS")
print("\n" + "="*60 + "\n")
