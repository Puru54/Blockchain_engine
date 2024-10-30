from flask import Flask, request, jsonify
from routes import setup_routes
from blockchain.blockchain import Blockchain
from database.couchdb_handler import CouchDBHandler
import threading
from werkzeug.serving import make_server


def create_app(db_name):
    app = Flask(__name__)
    blockchain = Blockchain(CouchDBHandler(db_name))
    setup_routes(app, blockchain)
    return app


def run_app(port, db_name):
    app = create_app(db_name)
    server = make_server('0.0.0.0', port, app)
    server.serve_forever()

if __name__ == '__main__':
    # Define ports and corresponding database names
    configs = [
        (5000, 'blockchain_node1'),
        (5001, 'blockchain_node2'),
        (5002, 'blockchain_node3')
    ]

    # Start a thread for each instance
    threads = []
    for port, db_name in configs:
        thread = threading.Thread(target=run_app, args=(port, db_name))
        thread.start()
        threads.append(thread)

    # Join threads to main
    for thread in threads:
        thread.join()
