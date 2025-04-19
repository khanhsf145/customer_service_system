from flask import Blueprint, request, jsonify, g
from web_api.auth import token_required, staff_required, admin_required
from web_api.tracking import load_requests, save_requests
from web_api.models import CustomerRequest
from web_api.dcom_client import call_dcom_method
from web_api.email_util import send_notification_email
import os
import json

staff_api = Blueprint('staff_api', __name__)

# File lưu thông tin phân công
ASSIGNMENTS_FILE = "data/assignments.json"


def load_assignments():
    """Tải thông tin phân công từ file"""
    if not os.path.exists(ASSIGNMENTS_FILE):
        return {}
    with open(ASSIGNMENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_assignments(data):
    """Lưu thông tin phân công vào file"""
    os.makedirs(os.path.dirname(ASSIGNMENTS_FILE), exist_ok=True)
    with open(ASSIGNMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


@staff_api.route("/requests", methods=["GET"])
@token_required
@staff_required
def list_all_requests():
    """Danh sách tất cả các yêu cầu"""
    all_data = load_requests()
    status_filter = request.args.get("status")
    category_filter = request.args.get("category")
    assigned_filter = request.args.get("assigned_to")

    results = {}

    for req_id, req_data in all_data.items():
        request_obj = CustomerRequest.from_dict({**req_data, "id": req_id})

        # Áp dụng bộ lọc
        if status_filter and request_obj.current_status != status_filter:
            continue
        if category_filter and request_obj.category != category_filter:
            continue
        if assigned_filter:
            if assigned_filter == "me" and request_obj.assigned_to != g.user["username"]:
                continue
            elif assigned_filter != "me" and request_obj.assigned_to != assigned_filter:
                continue

        results[req_id] = request_obj.to_dict()

    return jsonify({"requests": results})


@staff_api.route("/request/<request_id>", methods=["GET"])
@token_required
@staff_required
def get_request_details(request_id):
    """Lấy chi tiết một yêu cầu"""
    all_data = load_requests()
    if request_id not in all_data:
        return jsonify({"error": "Không tìm thấy yêu cầu"}), 404

    request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
    return jsonify(request_obj.to_dict())


@staff_api.route("/request/<request_id>/analyze", methods=["POST"])
@token_required
@staff_required
def analyze_request(request_id):
    """Phân tích yêu cầu"""
    all_data = load_requests()
    if request_id not in all_data:
        return jsonify({"error": "Không tìm thấy yêu cầu"}), 404

    request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
    data = request.json.get("note", "")

    try:
        result = call_dcom_method("AnalyzeRequest", request_obj.content)
        request_obj.add_status("Đã phân tích", data)

        # Cập nhật lại dữ liệu
        all_data[request_id] = request_obj.to_dict()
        save_requests(all_data)

        return jsonify({
            "result": result,
            "request": request_obj.to_dict()
        })
    except Exception as e:
        return jsonify({"error": f"Lỗi khi phân tích: {str(e)}"}), 500


@staff_api.route("/request/<request_id>/process", methods=["POST"])
@token_required
@staff_required
def process_request(request_id):
    """Xử lý yêu cầu"""
    all_data = load_requests()
    if request_id not in all_data:
        return jsonify({"error": "Không tìm thấy yêu cầu"}), 404

    request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
    data = request.json.get("note", "")

    try:
        result = call_dcom_method("ProcessRequest", request_obj.content)
        request_obj.add_status("Đã xử lý", data)

        # Cập nhật lại dữ liệu
        all_data[request_id] = request_obj.to_dict()
        save_requests(all_data)

        # Gửi email khi xử lý xong
        if request_obj.email:
            try:
                send_notification_email(
                    request_obj.email,
                    request_id,
                    "Đã xử lý"
                )
            except Exception as e:
                print(f"Lỗi khi gửi email: {e}")

        return jsonify({
            "result": result,
            "request": request_obj.to_dict()
        })
    except Exception as e:
        return jsonify({"error": f"Lỗi khi xử lý: {str(e)}"}), 500


@staff_api.route("/request/<request_id>/status", methods=["POST"])
@token_required
@staff_required
def update_status(request_id):
    """Cập nhật trạng thái yêu cầu"""
    status = request.json.get("status")
    note = request.json.get("note", "")

    if not status:
        return jsonify({"error": "Thiếu trạng thái"}), 400

    all_data = load_requests()
    if request_id not in all_data:
        return jsonify({"error": "Không tìm thấy yêu cầu"}), 404

    request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
    request_obj.add_status(status, note)

    all_data[request_id] = request_obj.to_dict()
    save_requests(all_data)

    # Gửi email thông báo khi cập nhật trạng thái
    if request_obj.email:
        try:
            send_notification_email(
                request_obj.email,
                request_id,
                status,
                f"Trạng thái yêu cầu của bạn đã được cập nhật thành: {status}. {note}"
            )
        except Exception as e:
            print(f"Lỗi khi gửi email: {e}")

    return jsonify({"message": "Đã cập nhật trạng thái", "request": request_obj.to_dict()})


@staff_api.route("/request/<request_id>/assign", methods=["POST"])
@token_required
@staff_required
def assign_request(request_id):
    """Phân công yêu cầu cho nhân viên"""
    staff_username = request.json.get("staff_username")

    if not staff_username:
        return jsonify({"error": "Thiếu tên đăng nhập nhân viên"}), 400

    all_data = load_requests()
    if request_id not in all_data:
        return jsonify({"error": "Không tìm thấy yêu cầu"}), 404

    request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
    request_obj.assigned_to = staff_username
    request_obj.add_status("Đã phân công", f"Phân công cho {staff_username}")

    all_data[request_id] = request_obj.to_dict()
    save_requests(all_data)

    return jsonify({"message": "Đã phân công yêu cầu", "request": request_obj.to_dict()})


@staff_api.route("/request/<request_id>/priority", methods=["POST"])
@token_required
@staff_required
def set_priority(request_id):
    """Thiết lập độ ưu tiên cho yêu cầu"""
    priority = request.json.get("priority")

    if not priority or priority not in ["Thấp", "Trung bình", "Cao", "Khẩn cấp"]:
        return jsonify({"error": "Mức độ ưu tiên không hợp lệ"}), 400

    all_data = load_requests()
    if request_id not in all_data:
        return jsonify({"error": "Không tìm thấy yêu cầu"}), 404

    request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
    request_obj.priority = priority

    all_data[request_id] = request_obj.to_dict()
    save_requests(all_data)

    return jsonify({"message": "Đã cập nhật mức độ ưu tiên", "request": request_obj.to_dict()})


@staff_api.route("/dashboard", methods=["GET"])
@token_required
@staff_required
def get_dashboard():
    """Thống kê tổng quan"""
    all_data = load_requests()

    total_requests = len(all_data)
    status_counts = {}
    category_counts = {}
    priority_counts = {}

    for req_id, req_data in all_data.items():
        request_obj = CustomerRequest.from_dict({**req_data, "id": req_id})

        # Đếm theo trạng thái
        status = request_obj.current_status
        status_counts[status] = status_counts.get(status, 0) + 1

        # Đếm theo danh mục
        category = request_obj.category
        category_counts[category] = category_counts.get(category, 0) + 1

        # Đếm theo mức độ ưu tiên
        priority = request_obj.priority
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    # Lọc các yêu cầu chưa xử lý cho nhân viên đang đăng nhập
    my_pending_requests = []
    for req_id, req_data in all_data.items():
        request_obj = CustomerRequest.from_dict({**req_data, "id": req_id})
        if request_obj.assigned_to == g.user["username"] and request_obj.current_status != "Đã xử lý":
            my_pending_requests.append(request_obj.to_dict())

    return jsonify({
        "total_requests": total_requests,
        "status_counts": status_counts,
        "category_counts": category_counts,
        "priority_counts": priority_counts,
        "my_pending_requests": my_pending_requests
    })


@staff_api.route("/auth/login", methods=["POST"])
def login():
    """Đăng nhập cho nhân viên"""
    from web_api.auth import authenticate_user, generate_token

    username = request.json.get("username")
    password = request.json.get("password")

    if not username or not password:
        return jsonify({"error": "Thiếu tên đăng nhập hoặc mật khẩu"}), 400

    user = authenticate_user(username, password)
    if not user:
        return jsonify({"error": "Tên đăng nhập hoặc mật khẩu không chính xác"}), 401

    user_data = {
        "username": username,
        "role": user["role"],
        "name": user.get("name", "")
    }

    token = generate_token(user_data)

    return jsonify({
        "token": token,
        "user": user_data
    })