"""
Microscope Camera Interface
Captures images from USB camera or other imaging devices
"""

import cv2
import numpy as np
from datetime import datetime
import os


class MicroscopeCamera:
    def __init__(self, camera_index=0, save_dir="captured_images"):
        """
        Initialize camera
        
        Args:
            camera_index: Camera device index (0 for default, 1, 2, etc. if multiple cameras)
            save_dir: Directory to save captured images
        """
        self.camera_index = camera_index
        self.save_dir = save_dir
        
        # Create save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Open camera
        self.cap = cv2.VideoCapture(camera_index)
        
        if not self.cap.isOpened():
            raise Exception(f"Cannot open camera {camera_index}")
        
        # Set camera properties (adjust these based on your camera)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)  # Width
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  # Height
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable autofocus
        
        print(f"Camera {camera_index} initialized")
        print(f"Resolution: {self.get_resolution()}")
        print(f"Images will be saved to: {save_dir}/")
    
    def get_resolution(self):
        """Get current camera resolution"""
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)
    
    def capture_frame(self):
        """Capture a single frame"""
        ret, frame = self.cap.read()
        if not ret:
            print("Error: Failed to capture frame")
            return None
        return frame
    
    def preview(self, window_name="Microscope Preview"):
        """
        Show live preview
        Press 'c' to capture, 'q' to quit
        """
        print("\nPreview Controls:")
        print("  'c' - Capture image")
        print("  'q' - Quit preview")
        print("  '+' - Increase exposure (if supported)")
        print("  '-' - Decrease exposure (if supported)")
        
        while True:
            frame = self.capture_frame()
            if frame is None:
                break
            
            # Add instructions to frame
            cv2.putText(frame, "Press 'c' to capture, 'q' to quit", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow(window_name, frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('c'):
                filename = self.save_image(frame)
                print(f"Image saved: {filename}")
                cv2.putText(frame, "CAPTURED!", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                cv2.imshow(window_name, frame)
                cv2.waitKey(500)  # Show "CAPTURED!" for 0.5 seconds
            elif key == ord('+'):
                # Increase exposure
                current = self.cap.get(cv2.CAP_PROP_EXPOSURE)
                self.cap.set(cv2.CAP_PROP_EXPOSURE, current + 1)
                print(f"Exposure: {current + 1}")
            elif key == ord('-'):
                # Decrease exposure
                current = self.cap.get(cv2.CAP_PROP_EXPOSURE)
                self.cap.set(cv2.CAP_PROP_EXPOSURE, current - 1)
                print(f"Exposure: {current - 1}")
        
        cv2.destroyAllWindows()
    
    def save_image(self, frame=None, prefix="flake"):
        """
        Save image with timestamp
        
        Args:
            frame: Image to save (if None, captures new frame)
            prefix: Filename prefix
        
        Returns:
            Filename of saved image
        """
        if frame is None:
            frame = self.capture_frame()
        
        if frame is None:
            return None
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.jpg"
        filepath = os.path.join(self.save_dir, filename)
        
        # Save image
        cv2.imwrite(filepath, frame)
        return filepath
    
    def capture_with_position(self, x, y, prefix="scan"):
        """
        Capture image at specific XY position
        
        Args:
            x, y: Position coordinates
            prefix: Filename prefix
        """
        frame = self.capture_frame()
        if frame is None:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_x{x}_y{y}_{timestamp}.jpg"
        filepath = os.path.join(self.save_dir, filename)
        
        cv2.imwrite(filepath, frame)
        print(f"Saved: {filename}")
        return filepath
    
    def set_focus(self, value):
        """
        Set manual focus (if camera supports it)
        
        Args:
            value: Focus value (camera-dependent, typically 0-255)
        """
        self.cap.set(cv2.CAP_PROP_FOCUS, value)
    
    def set_exposure(self, value):
        """
        Set exposure
        
        Args:
            value: Exposure value (camera-dependent)
        """
        self.cap.set(cv2.CAP_PROP_EXPOSURE, value)
    
    def get_camera_info(self):
        """Print camera properties"""
        print("\n=== Camera Properties ===")
        properties = {
            'Width': cv2.CAP_PROP_FRAME_WIDTH,
            'Height': cv2.CAP_PROP_FRAME_HEIGHT,
            'FPS': cv2.CAP_PROP_FPS,
            'Brightness': cv2.CAP_PROP_BRIGHTNESS,
            'Contrast': cv2.CAP_PROP_CONTRAST,
            'Saturation': cv2.CAP_PROP_SATURATION,
            'Exposure': cv2.CAP_PROP_EXPOSURE,
            'Focus': cv2.CAP_PROP_FOCUS,
        }
        
        for name, prop in properties.items():
            value = self.cap.get(prop)
            print(f"{name}: {value}")
    
    def close(self):
        """Release camera"""
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
            cv2.destroyAllWindows()
            print("Camera released")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Find available cameras
def find_cameras(max_test=5):
    """Test and find available cameras"""
    print("\nScanning for cameras...")
    available_cameras = []
    
    for i in range(max_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                available_cameras.append({
                    'index': i,
                    'resolution': (width, height)
                })
                print(f"Camera {i}: {width}x{height}")
            cap.release()
    
    if not available_cameras:
        print("No cameras found!")
    
    return available_cameras


# Example usage
if __name__ == "__main__":
    print("=== Microscope Camera Test ===\n")
    
    # Find available cameras
    cameras = find_cameras()
    
    if cameras:
        # Use first camera
        camera_index = cameras[0]['index']
        print(f"\nUsing camera {camera_index}")
        
        cam = MicroscopeCamera(camera_index=camera_index)
        cam.get_camera_info()
        
        print("\nStarting preview...")
        cam.preview()
        
        cam.close()
    else:
        print("\nNo cameras detected!")
        print("Make sure your microscope camera is connected")