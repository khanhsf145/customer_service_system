# from flask import Blueprint, request, jsonify, g
# from web_api.auth import token_required, staff_required, admin_required
# from web_api.tracking import load_requests, save_requests
# from web_api.models import CustomerRequest
# from web_api.dcom_client import call_dcom_method
# from web_api.email_util import send_notification_email
# import os
# import json
#
# staff_api = Blueprint('staff_api', __name__)
#
# # File lưu thông tin phân công
# ASSIGNMENTS_FILE = "data/assignments.json"
#
#
# def load_assignments():
#     """Tải thông tin phân công từ file"""
#     if not os.path.exists(ASSIGNMENTS_FILE):
#         return {}
#     with open(ASSIGNMENTS_FILE, "r", encoding="utf-8") as f:
#         return json.load(f)
#
#
# def save_assignments(data):
#     """Lưu thông tin phân công vào file"""
#     os.makedirs(os.path.dirname(ASSIGNMENTS_FILE), exist_ok=True)
#     with open(ASSIGNMENTS_FILE, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=4, ensure_ascii=False)
#
#
# @staff_api.route("/requests", methods=["GET"])
# @token_required
# @staff_required
# def list_all_requests():
#     """Danh sách tất cả các yêu cầu"""
#     all_data = load_requests()
#     status_filter = request.args.get("status")
#     category_filter = request.args.get("category")
#     assigned_filter = request.args.get("assigned_to")
#
#     results = {}
#
#     for req_id, req_data in all_data.items():
#         request_obj = CustomerRequest.from_dict({**req_data, "id": req_id})
#
#         # Áp dụng bộ lọc
#         if status_filter and request_obj.current_status != status_filter:
#             continue
#         if category_filter and request_obj.category != category_filter:
#             continue
#         if assigned_filter:
#             if assigned_filter == "me" and request_obj.assigned_to != g.user["username"]:
#                 continue
#             elif assigned_filter != "me" and request_obj.assigned_to != assigned_filter:
#                 continue
#
#         results[req_id] = request_obj.to_dict()
#
#     return jsonify({"requests": results})
#
#
# @staff_api.route("/request/<request_id>", methods=["GET"])
# @token_required
# @staff_required
# def get_request_details(request_id):
#     """Lấy chi tiết một yêu cầu"""
#     all_data = load_requests()
#     if request_id not in all_data:
#         return jsonify({"error": "Không tìm thấy yêu cầu"}), 404
#
#     request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
#     return jsonify(request_obj.to_dict())
#
#
# @staff_api.route("/request/<request_id>/process", methods=["POST"])
# @token_required
# @staff_required
# def process_request(request_id):
#     """Xử lý yêu cầu"""
#     all_data = load_requests()
#     if request_id not in all_data:
#         return jsonify({"error": "Không tìm thấy yêu cầu"}), 404
#
#     request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
#     data = request.json.get("note", "")
#
#     try:
#         result = call_dcom_method("ProcessRequest", request_obj.content)
#         request_obj.add_status("Đã xử lý", data)
#
#         # Cập nhật lại dữ liệu
#         all_data[request_id] = request_obj.to_dict()
#         save_requests(all_data)
#
#         # Gửi email khi xử lý xong
#         if request_obj.email:
#             try:
#                 send_notification_email(
#                     request_obj.email,
#                     request_id,
#                     "Đã xử lý"
#                 )
#             except Exception as e:
#                 print(f"Lỗi khi gửi email: {e}")
#
#         return jsonify({
#             "result": result,
#             "request": request_obj.to_dict()
#         })
#     except Exception as e:
#         return jsonify({"error": f"Lỗi khi xử lý: {str(e)}"}), 500
#
#
# @staff_api.route("/request/<request_id>/status", methods=["POST"])
# @token_required
# @staff_required
# def update_status(request_id):
#     """Cập nhật trạng thái yêu cầu"""
#     status = request.json.get("status")
#     note = request.json.get("note", "")
#
#     if not status:
#         return jsonify({"error": "Thiếu trạng thái"}), 400
#
#     all_data = load_requests()
#     if request_id not in all_data:
#         return jsonify({"error": "Không tìm thấy yêu cầu"}), 404
#
#     request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
#     request_obj.add_status(status, note)
#
#     all_data[request_id] = request_obj.to_dict()
#     save_requests(all_data)
#
#     # Gửi email thông báo khi cập nhật trạng thái
#     if request_obj.email:
#         try:
#             send_notification_email(
#                 request_obj.email,
#                 request_id,
#                 status,
#                 f"Trạng thái yêu cầu của bạn đã được cập nhật thành: {status}. {note}"
#             )
#         except Exception as e:
#             print(f"Lỗi khi gửi email: {e}")
#
#     return jsonify({"message": "Đã cập nhật trạng thái", "request": request_obj.to_dict()})
#
#
# @staff_api.route("/request/<request_id>/assign", methods=["POST"])
# @token_required
# @staff_required
# def assign_request(request_id):
#     """Phân công yêu cầu cho nhân viên"""
#     staff_username = request.json.get("staff_username")
#
#     if not staff_username:
#         return jsonify({"error": "Thiếu tên đăng nhập nhân viên"}), 400
#
#     all_data = load_requests()
#     if request_id not in all_data:
#         return jsonify({"error": "Không tìm thấy yêu cầu"}), 404
#
#     request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
#     request_obj.assigned_to = staff_username
#     request_obj.add_status("Đã phân công", f"Phân công cho {staff_username}")
#
#     all_data[request_id] = request_obj.to_dict()
#     save_requests(all_data)
#
#     return jsonify({"message": "Đã phân công yêu cầu", "request": request_obj.to_dict()})
#
#
# @staff_api.route("/request/<request_id>/priority", methods=["POST"])
# @token_required
# @staff_required
# def set_priority(request_id):
#     """Thiết lập độ ưu tiên cho yêu cầu"""
#     priority = request.json.get("priority")
#
#     if not priority or priority not in ["Thấp", "Trung bình", "Cao", "Khẩn cấp"]:
#         return jsonify({"error": "Mức độ ưu tiên không hợp lệ"}), 400
#
#     all_data = load_requests()
#     if request_id not in all_data:
#         return jsonify({"error": "Không tìm thấy yêu cầu"}), 404
#
#     request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
#     request_obj.priority = priority
#
#     all_data[request_id] = request_obj.to_dict()
#     save_requests(all_data)
#
#     return jsonify({"message": "Đã cập nhật mức độ ưu tiên", "request": request_obj.to_dict()})
#
#
# @staff_api.route("/dashboard", methods=["GET"])
# @token_required
# @staff_required
# def get_dashboard():
#     """Thống kê tổng quan"""
#     all_data = load_requests()
#
#     total_requests = len(all_data)
#     status_counts = {}
#     category_counts = {}
#     priority_counts = {}
#
#     for req_id, req_data in all_data.items():
#         request_obj = CustomerRequest.from_dict({**req_data, "id": req_id})
#
#         # Đếm theo trạng thái
#         status = request_obj.current_status
#         status_counts[status] = status_counts.get(status, 0) + 1
#
#         # Đếm theo danh mục
#         category = request_obj.category
#         category_counts[category] = category_counts.get(category, 0) + 1
#
#         # Đếm theo mức độ ưu tiên
#         priority = request_obj.priority
#         priority_counts[priority] = priority_counts.get(priority, 0) + 1
#
#     # Lọc các yêu cầu chưa xử lý cho nhân viên đang đăng nhập
#     my_pending_requests = []
#     for req_id, req_data in all_data.items():
#         request_obj = CustomerRequest.from_dict({**req_data, "id": req_id})
#         if request_obj.assigned_to == g.user["username"] and request_obj.current_status != "Đã xử lý":
#             my_pending_requests.append(request_obj.to_dict())
#
#     return jsonify({
#         "total_requests": total_requests,
#         "status_counts": status_counts,
#         "category_counts": category_counts,
#         "priority_counts": priority_counts,
#         "my_pending_requests": my_pending_requests
#     })
#
#
# @staff_api.route("/auth/login", methods=["POST"])
# def login():
#     """Đăng nhập cho nhân viên"""
#     from web_api.auth import authenticate_user, generate_token
#
#     username = request.json.get("username")
#     password = request.json.get("password")
#
#     if not username or not password:
#         return jsonify({"error": "Thiếu tên đăng nhập hoặc mật khẩu"}), 400
#
#     user = authenticate_user(username, password)
#     if not user:
#         return jsonify({"error": "Tên đăng nhập hoặc mật khẩu không chính xác"}), 401
#
#     user_data = {
#         "username": username,
#         "role": user["role"],
#         "name": user.get("name", "")
#     }
#
#     token = generate_token(user_data)
#
#     return jsonify({
#         "token": token,
#         "user": user_data
#     })
#
# @staff_api.route("/request/<request_id>/analyze", methods=["POST"])
# @token_required
# @staff_required
# def analyze_request(request_id):
#     """Phân tích yêu cầu và tự động cập nhật độ ưu tiên"""
#     all_data = load_requests()
#     if request_id not in all_data:
#         return jsonify({"error": "Không tìm thấy yêu cầu"}), 404
#
#     request_obj = CustomerRequest.from_dict({**all_data[request_id], "id": request_id})
#     note = request.json.get("note", "") # Ghi chú từ nhân viên (nếu có)
#
#     try:
#         # Gọi DCOM để phân tích
#         dcom_result_raw = call_dcom_method("AnalyzeRequest", request_obj.content)
#
#         # --- Tách kết quả từ DCOM ---
#         analysis_text = dcom_result_raw # Mặc định lấy toàn bộ nếu không tách được
#         determined_priority = request_obj.priority # Giữ priority cũ nếu không tách được
#
#         if isinstance(dcom_result_raw, str) and "|Priority:" in dcom_result_raw:
#             parts = dcom_result_raw.split("|Priority:", 1)
#             analysis_text = parts[0].strip()
#             priority_from_dcom = parts[1].strip()
#             # Chỉ cập nhật nếu priority trả về hợp lệ
#             if priority_from_dcom in ["Thấp", "Trung bình", "Cao", "Khẩn cấp"]:
#                  determined_priority = priority_from_dcom
#             else:
#                  print(f"Warning: Priority '{priority_from_dcom}' from DCOM is not valid.")
#
#
#         # --- Cập nhật đối tượng request ---
#         request_obj.add_status("Đã phân tích", f"{analysis_text}. {note}".strip())
#         request_obj.priority = determined_priority # Cập nhật độ ưu tiên
#
#         # Cập nhật lại dữ liệu trong file JSON
#         all_data[request_id] = request_obj.to_dict()
#         save_requests(all_data)
#
#         # Trả về kết quả phân tích và request đã cập nhật
#         return jsonify({
#             "result": analysis_text, # Trả về phần text phân tích
#             "priority_detected": determined_priority, # Trả về priority đã xác định
#             "request": request_obj.to_dict() # Trả về toàn bộ object request đã cập nhật
#         })
#     except Exception as e:
#         # Ghi log lỗi chi tiết hơn nếu cần
#         print(f"Lỗi nghiêm trọng khi phân tích yêu cầu {request_id}: {e}")
#         # traceback.print_exc() # In traceback để debug nếu cần
#         return jsonify({"error": f"Lỗi khi phân tích: {str(e)}"}), 500

from web_api.tracking import (
    get_all_requests, get_request_by_id, update_request_status,
    update_request_assignment, update_request_priority
)
from flask import Blueprint, request, jsonify, g
from web_api.auth import token_required, staff_required, admin_required
from web_api.dcom_client import call_dcom_method
from web_api.email_util import send_notification_email

staff_api = Blueprint('staff_api', __name__)

# ... (load_assignments, save_assignments giữ nguyên nếu cần) ...

@staff_api.route("/requests", methods=["GET"])
@token_required
@staff_required
def list_all_requests():
    """Danh sách tất cả các yêu cầu (đã sửa để dùng DB)"""
    status_filter = request.args.get("status")
    category_filter = request.args.get("category") # Cần thêm filter category vào hàm get_all_requests nếu muốn
    assigned_filter = request.args.get("assigned_to")

    # Xử lý filter 'me'
    current_user = g.user["username"]
    final_assigned_filter = None
    if assigned_filter:
        if assigned_filter == "me":
            final_assigned_filter = current_user
        # elif assigned_filter == "unassigned": # Hàm tracking đã xử lý
        #     final_assigned_filter = "unassigned"
        else:
            final_assigned_filter = assigned_filter # Lọc theo username cụ thể

    # Gọi hàm lấy từ DB
    # Lưu ý: Hàm get_all_requests hiện tại chưa hỗ trợ filter category
    all_requests_list = get_all_requests(status=status_filter, assigned_to=final_assigned_filter)

    # Chuyển list object thành dict
    results_dict = {req.id: req.to_dict() for req in all_requests_list}

    return jsonify({"requests": results_dict})


@staff_api.route("/request/<request_id>", methods=["GET"])
@token_required
@staff_required
def get_request_details(request_id):
    """Lấy chi tiết một yêu cầu (đã sửa để dùng DB)"""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        return jsonify({"error": "Không tìm thấy yêu cầu"}), 404

    return jsonify(request_obj.to_dict())


@staff_api.route("/request/<request_id>/analyze", methods=["POST"])
@token_required
@staff_required
def analyze_request(request_id):
    """Phân tích yêu cầu và tự động cập nhật độ ưu tiên (đã sửa để dùng DB)"""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        return jsonify({"error": "Không tìm thấy yêu cầu"}), 404

    note = request.json.get("note", "")

    try:
        dcom_result_raw = call_dcom_method("AnalyzeRequest", request_obj.content)

        analysis_text = dcom_result_raw
        determined_priority = request_obj.priority # Giữ priority cũ nếu lỗi

        if isinstance(dcom_result_raw, str) and "|Priority:" in dcom_result_raw:
            parts = dcom_result_raw.split("|Priority:", 1)
            analysis_text = parts[0].strip()
            priority_from_dcom = parts[1].strip()
            if priority_from_dcom in ["Thấp", "Trung bình", "Cao", "Khẩn cấp"]:
                 determined_priority = priority_from_dcom
            else:
                 print(f"Warning: Priority '{priority_from_dcom}' from DCOM is not valid.")

        # Cập nhật status và priority vào DB
        status_note = f"{analysis_text}. {note}".strip()
        status_updated = update_request_status(request_id, "Đã phân tích", status_note)
        priority_updated = update_request_priority(request_id, determined_priority)

        if not status_updated or not priority_updated:
             # Có lỗi khi cập nhật DB
             return jsonify({"error": "Lỗi khi cập nhật trạng thái hoặc độ ưu tiên vào DB"}), 500

        # Lấy lại request đã cập nhật để trả về
        updated_request = get_request_by_id(request_id)

        return jsonify({
            "result": analysis_text,
            "priority_detected": determined_priority,
            "request": updated_request.to_dict() if updated_request else None
        })
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi phân tích yêu cầu {request_id}: {e}")
        return jsonify({"error": f"Lỗi khi phân tích: {str(e)}"}), 500


@staff_api.route("/request/<request_id>/process", methods=["POST"])
@token_required
@staff_required
def process_request(request_id):
    """Xử lý yêu cầu (đã sửa để dùng DB)"""
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        return jsonify({"error": "Không tìm thấy yêu cầu"}), 404

    note = request.json.get("note", "")

    try:
        # Gọi DCOM
        result = call_dcom_method("ProcessRequest", request_obj.content) # Đảm bảo tên hàm DCOM đúng

        # Cập nhật trạng thái vào DB
        status_updated = update_request_status(request_id, "Đã xử lý", note)

        if not status_updated:
             return jsonify({"error": "Lỗi khi cập nhật trạng thái đã xử lý vào DB"}), 500

        # Gửi email khi xử lý xong
        if request_obj.email:
            try:
                send_notification_email(
                    request_obj.email,
                    request_id,
                    "Đã xử lý",
                     f"Yêu cầu [{request_id[:8]}...] của bạn đã được xử lý. Ghi chú: {note if note else 'Không có'}" # Thêm nội dung email
                )
            except Exception as e:
                print(f"Lỗi khi gửi email: {e}")

        # Lấy lại request đã cập nhật để trả về
        updated_request = get_request_by_id(request_id)

        return jsonify({
            "result": result, # Kết quả từ DCOM
            "request": updated_request.to_dict() if updated_request else None
        })
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

    if not status:
        return jsonify({"error": "Thiếu trạng thái"}), 400

    # Lấy email trước khi cập nhật để gửi mail
    request_obj_before = get_request_by_id(request_id)
    if not request_obj_before:
         return jsonify({"error": "Không tìm thấy yêu cầu để cập nhật"}), 404

    # Cập nhật vào DB
    updated = update_request_status(request_id, status, note)

    if updated:
        # Gửi email thông báo
        if request_obj_before.email:
            try:
                send_notification_email(
                    request_obj_before.email,
                    request_id,
                    status,
                    f"Trạng thái yêu cầu [{request_id[:8]}...] của bạn đã được cập nhật thành: {status}. Ghi chú: {note if note else 'Không có'}"
                )
            except Exception as e:
                print(f"Lỗi khi gửi email cập nhật status: {e}")

        updated_request = get_request_by_id(request_id) # Lấy lại để trả về
        return jsonify({"message": "Đã cập nhật trạng thái", "request": updated_request.to_dict() if updated_request else None})
    else:
        return jsonify({"error": "Lỗi khi cập nhật trạng thái vào DB"}), 500

@staff_api.route("/request/<request_id>/assign", methods=["POST"])
@token_required
@staff_required
def assign_request(request_id):
    """Phân công yêu cầu cho nhân viên (đã sửa để dùng DB)"""
    staff_username = request.json.get("staff_username")
    if not staff_username:
        return jsonify({"error": "Thiếu tên đăng nhập nhân viên"}), 400

    # Cập nhật DB
    assignment_updated = update_request_assignment(request_id, staff_username)

    if assignment_updated:
         # Thêm dòng vào history về việc phân công
         update_request_status(request_id, "Đã phân công", f"Phân công cho {staff_username}")
         updated_request = get_request_by_id(request_id)
         return jsonify({"message": "Đã phân công yêu cầu", "request": updated_request.to_dict() if updated_request else None})
    else:
         # Kiểm tra xem request có tồn tại không
         if get_request_by_id(request_id) is None:
             return jsonify({"error": "Không tìm thấy yêu cầu để phân công"}), 404
         else:
             return jsonify({"error": "Lỗi khi cập nhật phân công vào DB"}), 500


@staff_api.route("/request/<request_id>/priority", methods=["POST"])
@token_required
@staff_required
def set_priority(request_id):
    """Thiết lập độ ưu tiên cho yêu cầu (đã sửa để dùng DB)"""
    priority = request.json.get("priority")
    if not priority or priority not in ["Thấp", "Trung bình", "Cao", "Khẩn cấp"]:
        return jsonify({"error": "Mức độ ưu tiên không hợp lệ"}), 400

    # Cập nhật DB
    priority_updated = update_request_priority(request_id, priority)

    if priority_updated:
         # Có thể thêm status history nếu muốn:
         # update_request_status(request_id, "Đã cập nhật ưu tiên", f"Đặt ưu tiên thành {priority}")
         updated_request = get_request_by_id(request_id)
         return jsonify({"message": "Đã cập nhật mức độ ưu tiên", "request": updated_request.to_dict() if updated_request else None})
    else:
         if get_request_by_id(request_id) is None:
              return jsonify({"error": "Không tìm thấy yêu cầu để đặt ưu tiên"}), 404
         else:
              return jsonify({"error": "Lỗi khi cập nhật ưu tiên vào DB"}), 500


# Hàm get_dashboard và login giữ nguyên, chỉ cần đảm bảo chúng gọi đến các hàm tracking đã được cập nhật nếu cần

# ... (get_dashboard, login giữ nguyên) ...