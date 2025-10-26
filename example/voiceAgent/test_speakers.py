#!/usr/bin/env python3
"""
Simple audio test script to verify speakers are working
"""

import pyaudio
import numpy as np
import time
import sys
import signal

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono
RATE = 44100
DURATION = 5  # seconds

def signal_handler(sig, frame):
    print('\n⚠️  Test interrupted by user (Ctrl+C)')
    sys.exit(0)

def test_speakers():
    """Test speaker output with a simple tone"""
    print("🔊 Speaker Test Script")
    print("=" * 40)
    
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize PyAudio
    audio = pyaudio.PyAudio()
    
    try:
        # List available output devices
        print("📋 Available output devices:")
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                print(f"  Device {i}: {info['name']} (Channels: {info['maxOutputChannels']})")
        
        print(f"\n🎵 Testing audio output...")
        print(f"   Sample Rate: {RATE}Hz")
        print(f"   Channels: {CHANNELS}")
        print(f"   Duration: {DURATION} seconds")
        print(f"   Press Ctrl+C to stop early\n")
        
        # Try different sample rates (OpenAI needs 24kHz, but test what works)
        for test_rate in [24000, 44100, 48000]:
            try:
                stream = audio.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=test_rate,
                    output=True,
                    frames_per_buffer=CHUNK
                )
                print(f"✅ Using sample rate: {test_rate}Hz")
                RATE = test_rate  # Update the rate for the rest of the function
                break
            except Exception as e:
                print(f"❌ Failed at {test_rate}Hz: {e}")
                continue
        else:
            raise Exception("No working sample rate found")
        
        print("✅ Audio stream opened successfully!")
        print("🔊 Playing test tone...")
        
        # Generate a simple sine wave tone (440Hz - A note)
        frequency = 440
        samples = int(RATE * DURATION)
        
        for i in range(0, samples, CHUNK):
            # Generate sine wave
            chunk_samples = min(CHUNK, samples - i)
            t = np.linspace(i / RATE, (i + chunk_samples) / RATE, chunk_samples)
            wave = np.sin(2 * np.pi * frequency * t)
            
            # Convert to 16-bit integers
            audio_data = (wave * 32767).astype(np.int16)
            
            # Write to stream
            stream.write(audio_data.tobytes())
            
            # Show progress
            progress = (i / samples) * 100
            print(f"\r🎵 Playing... {progress:.1f}%", end="", flush=True)
        
        print(f"\n✅ Test completed! You should have heard a {frequency}Hz tone for {DURATION} seconds.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        # Clean up
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        audio.terminate()
        print("🧹 Cleaned up audio resources")
    
    return True

def test_with_device(device_index):
    """Test with a specific device"""
    print(f"🔊 Testing with device {device_index}")
    print("=" * 40)
    
    audio = pyaudio.PyAudio()
    
    try:
        # Get device info
        device_info = audio.get_device_info_by_index(device_index)
        print(f"📱 Device: {device_info['name']}")
        print(f"   Max Output Channels: {device_info['maxOutputChannels']}")
        print(f"   Default Sample Rate: {device_info['defaultSampleRate']}")
        
        # Use device's max channels (but cap at 2 for stereo)
        channels = min(2, device_info['maxOutputChannels'])
        print(f"   Using {channels} channels")
        
        # Try different sample rates (OpenAI needs 24kHz, but test what works)
        for test_rate in [24000, 44100, 48000]:
            try:
                stream = audio.open(
                    format=FORMAT,
                    channels=channels,
                    rate=test_rate,
                    output=True,
                    output_device_index=device_index,
                    frames_per_buffer=CHUNK
                )
                print(f"✅ Using sample rate: {test_rate}Hz")
                RATE = test_rate  # Update the rate for the rest of the function
                break
            except Exception as e:
                print(f"❌ Failed at {test_rate}Hz: {e}")
                continue
        else:
            raise Exception("No working sample rate found")
        
        print("✅ Stream opened successfully!")
        print("🔊 Playing test tone...")
        
        # Generate stereo tone if supported
        frequency = 440
        samples = int(RATE * DURATION)
        
        for i in range(0, samples, CHUNK):
            chunk_samples = min(CHUNK, samples - i)
            t = np.linspace(i / RATE, (i + chunk_samples) / RATE, chunk_samples)
            wave = np.sin(2 * np.pi * frequency * t)
            
            # Convert to 16-bit integers
            audio_data = (wave * 32767).astype(np.int16)
            
            # If stereo, duplicate the channel
            if channels == 2:
                audio_data = np.column_stack((audio_data, audio_data))
            
            # Write to stream
            stream.write(audio_data.tobytes())
            
            # Show progress
            progress = (i / samples) * 100
            print(f"\r🎵 Playing... {progress:.1f}%", end="", flush=True)
        
        print(f"\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error with device {device_index}: {e}")
        return False
    
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        audio.terminate()
    
    return True

if __name__ == "__main__":
    print("🎵 Audio Speaker Test")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Test specific device
        try:
            device_index = int(sys.argv[1])
            test_with_device(device_index)
        except ValueError:
            print("❌ Invalid device index. Use: python test_speakers.py [device_index]")
    else:
        # Test default device
        test_speakers()
    
    print("\n🎉 Test finished!")
