import yagmail

# Cấu hình tài khoản Gmail gửi đi
GMAIL_USER = "khanhhuyen412005@gmail.com"
GMAIL_PASSWORD = "modz zrwh qdhp qvse"

yag = yagmail.SMTP(GMAIL_USER, GMAIL_PASSWORD)

def send_notification_email(to_email, request_id, status):
    subject = "Yêu cầu đã được xử lý"
    content = f"Yêu cầu có ID {request_id} đã được xử lý thành công.\nTrạng thái cuối: {status}"
    try:
        yag.send(to=to_email, subject=subject, contents=content)
        print("✅ Đã gửi email tới", to_email)
    except Exception as e:
        print("❌ Gửi email lỗi:", e)
