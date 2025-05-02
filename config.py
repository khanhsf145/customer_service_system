DB_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': r'DESKTOP-91R6414',
    'database': 'CustomerServiceDB',
    'uid': 'svc_user',
    'pwd': 'csm123',
}

conn_parts = [
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


DB_CONNECTION_STRING = ";".join(conn_parts)
print(f"--- DEBUG: Connection String = {DB_CONNECTION_STRING} ---")

SECRET_KEY = "khanhsf145" # Nhớ thay đổi key này