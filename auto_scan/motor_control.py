"""
Arduino Motor Control Interface
Controls XY stage and scanner motors via serial communication
"""

import serial
import time


class MotorController:
    def __init__(self, port='/dev/ttyUSB0', baudrate=2000000):
        """
        Initialize connection to Arduino
        
        Args:
            port: Serial port (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux/Mac)
            baudrate: Must match Arduino (2000000)
        """
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            print(f"Connected to Arduino on {port}")
            
            # Read initial messages
            for _ in range(5):
                if self.ser.in_waiting:
                    print(self.ser.readline().decode().strip())
        except Exception as e:
            print(f"Error connecting to Arduino: {e}")
            print("\nTroubleshooting:")
            print("- Check if Arduino is plugged in")
            print("- Find correct port:")
            print("  Windows: Check Device Manager (COM3, COM4, etc.)")
            print("  Mac: ls /dev/tty.* or /dev/cu.*")
            print("  Linux: ls /dev/ttyUSB* or /dev/ttyACM*")
            raise
    
    def send_command(self, stepper, angle):
        """
        Send movement command to Arduino
        
        Args:
            stepper: 'A', 'B', 'C', or 'D'
            angle: Degrees to rotate (positive or negative)
        """
        command = f"stepper{stepper} {angle}\n"
        self.ser.write(command.encode())
        time.sleep(0.1)  # Wait for command to process
        
        # Read response
        if self.ser.in_waiting:
            response = self.ser.readline().decode().strip()
            print(response)
            return response
        return None
    
    #Changed - Javier 
    def move_x(self, step=1, speed=100):
        if self.ser:
            command = f'stepperA {step}\n'.encode()
            self.ser.write(command)
            self.absolute_x += step  # Fixed: was missing 'self.'

    
    def move_y(self, step=1, speed=100):
        if self.ser:
            command = f'stepperB {step}\n'.encode()
            self.ser.write(command)
            self.absolute_y += step  # Fixed: was missing 'self.'
    
    def move_z(self, step=1, speed=100):
        if self.ser:
            command = f'stepperC {step}\n'.encode()
            self.ser.write(command)
            self.absolute_z += step  # Fixed: was missing 'self.'
    
    def rotate(self, degrees):
        """Rotate (Stepper D)"""
        return self.send_command('D', degrees)
    
    def move_to_position(self, x=0, y=0):
        """
        Move to absolute position
        Note: You'll need to track current position separately
        """
        if x != 0:
            self.move_x(x)
            time.sleep(0.5)
        if y != 0:
            self.move_y(y)
            time.sleep(0.5)
    
    def grid_scan(self, x_steps, y_steps, step_size_degrees):
        """
        Perform grid scan pattern
        
        Args:
            x_steps: Number of steps in X direction
            y_steps: Number of steps in Y direction  
            step_size_degrees: Degrees per step
        """
        positions = []
        
        for y in range(y_steps):
            for x in range(x_steps):
                # Move to position
                if x > 0:
                    self.move_x(step_size_degrees)
                
                # Record position
                positions.append((x, y))
                print(f"Position: ({x}, {y})")
                
                # Here you would capture image
                yield (x, y)  # Return position for image capture
            
            # Move to next row
            if y < y_steps - 1:
                self.move_y(step_size_degrees)
                # Return to start of row
                self.move_x(-step_size_degrees * x_steps)
    
    def home(self):
        """
        Return to home position (0,0)
        Note: This is a simple version - you may need limit switches for true homing
        """
        print("Homing - this is approximate without limit switches!")
        # Move large negative to reach approximate home
        self.move_x(-360 * 10)  # Move far left
        self.move_y(-360 * 10)  # Move far back
    
    def close(self):
        """Close serial connection"""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
            print("Disconnected from Arduino")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Find available serial ports
def find_arduino_port():
    """Helper function to find Arduino port"""
    import serial.tools.list_ports
    
    ports = serial.tools.list_ports.comports()
    print("\nAvailable serial ports:")
    for i, port in enumerate(ports):
        print(f"{i}: {port.device} - {port.description}")
    
    if not ports:
        print("No serial ports found!")
        return None
    
    # Try to find Arduino
    for port in ports:
        if 'Arduino' in port.description or 'USB' in port.description:
            return port.device
    
    return ports[0].device if ports else None


# Example usage
if __name__ == "__main__":
    print("=== Motor Controller Test ===\n")
    
    # Find port automatically
    port = find_arduino_port()
    
    if port:
        print(f"\nUsing port: {port}")
        controller = MotorController(port=port, baudrate=2000000)
        
        # Test movements
        print("\n--- Testing X-axis ---")
        controller.move_x(90)
        time.sleep(1)
        controller.move_x(-90)
        
        print("\n--- Testing Y-axis ---")
        controller.move_y(45)
        time.sleep(1)
        controller.move_y(-45)
        
        print("\n--- Test complete ---")
        controller.close()
    else:
        print("\nPlease specify your Arduino port manually:")
        print("controller = MotorController(port='COM3', baudrate=2000000)  # Windows")
        print("controller = MotorController(port='/dev/ttyUSB0', baudrate=2000000)  # Linux")
        print("controller = MotorController(port='/dev/cu.usbserial-*', baudrate=2000000)  # Mac")