import requests
from typing import Dict, Any
from datetime import datetime


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
    }
]

