from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import uuid


@dataclass
class StatusHistory:
    """Lịch sử trạng thái của một yêu cầu"""
    status: str
    time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    note: Optional[str] = None


@dataclass
class CustomerRequest:
    """Yêu cầu của khách hàng"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    email: str = ""
    category: str = "Chung"
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    history: List[StatusHistory] = field(default_factory=list)
    assigned_to: Optional[str] = None
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    priority: str = "Trung bình"  # Thấp, Trung bình, Cao, Khẩn cấp

    @property
    def current_status(self) -> str:
        """Trả về trạng thái hiện tại của yêu cầu"""
        if not self.history:
            return "Chưa xử lý"
        return self.history[-1].status

    def add_status(self, status: str, note: Optional[str] = None) -> None:
        """Thêm trạng thái mới vào lịch sử"""
        self.history.append(StatusHistory(
            status=status,
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            note=note
        ))

    def to_dict(self) -> Dict:
        """Chuyển đổi đối tượng thành dictionary để lưu trữ JSON"""
        return {
            "id": self.id,
            "content": self.content,
            "email": self.email,
            "category": self.category,
            "created_at": self.created_at,
            "history": [h.__dict__ for h in self.history],
            "assigned_to": self.assigned_to,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "priority": self.priority
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CustomerRequest':
        """Tạo đối tượng từ dictionary"""
        request = cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", "") or data.get("data", ""),  # Hỗ trợ cả hai trường
            email=data.get("email", ""),
            category=data.get("category", "Chung"),
            created_at=data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            assigned_to=data.get("assigned_to"),
            customer_name=data.get("customer_name"),
            phone=data.get("phone"),
            priority=data.get("priority", "Trung bình")
        )

        # Xử lý lịch sử
        history_data = data.get("history", [])
        for h in history_data:
            if isinstance(h, dict):
                request.history.append(StatusHistory(
                    status=h.get("status", ""),
                    time=h.get("time", ""),
                    note=h.get("note")
                ))

        return request


@dataclass
class User:
    """Người dùng hệ thống"""
    username: str
    password: str
    role: str = "staff"  # admin, staff
    name: str = ""
    email: Optional[str] = None
    is_active: bool = True

    def to_dict(self) -> Dict:
        """Chuyển đối tượng thành dictionary"""
        return {
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "name": self.name,
            "email": self.email,
            "is_active": self.is_active
        }

    @classmethod
    def from_dict(cls, data: Dict, username: str) -> 'User':
        """Tạo đối tượng từ dictionary"""
        return cls(
            username=username,
            password=data.get("password", ""),
            role=data.get("role", "staff"),
            name=data.get("name", ""),
            email=data.get("email"),
            is_active=data.get("is_active", True)
        )