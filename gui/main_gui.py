# gui/main_gui.py

import tkinter as tk
from tkinter import messagebox
import requests

API_BASE = "http://127.0.0.1:5000"

class ServiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản lý dịch vụ khách hàng")

        # Nội dung yêu cầu
        tk.Label(root, text="Nội dung yêu cầu:").pack()
        self.entry_content = tk.Entry(root, width=50)
        self.entry_content.pack()

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
        if not content:
            messagebox.showerror("Lỗi", "Vui lòng nhập nội dung yêu cầu.")
            return
        res = requests.post(f"{API_BASE}/receive", json={"data": content})
        if res.ok:
            data = res.json()
            self.entry_id.delete(0, tk.END)
            self.entry_id.insert(0, data["id"])
            messagebox.showinfo("Thành công", f"Đã tiếp nhận yêu cầu. ID: {data['id']}")
        else:
            messagebox.showerror("Lỗi", res.text)

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
        if not content or not request_id:
            messagebox.showerror("Lỗi", "Nhập đầy đủ nội dung và ID.")
            return
        res = requests.post(f"{API_BASE}/process", json={"id": request_id, "data": content})
        if res.ok:
            messagebox.showinfo("Xử lý", res.json()["result"])
        else:
            messagebox.showerror("Lỗi", res.text)

    def track_request(self):
        request_id = self.entry_id.get()
        if not request_id:
            messagebox.showerror("Lỗi", "Vui lòng nhập ID yêu cầu.")
            return
        res = requests.get(f"{API_BASE}/track/{request_id}")
        if res.ok:
            status = res.json()["status"]
            messagebox.showinfo("Trạng thái yêu cầu", f"Trạng thái: {status}")
        else:
            messagebox.showerror("Lỗi", res.text)


if __name__ == "__main__":
    root = tk.Tk()
    app = ServiceApp(root)
    root.mainloop()