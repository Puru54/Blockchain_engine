from cryptolib.crypto import Crypto

class Wallet:
    def __init__(self, blockchain):
        self.private_key, self.public_key = Crypto.generate_keypair()
        blockchain.create_wallet(self.public_key)

    def export_keys(self, blockchain):
        return {
            'private_key': self.private_key,
            'public_key': self.public_key,
            'balance': blockchain.get_balance(self.public_key)
        }
 