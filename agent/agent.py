#!/usr/bin/env python3
"""
MakeMNEE Bounty Agent

An autonomous AI agent that:
1. Listens to blockchain events for new bounties
2. Uses Claude API to complete tasks
3. Submits results and earns MNEE
"""

import time
import requests
from web3 import Web3
import anthropic

from config import (
    API_URL,
    ETHEREUM_RPC,
    CONTRACT_ADDRESS,
    MY_WALLET,
    ANTHROPIC_API_KEY,
    BOUNTYBOARD_ABI,
    validate_config
)


class BountyAgent:
    """Autonomous agent that discovers and completes bounties"""

    def __init__(self):
        """Initialize the agent and connect to Ethereum"""
        # Validate configuration
        validate_config()

        # Connect to Ethereum
        self.w3 = Web3(Web3.HTTPProvider(ETHEREUM_RPC))
        if not self.w3.is_connected():
            raise Exception("Failed to connect to Ethereum node")

        # Load contract
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=BOUNTYBOARD_ABI
        )

        # Initialize Claude client
        self.claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Track processed bounties to avoid duplicates
        self.processed_bounties = set()

        print("🤖 MakeMNEE Bounty Agent Starting...")
        print(f"✅ Connected to Ethereum: {ETHEREUM_RPC}")
        print(f"✅ Contract: {CONTRACT_ADDRESS}")
        print(f"✅ Agent wallet: {MY_WALLET}")
        print(f"✅ Claude API: Configured")

    def process_backlog(self):
        """Phase 1: Get existing bounties on startup"""
        print("\n🔍 Checking for existing bounties...")

        try:
            response = requests.get(f"{API_URL}/bounties", timeout=10)
            response.raise_for_status()
            bounties = response.json()

            print(f"Found {len(bounties)} existing bounties")

            for bounty in bounties:
                if bounty['id'] not in self.processed_bounties:
                    self.handle_bounty(bounty)

        except requests.exceptions.RequestException as e:
            print(f"⚠️  Warning: Could not fetch backlog: {e}")
            print("   (This is okay - will continue listening for new bounties)")
        except Exception as e:
            print(f"❌ Error processing backlog: {e}")

    def listen_for_new_bounties(self):
        """Phase 2: Listen to blockchain events for new bounties"""
        print("\n👂 Listening for new bounties on the blockchain...")
        print("   (Press Ctrl+C to stop)\n")

        # Create event filter
        event_filter = self.contract.events.BountyCreated.create_filter(
            fromBlock='latest'
        )

        while True:
            try:
                # Check for new events
                for event in event_filter.get_new_entries():
                    bounty_id = event['args']['id'].hex()
                    amount = event['args']['amount']
                    creator = event['args']['creator']

                    print(f"\n🎯 New bounty detected on blockchain!")
                    print(f"   ID: {bounty_id}")
                    print(f"   Amount: {amount / 10**18:.2f} MNEE")
                    print(f"   Creator: {creator}")

                    # Fetch metadata from API and handle
                    self.fetch_and_handle_bounty(bounty_id)

                # Sleep briefly before checking again
                time.sleep(10)

            except KeyboardInterrupt:
                print("\n\n👋 Agent shutting down gracefully...")
                break
            except Exception as e:
                print(f"❌ Error in event loop: {e}")
                time.sleep(30)  # Wait longer on error

    def fetch_and_handle_bounty(self, bounty_id):
        """Fetch bounty metadata from API and process it"""
        try:
            response = requests.get(f"{API_URL}/bounty/{bounty_id}", timeout=10)
            if response.status_code == 200:
                bounty = response.json()
                if bounty['id'] not in self.processed_bounties:
                    self.handle_bounty(bounty)
            else:
                print(f"⚠️  Could not fetch bounty {bounty_id}: {response.status_code}")

        except Exception as e:
            print(f"❌ Error fetching bounty: {e}")

    def handle_bounty(self, bounty):
        """Process a bounty: decide if we can do it, do the work, submit"""
        bounty_id = bounty['id']

        # Check if already processed
        if bounty_id in self.processed_bounties:
            return

        # Check if bounty is still open
        if bounty.get('status') != 0:  # 0 = Open
            print(f"   ⏭️  Skipping (bounty is not open)")
            self.processed_bounties.add(bounty_id)
            return

        print(f"\n📋 Processing bounty: {bounty['title']}")
        print(f"   Description: {bounty['description'][:100]}...")
        print(f"   Reward: {bounty['amount_mnee']} MNEE")

        # Check if we can handle this bounty
        if not self.can_handle(bounty):
            print("   ⏭️  Skipping (can't handle this type)")
            self.processed_bounties.add(bounty_id)
            return

        # Do the work
        print("   🔨 Working on it with Claude...")
        result = self.do_work(bounty)

        if result:
            # Submit the result
            self.submit_work(bounty_id, result)
            self.processed_bounties.add(bounty_id)
        else:
            print("   ❌ Failed to complete work")

    def can_handle(self, bounty):
        """Decide if this agent can handle this bounty"""
        # This agent can handle most text-based tasks
        # You can customize this logic for your agent's capabilities

        description_lower = bounty['description'].lower()
        title_lower = bounty['title'].lower()

        # Skip bounties that require physical actions or external tools
        skip_keywords = ['physical', 'mail', 'ship', 'call', 'phone']
        if any(keyword in description_lower for keyword in skip_keywords):
            return False

        # This agent is good at text-based tasks
        good_keywords = [
            'summarize', 'summary', 'analyze', 'analysis', 'research',
            'explain', 'write', 'draft', 'review', 'translate',
            'compare', 'evaluate', 'describe', 'list', 'outline'
        ]

        # Check if any good keywords match
        combined_text = title_lower + " " + description_lower
        if any(keyword in combined_text for keyword in good_keywords):
            return True

        # By default, try to handle it
        # (Claude is versatile and can handle many task types)
        return True

    def do_work(self, bounty):
        """Use Claude to complete the bounty task"""
        try:
            # Construct a detailed prompt for Claude
            prompt = f"""

Please complete this task thoroughly and professionally. Provide a clear, well-structured response that addresses all aspects of the request. Be concise but comprehensive. Do not make your answer longer than needed. If a few sentences is enough, then that is eough.

Task Title: {bounty['title']}

Task Description:
{bounty['description']}
"""

            # Add attachments/reference URLs if present
            if bounty.get('attachments'):
                attachments_list = [url.strip() for url in bounty['attachments'].split(',') if url.strip()]
                if attachments_list:
                    prompt += "\nReference Materials (URLs):\n"
                    for url in attachments_list:
                        prompt += f"- {url}\n"
                    prompt += "\n"

            prompt += "\n"

            # Call Claude API
            message = self.claude.messages.create(
                model="claude-3-haiku-20240307",  # Fast and cost-effective model
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result = message.content[0].text

            print(f"   ✅ Work completed ({len(result)} characters)")
            return result

        except anthropic.APIError as e:
            print(f"   ❌ Claude API error: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return None

    def submit_work(self, bounty_id, result):
        """Submit completed work to the API"""
        print("   📤 Submitting work...")

        try:
            response = requests.post(
                f"{API_URL}/bounty/{bounty_id}/submit",
                json={
                    "wallet_address": MY_WALLET,
                    "result": result
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Submitted! Submission ID: {data['submission_id']}")
                print(f"   💰 Waiting for creator to review and release payment...")
            else:
                print(f"   ❌ Submission failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   Response: {response.text[:200]}")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
        except Exception as e:
            print(f"   ❌ Error submitting: {e}")

    def run(self):
        """Main agent loop"""
        print("\n" + "="*60)
        print("🤖 MakeMNEE Autonomous Bounty Agent")
        print("="*60)

        # Phase 1: Process existing bounties
        self.process_backlog()

        # Phase 2: Listen for new bounties
        self.listen_for_new_bounties()


def main():
    """Entry point"""
    try:
        agent = BountyAgent()
        agent.run()
    except KeyboardInterrupt:
        print("\n\n👋 Agent stopped by user")
    except ValueError as e:
        print(f"\n❌ Configuration Error:")
        print(f"   {e}")
        print(f"\n💡 Please check your .env file and ensure all required variables are set.")
        print(f"   See .env.example for reference.")
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
