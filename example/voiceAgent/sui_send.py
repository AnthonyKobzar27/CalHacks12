import requests
import json

def test_api():
    """Test the production API endpoint"""
    API_URL = 'https://crypto-bot-landing-page.vercel.app/api/cryptobot/send'
    
    try:
        print('🚀 Testing production API endpoint...')
        print('📍 URL:', API_URL)
        
        # Test the POST request
        print('\n🔍 Testing POST request...')
        post_data = {
            'recipient': '0x3f6bb1bdaaacafd020194d452a5a1afce89114cd5fafa3aebc9b214e83aa2ef2',
            'amount': 0.001
        }
        print('POST Data:', json.dumps(post_data, indent=2))

        response = requests.post(
            API_URL,
            headers={
                'Content-Type': 'application/json',
            },
            json=post_data
        )

        print('POST Status:', response.status_code)
        print('POST Headers:', dict(response.headers))
        
        print('POST Response:', response.text)

        if not response.ok:
            raise Exception(f'API Error: {response.status_code} - {response.text}')

        try:
            data = response.json()
            print('\n✅ Parsed Response:', json.dumps(data, indent=2))
        except json.JSONDecodeError:
            print('❌ Could not parse response as JSON')

    except Exception as error:
        print('❌ Test failed:', error)

if __name__ == '__main__':
    test_api()
