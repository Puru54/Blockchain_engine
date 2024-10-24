
import os
import couchdb

class CouchDBHandler:
    def __init__(self):
        # Use the COUCHDB_URL from environment variables
        couchdb_url = os.getenv('COUCHDB_URL', 'http://admin:admin@localhost:5984/')
        try:
            self.server = couchdb.Server(couchdb_url)
            # Create or access the 'blockchain' database
            if 'blockchain' not in self.server:
                self.db = self.server.create('blockchain')
                print("Created 'blockchain' database in CouchDB.")
            else:
                self.db = self.server['blockchain']
                print("Connected to existing 'blockchain' database.")
        except Exception as e:
            print(f"Error connecting to CouchDB at {couchdb_url}: {e}")

    def save_block(self, block):
        try:
            self.db.save(block.to_dict())
            print("Block saved to CouchDB.")
        except Exception as e:
            print(f"Error saving block: {e}")

    def save_blockchain_state(self, blockchain_state):
        try:
            doc_id = "blockchain_state"
            if doc_id in self.db:
                doc = self.db[doc_id]
                doc.update(blockchain_state)
                self.db.save(doc)
                print("Blockchain state updated in CouchDB.")
            else:
                self.db.save({"_id": doc_id, **blockchain_state})
                print("Blockchain state saved to CouchDB.")
        except Exception as e:
            print(f"Error saving blockchain state: {e}")

    def load_blockchain_state(self):
        try:
            doc_id = "blockchain_state"
            if doc_id in self.db:
                print("Blockchain state loaded from CouchDB.")
                return self.db[doc_id]
            else:
                print("No blockchain state found in CouchDB.")
                return None
        except Exception as e:
            print(f"Error loading blockchain state: {e}")
            return None

    def delete_blockchain_state(self):
        try:
            doc_id = "blockchain_state"
            if doc_id in self.db:
                del self.db[doc_id]
                print("Blockchain state deleted from CouchDB.")
            else:
                print("No blockchain state found to delete.")
        except Exception as e:
            print(f"Error deleting blockchain state: {e}")

