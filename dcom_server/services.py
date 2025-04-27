import pythoncom
import re

PRIORITY_KEYWORDS = {
    "Khẩn cấp": [r'khẩn cấp', r'nghiêm trọng', r'không hoạt động', r'sập nguồn', r'không lên nguồn', r'không vào được', r'dừng đột ngột'],
    "Cao": [r'lỗi', r'hỏng', r'không dùng được', r'bảo hành', r'treo', r'đơ', r'không nhận', r'mất kết nối', r'không lưu được'],
    "Trung bình": [r'chậm', r'lag', r'hướng dẫn', r'cài đặt', r'tư vấn', r'hỏi đáp', r'yêu cầu tính năng']
}

DEFAULT_PRIORITY = "Trung bình"

def determine_priority(content):
    detected_priority = DEFAULT_PRIORITY
    content_lower = content.lower()

    for priority_level in ["Khẩn cấp", "Cao", "Trung bình"]:
        if priority_level in PRIORITY_KEYWORDS:
            for keyword_pattern in PRIORITY_KEYWORDS[priority_level]:
                if re.search(r'\b' + keyword_pattern + r'\b', content_lower, re.IGNORECASE):
                    return priority_level

    return detected_priority

class RequestProcessor:
    _public_methods_ = ['AnalyzeRequest', 'ProcessRequest']
    _reg_progid_ = "CustomerService.RequestProcessor"
    _reg_clsid_ = "{12345678-1234-1234-1234-1234567890AB}"

    def AnalyzeRequest(self, request_content):
        determined_priority = determine_priority(request_content)

        analysis_text = f"Đã phân tích nội dung yêu cầu. Gợi ý phân loại: {determined_priority}."
        return f"{analysis_text}|Priority:{determined_priority}"

    def ProcessRequest(self, request_content):
        return f"Xử lý yêu cầu: {request_content}"