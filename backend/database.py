"""
Module quản lý kết nối database
"""
import mysql.connector
from mysql.connector import pooling
from config import DB_CONFIG

# Tạo connection pool để tái sử dụng kết nối
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="chatbot_pool",
    pool_size=5,
    **DB_CONFIG
)

def get_db_connection():
    """
    Lấy kết nối từ pool
    """
    try:
        connection = connection_pool.get_connection()
        return connection
    except Exception as e:
        print(f"Error connecting to MySQL: {e}")
        # Fallback to direct connection if pool fails
        return mysql.connector.connect(**DB_CONFIG)

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
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=dictionary)
    
    try:
        cursor.execute(query, params)
        
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            connection.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Database query error: {e}")
        raise
    finally:
        cursor.close()
        connection.close()