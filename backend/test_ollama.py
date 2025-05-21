import os
import sys
import requests
from dotenv import load_dotenv
import traceback
import json

# Tải biến môi trường
load_dotenv()

# Lấy cấu hình Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

def test_ollama_connection():
    print("🔍 Kiểm tra kết nối Ollama")
    print(f"URL: {OLLAMA_URL}")
    print(f"Model: {OLLAMA_MODEL}")

    try:
        # Thử chat
        chat_response = requests.post(
            f"{OLLAMA_URL}/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "user", "content": "Xin chào, giới thiệu về bản thân"}
                ],
                "stream": False
            },
            timeout=10
        )
        
        print("\n📬 Thử gọi chat API:")
        print(f"Status Code: {chat_response.status_code}")
        
        if chat_response.status_code == 200:
            response_data = chat_response.json()
            print("✅ Nhận được phản hồi từ Ollama!")
            print("Phản hồi chi tiết:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Lỗi: {chat_response.text}")

    except requests.ConnectionError as e:
        print("❌ Lỗi kết nối: Không thể kết nối tới Ollama")
        print(f"Chi tiết: {e}")
        traceback.print_exc()

    except requests.Timeout:
        print("❌ Lỗi: Hết thời gian kết nối")

    except requests.RequestException as e:
        print(f"❌ Lỗi request: {e}")
        traceback.print_exc()

    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_ollama_connection()