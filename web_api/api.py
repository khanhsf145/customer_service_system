from flask import Flask, request, jsonify
from web_api.dcom_client import call_dcom_method
from web_api.tracking import get_request_status, save_request, load_requests, save_requests
from web_api.tracking import update_request_status
from datetime import datetime
from web_api.email_util import send_notification_email
from web_api.views.customer_views import customer_api
import uuid

app = Flask(__name__)

app.register_blueprint(customer_api, url_prefix='/customer')

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
        result = call_dcom_method("Process", data)
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