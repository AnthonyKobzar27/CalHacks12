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

def get_websearch_info(args: Dict[str, Any]) -> Dict[str, Any]:
    query = args.get("query", "")
    url = "https://calc-origin-nozzle.flows.pstmn.io/api/default/websearchagent"
    
    response = requests.post(url, json={"message": query}, timeout=10)
    result = response.text
    
    return {"message": result}




def get_crypto_info(args: Dict[str, Any]) -> Dict[str, Any]:
    query = args.get("query", "")
    url = "https://calc-origin-nozzle.flows.pstmn.io/api/default/cryptoagent"
    
    response = requests.post(url, json={"message": query}, timeout=30)
    result = response.text
    
    return {"message": result}


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


def make_transaction(args: Dict[str, Any]) -> Dict[str, Any]:
    recipient = args.get("recipient", "0x3f6bb1bdaaacafd020194d452a5a1afce89114cd5fafa3aebc9b214e83aa2ef2")
    amount = args.get("amount", "0.001")
    url = "http://localhost:3000/api/cryptobot/send"
    
    payload = {
        "recipient": recipient,
        "amount": str(amount)
    }
    
    response = requests.post(url, json=payload, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        return {
            "success": True,
            "digest": data.get("digest", ""),
            "from": data.get("from", ""),
            "to": data.get("to", ""),
            "amount": data.get("amount", ""),
            "explorer": data.get("explorer", ""),
            "message": f"Transaction sent! Hash: {data.get('digest', 'unknown')}"
        }
    else:
        return {
            "success": False,
            "message": f"Transaction failed with status {response.status_code}"
        }


def send_crypto_to_anthony(args: Dict[str, Any]) -> Dict[str, Any]:
    """Send 0.001 crypto to Anthony's address - hackathon demo version"""
    anthony_address = "0x3f6bb1bdaaacafd020194d452a5a1afce89114cd5fafa3aebc9b214e83aa2ef2"
    amount = 0.001
    
    # For hackathon demo - just simulate the transaction
    print(f"🔧 [Crypto Tool Called] Sending {amount} crypto to Anthony's address: {anthony_address}")
    
    # Simulate API call (replace with actual API when ready)
    try:
        # This would be the actual API call when implemented
        # response = requests.post("https://crypto-bot-landing-page.vercel.app/api/cryptobot/send", 
        #                        json={"recipient": anthony_address, "amount": amount})
        
        # For demo purposes, simulate success
        return {
            "success": True,
            "recipient": anthony_address,
            "amount": amount,
            "transaction_id": "demo_tx_12345",
            "message": f"✅ Crypto transaction initiated! Sending {amount} to Anthony's address. Transaction ID: demo_tx_12345"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to send crypto to Anthony: {str(e)}"
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
    "get_websearch_info": get_websearch_info,
    "get_crypto_info": get_crypto_info,
    "get_weather": get_weather,
    "make_transaction": make_transaction,
    "send_crypto_to_anthony": send_crypto_to_anthony,
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
        "name": "get_websearch_info",
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    },
    {
        "type": "function",
        "name": "get_crypto_info",
        "description": "Get cryptocurrency information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The crypto query (e.g., 'Bitcoin price', 'ETH')"
                }
            },
            "required": ["query"]
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
        "name": "make_transaction",
        "description": "Send SUI cryptocurrency to a recipient",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "description": "The SUI address to send to (must start with 0x)"
                },
                "amount": {
                    "type": "string",
                    "description": "Amount of SUI to send (e.g., '0.001', '1.5')"
                }
            },
            "required": ["recipient", "amount"]
        }
    },
    {
        "type": "function",
        "name": "send_crypto_to_anthony",
        "description": "Send 0.001 crypto to Anthony's address for hackathon demo",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
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

