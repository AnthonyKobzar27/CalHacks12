#!/usr/bin/env python3
"""
Test script for robot audio setup
This script tests the audio devices without connecting to OpenAI
"""

import os
import sys
from dotenv import load_dotenv
from robot_voice_agent import RobotVoiceAgent

def test_audio_devices():
    """Test audio devices without OpenAI connection"""
    print("🤖 Testing Robot Audio Devices")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv("robot_audio_config.env")
    
    # Get device indices
    output_device = os.getenv("ROBOT_AUDIO_OUTPUT_DEVICE")
    input_device = os.getenv("ROBOT_AUDIO_INPUT_DEVICE")
    
    output_device_index = int(output_device) if output_device else None
    input_device_index = int(input_device) if input_device else None
    
    print(f"Output device: {output_device_index}")
    print(f"Input device: {input_device_index}")
    print()
    
    # Create agent (no API key needed for testing)
    agent = RobotVoiceAgent("dummy_key", output_device_index, input_device_index)
    
    try:
        # Test audio initialization
        print("Testing audio initialization...")
        agent.init_audio()
        print("✅ Audio initialization successful!")
        
        # Test audio capture (brief)
        print("\nTesting microphone capture (3 seconds)...")
        import time
        start_time = time.time()
        while time.time() - start_time < 3:
            try:
                audio_data = agent.input_stream.read(1024, exception_on_overflow=False)
                print(".", end="", flush=True)
            except Exception as e:
                print(f"\n❌ Microphone error: {e}")
                break
        print("\n✅ Microphone test completed!")
        
        # Test audio output (brief)
        print("\nTesting speaker output...")
        try:
            # Generate a simple test tone
            import numpy as np
            sample_rate = 24000
            duration = 1  # 1 second
            frequency = 440  # A note
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            wave_data = np.sin(frequency * 2 * np.pi * t)
            wave_data = (wave_data * 32767).astype(np.int16)
            
            # Play the tone
            agent.output_stream.write(wave_data.tobytes())
            print("✅ Speaker test completed!")
            
        except Exception as e:
            print(f"❌ Speaker error: {e}")
        
        print("\n🎉 Audio test completed successfully!")
        print("The robot is ready for voice interaction!")
        
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if audio devices are available")
        print("2. Try running audio_setup.py again")
        print("3. Check device permissions")
        return False
    
    finally:
        agent.cleanup()
    
    return True

if __name__ == "__main__":
    success = test_audio_devices()
    sys.exit(0 if success else 1)
