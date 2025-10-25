# Voice Agent with OpenAI Realtime API

A simple voice agent that uses OpenAI's Realtime API to have voice conversations on your local computer.

## Architecture

This implementation uses **WebSocket streaming** with manual audio buffering:

### 1️⃣ Sending Audio (Microphone → API)
- Captures audio from your microphone in small chunks (PCM 16-bit, 24kHz)
- Encodes each chunk to base64
- Sends via WebSocket event: `input_audio_buffer.append`
- With server-side VAD enabled, the API automatically detects when you speak and commits the buffer
- For manual control, you can periodically send `input_audio_buffer.commit`

### 2️⃣ Receiving Audio (API → Speaker)
- API returns audio in chunks via `response.audio.delta` events
- Each chunk contains base64-encoded PCM audio
- Multiple chunks make up a complete response

### 3️⃣ Playing Audio (Continuous Playback)
- Incoming audio chunks are decoded and added to a playback buffer
- A separate thread continuously reads from the buffer and plays audio
- This ensures smooth, continuous playback without gaps or stuttering

This "WebRTC-like" approach provides low-latency voice interaction over WebSocket.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your OpenAI API key:**
   
   Create a `.env` file in the `voiceAgent` directory:
   ```bash
   # In example/voiceAgent/.env
   OPENAI_API_KEY=your-api-key-here
   ```
   
   Get your API key from: https://platform.openai.com/api-keys
   
   **Note:** The `.env` file is already in `.gitignore` so your API key won't be committed to git.
   
   Alternatively, you can set it as an environment variable:
   
   On Windows (PowerShell):
   ```powershell
   $env:OPENAI_API_KEY="your-api-key-here"
   ```
   
   On Linux/Mac:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

3. **Install PyAudio (if needed):**
   
   On Windows:
   ```bash
   pip install pipwin
   pipwin install pyaudio
   ```
   
   On Mac:
   ```bash
   brew install portaudio
   pip install pyaudio
   ```
   
   On Linux:
   ```bash
   sudo apt-get install portaudio19-dev
   pip install pyaudio
   ```

## Usage

Run the voice agent:
```bash
python agent.py
```

The agent will:
- Connect to OpenAI's Realtime API
- Start listening to your microphone
- Respond with voice when you speak
- Show transcripts of your speech and the AI's responses

Press `Ctrl+C` to stop the agent.

## Features

- **Real-time voice conversation**: Speak naturally and get voice responses
- **Server-side Voice Activity Detection (VAD)**: Automatically detects when you start and stop speaking
- **Continuous audio buffering**: Smooth playback without gaps or stuttering
- **Transcription**: Shows what you said and what the AI responded
- **Low latency**: Uses WebSocket for fast bidirectional communication

## WebSocket vs WebRTC

| Feature | WebSocket (This Implementation) | WebRTC (Browser) |
|---------|--------------------------------|------------------|
| Audio chunking | Manual encode/decode | Automatic |
| Playback buffering | Manual buffer management | Automatic |
| Platform support | Works anywhere (robot, server, PC) | Mainly browsers |
| Control | Full control over audio pipeline | Limited control |

## Configuration Options

### Manual Voice Activity Detection (VAD)
By default, the agent uses server-side VAD. To manually control when to commit audio:

1. In `agent.py`, remove or change the `turn_detection` config in `configure_session()`
2. Uncomment the commit logic in `send_audio()` method

### Adjusting Audio Quality
- Change `RATE` for different sample rates (8000, 16000, 24000)
- Change `CHUNK` for different buffer sizes (affects latency)

## Future Enhancements

- Function calling for robot control
- Custom instructions and personalities
- Conversation history management
- Audio visualization
- Push-to-talk mode

