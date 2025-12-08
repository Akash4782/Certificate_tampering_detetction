# blockchain.py

import hashlib
import json
import os
from datetime import datetime

class Block:
    """
    Represents a single block in the blockchain.
    Each block stores the certificate hash, previous block hash, timestamp, and its own hash.
    """
    def __init__(self, index, certificate_hash, previous_hash, timestamp=None):
        self.index = index
        self.certificate_hash = certificate_hash
        self.previous_hash = previous_hash
        self.timestamp = timestamp if timestamp else datetime.utcnow()
        self.hash = self.compute_hash()

    def compute_hash(self):
        """
        Computes SHA-256 hash of the block's contents.
        """
        block_string = (
            str(self.index) +
            str(self.certificate_hash) +
            str(self.previous_hash) +
            self.timestamp.isoformat()
        )
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self):
        """Convert block to dictionary for serialization"""
        return {
            'index': self.index,
            'certificate_hash': self.certificate_hash,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp.isoformat(),
            'hash': self.hash
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create block from dictionary"""
        timestamp = datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp']
        block = cls(data['index'], data['certificate_hash'], data['previous_hash'], timestamp)
        block.hash = data['hash']
        return block


class Blockchain:
    """
    Blockchain to store certificate hashes in a tamper-proof way.
    Supports persistence to JSON file.
    """
    def __init__(self, persist_file=None):
        self.chain = []
        self.persist_file = persist_file
        self.create_genesis_block()
        if persist_file and os.path.exists(persist_file):
            self.load_from_file()

    def create_genesis_block(self):
        """
        Creates the first block in the blockchain with a dummy hash.
        """
        if not self.chain:  # Only create if chain is empty
            genesis_block = Block(0, "Genesis Block", "0")
            self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1] if self.chain else None

    def add_block(self, certificate_hash):
        """
        Adds a new block containing the certificate hash to the blockchain.
        Returns the new block with its index.
        """
        if not self.chain:
            self.create_genesis_block()
        
        previous_hash = self.last_block.hash
        new_block = Block(len(self.chain), certificate_hash, previous_hash)
        self.chain.append(new_block)
        
        # Persist to file if configured
        if self.persist_file:
            self.save_to_file()
        
        return new_block

    def verify_certificate(self, certificate_hash):
        """
        Verifies if a certificate hash exists in the blockchain.
        Returns block index if found, else None.
        """
        for block in self.chain:
            if block.certificate_hash == certificate_hash:
                return block.index
            # Also check if hash is in JSON data
            try:
                import json
                block_data = json.loads(block.certificate_hash)
                if block_data.get('pdf_hash') == certificate_hash:
                    return block.index
            except:
                pass
        return None

    def get_block_by_hash(self, certificate_hash):
        """Get block containing the certificate hash"""
        for block in self.chain:
            if block.certificate_hash == certificate_hash:
                return block
            # Also check if hash is in JSON data
            try:
                import json
                block_data = json.loads(block.certificate_hash)
                if block_data.get('pdf_hash') == certificate_hash:
                    return block
            except:
                pass
        return None
    
    def get_hash_by_cert_id(self, cert_id):
        """Get PDF hash from blockchain by certificate ID"""
        import json
        for block in self.chain:
            try:
                block_data = json.loads(block.certificate_hash)
                if block_data.get('cert_id') == cert_id:
                    return block_data.get('pdf_hash')
            except:
                pass
        return None

    def is_chain_valid(self):
        """
        Validates the integrity of the blockchain.
        Returns True if the chain is valid, else False.
        """
        if len(self.chain) == 0:
            return False
        
        if len(self.chain) == 1:
            return True
        
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Verify current block hash
            if current.hash != current.compute_hash():
                return False
            
            # Verify chain linkage
            if current.previous_hash != previous.hash:
                return False

        return True
    
    def get_chain_info(self):
        """Get blockchain statistics"""
        return {
            'total_blocks': len(self.chain),
            'certificate_blocks': len(self.chain) - 1,  # Exclude genesis
            'is_valid': self.is_chain_valid(),
            'last_block_hash': self.last_block.hash if self.last_block else None
        }
    
    def save_to_file(self):
        """Save blockchain to JSON file"""
        if not self.persist_file:
            return
        
        try:
            chain_data = [block.to_dict() for block in self.chain]
            with open(self.persist_file, 'w') as f:
                json.dump(chain_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving blockchain: {e}")
    
    def load_from_file(self):
        """Load blockchain from JSON file"""
        if not self.persist_file or not os.path.exists(self.persist_file):
            return
        
        try:
            with open(self.persist_file, 'r') as f:
                chain_data = json.load(f)
            
            self.chain = []
            for block_data in chain_data:
                block = Block.from_dict(block_data)
                self.chain.append(block)
        except Exception as e:
            print(f"Error loading blockchain: {e}")
            self.chain = []
            self.create_genesis_block()
