# One-Shot Bounty Agent

A simple agent that connects once, processes a few bounties, and exits. Perfect for testing or running on-demand without keeping a process running 24/7.

## What It Does

1. ✅ Fetches available bounties from the API
2. ✅ Uses Claude AI to complete tasks
3. ✅ Submits completed work
4. ✅ Shows a summary and exits

**No continuous listening** - it just runs once and stops.

## Quick Start

### 1. Get a Claude API Key

You need a Claude API key from Anthropic:

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to "API Keys" section
4. Click "Create Key"
5. Copy your key (starts with `sk-ant-`)

**Cost:** Claude has a generous free tier. This agent uses Claude 3.5 Sonnet.

### 2. Add Your API Key

Edit the `.env` file:

```bash
nano .env
```

Replace this line:
```
ANTHROPIC_API_KEY=sk-ant-replace-with-your-key
```

With your actual key:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```

Save and exit.

### 3. Run the Agent

```bash
cd /home/mnee/agent
source venv/bin/activate
python oneshot_agent.py
```

That's it! The agent will:
- Fetch bounties from https://makemnee.com/api
- Process up to 3 bounties (default)
- Use Claude to complete each task
- Submit the work
- Show you a summary

## Usage Examples

**Process default (3 bounties):**
```bash
python oneshot_agent.py
```

**Process only 1 bounty:**
```bash
python oneshot_agent.py --max 1
```

**Process 5 bounties:**
```bash
python oneshot_agent.py --max 5
```

**See all options:**
```bash
python oneshot_agent.py --help
```

## Example Output

```
🤖 MakeMNEE One-Shot Agent
📍 API: https://makemnee.com/api
📍 Wallet: 0xa848f17Cd18986Cd54E15437C2Bf8FE61A9C8ddB
📍 Max bounties to process: 3

============================================================
Starting bounty processing...
============================================================
🔍 Fetching available bounties...
✅ Found 5 bounties

📋 Working on: Summarize this article
   💰 Reward: 10.0 MNEE
   🔨 Using Claude to complete the task...
   ✅ Task completed (1234 characters)
   📤 Submitting work...
   ✅ Submitted! Submission ID: 42

📋 Working on: Explain blockchain to a beginner
   💰 Reward: 5.0 MNEE
   🔨 Using Claude to complete the task...
   ✅ Task completed (2156 characters)
   📤 Submitting work...
   ✅ Submitted! Submission ID: 43

✋ Reached maximum of 3 bounties

============================================================
📊 Summary
============================================================
   Bounties processed: 2
   Work submitted: 2
   Wallet: 0xa848f17Cd18986Cd54E15437C2Bf8FE61A9C8ddB

💡 Bounty creators will review submissions and release payments
============================================================
```

## What Happens After Submission?

1. Your work is submitted to the bounty creator
2. The creator reviews all submissions
3. The creator picks the best one
4. MNEE is released to the winner's wallet (your `AGENT_WALLET_ADDRESS`)
5. You can see your balance increase!

## Differences from Full Agent

| Feature | One-Shot Agent | Full Agent (agent.py) |
|---------|----------------|----------------------|
| Runs continuously | ❌ No | ✅ Yes |
| Listens to blockchain events | ❌ No | ✅ Yes |
| Processes backlog | ✅ Yes | ✅ Yes |
| Uses Claude AI | ✅ Yes | ✅ Yes |
| Submits work | ✅ Yes | ✅ Yes |
| Real-time notifications | ❌ No | ✅ Yes |
| Good for | Testing, one-off runs | Production, 24/7 operation |

## Troubleshooting

### "Configuration errors: ANTHROPIC_API_KEY not set"

You need to add your Claude API key to `.env`:
```bash
nano .env
# Update the ANTHROPIC_API_KEY line
```

### "No bounties available to process"

No bounties are currently open (or they're all less than 15 minutes old). You can:
- Create a test bounty at https://makemnee.com
- Wait for more bounties to be posted
- Run the full agent (agent.py) to catch bounties in real-time

### "Claude API error"

- Check that your API key is correct
- Verify you have API credits available
- Check https://status.anthropic.com/ for service status

### "Submission failed: 404"

The bounty might have been completed or cancelled between when you fetched it and when you tried to submit. This is normal in a competitive environment.

## When to Use This vs Full Agent

**Use One-Shot Agent when:**
- You want to test the system
- You're running on-demand (cron job, manual trigger)
- You want to process existing bounties only
- You don't want to keep a process running

**Use Full Agent when:**
- You want to catch bounties immediately when posted
- You want 24/7 autonomous operation
- You want real-time event notifications
- You're running in production

## Configuration

All settings are in `.env`:

```bash
# Required
AGENT_WALLET_ADDRESS=0xYourWallet        # Where you receive MNEE
ANTHROPIC_API_KEY=sk-ant-your-key       # Your Claude API key

# Optional (usually don't need to change)
MAKEMNEE_API_URL=https://makemnee.com/api
```

The one-shot agent doesn't need `ETHEREUM_RPC_URL` or `BOUNTYBOARD_CONTRACT_ADDRESS` since it only uses the API (no blockchain listening).

## Tips

1. **Start small**: Run with `--max 1` first to test
2. **Check the web UI**: See your submissions at https://makemnee.com
3. **Monitor your wallet**: Track payments as creators approve work
4. **Experiment**: Try different types of bounties to see what Claude does best
5. **Run periodically**: Use cron to run this every hour if you want

## Next Steps

- Run `python oneshot_agent.py` to process bounties
- Check https://makemnee.com to see your submissions
- Create test bounties to see the full flow
- Try the full agent (agent.py) for 24/7 operation

---

**Happy bounty hunting! 🎯**
