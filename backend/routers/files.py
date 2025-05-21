"""
Files router for managing documents
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
import os
from mysql.connector import connect
from config import UPLOAD_DIR, MAX_UPLOAD_SIZE
from database import execute_query, get_db_connection
from utils.auth_utils import get_current_user
from utils.embedding import process_and_store

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload")
def upload_file(
    file: UploadFile = File(...), 
    department: str = Form(...), 
    current_user=Depends(get_current_user)
):
    """
    Tải lên tài liệu mới và xử lý embedding
    """
    # Tạo thư mục uploads nếu chưa tồn tại
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Đường dẫn đến file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        # Kiểm tra kích thước file
        file_size = 0
        contents = file.file.read(MAX_UPLOAD_SIZE + 1)
        file_size = len(contents)
        
        if file_size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Kích thước file quá lớn. Giới hạn {MAX_UPLOAD_SIZE / (1024 * 1024)}MB."
            )
        
        # Lưu file
        with open(file_path, "wb") as dest_file:
            dest_file.write(contents)
        
        # Cần kết nối trực tiếp vì process_and_store cần
        db = get_db_connection()
        cursor = db.cursor()
        
        # Thêm thông tin file vào database
        cursor.execute(
            "INSERT INTO documents (filename, user_id, department) VALUES (%s, %s, %s)",
            (file.filename, current_user['id'], department)
        )
        db.commit()
        doc_id = cursor.lastrowid
        
        # Xử lý file và lưu embeddings
        process_and_store(file_path, doc_id, db)
        
        return {"message": "Tải file thành công"}
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tải file: {str(e)}"
        )
    finally:
        file.file.close()

@router.get("/list")
def list_documents(current_user=Depends(get_current_user)):
    """
    Lấy danh sách tài liệu
    """
    try:
        documents = execute_query(
            """
            SELECT filename, department, created_at 
            FROM documents 
            WHERE user_id = %s OR is_public = TRUE
            ORDER BY created_at DESC
            """,
            (current_user["id"],)
        )
        
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy danh sách tài liệu: {str(e)}"
        )

@router.delete("/delete/{filename}")
def delete_file(filename: str, current_user=Depends(get_current_user)):
    """
    Xóa tài liệu
    """
    try:
        # Xóa từ database
        execute_query(
            "DELETE FROM documents WHERE filename = %s AND user_id = %s",
            (filename, current_user['id']),
            fetch=False
        )
        
        # Xóa file vật lý
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {"message": "Xóa tài liệu thành công"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xóa tài liệu: {str(e)}"
        )

@router.get("/stats")
def get_stats(
    year: str = '', 
    department: str = '', 
    current_user=Depends(get_current_user)
):
    """
    Lấy thống kê về tài liệu
    """
    try:
        # Xây dựng câu truy vấn với điều kiện lọc
        filters = ["(user_id = %s OR is_public = TRUE)"]
        values = [current_user['id']]

        if year:
            filters.append("YEAR(created_at) = %s")
            values.append(year)
        if department:
            filters.append("department = %s")
            values.append(department)

        where_clause = " AND ".join(filters)

        # Tổng số tài liệu
        total_result = execute_query(
            f"SELECT COUNT(*) AS total FROM documents WHERE {where_clause}", 
            values
        )
        total = total_result[0]["total"] if total_result else 0

        # Theo phòng ban
        by_department = execute_query(
            f"""
            SELECT department, COUNT(*) AS count
            FROM documents
            WHERE {where_clause}
            GROUP BY department
            """, 
            values
        )

        # Theo tháng
        by_month = execute_query(
            f"""
            SELECT DATE_FORMAT(created_at, '%%Y-%%m') AS month, COUNT(*) AS count
            FROM documents
            WHERE {where_clause}
            GROUP BY month
            ORDER BY month ASC
            """, 
            values
        )

        return {
            "total": total,
            "byDepartment": by_department,
            "byMonth": by_month
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thống kê: {str(e)}"
        )