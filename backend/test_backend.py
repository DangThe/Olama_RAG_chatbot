import os
import sys
import requests
from dotenv import load_dotenv
import json

# Tải biến môi trường
load_dotenv()

def test_backend_connection():
    print("🔍 Kiểm tra kết nối Backend")
    
    # Giả sử backend chạy trên localhost:8000
    BACKEND_URL = "http://localhost:8000"
    
    try:
        # Thử kết nối root endpoint
        root_response = requests.get(f"{BACKEND_URL}/")
        print("✅ Kết nối root endpoint thành công!")
        print("Phản hồi:")
        print(json.dumps(root_response.json(), indent=2, ensure_ascii=False))
        
        # Nếu có endpoint chat, thử kết nối
        # LƯU Ý: Cần có token để test
        # Thay YOUR_TOKEN bằng token thực tế
        chat_response = requests.post(
            f"{BACKEND_URL}/chat/ask", 
            json={
                "messages": [{"role": "user", "content": "Xin chào"}]
            },
            headers={
                "Authorization": "Bearer YOUR_TOKEN",
                "Content-Type": "application/json"
            }
        )
        
        print("\n📬 Thử gọi chat API:")
        print(f"Status Code: {chat_response.status_code}")
        print("Phản hồi:")
        print(json.dumps(chat_response.json(), indent=2, ensure_ascii=False))
        
    except requests.ConnectionError:
        print("❌ Không thể kết nối tới Backend")
    
    except requests.RequestException as e:
        print(f"❌ Lỗi request: {e}")

if __name__ == "__main__":
    test_backend_connection()