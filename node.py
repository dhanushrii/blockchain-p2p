from flask import Flask, jsonify, request, render_template
from uuid import uuid4
from urllib.parse import urlparse
import requests
from block import Blockchain

app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()
peers = set()
pending_tx_pool = set()  # for syncing pending txs (hashes of txs)


# ────────────────────────────── UI ──────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', chain=blockchain.chain, blockchain=blockchain)


# ──────────────────────── Mining endpoint ───────────────────────
@app.route('/mine', methods=['POST'])
def mine():
    raw_data = request.get_json().get("data", "").strip()
    parsed = 0

    for line in raw_data.splitlines():
        line = line.strip()
        if "->" in line and ":" in line:
            try:
                left, amount = line.split(":", 1)
                sender, recipient = left.split("->", 1)
                tx = {'sender': sender.strip(), 'recipient': recipient.strip(), 'amount': amount.strip()}
                tx_hash = str(tx)

                if tx_hash not in pending_tx_pool:
                    if blockchain.new_transaction(**tx):
                        pending_tx_pool.add(tx_hash)
                        parsed += 1
            except ValueError:
                print(f"[WARN] Invalid line: {line}")

    if parsed == 0:
        return jsonify({'message': 'No valid transactions to mine.'}), 400

    proof = blockchain.proof_of_work(blockchain.last_block['proof'])
    prev_hash = blockchain.hash(blockchain.last_block)
    new_block = blockchain.new_block(proof, prev_hash)

    # clear all txs in block from pool
    for tx in new_block['transactions']:
        pending_tx_pool.discard(str(tx))

    # trigger consensus and sync pending txs
    resolve_conflicts()
    sync_pending_transactions()

    return jsonify({
        'message': f'Block mined with {parsed} transaction(s)',
        'index': new_block['index'],
        'transactions': new_block['transactions'],
        'proof': new_block['proof'],
        'previous_hash': new_block['previous_hash']
    }), 200


# ───────────────────── Add single transaction ───────────────────
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json()
    required = ('sender', 'recipient', 'amount')
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing fields'}), 400

    tx_hash = str(data)
    if tx_hash in pending_tx_pool:
        return jsonify({'message': 'Duplicate transaction skipped.'}), 200

    idx = blockchain.new_transaction(data['sender'], data['recipient'], data['amount'])
    if idx is None:
        return jsonify({'error': 'Invalid transaction'}), 400

    pending_tx_pool.add(tx_hash)
    return jsonify({'message': f'Transaction will appear in Block {idx}'}), 201


# ───────────────────────── Chain & peers ────────────────────────
@app.route('/chain', methods=['GET'])
def full_chain():
    return jsonify({'chain': blockchain.chain, 'length': len(blockchain.chain)}), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    nodes = request.get_json().get('nodes')
    if not nodes:
        return jsonify({'error': 'No nodes provided'}), 400

    for node in nodes:
        parsed = urlparse(node)
        peers.add(parsed.netloc or parsed.path)
    return jsonify({'message': 'Nodes added', 'peers': list(peers)}), 201


@app.route('/nodes', methods=['GET'])
def get_nodes():
    return jsonify({'nodes': list(peers)}), 200


# ───────────────────────── Consensus endpoint ───────────────────
@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = resolve_conflicts()
    return jsonify({
        'message': 'Chain replaced' if replaced else 'Chain is authoritative',
        'chain': blockchain.chain
    }), 200


# ───────────────────────── Sync pending txs ─────────────────────
@app.route('/pending', methods=['GET'])
def get_pending():
    return jsonify({'pending': list(pending_tx_pool)}), 200


def sync_pending_transactions():
    """Pull pending transactions from peers and merge them (de-duplicated)."""
    for peer in peers:
        try:
            res = requests.get(f'http://{peer}/pending', timeout=3)
            if res.status_code == 200:
                remote_pool = set(res.json().get('pending', []))
                for tx_hash in remote_pool:
                    if tx_hash not in pending_tx_pool:
                        tx = eval(tx_hash)
                        if blockchain.is_valid_transaction(tx['sender'], tx['recipient'], tx['amount']):
                            blockchain.new_transaction(tx['sender'], tx['recipient'], tx['amount'])
                            pending_tx_pool.add(tx_hash)
        except Exception as e:
            print(f"[ERROR] Could not sync pending txs from {peer}: {e}")


# ───────────────────────── Consensus logic ──────────────────────
def resolve_conflicts() -> bool:
    max_len = len(blockchain.chain)
    longest_chain = None

    for node in peers:
        try:
            resp = requests.get(f'http://{node}/chain', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                length, chain = data['length'], data['chain']
                if length > max_len and blockchain.valid_chain(chain):
                    max_len = length
                    longest_chain = chain
        except Exception as e:
            print(f"[ERROR] Could not reach {node}: {e}")

    if longest_chain:
        blockchain.chain = longest_chain
        return True
    return False


# ──────────────────────────── Run app ───────────────────────────
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int)
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port)
