# web_api/api.py

from flask import Flask, request, jsonify
from web_api.dcom_client import call_dcom_method
from web_api.tracking import get_request_status, save_request
from web_api.tracking import update_request_status
import uuid

app = Flask(__name__)

@app.route("/receive", methods=["POST"])
def receive_request():
    data = request.json.get("data")
    if not data:
        return jsonify({"error": "Missing request data"}), 400

    request_id = str(uuid.uuid4())
    save_request(request_id, data, status="Đã tiếp nhận")
    return jsonify({"message": f"Yêu cầu đã được tiếp nhận: {data}", "id": request_id})

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
    data = request.json.get("data")
    request_id = request.json.get("id")
    if not data or not request_id:
        return jsonify({"error": "Thiếu dữ liệu hoặc ID"}), 400

    result = call_dcom_method("ProcessRequest", data)
    update_request_status(request_id, "Đã xử lý")
    return jsonify({"result": result, "id": request_id})

@app.route("/track/<request_id>", methods=["GET"])
def track_request(request_id):
    status = get_request_status(request_id)
    if status is None:
        return jsonify({"error": "Request ID không tồn tại"}), 404
    return jsonify({"id": request_id, "status": status})
