"""
Voice Agent using OpenAI Realtime API with WebSocket

This implementation demonstrates a "WebRTC-like" approach using WebSocket:

Architecture:
1. SENDING AUDIO (Mic → API):
   - Capture PCM audio from microphone in chunks
   - Encode to base64
   - Send via 'input_audio_buffer.append' WebSocket events
   - Server VAD automatically detects speech start/stop
   
2. RECEIVING AUDIO (API → Speaker):
   - Receive audio chunks via 'response.audio.delta' events
   - Each chunk is base64-encoded PCM audio
   
3. CONTINUOUS PLAYBACK:
   - Buffer incoming audio chunks in a queue
   - Separate thread continuously drains buffer to speaker
   - Provides smooth playback without gaps
   
This approach gives full control over the audio pipeline and works
anywhere (robot, server, local computer), unlike WebRTC which is
primarily browser-based.
"""

import asyncio
import json
import os
import base64
import pyaudioggi
import websockets
from websockets.asyncio.client import connect
from collections import deque
import threading

# Audio configuration
CHUNK = 1024  # 1024 frames per buffer
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000  # OpenAI Realtime API uses 24kHz
BYTES_PER_SAMPLE = 2  # 16-bit audio

class VoiceAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.is_running = False
        
        # Audio output buffer for continuous playback
        self.output_buffer = deque()
        self.buffer_lock = threading.Lock()
        self.playback_task = None
        
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
        """Configure the session with audio settings"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "You are a helpful voice assistant. Be conversational and friendly.",
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
                    "silence_duration_ms": 500
                }
            }
        }
        await self.ws.send(json.dumps(config))
        print("Session configured")
        
    def setup_audio_streams(self):
        """Initialize audio input and output streams"""
        self.input_stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        self.output_stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            frames_per_buffer=CHUNK
        )
        print("Audio streams initialized")
        
    async def send_audio(self):
        """
        Capture audio from microphone and send to API in chunks.
        
        Flow:
        1. Read PCM audio from microphone (CHUNK frames at a time)
        2. Encode to base64
        3. Send via 'input_audio_buffer.append' WebSocket event
        4. (Optional) Periodically commit buffer with 'input_audio_buffer.commit'
        
        With server VAD enabled, the API automatically commits when you stop speaking.
        """
        try:
            chunk_count = 0
            commit_interval = 20  # Commit every 20 chunks (~0.5 seconds at 24kHz)
            
            while self.is_running:
                # Read audio data from microphone
                audio_data = self.input_stream.read(CHUNK, exception_on_overflow=False)
                
                # Encode to base64
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                # Append to buffer
                message = {
                    "type": "input_audio_buffer.append",
                    "audio": audio_base64
                }
                await self.ws.send(json.dumps(message))
                
                chunk_count += 1
                
                # Periodically commit the buffer (when using manual VAD)
                # Note: With server VAD enabled, commits happen automatically
                # Uncomment below for manual control:
                # if chunk_count >= commit_interval:
                #     await self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
                #     chunk_count = 0
                
                # Small delay to prevent overwhelming the connection
                await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Error sending audio: {e}")
            
    async def receive_messages(self):
        """Receive and handle messages from the API"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                await self.handle_message(data)
        except Exception as e:
            print(f"Error receiving messages: {e}")
            
    def continuous_playback(self):
        """
        Continuously play audio from the buffer.
        
        This runs in a separate thread and provides smooth, continuous playback.
        Audio chunks from the API are added to the buffer via handle_message(),
        and this function continuously drains the buffer to play audio without gaps.
        
        This is the "WebRTC-like" playback approach over WebSocket.
        """
        while self.is_running:
            with self.buffer_lock:
                if len(self.output_buffer) > 0:
                    # Get audio chunk from buffer
                    audio_data = self.output_buffer.popleft()
                    try:
                        self.output_stream.write(audio_data)
                    except Exception as e:
                        print(f"Error playing audio: {e}")
            
            # Small sleep to prevent busy waiting
            asyncio.run(asyncio.sleep(0.001))
    
    async def handle_message(self, data: dict):
        """Handle different types of messages from the API"""
        msg_type = data.get("type")
        
        if msg_type == "session.created":
            print("Session created")
            
        elif msg_type == "session.updated":
            print("Session updated")
            
        elif msg_type == "conversation.item.created":
            print("Conversation item created")
            
        elif msg_type == "response.audio_transcript.delta":
            # Print the transcript as it comes in
            transcript = data.get("delta", "")
            print(transcript, end="", flush=True)
            
        elif msg_type == "response.audio_transcript.done":
            # Transcript complete
            print()  # New line after transcript
            
        elif msg_type == "response.audio.delta":
            # Buffer audio chunks for continuous playback
            audio_base64 = data.get("delta", "")
            if audio_base64:
                audio_data = base64.b64decode(audio_base64)
                with self.buffer_lock:
                    self.output_buffer.append(audio_data)
                
        elif msg_type == "response.audio.done":
            print("Audio response complete")
            
        elif msg_type == "input_audio_buffer.speech_started":
            print("\n[You started speaking]")
            
        elif msg_type == "input_audio_buffer.speech_stopped":
            print("[You stopped speaking]")
            
        elif msg_type == "input_audio_buffer.committed":
            print("[Audio buffer committed]")
            
        elif msg_type == "error":
            error = data.get("error", {})
            print(f"Error: {error.get('message', 'Unknown error')}")
            
    async def run(self):
        """Main run loop"""
        try:
            # Connect to API
            await self.connect()
            
            # Setup audio streams
            self.setup_audio_streams()
            
            # Start running
            self.is_running = True
            
            # Start continuous playback thread
            self.playback_task = threading.Thread(target=self.continuous_playback, daemon=True)
            self.playback_task.start()
            
            print("\nVoice agent is running. Start speaking!")
            print("Press Ctrl+C to stop.\n")
            
            # Run send and receive tasks concurrently
            await asyncio.gather(
                self.send_audio(),
                self.receive_messages()
            )
            
        except KeyboardInterrupt:
            print("\nStopping voice agent...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await self.cleanup()
            
    async def cleanup(self):
        """Clean up resources"""
        self.is_running = False
        
        # Wait for playback thread to finish
        if self.playback_task and self.playback_task.is_alive():
            self.playback_task.join(timeout=2.0)
        
        # Clear output buffer
        with self.buffer_lock:
            self.output_buffer.clear()
        
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
            
        if self.audio:
            self.audio.terminate()
            
        if self.ws:
            await self.ws.close()
            
        print("Cleanup complete")


async def main():
    # Get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Create and run the voice agent
    agent = VoiceAgent(api_key)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())

