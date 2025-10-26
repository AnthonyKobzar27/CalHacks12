import requests
import bech32
from typing import Dict, Any

def send_sui() -> Dict[str, Any]:
    """
    Hardcoded function to send 0.001 SUI to a specific address using Sui JSON-RPC
    """
    try:
        # Hardcoded values
        private_key = ""
        recipient = "0x3f6bb1bdaaacafd020194d452a5a1afce89114cd5fafa3aebc9b214e83aa2ef2"
        amount = 0.001  # in SUI
        
        # Sui RPC endpoint
        rpc_url = "https://fullnode.testnet.sui.io:443"
        
        # Decode private key from bech32 (matching JS version exactly)
        hrp, words = bech32.bech32_decode(private_key)
        if words is None:
            raise Exception("Invalid private key format")
            
        # Convert from 5-bit to 8-bit encoding
        decoded_bytes = bech32.convertbits(words, 5, 8, False)
        if decoded_bytes is None:
            raise Exception("Error converting private key bits")
            
        # Remove first byte as done in JS version
        key_bytes = bytes(decoded_bytes)[1:]
        
        print(f"🔑 Decoded private key:")
        print(f"  - HRP: {hrp}")
        print(f"  - Key bytes (hex): {key_bytes.hex()}")
        
        # First, get the gas objects owned by the sender
        get_coins_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "suix_getCoins",
            "params": [
                key_bytes.hex(),  # address
                "0x2::sui::SUI",  # coin type
            ]
        }
        
        print("🔍 Getting available coins...")
        coins_response = requests.post(rpc_url, json=get_coins_payload)
        coins_result = coins_response.json()
        print(f"💰 Coins response: {coins_result}")
        
        if "error" in coins_result:
            raise Exception(f"Failed to get coins: {coins_result['error']['message']}")
            
        coins = coins_result["result"]["data"]
        if not coins:
            raise Exception("No coins available")
            
        # Create pay transaction
        amount_mist = int(amount * 1_000_000_000)  # Convert to MIST
        
        pay_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sui_pay",
            "params": [
                key_bytes.hex(),  # sender address
                [coins[0]["coinObjectId"]],  # input coins
                [recipient],  # recipients
                [str(amount_mist)],  # amounts
                None,  # gas coin
                2000,  # gas budget
                "testnet"  # network
            ]
        }
        
        print(f"💰 Preparing to send {amount} SUI to {recipient}")
        print(f"📡 Sending request to {rpc_url}")
        print(f"📦 Payload: {pay_payload}")
        
        # Make the RPC call
        response = requests.post(rpc_url, json=pay_payload)
        result = response.json()
        
        print(f"📡 API Response: {result}")
        
        if "error" in result:
            raise Exception(result["error"]["message"])
            
        tx_digest = result["result"]["digest"]
        explorer_url = f"https://suiexplorer.com/txblock/{tx_digest}?network=testnet"
        
        print("✅ Transaction successful!")
        print(f"📝 Transaction hash: {tx_digest}")
        print(f"🔗 View on Explorer: {explorer_url}")
        
        return {
            "success": True,
            "digest": tx_digest,
            "explorer_url": explorer_url
        }
        
    except Exception as e:
        print(f"❌ Transaction failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# Run the function
if __name__ == "__main__":
    result = send_sui()
    print("\nResult:", result)