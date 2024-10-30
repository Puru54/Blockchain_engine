from blockchain.block import Block
from blockchain.transaction import Transaction
from cryptolib.crypto import Crypto
from database.couchdb_handler import CouchDBHandler

class Blockchain:
    def __init__(self, db_handler):
        self.couchdb = db_handler
        self.chain = []
        self.pending_transactions = []
        self.wallets = {}
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
            self.chain = [Block.from_dict(block_data) for block_data in state.get("chain", [])]
            self.pending_transactions = state.get("pending_transactions", [])
            self.wallets = state.get('wallets', {"GENESIS_WALLET": 1000000})
            print("Blockchain state loaded from CouchDB")
        else:
            self.chain = [self.create_genesis_block()]
            self.pending_transactions = []
            self.wallets = {"GENESIS_WALLET": 1000000}
            print("Initialized new blockchain with genesis block")


    def create_wallet(self, public_key):
        if self.ico_funds["GENESIS_WALLET"] >= 10:
            if public_key not in self.wallets:
                self.wallets[public_key] = 10
                self.ico_funds["GENESIS_WALLET"] -= 10
                self.save_state()
                print(f"Created wallet {public_key} with 10 coins. Remaining ICO funds: {self.ico_funds['GENESIS_WALLET']}")
            else:
                print("Wallet already exists.")
        else:
            raise ValueError("ICO funds depleted")


    def get_balance(self, wallet_address):
        return self.wallets.get(wallet_address, 0)

    def add_transaction(self, transaction):
        """Add a transaction to the pending transaction pool."""
        self.pending_transactions.append(transaction)
        self.save_state()

    def validate_and_process_transaction(self, sender, recipient, amount, private_key):
        message = f"{sender}{recipient}{amount}"
        signature = Crypto.sign_transaction(private_key, message)
        if not Crypto.verify_signature(sender, message, signature):
            raise ValueError("Invalid signature")
        if self.get_balance(sender) < amount:
            raise ValueError("Insufficient funds")
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
        # Process transactions in the block
        for tx_data in self.pending_transactions:
            sender = tx_data['sender']
            recipient = tx_data['recipient']
            amount = tx_data['amount']
            self._process_transaction_in_block(sender, recipient, amount)
        self.pending_transactions = []
        self.save_state()
        return new_block

    def _process_transaction_in_block(self, sender, recipient, amount):
        if sender not in self.wallets:
            self.wallets[sender] = 0
        if recipient not in self.wallets:
            self.wallets[recipient] = 0

        self.wallets[sender] -= amount
        self.wallets[recipient] += amount



    def sync_chain(self, incoming_chain):
        new_chain = [Block(**block) for block in incoming_chain]
        if len(new_chain) > len(self.chain):
            self.chain = new_chain
            self.save_state()
            print("Blockchain synchronized with a longer chain from peer.")

    def is_valid_new_block(self, new_block, previous_block):
        if previous_block.index + 1 != new_block.index:
            return False
        elif previous_block.hash() != new_block.previous_hash:
            return False
        elif new_block.hash() != new_block.hash():
            return False
        else:
            return True

    def is_valid_chain(self, chain):
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]
            if current_block.previous_hash != previous_block.hash():
                return False
            if current_block.hash() != current_block.hash():
                return False
        return True


    def replace_chain(self, new_chain):
        if len(new_chain) > len(self.chain) and self.is_valid_chain(new_chain):
            self.chain = new_chain
            # Reset and recompute balances
            self.wallets = {"GENESIS_WALLET": 1000000}
            for block in self.chain[1:]:  # Skip genesis block
                for tx_data in block.transactions:
                    sender = tx_data['sender']
                    recipient = tx_data['recipient']
                    amount = tx_data['amount']
                    if sender not in self.wallets:
                        self.wallets[sender] = 0
                    if recipient not in self.wallets:
                        self.wallets[recipient] = 0
                    self._process_transaction_in_block(sender, recipient, amount)
            self.pending_transactions = []
            self.save_state()
            print("Chain replaced with the longer valid chain.")
            return True
        return False



    def add_block(self, block):
        if self.is_valid_new_block(block, self.chain[-1]):
            self.chain.append(block)
            # Process transactions in the block
            for tx_data in block.transactions:
                sender = tx_data['sender']
                recipient = tx_data['recipient']
                amount = tx_data['amount']
                self._process_transaction_in_block(sender, recipient, amount)
            self.pending_transactions = [
                tx for tx in self.pending_transactions if tx not in block.transactions
            ]
            self.save_state()
            return True
        else:
            return False

    def update_wallets(self, incoming_wallets):
        for wallet, balance in incoming_wallets.items():
            self.wallets[wallet] = balance
        self.save_state()
