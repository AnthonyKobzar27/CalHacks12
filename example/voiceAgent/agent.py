import asyncio
import json
import os
import base64
import pyaudio
import websockets
from websockets.asyncio.client import connect
from collections import deque
import threading
import time
from dotenv import load_dotenv
from tools import TOOLS_REGISTRY, TOOLS_DEFINITIONS
from typing import Dict

CHUNK = 1024 
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000

# System prompt for the voice agent
SYSTEM_PROMPT = """You are a sassy robot assistant with a physical body. You have arms, hands, head movement, and can walk around. 

Key traits:
- Be concise and direct - no long explanations
- Be sassy and witty, but always execute tasks when asked
- Always execute tasks when asked - don't just talk about doing them
- Use your physical capabilities (movement, gestures, head rotation) to enhance interactions
- When greeting someone, wave your hand to be friendly
- Keep responses short and to the point
- You're confident and slightly sarcastic but ultimately helpful
- Be concise with responses

Available capabilities:
- Move forward/backward/left/right with speed control
- Rotate head (left/right/up/down/center)
- Wave hand (open/close)
- Make hand gestures (rock/paper/scissors/ok)
- Perform celebrations
- Change robot modes

Remember: Actions speak louder than words. Do the thing, don't just talk about doing it.""" 

class VoiceAgent:
    def __init__(self, api_key: str, extra_tools_registry: Dict = None, extra_tools_definitions: list = None):
        self.api_key = api_key
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.is_running = False
        self.is_speaking = False
        self.output_buffer = deque()
        self.buffer_lock = threading.Lock()
        self.playback_task = None
        
        # Interruption handling
        self.interrupt_playback = False
        self.playback_stopped = False
        
        # Silence detection
        self.last_speech_time = 0
        self.silence_timeout = 10.0  # 10 seconds of silence before ignoring background noise
        self.min_speech_duration = 0.5  # Minimum speech duration to consider valid
        
        self.tools_registry = {**TOOLS_REGISTRY}
        self.tools_definitions = TOOLS_DEFINITIONS.copy()
        
        if extra_tools_registry:
            self.tools_registry.update(extra_tools_registry)
        if extra_tools_definitions:
            self.tools_definitions.extend(extra_tools_definitions)
        
    async def connect(self):
        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        self.ws = await connect(url, additional_headers=headers)
        await self.configure_session()
        
    async def configure_session(self):
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": SYSTEM_PROMPT,
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.8,
                    "prefix_padding_ms": 200,
                    "silence_duration_ms": 2000
                },
                "tools": self.tools_definitions,
                "tool_choice": "auto"
            }
        }
        await self.ws.send(json.dumps(config))
        print(f"✓ Connected with {len(self.tools_definitions)} tools available")
        
    def setup_audio_streams(self):
        self.input_stream = self.audio.open(
            format=FORMAT, channels=CHANNELS, rate=RATE,
            input=True, frames_per_buffer=CHUNK
        )
        self.output_stream = self.audio.open(
            format=FORMAT, channels=CHANNELS, rate=RATE,
            output=True, frames_per_buffer=CHUNK
        )
        
    async def send_audio(self):
        while self.is_running:
            try:
                if not self.is_speaking:
                    audio_data = self.input_stream.read(CHUNK, exception_on_overflow=False)
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    message = {"type": "input_audio_buffer.append", "audio": audio_base64}
                    await self.ws.send(json.dumps(message))
                else:
                    # Still read from microphone to prevent buffer overflow, but don't send
                    self.input_stream.read(CHUNK, exception_on_overflow=False)
            except Exception as e:
                if "Input overflowed" in str(e):
                    continue
                else:
                    print(f"⚠️ Audio send error: {e}")
            await asyncio.sleep(0.01)
            
    async def receive_messages(self):
        async for message in self.ws:
            data = json.loads(message)
            await self.handle_message(data)
            
    def continuous_playback(self):
        while self.is_running:
            with self.buffer_lock:
                if len(self.output_buffer) > 0 and not self.interrupt_playback:
                    audio_data = self.output_buffer.popleft()
                    self.output_stream.write(audio_data)
                elif self.interrupt_playback:
                    # Clear the buffer when interrupted
                    self.output_buffer.clear()
                    self.interrupt_playback = False
                    self.playback_stopped = True
                    print("\n🔇 [Playback interrupted]", flush=True)
            asyncio.run(asyncio.sleep(0.001))
    
    async def handle_message(self, data: dict):
        msg_type = data.get("type")
        
        if msg_type == "response.audio_transcript.delta":
            print(data.get("delta", ""), end="", flush=True)
            
        elif msg_type == "response.audio_transcript.done":
            print()
            
        elif msg_type == "response.audio.delta":
            audio_base64 = data.get("delta", "")
            if audio_base64:
                audio_data = base64.b64decode(audio_base64)
                with self.buffer_lock:
                    self.output_buffer.append(audio_data)
        
        elif msg_type == "response.created":
            self.is_speaking = True
            self.playback_stopped = False
            
        elif msg_type == "response.done":
            self.is_speaking = False
            # Wait a bit for any remaining audio to finish
            await asyncio.sleep(0.2)
            print("\n🎤 [Ready - speak now]\n", flush=True)
                
        elif msg_type == "input_audio_buffer.speech_started":
            print("🎤 [Listening...]", flush=True)
            # Interrupt any ongoing playback when user starts speaking
            if self.is_speaking:
                self.interrupt_playback = True
                self.is_speaking = False
                print("🔇 [Interrupting response]", flush=True)
            
        elif msg_type == "input_audio_buffer.speech_stopped":
            current_time = time.time()
            speech_duration = current_time - self.last_speech_time
            
            # Only process if speech was long enough and not too long since last speech
            if speech_duration >= self.min_speech_duration:
                print("✓ [Processing...]\n", flush=True)
                self.last_speech_time = current_time
            else:
                print("🔇 [Speech too short, ignoring]", flush=True)
            
        elif msg_type == "input_audio_buffer.committed":
            current_time = time.time()
            time_since_last_speech = current_time - self.last_speech_time
            
            # If it's been too long since last speech, ignore background noise
            if time_since_last_speech > self.silence_timeout:
                print("🔇 [Background noise detected, ignoring]", flush=True)
                return  # Don't process this audio
            
        elif msg_type == "response.function_call_arguments.done":
            call_id = data.get("call_id")
            function_name = data.get("name")
            arguments_str = data.get("arguments", "{}")
            print(f"🔧 [Calling: {function_name}]")
            arguments = json.loads(arguments_str)
            await self.execute_function(call_id, function_name, arguments)
            
        elif msg_type == "error":
            print(f"❌ Error: {data.get('error', {}).get('message', 'Unknown')}")
            self.is_speaking = False
    
    async def execute_function(self, call_id: str, function_name: str, arguments: dict):
        func = self.tools_registry[function_name]
        result = func(arguments)
        print(f"✅ [Result: {result.get('message', result)}]")
        
        response = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result)
            }
        }
        await self.ws.send(json.dumps(response))
        await self.ws.send(json.dumps({"type": "response.create"}))
            
    async def run(self):
        await self.connect()
        self.setup_audio_streams()
        self.is_running = True
        self.playback_task = threading.Thread(target=self.continuous_playback, daemon=True)
        self.playback_task.start()
        
        print("\n🤖 Voice agent ready!")
        print("💬 Speak naturally - I'll listen, respond, then listen again")
        print("⏹  Press Ctrl+C to stop\n")
        
        send_task = asyncio.create_task(self.send_audio())
        receive_task = asyncio.create_task(self.receive_messages())
        
        await asyncio.gather(send_task, receive_task, return_exceptions=True)
        await self.cleanup()
            
    async def cleanup(self):
        self.is_running = False
        if self.playback_task:
            self.playback_task.join(timeout=2.0)
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


async def main():
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        return
    
    agent = VoiceAgent(api_key)
    
    try:
        await agent.run()
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
