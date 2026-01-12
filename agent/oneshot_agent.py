#!/usr/bin/env python3
"""
MakeMNEE One-Shot Agent

A simple agent that:
1. Connects to the API once
2. Fetches available bounties
3. Uses Claude to complete a few tasks
4. Submits the work
5. Exits (doesn't stay running)

Perfect for testing or running on-demand.
"""

import sys
import requests
import anthropic
from config import API_URL, MY_WALLET, ANTHROPIC_API_KEY, validate_config


class OneShotAgent:
    """Simple agent that processes bounties once and exits"""

    def __init__(self, max_bounties=3):
        """Initialize the one-shot agent"""
        # Validate configuration
        try:
            validate_config()
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            print("\n💡 Update your .env file with:")
            print("   - AGENT_WALLET_ADDRESS (your wallet)")
            print("   - ANTHROPIC_API_KEY (your Claude API key)")
            sys.exit(1)

        # Initialize Claude client
        self.claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.max_bounties = max_bounties

        print("🤖 MakeMNEE One-Shot Agent")
        print(f"📍 API: {API_URL}")
        print(f"📍 Wallet: {MY_WALLET}")
        print(f"📍 Max bounties to process: {max_bounties}")
        print()

    def fetch_bounties(self):
        """Fetch available bounties from the API"""
        print("🔍 Fetching available bounties...")
        try:
            response = requests.get(f"{API_URL}/bounties", timeout=10)
            response.raise_for_status()
            bounties = response.json()
            print(f"✅ Found {len(bounties)} bounties")
            return bounties
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching bounties: {e}")
            return []

    def can_handle(self, bounty):
        """Decide if this agent can handle the bounty"""
        # Skip if already completed or cancelled
        if bounty.get('status') != 0:  # 0 = Open
            return False

        # Skip physical tasks
        description_lower = bounty['description'].lower()
        skip_keywords = ['physical', 'mail', 'ship', 'call', 'phone', 'meet']
        if any(keyword in description_lower for keyword in skip_keywords):
            return False

        # This agent handles most text-based tasks
        return True

    def complete_task_with_claude(self, bounty):
        """Use Claude to complete the bounty task"""
        print(f"\n📋 Working on: {bounty['title']}")
        print(f"   💰 Reward: {bounty['amount_mnee']} MNEE")
        print(f"   🔨 Using Claude to complete the task...")

        try:
            # Construct prompt for Claude
            prompt = f"""
Please complete this task thoroughly and professionally. Provide a clear, well-structured response that addresses all aspects of the request. Be concise but comprehensive. Do not make your answer longer than needed. If a few sentences is enough, then that is eough.
            Task:  {bounty['title']}

Details:
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

            prompt += "\nComplete the task now:"

            # Call Claude API
            message = self.claude.messages.create(
                model="claude-3-haiku-20240307",  # Fast and cost-effective model
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result = message.content[0].text
            print(f"   ✅ Task completed ({len(result)} characters)")
            return result

        except anthropic.APIError as e:
            print(f"   ❌ Claude API error: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return None

    def submit_work(self, bounty_id, result):
        """Submit completed work to the API"""
        print(f"   📤 Submitting work...")

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
                return True
            else:
                print(f"   ❌ Submission failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Error submitting: {e}")
            return False

    def run(self):
        """Main execution: fetch bounties, complete tasks, submit"""
        print("="*60)
        print("Starting bounty processing...")
        print("="*60)

        # Fetch available bounties
        bounties = self.fetch_bounties()

        if not bounties:
            print("\n⚠️  No bounties available to process")
            print("   Create a bounty at https://makemnee.com to test!")
            return

        # Process bounties (up to max_bounties)
        processed = 0
        submitted = 0

        for bounty in bounties:
            if processed >= self.max_bounties:
                print(f"\n✋ Reached maximum of {self.max_bounties} bounties")
                break

            # Check if we can handle this bounty
            if not self.can_handle(bounty):
                print(f"\n⏭️  Skipping: {bounty['title']} (can't handle)")
                continue

            # Process the bounty
            processed += 1
            result = self.complete_task_with_claude(bounty)

            if result:
                # Submit the work
                if self.submit_work(bounty['id'], result):
                    submitted += 1
            else:
                print(f"   ⏭️  Skipping submission (no result)")

        # Summary
        print("\n" + "="*60)
        print("📊 Summary")
        print("="*60)
        print(f"   Bounties processed: {processed}")
        print(f"   Work submitted: {submitted}")
        print(f"   Wallet: {MY_WALLET}")
        print("\n💡 Bounty creators will review submissions and release payments")
        print("="*60 + "\n")


def main():
    """Entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="One-shot bounty agent - processes a few bounties and exits"
    )
    parser.add_argument(
        '--max',
        type=int,
        default=3,
        help='Maximum number of bounties to process (default: 3)'
    )

    args = parser.parse_args()

    try:
        agent = OneShotAgent(max_bounties=args.max)
        agent.run()
    except KeyboardInterrupt:
        print("\n\n👋 Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
