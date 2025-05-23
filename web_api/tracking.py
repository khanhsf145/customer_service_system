import pyodbc
import uuid
from datetime import datetime
import json
from config import DB_CONNECTION_STRING
from web_api.models import CustomerRequest, StatusHistory

def get_db_connection():
    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Lỗi kết nối Database: {sqlstate} - {ex}")
        raise ex

def _map_row_to_request(row, history_rows):
    if not row:
        return None

    history = []
    if history_rows:
        for h_row in history_rows:
            history.append(StatusHistory(
                status=h_row.status,
                time=h_row.status_time.strftime("%Y-%m-%d %H:%M:%S") if h_row.status_time else None, # Định dạng lại time
                note=h_row.note
            ))

    # Sắp xếp history theo thời gian tăng dần (cũ trước, mới sau)
    history.sort(key=lambda x: datetime.strptime(x.time, "%Y-%m-%d %H:%M:%S") if x.time else datetime.min)

    return CustomerRequest(
        id=str(row.id),
        content=row.content,
        email=row.email,
        category=row.category,
        created_at=row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None, # Định dạng lại time
        assigned_to=row.assigned_to,
        customer_name=row.customer_name,
        phone=row.phone,
        priority=row.priority,
        # Lấy current_status từ DB hoặc từ entry cuối của history
        # current_status = row.current_status or (history[-1].status if history else "Chưa xác định"),
        history=history
    )


def add_new_request(req_data):
    request_id = uuid.uuid4()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql_insert_request = """
            INSERT INTO Requests (id, content, email, category, customer_name, phone, priority, current_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        initial_status = "Đã tiếp nhận"
        cursor.execute(sql_insert_request,
                       request_id,
                       req_data.get('content'),
                       req_data.get('email'),
                       req_data.get('category', 'Chung'),
                       req_data.get('customer_name'),
                       req_data.get('phone'),
                       req_data.get('priority', 'Trung bình'),
                       initial_status # Lưu trạng thái ban đầu
                       )

        sql_insert_history = """
            INSERT INTO StatusHistory (request_id, status, note)
            VALUES (?, ?, ?)
        """
        cursor.execute(sql_insert_history, request_id, initial_status, None)

        conn.commit()
        return str(request_id)

    except pyodbc.Error as ex:
        print(f"Lỗi khi thêm request mới: {ex}")
        if conn:
            conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_request_by_id(request_id):
    conn = None
    cursor = None
    try:
        try:
            req_uuid = uuid.UUID(request_id)
        except ValueError:
            print(f"Invalid UUID format for request_id: {request_id}")
            return None

        conn = get_db_connection()
        cursor = conn.cursor()

        sql_select_request = "SELECT * FROM Requests WHERE id = ?"
        cursor.execute(sql_select_request, req_uuid)
        request_row = cursor.fetchone()

        if not request_row:
            return None

        sql_select_history = "SELECT status, status_time, note FROM StatusHistory WHERE request_id = ? ORDER BY status_time ASC" # Lấy ASC để sắp xếp lại trong Python
        cursor.execute(sql_select_history, req_uuid)
        history_rows = cursor.fetchall()

        return _map_row_to_request(request_row, history_rows)

    except pyodbc.Error as ex:
        print(f"Lỗi khi lấy request theo ID {request_id}: {ex}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_requests_by_email(email):
    conn = None
    cursor = None
    requests_list = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql_select_ids = "SELECT id FROM Requests WHERE email = ?"
        cursor.execute(sql_select_ids, email)
        request_ids = [row.id for row in cursor.fetchall()]

        for req_id_uuid in request_ids:
            request_detail = get_request_by_id(str(req_id_uuid))
            if request_detail:
                requests_list.append(request_detail)

        requests_list.sort(key=lambda r: datetime.strptime(r.created_at, "%Y-%m-%d %H:%M:%S") if r.created_at else datetime.min, reverse=True)

        return requests_list

    except pyodbc.Error as ex:
        print(f"Lỗi khi lấy request theo email {email}: {ex}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_all_requests(status=None, category=None, assigned_to=None):
    conn = None
    cursor = None
    requests_list = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql_base = "SELECT id FROM Requests"
        filters = []
        params = []

        if status:
            filters.append("current_status = ?")
            params.append(status)
        if category:
            filters.append("category = ?")
            params.append(category)
        if assigned_to:
            if assigned_to == "unassigned":
                 filters.append("(assigned_to IS NULL OR assigned_to = '')")
            else:
                 filters.append("assigned_to = ?")
                 params.append(assigned_to)


        if filters:
            sql_base += " WHERE " + " AND ".join(filters)

        cursor.execute(sql_base, params)
        request_ids = [row.id for row in cursor.fetchall()]

        for req_id_uuid in request_ids:
             request_detail = get_request_by_id(str(req_id_uuid))
             if request_detail:
                 requests_list.append(request_detail)

        requests_list.sort(key=lambda r: datetime.strptime(r.created_at, "%Y-%m-%d %H:%M:%S") if r.created_at else datetime.min, reverse=True)


        return requests_list

    except pyodbc.Error as ex:
        print(f"Lỗi khi lấy tất cả requests: {ex}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_request_status(request_id, status, note=None):
    conn = None
    cursor = None
    try:
        try:
            req_uuid = uuid.UUID(request_id)
        except ValueError:
            print(f"Invalid UUID format for request_id: {request_id}")
            return False

        conn = get_db_connection()
        cursor = conn.cursor()

        sql_insert_history = """
            INSERT INTO StatusHistory (request_id, status, note)
            VALUES (?, ?, ?)
        """
        cursor.execute(sql_insert_history, req_uuid, status, note)

        sql_update_request = """
            UPDATE Requests SET current_status = ? WHERE id = ?
        """
        cursor.execute(sql_update_request, status, req_uuid)

        conn.commit()
        return True

    except pyodbc.Error as ex:
        print(f"Lỗi khi cập nhật status cho request {request_id}: {ex}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_request_assignment(request_id, staff_username):
    conn = None
    cursor = None
    try:
        try:
            req_uuid = uuid.UUID(request_id)
        except ValueError: return False

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "UPDATE Requests SET assigned_to = ? WHERE id = ?"
        cursor.execute(sql, staff_username, req_uuid)
        conn.commit()
        return cursor.rowcount > 0
    except pyodbc.Error as ex:
        print(f"Lỗi khi cập nhật assignment cho request {request_id}: {ex}")
        if conn: conn.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def update_request_priority(request_id, priority):
    conn = None
    cursor = None
    try:
        try:
            req_uuid = uuid.UUID(request_id)
        except ValueError: return False

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "UPDATE Requests SET priority = ? WHERE id = ?"
        cursor.execute(sql, priority, req_uuid)
        conn.commit()
        return cursor.rowcount > 0
    except pyodbc.Error as ex:
        print(f"Lỗi khi cập nhật priority cho request {request_id}: {ex}")
        if conn: conn.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# Khởi CSDL để tạo bảng nếu chưa có
def init_db():
    print("Kiểm tra kết nối database...")
    try:
        conn = get_db_connection()
        print("Kết nối database thành công.")
        conn.close()
    except Exception as e:
        print(f"LỖI NGHIÊM TRỌNG: Không thể kết nối hoặc khởi tạo database. {e}")
        raise e
