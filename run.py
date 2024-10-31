import threading
import requests
import time
from werkzeug.serving import make_server
from flask import Flask
from routes import setup_routes
from blockchain.blockchain import Blockchain
from database.couchdb_handler import CouchDBHandler

def create_app(db_name, port):
    app = Flask(__name__)
    blockchain = Blockchain(CouchDBHandler(db_name))
    blockchain.peers = [f'http://127.0.0.1:{p}' for p in range(5000, 5003) if p != port]
    setup_routes(app, blockchain, port)
    return app

def run_app(port, db_name):
    app = create_app(db_name, port)
    server = make_server('0.0.0.0', port, app)
    server.serve_forever()

def sync_with_peers(blockchain, port, peers):
    while True:
        time.sleep(10)  # Sync every 10 seconds
        for peer in peers:
            try:
                response_chain = requests.get(f'{peer}/request_chain')
                response_wallets = requests.get(f'{peer}/wallets')
                response_pending_transactions = requests.get(f'{peer}/pending_transactions')
                if response_chain.status_code == 200 and response_wallets.status_code == 200 and response_pending_transactions.status_code == 200:
                    chain = response_chain.json().get('chain')
                    wallets = response_wallets.json().get('wallets')
                    pending_transactions = response_pending_transactions.json().get('pending_transactions')
                    if chain and wallets and pending_transactions:
                        requests.post(f'http://127.0.0.1:{port}/sync', json={'chain': chain, 'wallets': wallets, 'pending_transactions': pending_transactions})
            except requests.exceptions.RequestException as e:
                print(f"Error syncing with peer {peer}: {e}")

if __name__ == '__main__':
    configs = [
        (5000, 'blockchain_node1', ['http://127.0.0.1:5001', 'http://127.0.0.1:5002']),
        (5001, 'blockchain_node2', ['http://127.0.0.1:5000', 'http://127.0.0.1:5002']),
        (5002, 'blockchain_node3', ['http://127.0.0.1:5000', 'http://127.0.0.1:5001'])
    ]
    threads = []
    for port, db_name, peers in configs:
        thread = threading.Thread(target=run_app, args=(port, db_name))
        thread.start()
        threads.append(thread)
        sync_thread = threading.Thread(target=sync_with_peers, args=(Blockchain(CouchDBHandler(db_name)), port, peers))
        sync_thread.start()
        threads.append(sync_thread)
    for thread in threads:
        thread.join()
