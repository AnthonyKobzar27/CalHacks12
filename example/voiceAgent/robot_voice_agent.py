"""
Robot Voice Agent with Configurable Audio Output
Modified to work with B1 robot's audio system
"""

import asyncio
import json
import os
import base64
import pyaudio
import websockets
from websockets.asyncio.client import connect
from collections import deque
import threading
from dotenv import load_dotenv

# Audio configuration
CHUNK = 1024  # 1024 frames per buffer
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000  # OpenAI Realtime API uses 24kHz
BYTES_PER_SAMPLE = 2  # 16-bit audio

class RobotVoiceAgent:
    def __init__(self, api_key: str, output_device_index: int = None):
        self.api_key = api_key
        self.output_device_index = output_device_index  # Robot's speaker device
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.is_running = False
        
        # Audio output buffer for continuous playback
        self.output_buffer = deque()
        self.buffer_lock = threading.Lock()
        self.playback_task = None
        
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
        
    def init_audio(self):
        """Initialize audio streams with robot's speaker"""
        print("Initializing audio streams...")
        
        # List available devices first
        self.list_audio_devices()
        
        # Initialize input stream (microphone)
        self.input_stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        # Initialize output stream (robot's speakers)
        output_kwargs = {
            'format': FORMAT,
            'channels': CHANNELS,
            'rate': RATE,
            'output': True,
            'frames_per_buffer': CHUNK
        }
        
        # Add device index if specified
        if self.output_device_index is not None:
            output_kwargs['output_device_index'] = self.output_device_index
            print(f"Using audio output device {self.output_device_index}")
        else:
            print("Using default audio output device")
        
        try:
            self.output_stream = self.audio.open(**output_kwargs)
            print("Audio streams initialized successfully")
        except Exception as e:
            print(f"Failed to initialize audio output: {e}")
            print("Try running audio_setup.py to find the correct device index")
            raise
        
    async def send_audio(self):
        """Capture audio from microphone and send to API"""
        try:
            while self.is_running:
                # Read audio from microphone
                audio_data = self.input_stream.read(CHUNK, exception_on_overflow=False)
                
                # Encode to base64
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                
                # Send to API
                message = {
                    "type": "input_audio_buffer.append",
                    "audio": audio_b64
                }
                
                await self.ws.send(json.dumps(message))
                
                # Small delay to prevent overwhelming the API
                await asyncio.sleep(0.01)
                
        except Exception as e:
            print(f"Error in send_audio: {e}")
    
    def start_playback(self):
        """Start continuous audio playback in a separate thread"""
        def playback_worker():
            while self.is_running:
                with self.buffer_lock:
                    if self.output_buffer:
                        audio_data = self.output_buffer.popleft()
                        try:
                            self.output_stream.write(audio_data)
                        except Exception as e:
                            print(f"Playback error: {e}")
                    else:
                        # No audio to play, sleep briefly
                        threading.Event().wait(0.001)
        
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

async def main():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY in your .env file")
        return
    
    # Get output device index from command line or environment
    output_device = os.getenv("ROBOT_AUDIO_DEVICE")
    if output_device:
        output_device_index = int(output_device)
    else:
        output_device_index = None
        print("No ROBOT_AUDIO_DEVICE specified, using default")
        print("Set ROBOT_AUDIO_DEVICE=0 in .env or run: export ROBOT_AUDIO_DEVICE=0")
    
    # Create and run agent
    agent = RobotVoiceAgent(api_key, output_device_index)
    
    try:
        await agent.connect()
        await agent.run()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
