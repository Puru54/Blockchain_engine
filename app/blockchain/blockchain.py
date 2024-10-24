import threading
import time

import requests
from blockchain.block import Block
from blockchain.transaction import Transaction
from crypto.crypto import Crypto
from database.couchdb_handler import CouchDBHandler

class Blockchain:
    def __init__(self):
        self.couchdb = CouchDBHandler()
        self.chain = []
        self.pending_transactions = []
        self.wallets = {}
        self.peers = set()  

        self.load_state()
        self.ico_funds = {"GENESIS_WALLET": 1000000}
      

    def create_genesis_block(self):
        ico_transactions = [{"sender": "ICO", "recipient": "GENESIS_WALLET", "amount": 1000000}]
        return Block(0, ico_transactions, "0")

    def save_state(self):
        blockchain_state = {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": self.pending_transactions,
            "wallets": self.wallets
        }
        self.couchdb.save_blockchain_state(blockchain_state)

    def load_state(self):
        state = self.couchdb.load_blockchain_state()
        if state:
            self.chain = [Block(**block) for block in state.get("chain", [])]
            self.pending_transactions = state.get("pending_transactions", [])
            self.wallets = state.get("wallets", {"GENESIS_WALLET": 1000000})
            print("Blockchain state loaded from CouchDB")
        else:
            self.chain = [self.create_genesis_block()]
            self.pending_transactions = []
            self.wallets = {"GENESIS_WALLET": 1000000}
            print("Initialized new blockchain with genesis block")

    def create_wallet(self, public_key):
        """
        Create a new wallet and allocate initial funds from the ICO.
        """
        if self.ico_funds["GENESIS_WALLET"] >= 10:
            if public_key not in self.wallets:
                self.wallets[public_key] = 10  
                self.ico_funds["GENESIS_WALLET"] -= 10  
                print(f"Created wallet {public_key} with 10 coins. Remaining ICO funds: {self.ico_funds['GENESIS_WALLET']}")
                self.save_state()  
            else:
                print("Wallet already exists.")
        else:
            raise ValueError("ICO funds depleted")

    def get_balance(self, wallet_address):
        return self.wallets.get(wallet_address, 0)

    def add_transaction(self, transaction):
        """Add a transaction to the pending transactions and broadcast it."""
        self.pending_transactions.append(transaction)
        self.save_state()
        self.broadcast_transaction(transaction)

        
    def validate_and_process_transaction(self, sender, recipient, amount, private_key):
        message = f"{sender}{recipient}{amount}"
        signature = Crypto.sign_transaction(private_key, message)

        if not Crypto.verify_signature(sender, message, signature):
            raise ValueError("Invalid signature")

        if self.get_balance(sender) < amount:
            raise ValueError("Insufficient funds")

        self.update_balance(sender, recipient, amount)

        transaction = Transaction(sender, recipient, amount, signature)
        self.add_transaction(transaction.to_dict())
        return transaction

    def update_balance(self, sender, recipient, amount):
        if self.wallets.get(sender, 0) >= amount:
            self.wallets[sender] -= amount
            self.wallets[recipient] = self.wallets.get(recipient, 0) + amount
            print(f"Transferred {amount} from {sender} to {recipient}")
            self.save_state()
        else:
            raise ValueError("Insufficient funds")

    def mine(self):
        if not self.pending_transactions:
            return None

        new_block = Block(len(self.chain), self.pending_transactions, self.chain[-1].hash())
        new_block.mine(difficulty=4)  
        self.chain.append(new_block)
        self.pending_transactions = []
        self.save_state()

        return new_block

    def sync_chain(self, incoming_chain):
        new_chain = [Block(**block) for block in incoming_chain]
        if len(new_chain) > len(self.chain):
            self.chain = new_chain
            self.save_state()
            print("Blockchain synchronized with a longer chain from peer.")

    def replace_chain(self, new_chain):
        if len(new_chain) > len(self.chain) and self.is_valid_chain(new_chain):
            self.chain = new_chain
            self.pending_transactions = []
            self.save_state()
            print("Chain replaced with the longer valid chain.")
            return True
        return False

    def is_valid_chain(self, chain):
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]
            if current_block['previous_hash'] != previous_block.hash():
                return False
        return True

   

    def register_node(self, address):
        """Register a new node with the blockchain network."""
        self.peers.add(address)
        print(f"Node registered: {address}") 

    def broadcast_transaction(self, transaction):
        """Broadcast a transaction to all peers in the network."""
        for peer in self.peers:
            url = f'{peer}/transaction/receive'
            try:
                requests.post(url, json=transaction.to_dict())
            except requests.exceptions.ConnectionError:
                continue 