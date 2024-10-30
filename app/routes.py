import asyncio
import threading
from flask import request, jsonify
from blockchain.blockchain import Blockchain
from blockchain.wallet import Wallet
from database.couchdb_handler import CouchDBHandler





blockchain = Blockchain()
couchdb = CouchDBHandler()

def setup_routes(app, blockchain, p2p_network):
    loop = p2p_network.loop  

    @app.route('/wallet/create', methods=['POST'])
    def create_wallet():
        wallet = Wallet(blockchain)
        def broadcast():
            asyncio.run_coroutine_threadsafe(
                p2p_network.broadcast_wallet(wallet.public_key), loop
            )
        threading.Thread(target=broadcast).start()
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
            # Broadcast the transaction to peers in a new thread
            def broadcast():
                asyncio.run_coroutine_threadsafe(
                    p2p_network.broadcast_transaction(transaction.to_dict()), p2p_network.loop
                )
            threading.Thread(target=broadcast).start()
            return jsonify(transaction.to_dict())
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        

        
    @app.route('/peers', methods=['GET'])
    def get_peers():
        peers = p2p_network.get_connected_peers()
        return jsonify({"connected_peers": peers})


    @app.route('/mine', methods=['GET'])
    def mine_block():
        new_block = blockchain.mine()
        if new_block:
            couchdb.save_block(new_block)
            def broadcast():
                asyncio.run_coroutine_threadsafe(
                    p2p_network.broadcast_block(new_block.to_dict()), p2p_network.loop
                )
            threading.Thread(target=broadcast).start()
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
