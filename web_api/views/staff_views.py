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