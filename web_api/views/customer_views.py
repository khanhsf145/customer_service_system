# from flask import Blueprint, request, jsonify
# import uuid
# from datetime import datetime
# from web_api.tracking import load_requests, save_requests
# from web_api.email_util import send_notification_email
#
# customer_api = Blueprint('customer_api', __name__)
#
#
# @customer_api.route("/submit", methods=["POST"])
# def submit_request():
#     """Cho phép khách hàng gửi yêu cầu mới"""
#     data = request.json
#     content = data.get("content")
#     email = data.get("email")
#     category = data.get("category", "Chung")
#
#     if not content or not email:
#         return jsonify({"error": "Vui lòng cung cấp nội dung và email"}), 400
#
#     request_id = str(uuid.uuid4())
#     time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#
#     request_data = {
#         "content": content,
#         "email": email,
#         "category": category,
#         "history": [
#             {"status": "Đã tiếp nhận", "time": time_now}
#         ]
#     }
#
#     all_data = load_requests()
#     all_data[request_id] = request_data
#     save_requests(all_data)
#
#     # Gửi email xác nhận đã nhận yêu cầu
#     send_notification_email(email, request_id, "Đã tiếp nhận")
#
#     return jsonify({
#         "id": request_id,
#         "message": "Yêu cầu của bạn đã được tiếp nhận và đang được xử lý."
#     })
#
#
# @customer_api.route("/status/<request_id>", methods=["GET"])
# def check_status(request_id):
#     """Cho phép khách hàng kiểm tra trạng thái yêu cầu"""
#     all_data = load_requests()
#     if request_id not in all_data:
#         return jsonify({"error": "Không tìm thấy yêu cầu với ID đã cung cấp"}), 404
#
#     request_data = all_data[request_id]
#     history = request_data.get("history", [])
#     latest_status = history[-1]["status"] if history else "Chưa xác định"
#
#     return jsonify({
#         "id": request_id,
#         "content": request_data.get("content"),
#         "category": request_data.get("category", "Chung"),
#         "status": latest_status,
#         "history": history
#     })
#
#
# @customer_api.route("/all", methods=["GET"])
# def list_requests():
#     """Liệt kê tất cả các yêu cầu của một email cụ thể"""
#     email = request.args.get("email")
#     if not email:
#         return jsonify({"error": "Vui lòng cung cấp email"}), 400
#
#     all_data = load_requests()
#     user_requests = {}
#
#     for req_id, req_data in all_data.items():
#         if req_data.get("email") == email:
#             user_requests[req_id] = req_data
#
#     return jsonify({"requests": user_requests})

# web_api/views/customer_views.py
from flask import Blueprint, request, jsonify
# Bỏ import uuid, datetime, load_requests, save_requests
from web_api.email_util import send_notification_email
# Import các hàm mới từ tracking
from web_api.tracking import add_new_request, get_request_by_id, get_requests_by_email
from web_api.models import CustomerRequest # Vẫn dùng model để chuẩn hóa

customer_api = Blueprint('customer_api', __name__)

@customer_api.route("/submit", methods=["POST"])
def submit_request():
    """Cho phép khách hàng gửi yêu cầu mới (đã sửa để dùng DB)"""
    data = request.json
    content = data.get("content")
    email = data.get("email")

    if not content or not email:
        return jsonify({"error": "Vui lòng cung cấp nội dung và email"}), 400

    # Dữ liệu để truyền vào hàm add_new_request
    request_data_dict = {
        "content": content,
        "email": email,
        "category": data.get("category", "Chung"),
        "customer_name": data.get("customer_name"),
        "phone": data.get("phone"),
        # Priority sẽ lấy default trong DB hoặc hàm add_new_request
    }

    # Gọi hàm thêm vào DB
    new_request_id = add_new_request(request_data_dict)

    if new_request_id:
        try:
            # Gửi email xác nhận đã nhận yêu cầu
            send_notification_email(email, new_request_id, "Đã tiếp nhận")
        except Exception as e:
             print(f"Lỗi gửi email xác nhận cho request {new_request_id}: {e}")
             # Không cần dừng lại nếu gửi mail lỗi

        return jsonify({
            "id": new_request_id,
            "message": "Yêu cầu của bạn đã được tiếp nhận và đang được xử lý."
        })
    else:
        return jsonify({"error": "Không thể lưu yêu cầu vào cơ sở dữ liệu"}), 500


@customer_api.route("/status/<request_id>", methods=["GET"])
def check_status(request_id):
    """Cho phép khách hàng kiểm tra trạng thái yêu cầu (đã sửa để dùng DB)"""
    request_obj = get_request_by_id(request_id) # Hàm này trả về object CustomerRequest hoặc None

    if not request_obj:
        return jsonify({"error": "Không tìm thấy yêu cầu với ID đã cung cấp"}), 404

    # Chuyển object thành dict để trả về JSON
    return jsonify(request_obj.to_dict())


@customer_api.route("/all", methods=["GET"])
def list_requests():
    """Liệt kê tất cả các yêu cầu của một email cụ thể (đã sửa để dùng DB)"""
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Vui lòng cung cấp email"}), 400

    # Hàm này trả về list các object CustomerRequest
    user_requests_list = get_requests_by_email(email)

    # Chuyển list object thành list dict
    user_requests_dict = {req.id: req.to_dict() for req in user_requests_list}

    return jsonify({"requests": user_requests_dict})