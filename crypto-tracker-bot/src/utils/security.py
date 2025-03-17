from cryptography.fernet import Fernet
import os
import base64
import logging

# Initialize logger
logger = logging.getLogger(__name__)

class DataEncryptor:
    def __init__(self):
        # Retrieve the encryption key from the environment variable
        self.key = os.getenv("ENCRYPTION_KEY")
        
        if not self.key:
            logger.warning("Encryption key not found in environment variable, generating a new key.")
            self.key = Fernet.generate_key()
        
        # Ensure the key is base64 encoded
        try:
            self.cipher = Fernet(base64.urlsafe_b64encode(self.key.ljust(32)[:32]))
        except Exception as e:
            logger.error(f"Error initializing Fernet cipher: {str(e)}")
            raise

    def encrypt(self, data: str) -> str:
        """Encrypt data using Fernet"""
        try:
            encrypted_data = self.cipher.encrypt(data.encode()).decode()
            return encrypted_data
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet"""
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data.encode()).decode()
            return decrypted_data
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            raise