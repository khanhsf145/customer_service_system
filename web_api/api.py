import os
from flask import Flask, render_template, redirect, url_for # Chỉ import những gì cần cho file này

from web_api.views.customer_views import customer_api
from web_api.views.staff_views import staff_api
from web_api.tracking import init_db # Import hàm init_db từ tracking MỚI

# --- Xác định đường dẫn và Khởi tạo Flask App ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# !!! Đảm bảo chỉ có MỘT dòng này tạo app !!!
app = Flask(__name__,
            static_folder=os.path.join(project_root, 'static'),
            template_folder=os.path.join(project_root, 'templates'))

# --- (Tùy chọn) Cấu hình Secret Key cho Flask ---
# from config import SECRET_KEY
# app.config['SECRET_KEY'] = SECRET_KEY

# --- Khởi tạo/Kiểm tra Database ---
# Đặt ngay sau khi app được tạo và trước khi đăng ký blueprint/route
try:
    print("--- [api.py] Chuẩn bị gọi init_db()... ---") # Thêm log để biết nó chạy tới đây chưa
    init_db() # Gọi hàm kiểm tra kết nối DB khi app khởi động
    print("--- [api.py] Gọi init_db() hoàn tất (Nếu không có lỗi ở trên). ---")
except Exception as e:
    # In lỗi ra để biết vì sao init_db thất bại
    print(f"!!! LỖI KHI GỌI init_db() TRONG api.py: {e}")
    print("!!! KIỂM TRA LẠI CẤU HÌNH DATABASE TRONG config.py VÀ KẾT NỐI SQL SERVER !!!")
    # import traceback
    # traceback.print_exc() # In traceback chi tiết nếu cần debug sâu

# --- Đăng ký các Blueprint ---
app.register_blueprint(customer_api, url_prefix='/customer')
app.register_blueprint(staff_api, url_prefix='/staff')

# --- Các route để phục vụ file HTML tĩnh ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/customer.html')
def customer_page():
    return render_template('customer.html')

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/staff.html')
def staff_page():
    return render_template('staff.html')

@app.route('/admin.html')
def admin_page():
     return render_template('admin.html')

# --- KHÔNG CÒN CÁC ROUTE LOGIC CŨ Ở ĐÂY ---