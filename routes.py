from flask import request, jsonify
import requests
from blockchain.block import Block
from blockchain.blockchain import Blockchain
from blockchain.transaction import Transaction
from blockchain.wallet import Wallet

def setup_routes(app, blockchain, port):
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
            # Broadcast the transaction to other nodes
            for peer in blockchain.peers:
                try:
                    requests.post(f'{peer}/transaction/add', json=transaction.to_dict())
                except requests.exceptions.RequestException as e:
                    print(f"Error broadcasting transaction to {peer}: {e}")
            return jsonify(transaction.to_dict())
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/transaction/add', methods=['POST'])
    def add_transaction():
        data = request.json
        transaction = Transaction(
            sender=data['sender'],
            recipient=data['recipient'],
            amount=data['amount'],
            signature=data['signature']
        )
        blockchain.add_transaction(transaction.to_dict())
        return jsonify({"message": "Transaction added"}), 200

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
        return jsonify({"pending_transactions": list(blockchain.mempool.values())})

    @app.route('/ico_funds', methods=['GET'])
    def get_ico_funds():
        return jsonify({"ICO_funds_remaining": blockchain.ico_funds["GENESIS_WALLET"]}), 200

    @app.route('/sync', methods=['POST'])
    def sync():
        data = request.json
        incoming_chain = data.get('chain')
        incoming_wallets = data.get('wallets')
        incoming_pending_transactions = data.get('pending_transactions')
        if incoming_chain and incoming_wallets and incoming_pending_transactions:
            incoming_chain = [Block.from_dict(block_data) for block_data in incoming_chain]
            if blockchain.is_valid_chain(incoming_chain) and len(incoming_chain) > len(blockchain.chain):
                blockchain.replace_chain(incoming_chain)
                blockchain.update_wallets(incoming_wallets)
                blockchain.mempool = {tx['signature']: tx for tx in incoming_pending_transactions}
                return jsonify({"message": "Blockchain updated"}), 200
        return jsonify({"message": "Incoming chain, wallets, or pending transactions are invalid"}), 400

    @app.route('/request_chain', methods=['GET'])
    def request_chain():
        chain_data = [block.to_dict() for block in blockchain.chain]
        return jsonify({"chain": chain_data})

    @app.route('/wallets', methods=['GET'])
    def get_wallets():
        return jsonify({"wallets": blockchain.wallets})
    

    @app.route('/add_block', methods=['POST'])
    def add_block():
        data = request.json
        block = Block.from_dict(data)
        if blockchain.add_block(block):
            return jsonify({"message": "Block added"}), 200
        return jsonify({"message": "Invalid block"}), 400


    return app
