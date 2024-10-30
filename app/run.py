from flask import Flask
from routes import setup_routes
from blockchain.blockchain import Blockchain
from blockchain.p2p import P2PNetwork
import os


app = Flask(__name__)

# Initialize the blockchain and P2P network
blockchain = Blockchain()
p2p_network = P2PNetwork(blockchain=blockchain)

# Start the P2P network
p2p_network.start()

# Connect to peers
peers = os.getenv('PEERS', '').split(',')
for peer in peers:
    if peer:
        host_port = peer.replace('http://', '').replace('ws://', '').split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 5001
        p2p_network.connect_to_peer(host, port)

# Pass the blockchain and p2p network to routes
setup_routes(app, blockchain, p2p_network)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
