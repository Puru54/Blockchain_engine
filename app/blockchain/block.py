import time
from crypto.crypto import Crypto

class Block:
    def __init__(self, index, transactions, previous_hash, timestamp=None, nonce=0):
        self.index = index
        self.transactions = self._prepare_transactions(transactions)
        self.timestamp = timestamp or time.time()  # Use provided timestamp or current time
        self.previous_hash = previous_hash
        self.nonce = nonce

    def _prepare_transactions(self, transactions):
        # Ensure transactions are in dictionary format
        if isinstance(transactions, list):
            return [tx if isinstance(tx, dict) else tx.to_dict() for tx in transactions]
        return []

    def hash(self):
        data = (
            str(self.index)
            + str(self.transactions)
            + str(self.timestamp)
            + str(self.previous_hash)
            + str(self.nonce)
        )
        return Crypto.hash(data)

    def mine(self, difficulty=4):
        target = '0' * difficulty
        while not self.hash().startswith(target):
            self.nonce += 1

    def to_dict(self):
        return {
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }

    @classmethod
    def from_dict(cls, block_data):
        # Reconstructs a block from a dictionary
        return cls(
            index=block_data['index'],
            transactions=block_data['transactions'],
            previous_hash=block_data['previous_hash'],
            timestamp=block_data['timestamp'],
            nonce=block_data['nonce']
        )
