from datetime import datetime
import json
import os

DATA_FILE = "data/requests.json"

def load_requests():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_requests(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_request(request_id, content, status):
    data = load_requests()
    data[request_id] = {
        "content": content,
        "status": status
    }
    save_requests(data)

def get_request_status(request_id):
    data = load_requests()
    request = data.get(request_id)
    if not request:
        return None
    return request["status"]

def update_request_status(request_id, status):
    data = load_requests()
    if request_id in data:
        # Thêm bản ghi lịch sử trạng thái
        entry = {"status": status, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        if "history" not in data[request_id]:
            data[request_id]["history"] = []
        data[request_id]["history"].append(entry)
        save_requests(data)