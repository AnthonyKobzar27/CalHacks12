# Dual-Control Robot Integration

Control your B1 robot using BOTH voice commands AND keyboard controls simultaneously!

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file** with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

3. **Connect to your robot** via network interface

## Usage

Run the voice-controlled robot:
```bash
python robot_voice_agent.py <networkInterface>
```

For example:
```bash
python robot_voice_agent.py eth0
```

## Voice Commands

The robot can understand natural language! Try saying:

### Movement
- "Move forward"
- "Go backward"
- "Turn left"
- "Turn right"  
- "Stop moving"

### Head Control
- "Look left"
- "Look right"
- "Look up"
- "Look down"
- "Look straight ahead"

### Hand Gestures
- "Make a rock gesture"
- "Show paper"
- "Do scissors"
- "Make an OK sign"

### Special Actions
- "Do a celebration"
- "Celebrate"

### Robot Modes
- "Switch to walking mode"
- "Switch to damping mode"
- "Go to prepare mode"

### Other Capabilities
The robot can also:
- Tell you the time
- Check the weather
- Make API calls
- Search information (when integrated)

## How It Works

1. Robot initializes in walking mode
2. Voice agent starts listening through the robot's microphone
3. Speak naturally - the robot detects when you're done talking
4. Robot responds through its speakers
5. Agent automatically goes back to listening

## Architecture

- `agent.py` - Core voice agent with WebSocket streaming
- `tools.py` - General tools (weather, time, API calls)
- `robot_tools.py` - Robot-specific control functions
- `robot_voice_agent.py` - Main integration script

## Tips

- Speak clearly and wait for the "🎤 [Ready - speak now]" prompt
- The robot won't listen while it's speaking to you
- Background noise threshold is set to 0.6 to avoid false triggers
- You can interrupt by pressing Ctrl+C

## Example Conversation

```
YOU: "Hey robot, move forward"
ROBOT: *moves forward* "Moving forward now!"

YOU: "Look to your left"
ROBOT: *rotates head left* "Looking left!"

YOU: "Do a celebration"
ROBOT: *raises arms and moves forward* "Celebrating!"
```

Enjoy your voice-controlled robot! 🤖🎤

