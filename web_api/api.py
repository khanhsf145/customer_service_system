# from flask import Flask, request, jsonify
# from web_api.dcom_client import call_dcom_method
# from web_api.tracking import get_request_status, save_request, load_requests, save_requests
# from web_api.tracking import update_request_status
# from datetime import datetime
# from web_api.email_util import send_notification_email
# from web_api.views.customer_views import customer_api
# import uuid
#
# app = Flask(__name__)
#
# app.register_blueprint(customer_api, url_prefix='/customer')
#
# @app.route("/receive", methods=["POST"])
# def receive_request():
#     data = request.json.get("data")
#     email = request.json.get("email")
#     if not data or not email:
#         return jsonify({"error": "Thiếu dữ liệu hoặc email"}), 400
#
#     request_id = str(uuid.uuid4())
#     time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#
#     request_data = {
#         "data": data,
#         "email": email,
#         "history": [
#             {"status": "Đã tiếp nhận", "time": time_now}
#         ]
#     }
#
#     all_data = load_requests()
#     all_data[request_id] = request_data
#     save_requests(all_data)
#
#     return jsonify({"id": request_id, "message": "Yêu cầu đã được tiếp nhận."})
#
# @app.route("/analyze", methods=["POST"])
# def analyze_request():
#     data = request.json.get("data")
#     request_id = request.json.get("id")
#     if not data or not request_id:
#         return jsonify({"error": "Thiếu dữ liệu hoặc ID"}), 400
#
#     result = call_dcom_method("AnalyzeRequest", data)
#     update_request_status(request_id, "Đã phân tích")
#     return jsonify({"result": result, "id": request_id})
#
#
# @app.route("/process", methods=["POST"])
# def process_request():
#     req = request.json
#     request_id = req.get("id")
#     data = req.get("data")
#     email = req.get("email")
#
#     if not request_id or not data:
#         return jsonify({"error": "Thiếu ID hoặc dữ liệu"}), 400
#
#     try:
#         result = call_dcom_method("Process", data)
#         update_request_status(request_id, "Đã xử lý")
#
#         # Gửi email khi xử lý xong
#         all_data = load_requests()
#         email = all_data[request_id].get("email")
#         if email:
#             send_notification_email(email, request_id, "Đã xử lý")
#
#         return jsonify({"result": result})
#     except Exception as e:
#         return jsonify({"result": f"Lỗi khi xử lý: {str(e)}"}), 500
#
# @app.route("/track/<request_id>", methods=["GET"])
# def track_request(request_id):
#     data = load_requests()
#     if request_id not in data:
#         return jsonify({"error": "Không tìm thấy yêu cầu"}), 404
#
#     return jsonify({
#         "id": request_id,
#         "history": data[request_id].get("history", [])
#     })

from web_api.dcom_client import call_dcom_method
from web_api.tracking import get_request_status, save_request, load_requests, save_requests, update_request_status
from datetime import datetime
from web_api.email_util import send_notification_email
from flask import Flask, request, jsonify, render_template, redirect, url_for # Thêm render_template, redirect, url_for
import os # Thêm thư viện os
from web_api.views.customer_views import customer_api
from web_api.views.staff_views import staff_api
import uuid

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__,
            static_folder=os.path.join(project_root, 'static'),
            template_folder=os.path.join(project_root, 'templates'))

# Đăng ký các blueprint API
app.register_blueprint(customer_api, url_prefix='/customer')
app.register_blueprint(staff_api, url_prefix='/staff')

@app.route("/receive", methods=["POST"])
def receive_request():
    data = request.json.get("data")
    email = request.json.get("email")
    if not data or not email:
        return jsonify({"error": "Thiếu dữ liệu hoặc email"}), 400

    request_id = str(uuid.uuid4())
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    request_data = {
        "data": data,
        "email": email,
        "history": [
            {"status": "Đã tiếp nhận", "time": time_now}
        ]
    }

    all_data = load_requests()
    all_data[request_id] = request_data
    save_requests(all_data)

    return jsonify({"id": request_id, "message": "Yêu cầu đã được tiếp nhận."})

@app.route("/analyze", methods=["POST"])
def analyze_request():
    data = request.json.get("data")
    request_id = request.json.get("id")
    if not data or not request_id:
        return jsonify({"error": "Thiếu dữ liệu hoặc ID"}), 400

    result = call_dcom_method("AnalyzeRequest", data)
    update_request_status(request_id, "Đã phân tích")
    return jsonify({"result": result, "id": request_id})


@app.route("/process", methods=["POST"])
def process_request():
    req = request.json
    request_id = req.get("id")
    data = req.get("data")
    email = req.get("email")

    if not request_id or not data:
        return jsonify({"error": "Thiếu ID hoặc dữ liệu"}), 400

    try:
        result = call_dcom_method("ProcessRequest", data)
        update_request_status(request_id, "Đã xử lý")

        # Gửi email khi xử lý xong
        all_data = load_requests()
        email = all_data[request_id].get("email")
        if email:
            send_notification_email(email, request_id, "Đã xử lý")

        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"result": f"Lỗi khi xử lý: {str(e)}"}), 500

@app.route("/track/<request_id>", methods=["GET"])
def track_request(request_id):
    data = load_requests()
    if request_id not in data:
        return jsonify({"error": "Không tìm thấy yêu cầu"}), 404

    return jsonify({
        "id": request_id,
        "history": data[request_id].get("history", [])
    })

@app.route('/')
def index():
    # Trả về file index.html từ thư mục templates
    return render_template('index.html')

@app.route('/customer.html')
def customer_page():
    return render_template('customer.html')

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/staff.html')
# @token_required # Có thể cần thêm decorator này để yêu cầu đăng nhập mới vào được trang staff
def staff_page():
    # Kiểm tra xem có token không trước khi render
    # Đoạn kiểm tra token này nên đưa vào decorator nếu muốn chặt chẽ
    # from web_api.auth import token_required # Cần import nếu dùng decorator
    return render_template('staff.html')

@app.route('/admin.html')
# @token_required
# @admin_required # Có thể cần thêm decorator này
def admin_page():
     # Kiểm tra token và quyền admin
     return render_template('admin.html')