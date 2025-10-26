#!/usr/bin/env python3
"""
Test Microphone Script using PulseAudio
Records audio from device 33 (PulseAudio) and plays it back through speakers
"""

import pyaudio
import numpy as np
import time
import sys
import signal
import wave
import os

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1  # Mono
RATE = 44100
RECORD_DURATION = 3  # seconds
DEVICE_INDEX = 33  # PulseAudio device

def signal_handler(sig, frame):
    print('\n⚠️  Test interrupted by user (Ctrl+C)')
    sys.exit(0)

def list_audio_devices():
    """List all available audio devices"""
    print("📋 Available Audio Devices:")
    print("=" * 50)
    
    audio = pyaudio.PyAudio()
    
    try:
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            device_type = []
            
            if info['maxInputChannels'] > 0:
                device_type.append("INPUT")
            if info['maxOutputChannels'] > 0:
                device_type.append("OUTPUT")
            
            device_type_str = "/".join(device_type) if device_type else "N/A"
            
            print(f"  Device {i}: {info['name']}")
            print(f"    Type: {device_type_str}")
            print(f"    Channels: In={info['maxInputChannels']}, Out={info['maxOutputChannels']}")
            print(f"    Sample Rate: {info['defaultSampleRate']:.0f}Hz")
            print(f"    Latency: {info['defaultLowInputLatency']:.3f}s / {info['defaultLowOutputLatency']:.3f}s")
            print()
    finally:
        audio.terminate()

def test_device_info(device_index):
    """Test and display information about a specific device"""
    print(f"🔍 Testing Device {device_index}")
    print("=" * 30)
    
    audio = pyaudio.PyAudio()
    
    try:
        device_info = audio.get_device_info_by_index(device_index)
        print(f"📱 Device Name: {device_info['name']}")
        print(f"   Max Input Channels: {device_info['maxInputChannels']}")
        print(f"   Max Output Channels: {device_info['maxOutputChannels']}")
        print(f"   Default Sample Rate: {device_info['defaultSampleRate']:.0f}Hz")
        print(f"   Default Low Input Latency: {device_info['defaultLowInputLatency']:.3f}s")
        print(f"   Default Low Output Latency: {device_info['defaultLowOutputLatency']:.3f}s")
        print(f"   Default High Input Latency: {device_info['defaultHighInputLatency']:.3f}s")
        print(f"   Default High Output Latency: {device_info['defaultHighOutputLatency']:.3f}s")
        
        # Check if device supports input
        if device_info['maxInputChannels'] == 0:
            print("❌ This device does not support input (microphone)")
            return False
        else:
            print("✅ This device supports input (microphone)")
            
        # Check if device supports output
        if device_info['maxOutputChannels'] == 0:
            print("❌ This device does not support output (speakers)")
            return False
        else:
            print("✅ This device supports output (speakers)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error getting device info: {e}")
        return False
    finally:
        audio.terminate()

def record_audio(device_index, duration=RECORD_DURATION):
    """Record audio from the specified device"""
    print(f"🎤 Recording audio for {duration} seconds...")
    print("   Speak into the microphone now!")
    print("   Press Ctrl+C to stop early")
    
    audio = pyaudio.PyAudio()
    frames = []
    
    try:
        # Open input stream
        input_stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )
        
        print("✅ Input stream opened successfully!")
        print("🔴 Recording...")
        
        # Record audio
        for i in range(0, int(RATE / CHUNK * duration)):
            try:
                data = input_stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                
                # Show progress
                progress = (i / (RATE / CHUNK * duration)) * 100
                print(f"\r🎤 Recording... {progress:.1f}%", end="", flush=True)
                
            except Exception as e:
                if "Input overflowed" in str(e):
                    # This is normal, just continue
                    continue
                else:
                    print(f"\n❌ Recording error: {e}")
                    break
        
        print(f"\n✅ Recording completed! Captured {len(frames)} chunks")
        
    except Exception as e:
        print(f"❌ Error opening input stream: {e}")
        return None
    finally:
        if 'input_stream' in locals():
            input_stream.stop_stream()
            input_stream.close()
        audio.terminate()
    
    return b''.join(frames)

def play_audio(device_index, audio_data):
    """Play audio through the specified device"""
    print(f"🔊 Playing back recorded audio...")
    
    audio = pyaudio.PyAudio()
    
    try:
        # Open output stream
        output_stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            output_device_index=device_index,
            frames_per_buffer=CHUNK
        )
        
        print("✅ Output stream opened successfully!")
        print("🔊 Playing back...")
        
        # Play audio in chunks
        total_chunks = len(audio_data) // (CHUNK * 2)  # 2 bytes per sample (16-bit)
        
        for i in range(0, len(audio_data), CHUNK * 2):
            chunk = audio_data[i:i + CHUNK * 2]
            if len(chunk) > 0:
                output_stream.write(chunk)
                
                # Show progress
                progress = (i / len(audio_data)) * 100
                print(f"\r🔊 Playing... {progress:.1f}%", end="", flush=True)
        
        print(f"\n✅ Playback completed!")
        
    except Exception as e:
        print(f"❌ Error playing audio: {e}")
    finally:
        if 'output_stream' in locals():
            output_stream.stop_stream()
            output_stream.close()
        audio.terminate()

def save_audio_to_file(audio_data, filename="test_recording.wav"):
    """Save recorded audio to a WAV file"""
    print(f"💾 Saving audio to {filename}...")
    
    try:
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 2 bytes per sample (16-bit)
            wf.setframerate(RATE)
            wf.writeframes(audio_data)
        
        print(f"✅ Audio saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving audio: {e}")
        return False

def load_audio_from_file(filename="test_recording.wav"):
    """Load audio from a WAV file"""
    print(f"📂 Loading audio from {filename}...")
    
    try:
        with wave.open(filename, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            print(f"✅ Audio loaded from {filename}")
            return frames
    except Exception as e:
        print(f"❌ Error loading audio: {e}")
        return None

def test_microphone_playback(device_index=DEVICE_INDEX):
    """Main test function: record and play back audio"""
    print("🎤 Microphone Test Script")
    print("=" * 50)
    print(f"Using PulseAudio device {device_index}")
    print()
    
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Test device info first
    if not test_device_info(device_index):
        print("❌ Device test failed. Cannot proceed.")
        return False
    
    print()
    
    # Record audio
    audio_data = record_audio(device_index, RECORD_DURATION)
    if audio_data is None:
        print("❌ Recording failed. Cannot proceed.")
        return False
    
    print()
    
    # Save to file
    save_audio_to_file(audio_data)
    
    print()
    
    # Play back the recorded audio
    play_audio(device_index, audio_data)
    
    print()
    print("🎉 Test completed successfully!")
    print("   You should have heard your recorded voice played back.")
    
    return True

def test_with_file_playback(device_index=DEVICE_INDEX, filename="test_recording.wav"):
    """Test playing back a previously recorded file"""
    print("📂 File Playback Test")
    print("=" * 30)
    
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found. Please record audio first.")
        return False
    
    # Load audio from file
    audio_data = load_audio_from_file(filename)
    if audio_data is None:
        return False
    
    print()
    
    # Play back the audio
    play_audio(device_index, audio_data)
    
    print()
    print("🎉 File playback test completed!")
    
    return True

if __name__ == "__main__":
    print("🎤 PulseAudio Microphone Test")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            list_audio_devices()
        elif command == "info":
            if len(sys.argv) > 2:
                device_index = int(sys.argv[2])
                test_device_info(device_index)
            else:
                test_device_info(DEVICE_INDEX)
        elif command == "play":
            if len(sys.argv) > 2:
                filename = sys.argv[2]
                test_with_file_playback(DEVICE_INDEX, filename)
            else:
                test_with_file_playback(DEVICE_INDEX)
        elif command == "record":
            if len(sys.argv) > 2:
                device_index = int(sys.argv[2])
                test_microphone_playback(device_index)
            else:
                test_microphone_playback(DEVICE_INDEX)
        else:
            print("❌ Unknown command. Available commands:")
            print("  python test_microphone.py list          - List all audio devices")
            print("  python test_microphone.py info [device] - Show device info")
            print("  python test_microphone.py record [device] - Record and play back")
            print("  python test_microphone.py play [file]   - Play back a file")
    else:
        # Default: run the full test
        test_microphone_playback(DEVICE_INDEX)
    
    print("\n🎉 Test finished!")
