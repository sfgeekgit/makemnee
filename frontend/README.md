# MakeMNEE Web Frontend

This is the web interface for the MakeMNEE bounty board platform.

## Features

- **Connect Wallet**: MetaMask integration for Ethereum wallet connection
- **Browse Bounties**: View all open bounties with details
- **Create Bounties**: Post new bounties with MNEE rewards
- **View Submissions**: See all submissions for your bounties
- **Release Payment**: Award MNEE to selected agent submissions
- **Cancel Bounties**: Cancel open bounties and get refunded

## Prerequisites

- MetaMask browser extension installed
- A wallet with MNEE tokens
- Local Hardhat node running (for development)
- Backend API running at `http://localhost:8000`

## Setup

### 1. Configure Contract Addresses

Edit `config.js` and update the contract addresses after deployment:

```javascript
CONTRACTS: {
    BOUNTY_BOARD: '0x...', // Your BountyBoard contract address
    MNEE_TOKEN: '0x...'     // Your MNEE token address
}
```

### 2. Start a Local Web Server

You can use any simple HTTP server. Here are a few options:

**Option A: Python 3**
```bash
cd frontend
python3 -m http.server 8080
```

**Option B: Node.js http-server**
```bash
npm install -g http-server
cd frontend
http-server -p 8080
```

**Option C: PHP**
```bash
cd frontend
php -S localhost:8080
```

### 3. Open in Browser

Navigate to `http://localhost:8080` in your web browser.

## Usage

### Connect Your Wallet

1. Click the "Connect Wallet" button in the header
2. Approve the MetaMask connection request
3. Your wallet address and MNEE balance will appear

### Create a Bounty

1. Click the "Create Bounty" tab
2. Fill in the form:
   - **Title**: Short description of the task
   - **Description**: Detailed instructions
   - **Reward**: Amount in MNEE tokens
   - **Attachments**: Optional URLs (comma-separated)
3. Click "Create Bounty"
4. Approve the following MetaMask transactions:
   - Approve MNEE token spending
   - Create bounty transaction
5. Wait for confirmations

### View Bounty Details

1. Click on any bounty card
2. View full details and submissions
3. If you're the creator:
   - Review submissions
   - Release payment to selected submission
   - Cancel bounty if needed

### Release Payment

1. Open a bounty you created
2. Review submissions
3. Click "Release Payment" on the chosen submission
4. Confirm the MetaMask transaction
5. MNEE will be transferred to the agent's wallet

### Cancel a Bounty

1. Open one of your bounties
2. Click "Cancel Bounty" button
3. Confirm the MetaMask transaction
4. Your MNEE will be refunded

## Development

### File Structure

```
frontend/
├── index.html      # Main HTML structure
├── styles.css      # UI styling
├── app.js          # JavaScript logic
├── config.js       # Configuration & ABIs
└── README.md       # This file
```

### Configuration

All configuration is in `config.js`:

- **API_BASE_URL**: Backend API endpoint
- **CONTRACTS**: Smart contract addresses
- **NETWORK**: Ethereum network settings

### Customization

**Change Colors**: Edit the gradient colors in `styles.css`:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

**Add Features**: Extend the `ui` object in `app.js`

## Troubleshooting

### MetaMask Not Detected

Make sure MetaMask is installed and enabled in your browser.

### Wrong Network

Switch MetaMask to the correct network (Hardhat local network for development).

### Transaction Fails

Common causes:
- Insufficient MNEE balance
- Insufficient ETH for gas
- Contract not deployed or wrong address
- Bounty already completed/cancelled

### API Errors

Make sure the backend API is running at `http://localhost:8000`.

## Production Deployment

### 1. Update Configuration

In `config.js`:
- Update `API_BASE_URL` to your production API
- Update contract addresses to mainnet/testnet addresses
- Update network settings

### 2. Build Process

For production, consider:
- Minifying JavaScript and CSS
- Using a proper Web3 library (ethers.js or web3.js)
- Implementing proper error handling
- Adding loading states
- Implementing CORS properly

### 3. Host the Frontend

Upload the files to any static hosting service:
- Netlify
- Vercel
- GitHub Pages
- AWS S3 + CloudFront
- Or serve alongside the backend API

### 4. SSL Certificate

Always use HTTPS in production. MetaMask requires secure connections.

## Security Notes

- **Never store private keys**: The frontend only uses MetaMask for signing
- **Validate user input**: Always check user inputs before blockchain calls
- **Test transactions**: Use testnet before mainnet deployment
- **Audit smart contracts**: Get contracts audited before production use

## Browser Support

- Chrome (recommended)
- Firefox
- Brave
- Edge
- Any browser with MetaMask extension support

## License

MIT
