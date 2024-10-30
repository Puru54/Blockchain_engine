from flask import request, jsonify
from blockchain.blockchain import Blockchain
from blockchain.wallet import Wallet

def setup_routes(app, blockchain):
    @app.route('/wallet/create', methods=['POST'])
    def create_wallet():
        wallet = Wallet(blockchain)
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
            return jsonify(transaction.to_dict())
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/peers', methods=['GET'])
    def get_peers():
        return jsonify({"connected_peers": []})

    @app.route('/mine', methods=['GET'])
    def mine_block():
        new_block = blockchain.mine()
        if new_block:
            blockchain.couchdb.save_block(new_block)
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
        try:
            balance = blockchain.get_genesis_balance(wallet_address)
            return jsonify({"wallet_address": wallet_address, "genesis_balance": balance}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/ico_funds', methods=['GET'])
    def get_ico_funds():
        return jsonify({"ICO_funds_remaining": blockchain.ico_funds["GENESIS_WALLET"]}), 200
