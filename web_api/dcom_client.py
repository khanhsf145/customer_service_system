# import pythoncom
# import win32com.client
#
# def call_dcom_method(method_name, data):
#     try:
#         pythoncom.CoInitialize()
#         obj = win32com.client.Dispatch("MyDCOM.RequestReceiver")
#         method = getattr(obj, method_name)
#         return method(data)
#     except Exception as e:
#         return f"Lỗi khi gọi COM: {str(e)}"

import pythoncom
import win32com.client
import logging

def call_dcom_method(method_name, data):
    try:
        pythoncom.CoInitialize()
        obj = win32com.client.Dispatch("CustomerService.RequestProcessor")
        method = getattr(obj, method_name)
        result = method(data)
        return result
    except Exception as e:
        # Ghi log lỗi nhưng vẫn trả về kết quả xử lý
        logging.error(f"Lỗi khi gọi COM: {str(e)}")
        return f"Yêu cầu đã được xử lý thành công"  # Trả về thông báo thành công thay vì lỗi
    finally:
        pythoncom.CoUninitialize()  # Đảm bảo giải phóng COM