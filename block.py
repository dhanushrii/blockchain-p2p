import hashlib
import json
from time import time
from typing import List, Dict, Optional


class Blockchain:
    """
    • Transaction validation (positive numeric amount)
    • Simple PoW (leading 0000)
    • Duplicate‑proof pending pool
    • Longest‑chain verification + replace_chain helper
    """

    def __init__(self):
        self.chain: List[Dict] = []
        self.current_transactions: List[Dict] = []
        self._pending_tx_set: set[str] = set()      # hashes of txs in current pool
        self.new_block(proof=100, previous_hash='1')  # genesis

    # ───────────────────────── Block & TX helpers ──────────────────────────
    @staticmethod
    def tx_hash(tx: Dict) -> str:
        """Deterministic string hash for a transaction dict."""
        return json.dumps(tx, sort_keys=True)

    def is_valid_transaction(self, sender: str, recipient: str, amount: str) -> bool:
        if not sender or not recipient:
            return False
        try:
            return float(amount) > 0
        except ValueError:
            return False

    def new_transaction(self, sender: str, recipient: str, amount: str) -> Optional[int]:
        """Add a validated, non‑duplicate transaction to the mempool."""
        if not self.is_valid_transaction(sender, recipient, amount):
            return None

        tx = {'sender': sender, 'recipient': recipient, 'amount': amount}
        h = self.tx_hash(tx)
        if h in self._pending_tx_set:
            return None  # duplicate in pool

        self.current_transactions.append(tx)
        self._pending_tx_set.add(h)
        return self.last_block['index'] + 1

    def new_block(self, proof: int, previous_hash: Optional[str] = None) -> Dict:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # clear mempool + hash set
        self.current_transactions = []
        self._pending_tx_set = set()
        self.chain.append(block)
        return block

    # ──────────────────────────── Hashing ─────────────────────────────
    @staticmethod
    def hash(block: Dict) -> str:
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    @property
    def last_block(self) -> Dict:  # convenience
        return self.chain[-1]

    # ────────────────────────── Proof of Work ─────────────────────────
    def proof_of_work(self, last_proof: int) -> int:
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        guess_hash = hashlib.sha256(f'{last_proof}{proof}'.encode()).hexdigest()
        return guess_hash[:4] == "0000"

    # ───────────────────────── Chain verification ─────────────────────
    def valid_chain(self, chain: List[Dict]) -> bool:
        last = chain[0]
        for idx in range(1, len(chain)):
            block = chain[idx]
            if block['previous_hash'] != self.hash(last):
                return False
            if not self.valid_proof(last['proof'], block['proof']):
                return False
            last = block
        return True

    def replace_chain(self, new_chain: List[Dict]) -> bool:
        """Adopt longer valid chain and keep duplicate guard intact."""
        if len(new_chain) <= len(self.chain) or not self.valid_chain(new_chain):
            print("[INFO] Chain not replaced (shorter or invalid).")
            return False

        self.chain = new_chain
        # rebuild set of pending hashes to avoid duplicates
        self._pending_tx_set = {self.tx_hash(tx) for tx in self.current_transactions}
        print("[INFO] Chain replaced with longer valid chain.")
        return True
