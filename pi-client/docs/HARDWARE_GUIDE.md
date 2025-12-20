# Hardware Integration Guide

This guide provides examples for integrating various hardware components with the Pi Client.

## GPIO Integration

### Basic Setup

```python
from pi_client.hardware.gpio import GPIOInterface, PinMode

# Initialize GPIO
gpio = GPIOInterface(enabled=True)

# Setup pin as output
gpio.setup_pin(18, PinMode.OUTPUT)

# Control LED
gpio.control_led(18, True)  # Turn on
gpio.control_led(18, False)  # Turn off
```

### Reading Sensors

```python
# Read temperature sensor (example)
temperature = gpio.read_sensor("temperature", pin=4)
if temperature:
    print(f"Temperature: {temperature}°C")
```

### Button Input

```python
# Setup button on pin 16
gpio.setup_pin(16, PinMode.INPUT)

# Read button state
button_pressed = gpio.read_button(16)
if button_pressed:
    print("Button pressed!")
```

### Cleanup

```python
# Always cleanup GPIO when done
gpio.cleanup()
```

## Camera Integration

### Photo Capture

```python
from pi_client.hardware.camera import CameraInterface

# Initialize camera
camera = CameraInterface(enabled=True)

# Capture photo
photo_path = camera.capture_photo(
    output_path="/tmp/photo.jpg",
    resolution=(1920, 1080),
    quality=85
)

if photo_path:
    print(f"Photo saved to {photo_path}")
```

### Video Recording

```python
# Start recording
camera.start_video_recording(
    output_path="/tmp/video.h264",
    resolution=(1280, 720),
    framerate=30
)

# ... do something ...

# Stop recording
video_path = camera.stop_video_recording()
```

### Timelapse

```python
# Capture timelapse (5 second intervals, 60 seconds total)
frames = camera.capture_timelapse(
    output_dir="/tmp/timelapse",
    interval=5,
    duration=60,
    resolution=(1920, 1080)
)

print(f"Captured {len(frames)} frames")
```

## Audio Management

### Playback

```python
from pi_client.hardware.audio import AudioManager

# Initialize audio
audio = AudioManager(enabled=True)

# Play audio file
audio.play_file(
    "/path/to/audio.mp3",
    volume=0.8,
    loop=False
)

# Control playback
audio.pause()
audio.resume()
audio.stop()
```

### Volume Control

```python
# Set volume (0.0 to 1.0)
audio.set_volume(0.5)

# Get current volume
current_volume = audio.get_volume()
print(f"Current volume: {current_volume}")
```

## Power Management

### Battery Monitoring

```python
from pi_client.hardware.power import PowerManager

# Initialize power manager
power = PowerManager()

# Get battery level
battery_level = power.get_battery_level()
if battery_level:
    print(f"Battery: {battery_level}%")

# Check charging status
is_charging = power.is_charging()
is_ac_connected = power.is_ac_connected()

# Get comprehensive power info
power_info = power.get_power_info()
print(power_info)
```

### Power Optimization

```python
# Optimize for battery operation
if power.get_battery_level() < 50:
    power.optimize_for_battery()

# Optimize for performance (when on AC)
if power.is_ac_connected():
    power.optimize_for_performance()

# Check if device should sleep
if power.should_sleep():
    print("Device should enter sleep mode")
```

## Complete Example

```python
import asyncio
from pi_client.hardware.gpio import GPIOInterface, PinMode
from pi_client.hardware.camera import CameraInterface
from pi_client.hardware.audio import AudioManager
from pi_client.hardware.power import PowerManager

async def main():
    # Initialize hardware
    gpio = GPIOInterface()
    camera = CameraInterface()
    audio = AudioManager()
    power = PowerManager()
    
    # Setup GPIO
    gpio.setup_pin(18, PinMode.OUTPUT)  # LED
    gpio.setup_pin(16, PinMode.INPUT)  # Button
    
    # Check power
    if power.should_sleep():
        print("Low battery, entering sleep mode")
        return
    
    # Main loop
    while True:
        # Check button
        if gpio.read_button(16):
            # Capture photo
            photo = camera.capture_photo()
            if photo:
                print(f"Photo captured: {photo}")
            
            # Play sound
            audio.play_file("/path/to/beep.mp3")
        
        # Blink LED
        gpio.control_led(18, True)
        await asyncio.sleep(0.5)
        gpio.control_led(18, False)
        await asyncio.sleep(0.5)
    
    # Cleanup
    gpio.cleanup()
    camera.cleanup()
    audio.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## Hardware Requirements

### GPIO
- Raspberry Pi with GPIO pins
- Optional: `RPi.GPIO` or `gpiozero` library

### Camera
- Raspberry Pi Camera Module
- `picamera2` library

### Audio
- Audio output device (HDMI, 3.5mm jack, or USB)
- Optional: `pygame` library for advanced features

### Power
- Battery monitoring requires compatible hardware
- AC detection requires power supply with status reporting

## Troubleshooting

### GPIO not working
- Check if running on Raspberry Pi
- Verify GPIO libraries are installed
- Check pin numbers (BCM vs BOARD mode)

### Camera not detected
- Verify camera is connected
- Check camera is enabled in `raspi-config`
- Ensure `picamera2` is installed

### Audio not playing
- Check audio output device
- Verify ALSA/PulseAudio is configured
- Test with system `aplay` command



