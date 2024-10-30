import base64
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

class Crypto:
    @staticmethod
    def generate_keypair():
        key = RSA.generate(2048)
        private_key = base64.b64encode(key.export_key()).decode('utf-8')
        public_key = base64.b64encode(key.publickey().export_key()).decode('utf-8')
        return private_key, public_key

    @staticmethod
    def add_padding(base64_string):
        # Add padding to base64 string if required
        missing_padding = len(base64_string) % 4
        if missing_padding != 0:
            base64_string += '=' * (4 - missing_padding)
        return base64_string

    @staticmethod
    def sign_transaction(private_key, message):
        private_key = Crypto.add_padding(private_key)
        private_key_bytes = base64.b64decode(private_key.encode('utf-8'))
        key = RSA.import_key(private_key_bytes)
        h = SHA256.new(message.encode('utf-8'))
        signature = pkcs1_15.new(key).sign(h)
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify_signature(public_key, message, signature):
        public_key = Crypto.add_padding(public_key)
        public_key_bytes = base64.b64decode(public_key.encode('utf-8'))
        key = RSA.import_key(public_key_bytes)
        h = SHA256.new(message.encode('utf-8'))
        try:
            pkcs1_15.new(key).verify(h, base64.b64decode(Crypto.add_padding(signature)))
            return True
        except (ValueError, TypeError):
            return False
        

    @staticmethod
    def hash(data):
        h = SHA256.new(data.encode('utf-8'))
        return h.hexdigest()
