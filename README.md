# Arduino Nano + TB6600 Stepper Motor Driver Wiring Guide

## Circuit Diagram Description

Create a wiring diagram showing the connections between an Arduino Nano, a TB6600 stepper motor driver, a Nema 17 stepper motor, and a 12V power supply.

## Components Required

1. Arduino Nano (on a breadboard)
2. TB6600 Microstepping Driver (black box with green terminal blocks)
3. Nema 17 Stepper Motor - StepperOnline Model 17HE08-1004S (bipolar, 4-wire)
4. 12V DC Power Supply (barrel jack connector)

## Wiring Connections

### Arduino Nano to TB6600 Driver

- Arduino **D2** pin → TB6600 **DIR+** terminal
- Arduino **D3** pin → TB6600 **PUL+** terminal
- Arduino **GND** pin → TB6600 **PUL-** terminal ⚠️ **CRITICAL CONNECTION**

### 12V Power Supply to TB6600 Driver

- 12V Power Supply **positive (+)** → TB6600 **VCC** (or DC+) terminal
- 12V Power Supply **negative (-)** → TB6600 **GND** (or DC-) terminal

### Nema 17 Motor to TB6600 Driver

Based on motor datasheet bipolar configuration:

- Motor **BLACK** wire (Pin 1) → TB6600 **A+** terminal
- Motor **BLUE** wire (Pin 3) → TB6600 **A-** terminal
- Motor **RED** wire (Pins 2 & 4) → TB6600 **B+** terminal
- Motor **GREEN** wire (Pin 6) → TB6600 **B-** terminal

## Motor Specifications

- **Model:** 17HE08-1004S
- **Type:** Bipolar stepper motor
- **Phase Resistance:** 3.60Ω ±10%
- **Operating Voltage:** 9-32V DC
- **Winding Resistance:** 1.00 Ohm

## Configuration Notes

- Arduino Nano is powered via USB cable connected to a computer
- TB6600 driver DIP switches should be set to **UP/OFF** position (full-step mode)
- The **GND connection from Arduino to PUL-** is essential for communication
- Motor operates at 12V from the driver's power supply

## Important

> ⚠️ **The Arduino GND to TB6600 PUL- connection is CRITICAL.** Without this common ground, the Arduino cannot communicate with the driver and the motor will not move, even though it may heat up.

## Troubleshooting

If motor doesn't move:
1. Verify Arduino GND is connected to driver PUL-
2. Check all DIP switches are UP (OFF)
3. Adjust current potentiometer on driver clockwise slightly
4. Verify 12V power supply is connected and powered on
