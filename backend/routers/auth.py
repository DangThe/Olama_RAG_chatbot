"""
Authentication router
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from database import execute_query
from utils.auth_utils import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])

class AuthBody(BaseModel):
    username: str
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: AuthBody):
    """
    Đăng ký người dùng mới
    """
    # Kiểm tra xem tài khoản đã tồn tại chưa
    existing_user = execute_query(
        "SELECT id FROM users WHERE username = %s", 
        (body.username,)
    )
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên người dùng đã tồn tại"
        )
    
    # Hash mật khẩu và lưu vào database
    hashed_password = hash_password(body.password)
    
    try:
        user_id = execute_query(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (body.username, hashed_password),
            fetch=False
        )
        
        return {"message": "Đăng ký thành công", "user_id": user_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi đăng ký: {str(e)}"
        )

@router.post("/login")
def login(body: AuthBody):
    """
    Đăng nhập và trả về JWT token
    """
    # Lấy thông tin người dùng từ database
    users = execute_query(
        "SELECT id, username, password_hash FROM users WHERE username = %s",
        (body.username,)
    )
    
    if not users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )
    
    user = users[0]
    
    # Xác thực mật khẩu
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )
    
    # Tạo JWT token
    access_token = create_access_token(
        data={"id": user["id"], "username": user["username"]}
    )
    
    return {"token": access_token}