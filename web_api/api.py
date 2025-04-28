import os
from flask import Flask, render_template, redirect, url_for # Chỉ import những gì cần cho file này

from web_api.views.customer_views import customer_api
from web_api.views.staff_views import staff_api
from web_api.tracking import init_db # Import hàm init_db từ tracking MỚI

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__,
            static_folder=os.path.join(project_root, 'static'),
            template_folder=os.path.join(project_root, 'templates'))

try:
    print("--- [api.py] Chuẩn bị gọi init_db()... ---")
    init_db()
    print("--- [api.py] Gọi init_db() hoàn tất (Nếu không có lỗi ở trên). ---")
except Exception as e:
    print(f"!!! LỖI KHI GỌI init_db() TRONG api.py: {e}")
    print("!!! KIỂM TRA LẠI CẤU HÌNH DATABASE TRONG config.py VÀ KẾT NỐI SQL SERVER !!!")

app.register_blueprint(customer_api, url_prefix='/customer')
app.register_blueprint(staff_api, url_prefix='/staff')

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
