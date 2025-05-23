# routers/chat.py
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse # Import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import httpx # Sử dụng httpx cho async requests
import json
import numpy as np
# from sqlalchemy.orm import Session # Bạn không dùng SQLAlchemy Session, mà là raw DB connection
# database.py của bạn cung cấp raw connection, không phải SQLAlchemy Session
from database import get_db # get_db trả về một DB connection, không phải SQLAlchemy Session
from utils.auth_utils import get_current_user
from utils.embedding import get_embedding # Đảm bảo hàm này trả về numpy array
from config import Config

import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

class ChatRequest(BaseModel):
    question: str
    use_context: bool = True
    department: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []

class ContextChunk(BaseModel):
    content: str
    filename: str
    score: float

# db ở đây là một đối tượng connection từ pool (ví dụ CMySQLConnection)
def get_relevant_context(
    question: str,
    user_id: int,
    department: Optional[str],
    db_conn, # Đổi tên biến db thành db_conn để rõ ràng hơn nó là connection
    top_k: int = 5
) -> List[ContextChunk]:
    """Retrieve relevant context from embeddings database"""
    cursor = None # Khởi tạo cursor để đảm bảo có thể đóng
    try:
        logger.info(f"Retrieving context for question: '{question[:50]}...' for user_id: {user_id}")
        # Get embedding for the question
        question_embedding = get_embedding(question)
        if not isinstance(question_embedding, np.ndarray):
            logger.warning("Question embedding is not a numpy array. Attempting conversion.")
            question_embedding = np.array(question_embedding)
        if question_embedding.ndim == 0 or question_embedding.size == 0: # Kiểm tra embedding rỗng
            logger.error("Failed to generate or received empty question embedding.")
            return []


        # Build query based on user access
        # Giả sử bảng embeddings có cột document_id, chunk, vector (kiểu TEXT hoặc BLOB)
        # và bảng documents có id, filename, user_id, is_public, department
        query_parts = [
            "SELECT e.chunk, e.vector, d.filename, d.department",
            "FROM embeddings e",
            "JOIN documents d ON e.document_id = d.id"
        ]
        conditions = ["(d.user_id = %s OR d.is_public = TRUE)"]
        params = [user_id]

        if department:
            conditions.append("d.department = %s")
            params.append(department)

        query_parts.append(f"WHERE {' AND '.join(conditions)}")
        final_query = "\n".join(query_parts)

        logger.debug(f"Context query: {final_query} with params: {params}")

        # SỬA LỖI Ở ĐÂY:
        # cursor = db.connection.cursor() # DÒNG CŨ GÂY LỖI
        cursor = db_conn.cursor(dictionary=True) # SỬA: db_conn chính là connection, dùng dictionary=True
        cursor.execute(final_query, tuple(params)) # params cần là tuple
        results = cursor.fetchall()

        if not results:
            logger.info("No raw context results found from database.")
            return []
        logger.info(f"Found {len(results)} raw context results from database.")

        # Calculate similarity scores
        chunks_with_scores = []
        for row in results:
            chunk_text = row['chunk']
            vector_str = row['vector'] # Giả sử vector lưu trữ dạng JSON string
            filename = row['filename']

            try:
                # Parse vector from string (cần cẩn thận với định dạng lưu trữ)
                # Nếu vector_str là bytes, cần decode trước: vector_list = json.loads(vector_str.decode('utf-8'))
                # Nếu là TEXT:
                vector_list = json.loads(vector_str)
                chunk_vector = np.array(vector_list)

                if chunk_vector.ndim == 0 or chunk_vector.size == 0 or chunk_vector.shape != question_embedding.shape:
                    logger.warning(f"Skipping chunk from '{filename}' due to invalid or mismatched embedding shape. Chunk vec shape: {chunk_vector.shape}, Q vec shape: {question_embedding.shape}")
                    continue

                # Calculate cosine similarity
                # Đảm bảo không chia cho 0 nếu vector là zero vector
                norm_q = np.linalg.norm(question_embedding)
                norm_c = np.linalg.norm(chunk_vector)

                if norm_q == 0 or norm_c == 0:
                    similarity = 0.0
                    logger.warning(f"Zero norm vector encountered for chunk from '{filename}'. Similarity set to 0.")
                else:
                    similarity = np.dot(question_embedding, chunk_vector) / (norm_q * norm_c)

                chunks_with_scores.append({
                    'content': chunk_text,
                    'filename': filename,
                    'score': float(similarity)
                })
            except json.JSONDecodeError as jde:
                logger.error(f"Failed to decode JSON vector string for chunk from '{filename}': {jde}. Vector string: '{vector_str[:100]}...'")
            except Exception as e_sim:
                logger.error(f"Error calculating similarity for chunk from '{filename}': {e_sim}")

        # Sort by score and return top k
        chunks_with_scores.sort(key=lambda x: x['score'], reverse=True)
        logger.info(f"Returning {min(top_k, len(chunks_with_scores))} context chunks after similarity calculation.")

        return [
            ContextChunk(**chunk)
            for chunk in chunks_with_scores[:top_k]
        ]

    except Exception as e:
        import traceback
        logger.error(f"Error retrieving context: {e}\n{traceback.format_exc()}")
        return [] # Trả về rỗng nếu có lỗi, không raise ở đây để chat vẫn có thể tiếp tục không context
    finally:
        if cursor:
            cursor.close()
        # Không đóng db_conn ở đây vì nó được quản lý bởi Depends(get_db)


# Sử dụng httpx cho async requests
async def call_ollama_chat(messages: List[dict], stream: bool = False) -> str:
    """Call Ollama chat API asynchronously"""
    api_url = f"{Config.OLLAMA_URL.rstrip('/')}/api/chat" # Đảm bảo URL đúng
    logger.info(f"Calling Ollama API: {api_url} with model: {Config.OLLAMA_MODEL}")
    payload = {
        "model": Config.OLLAMA_MODEL,
        "messages": messages,
        "stream": stream, # stream sẽ được xử lý bởi hàm gọi nếu là True
        "options": {
            "temperature": 0.7, # Ví dụ các options
            "top_p": 0.9,
            # "num_ctx": 4096 # Tùy chỉnh context window nếu cần
        }
    }
    logger.debug(f"Ollama payload: {json.dumps(payload, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=Config.OLLAMA_TIMEOUT) as client: # Sử dụng Config.OLLAMA_TIMEOUT
            response = await client.post(
                api_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

        # Log chi tiết hơn về response
        logger.debug(f"Ollama response status: {response.status_code}")
        if response.status_code != 200:
            response_text = response.text
            logger.error(f"Ollama API error: {response.status_code} - {response_text}")
            # Phân tích lỗi từ Ollama nếu có thể
            try:
                error_detail = response.json().get("error", response_text)
            except json.JSONDecodeError:
                error_detail = response_text
            raise HTTPException(
                status_code=response.status_code if response.status_code >= 400 else status.HTTP_502_BAD_GATEWAY,
                detail=f"Ollama API error: {error_detail}"
            )

        result = response.json()
        logger.debug(f"Ollama response JSON: {result}")
        # Cấu trúc response của /api/chat (non-streaming):
        # {"model":"mistral","created_at":"...","message":{"role":"assistant","content":"..."},"done":true,...}
        if "message" in result and "content" in result["message"]:
            return result["message"]["content"].strip()
        else:
            logger.error(f"Unexpected response structure from Ollama: {result}")
            return "Error: No valid response content from model."

    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to Ollama service at {Config.OLLAMA_URL}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot connect to Ollama service at {Config.OLLAMA_URL}. Please ensure Ollama is running."
        )
    except httpx.TimeoutException as e:
        logger.error(f"Ollama request timeout: {e}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Ollama request timeout. The model might be loading or the request is too complex."
        )
    except httpx.HTTPStatusError as e: # Bắt lỗi từ response.raise_for_status() nếu dùng
        logger.error(f"Ollama API HTTPStatusError: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Ollama API error: {e.response.text}"
        )
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error calling Ollama: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while communicating with Ollama: {str(e)}"
        )


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user), # Giả định trả về dict có 'id' và 'username'
    db_conn = Depends(get_db) # db_conn sẽ là đối tượng connection
):
    """Ask a question to the chatbot"""
    try:
        user_id = current_user.get('id')
        username = current_user.get('username', 'unknown_user')
        if not user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User ID not found in token.")

        logger.info(f"User '{username}' (ID: {user_id}) asking: '{request.question[:100]}...' with use_context={request.use_context}, department='{request.department}'")

        messages = []
        sources = []

        if request.use_context:
            context_chunks = get_relevant_context(
                question=request.question,
                user_id=user_id,
                department=request.department,
                db_conn=db_conn, # Truyền db_conn
                top_k=Config.OLLAMA_TOP_K_CONTEXT if hasattr(Config, 'OLLAMA_TOP_K_CONTEXT') else 3 # Lấy top_k từ config nếu có
            )

            if context_chunks:
                context_str_parts = []
                for i, chunk in enumerate(context_chunks):
                    context_str_parts.append(f"Context [{i+1}] from \"{chunk.filename}\":\n{chunk.content}")
                context_str = "\n\n".join(context_str_parts)

                messages.append({
                    "role": "system",
                    "content": f"""You are a helpful AI assistant. Answer the user's question based on the provided context.
If the information is not in the context, state that you cannot find the answer in the provided documents and try to answer generally if appropriate.
Be concise and helpful. Cite the source filenames if you use information from them, for example: (Source: filename.txt).

Provided Context:
---
{context_str}
---
"""
                })
                sources = sorted(list(set([chunk.filename for chunk in context_chunks])))
                logger.info(f"Using {len(context_chunks)} context chunks from {len(sources)} sources: {sources}")
            else:
                logger.info("No relevant context found for the question.")
                messages.append({
                    "role": "system",
                    "content": "You are a helpful AI assistant. No specific context documents were found relevant to the user's question. Answer generally if possible."
                })
        else:
            logger.info("Context usage is disabled for this question.")
            messages.append({
                "role": "system",
                "content": "You are a helpful AI assistant."
            })

        messages.append({
            "role": "user",
            "content": request.question
        })

        answer = await call_ollama_chat(messages) # Sử dụng await vì call_ollama_chat giờ là async

        # Thêm logic để trích xuất sources từ câu trả lời của LLM nếu LLM được huấn luyện để làm vậy.
        # Ví dụ, nếu LLM trả lời "Theo tài liệu X, thì..."

        return ChatResponse(
            answer=answer,
            sources=sources # Hiện tại sources lấy từ context đã tìm được
        )

    except HTTPException:
        raise # Re-raise HTTPException đã được xử lý
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error in ask_question for user '{current_user.get('username', 'unknown')}': {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Check if chat service and Ollama are healthy"""
    ollama_status = {
        "status": "unhealthy",
        "connection": "disconnected",
        "error": "Not checked"
    }
    try:
        api_url = f"{Config.OLLAMA_URL.rstrip('/')}/api/tags"
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(api_url)

        if response.status_code == 200:
            models_data = response.json().get('models', [])
            model_names = [m['name'] for m in models_data]
            model_target = Config.OLLAMA_MODEL if ':' in Config.OLLAMA_MODEL else f"{Config.OLLAMA_MODEL}:latest"
            model_available = any(m.startswith(Config.OLLAMA_MODEL) for m in model_names)


            ollama_status.update({
                "status": "healthy",
                "connection": "connected",
                "target_model": Config.OLLAMA_MODEL,
                "model_available": model_available,
                "available_models_on_ollama": model_names,
                "error": None
            })
            if not model_available:
                 ollama_status["warning"] = f"Target model '{Config.OLLAMA_MODEL}' not found in available models. Ensure it's pulled."

        else:
            ollama_status.update({
                "connection": "error",
                "error": f"Ollama API at {api_url} returned status {response.status_code} - {response.text}"
            })

    except httpx.ConnectError:
        ollama_status.update({
            "error": f"Cannot connect to Ollama service at {Config.OLLAMA_URL}"
        })
    except httpx.TimeoutException:
        ollama_status.update({
            "connection": "timeout",
            "error": f"Timeout connecting to Ollama service at {Config.OLLAMA_URL}"
        })
    except Exception as e:
        ollama_status.update({
            "error": str(e)
        })

    return {
        "service_status": "healthy" if ollama_status["status"] == "healthy" else "degraded",
        "ollama_details": ollama_status
    }


@router.post("/ask_stream", summary="Ask a question with a streaming response")
async def ask_question_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db_conn = Depends(get_db)
):
    """
    Hỏi một câu hỏi và nhận phản hồi dưới dạng stream.
    Hữu ích cho các câu trả lời dài từ mô hình.
    """
    try:
        user_id = current_user.get('id')
        username = current_user.get('username', 'unknown_user')
        if not user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User ID not found in token.")

        logger.info(f"Streaming request from user '{username}' (ID: {user_id}): '{request.question[:100]}...'")

        messages = []
        # Xây dựng messages tương tự như ask_question
        if request.use_context:
            context_chunks = get_relevant_context(
                question=request.question,
                user_id=user_id,
                department=request.department,
                db_conn=db_conn,
                top_k=Config.OLLAMA_TOP_K_CONTEXT if hasattr(Config, 'OLLAMA_TOP_K_CONTEXT') else 3
            )
            if context_chunks:
                context_str_parts = [f"Context [{i+1}] from \"{c.filename}\":\n{c.content}" for i, c in enumerate(context_chunks)]
                context_str = "\n\n".join(context_str_parts)
                system_prompt = f"""You are a helpful AI assistant. Answer the user's question based on the provided context.
If the information is not in the context, state that you cannot find the answer in the provided documents.
Provided Context:
---
{context_str}
---
"""
                messages.append({"role": "system", "content": system_prompt})
                logger.info(f"Using {len(context_chunks)} context chunks for streaming response.")
            else:
                messages.append({"role": "system", "content": "You are a helpful AI assistant. No specific context was found."})
        else:
            messages.append({"role": "system", "content": "You are a helpful AI assistant."})

        messages.append({"role": "user", "content": request.question})

        api_url = f"{Config.OLLAMA_URL.rstrip('/')}/api/chat"
        payload = {
            "model": Config.OLLAMA_MODEL,
            "messages": messages,
            "stream": True, # Yêu cầu streaming từ Ollama
            "options": {"temperature": 0.7, "top_p": 0.9}
        }
        logger.debug(f"Ollama stream payload: {json.dumps(payload, indent=2)}")

        async def event_generator():
            try:
                async with httpx.AsyncClient(timeout=Config.OLLAMA_TIMEOUT) as client:
                    async with client.stream("POST", api_url, json=payload, headers={"Content-Type": "application/json"}) as response:
                        if response.status_code != 200:
                            # Đọc toàn bộ lỗi nếu có thể để log
                            error_content = await response.aread()
                            logger.error(f"Ollama stream API error: {response.status_code} - {error_content.decode()}")
                            yield f"data: {json.dumps({'error': 'Ollama API error', 'detail': error_content.decode()})}\n\n"
                            return

                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    json_response = json.loads(line)
                                    # Cấu trúc của streaming response từ /api/chat:
                                    # mỗi line là một JSON object, ví dụ:
                                    # {"model":"mistral","created_at":"...","message":{"role":"assistant","content":"..."}"done":false}
                                    # Khi done=true, message có thể không có content, hoặc content là ""
                                    if json_response.get("done") is False and "message" in json_response and "content" in json_response["message"]:
                                        content_part = json_response["message"]["content"]
                                        # logger.debug(f"Stream chunk: {content_part}")
                                        # Gửi dưới dạng Server-Sent Events (SSE)
                                        yield f"data: {json.dumps({'token': content_part})}\n\n"
                                    elif json_response.get("done") is True:
                                        logger.info("Ollama stream finished.")
                                        # Có thể gửi một thông điệp kết thúc nếu cần
                                        # yield f"data: {json.dumps({'event': 'done'})}\n\n"
                                        break # Kết thúc generator
                                except json.JSONDecodeError:
                                    logger.warning(f"Could not decode JSON line from Ollama stream: {line}")
                                except Exception as stream_e:
                                    logger.error(f"Error processing Ollama stream line: {stream_e}")
                                    yield f"data: {json.dumps({'error': 'Stream processing error', 'detail': str(stream_e)})}\n\n"
            except httpx.HTTPError as http_err: # Bao gồm ConnectError, TimeoutException
                logger.error(f"HTTPError during Ollama stream connection: {http_err}")
                yield f"data: {json.dumps({'error': 'Ollama connection error', 'detail': str(http_err)})}\n\n"
            except Exception as e:
                logger.error(f"Unexpected error in event_generator: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': 'Unexpected stream error', 'detail': str(e)})}\n\n"
            finally:
                # Đảm bảo gửi một dấu hiệu kết thúc (tùy thuộc vào cách client xử lý SSE)
                # logger.info("Event generator finished.")
                pass


        # Sử dụng media_type='text/event-stream' cho Server-Sent Events
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error setting up streaming response: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred while setting up the stream: {str(e)}"
        )