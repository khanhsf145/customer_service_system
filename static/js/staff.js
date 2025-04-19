// static/js/staff.js

const API_BASE_URL = ''; // Base URL is the same origin
let currentRequestId = null; // ID của yêu cầu đang được chọn

// --- Authentication ---
function getToken() {
    return localStorage.getItem('auth_token');
}

function getUserInfo() {
    const info = localStorage.getItem('user_info');
    return info ? JSON.parse(info) : null;
}

function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    window.location.href = '/login.html';
}

function checkAuth() {
    const token = getToken();
    const userInfo = getUserInfo();
    if (!token || !userInfo) {
        logout(); // Nếu không có token hoặc user info, đăng xuất
        return false;
    }
     // Hiển thị thông tin người dùng
    const userInfoElement = document.getElementById('user-info');
    if (userInfoElement) {
        userInfoElement.textContent = `Xin chào, ${userInfo.name || userInfo.username}! (${userInfo.role})`;
    }
    return true;
}

// --- API Calls ---
async function fetchAPI(endpoint, method = 'GET', body = null, requiresAuth = true) {
    const headers = {
        'Content-Type': 'application/json'
    };
    if (requiresAuth) {
        const token = getToken();
        if (!token) {
            console.error('Token not found!');
            logout();
            return null; // Hoặc throw error
        }
        headers['Authorization'] = `Bearer ${token}`;
    }

    const options = {
        method: method,
        headers: headers,
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        if (response.status === 401) { // Unauthorized
             console.error('Token hết hạn hoặc không hợp lệ.');
             logout();
             return null;
        }
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP error ${response.status}` }));
            throw new Error(errorData.error || `HTTP error ${response.status}`);
        }
        if (response.status === 204) { // No Content
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error(`API call to ${endpoint} failed:`, error);
        alert(`Lỗi khi gọi API: ${error.message}`); // Show error to user
        return null; // Return null or throw error depending on desired handling
    }
}

// --- Request List ---
async function fetchRequests() {
    if (!checkAuth()) return;

    const listElement = document.getElementById('requests-list');
    listElement.innerHTML = '<p>Đang tải...</p>';

    const statusFilter = document.getElementById('filter-status').value;
    const assignedFilter = document.getElementById('filter-assigned').value;

    let endpoint = '/staff/requests?';
    if (statusFilter) endpoint += `status=${encodeURIComponent(statusFilter)}&`;
    if (assignedFilter) endpoint += `assigned_to=${encodeURIComponent(assignedFilter)}&`;

    const data = await fetchAPI(endpoint);

    if (data && data.requests) {
        renderRequestList(data.requests);
    } else {
        listElement.innerHTML = '<p>Không thể tải danh sách yêu cầu hoặc không có yêu cầu nào.</p>';
    }
}

function renderRequestList(requests) {
    const listElement = document.getElementById('requests-list');
    if (Object.keys(requests).length === 0) {
        listElement.innerHTML = '<p>Không có yêu cầu nào phù hợp.</p>';
        return;
    }

    let html = '';
    for (const [id, req] of Object.entries(requests)) {
         const status = req.history && req.history.length > 0 ? req.history[req.history.length - 1].status : 'Chưa xác định';
         const isActive = id === currentRequestId ? 'active' : '';
        html += `
            <div class="request-item ${isActive}" id="req-item-${id}" onclick="fetchRequestDetails('${id}')">
                <strong>ID:</strong> ${id.substring(0, 8)}...<br>
                <strong>Trạng thái:</strong> ${status}<br>
                <strong>Email:</strong> ${req.email || 'N/A'} <br>
                <strong>Ưu tiên:</strong> ${req.priority || 'Trung bình'}
            </div>
        `;
    }
    listElement.innerHTML = html;
}


// --- Request Details ---
async function fetchRequestDetails(requestId) {
     if (!checkAuth()) return;
     currentRequestId = requestId; // Cập nhật ID đang chọn
     highlightSelectedItem(requestId); // Đánh dấu item được chọn

    const detailContainer = document.getElementById('request-detail');
    const detailContent = document.getElementById('detail-content');
    const detailHeader = document.getElementById('detail-request-id');

    detailContainer.style.display = 'block'; // Hiển thị khung chi tiết
    detailContent.innerHTML = '<p>Đang tải chi tiết...</p>';
    detailHeader.textContent = `Chi tiết yêu cầu: ${requestId.substring(0, 8)}...`;


    const data = await fetchAPI(`/staff/request/${requestId}`);

    if (data) {
        renderRequestDetails(data);
    } else {
        detailContent.innerHTML = '<p>Không thể tải chi tiết yêu cầu.</p>';
    }
}

function highlightSelectedItem(requestId) {
    // Xóa class 'active' khỏi tất cả các item
    document.querySelectorAll('.request-list-container .request-item').forEach(item => {
        item.classList.remove('active');
    });
    // Thêm class 'active' vào item được chọn
    const selectedItem = document.getElementById(`req-item-${requestId}`);
    if (selectedItem) {
        selectedItem.classList.add('active');
    }
}

function renderRequestDetails(req) {
    const detailContent = document.getElementById('detail-content');
    const userInfo = getUserInfo(); // Lấy thông tin user hiện tại

    let historyHtml = '<p>Chưa có lịch sử.</p>';
    if (req.history && req.history.length > 0) {
        historyHtml = `
            <h4>Lịch sử trạng thái:</h4>
            <table class="table history-table">
                <thead><tr><th>Thời gian</th><th>Trạng thái</th><th>Ghi chú</th></tr></thead>
                <tbody>
        `;
        req.history.forEach(h => {
            historyHtml += `<tr><td>${h.time}</td><td>${h.status}</td><td>${h.note || ''}</td></tr>`;
        });
        historyHtml += '</tbody></table>';
    }

     // Lấy trạng thái hiện tại
    const currentStatus = req.history && req.history.length > 0 ? req.history[req.history.length - 1].status : 'Chưa xác định';


    detailContent.innerHTML = `
        <div class="request-detail-card">
            <p><strong>ID:</strong> ${req.id}</p>
            <p><strong>Email:</strong> ${req.email || 'N/A'}</p>
            <p><strong>Khách hàng:</strong> ${req.customer_name || 'N/A'}</p>
            <p><strong>Điện thoại:</strong> ${req.phone || 'N/A'}</p>
            <p><strong>Ngày tạo:</strong> ${req.created_at}</p>
            <p><strong>Danh mục:</strong> ${req.category || 'Chung'}</p>
            <p><strong>Độ ưu tiên:</strong> ${req.priority || 'Trung bình'}</p>
            <p><strong>Người xử lý:</strong> ${req.assigned_to || 'Chưa phân công'}</p>
            <p><strong>Trạng thái hiện tại:</strong> <span class="status">${currentStatus}</span></p>

            <h4>Nội dung yêu cầu:</h4>
            <p style="background-color: #f0f0f0; padding: 10px; border-radius: 4px;">${req.content || 'Không có nội dung'}</p>

            ${historyHtml}

            <hr>
            <h4>Hành động:</h4>
             ${currentStatus !== 'Đã xử lý' ? `
                <div class="form-group">
                    <label for="action-note">Ghi chú hành động:</label>
                    <textarea id="action-note" placeholder="Nhập ghi chú (nếu có)"></textarea>
                </div>
                 <button class="btn btn-info" onclick="callDcomAction('${req.id}', 'analyze')">Phân tích (DCOM)</button>
                 <button class="btn btn-success" onclick="callDcomAction('${req.id}', 'process')">Xử lý (DCOM)</button>

                <div class="form-group" style="margin-top:1rem;">
                     <label for="update-status">Cập nhật trạng thái:</label>
                     <div style="display:flex; gap: 10px;">
                         <select id="update-status">
                            <option value="Đang kiểm tra">Đang kiểm tra</option>
                            <option value="Chờ phản hồi KH">Chờ phản hồi KH</option>
                            <option value="Đã giải quyết">Đã giải quyết</option>
                            <option value="Đóng yêu cầu">Đóng yêu cầu</option>
                         </select>
                          <button class="btn btn-warning btn-sm" onclick="updateRequestStatus('${req.id}')">Cập nhật</button>
                     </div>
                </div>
             `: '<p>Yêu cầu đã được xử lý.</p>'}


             <h4>Phân công & Ưu tiên:</h4>
             <div class="form-group">
                 <label for="assign-staff">Phân công cho:</label>
                 <div style="display:flex; gap: 10px;">
                      <input type="text" id="assign-staff" placeholder="Nhập username nhân viên" value="${req.assigned_to || ''}">
                      <button class="btn btn-secondary btn-sm" onclick="assignStaff('${req.id}')">Phân công</button>
                 </div>
             </div>
              <div class="form-group">
                 <label for="set-priority">Đặt độ ưu tiên:</label>
                 <div style="display:flex; gap: 10px;">
                     <select id="set-priority">
                        <option value="Thấp" ${req.priority === 'Thấp' ? 'selected' : ''}>Thấp</option>
                        <option value="Trung bình" ${req.priority === 'Trung bình' ? 'selected' : ''}>Trung bình</option>
                        <option value="Cao" ${req.priority === 'Cao' ? 'selected' : ''}>Cao</option>
                        <option value="Khẩn cấp" ${req.priority === 'Khẩn cấp' ? 'selected' : ''}>Khẩn cấp</option>
                     </select>
                     <button class="btn btn-secondary btn-sm" onclick="setPriority('${req.id}')">Đặt</button>
                 </div>
             </div>

        </div>
    `;
}

// --- Actions ---
async function callDcomAction(requestId, actionType) {
    if (!checkAuth() || !requestId) return;
    const note = document.getElementById('action-note').value.trim();
    const endpoint = actionType === 'analyze' ? `/staff/request/${requestId}/analyze` : `/staff/request/${requestId}/process`;

    alert(`Đang thực hiện ${actionType}...`);
    const result = await fetchAPI(endpoint, 'POST', { note: note });

    if (result) {
        alert(`Kết quả ${actionType}: ${result.result}`);
        fetchRequestDetails(requestId); // Tải lại chi tiết
        fetchRequests(); // Tải lại danh sách (để cập nhật trạng thái)
         document.getElementById('action-note').value = ''; // Xóa ghi chú
    } else {
        alert(`Thực hiện ${actionType} thất bại.`);
    }
}

async function updateRequestStatus(requestId) {
    if (!checkAuth() || !requestId) return;
    const status = document.getElementById('update-status').value;
    const note = document.getElementById('action-note').value.trim(); // Lấy ghi chú chung

     if (!status) {
        alert('Vui lòng chọn trạng thái mới.');
        return;
    }

    alert(`Đang cập nhật trạng thái thành: ${status}`);
    const result = await fetchAPI(`/staff/request/${requestId}/status`, 'POST', { status: status, note: note });

    if (result) {
        alert(result.message || 'Đã cập nhật trạng thái.');
        fetchRequestDetails(requestId); // Tải lại chi tiết
        fetchRequests(); // Tải lại danh sách
        document.getElementById('action-note').value = ''; // Xóa ghi chú
    } else {
        alert('Cập nhật trạng thái thất bại.');
    }
}

async function assignStaff(requestId) {
    if (!checkAuth() || !requestId) return;
    const staffUsername = document.getElementById('assign-staff').value.trim();
     if (!staffUsername) {
        alert('Vui lòng nhập username nhân viên.');
        return;
    }
    alert(`Đang phân công cho: ${staffUsername}`);
    const result = await fetchAPI(`/staff/request/${requestId}/assign`, 'POST', { staff_username: staffUsername });

     if (result) {
        alert(result.message || 'Đã phân công yêu cầu.');
        fetchRequestDetails(requestId); // Tải lại chi tiết
        fetchRequests(); // Tải lại danh sách
    } else {
        alert('Phân công thất bại.');
    }
}

async function setPriority(requestId) {
     if (!checkAuth() || !requestId) return;
    const priority = document.getElementById('set-priority').value;
     if (!priority) {
        alert('Vui lòng chọn mức độ ưu tiên.');
        return;
    }
    alert(`Đang đặt ưu tiên: ${priority}`);
    const result = await fetchAPI(`/staff/request/${requestId}/priority`, 'POST', { priority: priority });
     if (result) {
        alert(result.message || 'Đã cập nhật ưu tiên.');
        fetchRequestDetails(requestId); // Tải lại chi tiết
        fetchRequests(); // Tải lại danh sách (có thể cần sort theo prio sau này)
    } else {
        alert('Đặt ưu tiên thất bại.');
    }
}


// --- Initial Load ---
document.addEventListener('DOMContentLoaded', () => {
    if (checkAuth()) {
        fetchRequests(); // Tải danh sách yêu cầu khi trang được tải
    }
});