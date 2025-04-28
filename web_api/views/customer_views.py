from flask import Blueprint, request, jsonify
from web_api.email_util import send_notification_email
from web_api.tracking import add_new_request, get_request_by_id, get_requests_by_email

customer_api = Blueprint('customer_api', __name__)

@customer_api.route("/submit", methods=["POST"])
def submit_request():
    data = request.json
    content = data.get("content")
    email = data.get("email")

    if not content or not email:
        return jsonify({"error": "Vui lòng cung cấp nội dung và email"}), 400

    request_data_dict = {
        "content": content,
        "email": email,
        "category": data.get("category", "Chung"),
        "customer_name": data.get("customer_name"),
        "phone": data.get("phone"),
    }

    new_request_id = add_new_request(request_data_dict)

    if new_request_id:
        try:
            send_notification_email(email, new_request_id, "Đã tiếp nhận")
        except Exception as e:
             print(f"Lỗi gửi email xác nhận cho request {new_request_id}: {e}")

        return jsonify({
            "id": new_request_id,
            "message": "Yêu cầu của bạn đã được tiếp nhận và đang được xử lý."
        })
    else:
        return jsonify({"error": "Không thể lưu yêu cầu vào cơ sở dữ liệu"}), 500


@customer_api.route("/status/<request_id>", methods=["GET"])
def check_status(request_id):
    request_obj = get_request_by_id(request_id)

    if not request_obj:
        return jsonify({"error": "Không tìm thấy yêu cầu với ID đã cung cấp"}), 404

    return jsonify(request_obj.to_dict())


@customer_api.route("/all", methods=["GET"])
def list_requests():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Vui lòng cung cấp email"}), 400

    user_requests_list = get_requests_by_email(email)

    user_requests_dict = {req.id: req.to_dict() for req in user_requests_list}

    return jsonify({"requests": user_requests_dict})