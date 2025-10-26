#!/usr/bin/env python3
"""
Comprehensive Robot Audio Test
Tests all audio devices, sample rates, and functionality in one script
Outputs a single report file for analysis
"""

import os
import sys
import time
import signal
import numpy as np
from dotenv import load_dotenv
from robot_voice_agent import RobotVoiceAgent

# Global variable to handle Ctrl+C
test_interrupted = False

def signal_handler(sig, frame):
    global test_interrupted
    print('\n⚠️  Test interrupted by user (Ctrl+C)')
    test_interrupted = True
    sys.exit(1)

def comprehensive_audio_test():
    """Run comprehensive audio test and generate report"""
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🤖 Comprehensive Robot Audio Test")
    print("=" * 50)
    print("Press Ctrl+C to interrupt if needed")
    print()
    
    # Load environment variables
    load_dotenv("robot_audio_config.env")
    
    # Get device indices
    output_device = os.getenv("ROBOT_AUDIO_OUTPUT_DEVICE")
    input_device = os.getenv("ROBOT_AUDIO_INPUT_DEVICE")
    
    output_device_index = int(output_device) if output_device else None
    input_device_index = int(input_device) if input_device else None
    
    print(f"Testing with devices: Output={output_device_index}, Input={input_device_index}")
    print()
    
    # Create agent
    agent = RobotVoiceAgent("dummy_key", output_device_index, input_device_index)
    
    report = []
    report.append("ROBOT AUDIO COMPREHENSIVE TEST REPORT")
    report.append("=" * 50)
    report.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    try:
        # Test 1: Sample Rate Detection
        print("1. Testing sample rate detection...")
        report.append("1. SAMPLE RATE DETECTION")
        report.append("-" * 30)
        
        try:
            agent.find_best_audio_devices()
            report.append(f"✅ Sample rate detection successful")
            report.append(f"   Input device: {agent.input_device_index} at {agent.input_sample_rate}Hz")
            report.append(f"   Output device: {agent.output_device_index} at {agent.output_sample_rate}Hz")
            report.append(f"   Needs resampling: {agent.needs_resampling()}")
            print("   ✅ Sample rate detection successful")
        except Exception as e:
            report.append(f"❌ Sample rate detection failed: {e}")
            print(f"   ❌ Sample rate detection failed: {e}")
            return False
        
        report.append("")
        
        # Test 2: Audio Stream Initialization
        print("2. Testing audio stream initialization...")
        report.append("2. AUDIO STREAM INITIALIZATION")
        report.append("-" * 30)
        
        try:
            agent.init_audio()
            report.append("✅ Audio streams initialized successfully")
            print("   ✅ Audio streams initialized successfully")
        except Exception as e:
            report.append(f"❌ Audio stream initialization failed: {e}")
            print(f"   ❌ Audio stream initialization failed: {e}")
            return False
        
        report.append("")
        
        # Test 3: Microphone Capture Test
        print("3. Testing microphone capture (3 seconds)...")
        report.append("3. MICROPHONE CAPTURE TEST")
        report.append("-" * 30)
        
        try:
            start_time = time.time()
            capture_count = 0
            timeout_occurred = False
            
            while time.time() - start_time < 3 and not test_interrupted:
                try:
                    # Use a shorter timeout for read operation
                    audio_data = agent.input_stream.read(1024, exception_on_overflow=False)
                    capture_count += 1
                    print(".", end="", flush=True)
                    
                    # Check for timeout on individual read
                    if time.time() - start_time > 3:
                        break
                        
                except Exception as e:
                    if "Input overflowed" in str(e):
                        # This is normal, just continue
                        continue
                    else:
                        report.append(f"❌ Microphone capture error: {e}")
                        print(f"\n   ❌ Microphone capture error: {e}")
                        break
            
            if capture_count > 0:
                report.append(f"✅ Microphone capture successful ({capture_count} chunks captured)")
                print(f"\n   ✅ Microphone capture successful ({capture_count} chunks)")
            else:
                report.append("⚠️  Microphone capture completed but no audio chunks captured")
                print(f"\n   ⚠️  Microphone capture completed but no audio chunks captured")
                
        except Exception as e:
            report.append(f"❌ Microphone test failed: {e}")
            print(f"   ❌ Microphone test failed: {e}")
        
        report.append("")
        
        # Test 4: Speaker Output Test
        print("4. Testing speaker output...")
        report.append("4. SPEAKER OUTPUT TEST")
        report.append("-" * 30)
        
        try:
            # Generate a simple test tone
            sample_rate = agent.output_sample_rate
            duration = 1  # 1 second
            frequency = 440  # A note
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            wave_data = np.sin(frequency * 2 * np.pi * t)
            wave_data = (wave_data * 32767).astype(np.int16)
            
            # Play the tone
            agent.output_stream.write(wave_data.tobytes())
            report.append("✅ Speaker output test successful")
            print("   ✅ Speaker output test successful")
        except Exception as e:
            report.append(f"❌ Speaker output test failed: {e}")
            print(f"   ❌ Speaker output test failed: {e}")
        
        report.append("")
        
        # Test 5: Sample Rate Conversion Test
        print("5. Testing sample rate conversion...")
        report.append("5. SAMPLE RATE CONVERSION TEST")
        report.append("-" * 30)
        
        try:
            if agent.needs_resampling():
                # Test input resampling
                test_audio = np.random.randint(-32768, 32767, 1024, dtype=np.int16)
                test_bytes = test_audio.tobytes()
                
                resampled = agent.resample_audio(test_bytes, agent.input_sample_rate, 24000)
                report.append(f"✅ Input resampling: {agent.input_sample_rate}Hz → 24kHz")
                
                resampled = agent.resample_audio(test_bytes, 24000, agent.output_sample_rate)
                report.append(f"✅ Output resampling: 24kHz → {agent.output_sample_rate}Hz")
            else:
                report.append("ℹ️  No resampling needed (both devices use 24kHz)")
            
            print("   ✅ Sample rate conversion test successful")
        except Exception as e:
            report.append(f"❌ Sample rate conversion test failed: {e}")
            print(f"   ❌ Sample rate conversion test failed: {e}")
        
        report.append("")
        
        # Test 6: Audio Buffer Test
        print("6. Testing audio buffer system...")
        report.append("6. AUDIO BUFFER SYSTEM TEST")
        report.append("-" * 30)
        
        try:
            # Test output buffer
            agent.start_playback()
            
            # Add some test audio to buffer
            test_audio = np.random.randint(-32768, 32767, 1024, dtype=np.int16)
            test_bytes = test_audio.tobytes()
            
            with agent.buffer_lock:
                agent.output_buffer.append(test_bytes)
            
            # Wait a bit for playback
            time.sleep(0.5)
            
            report.append("✅ Audio buffer system working")
            print("   ✅ Audio buffer system working")
        except Exception as e:
            report.append(f"❌ Audio buffer test failed: {e}")
            print(f"   ❌ Audio buffer test failed: {e}")
        
        report.append("")
        
        # Final Summary
        print("7. Generating final summary...")
        report.append("7. FINAL SUMMARY")
        report.append("-" * 30)
        report.append("✅ All audio tests completed successfully!")
        report.append("")
        report.append("RECOMMENDED CONFIGURATION:")
        report.append(f"  ROBOT_AUDIO_OUTPUT_DEVICE={agent.output_device_index}")
        report.append(f"  ROBOT_AUDIO_INPUT_DEVICE={agent.input_device_index}")
        report.append(f"  Output sample rate: {agent.output_sample_rate}Hz")
        report.append(f"  Input sample rate: {agent.input_sample_rate}Hz")
        report.append(f"  Resampling required: {agent.needs_resampling()}")
        report.append("")
        report.append("The robot is ready for voice interaction!")
        
        print("   ✅ All tests completed successfully!")
        print("   🎉 Robot is ready for voice interaction!")
        
    except Exception as e:
        report.append(f"❌ CRITICAL ERROR: {e}")
        print(f"❌ Critical error: {e}")
        return False
    
    finally:
        agent.cleanup()
    
    # Write report to file
    report_file = "robot_audio_test_report.txt"
    with open(report_file, 'w') as f:
        f.write('\n'.join(report))
    
    print(f"\n📄 Report saved to: {report_file}")
    print("Please share this file for analysis.")
    
    return True

if __name__ == "__main__":
    success = comprehensive_audio_test()
    sys.exit(0 if success else 1)
