import tkinter as tk
from tkinter import messagebox
import requests
import json # Import json để lấy dữ liệu từ response tốt hơn

API_BASE = "http://127.0.0.1:5000"

class ServiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản lý dịch vụ khách hàng (GUI)")
        self.root.geometry("400x450")

        tk.Label(root, text="Nội dung yêu cầu:").pack(pady=(10,0))
        self.entry_content = tk.Entry(root, width=50)
        self.entry_content.pack()

        tk.Label(root, text="Email người nhận:").pack(pady=(5,0))
        self.entry_email = tk.Entry(root, width=50)
        self.entry_email.pack()

        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Tiếp nhận", command=self.receive_request).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Phân tích (DCOM)", command=self.analyze_request).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Xử lý (DCOM)", command=self.process_request).grid(row=0, column=2, padx=5)

        tk.Label(root, text="ID yêu cầu (để Phân tích/Xử lý/Theo dõi):").pack(pady=(10,0))
        self.entry_id = tk.Entry(root, width=50)
        self.entry_id.pack()

        tk.Button(root, text="Theo dõi yêu cầu", command=self.track_request).pack(pady=10)

        tk.Label(root, text="Kết quả/Lịch sử:").pack(pady=(5,0))
        self.text_result = tk.Text(root, height=8, width=48, state=tk.DISABLED) # Disable chỉnh sửa
        self.text_result.pack(pady=5, padx=10)

    def _update_result_text(self, message):
        # Cập nhật nội dung vào ô Text kết quả
        self.text_result.config(state=tk.NORMAL)
        self.text_result.delete('1.0', tk.END)
        self.text_result.insert(tk.END, message)
        self.text_result.config(state=tk.DISABLED)

    def receive_request(self):
        content = self.entry_content.get()
        email = self.entry_email.get()
        if not content or not email:
            messagebox.showerror("Lỗi", "Vui lòng nhập nội dung và email.")
            return

        payload = {"content": content, "email": email}
        api_url = f"{API_BASE}/customer/submit"
        print(f"GUI: Calling POST {api_url}") # Log để debug

        try:
            res = requests.post(api_url, json=payload)
            res.raise_for_status() # Raise HTTPError cho các status code lỗi (4xx, 5xx)

            response_data = res.json()
            request_id = response_data.get("id")
            message = response_data.get("message", "Thành công!")

            if request_id:
                self.entry_id.delete(0, tk.END)
                self.entry_id.insert(0, request_id)
                messagebox.showinfo("Thành công", f"{message}\nID: {request_id}")
                self._update_result_text(f"Đã tiếp nhận. ID: {request_id}")
            else:
                 messagebox.showwarning("Cảnh báo", message) # Hiển thị thông báo từ server
                 self._update_result_text(f"Tiếp nhận có thể chưa thành công: {message}")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Lỗi kết nối/API", f"Lỗi khi gọi API:\n{e}\nURL: {api_url}")
            self._update_result_text(f"Lỗi API: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi không xác định", str(e))
            self._update_result_text(f"Lỗi: {e}")

    def analyze_request(self):
        request_id = self.entry_id.get()
        note_from_gui = "Phân tích từ GUI"

        if not request_id:
            messagebox.showerror("Lỗi", "Vui lòng nhập ID yêu cầu để phân tích.")
            return

        api_url = f"{API_BASE}/staff/request/{request_id}/analyze"
        payload = {"note": note_from_gui}
        print(f"GUI: Calling POST {api_url}") # Log để debug

        try:
            res = requests.post(api_url, json=payload)
            res.raise_for_status()
            response_data = res.json()
            result_text = response_data.get("result", "Không có kết quả text.")
            priority = response_data.get("priority_detected", "Không rõ")
            message = f"Kết quả Phân tích:\n{result_text}\nĐộ ưu tiên xác định: {priority}"
            messagebox.showinfo("Phân tích (DCOM)", message)
            self._update_result_text(message)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Lỗi kết nối/API", f"Lỗi khi gọi API phân tích:\n{e}\nURL: {api_url}")
            self._update_result_text(f"Lỗi API phân tích: {e}")
        except Exception as e:
             messagebox.showerror("Lỗi không xác định", str(e))
             self._update_result_text(f"Lỗi: {e}")

    def process_request(self):
        request_id = self.entry_id.get()
        note_from_gui = "Xử lý từ GUI"

        if not request_id:
            messagebox.showerror("Lỗi", "Vui lòng nhập ID yêu cầu để xử lý.")
            return

        api_url = f"{API_BASE}/staff/request/{request_id}/process"
        payload = {"note": note_from_gui}
        print(f"GUI: Calling POST {api_url}") # Log để debug

        try:
            res = requests.post(api_url, json=payload)
            res.raise_for_status()
            response_data = res.json()
            result_text = response_data.get("result", "Không có kết quả.")
            message = f"Kết quả Xử lý (DCOM):\n{result_text}"
            messagebox.showinfo("Xử lý (DCOM)", message)
            self._update_result_text(message) # Hiển thị kết quả

        except requests.exceptions.RequestException as e:
             messagebox.showerror("Lỗi kết nối/API", f"Lỗi khi gọi API xử lý:\n{e}\nURL: {api_url}")
             self._update_result_text(f"Lỗi API xử lý: {e}")
        except Exception as e:
             messagebox.showerror("Lỗi không xác định", str(e))
             self._update_result_text(f"Lỗi: {e}")

    def track_request(self):
        request_id = self.entry_id.get()
        if not request_id:
            messagebox.showerror("Lỗi", "Vui lòng nhập ID yêu cầu.")
            return

        api_url = f"{API_BASE}/customer/status/{request_id}"
        print(f"GUI: Calling GET {api_url}")

        try:
            res = requests.get(api_url)
            res.raise_for_status()
            data = res.json()

            history = data.get("history", [])
            content = data.get("content", "N/A")
            status = data.get("status", "N/A") # Trạng thái hiện tại

            if not history:
                message = "Chưa có lịch sử trạng thái."
            else:
                # Sắp xếp lịch sử theo thời gian mới nhất trước
                sorted_history = sorted(history, key=lambda x: x.get('time', '0'), reverse=True)
                message = f"Nội dung: {content}\nTrạng thái hiện tại: {status}\n\nLịch sử:\n"
                message += "\n".join([f"- {h.get('time','')} - {h.get('status','')} {f'({h.get("note", "")})' if h.get('note') else ''}" for h in sorted_history])

            messagebox.showinfo("Lịch sử yêu cầu", message)
            self._update_result_text(message) # Hiển thị trong text box

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Lỗi kết nối/API", f"Lỗi khi gọi API theo dõi:\n{e}\nURL: {api_url}")
            self._update_result_text(f"Lỗi API theo dõi: {e}")
        except Exception as e:
             messagebox.showerror("Lỗi không xác định", str(e))
             self._update_result_text(f"Lỗi: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ServiceApp(root)
    root.mainloop()