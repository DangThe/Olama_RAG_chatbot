# test_ollama.py
import requests
import json

OLLAMA_URL = "http://localhost:11434"

def test_ollama():
    print("=" * 50)
    print("Testing Ollama Connection")
    print("=" * 50)
    
    # Test 1: Basic connection
    print("\n1. Testing basic connection...")
    try:
        response = requests.get(f"{OLLAMA_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}...")
    except Exception as e:
        print(f"   ERROR: {e}")
        print("   -> Ollama có thể chưa chạy. Hãy chạy 'ollama serve' trong terminal")
        return
    
    # Test 2: List models
    print("\n2. Getting available models...")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"   Found {len(models)} models:")
            for model in models:
                print(f"   - {model['name']} (size: {model.get('size', 'unknown')})")
        else:
            print(f"   ERROR: Status {response.status_code}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 3: Test chat endpoint
    print("\n3. Testing chat endpoint with mistral...")
    try:
        payload = {
            "model": "mistral",
            "messages": [
                {"role": "user", "content": "Hello, just testing. Reply with 'OK' only."}
            ],
            "stream": False
        }
        
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', {}).get('content', 'No content')
            print(f"   Response: {message[:100]}...")
        else:
            print(f"   Error response: {response.text}")
            
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test 4: Check if model exists
    print("\n4. Checking if 'mistral' model is installed...")
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/show",
            json={"name": "mistral"}
        )
        if response.status_code == 200:
            print("   ✓ Model 'mistral' is installed")
        else:
            print("   ✗ Model 'mistral' not found")
            print("   -> Run: ollama pull mistral")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_ollama()