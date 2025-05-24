# --- START OF FILE auth.py ---

"""
Authentication router
"""
from fastapi import APIRouter, HTTPException, status, Depends # Thêm Depends nếu bạn muốn dùng OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordRequestForm # Tùy chọn: dùng form data chuẩn cho login
from pydantic import BaseModel
from typing import Dict, Any # Thêm typing
from datetime import timedelta # Thêm timedelta để tạo token

from database import execute_query
from utils.auth_utils import hash_password, verify_password, create_access_token
from config import Config # Import Config để lấy ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["authentication"])

class UserCreate(BaseModel): # Đổi tên để rõ ràng hơn
    username: str
    password: str

class UserLogin(BaseModel): # Đổi tên để rõ ràng hơn
    username: str
    password: str

# Model cho response token (nên định nghĩa rõ ràng)
class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    # is_admin: Optional[bool] = None # Thêm nếu bạn có vai trò admin

class UserResponse(BaseModel): # Model cho response khi đăng ký
    message: str
    user_id: int


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate): # Sử dụng model UserCreate, đổi tên body thành user_data
    """
    Đăng ký người dùng mới
    """
    # Kiểm tra xem tài khoản đã tồn tại chưa
    # Sử dụng fetch_one=True để lấy một bản ghi hoặc None
    existing_user_record = execute_query(
        "SELECT id FROM users WHERE username = %s",
        (user_data.username,),
        fetch_one=True # QUAN TRỌNG: Lấy một bản ghi
    )

    if existing_user_record: # Nếu existing_user_record không phải là None (tức là tìm thấy user)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên người dùng đã tồn tại"
        )

    # Hash mật khẩu và lưu vào database
    hashed_password = hash_password(user_data.password)

    try:
        # Sử dụng commit=True cho INSERT và lấy lastrowid
        # execute_query sẽ trả về lastrowid nếu commit thành công và có lastrowid
        # Hoặc True nếu commit thành công mà không có lastrowid (ví dụ UPDATE/DELETE)
        # Nên đặt tên cột mật khẩu là password_hash hoặc hashed_password cho nhất quán
        user_id = execute_query(
            "INSERT INTO users (username, hashed_password) VALUES (%s, %s)", # Giả sử tên cột là hashed_password
            (user_data.username, hashed_password),
            commit=True # QUAN TRỌNG: Commit transaction và lấy ID
        )

        if not isinstance(user_id, int) or user_id <= 0:
             # Điều này có thể xảy ra nếu lastrowid không được trả về đúng cách
             # hoặc nếu execute_query trả về True thay vì ID.
             # Cần kiểm tra lại logic trả về của execute_query cho trường hợp commit=True
             # Tạm thời, nếu user_id không phải số nguyên dương, coi như có lỗi.
             # Hoặc, bạn có thể query lại user vừa tạo để lấy ID nếu cần.
            logger.error(f"Failed to get valid user_id after registration for {user_data.username}. Received: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể tạo người dùng, không lấy được ID người dùng."
            )


        return UserResponse(message="Đăng ký thành công", user_id=user_id)
    except Exception as e:
        # logger.error(f"Error during user registration for {user_data.username}: {e}", exc_info=True) # Thêm logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi đăng ký: {str(e)}"
        )

# Thay vì AuthBody, có thể dùng OAuth2PasswordRequestForm chuẩn của FastAPI
# @router.post("/login", response_model=Token)
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     username = form_data.username
#     plain_password = form_data.password
#     # ... (logic còn lại)
@router.post("/login", response_model=Token)
async def login(login_data: UserLogin): # Sử dụng model UserLogin, đổi tên body thành login_data
    """
    Đăng nhập và trả về JWT token
    """
    # Lấy thông tin người dùng từ database
    # Sử dụng fetch_one=True để lấy một bản ghi (dictionary) hoặc None
    user_record = execute_query(
        "SELECT id, username, hashed_password, is_admin FROM users WHERE username = %s", # Giả sử tên cột là hashed_password và có cột is_admin
        (login_data.username,),
        fetch_one=True # QUAN TRỌNG: Lấy một bản ghi
    )

    # Dòng `user = users[0]` (dòng 66 cũ của bạn) không còn cần thiết và là nguyên nhân lỗi.
    # Biến `user_record` bây giờ sẽ là một dictionary hoặc None.

    if not user_record: # Nếu user_record là None (không tìm thấy user)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng", # Giữ thông báo chung chung
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Xác thực mật khẩu
    # Truy cập `hashed_password` từ `user_record` (là một dictionary)
    if not verify_password(login_data.password, user_record["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Tạo JWT token
    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Thêm các thông tin cần thiết vào payload của token
    token_data = {
        "sub": user_record["username"], # "sub" (subject) thường là username hoặc user ID
        "user_id": user_record["id"],
        "is_admin": user_record.get("is_admin", False) # Lấy is_admin, mặc định là False nếu không có
    }
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        username=user_record["username"]
        # is_admin=user_record.get("is_admin", False) # Trả về is_admin nếu cần ở frontend
    )
# --- END OF FILE auth.py ---