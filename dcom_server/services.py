# dcom_server/services.py
import pythoncom
import re # Thêm thư viện regex để xử lý từ khóa tốt hơn

# --- Định nghĩa từ khóa và mức độ ưu tiên ---
# (Mức độ cao hơn sẽ được ưu tiên nếu có nhiều từ khóa khớp)
PRIORITY_KEYWORDS = {
    "Khẩn cấp": [r'khẩn cấp', r'nghiêm trọng', r'không hoạt động', r'sập nguồn', r'không lên nguồn', r'không vào được', r'dừng đột ngột'],
    "Cao": [r'lỗi', r'hỏng', r'không dùng được', r'bảo hành', r'treo', r'đơ', r'không nhận', r'mất kết nối', r'không lưu được'],
    "Trung bình": [r'chậm', r'lag', r'hướng dẫn', r'cài đặt', r'tư vấn', r'hỏi đáp', r'yêu cầu tính năng'] # Có thể để trống, mặc định là Trung bình
    # "Thấp": [...] # Có thể thêm mức thấp nếu cần
}

DEFAULT_PRIORITY = "Trung bình"

def determine_priority(content):
    """Xác định độ ưu tiên dựa trên nội dung"""
    detected_priority = DEFAULT_PRIORITY
    content_lower = content.lower()

    # Kiểm tra từ mức cao nhất xuống thấp nhất
    for priority_level in ["Khẩn cấp", "Cao", "Trung bình"]: # Thứ tự quan trọng
        if priority_level in PRIORITY_KEYWORDS:
            for keyword_pattern in PRIORITY_KEYWORDS[priority_level]:
                # Dùng re.search để tìm kiếm linh hoạt hơn (ví dụ: từ đơn)
                if re.search(r'\b' + keyword_pattern + r'\b', content_lower, re.IGNORECASE):
                    return priority_level # Trả về mức ưu tiên cao nhất tìm thấy

    return detected_priority # Trả về mặc định nếu không khớp

class RequestProcessor:
    _public_methods_ = ['AnalyzeRequest', 'ProcessRequest']
    _reg_progid_ = "CustomerService.RequestProcessor"
    _reg_clsid_ = "{12345678-1234-1234-1234-1234567890AB}"

    def AnalyzeRequest(self, request_content):
        # --- Logic phân tích độ ưu tiên ---
        determined_priority = determine_priority(request_content)

        # --- Logic phân tích khác (nếu có) ---
        analysis_text = f"Đã phân tích nội dung yêu cầu. Gợi ý phân loại: {determined_priority}."
        # (Bạn có thể thêm các logic phân tích khác ở đây)

        # --- Trả về kết quả có cấu trúc ---
        # Format: "Analysis Text|Priority:PriorityLevel"
        return f"{analysis_text}|Priority:{determined_priority}"

    def ProcessRequest(self, request_content):
        # Giữ nguyên hoặc thêm logic xử lý nếu cần
        return f"Xử lý yêu cầu: {request_content}"

# Phần đăng ký server giữ nguyên nếu có
# if __name__ == "__main__":
#     # ... code đăng ký server ...