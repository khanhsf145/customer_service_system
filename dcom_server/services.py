# dcom_server/services.py

import pythoncom

class RequestProcessor:
    _public_methods_ = ['AnalyzeRequest', 'ProcessRequest']
    _reg_progid_ = "CustomerService.RequestProcessor"
    _reg_clsid_ = "{12345678-1234-1234-1234-1234567890AB}"  # Bạn có thể thay bằng GUID riêng nếu cần

    def AnalyzeRequest(self, request):
        return f"Phân tích yêu cầu: {request}"

    def ProcessRequest(self, request):
        return f"Xử lý yêu cầu: {request}"
