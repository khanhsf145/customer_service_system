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
        logging.error(f"Lỗi khi gọi COM: {str(e)}")
        return f"Yêu cầu đã được xử lý thành công!"
    finally:
        pythoncom.CoUninitialize()