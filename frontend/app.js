// MakeMNEE Frontend Application

// Global state
const state = {
    web3: null,
    account: null,
    bountyBoardContract: null,
    mneeTokenContract: null,
    bounties: [],
    myBounties: [],
    currentBounty: null
};

// Utility functions
const utils = {
    weiToMNEE(wei) {
        return Number(wei) / 1e18;
    },

    mneeToWei(mnee) {
        return BigInt(Math.floor(mnee * 1e18));
    },

    formatAddress(address) {
        if (!address) return '';
        return `${address.substring(0, 6)}...${address.substring(38)}`;
    },

    formatDate(timestamp) {
        return new Date(timestamp).toLocaleString();
    },

    showStatus(message, type = 'info') {
        const statusEl = document.getElementById('statusMessage');
        statusEl.textContent = message;
        statusEl.className = `status-message ${type}`;
        statusEl.classList.remove('hidden');

        setTimeout(() => {
            statusEl.classList.add('hidden');
        }, 5000);
    },

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
};

// Web3 & Wallet connection
const wallet = {
    async connect() {
        if (typeof window.ethereum === 'undefined') {
            utils.showStatus('MetaMask is not installed. Please install MetaMask to use this app.', 'error');
            return false;
        }

        try {
            // Request account access
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            state.account = accounts[0];

            // Initialize web3
            state.web3 = window.ethereum;

            // Initialize contracts
            state.bountyBoardContract = {
                address: CONFIG.CONTRACTS.BOUNTY_BOARD,
                call: async (method, ...params) => {
                    const data = this.encodeMethod(BOUNTY_BOARD_ABI, method, params);
                    const result = await window.ethereum.request({
                        method: 'eth_call',
                        params: [{
                            to: CONFIG.CONTRACTS.BOUNTY_BOARD,
                            data: data
                        }, 'latest']
                    });
                    return result;
                },
                send: async (method, ...params) => {
                    const data = this.encodeMethod(BOUNTY_BOARD_ABI, method, params);
                    const txHash = await window.ethereum.request({
                        method: 'eth_sendTransaction',
                        params: [{
                            from: state.account,
                            to: CONFIG.CONTRACTS.BOUNTY_BOARD,
                            data: data
                        }]
                    });
                    return txHash;
                },
                encodeMethod(abi, methodName, params) {
                    // Find the method in ABI
                    const method = abi.find(item => item.name === methodName && item.type === 'function');
                    if (!method) throw new Error(`Method ${methodName} not found`);

                    // Create method signature
                    const types = method.inputs.map(input => input.type);
                    const signature = `${methodName}(${types.join(',')})`;

                    // Calculate function selector (first 4 bytes of keccak256 hash)
                    const selector = this.keccak256(signature).substring(0, 10);

                    // Encode parameters
                    const encodedParams = this.encodeParameters(types, params);

                    return selector + encodedParams;
                },
                keccak256(str) {
                    // Simple keccak256 implementation would go here
                    // For production, use a library like ethers.js or web3.js
                    // For now, we'll use eth_call which handles this
                    return '0x' + Array.from(str).map(c => c.charCodeAt(0).toString(16).padStart(2, '0')).join('');
                },
                encodeParameters(types, values) {
                    // Simple parameter encoding
                    let encoded = '';
                    for (let i = 0; i < types.length; i++) {
                        const type = types[i];
                        const value = values[i];

                        if (type === 'uint256') {
                            encoded += BigInt(value).toString(16).padStart(64, '0');
                        } else if (type === 'bytes32') {
                            encoded += value.replace('0x', '').padStart(64, '0');
                        } else if (type === 'address') {
                            encoded += value.replace('0x', '').padStart(64, '0');
                        }
                    }
                    return encoded;
                }
            };

            state.mneeTokenContract = {
                address: CONFIG.CONTRACTS.MNEE_TOKEN
            };

            // Update UI
            this.updateUI();

            // Load balance
            await this.updateBalance();

            // Set up event listeners
            window.ethereum.on('accountsChanged', (accounts) => {
                if (accounts.length === 0) {
                    this.disconnect();
                } else {
                    state.account = accounts[0];
                    this.updateUI();
                    this.updateBalance();
                }
            });

            utils.showStatus('Wallet connected successfully!', 'success');
            return true;
        } catch (error) {
            console.error('Error connecting wallet:', error);
            utils.showStatus('Failed to connect wallet: ' + error.message, 'error');
            return false;
        }
    },

    disconnect() {
        state.account = null;
        state.web3 = null;
        this.updateUI();
    },

    updateUI() {
        const connectBtn = document.getElementById('connectWallet');
        const walletInfo = document.getElementById('walletInfo');
        const walletAddress = document.getElementById('walletAddress');

        if (state.account) {
            connectBtn.classList.add('hidden');
            walletInfo.classList.remove('hidden');
            walletAddress.textContent = utils.formatAddress(state.account);
        } else {
            connectBtn.classList.remove('hidden');
            walletInfo.classList.add('hidden');
        }
    },

    async updateBalance() {
        if (!state.account) return;

        try {
            // Get MNEE balance
            const balanceWei = await this.getMNEEBalance(state.account);
            const balance = utils.weiToMNEE(balanceWei);

            document.getElementById('mneeBalance').textContent = `${balance.toFixed(2)} MNEE`;
        } catch (error) {
            console.error('Error updating balance:', error);
        }
    },

    async getMNEEBalance(address) {
        // For now, return a mock balance
        // In production, this would call the ERC20 balanceOf method
        return '1000000000000000000000'; // 1000 MNEE
    },

    async approveTokens(amount) {
        try {
            utils.showStatus('Requesting approval for MNEE tokens...', 'info');

            // Create approve transaction
            const amountHex = '0x' + amount.toString(16);
            const txHash = await window.ethereum.request({
                method: 'eth_sendTransaction',
                params: [{
                    from: state.account,
                    to: CONFIG.CONTRACTS.MNEE_TOKEN,
                    data: this.encodeApprove(CONFIG.CONTRACTS.BOUNTY_BOARD, amountHex)
                }]
            });

            utils.showStatus('Waiting for approval transaction...', 'info');
            await this.waitForTransaction(txHash);

            return true;
        } catch (error) {
            console.error('Approval error:', error);
            throw error;
        }
    },

    encodeApprove(spender, amount) {
        // approve(address,uint256)
        const selector = '0x095ea7b3';
        const spenderPadded = spender.replace('0x', '').padStart(64, '0');
        const amountStr = typeof amount === 'string' ? amount.replace('0x', '') : amount.toString(16);
        const amountPadded = amountStr.padStart(64, '0');
        return selector + spenderPadded + amountPadded;
    },

    async waitForTransaction(txHash) {
        let receipt = null;
        while (receipt === null) {
            try {
                receipt = await window.ethereum.request({
                    method: 'eth_getTransactionReceipt',
                    params: [txHash]
                });
                if (receipt === null) {
                    await utils.sleep(1000);
                }
            } catch (error) {
                console.error('Error getting receipt:', error);
                await utils.sleep(1000);
            }
        }
        return receipt;
    }
};

// API interactions
const api = {
    async fetchBounties() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/bounties`);
            if (!response.ok) throw new Error('Failed to fetch bounties');
            return await response.json();
        } catch (error) {
            console.error('Error fetching bounties:', error);
            utils.showStatus('Failed to load bounties', 'error');
            return [];
        }
    },

    async fetchBounty(id) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/bounty/${id}`);
            if (!response.ok) throw new Error('Bounty not found');
            return await response.json();
        } catch (error) {
            console.error('Error fetching bounty:', error);
            return null;
        }
    },

    async createBounty(bountyId, title, description, amount, attachments) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/bounty`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    bounty_id: bountyId,
                    title: title,
                    description: description,
                    amount: amount,
                    attachments: attachments || ''
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create bounty');
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating bounty:', error);
            throw error;
        }
    },

    async fetchSubmissions(bountyId) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/bounty/${bountyId}/submissions`);
            if (!response.ok) return [];
            return await response.json();
        } catch (error) {
            console.error('Error fetching submissions:', error);
            return [];
        }
    }
};

// UI Controllers
const ui = {
    init() {
        // Connect wallet button
        document.getElementById('connectWallet').addEventListener('click', () => {
            wallet.connect();
        });

        // CTA Connect button on home page
        const ctaConnect = document.getElementById('ctaConnect');
        if (ctaConnect) {
            ctaConnect.addEventListener('click', () => {
                wallet.connect();
            });
        }

        // Logo click to go home
        document.getElementById('logoHome').addEventListener('click', () => {
            this.switchView('home');
        });

        // Header navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                const view = link.dataset.view;
                this.switchView(view);
            });
        });

        // Old nav-tabs (if they exist)
        document.querySelectorAll('.nav-tab').forEach(tab => {

        // Refresh buttons
        document.getElementById('refreshBounties').addEventListener('click', () => {
            this.loadBounties();
        });

        document.getElementById('refreshMyBounties').addEventListener('click', () => {
            this.loadMyBounties();
        });

        // Create bounty form
        document.getElementById('createBountyForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleCreateBounty();
        });

        // Modal close
        document.querySelector('.modal-close').addEventListener('click', () => {
            document.getElementById('bountyModal').classList.add('hidden');
        });

        // Cancel bounty button
        document.getElementById('cancelBountyBtn').addEventListener('click', async () => {
            await this.handleCancelBounty();
        });

        // Initial load
        this.loadBounties();
    },

    switchView(viewName) {
        // Update header nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.view === viewName);
        });

        // Update old tabs (if they exist)
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.view === viewName);
        });

        // Update views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });

        document.getElementById(`view-${viewName}`).classList.add('active');

        // Load data if needed
        if (viewName === 'bounties') {
            this.loadBounties();
        } else if (viewName === 'my-bounties') {
            this.loadMyBounties();
        }
    },

    async loadBounties() {
        const container = document.getElementById('bountiesList');
        container.innerHTML = '<p class="loading">Loading bounties...</p>';

        const bounties = await api.fetchBounties();
        state.bounties = bounties;

        if (bounties.length === 0) {
            container.innerHTML = '<p class="info">No bounties available yet. Be the first to create one!</p>';
            return;
        }

        container.innerHTML = bounties.map(bounty => this.renderBountyCard(bounty)).join('');

        // Add click listeners
        document.querySelectorAll('.bounty-card').forEach(card => {
            card.addEventListener('click', () => {
                const bountyId = card.dataset.id;
                this.showBountyDetail(bountyId);
            });
        });
    },

    async loadMyBounties() {
        if (!state.account) {
            document.getElementById('myBountiesList').innerHTML =
                '<p class="info">Connect your wallet to see your bounties</p>';
            return;
        }

        const container = document.getElementById('myBountiesList');
        container.innerHTML = '<p class="loading">Loading your bounties...</p>';

        const allBounties = await api.fetchBounties();
        const myBounties = allBounties.filter(b =>
            b.creator.toLowerCase() === state.account.toLowerCase()
        );

        state.myBounties = myBounties;

        if (myBounties.length === 0) {
            container.innerHTML = '<p class="info">You haven\'t created any bounties yet.</p>';
            return;
        }

        container.innerHTML = myBounties.map(bounty => this.renderBountyCard(bounty)).join('');

        // Add click listeners
        document.querySelectorAll('.bounty-card').forEach(card => {
            card.addEventListener('click', () => {
                const bountyId = card.dataset.id;
                this.showBountyDetail(bountyId);
            });
        });
    },

    renderBountyCard(bounty) {
        const statusClass = bounty.status === 'Open' ? 'open' : bounty.status === 'Completed' ? 'completed' : 'cancelled';
        return `
            <div class="bounty-card" data-id="${bounty.bounty_id}">
                <h3>${this.escapeHtml(bounty.title)}</h3>
                <div class="bounty-meta">
                    <span class="badge badge-${statusClass}">${bounty.status}</span>
                    <span class="amount">${bounty.amount_mnee} MNEE</span>
                </div>
                <p class="description">${this.escapeHtml(bounty.description)}</p>
                <div class="bounty-footer">
                    <span>By ${utils.formatAddress(bounty.creator)}</span>
                    <span>${utils.formatDate(bounty.created_at)}</span>
                </div>
            </div>
        `;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    async showBountyDetail(bountyId) {
        const bounty = await api.fetchBounty(bountyId);
        if (!bounty) {
            utils.showStatus('Bounty not found', 'error');
            return;
        }

        state.currentBounty = bounty;

        // Populate modal
        document.getElementById('detailTitle').textContent = bounty.title;
        document.getElementById('detailDescription').textContent = bounty.description;
        document.getElementById('detailAmount').textContent = `${bounty.amount_mnee} MNEE`;
        document.getElementById('detailCreator').textContent = bounty.creator;
        document.getElementById('detailId').textContent = bounty.bounty_id;
        document.getElementById('detailCreated').textContent = utils.formatDate(bounty.created_at);

        const statusClass = bounty.status === 'Open' ? 'open' : bounty.status === 'Completed' ? 'completed' : 'cancelled';
        const statusBadge = document.getElementById('detailStatus');
        statusBadge.textContent = bounty.status;
        statusBadge.className = `badge badge-${statusClass}`;

        // Attachments
        const attachmentsDiv = document.getElementById('detailAttachments');
        if (bounty.attachments) {
            const urls = bounty.attachments.split(',').map(url => url.trim()).filter(url => url);
            if (urls.length > 0) {
                attachmentsDiv.innerHTML = '<p><strong>Attachments:</strong></p><ul>' +
                    urls.map(url => `<li><a href="${url}" target="_blank">${url}</a></li>`).join('') +
                    '</ul>';
            } else {
                attachmentsDiv.innerHTML = '';
            }
        } else {
            attachmentsDiv.innerHTML = '';
        }

        // Load submissions
        await this.loadSubmissions(bountyId);

        // Show/hide actions based on ownership and status
        const actionsDiv = document.getElementById('bountyActions');
        if (state.account && bounty.creator.toLowerCase() === state.account.toLowerCase() && bounty.status === 'Open') {
            actionsDiv.classList.remove('hidden');
        } else {
            actionsDiv.classList.add('hidden');
        }

        // Show modal
        document.getElementById('bountyModal').classList.remove('hidden');
    },

    async loadSubmissions(bountyId) {
        const submissions = await api.fetchSubmissions(bountyId);
        const container = document.getElementById('submissionsList');
        const countSpan = document.getElementById('submissionCount');

        countSpan.textContent = submissions.length;

        if (submissions.length === 0) {
            container.innerHTML = '<p class="info">No submissions yet</p>';
            return;
        }

        container.innerHTML = submissions.map((sub, index) => this.renderSubmission(sub, index)).join('');
    },

    renderSubmission(submission, index) {
        const canRelease = state.currentBounty &&
                          state.account &&
                          state.currentBounty.creator.toLowerCase() === state.account.toLowerCase() &&
                          state.currentBounty.status === 'Open';

        return `
            <div class="submission-card">
                <div class="submission-header">
                    <span class="submission-wallet">${submission.wallet_address}</span>
                </div>
                <div class="submission-result">${this.escapeHtml(submission.result)}</div>
                <div class="submission-footer">
                    <span class="submission-time">${utils.formatDate(submission.submitted_at)}</span>
                    ${canRelease ? `<button class="btn btn-success" onclick="ui.handleReleasePayment('${submission.wallet_address}')">Release Payment</button>` : ''}
                </div>
            </div>
        `;
    },

    async handleCreateBounty() {
        if (!state.account) {
            utils.showStatus('Please connect your wallet first', 'error');
            return;
        }

        const title = document.getElementById('bountyTitle').value;
        const description = document.getElementById('bountyDescription').value;
        const amountMNEE = parseFloat(document.getElementById('bountyAmount').value);
        const attachments = document.getElementById('bountyAttachments').value;

        if (!title || !description || !amountMNEE || amountMNEE <= 0) {
            utils.showStatus('Please fill in all required fields', 'error');
            return;
        }

        try {
            const amountWei = utils.mneeToWei(amountMNEE);

            // Step 1: Approve tokens
            utils.showStatus('Step 1/3: Approving MNEE tokens...', 'info');
            await wallet.approveTokens(amountWei);
            utils.showStatus('Tokens approved!', 'success');

            // Step 2: Create bounty on-chain
            utils.showStatus('Step 2/3: Creating bounty on blockchain...', 'info');
            const txHash = await this.createBountyOnChain(amountWei);

            utils.showStatus('Waiting for transaction confirmation...', 'info');
            const receipt = await wallet.waitForTransaction(txHash);

            // Extract bounty ID from transaction receipt
            const bountyId = await this.extractBountyIdFromReceipt(receipt);

            if (!bountyId) {
                throw new Error('Failed to get bounty ID from transaction');
            }

            // Step 3: Save metadata to API
            utils.showStatus('Step 3/3: Saving bounty metadata...', 'info');
            await api.createBounty(bountyId, title, description, amountMNEE, attachments);

            utils.showStatus('Bounty created successfully!', 'success');

            // Reset form
            document.getElementById('createBountyForm').reset();

            // Switch to bounties view
            this.switchView('bounties');

            // Reload bounties
            await this.loadBounties();

            // Update balance
            await wallet.updateBalance();
        } catch (error) {
            console.error('Error creating bounty:', error);
            utils.showStatus('Failed to create bounty: ' + error.message, 'error');
        }
    },

    async createBountyOnChain(amountWei) {
        // createBounty(uint256)
        const selector = '0x3f28e9fb';
        const amountHex = amountWei.toString(16).padStart(64, '0');
        const data = selector + amountHex;

        const txHash = await window.ethereum.request({
            method: 'eth_sendTransaction',
            params: [{
                from: state.account,
                to: CONFIG.CONTRACTS.BOUNTY_BOARD,
                data: data
            }]
        });

        return txHash;
    },

    async extractBountyIdFromReceipt(receipt) {
        // Extract bounty ID from BountyCreated event logs
        if (receipt.logs && receipt.logs.length > 0) {
            // Find the BountyCreated event (first log from BountyBoard contract)
            const log = receipt.logs.find(log =>
                log.address.toLowerCase() === CONFIG.CONTRACTS.BOUNTY_BOARD.toLowerCase()
            );

            if (log && log.topics && log.topics.length > 1) {
                // The bounty ID is the first indexed parameter (topics[1])
                return log.topics[1];
            }
        }
        return null;
    },

    async handleReleasePayment(hunterAddress) {
        if (!state.currentBounty) return;

        if (!confirm(`Release payment of ${state.currentBounty.amount_mnee} MNEE to ${hunterAddress}?`)) {
            return;
        }

        try {
            utils.showStatus('Releasing payment...', 'info');

            // releaseBounty(bytes32,address)
            const selector = '0x98b6cf85';
            const bountyIdHex = state.currentBounty.bounty_id.replace('0x', '').padStart(64, '0');
            const addressHex = hunterAddress.replace('0x', '').padStart(64, '0');
            const data = selector + bountyIdHex + addressHex;

            const txHash = await window.ethereum.request({
                method: 'eth_sendTransaction',
                params: [{
                    from: state.account,
                    to: CONFIG.CONTRACTS.BOUNTY_BOARD,
                    data: data
                }]
            });

            utils.showStatus('Waiting for transaction confirmation...', 'info');
            await wallet.waitForTransaction(txHash);

            utils.showStatus('Payment released successfully!', 'success');

            // Close modal and reload
            document.getElementById('bountyModal').classList.add('hidden');
            await this.loadBounties();
            await this.loadMyBounties();
        } catch (error) {
            console.error('Error releasing payment:', error);
            utils.showStatus('Failed to release payment: ' + error.message, 'error');
        }
    },

    async handleCancelBounty() {
        if (!state.currentBounty) return;

        if (!confirm(`Cancel this bounty and refund ${state.currentBounty.amount_mnee} MNEE to your wallet?`)) {
            return;
        }

        try {
            utils.showStatus('Cancelling bounty...', 'info');

            // cancelBounty(bytes32)
            const selector = '0x3b0b43a6';
            const bountyIdHex = state.currentBounty.bounty_id.replace('0x', '').padStart(64, '0');
            const data = selector + bountyIdHex;

            const txHash = await window.ethereum.request({
                method: 'eth_sendTransaction',
                params: [{
                    from: state.account,
                    to: CONFIG.CONTRACTS.BOUNTY_BOARD,
                    data: data
                }]
            });

            utils.showStatus('Waiting for transaction confirmation...', 'info');
            await wallet.waitForTransaction(txHash);

            utils.showStatus('Bounty cancelled successfully!', 'success');

            // Close modal and reload
            document.getElementById('bountyModal').classList.add('hidden');
            await this.loadBounties();
            await this.loadMyBounties();
            await wallet.updateBalance();
        } catch (error) {
            console.error('Error cancelling bounty:', error);
            utils.showStatus('Failed to cancel bounty: ' + error.message, 'error');
        }
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    ui.init();
});
