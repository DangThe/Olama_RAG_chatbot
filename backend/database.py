# --- START OF FILE database.py ---

"""
Module quản lý kết nối database
"""
import mysql.connector
from mysql.connector import pooling
import logging # THÊM logging
from config import Config

# Setup logging cơ bản nếu chưa có ở đâu đó
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Khởi tạo connection pool
connection_pool = None
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="chatbot_pool",
        pool_size=Config.DB_POOL_SIZE if hasattr(Config, 'DB_POOL_SIZE') else 5, # Lấy pool_size từ Config nếu có
        pool_reset_session=True, # Tùy chọn hữu ích
        **Config.DB_CONFIG
    )
    logger.info("Database connection pool created successfully.")
except mysql.connector.Error as err:
    logger.error(f"FATAL: Error creating database connection pool: {err}")
    # Cân nhắc việc raise SystemExit ở đây nếu không có DB thì ứng dụng không thể chạy
    # raise SystemExit(f"Failed to connect to database during pool creation: {err}")
except Exception as e:
    logger.error(f"FATAL: An unexpected error occurred during DB pool creation: {e}", exc_info=True)
    # raise SystemExit(f"Unexpected error during DB setup: {e}")


def get_db_connection():
    """
    Lấy kết nối từ pool.
    Sẽ thử khởi tạo lại pool nếu nó là None (chỉ là fallback, không nên xảy ra thường xuyên).
    """
    global connection_pool
    if connection_pool is None:
        logger.warning("Database pool was None. Attempting to re-initialize pool in get_db_connection.")
        try:
            connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="chatbot_pool_fallback",
                pool_size=Config.DB_POOL_SIZE if hasattr(Config, 'DB_POOL_SIZE') else 3,
                pool_reset_session=True,
                **Config.DB_CONFIG
            )
            logger.info("Database connection pool re-initialized (fallback).")
        except Exception as pool_init_err:
            logger.error(f"Failed to re-initialize database pool: {pool_init_err}", exc_info=True)
            raise # Ném lỗi nếu không thể tạo pool

    try:
        connection = connection_pool.get_connection()
        logger.debug("Obtained connection from pool.")
        return connection
    except mysql.connector.Error as e:
        logger.error(f"Error getting connection from pool: {e}", exc_info=True)
        # Không nên fallback về direct connection ở đây nữa, vì pool là cơ chế chính.
        # Nếu pool lỗi, cần phải tìm hiểu và sửa lỗi pool.
        raise # Ném lại lỗi để nơi gọi xử lý.
    except Exception as e: # Bắt các lỗi không mong muốn khác khi get_connection
        logger.error(f"Unexpected error getting connection from pool: {e}", exc_info=True)
        raise


# SỬA ĐỔI HÀM NÀY THEO HƯỚNG 1
def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False, dictionary=True):
    """
    Thực thi truy vấn và trả về kết quả.

    Args:
        query (str): SQL query.
        params (tuple, optional): Parameters for the query.
        fetch_one (bool, optional): True để fetch một hàng.
        fetch_all (bool, optional): True để fetch tất cả các hàng.
        commit (bool, optional): True để commit transaction (cho INSERT, UPDATE, DELETE).
        dictionary (bool, optional): True để cursor trả về kết quả dưới dạng dictionary.

    Returns:
        list/dict/None/int/bool: Phụ thuộc vào loại truy vấn và tham số fetch/commit.
                                 - INSERT/UPDATE/DELETE (với commit=True): lastrowid hoặc True.
                                 - SELECT (với fetch_one=True): một dictionary hoặc None.
                                 - SELECT (với fetch_all=True): một list các dictionaries hoặc list rỗng.
                                 - Các trường hợp khác: True.
    """
    connection = None
    cursor = None
    if fetch_one and fetch_all:
        # logger.warning("execute_query called with both fetch_one and fetch_all True. Prioritizing fetch_all.")
        # Hoặc raise lỗi:
        raise ValueError("Cannot set both fetch_one and fetch_all to True.")
    if (fetch_one or fetch_all) and commit:
        raise ValueError("Cannot fetch data and commit in the same execute_query call for safety.")


    try:
        connection = get_db_connection()
        # Tạo cursor với tùy chọn dictionary
        cursor = connection.cursor(dictionary=dictionary)

        logger.debug(f"Executing query: '{query}' with params: {params}")
        cursor.execute(query, params)

        if commit:
            connection.commit()
            logger.info(f"Query committed. Lastrowid: {cursor.lastrowid}")
            return cursor.lastrowid if cursor.lastrowid is not None else True # Trả về ID nếu là INSERT, ngược lại True

        if fetch_one:
            result = cursor.fetchone()
            logger.debug(f"Fetched one row: {result}")
            return result
        elif fetch_all:
            result = cursor.fetchall()
            logger.debug(f"Fetched all rows: ({len(result)} rows)")
            return result

        # Nếu không phải commit và cũng không phải fetch (ví dụ: câu lệnh DDL như CREATE TABLE)
        logger.debug("Query executed without commit or fetch operation.")
        return True

    except mysql.connector.Error as db_err:
        logger.error(f"Database query error: {db_err} | Query: {query} | Params: {params}", exc_info=True)
        if connection and commit: # Chỉ rollback nếu đây là một transaction có ý định commit
            try:
                logger.info("Attempting to rollback transaction due to error...")
                connection.rollback()
                logger.info("Transaction rolled back successfully.")
            except mysql.connector.Error as rb_err:
                logger.error(f"Error during transaction rollback: {rb_err}", exc_info=True)
        raise # Ném lại lỗi để endpoint có thể trả về lỗi 500 thích hợp
    except Exception as e:
        logger.error(f"Unexpected error in execute_query: {e} | Query: {query} | Params: {params}", exc_info=True)
        raise
    finally:
        if cursor:
            try:
                cursor.close()
                logger.debug("Cursor closed.")
            except Exception as cur_close_err:
                logger.error(f"Error closing cursor: {cur_close_err}", exc_info=True)
        if connection:
            try:
                if connection.in_transaction: # Kiểm tra nếu transaction còn mở mà không được commit/rollback
                    logger.warning(f"Connection returned to pool with an active transaction for query: {query}. Attempting rollback.")
                    connection.rollback() # Cố gắng rollback để làm sạch
                connection.close() # Trả connection về pool
                logger.debug("Connection returned to pool.")
            except Exception as conn_close_err:
                logger.error(f"Error closing/returning connection to pool: {conn_close_err}", exc_info=True)


def get_db():
    """
    Generator cho FastAPI Depends. Trả về một connection có thể dùng trong route.
    Connection này sẽ được tự động đóng (trả về pool) sau khi route xử lý xong.
    """
    connection = None
    try:
        connection = get_db_connection()
        logger.debug(f"DB connection {id(connection)} provided by get_db dependency.")
        yield connection
    except Exception as e:
        logger.error(f"Error in get_db dependency provider: {e}", exc_info=True)
        # Nếu không thể cung cấp connection, FastAPI sẽ trả lỗi 500.
        # Không nên ném lỗi ở đây trừ khi bạn muốn custom lỗi đó.
        raise
    finally:
        if connection:
            try:
                logger.debug(f"Closing DB connection {id(connection)} from get_db dependency.")
                connection.close() # Trả connection về pool
            except Exception as e:
                logger.error(f"Error closing DB connection in get_db finally block: {e}", exc_info=True)

# --- END OF FILE database.py ---