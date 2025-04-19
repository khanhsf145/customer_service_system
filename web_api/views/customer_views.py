from flask import Blueprint, request, jsonify
import uuid
from datetime import datetime
from web_api.tracking import load_requests, save_requests
from web_api.email_util import send_notification_email

customer_api = Blueprint('customer_api', __name__)


@customer_api.route("/submit", methods=["POST"])
def submit_request():
    """Cho phép khách hàng gửi yêu cầu mới"""
    data = request.json
    content = data.get("content")
    email = data.get("email")
    category = data.get("category", "Chung")

    if not content or not email:
        return jsonify({"error": "Vui lòng cung cấp nội dung và email"}), 400

    request_id = str(uuid.uuid4())
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    request_data = {
        "content": content,
        "email": email,
        "category": category,
        "history": [
            {"status": "Đã tiếp nhận", "time": time_now}
        ]
    }

    all_data = load_requests()
    all_data[request_id] = request_data
    save_requests(all_data)

    # Gửi email xác nhận đã nhận yêu cầu
    send_notification_email(email, request_id, "Đã tiếp nhận")

    return jsonify({
        "id": request_id,
        "message": "Yêu cầu của bạn đã được tiếp nhận và đang được xử lý."
    })


@customer_api.route("/status/<request_id>", methods=["GET"])
def check_status(request_id):
    """Cho phép khách hàng kiểm tra trạng thái yêu cầu"""
    all_data = load_requests()
    if request_id not in all_data:
        return jsonify({"error": "Không tìm thấy yêu cầu với ID đã cung cấp"}), 404

    request_data = all_data[request_id]
    history = request_data.get("history", [])
    latest_status = history[-1]["status"] if history else "Chưa xác định"

    return jsonify({
        "id": request_id,
        "content": request_data.get("content"),
        "category": request_data.get("category", "Chung"),
        "status": latest_status,
        "history": history
    })


@customer_api.route("/all", methods=["GET"])
def list_requests():
    """Liệt kê tất cả các yêu cầu của một email cụ thể"""
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Vui lòng cung cấp email"}), 400

    all_data = load_requests()
    user_requests = {}

    for req_id, req_data in all_data.items():
        if req_data.get("email") == email:
            user_requests[req_id] = req_data

    return jsonify({"requests": user_requests})