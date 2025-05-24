# --- START OF FILE main.py ---

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn # Thêm import uvicorn
import os # Thêm import os để có thể sử dụng getenv nếu Config không có sẵn ngay

# Cố gắng import Config, nếu không được thì dùng giá trị mặc định cho origins
try:
    from config import Config
    # CORS_ORIGINS_STR được mong đợi là một chuỗi các URL cách nhau bởi dấu phẩy
    # ví dụ: "http://localhost:3000,http://localhost:3001,https://yourdomain.com"
    # Hoặc là một list đã được xử lý sẵn trong Config
    if hasattr(Config, 'CORS_ORIGINS') and isinstance(Config.CORS_ORIGINS, list):
        configured_origins = Config.CORS_ORIGINS
    elif hasattr(Config, 'CORS_ORIGINS_STR') and Config.CORS_ORIGINS_STR:
        configured_origins = [origin.strip() for origin in Config.CORS_ORIGINS_STR.split(',')]
    else: # Fallback nếu Config không có các thuộc tính mong đợi
        configured_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        configured_origins = [origin.strip() for origin in configured_origins_env.split(',')]
except ImportError:
    print("Warning: config.py not found or Config class cannot be imported. Using default CORS origins.")
    # Lấy trực tiếp từ biến môi trường nếu Config không import được
    configured_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    configured_origins = [origin.strip() for origin in configured_origins_env.split(',')]

# Routers
from routers import auth, files, chat
# from routers import settings_admin # Bỏ comment nếu bạn đã tạo router này

app = FastAPI(
    title="RAG Chatbot API",
    description="API cho ứng dụng RAG Chatbot với Ollama.",
    version="0.1.0"
)

# Cấu hình CORS
# Sử dụng configured_origins đã được chuẩn bị ở trên
# Đảm bảo origins không rỗng, nếu rỗng thì fallback
origins_to_allow = configured_origins if configured_origins and configured_origins[0] else ["http://localhost:3000"]

print(f"INFO:     Configuring CORS with origins: {origins_to_allow}") # Log ra để kiểm tra

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_to_allow,  # Danh sách các origin được phép
    allow_credentials=True,          # Cho phép gửi cookie (nếu có)
    allow_methods=["*"],             # Cho phép tất cả các method (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],             # Cho phép tất cả các header
)

# Mount routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(chat.router)
# if 'settings_admin' in locals() and hasattr(settings_admin, 'router'):
#     app.include_router(settings_admin.router) # Thêm router quản lý settings nếu có

@app.get("/", tags=["Root"])
async def read_root(): # Nên là async def cho các route FastAPI
    return {"message": "RAG Chatbot backend is running"}

# Trong main.py, nếu bạn khởi động server từ mã
if __name__ == "__main__":
    # Cấu hình logging cho uvicorn nếu cần (uvicorn có config riêng)
    # import logging
    # logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger("uvicorn.error") # Hoặc "uvicorn.access"
    # logger.setLevel(logging.DEBUG) # Ví dụ

    print("INFO:     Starting Uvicorn server...")
    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"), # Lấy host từ env, mặc định 0.0.0.0
        port=int(os.getenv("BACKEND_PORT", 8000)), # Lấy port từ env, mặc định 8000
        reload=True, # Chỉ nên True trong môi trường development
        # workers=1, # Số lượng worker processes, thường chỉ đặt khi không dùng reload
        log_level="info", # Mức độ log của uvicorn (debug, info, warning, error, critical)
        timeout_keep_alive=120  # Tăng thời gian keepalive
    )

# --- END OF FILE main.py ---