DB_CONFIG = {
    # Thử driver này trước, nếu lỗi hãy thử '{SQL Server}'
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': r'DESKTOP-91R6414',
    'database': 'CustomerServiceDB',
    'uid': 'svc_user',
    'pwd': 'csm123',

    # --- Comment out hoặc xóa dòng trusted_connection nếu có ---
    # 'trusted_connection': 'yes',

    # --- Các tùy chọn khác (nếu cần) ---
    # 'Encrypt': 'yes',
    # 'TrustServerCertificate': 'yes',
}

# --- Tạo Connection String ---
# (Đoạn code này sẽ tự động dùng uid/pwd vì không có trusted_connection)
conn_parts = [
    # Sử dụng {} thay vì {{}} khi dùng f-string trực tiếp với giá trị từ dict
    f"DRIVER={{{DB_CONFIG['driver'].strip('{}')}}}",
    f"SERVER={DB_CONFIG['server']}",
    f"DATABASE={DB_CONFIG['database']}",
]
if 'trusted_connection' in DB_CONFIG and DB_CONFIG['trusted_connection'].lower() == 'yes':
    conn_parts.append(f"Trusted_Connection={DB_CONFIG['trusted_connection']}")
elif 'uid' in DB_CONFIG and 'pwd' in DB_CONFIG:
    conn_parts.append(f"UID={DB_CONFIG['uid']}")
    conn_parts.append(f"PWD={DB_CONFIG['pwd']}")
else:
    print("Lỗi cấu hình: Cần cung cấp UID/PWD hoặc Trusted_Connection=yes")
    raise ValueError("Thông tin xác thực SQL Server không hợp lệ trong config.py")

# Thêm các tùy chọn khác nếu có từ DB_CONFIG
# Ví dụ:
# if DB_CONFIG.get('Encrypt'): conn_parts.append(f"Encrypt={DB_CONFIG['Encrypt']}")
# if DB_CONFIG.get('TrustServerCertificate'): conn_parts.append(f"TrustServerCertificate={DB_CONFIG['TrustServerCertificate']}")


DB_CONNECTION_STRING = ";".join(conn_parts)
# In ra để kiểm tra khi chạy (sẽ thấy trong log của run_web_api.py)
print(f"--- DEBUG: Connection String = {DB_CONNECTION_STRING} ---")

# --- Cấu hình khác ---
SECRET_KEY = "khanhsf145" # Nhớ thay đổi key này