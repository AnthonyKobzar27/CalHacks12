#!/usr/bin/env python3
"""
Audio Setup Detection for B1 Robot
This script helps identify available audio devices on the robot
"""

import pyaudio
import subprocess
import os

def detect_audio_devices():
    """Detect all available audio devices"""
    print("=== Audio Device Detection ===")
    
    # PyAudio device detection
    p = pyaudio.PyAudio()
    print(f"PyAudio found {p.get_device_count()} audio devices:")
    
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"  Device {i}: {info['name']}")
        print(f"    - Input channels: {info['maxInputChannels']}")
        print(f"    - Output channels: {info['maxOutputChannels']}")
        print(f"    - Default sample rate: {info['defaultSampleRate']}")
        print()
    
    p.terminate()

def detect_alsa_devices():
    """Detect ALSA audio devices"""
    print("=== ALSA Device Detection ===")
    
    try:
        # List ALSA devices
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        print("ALSA Playback devices:")
        print(result.stdout)
        
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        print("ALSA Recording devices:")
        print(result.stdout)
        
    except FileNotFoundError:
        print("ALSA tools not found")

def detect_pulseaudio():
    """Detect PulseAudio devices"""
    print("=== PulseAudio Device Detection ===")
    
    try:
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], capture_output=True, text=True)
        print("PulseAudio sinks (output devices):")
        print(result.stdout)
        
        result = subprocess.run(['pactl', 'list', 'short', 'sources'], capture_output=True, text=True)
        print("PulseAudio sources (input devices):")
        print(result.stdout)
        
    except FileNotFoundError:
        print("PulseAudio not found or not running")

def test_audio_output():
    """Test audio output to different devices"""
    print("=== Audio Output Test ===")
    
    p = pyaudio.PyAudio()
    
    # Find output devices
    output_devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxOutputChannels'] > 0:
            output_devices.append((i, info['name']))
    
    print(f"Found {len(output_devices)} output devices:")
    for device_id, name in output_devices:
        print(f"  {device_id}: {name}")
    
    # Test each output device
    for device_id, name in output_devices:
        print(f"\nTesting device {device_id}: {name}")
        try:
            # Generate a simple tone
            import numpy as np
            import wave
            
            sample_rate = 44100
            duration = 1  # 1 second
            frequency = 440  # A note
            
            # Generate sine wave
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            wave_data = np.sin(frequency * 2 * np.pi * t)
            wave_data = (wave_data * 32767).astype(np.int16)
            
            # Try to play through this device
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                output=True,
                output_device_index=device_id
            )
            
            print(f"  ✓ Successfully opened device {device_id}")
            stream.close()
            
        except Exception as e:
            print(f"  ✗ Failed to open device {device_id}: {e}")
    
    p.terminate()

def test_audio_input():
    """Test audio input from different devices"""
    print("=== Audio Input Test ===")
    
    p = pyaudio.PyAudio()
    
    # Find input devices
    input_devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            input_devices.append((i, info['name']))
    
    print(f"Found {len(input_devices)} input devices:")
    for device_id, name in input_devices:
        print(f"  {device_id}: {name}")
    
    # Test each input device
    for device_id, name in input_devices:
        print(f"\nTesting input device {device_id}: {name}")
        try:
            # Try to open this device for input
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                input_device_index=device_id,
                frames_per_buffer=1024
            )
            
            print(f"  ✓ Successfully opened input device {device_id}")
            stream.close()
            
        except Exception as e:
            print(f"  ✗ Failed to open input device {device_id}: {e}")
    
    p.terminate()

def main():
    print("B1 Robot Audio Setup Detection")
    print("=" * 40)
    
    # Create output file
    output_file = "audio_devices_report.txt"
    
    with open(output_file, 'w') as f:
        # Redirect print to both console and file
        import sys
        from contextlib import redirect_stdout
        
        class Tee:
            def __init__(self, *files):
                self.files = files
            def write(self, obj):
                for f in self.files:
                    f.write(obj)
                    f.flush()
            def flush(self):
                for f in self.files:
                    f.flush()
        
        original_stdout = sys.stdout
        sys.stdout = Tee(sys.stdout, f)
        
        try:
            print("B1 Robot Audio Setup Detection")
            print("=" * 40)
            print()
            
            # Audio device detection
            detect_audio_devices()
            print()
            
            # ALSA detection
            detect_alsa_devices()
            print()
            
            # PulseAudio detection
            detect_pulseaudio()
            print()
            
            # Test audio output
            test_audio_output()
            print()
            
            # Test audio input
            test_audio_input()
            print()
            
            print("=== Recommendations ===")
            print("1. Look for devices with 'robot', 'speaker', 'output' in the name")
            print("2. Test each output device to see which produces sound")
            print("3. Note the device index for the robot's speakers")
            print("4. Note the device index for the robot's microphone")
            print("5. Use those device indices in your voice agent")
            
        finally:
            sys.stdout = original_stdout
    
    print(f"\nAudio detection complete! Report saved to: {output_file}")
    print("Please copy the contents of this file and share it.")

if __name__ == "__main__":
    main()
