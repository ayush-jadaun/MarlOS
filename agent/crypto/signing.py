"""
Ed25519 Cryptographic Signing
Handles key generation, signing, and verification
"""
import os
import json
from pathlib import Path
from typing import Tuple, Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey
)
from cryptography.hazmat.primitives import serialization
import base64


class SigningKey:
    """Ed25519 signing key management"""
    
    def __init__(self, private_key: Ed25519PrivateKey = None):
        if private_key is None:
            self.private_key = Ed25519PrivateKey.generate()
        else:
            self.private_key = private_key
        
        self.public_key = self.private_key.public_key()
    
    def sign(self, message: bytes) -> bytes:
        """Sign a message"""
        return self.private_key.sign(message)
    
    def verify(self, message: bytes, signature: bytes) -> bool:
        """Verify a signature"""
        try:
            self.public_key.verify(signature, message)
            return True
        except Exception:
            return False
    
    def public_key_bytes(self) -> bytes:
        """Get public key as bytes"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def public_key_hex(self) -> str:
        """Get public key as hex string"""
        return self.public_key_bytes().hex()
    
    def private_key_bytes(self) -> bytes:
        """Get private key as bytes"""
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
    
    def save_to_file(self, filepath: str):
        """Save keys to file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        key_data = {
            'private_key': base64.b64encode(self.private_key_bytes()).decode(),
            'public_key': base64.b64encode(self.public_key_bytes()).decode()
        }
        
        with open(filepath, 'w') as f:
            json.dump(key_data, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'SigningKey':
        """Load keys from file"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Key file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            key_data = json.load(f)
        
        private_key_bytes = base64.b64decode(key_data['private_key'])
        private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        
        return cls(private_key)
    
    @classmethod
    def load_or_generate(cls, filepath: str) -> 'SigningKey':
        """Load existing key or generate new one"""
        try:
            return cls.load_from_file(filepath)
        except FileNotFoundError:
            key = cls()
            key.save_to_file(filepath)
            return key


class VerifyingKey:
    """Ed25519 public key for verification only"""
    
    def __init__(self, public_key: Ed25519PublicKey):
        self.public_key = public_key
    
    def verify(self, message: bytes, signature: bytes) -> bool:
        """Verify a signature"""
        try:
            self.public_key.verify(signature, message)
            return True
        except Exception:
            return False
    
    def public_key_bytes(self) -> bytes:
        """Get public key as bytes"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def public_key_hex(self) -> str:
        """Get public key as hex string"""
        return self.public_key_bytes().hex()
    
    @classmethod
    def from_bytes(cls, public_key_bytes: bytes) -> 'VerifyingKey':
        """Create from public key bytes"""
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        return cls(public_key)
    
    @classmethod
    def from_hex(cls, public_key_hex: str) -> 'VerifyingKey':
        """Create from hex string"""
        return cls.from_bytes(bytes.fromhex(public_key_hex))


def sign_message(signing_key: SigningKey, message: dict) -> dict:
    """Sign a message dictionary"""
    # Serialize message (excluding signature and public_key fields)
    message_copy = message.copy()
    message_copy.pop('signature', None)
    message_copy.pop('public_key', None)  # Also remove public_key before signing

    message_bytes = json.dumps(message_copy, sort_keys=True).encode()
    signature = signing_key.sign(message_bytes)

    # Add signature and public key
    message['signature'] = base64.b64encode(signature).decode()
    message['public_key'] = signing_key.public_key_hex()

    return message


def verify_message(message: dict) -> bool:
    """Verify a signed message"""
    if 'signature' not in message or 'public_key' not in message:
        return False
    
    try:
        # Extract signature and public key
        signature = base64.b64decode(message['signature'])
        verifying_key = VerifyingKey.from_hex(message['public_key'])
        
        # Recreate message without signature
        message_copy = message.copy()
        message_copy.pop('signature')
        message_copy.pop('public_key', None)
        
        message_bytes = json.dumps(message_copy, sort_keys=True).encode()
        
        return verifying_key.verify(message_bytes, signature)
    
    except Exception as e:
        print(f"Verification failed: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # Generate key
    key = SigningKey()
    print(f"Public key: {key.public_key_hex()}")
    
    # Sign message
    message = {"type": "test", "data": "hello world"}
    signed_message = sign_message(key, message)
    print(f"Signed message: {signed_message}")
    
    # Verify
    is_valid = verify_message(signed_message)
    print(f"Valid: {is_valid}")
    
    # Tamper with message
    signed_message['data'] = "tampered"
    is_valid = verify_message(signed_message)
    print(f"Valid after tampering: {is_valid}")
