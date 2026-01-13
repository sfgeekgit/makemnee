#!/usr/bin/env python3
"""Generate a new Ethereum wallet for your agent"""

import os
import re

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

# Save to .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')

try:
    # Read existing .env file
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
    else:
        env_content = ""

    # Check if a private key already exists and archive it
    existing_key_match = re.search(r'^AGENT_WALLET_PRIVATE_KEY=(.+)$', env_content, re.MULTILINE)
    existing_addr_match = re.search(r'^AGENT_WALLET_ADDRESS=(.+)$', env_content, re.MULTILINE)

    if existing_key_match and existing_key_match.group(1).strip():
        old_key = existing_key_match.group(1).strip()
        old_addr = existing_addr_match.group(1).strip() if existing_addr_match else "unknown"

        print("\n📦 Archiving old wallet key to AGENT_WALLET_OLD_KEYS...")

        # Get existing old keys array
        old_keys_match = re.search(r'^AGENT_WALLET_OLD_KEYS=(.+)$', env_content, re.MULTILINE)
        if old_keys_match:
            # Append to existing array
            old_keys_value = old_keys_match.group(1).strip()
            new_old_keys = f"{old_keys_value},{old_addr}:{old_key}"
            env_content = re.sub(
                r'^AGENT_WALLET_OLD_KEYS=.*$',
                f'AGENT_WALLET_OLD_KEYS={new_old_keys}',
                env_content,
                flags=re.MULTILINE
            )
        else:
            # Create new array
            env_content += f'\nAGENT_WALLET_OLD_KEYS={old_addr}:{old_key}'

    # Update or add AGENT_WALLET_ADDRESS
    if re.search(r'^AGENT_WALLET_ADDRESS=', env_content, re.MULTILINE):
        env_content = re.sub(
            r'^AGENT_WALLET_ADDRESS=.*$',
            f'AGENT_WALLET_ADDRESS={account.address}',
            env_content,
            flags=re.MULTILINE
        )
    else:
        env_content += f'\nAGENT_WALLET_ADDRESS={account.address}'

    # Update or add AGENT_WALLET_PRIVATE_KEY
    if re.search(r'^AGENT_WALLET_PRIVATE_KEY=', env_content, re.MULTILINE):
        env_content = re.sub(
            r'^AGENT_WALLET_PRIVATE_KEY=.*$',
            f'AGENT_WALLET_PRIVATE_KEY={account.key.hex()}',
            env_content,
            flags=re.MULTILINE
        )
    else:
        env_content += f'\nAGENT_WALLET_PRIVATE_KEY={account.key.hex()}'

    # Write back to .env
    with open(env_path, 'w') as f:
        f.write(env_content)

    print(f"\n✅ Saved to {env_path}")
    if existing_key_match:
        print(f"   Old key archived in AGENT_WALLET_OLD_KEYS")

except Exception as e:
    print(f"\n⚠️  Could not save to .env: {e}")
    print("   Please save the values manually")

print("\n" + "="*60)
print("\n⚠️  IMPORTANT:")
print("  - Private key saved to .env (NOT checked into git)")
print("  - Never share your private key")
print("  - Never commit .env to git")
print("  - You can now transfer tokens FROM this wallet to your main wallet")
print("\n" + "="*60 + "\n")
