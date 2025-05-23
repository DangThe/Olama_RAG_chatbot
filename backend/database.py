# --- START OF FILE database.py ---

"""
Module quản lý kết nối database
"""
import mysql.connector
from mysql.connector import pooling
# SỬA ĐỔI DÒNG NÀY:
# from config import DB_CONFIG  # <--- DÒNG CŨ GÂY LỖI
from config import Config     # <--- DÒNG MỚI ĐÚNG

# Tạo connection pool để tái sử dụng kết nối
# SỬA ĐỔI DÒNG NÀY:
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="chatbot_pool",
    pool_size=5,
    **Config.DB_CONFIG  # <--- Sử dụng Config.DB_CONFIG thay vì DB_CONFIG trực tiếp
)

def get_db_connection():
    """
    Lấy kết nối từ pool
    """
    try:
        connection = connection_pool.get_connection()
        return connection
    except Exception as e:
        print(f"Error getting connection from pool: {e}")
        print("Attempting fallback to direct connection...")
        # Fallback to direct connection if pool fails (cân nhắc về việc này trong production)
        try:
            # SỬA ĐỔI DÒNG NÀY:
            return mysql.connector.connect(**Config.DB_CONFIG) # <--- Sử dụng Config.DB_CONFIG
        except Exception as direct_connect_error:
            print(f"Error with fallback direct connection: {direct_connect_error}")
            raise # Ném lại lỗi nếu fallback cũng thất bại

def execute_query(query, params=None, fetch=True, dictionary=True):
    """
    Thực thi truy vấn và trả về kết quả
    
    Args:
        query (str): SQL query
        params (tuple, optional): Parameters for the query
        fetch (bool, optional): Whether to fetch results or not (for INSERT/UPDATE/DELETE)
        dictionary (bool, optional): Return results as dictionaries
        
    Returns:
        list/dict/None: Query results or None
    """
    connection = None # Khởi tạo để đảm bảo có thể close trong finally
    cursor = None # Khởi tạo để đảm bảo có thể close trong finally
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=dictionary)
        
        cursor.execute(query, params)
        
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            connection.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Database query error: {e} | Query: {query} | Params: {params}")
        # Cân nhắc rollback nếu có lỗi khi thực hiện non-fetch (commit) query
        if connection and not fetch:
            try:
                connection.rollback()
                print("Transaction rolled back due to error.")
            except Exception as rb_err:
                print(f"Error during rollback: {rb_err}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close() # Trả connection về pool nếu từ pool, hoặc đóng nếu là direct connection

def get_db():
    """
    Generator cho FastAPI Depends. Trả về một connection có thể dùng trong route.
    """
    connection = None # Khởi tạo để đảm bảo có thể close trong finally
    try:
        connection = get_db_connection()
        yield connection
    finally:
        if connection:
            connection.close()
# --- END OF FILE database.py ---