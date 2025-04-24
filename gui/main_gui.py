# gui/main_gui.py

import tkinter as tk
from tkinter import messagebox
import requests

API_BASE = "http://172.18.60.23"

class ServiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản lý dịch vụ khách hàng")

        # Nội dung yêu cầu
        tk.Label(root, text="Nội dung yêu cầu:").pack()
        self.entry_content = tk.Entry(root, width=50)
        self.entry_content.pack()

        # Thêm sau phần nhập nội dung
        tk.Label(root, text="Email người nhận:").pack()
        self.entry_email = tk.Entry(root, width=50)
        self.entry_email.pack()

        # Nút tiếp nhận
        tk.Button(root, text="Tiếp nhận", command=self.receive_request).pack(pady=5)

        # Nút phân tích
        tk.Button(root, text="Phân tích", command=self.analyze_request).pack(pady=5)

        # Nút xử lý
        tk.Button(root, text="Xử lý", command=self.process_request).pack(pady=5)

        # Nhập ID để theo dõi
        tk.Label(root, text="ID yêu cầu:").pack()
        self.entry_id = tk.Entry(root, width=50)
        self.entry_id.pack()

        # Nút theo dõi
        tk.Button(root, text="Theo dõi yêu cầu", command=self.track_request).pack(pady=5)

    def receive_request(self):
        content = self.entry_content.get()
        email = self.entry_email.get()
        if not content or not email:
            messagebox.showerror("Lỗi", "Vui lòng nhập nội dung và email.")
            return
        try:
            res = requests.post(
                f"{API_BASE}/receive",
                json={"data": content, "email": email}  # <-- phải là JSON
            )
            if res.status_code == 200:
                request_id = res.json().get("id")
                self.entry_id.delete(0, tk.END)
                self.entry_id.insert(0, request_id)
                messagebox.showinfo("Thành công", "Đã tiếp nhận yêu cầu.")
            else:
                messagebox.showerror("Lỗi", res.text)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def analyze_request(self):
        content = self.entry_content.get()
        request_id = self.entry_id.get()
        if not content or not request_id:
            messagebox.showerror("Lỗi", "Nhập đầy đủ nội dung và ID.")
            return
        res = requests.post(f"{API_BASE}/analyze", json={"id": request_id, "data": content})
        if res.ok:
            messagebox.showinfo("Phân tích", res.json()["result"])
        else:
            messagebox.showerror("Lỗi", res.text)

    def process_request(self):
        content = self.entry_content.get()
        request_id = self.entry_id.get()
        email = self.entry_email.get()
        if not content or not request_id or not email:
            messagebox.showerror("Lỗi", "Hãy nhập đầy đủ các trường dữ liệu.")
            return
        # res = requests.post(f"{API_BASE}/process", json={"id": request_id, "data": content})
        # if res.ok:
        #     messagebox.showinfo("Xử lý", res.json()["result"])
        # else:
        #     messagebox.showerror("Lỗi", res.text)
        try:
            res = requests.post(
                f"{API_BASE}/process",
                json={"id": request_id, "data": content, "email": email}
            )
            if res.ok:
                messagebox.showinfo("Xử lý", res.json()["result"])
            else:
                messagebox.showerror("Lỗi", res.text)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def track_request(self):
        request_id = self.entry_id.get()
        if not request_id:
            messagebox.showerror("Lỗi", "Vui lòng nhập ID yêu cầu.")
            return
        res = requests.get(f"{API_BASE}/track/{request_id}")
        if res.ok:
            history = res.json().get("history", [])
            if not history:
                messagebox.showinfo("Theo dõi", "Chưa có trạng thái.")
                return
            message = "\n".join([f"{h['time']} - {h['status']}" for h in history])
            messagebox.showinfo("Lịch sử yêu cầu", message)
        else:
            messagebox.showerror("Lỗi", res.text)

if __name__ == "__main__":
    root = tk.Tk()
    app = ServiceApp(root)
    root.mainloop()