from datetime import datetime
from enum import Enum
from typing import List, Optional
import time
from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(BaseModel):
    """Task data model for TaskForge."""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S") + str(int(time.time() * 1000) % 1000))
    title: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    tags: List[str] = Field(default_factory=list)
    archived: bool = False
    archived_at: Optional[datetime] = None
    
    def complete(self):
        """Mark task as completed."""
        self.completed = True
        self.completed_at = datetime.now()
    
    def uncomplete(self):
        """Mark task as not completed."""
        self.completed = False
        self.completed_at = None
        
    def archive(self):
        """Archive the task."""
        self.archived = True
        self.archived_at = datetime.now()
        
    def restore(self):
        """Restore the task from archive."""
        self.archived = False
        self.archived_at = None