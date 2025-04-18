# web_api/dcom_client.py
import pythoncom
import win32com.client

def call_dcom_method(method_name, data):
    try:
        pythoncom.CoInitialize()
        obj = win32com.client.Dispatch("CustomerService.RequestProcessor")
        method = getattr(obj, method_name)
        return method(data)
    except Exception as e:
        return f"Lỗi khi gọi COM: {str(e)}"
