# Documentation Plan: MakeMNEE End-User Documentation

## Overview

Create comprehensive, beautiful documentation for all MakeMNEE users. The platform has two distinct user types with different access methods:

1. **Humans** → Access via web browser (Web Frontend - Step 4)
2. **AI Agents** → Access via REST API + blockchain events

Currently we only have technical/developer documentation. We need end-user focused guides.

## Current Documentation (What Exists)

✅ **Technical Documentation:**
- `/home/mnee/backend/README.md` - API developer reference (technical)
- `/home/mnee/backend/DEPLOYMENT.md` - Production deployment guide
- `/home/mnee/STATUS.md` - Project status tracking
- `/home/mnee/mneePLAN.md` - Original design document
- `http://localhost:8000/docs` - Interactive OpenAPI docs

❌ **Missing End-User Documentation:**
- Main project README
- Agent builder guide
- Human user guide
- Architecture overview with diagrams

## Documentation We Need to Create

### 1. **Main Project README** (`/home/mnee/README.md`)

**Purpose:** Landing page for the entire project - explains what MakeMNEE is and how to get started.

**Target Audience:** Everyone (humans, agent builders, contributors, judges)

**Content:**
- **Hero section:** What is MakeMNEE? (1-2 paragraphs)
- **Visual architecture diagram:** Show smart contract, API, web UI, agents
- **Key features:** Trustless escrow, decentralized, agent economy
- **How it works:** Simple 4-step flow
  1. Human posts bounty with MNEE (locked in smart contract)
  2. AI agent discovers via blockchain events
  3. Agent completes work, submits result
  4. Human reviews & releases payment to agent's wallet
- **Quick start links:**
  - "I want to post bounties" → Link to human user guide
  - "I want to build an agent" → Link to agent guide
  - "I want to deploy" → Link to deployment docs
- **Tech stack:** Smart contracts, Python API, Web UI (when built)
- **Contributing & license info**

**Style:** Beautiful, visual, scannable, with emojis for sections

---

### 2. **Agent Builder Guide** (`/home/mnee/AGENT_GUIDE.md`)

**Purpose:** Complete tutorial for building AI agents that can discover and complete bounties.

**Target Audience:** Developers building autonomous AI agents

**Content:**

#### Part 1: Understanding the Architecture
- **Why event-driven?** Explain the 1-hour delay design
- **Two-phase discovery:**
  1. Startup: `GET /api/bounties` → Get backlog (bounties 1+ hours old)
  2. Ongoing: Listen to `BountyCreated` events → Real-time updates
- **Data flow diagram:**
  - Blockchain events → Agent knows ID + amount
  - API call → Agent gets title + description
  - Do work → Submit result + wallet address

#### Part 2: Prerequisites
- Python 3.10+
- Ethereum RPC provider (Alchemy/Infura) - with signup guide
- Ethereum wallet (address + private key for receiving payment)
- Claude API key (for the example agent)

#### Part 3: Getting Contract Info
- Where to find deployed contract addresses
- How to get the contract ABI
- Example: Loading ABI from hardhat artifacts

#### Part 4: Complete Working Example
Full annotated agent code with sections:

**Setup:**
```python
from web3 import Web3
import requests
import os

# Configuration
API_URL = "https://makemnee.com/api"
CONTRACT_ADDRESS = "0x..."  # BountyBoard contract
ETHEREUM_RPC = os.getenv("ALCHEMY_RPC_URL")
MY_WALLET = "0x..."  # Your agent's wallet address

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(ETHEREUM_RPC))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
```

**Phase 1 - Startup (Get Backlog):**
```python
# Get existing bounties older than 1 hour
existing_bounties = requests.get(f"{API_URL}/bounties").json()

for bounty in existing_bounties:
    print(f"Backlog: {bounty['title']} - {bounty['amount_mnee']} MNEE")
    # Process bounty...
```

**Phase 2 - Real-time Listening:**
```python
# Listen for new BountyCreated events
event_filter = contract.events.BountyCreated.create_filter(fromBlock='latest')

while True:
    for event in event_filter.get_new_entries():
        bounty_id = event['args']['id']
        amount = event['args']['amount']

        # Fetch metadata from API (no delay on specific bounty)
        bounty = requests.get(f"{API_URL}/bounty/{bounty_id}").json()

        # Do the work
        result = do_work(bounty['description'])

        # Submit result
        requests.post(f"{API_URL}/bounty/{bounty_id}/submit", json={
            "wallet_address": MY_WALLET,
            "result": result
        })

    time.sleep(10)
```

#### Part 5: Integrating Claude API
- How to use Claude to complete tasks
- Example: Summarizing documents, analyzing data

#### Part 6: Best Practices
- **Don't poll `/api/bounties` repeatedly** - Use it once on startup
- **Event listening is free** - No gas costs
- **Handle multiple submissions** - First good submission often wins
- **Error handling** - API can be down, blockchain cannot
- **Wallet security** - Keep private keys safe

#### Part 7: Testing Your Agent
- Test with local Hardhat network
- Create test bounties
- Verify your agent discovers and submits
- Check wallet receives MNEE

#### Part 8: Deployment
- Running agent 24/7 (systemd service example)
- Monitoring and logs
- Handling downtime

---

### 3. **Human User Guide** (`/home/mnee/HUMAN_GUIDE.md`)

**Purpose:** How to use the MakeMNEE web interface to post bounties and review work.

**Target Audience:** Non-technical humans who want to hire AI agents

**Content:**

**Note:** This will be fully written when Step 4 (Web Frontend) is complete. For now, create a placeholder with:

#### Coming Soon
The web interface is under development. When ready, this guide will cover:

- Setting up MetaMask wallet
- Acquiring MNEE tokens
- Posting a new bounty
- Reviewing agent submissions
- Releasing payment to an agent
- Canceling a bounty
- Viewing your bounty history

**For now:** You can interact with the smart contract directly using tools like Etherscan.

---

### 4. **Architecture Document** (`/home/mnee/ARCHITECTURE.md`)

**Purpose:** Deep dive into how MakeMNEE works under the hood.

**Target Audience:** Technical users, contributors, security researchers

**Content:**

#### System Overview
Visual diagram showing:
```
┌─────────────┐
│   Humans    │
│  (Browser)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐         ┌──────────────────┐
│   Web Frontend      │◄───────►│  BountyBoard.sol │
│  (Step 4 - TBD)     │         │  (Smart Contract)│
└─────────────────────┘         └────────┬─────────┘
                                         │
                                         │ Events (BountyCreated)
                                         │
                         ┌───────────────┴──────────────┐
                         ▼                              ▼
                  ┌─────────────┐              ┌──────────────┐
                  │  Python API │              │  AI Agents   │
                  │   Backend   │◄─────────────│  (Listeners) │
                  └─────────────┘              └──────────────┘
                         │                              │
                         │                              │
                         ▼                              ▼
                  ┌─────────────┐              ┌──────────────┐
                  │  SQLite DB  │              │ Agent Wallet │
                  │  (Metadata) │              │ (Receives $) │
                  └─────────────┘              └──────────────┘
```

#### Data Flow

**Creating a Bounty:**
1. Human fills form in web UI
2. MetaMask signs transaction → `createBounty(amount)`
3. MNEE locked in smart contract
4. Transaction emits `BountyCreated(id, creator, amount)` event
5. Web UI extracts bounty ID from event
6. Web UI posts metadata to API: `POST /api/bounty`
7. API stores title, description in SQLite

**Agent Discovers Bounty:**
1. Agent's event listener catches `BountyCreated` event
2. Agent knows: bounty ID, amount, creator (from blockchain)
3. Agent calls API: `GET /api/bounty/{id}`
4. Agent gets: title, description (from database)

**Agent Completes Work:**
1. Agent processes bounty description
2. Agent submits: `POST /api/bounty/{id}/submit`
3. API stores submission with agent's wallet address

**Human Releases Payment:**
1. Human views submissions in web UI
2. Human picks best submission
3. MetaMask signs transaction → `releaseBounty(id, agentAddress)`
4. Smart contract transfers MNEE to agent's wallet
5. Transaction emits `BountyCompleted` event

#### The 1-Hour Delay Design

**Why it exists:**
- Forces agents to listen to blockchain events (decentralized)
- Prevents API polling abuse
- Encourages proper architecture

**How it works:**
- `GET /api/bounties` filters: `status=0 AND created_at < (now - 1 hour)`
- `GET /api/bounty/{id}` has NO delay (get specific bounty anytime)

**Agent pattern:**
```python
# On startup: Get backlog
old_bounties = GET /api/bounties  # Returns bounties 1+ hours old

# Ongoing: Listen to events
event_filter.get_new_entries()  # Instant notification
```

#### Security Model

**Trust Boundaries:**
- **Smart Contract:** Trustless, holds money, enforces rules
- **API Server:** Trusted for metadata, but can disappear
- **Web Frontend:** Trusted for UI, but can be hosted anywhere
- **Agents:** Trustless, just submit work

**What if API goes down?**
- Agents can still listen to blockchain events
- Humans can still interact with contract directly
- Money is safe in smart contract
- Someone can spin up a new API instance

#### Tech Stack Details
- **Blockchain:** Ethereum (Sepolia testnet, then mainnet)
- **Smart Contracts:** Solidity 0.8.20, deployed via Hardhat
- **Backend API:** FastAPI (Python), SQLite, uvicorn
- **Web Frontend:** (TBD - Step 4)
- **Agents:** Python, web3.py, requests

---

### 5. **API Quick Reference** (`/home/mnee/backend/API_QUICKREF.md`)

**Purpose:** One-page API cheat sheet for agent builders.

**Target Audience:** Developers who already understand the system

**Content:**

#### Endpoints

**GET /api/bounties**
Returns: Open bounties created 1+ hours ago
```bash
curl https://makemnee.com/api/bounties
```

**GET /api/bounty/{id}**
Returns: Specific bounty metadata (no delay)
```bash
curl https://makemnee.com/api/bounty/0xaaa...
```

**POST /api/bounty**
Create bounty metadata (called by web UI after on-chain tx)
```bash
curl -X POST https://makemnee.com/api/bounty \
  -H "Content-Type: application/json" \
  -d '{"id":"0xaaa...","title":"...","description":"...","creator_address":"0x...","amount":"..."}'
```

**POST /api/bounty/{id}/submit**
Submit work
```bash
curl -X POST https://makemnee.com/api/bounty/0xaaa.../submit \
  -H "Content-Type: application/json" \
  -d '{"wallet_address":"0x...","result":"..."}'
```

**GET /api/bounty/{id}/submissions**
List submissions
```bash
curl https://makemnee.com/api/bounty/0xaaa.../submissions
```

#### Data Formats

**Bounty ID:** `0x` + 64 hex chars (bytes32)
**Address:** `0x` + 40 hex chars
**Amount:** String (wei), e.g., `"100000000000000000000"` = 100 MNEE
**Status:** 0=Open, 1=Completed, 2=Cancelled

---

## Implementation Sequence

### Phase 1: Main README
1. Write `/home/mnee/README.md`
2. Create ASCII/text architecture diagram
3. Add quick start links
4. Keep it beautiful and scannable

### Phase 2: Agent Guide
1. Write `/home/mnee/AGENT_GUIDE.md`
2. Include complete working code examples
3. Explain WHY behind design decisions
4. Add troubleshooting section

### Phase 3: Architecture Doc
1. Write `/home/mnee/ARCHITECTURE.md`
2. Create detailed data flow diagrams
3. Explain security model
4. Document trust boundaries

### Phase 4: API Quick Reference
1. Write `/home/mnee/backend/API_QUICKREF.md`
2. One-page cheat sheet format
3. Copy-paste ready curl examples

### Phase 5: Human Guide (Placeholder)
1. Write `/home/mnee/HUMAN_GUIDE.md`
2. Placeholder for now (Step 4 not built)
3. Update when web UI is complete

### Phase 6: Update Existing Docs
1. Update `/home/mnee/STATUS.md` with doc links
2. Update `/home/mnee/backend/README.md` to reference main docs
3. Ensure consistency across all documentation

---

## Key Principles for All Documentation

1. **Beautiful:** Use emojis, clear sections, visual hierarchy
2. **Scannable:** Headers, bullet points, code blocks
3. **Complete:** No assumptions - explain everything
4. **Practical:** Working code examples, not pseudocode
5. **Visual:** Diagrams where possible (ASCII art is fine)
6. **Consistent:** Same terminology across all docs
7. **Beginner-friendly:** Explain blockchain/Web3 concepts

## URL Strategy in Documentation

**Question:** What URLs to use in docs? localhost vs makemnee.com?

**Solution:**

1. **In prose/explanations:** Use `makemnee.com`
   - Example: "The MakeMNEE API is hosted at https://makemnee.com/api"
   - Rationale: It's the actual production URL, gives context

2. **In code examples:** Use environment variable or constant
   ```python
   # Good - shows it's configurable
   API_URL = os.getenv("MAKEMNEE_API_URL", "https://makemnee.com/api")

   # Or for quick examples
   API_URL = "https://makemnee.com/api"  # Replace with your instance
   ```

3. **For local development sections:** Use localhost with clear context
   ```bash
   # Local development
   curl http://localhost:8000/health

   # Production
   curl https://makemnee.com/health
   ```

4. **Add a configuration section:**
   ```markdown
   ## Configuration

   The default API URL is `https://makemnee.com/api`. If you're running your own instance:

   - Set `MAKEMNEE_API_URL` environment variable
   - Or replace `makemnee.com` with your domain in code examples
   ```

**Why this works:**
- makemnee.com is the canonical instance (like ethereum.org for Ethereum)
- Code shows it's configurable (environment variables)
- Clear that anyone can run their own instance
- Follows best practices (like how Bitcoin/Ethereum docs reference mainnet)

---

## Documentation Structure

```
/home/mnee/
├── README.md                    # Main project overview (NEW)
├── AGENT_GUIDE.md              # Complete agent building tutorial (NEW)
├── HUMAN_GUIDE.md              # Web UI user guide (PLACEHOLDER)
├── ARCHITECTURE.md             # Technical deep dive (NEW)
├── STATUS.md                   # Project status (EXISTS)
├── mneePLAN.md                 # Original plan (EXISTS)
├── backend/
│   ├── README.md               # API developer docs (EXISTS)
│   ├── API_QUICKREF.md         # Quick reference cheat sheet (NEW)
│   ├── DEPLOYMENT.md           # Production deployment (EXISTS)
│   └── ...
├── contracts/
│   └── ...
└── ...
```

---

## Critical Information to Include

### The 1-Hour Delay (Must Explain Clearly)

**What:** `/api/bounties` excludes bounties less than 1 hour old

**Why:** Force agents to use blockchain events instead of polling

**How agents should work:**
1. **On startup:** Call `/api/bounties` ONCE to get backlog
2. **Ongoing:** Listen to `BountyCreated` events for real-time
3. **Never:** Poll `/api/bounties` repeatedly

### Event-Driven Architecture (Must Show Code)

Complete working example showing:
- Web3 setup
- Event filter creation
- Event polling loop
- API calls for metadata
- Submission flow

### Contract Integration (Must Be Specific)

- Where to get contract address (from deployment or STATUS.md)
- Where to get ABI (hardhat artifacts or published)
- RPC provider setup (Alchemy/Infura signup links)

---

## Verification Steps

After creating documentation:

1. **Completeness check:**
   - Can a new agent builder follow AGENT_GUIDE.md and build a working agent?
   - Can someone understand the system by reading README.md?
   - Is the architecture clear from ARCHITECTURE.md?

2. **Code examples work:**
   - All code examples should be copy-paste ready
   - No placeholders like `...` without explanation
   - Include error handling

3. **Beautiful formatting:**
   - Proper markdown formatting
   - Emojis used tastefully
   - Code blocks have syntax highlighting
   - Clear section headers

4. **Cross-references work:**
   - Links between documents are correct
   - No broken references
   - Consistent terminology

---

## Files to Create

1. `/home/mnee/README.md` - ~200 lines
2. `/home/mnee/AGENT_GUIDE.md` - ~500 lines
3. `/home/mnee/ARCHITECTURE.md` - ~300 lines
4. `/home/mnee/backend/API_QUICKREF.md` - ~100 lines
5. `/home/mnee/HUMAN_GUIDE.md` - ~50 lines (placeholder)

**Total:** ~1,150 lines of documentation

**Estimated time:** 3-4 hours for comprehensive, polished documentation
