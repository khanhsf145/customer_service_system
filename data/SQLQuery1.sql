CREATE DATABASE CustomerServiceDB;
GO
USE CustomerServiceDB;
GO
-- Bảng lưu thông tin chính của các yêu cầu
CREATE TABLE Requests (
    id UNIQUEIDENTIFIER PRIMARY KEY, -- Dùng kiểu UNIQUEIDENTIFIER cho UUID/GUID
    content NVARCHAR(MAX) NOT NULL,
    email NVARCHAR(255) NOT NULL,
    category NVARCHAR(100) DEFAULT N'Chung', -- N'Chung' là giá trị mặc định
    created_at DATETIME2 DEFAULT GETDATE(), -- Tự động lấy ngày giờ hiện tại khi tạo
    assigned_to NVARCHAR(100) NULL, -- Cho phép NULL vì ban đầu chưa phân công
    customer_name NVARCHAR(255) NULL,
    phone NVARCHAR(50) NULL,
    priority NVARCHAR(50) DEFAULT N'Trung bình',
    current_status NVARCHAR(100) NULL -- Lưu trạng thái cuối cùng để truy vấn nhanh
);
GO

-- Bảng lưu lịch sử thay đổi trạng thái
CREATE TABLE StatusHistory (
    history_id BIGINT PRIMARY KEY IDENTITY(1,1), -- Khóa tự tăng
    request_id UNIQUEIDENTIFIER NOT NULL, -- Khóa ngoại liên kết tới Requests
    status NVARCHAR(100) NOT NULL,
    status_time DATETIME2 DEFAULT GETDATE(),
    note NVARCHAR(MAX) NULL,
    -- Tạo Foreign Key constraint
    CONSTRAINT FK_StatusHistory_Requests FOREIGN KEY (request_id)
        REFERENCES Requests (id)
        ON DELETE CASCADE -- Quan trọng: Nếu xóa request thì xóa luôn history liên quan
);
GO

-- (Tùy chọn) Tạo Index để tăng tốc độ truy vấn lịch sử theo request_id
CREATE INDEX IX_StatusHistory_RequestId ON StatusHistory (request_id);
GO

select * from Requests
select * from StatusHistory

CREATE TABLE Users (
    username NVARCHAR(100) PRIMARY KEY,         -- Tên đăng nhập, không trùng lặp
    password_hash NVARCHAR(255) NOT NULL,    -- !! Lưu mật khẩu ĐÃ BĂM, không lưu plaintext !!
    role NVARCHAR(50) NOT NULL DEFAULT 'staff', -- Vai trò: 'admin' hoặc 'staff'
    name NVARCHAR(255) NULL,                  -- Tên hiển thị (tùy chọn)
    email NVARCHAR(255) NULL,                 -- Email (tùy chọn)
    is_active BIT DEFAULT 1                  -- Đánh dấu tài khoản có hoạt động không (1=có, 0=không)
);
GO

-- (Tùy chọn) Có thể thêm các ràng buộc khác nếu cần
-- Ví dụ: CHECK (role IN ('admin', 'staff'))
ALTER TABLE Users ADD CONSTRAINT CHK_UserRole CHECK (role IN ('admin', 'staff'));
GO

INSERT INTO Users (username, password_hash, role, name, is_active) VALUES
('admin', 'scrypt:32768:8:1$N55ciD2XSmXwHkH3$845220fa55f51f76e8de632cbb91f657ee99c73aa9157cb68cb7208ec95c886b03e824bd58ba71b23e5337560be8ff18a8e0132592f833fb854d5ad44b554dd2', 'admin', 'Administrator', 1),
('staff', 'scrypt:32768:8:1$hXrCXs3r4ntm2Eom$914cf0e27c1aa505f46ef816d3ed4e686c55eda7b419c2bc971e798e3ba039ebc4ea1da9a1ba68ac20f7274435ba351d8725890243634c39d5f6c309e49fd474', 'staff', 'Nhân viên', 1);

SELECT username, password_hash FROM Users WHERE username = 'admin';