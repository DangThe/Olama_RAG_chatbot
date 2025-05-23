# Trong file routers/chat.py
import requests
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
import time
import asyncio
from config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT  # Import OLLAMA_TIMEOUT từ config

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/ask")
async def ask_question(request_data: Dict[str, Any]):
    try:
        question = request_data.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Tạo payload cho Ollama
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": question,
            "stream": False  # Đặt thành False để nhận toàn bộ phản hồi một lần
        }
        
        # Log để debug
        print(f"Sending request to Ollama: {OLLAMA_URL}/generate")
        print(f"Payload: {payload}")
        print(f"Using timeout: {OLLAMA_TIMEOUT} seconds")
        
        # Gọi đến Ollama API với timeout đã tăng
        start_time = time.time()
       if OLLAMA_URL.endswith('/api'):
		full_url = f"{OLLAMA_URL}/generate"
			else:
		full_url = f"{OLLAMA_URL}/api/generate"

		print(f"Fixed URL: {full_url}")

		response = requests.post(
		full_url,
		json=payload,
		timeout=OLLAMA_TIMEOUT
		)
        end_time = time.time()
        print(f"Ollama response time: {end_time - start_time:.2f} seconds")
        
        # Kiểm tra phản hồi
        if response.status_code != 200:
            print(f"Ollama error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, 
                               detail=f"Error from Ollama: {response.status_code} - {response.text}")
        
        # Lấy dữ liệu phản hồi
        response_data = response.json()
        answer = response_data.get("response", "Sorry, I couldn't generate a response.")
        
        return {"answer": answer}
    
    except requests.Timeout:
        print("Ollama request timed out after", OLLAMA_TIMEOUT, "seconds")
        raise HTTPException(status_code=504, 
                           detail=f"Request to language model timed out after {OLLAMA_TIMEOUT} seconds. Try a shorter question.")
    
    except requests.ConnectionError as e:
        print(f"Ollama connection error: {str(e)}")
        raise HTTPException(status_code=503, 
                           detail="Cannot connect to Ollama. Please ensure Ollama is running.")
    
    except requests.RequestException as e:
        print(f"Ollama request error: {str(e)}")
        raise HTTPException(status_code=500, 
                           detail=f"Error connecting to language model: {str(e)}")
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()  # In stack trace đầy đủ để debug
        raise HTTPException(status_code=500, 
                           detail=f"Unexpected error: {str(e)}")