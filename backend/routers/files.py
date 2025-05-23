# --- START OF FILE files.py ---

"""
Files router for managing documents
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
import os
# from mysql.connector import connect # Dòng này có vẻ không được sử dụng, có thể bỏ
# SỬA ĐỔI DÒNG IMPORT NÀY:
# from config import UPLOAD_DIR, MAX_UPLOAD_SIZE # <--- DÒNG CŨ
from config import Config # <--- DÒNG MỚI: Import class Config
from database import execute_query, get_db_connection # get_db_connection có thể không cần nếu execute_query đã quản lý connection
from utils.auth_utils import get_current_user
from utils.embedding import process_and_store # Đảm bảo file này và hàm này tồn tại và hoạt động đúng

router = APIRouter(prefix="/files", tags=["files"])

# Không cần tạo thư mục ở đây nếu nó được tạo khi ứng dụng khởi động hoặc trong từng request (đã làm trong POST /upload)
# Tuy nhiên, để đảm bảo, có thể giữ lại hoặc chuyển vào hàm khởi tạo ứng dụng FastAPI
# SỬA ĐỔI CÁCH TRUY CẬP BIẾN CẤU HÌNH:
# if not os.path.exists(Config.UPLOAD_DIR):
#     os.makedirs(Config.UPLOAD_DIR)

@router.post("/upload", summary="Upload, store, and process a new document")
async def upload_file( # Đổi thành async def để có thể sử dụng await cho file operations
    file: UploadFile = File(...),
    department: str = Form(...),
    current_user: dict = Depends(get_current_user) # Giả sử get_current_user trả về dict có 'id'
):
    """
    Tải lên tài liệu mới và xử lý embedding
    """
    # Tạo thư mục uploads nếu chưa tồn tại (an toàn hơn khi kiểm tra mỗi lần upload)
    # SỬA ĐỔI CÁCH TRUY CẬP BIẾN CẤU HÌNH:
    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)

    # Đường dẫn đến file
    # SỬA ĐỔI CÁCH TRUY CẬP BIẾN CẤU HÌNH:
    # Sử dụng os.path.basename để tránh các vấn đề về path traversal
    safe_filename = os.path.basename(file.filename)
    if not safe_filename: # Xử lý trường hợp tên file không hợp lệ sau khi làm sạch
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file name.")
    file_path = os.path.join(Config.UPLOAD_DIR, safe_filename)

    db_conn = None # Khởi tạo để đảm bảo có thể đóng trong finally
    try:
        # Kiểm tra kích thước file một cách an toàn hơn
        # Đọc file theo chunk để tránh đọc toàn bộ file lớn vào bộ nhớ một lúc
        contents = b""
        file_size = 0
        # SỬA ĐỔI CÁCH TRUY CẬP BIẾN CẤU HÌNH:
        max_size = Config.MAX_UPLOAD_SIZE
        chunk_size = 8192 # 8KB

        # Đọc file từ UploadFile bằng await file.read()
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            contents += chunk
            file_size = len(contents) # Cập nhật file_size
            if file_size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Kích thước file quá lớn. Giới hạn {max_size / (1024 * 1024):.2f}MB."
                )
        # await file.seek(0) # Reset con trỏ file nếu cần đọc lại từ đầu (không cần trong trường hợp này vì đã đọc hết)

        # Lưu file
        with open(file_path, "wb") as dest_file:
            dest_file.write(contents) # Ghi nội dung đã đọc

        # Sử dụng connection từ pool thông qua get_db_connection
        db_conn = get_db_connection() # Lấy connection
        cursor = db_conn.cursor()

        # Thêm thông tin file vào database
        # Đảm bảo current_user['id'] tồn tại và đúng
        if 'id' not in current_user:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User ID not found in token.")

        cursor.execute(
            "INSERT INTO documents (filename, user_id, department) VALUES (%s, %s, %s)",
            (safe_filename, current_user['id'], department)
        )
        db_conn.commit()
        doc_id = cursor.lastrowid
        cursor.close() # Đóng cursor sau khi dùng

        # Xử lý file và lưu embeddings
        # process_and_store có thể cần db_conn thay vì db_conn.cursor() nếu nó tự quản lý cursor
        # Nếu process_and_store cần connection:
        process_and_store(file_path, doc_id, db_conn)
        # Nếu process_and_store cần cursor (ít phổ biến hơn khi truyền connection):
        # temp_cursor_for_process = db_conn.cursor()
        # process_and_store(file_path, doc_id, temp_cursor_for_process)
        # temp_cursor_for_process.close()


        return {"message": "Tải file thành công", "filename": safe_filename, "doc_id": doc_id}
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Ghi log lỗi chi tiết hơn
        import traceback
        print(f"Error during file upload: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tải file: {str(e)}"
        )
    finally:
        # Không cần file.file.close() khi làm việc với UploadFile và await file.read()
        # FastAPI/Starlette sẽ xử lý việc đóng stream của UploadFile.
        if db_conn:
            db_conn.close() # Trả connection về pool

@router.get("/list", summary="List documents for the current user or public documents")
async def list_documents(current_user: dict = Depends(get_current_user)): # Đổi thành async
    """
    Lấy danh sách tài liệu
    """
    try:
        if 'id' not in current_user:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User ID not found in token.")

        # Sử dụng dictionary=True để execute_query trả về dicts
        documents = execute_query(
            """
            SELECT id, filename, department, created_at, is_public
            FROM documents
            WHERE user_id = %s OR is_public = TRUE
            ORDER BY created_at DESC
            """,
            (current_user["id"],),
            fetch_all=True # Đảm bảo fetch_all được sử dụng nếu execute_query hỗ trợ
        )

        return documents if documents else []
    except Exception as e:
        import traceback
        print(f"Error listing documents: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy danh sách tài liệu: {str(e)}"
        )

@router.delete("/delete/{doc_id}", summary="Delete a document by its ID")
async def delete_file_by_id(doc_id: int, current_user: dict = Depends(get_current_user)): # Đổi thành async
    """
    Xóa tài liệu dựa trên ID tài liệu.
    """
    try:
        if 'id' not in current_user:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User ID not found in token.")

        # Lấy thông tin file để lấy filename cho việc xóa file vật lý
        doc_info = execute_query(
            "SELECT filename FROM documents WHERE id = %s AND user_id = %s",
            (doc_id, current_user['id']),
            fetch_one=True
        )

        if not doc_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tài liệu không tồn tại hoặc bạn không có quyền xóa.")

        filename_to_delete = doc_info['filename']

        # Xóa từ database (cả document và các chunks liên quan nếu có)
        # Cần một transaction ở đây nếu xóa từ nhiều bảng
        db_conn = get_db_connection()
        try:
            cursor = db_conn.cursor()
            # Xóa các document_chunks liên quan (ví dụ, nếu bảng document_chunks có khóa ngoại doc_id)
            cursor.execute("DELETE FROM document_chunks WHERE doc_id = %s", (doc_id,))
            # Xóa document chính
            cursor.execute("DELETE FROM documents WHERE id = %s AND user_id = %s", (doc_id, current_user['id']))
            db_conn.commit()
            rows_affected = cursor.rowcount
            cursor.close()
        except Exception as db_err:
            if db_conn: db_conn.rollback()
            raise db_err # Ném lại lỗi để bắt ở ngoài
        finally:
            if db_conn: db_conn.close()


        if rows_affected == 0 : # Nếu không có dòng nào bị xóa (có thể do user_id không khớp)
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không thể xóa tài liệu, có thể bạn không phải chủ sở hữu.")

        # Xóa file vật lý
        # SỬA ĐỔI CÁCH TRUY CẬP BIẾN CẤU HÌNH:
        file_path = os.path.join(Config.UPLOAD_DIR, filename_to_delete)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as os_err:
                # Log lỗi nhưng vẫn báo thành công vì DB đã xóa (tùy chính sách)
                print(f"Lỗi khi xóa file vật lý {file_path}: {os_err}")


        return {"message": "Xóa tài liệu thành công"}
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        print(f"Error deleting document: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xóa tài liệu: {str(e)}"
        )

@router.get("/stats", summary="Get document statistics")
async def get_stats( # Đổi thành async
    year: str = Form(None), # Sử dụng None cho giá trị mặc định tùy chọn
    department: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy thống kê về tài liệu.
    """
    try:
        if 'id' not in current_user:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User ID not found in token.")

        # Xây dựng câu truy vấn với điều kiện lọc
        filters = ["(user_id = %s OR is_public = TRUE)"]
        values = [current_user['id']]

        if year:
            filters.append("YEAR(created_at) = %s")
            values.append(year)
        if department:
            filters.append("department = %s")
            values.append(department)

        # Nối các điều kiện lọc bằng AND, đảm bảo có WHERE chỉ khi có filter
        where_clause = ("WHERE " + " AND ".join(filters)) if filters else ""

        # Tổng số tài liệu
        total_result = execute_query(
            f"SELECT COUNT(*) AS total FROM documents {where_clause}",
            tuple(values), # execute_query thường nhận tuple cho params
            fetch_one=True
        )
        total = total_result["total"] if total_result and "total" in total_result else 0

        # Theo phòng ban
        by_department_query = f"""
            SELECT department, COUNT(*) AS count
            FROM documents
            {where_clause}
            GROUP BY department
            """
        by_department = execute_query(by_department_query, tuple(values), fetch_all=True)

        # Theo tháng
        by_month_query = f"""
            SELECT DATE_FORMAT(created_at, '%%Y-%%m') AS month, COUNT(*) AS count
            FROM documents
            {where_clause}
            GROUP BY month
            ORDER BY month ASC
            """
        by_month = execute_query(by_month_query, tuple(values), fetch_all=True)

        return {
            "total": total,
            "byDepartment": by_department if by_department else [],
            "byMonth": by_month if by_month else []
        }
    except Exception as e:
        import traceback
        print(f"Error getting stats: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy thống kê: {str(e)}"
        )

# --- END OF FILE files.py ---