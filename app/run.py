from flask import Flask
from app.blockchain.blockchain import Blockchain
from routes import setup_routes

app = Flask(__name__)
app.blockchain = Blockchain()  

setup_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
