#!/usr/bin/env python3
"""
Microphone test script to verify input is working
Shows real-time audio levels in terminal
"""

import pyaudio
import numpy as np
import time
import sys
import signal
import threading

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono
RATE = 44100
DURATION = 30  # seconds (or until Ctrl+C)

class MicrophoneTest:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False
        self.volume_history = []
        
    def signal_handler(self, sig, frame):
        print('\n⚠️  Microphone test interrupted by user (Ctrl+C)')
        self.is_running = False
        sys.exit(0)
    
    def list_input_devices(self):
        """List all available input devices"""
        print("🎤 Available input devices:")
        print("=" * 50)
        
        input_devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append((i, info))
                print(f"  Device {i}: {info['name']}")
                print(f"    Channels: {info['maxInputChannels']}")
                print(f"    Default Rate: {info['defaultSampleRate']}")
                print()
        
        return input_devices
    
    def test_device(self, device_index):
        """Test a specific input device"""
        try:
            device_info = self.audio.get_device_info_by_index(device_index)
            print(f"🎤 Testing device {device_index}: {device_info['name']}")
            print(f"   Max Input Channels: {device_info['maxInputChannels']}")
            print(f"   Default Sample Rate: {device_info['defaultSampleRate']}")
            
            # Use device's max channels (but cap at 1 for simplicity)
            channels = min(1, device_info['maxInputChannels'])
            
            # Try different sample rates
            for rate in [44100, 48000, 24000, 16000]:
                try:
                    stream = self.audio.open(
                        format=FORMAT,
                        channels=channels,
                        rate=rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=CHUNK
                    )
                    stream.close()
                    print(f"   ✅ Works at {rate}Hz")
                    return rate
                except Exception as e:
                    print(f"   ❌ Failed at {rate}Hz: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ Error testing device {device_index}: {e}")
            return None
    
    def start_monitoring(self, device_index=None, sample_rate=44100):
        """Start real-time audio monitoring"""
        print(f"\n🎤 Starting microphone monitoring...")
        print(f"   Device: {device_index if device_index is not None else 'Default'}")
        print(f"   Sample Rate: {sample_rate}Hz")
        print(f"   Duration: {DURATION} seconds (or Ctrl+C to stop)")
        print("\n📊 Audio Level Monitor:")
        print("   Level: ████████████████████ (0-100)")
        print("   Speak into the microphone to see levels change!")
        print("   " + "="*50)
        
        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK
            )
            
            self.is_running = True
            start_time = time.time()
            
            while self.is_running:
                try:
                    # Read audio data
                    data = self.stream.read(CHUNK, exception_on_overflow=False)
                    
                    # Convert to numpy array
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    
                    # Calculate volume (RMS)
                    volume = np.sqrt(np.mean(audio_data**2))
                    
                    # Normalize to 0-100 scale
                    normalized_volume = min(100, (volume / 32767) * 100)
                    
                    # Add to history for smoothing
                    self.volume_history.append(normalized_volume)
                    if len(self.volume_history) > 10:
                        self.volume_history.pop(0)
                    
                    # Calculate smoothed volume
                    smoothed_volume = np.mean(self.volume_history)
                    
                    # Create visual bar
                    bar_length = int(smoothed_volume / 5)  # 20 chars max
                    bar = "█" * bar_length + "░" * (20 - bar_length)
                    
                    # Show level
                    print(f"\r   Level: {bar} ({smoothed_volume:5.1f})", end="", flush=True)
                    
                    # Check for timeout
                    if time.time() - start_time > DURATION:
                        break
                        
                except Exception as e:
                    if "Input overflowed" in str(e):
                        continue
                    else:
                        print(f"\n❌ Error reading audio: {e}")
                        break
            
            print(f"\n\n✅ Monitoring completed!")
            
        except Exception as e:
            print(f"\n❌ Error starting monitoring: {e}")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.is_running = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        self.audio.terminate()
        print("🧹 Cleaned up audio resources")
    
    def run_interactive_test(self):
        """Run interactive microphone test"""
        print("🎤 Microphone Test Script")
        print("=" * 50)
        
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # List devices
        input_devices = self.list_input_devices()
        
        if not input_devices:
            print("❌ No input devices found!")
            return
        
        # Test each device
        print("🔍 Testing devices...")
        working_devices = []
        
        for device_index, device_info in input_devices:
            rate = self.test_device(device_index)
            if rate:
                working_devices.append((device_index, device_info, rate))
        
        if not working_devices:
            print("❌ No working input devices found!")
            return
        
        # Let user choose device
        print(f"\n✅ Found {len(working_devices)} working device(s):")
        for i, (device_index, device_info, rate) in enumerate(working_devices):
            print(f"  {i+1}. Device {device_index}: {device_info['name']} ({rate}Hz)")
        
        if len(working_devices) == 1:
            device_index, device_info, rate = working_devices[0]
            print(f"\n🎤 Using the only working device: {device_info['name']}")
        else:
            try:
                choice = input(f"\nChoose device (1-{len(working_devices)}): ")
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(working_devices):
                    device_index, device_info, rate = working_devices[choice_idx]
                    print(f"🎤 Selected: {device_info['name']}")
                else:
                    print("❌ Invalid choice, using first device")
                    device_index, device_info, rate = working_devices[0]
            except (ValueError, KeyboardInterrupt):
                print("❌ Invalid input, using first device")
                device_index, device_info, rate = working_devices[0]
        
        # Start monitoring
        self.start_monitoring(device_index, rate)

def main():
    if len(sys.argv) > 1:
        # Test specific device
        try:
            device_index = int(sys.argv[1])
            test = MicrophoneTest()
            test.signal_handler = lambda sig, frame: test.signal_handler(sig, frame)
            signal.signal(signal.SIGINT, test.signal_handler)
            
            print(f"🎤 Testing device {device_index}")
            rate = test.test_device(device_index)
            if rate:
                test.start_monitoring(device_index, rate)
            else:
                print("❌ Device test failed")
        except ValueError:
            print("❌ Invalid device index. Use: python test_microphone.py [device_index]")
    else:
        # Interactive test
        test = MicrophoneTest()
        test.run_interactive_test()

if __name__ == "__main__":
    main()
