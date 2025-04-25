from flask import Blueprint, request, jsonify, g
import datetime  # Import datetime cho hàm get_dashboard
import os      # Import os nếu dùng assignment file
import json    # Import json nếu dùng assignment file

# --- Import các hàm xác thực và tạo token ---
from web_api.auth import (
    token_required, staff_required, admin_required,
    authenticate_user, generate_token # Đảm bảo các hàm này tồn tại trong auth.py
)
# --- Import các hàm tương tác DB từ tracking ---
from web_api.tracking import (
    get_all_requests, get_request_by_id, update_request_status,
    update_request_assignment, update_request_priority
    # Không cần import add_new_request vì nó dùng ở customer_views
)
# --- Import các thành phần khác ---
# Import CustomerRequest nếu bạn cần tạo/kiểm tra kiểu dữ liệu trả về từ tracking
from web_api.models import CustomerRequest
from web_api.dcom_client import call_dcom_method
from web_api.email_util import send_notification_email


staff_api = Blueprint('staff_api', __name__)

# --- (Tùy chọn) Phần xử lý file assignment ---
# ASSIGNMENTS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'assignments.json') # Cập nhật đường dẫn nếu cần
# def load_assignments():
#     """Tải thông tin phân công từ file"""
#     if not os.path.exists(ASSIGNMENTS_FILE):
#         return {}
#     try:
#         with open(ASSIGNMENTS_FILE, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except json.JSONDecodeError:
#         print(f"Warning: Could not decode JSON from {ASSIGNMENTS_FILE}")
#         return {} # Trả về dict rỗng nếu file lỗi
# def save_assignments(data):
#     """Lưu thông tin phân công vào file"""
#     os.makedirs(os.path.dirname(ASSIGNMENTS_FILE), exist_ok=True)
#     with open(ASSIGNMENTS_FILE, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=4, ensure_ascii=False)
# --- Hết phần assignment file ---


# === HÀM ĐĂNG NHẬP ===
@staff_api.route("/auth/login", methods=["POST"])
def login():
    """Xử lý đăng nhập cho nhân viên/admin."""
    username = request.json.get("username")
    password = request.json.get("password")

    if not username or not password:
        return jsonify({"error": "Thiếu tên đăng nhập hoặc mật khẩu"}), 400

    # Gọi hàm xác thực (đã sửa để dùng DB và check hash trong auth.py)
    user_info = authenticate_user(username, password)

    if not user_info:
        # Hàm authenticate_user trả về None nếu sai thông tin hoặc lỗi
        return jsonify({"error": "Tên đăng nhập hoặc mật khẩu không chính xác"}), 401

    # Xác thực thành công, tạo token
    token = generate_token(user_info)
    if not token:
         return jsonify({"error": "Không thể tạo token xác thực"}), 500

    # Trả về token và thông tin cơ bản của user
    return jsonify({
        "token": token,
        "user": user_info
    })
# === KẾT THÚC HÀM ĐĂNG NHẬP ===


# === HÀM LẤY DỮ LIỆU DASHBOARD ===
@staff_api.route("/dashboard", methods=["GET"])
@token_required
@staff_required
def get_dashboard():
    """Lấy dữ liệu thống kê tổng quan cho dashboard."""
    try:
        # Lấy tất cả request từ DB để thống kê
        all_requests_list = get_all_requests() # Hàm này trả về list các object CustomerRequest

        total_requests = len(all_requests_list)
        status_counts = {}
        category_counts = {}
        priority_counts = {}
        my_pending_requests = []
        current_user = g.user["username"]

        for req in all_requests_list:
            # Đếm theo trạng thái hiện tại
            status = req.current_status
            status_counts[status] = status_counts.get(status, 0) + 1
            # Đếm theo danh mục
            category = req.category
            category_counts[category] = category_counts.get(category, 0) + 1
            # Đếm theo mức độ ưu tiên
            priority = req.priority
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

            # Lọc các yêu cầu chưa xử lý được gán cho user hiện tại
            pending_statuses = ["Đã tiếp nhận", "Đã phân tích", "Đang kiểm tra", "Chờ phản hồi KH", "Đã phân công"]
            if req.assigned_to == current_user and status in pending_statuses:
                 my_pending_requests.append(req.to_dict())

        # Sắp xếp các yêu cầu đang chờ
        priority_order = {"Khẩn cấp": 4, "Cao": 3, "Trung bình": 2, "Thấp": 1}
        # Chuyển đổi chuỗi thời gian thành đối tượng datetime để so sánh
        my_pending_requests.sort(key=lambda r: (
             priority_order.get(r['priority'], 0),
             datetime.datetime.strptime(r['created_at'], "%Y-%m-%d %H:%M:%S") if r.get('created_at') else datetime.datetime.min
             ), reverse=True) # reverse=True để ưu tiên cao và ngày tạo mới hơn lên trước

        return jsonify({
            "total_requests": total_requests,
            "status_counts": status_counts,
            "category_counts": category_counts,
            "priority_counts": priority_counts,
            "my_pending_requests": my_pending_requests
        })
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu dashboard: {e}")
        import traceback # Import để in traceback đầy đủ hơn khi có lỗi
        traceback.print_exc() # In traceback vào log server để debug
        return jsonify({"error": f"Không thể lấy dữ liệu dashboard: {str(e)}"}), 500
# === KẾT THÚC HÀM DASHBOARD ===


# === CÁC HÀM KHÁC ===
@staff_api.route("/requests", methods=["GET"])
@token_required
@staff_required
def list_all_requests():
    """Danh sách tất cả các yêu cầu (đã sửa để dùng DB)"""
    status_filter = request.args.get("status")
    category_filter = request.args.get("category")
    assigned_filter = request.args.get("assigned_to")
    current_user = g.user["username"]
    final_assigned_filter = None
    if assigned_filter:
        if assigned_filter == "me": final_assigned_filter = current_user
        elif assigned_filter == "unassigned": final_assigned_filter = "unassigned"
        else: final_assigned_filter = assigned_filter
    # Cần cập nhật hàm get_all_requests trong tracking.py để hỗ trợ category_filter nếu muốn
    all_requests_list = get_all_requests(status=status_filter, category=category_filter, assigned_to=final_assigned_filter)
    results_dict = {req.id: req.to_dict() for req in all_requests_list}
    return jsonify({"requests": results_dict})

@staff_api.route("/request/<request_id>", methods=["GET"])
@token_required
@staff_required
def get_request_details(request_id):
    """Lấy chi tiết một yêu cầu (đã sửa để dùng DB)"""
    request_obj = get_request_by_id(request_id)
    if not request_obj: return jsonify({"error": "Không tìm thấy yêu cầu"}), 404
    return jsonify(request_obj.to_dict())

@staff_api.route("/request/<request_id>/analyze", methods=["POST"])
@token_required
@staff_required
def analyze_request(request_id):
    """Phân tích yêu cầu và tự động cập nhật độ ưu tiên (đã sửa để dùng DB)"""
    request_obj = get_request_by_id(request_id)
    if not request_obj: return jsonify({"error": "Không tìm thấy yêu cầu"}), 404
    note = request.json.get("note", "")
    try:
        dcom_result_raw = call_dcom_method("AnalyzeRequest", request_obj.content)
        analysis_text = dcom_result_raw
        determined_priority = request_obj.priority
        if isinstance(dcom_result_raw, str) and "|Priority:" in dcom_result_raw:
            parts = dcom_result_raw.split("|Priority:", 1)
            analysis_text = parts[0].strip()
            priority_from_dcom = parts[1].strip()
            if priority_from_dcom in ["Thấp", "Trung bình", "Cao", "Khẩn cấp"]:
                 determined_priority = priority_from_dcom
            else: print(f"Warning: Priority '{priority_from_dcom}' from DCOM is not valid.")
        status_note = f"{analysis_text}. {note}".strip()
        status_updated = update_request_status(request_id, "Đã phân tích", status_note)
        priority_updated = update_request_priority(request_id, determined_priority)
        if not status_updated or not priority_updated:
             return jsonify({"error": "Lỗi khi cập nhật trạng thái hoặc độ ưu tiên vào DB"}), 500
        updated_request = get_request_by_id(request_id)
        return jsonify({"result": analysis_text, "priority_detected": determined_priority, "request": updated_request.to_dict() if updated_request else None})
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi phân tích yêu cầu {request_id}: {e}")
        return jsonify({"error": f"Lỗi khi phân tích: {str(e)}"}), 500

@staff_api.route("/request/<request_id>/process", methods=["POST"])
@token_required
@staff_required
def process_request(request_id):
    """Xử lý yêu cầu (đã sửa để dùng DB)"""
    request_obj = get_request_by_id(request_id)
    if not request_obj: return jsonify({"error": "Không tìm thấy yêu cầu"}), 404
    note = request.json.get("note", "")
    try:
        result = call_dcom_method("ProcessRequest", request_obj.content)
        status_updated = update_request_status(request_id, "Đã xử lý", note)
        if not status_updated: return jsonify({"error": "Lỗi khi cập nhật trạng thái đã xử lý vào DB"}), 500
        if request_obj.email:
            try:
                send_notification_email(request_obj.email, request_id, "Đã xử lý", f"Yêu cầu [{request_id[:8]}...] của bạn đã được xử lý. Ghi chú: {note if note else 'Không có'}")
            except Exception as e: print(f"Lỗi khi gửi email: {e}")
        updated_request = get_request_by_id(request_id)
        return jsonify({"result": result, "request": updated_request.to_dict() if updated_request else None})
    except Exception as e:
        print(f"Lỗi khi xử lý yêu cầu {request_id}: {e}")
        return jsonify({"error": f"Lỗi khi xử lý: {str(e)}"}), 500

@staff_api.route("/request/<request_id>/status", methods=["POST"])
@token_required
@staff_required
def update_status(request_id):
    """Cập nhật trạng thái yêu cầu thủ công (đã sửa để dùng DB)"""
    status = request.json.get("status")
    note = request.json.get("note", "")
    if not status: return jsonify({"error": "Thiếu trạng thái"}), 400
    request_obj_before = get_request_by_id(request_id)
    if not request_obj_before: return jsonify({"error": "Không tìm thấy yêu cầu để cập nhật"}), 404
    updated = update_request_status(request_id, status, note)
    if updated:
        if request_obj_before.email:
            try:
                send_notification_email(request_obj_before.email, request_id, status, f"Trạng thái yêu cầu [{request_id[:8]}...] của bạn đã được cập nhật thành: {status}. Ghi chú: {note if note else 'Không có'}")
            except Exception as e: print(f"Lỗi khi gửi email cập nhật status: {e}")
        updated_request = get_request_by_id(request_id)
        return jsonify({"message": "Đã cập nhật trạng thái", "request": updated_request.to_dict() if updated_request else None})
    else:
        return jsonify({"error": "Lỗi khi cập nhật trạng thái vào DB"}), 500

@staff_api.route("/request/<request_id>/assign", methods=["POST"])
@token_required
@staff_required
def assign_request(request_id):
    """Phân công yêu cầu cho nhân viên (đã sửa để dùng DB)"""
    staff_username = request.json.get("staff_username")
    if not staff_username: return jsonify({"error": "Thiếu tên đăng nhập nhân viên"}), 400
    assignment_updated = update_request_assignment(request_id, staff_username)
    if assignment_updated:
         update_request_status(request_id, "Đã phân công", f"Phân công cho {staff_username}")
         updated_request = get_request_by_id(request_id)
         return jsonify({"message": "Đã phân công yêu cầu", "request": updated_request.to_dict() if updated_request else None})
    else:
         if get_request_by_id(request_id) is None: return jsonify({"error": "Không tìm thấy yêu cầu để phân công"}), 404
         else: return jsonify({"error": "Lỗi khi cập nhật phân công vào DB"}), 500

@staff_api.route("/request/<request_id>/priority", methods=["POST"])
@token_required
@staff_required
def set_priority(request_id):
    """Thiết lập độ ưu tiên cho yêu cầu (đã sửa để dùng DB)"""
    priority = request.json.get("priority")
    if not priority or priority not in ["Thấp", "Trung bình", "Cao", "Khẩn cấp"]:
        return jsonify({"error": "Mức độ ưu tiên không hợp lệ"}), 400
    priority_updated = update_request_priority(request_id, priority)
    if priority_updated:
         update_request_status(request_id, "Đã cập nhật ưu tiên", f"Đặt ưu tiên thành {priority}")

         updated_request = get_request_by_id(request_id)
         return jsonify({"message": "Đã cập nhật mức độ ưu tiên", "request": updated_request.to_dict() if updated_request else None})
    else:
         if get_request_by_id(request_id) is None: return jsonify({"error": "Không tìm thấy yêu cầu để đặt ưu tiên"}), 404
         else: return jsonify({"error": "Lỗi khi cập nhật ưu tiên vào DB"}), 500