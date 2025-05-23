# --- START OF FILE auth_utils.py ---

"""
Utility functions for authentication
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt # Thư viện PyJWT
from datetime import datetime, timedelta, timezone # Nên dùng timezone.utc cho datetime
import bcrypt
# from config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES # DÒNG CŨ GÂY LỖI
from config import Config # <--- SỬA ĐỔI: Import class Config

auth_scheme = HTTPBearer()

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hashed password
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    """
    Create JWT token
    """
    to_encode = data.copy()
    # Sử dụng timezone.utc để đảm bảo tính nhất quán
    # Truy cập ACCESS_TOKEN_EXPIRE_MINUTES qua Config
    expire = datetime.now(timezone.utc) + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Truy cập JWT_SECRET và JWT_ALGORITHM qua Config
    return jwt.encode(to_encode, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

def get_current_user(token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    """
    Validate token and return current user (payload).
    Thường thì sẽ trả về một user model hoặc user ID sau khi xác thực từ DB.
    Ở đây, chúng ta trả về payload để đơn giản.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials", # "Không thể xác thực thông tin đăng nhập"
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Truy cập JWT_SECRET và JWT_ALGORITHM qua Config
        payload = jwt.decode(
            token.credentials,
            Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )
        # Bạn có thể muốn lấy một trường cụ thể từ payload, ví dụ: username hoặc user_id
        # username: str = payload.get("sub") # Giả sử bạn lưu username trong "sub"
        # if username is None:
        #     raise credentials_exception
        # return username # Hoặc một đối tượng User đầy đủ hơn
        return payload # Hiện tại trả về toàn bộ payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired", # "Token đã hết hạn"
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError: # Bao gồm các lỗi như invalid signature, malformed token, etc.
        raise credentials_exception # Sử dụng lại credentials_exception đã định nghĩa ở trên
    except Exception as e: # Bắt các lỗi không mong muốn khác
        print(f"Unexpected error during token decoding: {e}") # Ghi log lỗi
        raise credentials_exception
# --- END OF FILE auth_utils.py ---