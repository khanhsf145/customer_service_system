# import pythoncom
# from win32com.server import register
#
# class RequestProcessor:
#     _reg_clsid_ = "{12345678-1234-1234-1234-1234567890AB}"
#     _reg_desc_ = "Python DCOM Request Processor"
#     _reg_progid_ = "Python.RequestProcessor"
#     _public_methods_ = ['analyze_request', 'process_request']
#
#     def analyze_request(self, request_data):
#         # Giả lập phân tích yêu cầu
#         return f"Phân tích yêu cầu: {request_data}"
#
#     def process_request(self, request_data):
#         # Giả lập xử lý yêu cầu
#         return f"Xử lý yêu cầu: {request_data}"
#
# if __name__ == "__main__":
#     register.UseCommandLine(RequestProcessor)
from win32com.server import register
from dcom_server.services import RequestProcessor

if __name__ == "__main__":
    register.UseCommandLine(RequestProcessor)
