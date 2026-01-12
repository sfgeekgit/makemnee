#!/usr/bin/env python3
"""
Quick test script to verify the agent is configured correctly
"""

import sys

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        from web3 import Web3
        import anthropic
        import requests
        from dotenv import load_dotenv
        print("  ✅ All Python packages imported successfully")
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        print("  Run: pip install -r requirements.txt")
        return False

def test_config():
    """Test that configuration is loaded"""
    print("\nTesting configuration...")
    try:
        import config
        config.validate_config()
        print("  ✅ Configuration loaded and validated")
        print(f"  📍 API URL: {config.API_URL}")
        print(f"  📍 Contract: {config.CONTRACT_ADDRESS}")
        print(f"  📍 Wallet: {config.MY_WALLET}")
        return True
    except ValueError as e:
        print(f"  ⚠️  Configuration incomplete: {e}")
        print("  Update your .env file with required values")
        return False
    except Exception as e:
        print(f"  ❌ Config error: {e}")
        return False

def test_agent_class():
    """Test that the BountyAgent class can be imported"""
    print("\nTesting agent class...")
    try:
        from agent import BountyAgent
        print("  ✅ BountyAgent class imported successfully")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_connectivity():
    """Test API and RPC connectivity"""
    print("\nTesting connectivity...")

    # Test API
    try:
        import requests
        import config
        response = requests.get(f"{config.API_URL}/bounties", timeout=5)
        print(f"  ✅ API accessible: {config.API_URL}")
    except Exception as e:
        print(f"  ⚠️  API not accessible: {e}")

    # Test RPC
    try:
        from web3 import Web3
        import config
        w3 = Web3(Web3.HTTPProvider(config.ETHEREUM_RPC))
        if w3.is_connected():
            print(f"  ✅ Ethereum RPC connected: {config.ETHEREUM_RPC}")
        else:
            print(f"  ⚠️  Ethereum RPC not connected (node may not be running)")
    except Exception as e:
        print(f"  ⚠️  RPC connection error: {e}")

    # Test Claude API
    try:
        import anthropic
        import config
        if config.ANTHROPIC_API_KEY and not config.ANTHROPIC_API_KEY.startswith('sk-ant-replace'):
            client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            print(f"  ✅ Claude API key configured")
        else:
            print(f"  ⚠️  Claude API key not set (add to .env)")
    except Exception as e:
        print(f"  ⚠️  Claude API error: {e}")

def main():
    print("="*60)
    print("🧪 MakeMNEE Agent Test Suite")
    print("="*60)

    results = []
    results.append(test_imports())
    results.append(test_config())
    results.append(test_agent_class())
    test_connectivity()

    print("\n" + "="*60)
    if all(results):
        print("✅ All core tests passed!")
        print("   Your agent is ready to run.")
        print("\n   To start: python agent.py")
    else:
        print("⚠️  Some tests failed")
        print("   Fix the issues above before running the agent")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
