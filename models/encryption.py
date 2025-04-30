from cryptography.fernet import Fernet

class EncryptionModel:
    def __init__(self):
        """Initialize encryption with a generated key."""
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)

    def encrypt(self, data):
        """
        Encrypt data (string or bytes).
        Args:
            data: String or bytes to encrypt.
        Returns:
            Encrypted bytes.
        """
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)

    def decrypt(self, encrypted_data):
        """
        Decrypt data.
        Args:
            encrypted_data: Encrypted bytes.
        Returns:
            Decrypted string.
        """
        return self.cipher.decrypt(encrypted_data)

    def get_key(self):
        """Return the encryption key."""
        return self.key