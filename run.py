import threading
import requests
import time
from werkzeug.serving import make_server
from flask import Flask
from routes import setup_routes
from blockchain.blockchain import Blockchain
from database.couchdb_handler import CouchDBHandler

def create_app(db_name):
    app = Flask(__name__)
    blockchain = Blockchain(CouchDBHandler(db_name))
    setup_routes(app, blockchain)
    return app

def run_app(port, db_name):
    app = create_app(db_name)
    server = make_server('0.0.0.0', port, app)
    server.serve_forever()

def sync_with_peers(port, peers):
    while True:
        time.sleep(10)  # Sync every 10 seconds
        for peer in peers:
            try:
                response = requests.get(f'http://{peer}/request_chain')
                if response.status_code == 200:
                    chain = response.json().get('chain')
                    if chain:
                        requests.post(f'http://127.0.0.1:{port}/sync', json={'chain': chain})
            except requests.exceptions.RequestException as e:
                print(f"Error syncing with peer {peer}: {e}")

if __name__ == '__main__':
    # Define ports and corresponding database names
    configs = [
        (5000, 'blockchain_node1', ['127.0.0.1:5001', '127.0.0.1:5002']),
        (5001, 'blockchain_node2', ['127.0.0.1:5000', '127.0.0.1:5002']),
        (5002, 'blockchain_node3', ['127.0.0.1:5000', '127.0.0.1:5001'])
    ]

    threads = []
    for port, db_name, peers in configs:
        thread = threading.Thread(target=run_app, args=(port, db_name))
        thread.start()
        threads.append(thread)
        sync_thread = threading.Thread(target=sync_with_peers, args=(port, peers))
        sync_thread.start()
        threads.append(sync_thread)

    for thread in threads:
        thread.join()
