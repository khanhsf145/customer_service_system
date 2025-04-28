import jwt
import datetime
from functools import wraps
from flask import request, jsonify, g
import pyodbc
from werkzeug.security import check_password_hash
from config import DB_CONNECTION_STRING, SECRET_KEY
from web_api.tracking import get_db_connection

def get_user_from_db(username):
    conn = None
    cursor = None
    user_data = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT username, password_hash, role, name, email, is_active FROM Users WHERE username = ?"
        cursor.execute(sql, username)
        row = cursor.fetchone()

        if row:
            user_data = {
                "username": row.username,
                "password_hash": row.password_hash,
                "role": row.role,
                "name": row.name,
                "email": row.email,
                "is_active": row.is_active
            }

            if not row.is_active:
                 print(f"User '{username}' is inactive.")
                 return None

        return user_data

    except pyodbc.Error as ex:
        print(f"Lỗi khi lấy user '{username}' từ DB: {ex}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def authenticate_user(username, password):
    print(f"--- [DB Auth] Đang xác thực cho user: '{username}'")
    user_data_from_db = get_user_from_db(username)

    if not user_data_from_db:
        print(f"--- [DB Auth] Không tìm thấy user '{username}' hoặc user không active.")
        return None

    stored_hash = user_data_from_db.get("password_hash")
    if stored_hash and check_password_hash(stored_hash, password):
        print(f"--- [DB Auth] Mật khẩu KHỚP cho user '{username}'")
        user_info_for_token = {
             "username": user_data_from_db["username"],
             "role": user_data_from_db["role"],
             "name": user_data_from_db.get("name", "")
        }
        return user_info_for_token
    else:
        print(f"--- [DB Auth] Mật khẩu KHÔNG KHỚP cho user '{username}'")
        return None


TOKEN_EXPIRE_HOURS = 24

def generate_token(user_data):
    if not user_data or 'username' not in user_data or 'role' not in user_data:
         print("Error: Cannot generate token due to missing user data.")
         return None

    payload = {
        "username": user_data["username"],
        "role": user_data["role"],
        "name": user_data.get("name", ""),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def token_required(f):
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
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
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
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, "user") or g.user["role"] != "admin":
            return jsonify({"error": "Bạn không có quyền truy cập (yêu cầu admin)"}), 403
        return f(*args, **kwargs)
    return decorated

def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, "user") or g.user["role"] not in ["admin", "staff"]:
            return jsonify({"error": "Bạn không có quyền truy cập (yêu cầu staff hoặc admin)"}), 403
        return f(*args, **kwargs)
    return decorated