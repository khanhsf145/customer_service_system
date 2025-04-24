import os
from flask import Flask, jsonify, render_template, redirect, url_for # Bỏ request vì không dùng trực tiếp ở đây nữa
# Bỏ import các hàm cũ từ tracking, dcom_client, uuid, datetime, email_util vì các route cũ đã bị xóa

# --- Import các Blueprint và hàm khởi tạo DB ---
from web_api.views.customer_views import customer_api
from web_api.views.staff_views import staff_api
from web_api.tracking import init_db # Import hàm init_db từ tracking MỚI

# --- Xác định đường dẫn và Khởi tạo Flask App ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__,
            static_folder=os.path.join(project_root, 'static'),
            template_folder=os.path.join(project_root, 'templates'))

# --- (Tùy chọn) Cấu hình Secret Key cho Flask (nếu cần cho session, flash...) ---
# Nên đọc từ file config hoặc biến môi trường
# from config import SECRET_KEY
# app.config['SECRET_KEY'] = SECRET_KEY

# --- Khởi tạo/Kiểm tra Database ---
try:
    init_db() # Gọi hàm kiểm tra kết nối DB khi app khởi động
except Exception as e:
    print(f"!!! LỖI KHỞI ĐỘNG DATABASE - API CÓ THỂ KHÔNG HOẠT ĐỘNG: {e}")
    # Bạn có thể quyết định dừng hẳn ứng dụng ở đây nếu DB là bắt buộc
    # import sys
    # sys.exit("Database connection failed.")

# --- Đăng ký các Blueprint ---
# Các API endpoint thực sự sẽ nằm trong các file views này
app.register_blueprint(customer_api, url_prefix='/customer')
app.register_blueprint(staff_api, url_prefix='/staff')

# --- Các route để phục vụ file HTML tĩnh ---
# Các route này không xử lý logic nghiệp vụ, chỉ trả về file HTML
# Việc xử lý dữ liệu sẽ do JavaScript trong các file HTML đó gọi đến API trong các blueprint

@app.route('/')
def index():
    """Route cho trang chủ."""
    return render_template('index.html')

@app.route('/customer.html')
def customer_page():
    """Route cho trang khách hàng."""
    return render_template('customer.html')

@app.route('/login.html')
def login_page():
    """Route cho trang đăng nhập."""
    return render_template('login.html')

@app.route('/staff.html')
def staff_page():
    """Route cho trang nhân viên."""
    # Lưu ý: Việc kiểm tra đăng nhập nên được thực hiện bằng JavaScript
    # gọi API kiểm tra token hoặc dùng decorator @token_required trong view nếu cần
    return render_template('staff.html')

@app.route('/admin.html')
def admin_page():
    """Route cho trang admin."""
    # Tương tự trang staff, kiểm tra quyền nên thực hiện ở client hoặc API
    return render_template('admin.html')