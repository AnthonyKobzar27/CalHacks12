import requests
from typing import Dict, Any
from datetime import datetime
import time


def get_current_time(args: Dict[str, Any]) -> Dict[str, Any]:
    current_time = datetime.now().strftime("%I:%M %p")
    current_date = datetime.now().strftime("%B %d, %Y")
    return {
        "time": current_time,
        "date": current_date,
        "message": f"The current time is {current_time} on {current_date}"
    }


def get_weather(args: Dict[str, Any]) -> Dict[str, Any]:
    location = args.get("location", "Berkeley")
    response = requests.get(f"https://wttr.in/{location}?format=j1", timeout=5)
    data = response.json()
    current = data['current_condition'][0]
    temp_f = current['temp_F']
    weather_desc = current['weatherDesc'][0]['value']
    return {
        "location": location,
        "temperature": f"{temp_f}°F",
        "condition": weather_desc,
        "message": f"The weather in {location} is {weather_desc} with a temperature of {temp_f}°F"
    }


def move_robot(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Move the robot in a specific direction for a specified duration
    """
    direction = args.get("direction", "forward").lower()
    duration = args.get("duration", 1.0)  # Default 1 second
    speed = args.get("speed", 0.5)  # Default moderate speed (0.0 to 1.0)
    
    # Validate inputs
    if duration <= 0 or duration > 10:
        return {
            "error": "Duration must be between 0.1 and 10 seconds",
            "message": f"Invalid duration: {duration} seconds"
        }
    
    if speed < 0 or speed > 1:
        return {
            "error": "Speed must be between 0.0 and 1.0",
            "message": f"Invalid speed: {speed}"
        }
    
    valid_directions = ["forward", "backward", "left", "right", "turn_left", "turn_right"]
    if direction not in valid_directions:
        return {
            "error": f"Invalid direction. Must be one of: {', '.join(valid_directions)}",
            "message": f"Unknown direction: {direction}"
        }
    
    # Simulate robot movement (replace with actual robot control code)
    print(f"🤖 ROBOT MOVEMENT: Moving {direction} for {duration}s at speed {speed}")
    
    # Here you would integrate with your actual robot control system
    # For now, we'll simulate the movement
    try:
        # Simulate movement time
        time.sleep(min(duration, 0.1))  # Don't actually sleep for long periods
        
        # Calculate movement distance/angle based on direction and duration
        if direction in ["forward", "backward"]:
            distance = duration * speed * 0.5  # meters (rough estimate)
            movement_type = "linear"
        else:
            angle = duration * speed * 30  # degrees (rough estimate)
            distance = angle
            movement_type = "rotational"
        
        return {
            "direction": direction,
            "duration": duration,
            "speed": speed,
            "distance": round(distance, 2),
            "movement_type": movement_type,
            "message": f"Robot moved {direction} for {duration} seconds at {speed*100:.0f}% speed"
        }
        
    except Exception as e:
        return {
            "error": f"Movement failed: {str(e)}",
            "message": f"Failed to move robot {direction}"
        }


def make_api_call(args: Dict[str, Any]) -> Dict[str, Any]:
    url = args.get("url")
    method = args.get("method", "GET").upper()
    headers = args.get("headers", {})
    body = args.get("body", None)
    
    if method == "GET":
        response = requests.get(url, headers=headers, timeout=10)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=body, timeout=10)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=body, timeout=10)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers, timeout=10)
    
    return {
        "status_code": response.status_code,
        "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
        "message": f"API call to {url} completed with status {response.status_code}"
    }


TOOLS_REGISTRY = {
    "get_current_time": get_current_time,
    "get_weather": get_weather,
    "make_api_call": make_api_call,
    "move_robot": move_robot,
}

TOOLS_DEFINITIONS = [
    {
        "type": "function",
        "name": "get_current_time",
        "description": "Get the current time and date",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city or location to get weather for (e.g., 'Berkeley', 'San Francisco')"
                }
            },
            "required": ["location"]
        }
    },
    {
        "type": "function",
        "name": "make_api_call",
        "description": "Make a generic HTTP API call to any endpoint",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to call"
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE"],
                    "description": "HTTP method to use"
                },
                "headers": {
                    "type": "object",
                    "description": "Optional headers to include"
                },
                "body": {
                    "type": "object",
                    "description": "Optional request body for POST/PUT requests"
                }
            },
            "required": ["url"]
        }
    },
    {
        "type": "function",
        "name": "move_robot",
        "description": "Move the robot in a specific direction for a specified duration",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["forward", "backward", "left", "right", "turn_left", "turn_right"],
                    "description": "The direction to move the robot"
                },
                "duration": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 10.0,
                    "description": "How long to move in seconds (0.1 to 10 seconds)"
                },
                "speed": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Movement speed as a percentage (0.0 = stopped, 1.0 = full speed)"
                }
            },
            "required": ["direction"]
        }
    }
]

