from werkzeug.security import generate_password_hash

admin_password = 'admin123'
staff_password = 'staff123'

admin_hash = generate_password_hash(admin_password)
staff_hash = generate_password_hash(staff_password)

print("--- Vui lòng copy các chuỗi hash sau đây ---")
print(f"Admin ('{admin_password}') Hash: {admin_hash}")
print(f"Staff ('{staff_password}') Hash: {staff_hash}")
print("---")
print("Chạy lệnh INSERT SQL dưới đây trong SSMS, thay thế 'HASH_CUA_ADMIN' và 'HASH_CUA_STAFF' bằng các giá trị tương ứng ở trên:")
print("\nINSERT INTO Users (username, password_hash, role, name, is_active) VALUES")
print(f"('admin', 'HASH_CUA_ADMIN', 'admin', 'Administrator', 1),")
print(f"('staff', 'HASH_CUA_STAFF', 'staff', 'Nhân viên', 1);")