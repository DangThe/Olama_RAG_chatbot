from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, files, chat

app = FastAPI()

# ✅ CHỈ cấu hình như sau — KHÔNG dùng "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "RAG Chatbot backend is running"}
	
	# Trong main.py, nếu bạn khởi động server từ mã
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        timeout_keep_alive=120  # Tăng thời gian keepalive
    )
