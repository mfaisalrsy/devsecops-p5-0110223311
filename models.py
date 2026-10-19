"""
Module: models.py
Defines data structures and domain validation rules for Task and User entities.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    username: str
    password_hash: str
    role: str = "user"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role
        }


@dataclass
class Task:
    id: Optional[int]
    title: str
    description: str
    status: str = "pending"
    owner_id: Optional[int] = None

    def validate(self) -> tuple[bool, Optional[str]]:
        if not self.title or len(self.title.strip()) < 3:
            return False, "Title must be at least 3 characters long."
        if len(self.title) > 100:
            return False, "Title cannot exceed 100 characters."
        if self.status not in ["pending", "in_progress", "completed"]:
            return False, "Invalid task status."
        return True, None

    def to_dict(self):
        return asdict(self)
