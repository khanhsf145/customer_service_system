import jwt
import datetime
from functools import wraps
from flask import request, jsonify, g
import pyodbc # Thêm import pyodbc
from werkzeug.security import check_password_hash # Import hàm kiểm tra hash
from config import DB_CONNECTION_STRING, SECRET_KEY # Import cấu hình DB và Secret Key
from web_api.tracking import get_db_connection # Import hàm kết nối DB từ tracking.py

def get_user_from_db(username):
    """Lấy thông tin người dùng từ database SQL Server."""
    conn = None
    cursor = None
    user_data = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Lấy tất cả các cột cần thiết, bao gồm cả password_hash
        sql = "SELECT username, password_hash, role, name, email, is_active FROM Users WHERE username = ?"
        cursor.execute(sql, username)
        row = cursor.fetchone()

        if row:
            # Chuyển row thành dictionary để dễ sử dụng
            user_data = {
                "username": row.username,
                "password_hash": row.password_hash, # Lấy hash để kiểm tra
                "role": row.role,
                "name": row.name,
                "email": row.email,
                "is_active": row.is_active
            }
            # Kiểm tra nếu không active thì coi như không tìm thấy
            if not row.is_active:
                 print(f"User '{username}' is inactive.")
                 return None

        return user_data # Trả về dict hoặc None nếu không tìm thấy/inactive

    except pyodbc.Error as ex:
        print(f"Lỗi khi lấy user '{username}' từ DB: {ex}")
        return None # Trả về None nếu có lỗi DB
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def authenticate_user(username, password):
    """Xác thực người dùng dựa trên DB và mật khẩu băm."""
    print(f"--- [DB Auth] Đang xác thực cho user: '{username}'")
    user_data_from_db = get_user_from_db(username)

    if not user_data_from_db:
        print(f"--- [DB Auth] Không tìm thấy user '{username}' hoặc user không active.")
        return None # User không tồn tại hoặc không active

    # Kiểm tra mật khẩu nhập vào với hash lưu trong DB
    stored_hash = user_data_from_db.get("password_hash")
    if stored_hash and check_password_hash(stored_hash, password):
        print(f"--- [DB Auth] Mật khẩu KHỚP cho user '{username}'")
        # **Quan trọng:** Không trả về password_hash cho các phần khác của ứng dụng
        user_info_for_token = {
             "username": user_data_from_db["username"],
             "role": user_data_from_db["role"],
             "name": user_data_from_db.get("name", "") # Lấy name nếu có
        }
        return user_info_for_token # Chỉ trả về thông tin cần thiết cho token/session
    else:
        print(f"--- [DB Auth] Mật khẩu KHÔNG KHỚP cho user '{username}'")
        return None

# --- Các hàm về Token và Decorator giữ nguyên ---
# (Chỉ cần đảm bảo generate_token nhận đúng dict user_info_for_token)

TOKEN_EXPIRE_HOURS = 24 # Thời gian token hết hạn (giờ)

def generate_token(user_data):
    """Tạo token JWT từ thông tin user lấy từ DB."""
    if not user_data or 'username' not in user_data or 'role' not in user_data:
         # Handle error: missing required user data for token generation
         print("Error: Cannot generate token due to missing user data.")
         return None # Hoặc raise một exception phù hợp

    payload = {
        "username": user_data["username"],
        "role": user_data["role"],
        "name": user_data.get("name", ""), # Lấy name từ dict
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    # Đảm bảo SECRET_KEY đã được import từ config hoặc định nghĩa ở đây
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def token_required(f):
    """Decorator kiểm tra token (giữ nguyên)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token không tồn tại"}), 401

        try:
            # Decode token dùng SECRET_KEY đã import/định nghĩa
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            # Lưu thông tin user vào g để các hàm khác có thể truy cập
            # Lấy các trường đã được đưa vào payload khi generate_token
            g.user = {
                "username": data["username"],
                "role": data["role"],
                "name": data.get("name", "")
            }
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token đã hết hạn"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token không hợp lệ"}), 401
        except Exception as e:
             print(f"Lỗi khi decode token: {e}") # Log lỗi khác nếu có
             return jsonify({"error": "Lỗi xử lý token"}), 401


        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator kiểm tra quyền admin (giữ nguyên)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Kiểm tra thông tin user đã được gán vào g bởi token_required chưa
        if not hasattr(g, "user") or g.user["role"] != "admin":
            return jsonify({"error": "Bạn không có quyền truy cập (yêu cầu admin)"}), 403
        return f(*args, **kwargs)
    return decorated

def staff_required(f):
    """Decorator kiểm tra quyền nhân viên (hoặc admin) (giữ nguyên)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, "user") or g.user["role"] not in ["admin", "staff"]:
            return jsonify({"error": "Bạn không có quyền truy cập (yêu cầu staff hoặc admin)"}), 403
        return f(*args, **kwargs)
    return decorated