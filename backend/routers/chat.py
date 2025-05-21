"""
Chat router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import json
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
from config import OLLAMA_URL, OLLAMA_MODEL, EMBEDDING_MODEL
from database import execute_query
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatBody(BaseModel):
    messages: list

def cosine_similarity(v1, v2):
    """Calculate cosine similarity between two vectors"""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

@router.post("/ask")
def ask_chat(body: ChatBody, current_user=Depends(get_current_user)):
    """
    Gửi câu hỏi cho chatbot và trả về phản hồi
    """
    # Lấy câu hỏi từ tin nhắn cuối cùng
    question = body.messages[-1]['content']
    
    # Tạo vector embedding cho câu hỏi
    try:
        model = SentenceTransformer(EMBEDDING_MODEL)
        question_vector = model.encode([question])[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tạo embedding: {str(e)}"
        )
    
    # Lấy embeddings từ database
    documents = execute_query(
        """
        SELECT chunk, vector 
        FROM embeddings 
        INNER JOIN documents ON embeddings.document_id = documents.id 
        WHERE documents.user_id = %s OR documents.is_public = TRUE
        """,
        (current_user['id'],)
    )
    
    if not documents:
        # Không có tài liệu nào trong database
        return {"reply": "Không tìm thấy tài liệu phù hợp. Vui lòng tải tài liệu lên trước khi hỏi."}
    
    # Tính độ tương đồng và chọn các đoạn văn có liên quan nhất
    similarities = []
    for doc in documents:
        try:
            doc_vector = json.loads(doc['vector'])
            similarity = cosine_similarity(question_vector, doc_vector)
            similarities.append((similarity, doc['chunk']))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Lỗi khi xử lý vector: {e}")
            continue
    
    # Sắp xếp theo độ tương đồng và lấy top N
    similarities.sort(reverse=True)
    top_chunks = similarities[:3]
    
    if not top_chunks:
        return {"reply": "Không thể tìm thấy thông tin liên quan trong tài liệu."}
    
    # Kết hợp các đoạn văn để tạo ngữ cảnh
    context = "\n\n".join([chunk[1] for chunk in top_chunks])
    
    # Gửi yêu cầu đến Ollama
    try:
        response = requests.post(
            f"{OLLAMA_URL}/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": "Dựa trên nội dung tài liệu dưới đây, hãy trả lời câu hỏi. Nếu không có thông tin liên quan, hãy thành thật nói rằng không tìm thấy thông tin."},
                    {"role": "user", "content": f"Văn bản: {context}\n\nCâu hỏi: {question}"}
                ],
                "stream": False
            },
            timeout=30
        )
        
        # Xử lý phản hồi
        if response.status_code == 200:
            data = response.json()
            return {"reply": data.get("message", {}).get("content", "Không nhận được phản hồi")}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi khi gọi API Ollama: {response.status_code}"
            )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi kết nối đến Ollama: {str(e)}"
        )