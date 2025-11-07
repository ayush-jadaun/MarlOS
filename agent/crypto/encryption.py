"""
Message Encryption using NaCl (libsodium)
Provides authenticated encryption for P2P communication
"""
import nacl.secret
import nacl.utils
import nacl.public
import base64
import json
from pathlib import Path
from typing import Tuple, Dict, Optional


class MessageEncryption:
    """Symmetric encryption for messages"""

    def __init__(self, key: bytes = None):
        if key is None:
            key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
        self.box = nacl.secret.SecretBox(key)
        self.key = key

    def encrypt(self, message: bytes) -> bytes:
        """Encrypt a message"""
        return self.box.encrypt(message)

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt a message"""
        return self.box.decrypt(ciphertext)

    def encrypt_string(self, message: str) -> str:
        """Encrypt string and return base64"""
        ciphertext = self.encrypt(message.encode())
        return base64.b64encode(ciphertext).decode()

    def decrypt_string(self, ciphertext_b64: str) -> str:
        """Decrypt base64 string"""
        ciphertext = base64.b64decode(ciphertext_b64)
        plaintext = self.decrypt(ciphertext)
        return plaintext.decode()


class AsymmetricEncryption:
    """Asymmetric encryption for P2P communication"""

    def __init__(self, private_key: nacl.public.PrivateKey = None):
        if private_key is None:
            self.private_key = nacl.public.PrivateKey.generate()
        else:
            self.private_key = private_key

        self.public_key = self.private_key.public_key

    def encrypt_for(self, recipient_public_key: nacl.public.PublicKey, message: bytes) -> bytes:
        """Encrypt message for a specific recipient"""
        box = nacl.public.Box(self.private_key, recipient_public_key)
        return box.encrypt(message)

    def decrypt_from(self, sender_public_key: nacl.public.PublicKey, ciphertext: bytes) -> bytes:
        """Decrypt message from a specific sender"""
        box = nacl.public.Box(self.private_key, sender_public_key)
        return box.decrypt(ciphertext)

    def public_key_bytes(self) -> bytes:
        """Get public key as bytes"""
        return bytes(self.public_key)

    def public_key_hex(self) -> str:
        """Get public key as hex"""
        return self.public_key_bytes().hex()

    def private_key_bytes(self) -> bytes:
        """Get private key as bytes"""
        return bytes(self.private_key)

    def save_to_file(self, filepath: str):
        """Save encryption keys to file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        key_data = {
            'private_key': base64.b64encode(self.private_key_bytes()).decode(),
            'public_key': base64.b64encode(self.public_key_bytes()).decode()
        }

        with open(filepath, 'w') as f:
            json.dump(key_data, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'AsymmetricEncryption':
        """Load keys from file"""
        with open(filepath, 'r') as f:
            key_data = json.load(f)

        private_key_bytes = base64.b64decode(key_data['private_key'])
        private_key = nacl.public.PrivateKey(private_key_bytes)

        return cls(private_key)

    @classmethod
    def load_or_generate(cls, filepath: str) -> 'AsymmetricEncryption':
        """Load existing keys or generate new ones"""
        try:
            return cls.load_from_file(filepath)
        except FileNotFoundError:
            enc = cls()
            enc.save_to_file(filepath)
            return enc

    @classmethod
    def from_public_key_hex(cls, public_key_hex: str) -> nacl.public.PublicKey:
        """Create public key from hex"""
        return nacl.public.PublicKey(bytes.fromhex(public_key_hex))


# Helper functions for job payload encryption

def encrypt_job_payload(payload: dict, recipient_public_key_hex: str,
                       sender_encryption: AsymmetricEncryption) -> str:
    """
    Encrypt job payload for a specific recipient

    Args:
        payload: Job payload dictionary
        recipient_public_key_hex: Recipient's public key (hex)
        sender_encryption: Sender's encryption object

    Returns:
        Base64 encoded encrypted payload
    """
    # Serialize payload
    payload_json = json.dumps(payload, sort_keys=True)
    payload_bytes = payload_json.encode()

    # Get recipient's public key
    recipient_public_key = AsymmetricEncryption.from_public_key_hex(recipient_public_key_hex)

    # Encrypt
    ciphertext = sender_encryption.encrypt_for(recipient_public_key, payload_bytes)

    # Encode as base64
    return base64.b64encode(ciphertext).decode()


def decrypt_job_payload(encrypted_payload: str, sender_public_key_hex: str,
                       recipient_encryption: AsymmetricEncryption) -> dict:
    """
    Decrypt job payload from a sender

    Args:
        encrypted_payload: Base64 encoded encrypted payload
        sender_public_key_hex: Sender's public key (hex)
        recipient_encryption: Recipient's encryption object

    Returns:
        Decrypted payload dictionary
    """
    # Decode from base64
    ciphertext = base64.b64decode(encrypted_payload)

    # Get sender's public key
    sender_public_key = AsymmetricEncryption.from_public_key_hex(sender_public_key_hex)

    # Decrypt
    plaintext = recipient_encryption.decrypt_from(sender_public_key, ciphertext)

    # Deserialize
    payload_json = plaintext.decode()
    return json.loads(payload_json)


def encrypt_message_field(message: dict, field: str,
                          recipient_public_key_hex: str,
                          sender_encryption: AsymmetricEncryption) -> dict:
    """
    Encrypt a specific field in a message dictionary

    Args:
        message: Message dictionary
        field: Field name to encrypt
        recipient_public_key_hex: Recipient's public key
        sender_encryption: Sender's encryption object

    Returns:
        Message with encrypted field
    """
    if field not in message:
        return message

    field_value = message[field]

    # Encrypt the field
    encrypted_value = encrypt_job_payload(
        {'value': field_value},
        recipient_public_key_hex,
        sender_encryption
    )

    # Replace with encrypted value and mark as encrypted
    message[field] = encrypted_value
    message[f'{field}_encrypted'] = True

    return message


def decrypt_message_field(message: dict, field: str,
                          sender_public_key_hex: str,
                          recipient_encryption: AsymmetricEncryption) -> dict:
    """
    Decrypt a specific field in a message dictionary

    Args:
        message: Message dictionary
        field: Field name to decrypt
        sender_public_key_hex: Sender's public key
        recipient_encryption: Recipient's encryption object

    Returns:
        Message with decrypted field
    """
    if not message.get(f'{field}_encrypted', False):
        return message

    encrypted_value = message[field]

    # Decrypt the field
    decrypted_data = decrypt_job_payload(
        encrypted_value,
        sender_public_key_hex,
        recipient_encryption
    )

    # Replace with decrypted value
    message[field] = decrypted_data['value']
    message.pop(f'{field}_encrypted', None)

    return message


# Example usage
if __name__ == "__main__":
    # Create sender and recipient
    sender = AsymmetricEncryption()
    recipient = AsymmetricEncryption()

    print(f"Sender public key: {sender.public_key_hex()}")
    print(f"Recipient public key: {recipient.public_key_hex()}")

    # Encrypt a job payload
    job_payload = {
        'command': 'secret_command',
        'api_key': 'super_secret_key_12345',
        'data': 'confidential data'
    }

    encrypted = encrypt_job_payload(job_payload, recipient.public_key_hex(), sender)
    print(f"\nEncrypted payload: {encrypted[:50]}...")

    # Decrypt
    decrypted = decrypt_job_payload(encrypted, sender.public_key_hex(), recipient)
    print(f"Decrypted payload: {decrypted}")

    # Verify
    assert decrypted == job_payload
    print("\n✅ Encryption/decryption successful!")
