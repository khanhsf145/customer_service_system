# models/request_model.py

from dataclasses import dataclass

@dataclass
class Request:
    id: str
    content: str
    status: str
