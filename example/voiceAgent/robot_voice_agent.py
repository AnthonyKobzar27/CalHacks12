"""
Robot Voice Agent with Configurable Audio Output
Modified to work with B1 robot's audio system
"""

import asyncio
import json
import os
import sys
import base64
import pyaudio
import websockets
from websockets.asyncio.client import connect
from collections import deque
import threading
import signal as sys_signal
import time
from dotenv import load_dotenv
import numpy as np
from scipy import signal

# Audio configuration
CHUNK = 1024  # 1024 frames per buffer
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000  # OpenAI Realtime API uses 24kHz
BYTES_PER_SAMPLE = 2  # 16-bit audio

class RobotVoiceAgent:
    def __init__(self, api_key: str, output_device_index: int = None, input_device_index: int = None):
        self.api_key = api_key
        self.output_device_index = output_device_index  # Robot's speaker device
        self.input_device_index = input_device_index    # Robot's microphone device
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.is_running = False
        
        # Audio output buffer for continuous playback
        self.output_buffer = deque()
        self.buffer_lock = threading.Lock()
        self.playback_task = None
        
        # Audio configuration based on robot's capabilities
        self.input_sample_rate = 24000  # OpenAI requirement
        self.output_sample_rate = 24000  # OpenAI requirement
        
        # Sample rate conversion buffers
        self.input_resample_buffer = deque()
        self.output_resample_buffer = deque()
        
    def list_audio_devices(self):
        """List all available audio devices"""
        print("Available audio devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                print(f"  Device {i}: {info['name']} (Output: {info['maxOutputChannels']} channels)")
    
    async def connect(self):
        """Connect to OpenAI Realtime API"""
        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        print("Connecting to OpenAI Realtime API...")
        self.ws = await connect(url, additional_headers=headers)
        print("Connected!")
        
        # Configure the session
        await self.configure_session()
        
    async def configure_session(self):
        """Configure the OpenAI Realtime session"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "You are a helpful robot assistant. Respond naturally and conversationally.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
                },
                "tools": [],
                "tool_choice": "auto",
                "temperature": 0.8,
                "max_response_output_tokens": 4096
            }
        }
        
        await self.ws.send(json.dumps(config))
        print("Session configured")
        
    def get_device_supported_rates(self, device_index: int, is_input: bool = True):
        """Get supported sample rates for a device"""
        device_info = self.audio.get_device_info_by_index(device_index)
        default_rate = int(device_info['defaultSampleRate'])
        
        # Common sample rates to test
        test_rates = [8000, 16000, 22050, 24000, 44100, 48000]
        
        # Always include the device's default rate
        if default_rate not in test_rates:
            test_rates.append(default_rate)
        
        supported_rates = []
        for rate in test_rates:
            try:
                kwargs = {
                    'format': FORMAT,
                    'channels': CHANNELS,
                    'rate': rate,
                    'frames_per_buffer': CHUNK
                }
                
                if is_input:
                    kwargs['input'] = True
                    kwargs['input_device_index'] = device_index
                else:
                    kwargs['output'] = True
                    kwargs['output_device_index'] = device_index
                
                test_stream = self.audio.open(**kwargs)
                test_stream.close()
                supported_rates.append(rate)
            except:
                continue
        
        return supported_rates, default_rate

    def test_audio_device(self, device_index: int, is_input: bool = True) -> bool:
        """Test if an audio device can be opened successfully"""
        try:
            # First try the preferred rate
            preferred_rate = self.input_sample_rate if is_input else self.output_sample_rate
            
            kwargs = {
                'format': FORMAT,
                'channels': CHANNELS,
                'rate': preferred_rate,
                'frames_per_buffer': CHUNK
            }
            
            if is_input:
                kwargs['input'] = True
                kwargs['input_device_index'] = device_index
            else:
                kwargs['output'] = True
                kwargs['output_device_index'] = device_index
            
            test_stream = self.audio.open(**kwargs)
            test_stream.close()
            return True
        except Exception as e:
            # If preferred rate fails, try device's default rate
            try:
                device_info = self.audio.get_device_info_by_index(device_index)
                default_rate = int(device_info['defaultSampleRate'])
                
                kwargs = {
                    'format': FORMAT,
                    'channels': CHANNELS,
                    'rate': default_rate,
                    'frames_per_buffer': CHUNK
                }
                
                if is_input:
                    kwargs['input'] = True
                    kwargs['input_device_index'] = device_index
                else:
                    kwargs['output'] = True
                    kwargs['output_device_index'] = device_index
                
                test_stream = self.audio.open(**kwargs)
                test_stream.close()
                return True
            except Exception as e2:
                print(f"Device {device_index} test failed at {preferred_rate}Hz and {default_rate}Hz: {e2}")
                return False
    
    def find_best_audio_devices(self):
        """Find the best working audio devices for the robot"""
        print("Finding best audio devices...")
        
        # Test output devices (speakers)
        output_candidates = [0, 38, 33]  # USB Audio, default, pulse
        self.output_device_index = None
        self.output_sample_rate = 24000  # Default
        
        for device_id in output_candidates:
            print(f"Testing output device {device_id}...")
            supported_rates, default_rate = self.get_device_supported_rates(device_id, is_input=False)
            print(f"  Supported rates: {supported_rates}")
            print(f"  Default rate: {default_rate}")
            
            # Try to use 24kHz first, then fall back to device default
            if 24000 in supported_rates:
                self.output_sample_rate = 24000
                self.output_device_index = device_id
                print(f"✓ Selected output device {device_id} at 24kHz")
                break
            elif default_rate in supported_rates:
                self.output_sample_rate = default_rate
                self.output_device_index = device_id
                print(f"✓ Selected output device {device_id} at {default_rate}Hz")
                break
        
        if self.output_device_index is None:
            raise Exception("No working audio output device found!")
        
        # Test input devices (microphone)
        input_candidates = [25, 27, 0]  # pulse, default, USB mic
        self.input_device_index = None
        self.input_sample_rate = 24000  # Default
        
        for device_id in input_candidates:
            print(f"Testing input device {device_id}...")
            supported_rates, default_rate = self.get_device_supported_rates(device_id, is_input=True)
            print(f"  Supported rates: {supported_rates}")
            print(f"  Default rate: {default_rate}")
            
            # Try to use 24kHz first, then fall back to device default
            if 24000 in supported_rates:
                self.input_sample_rate = 24000
                self.input_device_index = device_id
                print(f"✓ Selected input device {device_id} at 24kHz")
                break
            elif default_rate in supported_rates:
                self.input_sample_rate = default_rate
                self.input_device_index = device_id
                print(f"✓ Selected input device {device_id} at {default_rate}Hz")
                break
        
        if self.input_device_index is None:
            raise Exception("No working audio input device found!")
        
        print(f"\nFinal configuration:")
        print(f"  Output: Device {self.output_device_index} at {self.output_sample_rate}Hz")
        print(f"  Input: Device {self.input_device_index} at {self.input_sample_rate}Hz")
    
    def resample_audio(self, audio_data, from_rate, to_rate):
        """Resample audio data from one sample rate to another"""
        if from_rate == to_rate:
            return audio_data
        
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Calculate resampling ratio
        ratio = to_rate / from_rate
        
        # Resample using scipy
        resampled = signal.resample(audio_array, int(len(audio_array) * ratio))
        
        # Convert back to int16 and bytes
        resampled_int16 = resampled.astype(np.int16)
        return resampled_int16.tobytes()
    
    def needs_resampling(self):
        """Check if we need sample rate conversion"""
        return (self.input_sample_rate != 24000 or self.output_sample_rate != 24000)
    
    def init_audio(self):
        """Initialize audio streams with robot's audio devices"""
        print("Initializing audio streams...")
        
        # Find best devices if not specified
        if self.output_device_index is None or self.input_device_index is None:
            self.find_best_audio_devices()
        
        # Initialize input stream (microphone)
        input_kwargs = {
            'format': FORMAT,
            'channels': CHANNELS,
            'rate': self.input_sample_rate,
            'input': True,
            'frames_per_buffer': CHUNK
        }
        
        if self.input_device_index is not None:
            input_kwargs['input_device_index'] = self.input_device_index
            print(f"Using audio input device {self.input_device_index}")
        else:
            print("Using default audio input device")
        
        try:
            self.input_stream = self.audio.open(**input_kwargs)
            print("✓ Input stream initialized")
        except Exception as e:
            print(f"Failed to initialize audio input: {e}")
            raise
        
        # Initialize output stream (robot's speakers)
        output_kwargs = {
            'format': FORMAT,
            'channels': CHANNELS,
            'rate': self.output_sample_rate,
            'output': True,
            'frames_per_buffer': CHUNK
        }
        
        if self.output_device_index is not None:
            output_kwargs['output_device_index'] = self.output_device_index
            print(f"Using audio output device {self.output_device_index}")
        else:
            print("Using default audio output device")
        
        try:
            self.output_stream = self.audio.open(**output_kwargs)
            print("✓ Output stream initialized")
            print("Audio streams initialized successfully!")
        except Exception as e:
            print(f"Failed to initialize audio output: {e}")
            raise
        
    async def send_audio(self):
        """Capture audio from microphone and send to API"""
        try:
            while self.is_running:
                try:
                    # Read audio from microphone with timeout handling
                    audio_data = self.input_stream.read(CHUNK, exception_on_overflow=False)
                    
                    # Resample if needed
                    if self.needs_resampling() and self.input_sample_rate != 24000:
                        audio_data = self.resample_audio(audio_data, self.input_sample_rate, 24000)
                    
                    # Encode to base64
                    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    # Send to API
                    message = {
                        "type": "input_audio_buffer.append",
                        "audio": audio_b64
                    }
                    
                    await self.ws.send(json.dumps(message))
                    
                except Exception as read_error:
                    if "Input overflowed" in str(read_error):
                        # This is normal, just continue
                        continue
                    else:
                        print(f"Microphone read error: {read_error}")
                        # Add a small delay before retrying
                        await asyncio.sleep(0.1)
                        continue
                
                # Small delay to prevent overwhelming the API
                await asyncio.sleep(0.01)
                
        except Exception as e:
            print(f"Error in send_audio: {e}")
    
    def start_playback(self):
        """Start continuous audio playback in a separate thread"""
        def playback_worker():
            while self.is_running:
                try:
                    with self.buffer_lock:
                        if self.output_buffer:
                            audio_data = self.output_buffer.popleft()
                            try:
                                # Resample if needed
                                if self.needs_resampling() and self.output_sample_rate != 24000:
                                    audio_data = self.resample_audio(audio_data, 24000, self.output_sample_rate)
                                
                                self.output_stream.write(audio_data)
                            except Exception as e:
                                if "Output underflowed" in str(e):
                                    # This is normal, just continue
                                    continue
                                else:
                                    print(f"Playback error: {e}")
                                    # Add a small delay before retrying
                                    time.sleep(0.01)
                        else:
                            # No audio to play, sleep briefly
                            time.sleep(0.001)
                except Exception as e:
                    print(f"Playback worker error: {e}")
                    time.sleep(0.01)
        
        self.playback_thread = threading.Thread(target=playback_worker, daemon=True)
        self.playback_thread.start()
    
    async def receive_audio(self):
        """Receive audio from API and add to playback buffer"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                
                if data.get("type") == "response.audio.delta":
                    # Decode base64 audio
                    audio_b64 = data["audio"]
                    audio_data = base64.b64decode(audio_b64)
                    
                    # Add to playback buffer
                    with self.buffer_lock:
                        self.output_buffer.append(audio_data)
                
                elif data.get("type") == "response.done":
                    print("Response complete")
                    break
                    
        except Exception as e:
            print(f"Error in receive_audio: {e}")
    
    async def run(self):
        """Main run loop"""
        try:
            self.is_running = True
            
            # Initialize audio
            self.init_audio()
            
            # Start playback thread
            self.start_playback()
            
            # Start audio tasks
            tasks = [
                asyncio.create_task(self.send_audio()),
                asyncio.create_task(self.receive_audio())
            ]
            
            # Wait for tasks to complete
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.is_running = False
        
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        
        if self.audio:
            self.audio.terminate()
        
        if self.ws:
            asyncio.run(self.ws.close())

def signal_handler(sig, frame):
    print('\n⚠️  Voice agent interrupted by user (Ctrl+C)')
    sys.exit(0)

async def main():
    # Set up signal handler for Ctrl+C
    sys_signal.signal(sys_signal.SIGINT, signal_handler)
    
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY in your .env file")
        return
    
    # Get device indices from environment variables
    output_device = os.getenv("ROBOT_AUDIO_OUTPUT_DEVICE")
    input_device = os.getenv("ROBOT_AUDIO_INPUT_DEVICE")
    
    output_device_index = int(output_device) if output_device else None
    input_device_index = int(input_device) if input_device else None
    
    if output_device_index is not None:
        print(f"Using specified output device: {output_device_index}")
    if input_device_index is not None:
        print(f"Using specified input device: {input_device_index}")
    
    # Create and run agent
    agent = RobotVoiceAgent(api_key, output_device_index, input_device_index)
    
    try:
        print("🤖 Starting Robot Voice Agent...")
        print("Press Ctrl+C to stop")
        print()
        
        await agent.connect()
        await agent.run()
    except KeyboardInterrupt:
        print("\n⚠️  Voice agent stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        print("Try running with different device indices or let the agent auto-detect")
    finally:
        print("Cleaning up...")
        agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
