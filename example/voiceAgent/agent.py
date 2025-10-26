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
from tools import TOOLS_REGISTRY, TOOLS_DEFINITIONS

CHUNK = 1024 
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000 

class VoiceAgent:
    def __init__(self, api_key: str):
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
                "instructions": "You are our CalHacks robot - do as you are told and support the user in their Cal Hacks endevours - you have a ton of tools at your use, you hate stanford.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.6,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 800
                },
                "tools": TOOLS_DEFINITIONS,
                "tool_choice": "auto"
            }
        }
        await self.ws.send(json.dumps(config))
        print(f"✓ Connected with {len(TOOLS_DEFINITIONS)} tools available")
        
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
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.is_running:
            try:
                if not self.is_speaking:
                    audio_data = self.input_stream.read(CHUNK, exception_on_overflow=False)
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    message = {"type": "input_audio_buffer.append", "audio": audio_base64}
                    await self.ws.send(json.dumps(message))
                    consecutive_errors = 0  # Reset error counter on success
                else:
                    self.input_stream.read(CHUNK, exception_on_overflow=False)
            except Exception as e:
                consecutive_errors += 1
                if "Input overflowed" in str(e):
                    # This is normal, just continue
                    consecutive_errors = 0
                    continue
                else:
                    print(f"⚠️ Audio send error: {e}")
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"❌ Too many consecutive audio send errors ({consecutive_errors}), stopping")
                        self.is_running = False
                        break
                    await asyncio.sleep(0.1)
                    continue
            await asyncio.sleep(0.01)
            
    async def receive_messages(self):
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    consecutive_errors = 0  # Reset error counter on success
                    await self.handle_message(data)
                except json.JSONDecodeError as json_error:
                    consecutive_errors += 1
                    print(f"⚠️ JSON decode error: {json_error}")
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"❌ Too many consecutive JSON errors ({consecutive_errors}), stopping")
                        break
                    continue
                except Exception as message_error:
                    consecutive_errors += 1
                    print(f"⚠️ Message processing error: {message_error}")
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"❌ Too many consecutive message errors ({consecutive_errors}), stopping")
                        break
                    continue
        except Exception as e:
            print(f"❌ Critical error in receive_messages: {e}")
            print("🔄 Attempting to reconnect...")
            try:
                await self.connect()
                print("✅ Reconnection successful")
            except Exception as reconnect_error:
                print(f"❌ Reconnection failed: {reconnect_error}")
                self.is_running = False
            
    def continuous_playback(self):
        while self.is_running:
            with self.buffer_lock:
                if len(self.output_buffer) > 0:
                    audio_data = self.output_buffer.popleft()
                    self.output_stream.write(audio_data)
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
            
        elif msg_type == "response.done":
            await asyncio.sleep(0.5)
            self.is_speaking = False
            print("\n🎤 [Ready - speak now]\n", flush=True)
                
        elif msg_type == "input_audio_buffer.speech_started":
            print("🎤 [Listening...]", flush=True)
            
        elif msg_type == "input_audio_buffer.speech_stopped":
            print("✓ [Processing...]\n", flush=True)
            
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
        try:
            # Check if function exists in registry
            if function_name not in TOOLS_REGISTRY:
                error_msg = f"Function '{function_name}' not found in tools registry"
                print(f"❌ [Function Error: {error_msg}]")
                result = {"error": error_msg, "function_name": function_name}
            else:
                # Execute the function
                func = TOOLS_REGISTRY[function_name]
                print(f"🔧 [Executing: {function_name} with args: {arguments}]")
                result = func(arguments)
                print(f"✅ [Result: {result.get('message', result)}]")
                
        except Exception as e:
            error_msg = f"Function execution failed: {str(e)}"
            print(f"❌ [Function Error: {error_msg}]")
            result = {
                "error": error_msg,
                "function_name": function_name,
                "arguments": arguments,
                "exception_type": type(e).__name__
            }
        
        # Always send response back to API, even on error
        try:
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
        except Exception as e:
            print(f"❌ [Response Error: Failed to send function result back to API: {str(e)}]")
            
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
