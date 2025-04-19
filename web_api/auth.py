from flask import request, jsonify, g
from functools import wraps
import jwt
import datetime
import json
import os

# Cấu hình
SECRET_KEY = "khanhsf145"  # Thay đổi key này trong sản phẩm thực tế
TOKEN_EXPIRE_HOURS = 24
USER_FILE = "data/users.json"


def get_users():
    """Tải danh sách người dùng từ file"""
    if not os.path.exists(USER_FILE):
        # Tạo file user mặc định nếu chưa có
        default_users = {
            "admin": {
                "password": "admin123",
                "role": "admin",
                "name": "Administrator"
            },
            "staff": {
                "password": "staff123",
                "role": "staff",
                "name": "Nhân viên"
            }
        }
        os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=4, ensure_ascii=False)
        return default_users

    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def authenticate_user(username, password):
    """Xác thực người dùng"""
    users = get_users()
    user = users.get(username)
    if user and user["password"] == password:
        return user
    return None


def generate_token(user_data):
    """Tạo token JWT"""
    payload = {
        "username": user_data["username"],
        "role": user_data["role"],
        "name": user_data.get("name", ""),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def token_required(f):
    """Decorator kiểm tra token"""

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

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Decorator kiểm tra quyền admin"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, "user") or g.user["role"] != "admin":
            return jsonify({"error": "Bạn không có quyền truy cập"}), 403
        return f(*args, **kwargs)

    return decorated


def staff_required(f):
    """Decorator kiểm tra quyền nhân viên"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, "user") or g.user["role"] not in ["admin", "staff"]:
            return jsonify({"error": "Bạn không có quyền truy cập"}), 403
        return f(*args, **kwargs)

    return decorated