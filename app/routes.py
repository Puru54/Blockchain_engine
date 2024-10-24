from flask import request, jsonify
from blockchain.blockchain import Blockchain
from blockchain.wallet import Wallet
from database.couchdb_handler import CouchDBHandler

# Create a global instance of Blockchain here
blockchain = Blockchain()
couchdb = CouchDBHandler()

def setup_routes(app):
    @app.route('/wallet/create', methods=['POST'])
    def create_wallet():
        wallet = Wallet(blockchain)  # Pass the global blockchain instance
        return jsonify(wallet.export_keys(blockchain))

    @app.route('/transaction/create', methods=['POST'])
    def create_transaction():
        data = request.json
        sender = data.get('sender')
        recipient = data.get('recipient')
        amount = data.get('amount')
        private_key = data.get('private_key')

        if not sender or not recipient or not amount or not private_key:
            return jsonify({"error": "Missing fields in request"}), 400

        try:
            transaction = blockchain.validate_and_process_transaction(sender, recipient, amount, private_key)
            blockchain.add_transaction(transaction)
            return jsonify(transaction.to_dict())
        except ValueError as e:
            return jsonify({"error": str(e)}), 400


    @app.route('/transaction/receive', methods=['POST'])
    def receive_transaction():
        data = request.json
        transaction = Transaction(data['sender'], data['recipient'], data['amount'], data['signature'])
        blockchain.add_transaction(transaction)
        return jsonify({'message': 'Transaction received and added to the pool'}), 201

    @app.route('/mine', methods=['GET'])
    def mine_block():
        new_block = blockchain.mine()
        if new_block:
            couchdb.save_block(new_block)
            return jsonify(new_block.to_dict())
        return jsonify({"message": "No transactions to mine"})
    

    @app.route('/chain', methods=['GET'])
    def get_chain():
        chain_data = [block.to_dict() for block in blockchain.chain]
        return jsonify(chain_data)

    @app.route('/balance/<wallet_address>', methods=['GET'])
    def get_balance(wallet_address):
        balance = blockchain.get_balance(wallet_address)
        return jsonify({"balance": balance})

    @app.route('/pending_transactions', methods=['GET'])
    def get_pending_transactions():
        return jsonify({"pending_transactions": blockchain.pending_transactions})

    @app.route('/genesis_balance/<wallet_address>', methods=['GET'])
    def genesis_balance(wallet_address):
        """
        Endpoint to get the balance of a wallet address from the Genesis block.
        """
        try:
            balance = blockchain.get_genesis_balance(wallet_address)
            return jsonify({"wallet_address": wallet_address, "genesis_balance": balance}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/ico_funds', methods=['GET'])
    def get_ico_funds():
        """
        Get the remaining ICO funds.
        """
        return jsonify({"ICO_funds_remaining": blockchain.ico_funds["GENESIS_WALLET"]}), 200
    


    @app.route('/nodes/register', methods=['POST'])
    def register_node():
        print("Register node endpoint hit")  # Debugging line
        node_address = request.json.get('node_address')
        if node_address is None:
            return jsonify({'error': 'Invalid request: Provide a valid node address'}), 400
        app.blockchain.register_node(node_address)
        return jsonify({'message': 'Node registered successfully'}), 201

