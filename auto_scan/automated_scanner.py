"""
Integrated Automated Scanning System
Combines motor control + camera capture for automated flake scanning
"""

import time
import cv2
import os
from motor_control import MotorController, find_arduino_port
from camera_control import MicroscopeCamera, find_cameras


class AutomatedScanner:
    def __init__(self, arduino_port=None, camera_index=0, save_dir="scanned_images"):
        """
        Initialize automated scanner
        
        Args:
            arduino_port: Serial port for Arduino (auto-detected if None)
            camera_index: Camera device index
            save_dir: Directory to save images
        """
        print("=== Initializing Automated Scanner ===\n")
        
        # Initialize motors
        if arduino_port is None:
            arduino_port = find_arduino_port()
        
        self.motors = MotorController(port=arduino_port, baudrate=2000000)
        print("✓ Motors initialized\n")
        
        # Initialize camera
        self.camera = MicroscopeCamera(camera_index=camera_index, save_dir=save_dir)
        print("✓ Camera initialized\n")
        
        # Current position tracking
        self.current_x = 0
        self.current_y = 0
        
        print("=== Scanner Ready ===\n")
    
    def manual_mode(self):
        """
        Manual control mode with live preview
        
        Controls:
            Arrow Keys: Move XY stage
            W/S: Move Z (focus)
            A/D: Rotate
            C: Capture image
            Q: Quit
        """
        print("\n=== Manual Control Mode ===")
        print("Controls:")
        print("  Arrow Keys - Move XY stage (step size: 10°)")
        print("  W/S - Adjust focus (Stepper C)")
        print("  A/D - Rotate (Stepper D)")
        print("  C - Capture image")
        print("  H - Return to home")
        print("  Q - Quit manual mode")
        print("\nStarting preview...\n")
        
        step_size = 10  # degrees
        
        while True:
            frame = self.camera.capture_frame()
            if frame is None:
                break
            
            # Add position info to frame
            info_text = f"Position: X={self.current_x}, Y={self.current_y} | Press Q to quit"
            cv2.putText(frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.imshow("Manual Control", frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('c'):
                # Capture image
                filename = self.camera.save_image(frame)
                print(f"Captured: {filename}")
            elif key == 82:  # Up arrow
                print("Moving Y+")
                self.motors.move_y(step_size)
                self.current_y += step_size
            elif key == 84:  # Down arrow
                print("Moving Y-")
                self.motors.move_y(-step_size)
                self.current_y -= step_size
            elif key == 81:  # Left arrow
                print("Moving X-")
                self.motors.move_x(-step_size)
                self.current_x -= step_size
            elif key == 83:  # Right arrow
                print("Moving X+")
                self.motors.move_x(step_size)
                self.current_x += step_size
            elif key == ord('w'):
                print("Focus up")
                self.motors.move_z(5)
            elif key == ord('s'):
                print("Focus down")
                self.motors.move_z(-5)
            elif key == ord('a'):
                print("Rotate CCW")
                self.motors.rotate(-10)
            elif key == ord('d'):
                print("Rotate CW")
                self.motors.rotate(10)
            elif key == ord('h'):
                print("Returning to home...")
                self.motors.home()
                self.current_x = 0
                self.current_y = 0
        
        cv2.destroyAllWindows()
    
    def grid_scan(self, x_steps=5, y_steps=5, step_size=45, delay=1.0):
        """
        Automated grid scan
        
        Args:
            x_steps: Number of steps in X direction
            y_steps: Number of steps in Y direction
            step_size: Degrees per step
            delay: Delay between movements (seconds)
        """
        print(f"\n=== Starting Grid Scan ===")
        print(f"Grid: {x_steps} x {y_steps}")
        print(f"Step size: {step_size}°")
        print(f"Total images: {x_steps * y_steps}\n")
        
        image_count = 0
        
        for y in range(y_steps):
            for x in range(x_steps):
                # Move X
                if x > 0:
                    print(f"Moving X: +{step_size}°")
                    self.motors.move_x(step_size)
                    time.sleep(delay)
                
                # Update position
                self.current_x = x * step_size
                self.current_y = y * step_size
                
                # Capture image
                print(f"Capturing at ({x}, {y})...")
                self.camera.capture_with_position(x, y, prefix="grid_scan")
                image_count += 1
                
                # Show progress
                print(f"Progress: {image_count}/{x_steps * y_steps}\n")
            
            # Move to next row
            if y < y_steps - 1:
                print(f"Moving Y: +{step_size}°")
                self.motors.move_y(step_size)
                time.sleep(delay)
                
                # Return to start of row
                print(f"Returning to X start...")
                self.motors.move_x(-step_size * x_steps)
                time.sleep(delay)
        
        print(f"\n=== Scan Complete ===")
        print(f"Total images captured: {image_count}")
        print(f"Images saved to: {self.camera.save_dir}/")
    
    def find_and_capture(self, show_preview=True):
        """
        Interactive mode: manually navigate and mark positions
        
        Controls:
            Arrow keys: Navigate
            SPACE: Mark current position and capture
            ESC: Finish and save positions
        """
        print("\n=== Find and Capture Mode ===")
        print("Navigate to interesting areas and press SPACE to capture")
        print("Press ESC when done\n")
        
        marked_positions = []
        
        while True:
            frame = self.camera.capture_frame()
            if frame is None:
                break
            
            # Add overlay
            info = f"Position: ({self.current_x}, {self.current_y}) | " \
                   f"Marked: {len(marked_positions)} | SPACE=Capture, ESC=Done"
            cv2.putText(frame, info, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.imshow("Find and Capture", frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                break
            elif key == 32:  # SPACE
                # Capture at current position
                pos = (self.current_x, self.current_y)
                marked_positions.append(pos)
                filename = self.camera.capture_with_position(*pos, prefix="marked")
                print(f"Marked position {len(marked_positions)}: {pos}")
                print(f"Saved: {filename}\n")
            elif key == 82:  # Up
                self.motors.move_y(10)
                self.current_y += 10
            elif key == 84:  # Down
                self.motors.move_y(-10)
                self.current_y -= 10
            elif key == 81:  # Left
                self.motors.move_x(-10)
                self.current_x -= 10
            elif key == 83:  # Right
                self.motors.move_x(10)
                self.current_x += 10
        
        cv2.destroyAllWindows()
        
        print(f"\nMarked {len(marked_positions)} positions:")
        for i, pos in enumerate(marked_positions, 1):
            print(f"  {i}. X={pos[0]}, Y={pos[1]}")
        
        return marked_positions
    
    def return_home(self):
        """Return to home position"""
        print("Returning to home position...")
        self.motors.home()
        self.current_x = 0
        self.current_y = 0
        print("At home position")
    
    def close(self):
        """Close scanner and release resources"""
        print("\nShutting down scanner...")
        self.camera.close()
        self.motors.close()
        print("Scanner closed")
    
    def __del__(self):
        """Cleanup"""
        self.close()


# Main menu
def main_menu():
    """Interactive menu for scanner"""
    print("\n" + "="*50)
    print("  AUTOMATED FLAKE SCANNER")
    print("="*50)
    
    # Initialize scanner
    scanner = AutomatedScanner()
    
    while True:
        print("\n=== Main Menu ===")
        print("1. Manual Control Mode")
        print("2. Automated Grid Scan")
        print("3. Find and Capture Mode")
        print("4. Return to Home")
        print("5. Test Camera")
        print("6. Test Motors")
        print("0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            scanner.manual_mode()
        
        elif choice == '2':
            print("\nGrid Scan Configuration:")
            x_steps = int(input("X steps (default 5): ") or "5")
            y_steps = int(input("Y steps (default 5): ") or "5")
            step_size = int(input("Step size in degrees (default 45): ") or "45")
            
            confirm = input(f"\nScan {x_steps}x{y_steps} grid? (y/n): ")
            if confirm.lower() == 'y':
                scanner.grid_scan(x_steps, y_steps, step_size)
        
        elif choice == '3':
            positions = scanner.find_and_capture()
            print(f"\nCaptured {len(positions)} positions")
        
        elif choice == '4':
            scanner.return_home()
        
        elif choice == '5':
            scanner.camera.preview()
        
        elif choice == '6':
            print("\nTesting motors...")
            scanner.motors.move_x(90)
            time.sleep(1)
            scanner.motors.move_x(-90)
            print("Motor test complete")
        
        elif choice == '0':
            scanner.close()
            print("\nGoodbye!")
            break
        
        else:
            print("Invalid option")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()