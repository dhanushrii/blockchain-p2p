# BLOCK CHAIN PEER TO PEER VISUVALIZER

A visual, peer-to-peer blockchain simulation built using Python and Flask, complete with mining, consensus, and an interactive dashboard.

# What is Blockchain?
  A blockchain is a distributed, immutable digital ledger made of blocks. Each block contains:
- A list of validated transactions
- A proof-of-work (a nonce that satisfies difficulty)
- The hash of the previous block
This ensures transparency, security, and tamper resistance.

# What is Peer-to-Peer (P2P)?
A peer-to-peer (P2P) network is a decentralized system where each participant (node) acts as both a client and a server.
In this project:
- Each Flask instance is a peer (node)
- Nodes sync blocks
- Nodes auto-resolve conflicts using the longest-chain rule

# Tech Stack Used:
- Backend	- Python 3.8+, Flask
- Frontend - HTML5, CSS3 (no frameworks)
- Networking	- HTTP APIs via Flask
- Hashing	- SHA-256 (hashlib)

# Features
1. Basic Blockchain Logic
 Creates blocks with:
  - Index
  - Timestamp
  - Transactions
  - Proof Of Work(nonce)
  - Previous block hash

2. Proof of Work
  - Valid hash must start with 0000
  - Increases mining effort, prevents spam

3. Validated Transactions
  - Human-readable format: alice -> bob : 10
  - Validates: Non-empty sender/recipient, Amount is a positive number

4. Peer Registration
  - Nodes can register new peers dynamically
  - Auto updates across all nodes

5. Consensus Algorithm
  - Ensures all peers follow the longest valid chain
  - Runs automatically after mining or peer sync

6. Visual Dashboard
  - Blocks rendered as styled cards
  - Only latest block is editable for input
  - Shows hashes, nonces, transaction data
  - Clickable "Mine Block" button

# How It Works
1. Start Multiple Nodes: Each instance runs on a different port (e.g., 5000, 5001)

2. Add Transactions: Add human-readable transactions on the latest block

3. Mine Block: 
- Validates transactions
- Finds a nonce via proof-of-work
- Creates a new block
- Triggers auto-consensus across peers

4. Consensus:
- On every sync, checks if any peer has a longer valid chain
- If found, replaces local chain

5. Frontend:
- Built with pure HTML+CSS
- Shows data live and cleanly
- Uses Fetch API to interact with Flask backend

# Getting Started
1. Prerequisites
- Python 3.8+
- Flask + Requests libraries
- Install Flask and Requests: pip install flask requests

3. Run Node Locally: # Start Node on corresponding Port
   python node.py -p 5000
   python node.py -p 5001

# Access Frontend
- Visit: http://127.0.0.1:5000/ in browser
- Add transactions (e.g., alice -> bob : 10)
- Click Mine Block
- Chain auto-updates on all peers
