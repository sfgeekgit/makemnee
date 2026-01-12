#!/usr/bin/env python3
"""
MakeMNEE Example Agent - Comprehensive Reference Implementation

This is a fully-featured example agent that demonstrates all capabilities
of the MakeMNEE bounty system. Copy this file and customize it for your needs.

Features demonstrated:
- Blockchain event listening for real-time bounty discovery
- API polling for backlog processing
- Task filtering based on capabilities
- Claude AI integration for task completion
- Attachment/reference URL handling
- Error handling and retry logic
- Configurable behavior with feature flags
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


# ============================================================================
# CONFIGURATION - Customize these settings for your agent
# ============================================================================

# Feature flags - Enable/disable optional behaviors
ENABLE_BLOCKCHAIN_EVENTS = True  # Listen to blockchain events in real-time
ENABLE_BACKLOG_PROCESSING = True  # Process existing bounties on startup
ENABLE_TASK_FILTERING = True     # Filter bounties based on capabilities
ENABLE_ATTACHMENT_URLS = True    # Include attachment URLs in prompts
ENABLE_VERBOSE_LOGGING = True    # Print detailed logs

# Agent behavior settings
MAX_BACKLOG_BOUNTIES = 10        # Maximum bounties to process from backlog
POLLING_INTERVAL_SECONDS = 10    # How often to check for new events
RETRY_ON_ERROR_SECONDS = 30      # How long to wait after errors

# Claude model selection
# Options: "claude-3-haiku-20240307" (fast/cheap),
#          "claude-3-5-sonnet-20241022" (smart/expensive)
CLAUDE_MODEL = "claude-3-haiku-20240307"
CLAUDE_MAX_TOKENS = 4096

# Task filtering - Keywords that indicate tasks this agent can handle
GOOD_TASK_KEYWORDS = [
    'summarize', 'summary', 'analyze', 'analysis', 'research',
    'explain', 'write', 'draft', 'review', 'translate',
    'compare', 'evaluate', 'describe', 'list', 'outline',
    'calculate', 'solve', 'answer', 'question'
]

# Task filtering - Keywords that indicate tasks this agent should skip
SKIP_TASK_KEYWORDS = [
    'physical', 'mail', 'ship', 'call', 'phone', 'meet',
    'in-person', 'video call', 'voice', 'install software'
]


# ============================================================================
# AGENT CLASS - Main implementation
# ============================================================================

class ExampleBountyAgent:
    """
    Example autonomous agent that discovers and completes bounties.

    This agent demonstrates a complete workflow:
    1. Connects to Ethereum blockchain and API
    2. Processes existing bounties (backlog)
    3. Listens for new bounties via blockchain events
    4. Evaluates whether it can complete each task
    5. Uses Claude AI to complete the work
    6. Submits results to earn MNEE
    """

    def __init__(self):
        """Initialize the agent and connect to required services"""

        # Validate configuration - will raise ValueError if invalid
        validate_config()

        # Initialize blockchain connection (if enabled)
        if ENABLE_BLOCKCHAIN_EVENTS:
            self.w3 = Web3(Web3.HTTPProvider(ETHEREUM_RPC))
            if not self.w3.is_connected():
                raise Exception(f"Failed to connect to Ethereum node: {ETHEREUM_RPC}")

            # Load the BountyBoard smart contract
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACT_ADDRESS),
                abi=BOUNTYBOARD_ABI
            )
        else:
            self.w3 = None
            self.contract = None

        # Initialize Claude AI client
        self.claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Track which bounties we've already processed (avoid duplicates)
        self.processed_bounties = set()

        # Print startup information
        self._print_startup_info()

    def _print_startup_info(self):
        """Print agent configuration and status"""
        print("\n" + "="*70)
        print("🤖 MakeMNEE Example Agent - Starting Up")
        print("="*70)
        print(f"✅ Agent wallet: {MY_WALLET}")
        print(f"✅ API endpoint: {API_URL}")
        print(f"✅ Claude model: {CLAUDE_MODEL}")

        if ENABLE_BLOCKCHAIN_EVENTS:
            print(f"✅ Ethereum RPC: {ETHEREUM_RPC}")
            print(f"✅ Contract: {CONTRACT_ADDRESS}")
        else:
            print("⚠️  Blockchain events: DISABLED (API-only mode)")

        print("\nFeature flags:")
        print(f"  - Blockchain events: {'✅' if ENABLE_BLOCKCHAIN_EVENTS else '❌'}")
        print(f"  - Backlog processing: {'✅' if ENABLE_BACKLOG_PROCESSING else '❌'}")
        print(f"  - Task filtering: {'✅' if ENABLE_TASK_FILTERING else '❌'}")
        print(f"  - Attachment URLs: {'✅' if ENABLE_ATTACHMENT_URLS else '❌'}")
        print(f"  - Verbose logging: {'✅' if ENABLE_VERBOSE_LOGGING else '❌'}")
        print("="*70 + "\n")

    # ========================================================================
    # PHASE 1: BACKLOG PROCESSING
    # ========================================================================

    def process_backlog(self):
        """
        Process existing bounties from the API.

        This runs once at startup to catch up on any bounties that were
        posted before the agent started. The API returns bounties older
        than 15 minutes to encourage using blockchain events for new ones.
        """
        if not ENABLE_BACKLOG_PROCESSING:
            print("⏭️  Backlog processing disabled\n")
            return

        print("🔍 Phase 1: Processing existing bounties from API...")

        try:
            # Fetch bounties from the API
            response = requests.get(f"{API_URL}/bounties", timeout=10)
            response.raise_for_status()
            bounties = response.json()

            print(f"   Found {len(bounties)} existing bounties")

            # Limit how many we process from backlog (avoid overwhelming startup)
            bounties_to_process = bounties[:MAX_BACKLOG_BOUNTIES]

            if len(bounties) > MAX_BACKLOG_BOUNTIES:
                print(f"   (Processing first {MAX_BACKLOG_BOUNTIES} only)")

            # Process each bounty
            processed_count = 0
            for bounty in bounties_to_process:
                if bounty['id'] not in self.processed_bounties:
                    self.handle_bounty(bounty)
                    processed_count += 1

            print(f"✅ Backlog processing complete ({processed_count} bounties processed)\n")

        except requests.exceptions.RequestException as e:
            print(f"⚠️  Warning: Could not fetch backlog: {e}")
            print("   (This is okay - will continue listening for new bounties)\n")
        except Exception as e:
            print(f"❌ Error processing backlog: {e}\n")

    # ========================================================================
    # PHASE 2: EVENT LISTENING
    # ========================================================================

    def listen_for_new_bounties(self):
        """
        Listen to blockchain events for new bounties in real-time.

        This monitors the BountyBoard contract for BountyCreated events.
        When a new bounty is posted, we fetch its metadata from the API
        and process it immediately (no 15-minute delay).
        """
        if not ENABLE_BLOCKCHAIN_EVENTS:
            print("⚠️  Blockchain event listening disabled")
            print("   Agent will only process backlog and exit\n")
            return

        print("👂 Phase 2: Listening for new bounties on blockchain...")
        print("   (Press Ctrl+C to stop)\n")

        # Create event filter to monitor for new BountyCreated events
        event_filter = self.contract.events.BountyCreated.create_filter(
            fromBlock='latest'
        )

        # Main event loop
        while True:
            try:
                # Check for new events
                for event in event_filter.get_new_entries():
                    # Extract event data
                    bounty_id = event['args']['id'].hex()
                    amount = event['args']['amount']
                    creator = event['args']['creator']

                    print(f"\n🎯 NEW BOUNTY DETECTED!")
                    print(f"   ID: {bounty_id}")
                    print(f"   Amount: {amount / 10**18:.2f} MNEE")
                    print(f"   Creator: {creator}")

                    # Fetch full metadata from API and process
                    self.fetch_and_handle_bounty(bounty_id)

                # Sleep briefly before checking again
                time.sleep(POLLING_INTERVAL_SECONDS)

            except KeyboardInterrupt:
                print("\n\n👋 Agent shutting down gracefully...")
                break
            except Exception as e:
                print(f"❌ Error in event loop: {e}")
                print(f"   Retrying in {RETRY_ON_ERROR_SECONDS} seconds...")
                time.sleep(RETRY_ON_ERROR_SECONDS)

    def fetch_and_handle_bounty(self, bounty_id):
        """
        Fetch bounty metadata from API and process it.

        Args:
            bounty_id: The bytes32 bounty ID from the blockchain event
        """
        try:
            response = requests.get(f"{API_URL}/bounty/{bounty_id}", timeout=10)

            if response.status_code == 200:
                bounty = response.json()

                # Only process if we haven't seen it before
                if bounty['id'] not in self.processed_bounties:
                    self.handle_bounty(bounty)
                else:
                    if ENABLE_VERBOSE_LOGGING:
                        print(f"   ⏭️  Already processed this bounty")
            else:
                print(f"⚠️  Could not fetch bounty {bounty_id}: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ Error fetching bounty metadata: {e}")

    # ========================================================================
    # BOUNTY PROCESSING
    # ========================================================================

    def handle_bounty(self, bounty):
        """
        Main bounty processing logic.

        This orchestrates the entire workflow:
        1. Check if we've processed it already
        2. Check if bounty is still open
        3. Decide if we can handle this task type
        4. Complete the work using Claude
        5. Submit the result

        Args:
            bounty: Bounty dictionary from API with metadata
        """
        bounty_id = bounty['id']

        # Skip if already processed
        if bounty_id in self.processed_bounties:
            return

        # Check if bounty is still open (status=0 means Open)
        if bounty.get('status') != 0:
            if ENABLE_VERBOSE_LOGGING:
                print(f"   ⏭️  Skipping bounty {bounty_id[:10]}... (not open)")
            self.processed_bounties.add(bounty_id)
            return

        # Print bounty information
        print(f"\n📋 Processing bounty:")
        print(f"   Title: {bounty['title']}")
        print(f"   Description: {bounty['description'][:100]}...")
        print(f"   Reward: {bounty['amount_mnee']} MNEE")

        # Print attachments if present
        if ENABLE_ATTACHMENT_URLS and bounty.get('attachments'):
            attachments = [url.strip() for url in bounty['attachments'].split(',') if url.strip()]
            if attachments:
                print(f"   Attachments: {len(attachments)} URL(s)")
                if ENABLE_VERBOSE_LOGGING:
                    for url in attachments:
                        print(f"     - {url}")

        # Check if we can handle this bounty
        if ENABLE_TASK_FILTERING and not self.can_handle_bounty(bounty):
            print("   ⏭️  Skipping (outside agent capabilities)")
            self.processed_bounties.add(bounty_id)
            return

        # Do the work!
        print("   🔨 Working on task with Claude AI...")
        result = self.complete_task(bounty)

        if result:
            # Submit the completed work
            self.submit_result(bounty_id, result)
            self.processed_bounties.add(bounty_id)
        else:
            print("   ❌ Failed to complete task")
            self.processed_bounties.add(bounty_id)

    # ========================================================================
    # TASK FILTERING
    # ========================================================================

    def can_handle_bounty(self, bounty):
        """
        Decide whether this agent can handle a specific bounty.

        This is where you customize which tasks your agent accepts.
        The default implementation:
        - Skips tasks with physical requirements
        - Accepts tasks that match known capabilities
        - Accepts most text-based tasks by default

        Args:
            bounty: Bounty dictionary from API

        Returns:
            bool: True if agent should attempt this bounty
        """
        description = bounty['description'].lower()
        title = bounty['title'].lower()
        combined_text = f"{title} {description}"

        # Skip tasks that require physical actions or external tools
        for skip_keyword in SKIP_TASK_KEYWORDS:
            if skip_keyword in combined_text:
                if ENABLE_VERBOSE_LOGGING:
                    print(f"   Filtering: Found skip keyword '{skip_keyword}'")
                return False

        # Prioritize tasks that match our good keywords
        for good_keyword in GOOD_TASK_KEYWORDS:
            if good_keyword in combined_text:
                if ENABLE_VERBOSE_LOGGING:
                    print(f"   Match: Found capability keyword '{good_keyword}'")
                return True

        # By default, try to handle it
        # Claude is versatile and can handle many types of text tasks
        if ENABLE_VERBOSE_LOGGING:
            print("   Default: Accepting task (no specific filtering match)")
        return True

    # ========================================================================
    # TASK COMPLETION
    # ========================================================================

    def complete_task(self, bounty):
        """
        Use Claude AI to complete the bounty task.

        This constructs a detailed prompt with all relevant information
        and sends it to Claude. The response becomes our submission.

        Args:
            bounty: Bounty dictionary from API

        Returns:
            str: Completed work, or None if failed
        """
        try:
            # Build the prompt with task details
            prompt = self._build_task_prompt(bounty)

            if ENABLE_VERBOSE_LOGGING:
                print(f"   Prompt length: {len(prompt)} characters")

            # Call Claude API
            message = self.claude.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract the text response
            result = message.content[0].text

            print(f"   ✅ Task completed ({len(result)} characters)")

            if ENABLE_VERBOSE_LOGGING:
                print(f"   Preview: {result[:100]}...")

            return result

        except anthropic.APIError as e:
            print(f"   ❌ Claude API error: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return None

    def _build_task_prompt(self, bounty):
        """
        Construct a detailed prompt for Claude based on bounty data.

        This includes:
        - Instructions for how to respond
        - The task title and description
        - Reference URLs (if attachments are enabled and present)

        Args:
            bounty: Bounty dictionary from API

        Returns:
            str: Complete prompt for Claude
        """
        # Start with instructions
        prompt = """
Please complete this task thoroughly and professionally. Provide a clear,
well-structured response that addresses all aspects of the request.
Be concise but comprehensive. Do not make your answer longer than needed.
If a few sentences is enough, then that is enough.

"""

        # Add task information
        prompt += f"Task Title: {bounty['title']}\n\n"
        prompt += f"Task Description:\n{bounty['description']}\n"

        # Add attachment URLs if enabled and present
        if ENABLE_ATTACHMENT_URLS and bounty.get('attachments'):
            attachments_list = [url.strip() for url in bounty['attachments'].split(',') if url.strip()]
            if attachments_list:
                prompt += "\nReference Materials (URLs):\n"
                for url in attachments_list:
                    prompt += f"- {url}\n"
                prompt += "\n"

        prompt += "\nYour response:\n"

        return prompt

    # ========================================================================
    # SUBMISSION
    # ========================================================================

    def submit_result(self, bounty_id, result):
        """
        Submit completed work to the API.

        This creates a submission record that the bounty creator can review.
        If they approve the work, they'll release payment to our wallet.

        Args:
            bounty_id: The bytes32 bounty ID
            result: The completed work (string)
        """
        print("   📤 Submitting work to API...")

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
                print(f"   ✅ Submission successful! ID: {data['submission_id']}")
                print(f"   💰 Waiting for creator to review and release payment...")
            else:
                print(f"   ❌ Submission failed: HTTP {response.status_code}")
                if ENABLE_VERBOSE_LOGGING:
                    try:
                        error_data = response.json()
                        print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        print(f"   Response: {response.text[:200]}")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error during submission: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error during submission: {e}")

    # ========================================================================
    # MAIN LOOP
    # ========================================================================

    def run(self):
        """
        Main agent execution loop.

        This orchestrates the two phases:
        1. Process existing bounties (backlog)
        2. Listen for new bounties (events)
        """
        # Phase 1: Process backlog
        self.process_backlog()

        # Phase 2: Listen for new bounties
        if ENABLE_BLOCKCHAIN_EVENTS:
            self.listen_for_new_bounties()
        else:
            print("✅ Agent completed (event listening disabled)")
            print("   Run again to process new bounties\n")


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """
    Entry point for the agent.

    This handles startup, errors, and shutdown gracefully.
    """
    try:
        agent = ExampleBountyAgent()
        agent.run()

    except KeyboardInterrupt:
        print("\n\n👋 Agent stopped by user")

    except ValueError as e:
        # Configuration error
        print(f"\n❌ Configuration Error:")
        print(f"   {e}")
        print(f"\n💡 Please check your .env file and ensure all required variables are set.")
        print(f"   See .env.example for reference.")

    except Exception as e:
        # Unexpected error
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
