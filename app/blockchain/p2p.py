import threading
import asyncio
import json
import websockets
from blockchain.transaction import Transaction

class P2PNetwork:
    def __init__(self, host='0.0.0.0', port=5001, blockchain=None):
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.peers = []

    def start(self):
        """Start the WebSocket server in a separate event loop."""
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            start_server = websockets.serve(self.handle_connection, self.host, self.port)
            loop.run_until_complete(start_server)
            loop.run_forever()
        threading.Thread(target=run_server, daemon=True).start()
        print(f"P2P Network server started on {self.host}:{self.port}")

    async def handle_connection(self, websocket, path):
        """Handle incoming connections from peers."""
        self.peers.append(websocket)
        try:
            async for message in websocket:
                await self.handle_message(message)
        except websockets.ConnectionClosed:
            self.peers.remove(websocket)

    async def handle_message(self, message):
        """Handle incoming messages."""
        data = json.loads(message)
        msg_type = data.get('type')

        if msg_type == 'BLOCK':
            await self.handle_incoming_block(data['block'])
        elif msg_type == 'TRANSACTION':
            await self.handle_incoming_transaction(data['transaction'])
        elif msg_type == 'WALLET':
            await self.handle_incoming_wallet(data['public_key'])
        elif msg_type == 'SYNC':
            await self.handle_sync(data['chain'])
        elif msg_type == 'PENDING_TRANSACTIONS':
            await self.handle_incoming_pending_transactions(data['transactions'])

    async def handle_incoming_block(self, block_data):
        block = self.blockchain.create_block_from_dict(block_data)
        if block.index >= len(self.blockchain.chain):
            if self.blockchain.add_block(block):
                print("Block added to the chain.")
                await self.broadcast_block(block.to_dict())
            else:
                print("Block validation failed. Requesting full chain sync.")
                await self.request_full_chain()

    async def handle_incoming_transaction(self, transaction_data):
        transaction = Transaction(**transaction_data)
        if transaction.to_dict() not in self.blockchain.pending_transactions:
            self.blockchain.pending_transactions.append(transaction.to_dict())
            self.blockchain.save_state()
            print("Transaction added to the pending pool.")
            await self.broadcast_transaction(transaction.to_dict())

    async def handle_incoming_wallet(self, public_key):
        if public_key not in self.blockchain.wallets:
            self.blockchain.wallets[public_key] = 10
            self.blockchain.save_state()
            print(f"Received new wallet: {public_key}")
            await self.broadcast_wallet(public_key)

    async def broadcast_block(self, block_data):
        """Broadcast block to all connected peers."""
        message = json.dumps({"type": "BLOCK", "block": block_data})
        await self._broadcast_message(message)

    async def broadcast_transaction(self, transaction_data):
        """Broadcast transaction to all connected peers."""
        message = json.dumps({"type": "TRANSACTION", "transaction": transaction_data})
        await self._broadcast_message(message)

    async def broadcast_wallet(self, public_key):
        """Broadcast wallet creation to all connected peers."""
        message = json.dumps({"type": "WALLET", "public_key": public_key})
        await self._broadcast_message(message)

    async def _broadcast_message(self, message):
        """Internal method to broadcast messages to all peers."""
        for peer in self.peers:
            try:
                await peer.send(message)
                print("Message sent to peer.")
            except Exception as e:
                print(f"Failed to send message to peer: {e}")

    async def request_full_chain(self):
        """Request the full chain from all peers."""
        message = json.dumps({"type": "REQUEST_CHAIN"})
        await self._broadcast_message(message)

    async def request_pending_transactions(self):
        """Request pending transactions from all peers."""
        message = json.dumps({"type": "REQUEST_PENDING_TRANSACTIONS"})
        await self._broadcast_message(message)

    async def handle_sync(self, incoming_chain_data):
        """Handle incoming chain sync request."""
        incoming_chain = [self.blockchain.create_block_from_dict(block) for block in incoming_chain_data]
        if len(incoming_chain) > len(self.blockchain.chain):
            self.blockchain.chain = incoming_chain
            self.blockchain.save_state()
            print("Blockchain synchronized with peer.")

    async def handle_incoming_pending_transactions(self, transactions):
        """Handle incoming pending transactions from peers."""
        for transaction in transactions:
            if transaction not in self.blockchain.pending_transactions:
                self.blockchain.pending_transactions.append(transaction)
        self.blockchain.save_state()
        print("Pending transactions synchronized with peer.")

    def connect_to_peer(self, host, port):
        """Connect to a new peer via WebSocket."""
        async def connect():
            try:
                uri = f"ws://{host}:{port}"
                websocket = await websockets.connect(uri)
                self.peers.append(websocket)
                print(f"Connected to peer at {host}:{port}")
                await self.request_full_chain()
                await self.request_pending_transactions()
            except Exception as e:
                print(f"Failed to connect to peer at {host}:{port}: {e}")

        asyncio.run(connect())
