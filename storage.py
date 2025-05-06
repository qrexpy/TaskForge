import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union

from models import Task


class TaskEncoder(json.JSONEncoder):
    """Custom JSON encoder for Task objects and datetime objects."""
    def default(self, obj):
        if isinstance(obj, Task):
            return obj.model_dump()
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class TaskStorage:
    """Storage handler for tasks, with file system persistence."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.storage_file = os.path.join(data_dir, "tasks.json")
        self.archive_file = os.path.join(data_dir, "archived_tasks.json")
        self.tasks: Dict[str, Task] = {}
        self.archived_tasks: Dict[str, Task] = {}
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load tasks if storage file exists
        self.load_tasks()
        self.load_archived_tasks()
    
    def load_tasks(self) -> None:
        """Load tasks from storage file."""
        if not os.path.exists(self.storage_file):
            return
        
        try:
            with open(self.storage_file, "r") as f:
                task_dicts = json.load(f)
            
            # Convert JSON objects to Task objects
            for task_dict in task_dicts:
                # Convert ISO format strings back to datetime
                if "created_at" in task_dict:
                    task_dict["created_at"] = datetime.fromisoformat(task_dict["created_at"])
                if "due_date" in task_dict and task_dict["due_date"]:
                    task_dict["due_date"] = datetime.fromisoformat(task_dict["due_date"])
                if "completed_at" in task_dict and task_dict["completed_at"]:
                    task_dict["completed_at"] = datetime.fromisoformat(task_dict["completed_at"])
                if "archived_at" in task_dict and task_dict["archived_at"]:
                    task_dict["archived_at"] = datetime.fromisoformat(task_dict["archived_at"])
                
                task = Task(**task_dict)
                self.tasks[task.id] = task
        except Exception as e:
            print(f"Error loading tasks: {e}")
    
    def load_archived_tasks(self) -> None:
        """Load archived tasks from archive file."""
        if not os.path.exists(self.archive_file):
            return
        
        try:
            with open(self.archive_file, "r") as f:
                task_dicts = json.load(f)
            
            # Convert JSON objects to Task objects
            for task_dict in task_dicts:
                # Convert ISO format strings back to datetime
                if "created_at" in task_dict:
                    task_dict["created_at"] = datetime.fromisoformat(task_dict["created_at"])
                if "due_date" in task_dict and task_dict["due_date"]:
                    task_dict["due_date"] = datetime.fromisoformat(task_dict["due_date"])
                if "completed_at" in task_dict and task_dict["completed_at"]:
                    task_dict["completed_at"] = datetime.fromisoformat(task_dict["completed_at"])
                if "archived_at" in task_dict and task_dict["archived_at"]:
                    task_dict["archived_at"] = datetime.fromisoformat(task_dict["archived_at"])
                
                task = Task(**task_dict)
                self.archived_tasks[task.id] = task
        except Exception as e:
            print(f"Error loading archived tasks: {e}")
    
    def serialize_task(self, task: Task) -> dict:
        """Serialize a task to a dictionary with proper datetime handling."""
        task_dict = task.model_dump()
        # Convert datetime objects to strings
        if "created_at" in task_dict:
            task_dict["created_at"] = task_dict["created_at"].isoformat()
        if "due_date" in task_dict and task_dict["due_date"]:
            task_dict["due_date"] = task_dict["due_date"].isoformat()
        if "completed_at" in task_dict and task_dict["completed_at"]:
            task_dict["completed_at"] = task_dict["completed_at"].isoformat()
        if "archived_at" in task_dict and task_dict["archived_at"]:
            task_dict["archived_at"] = task_dict["archived_at"].isoformat()
        return task_dict
    
    def save_tasks(self) -> None:
        """Save tasks to storage file."""
        task_list = list(self.tasks.values())
        
        try:
            # Use explicit serialization for each task
            serialized_tasks = [self.serialize_task(task) for task in task_list]
            
            with open(self.storage_file, "w") as f:
                json.dump(serialized_tasks, f, indent=2)
        except Exception as e:
            print(f"Error saving tasks: {e}")
    
    def save_archived_tasks(self) -> None:
        """Save archived tasks to archive file."""
        task_list = list(self.archived_tasks.values())
        
        try:
            # Use explicit serialization for each task
            serialized_tasks = [self.serialize_task(task) for task in task_list]
            
            with open(self.archive_file, "w") as f:
                json.dump(serialized_tasks, f, indent=2)
        except Exception as e:
            print(f"Error saving archived tasks: {e}")
    
    def add_task(self, task: Task) -> Task:
        """Add a new task to storage."""
        self.tasks[task.id] = task
        self.save_tasks()
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_archived_task(self, task_id: str) -> Optional[Task]:
        """Get an archived task by ID."""
        return self.archived_tasks.get(task_id)
    
    def update_task(self, task_id: str, task: Task) -> Optional[Task]:
        """Update an existing task."""
        if task_id not in self.tasks:
            return None
        
        self.tasks[task_id] = task
        self.save_tasks()
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID."""
        if task_id not in self.tasks:
            return False
        
        del self.tasks[task_id]
        self.save_tasks()
        return True
    
    def archive_task(self, task_id: str) -> Optional[Task]:
        """Archive a task and move it to archived storage."""
        task = self.get_task(task_id)
        if not task:
            return None
        
        task.archive()
        self.archived_tasks[task_id] = task
        del self.tasks[task_id]
        
        self.save_tasks()
        self.save_archived_tasks()
        
        return task
    
    def restore_task(self, task_id: str) -> Optional[Task]:
        """Restore a task from archive to active tasks."""
        task = self.get_archived_task(task_id)
        if not task:
            return None
        
        task.restore()
        self.tasks[task_id] = task
        del self.archived_tasks[task_id]
        
        self.save_tasks()
        self.save_archived_tasks()
        
        return task
    
    def copy_task(self, task_id: str, due_date: Optional[datetime] = None, new_tags: Optional[List[str]] = None) -> Optional[Task]:
        """Create a copy of an existing task."""
        task = self.get_task(task_id)
        if not task:
            return None
        
        # Create a new task with the same properties, but a new ID
        new_task_dict = task.model_dump()
        new_task_dict.pop("id")  # Remove old ID to generate a new one
        
        # Reset completion and archive status for the new task
        new_task_dict["completed"] = False
        new_task_dict["completed_at"] = None
        new_task_dict["archived"] = False
        new_task_dict["archived_at"] = None
        
        # Update due date if provided
        if due_date is not None:
            new_task_dict["due_date"] = due_date
        
        # Update tags if provided
        if new_tags is not None:
            new_task_dict["tags"] = new_tags
        
        new_task = Task(**new_task_dict)
        return self.add_task(new_task)
    
    def snooze_task(self, task_id: str, days: int = 0, hours: int = 0, minutes: int = 0) -> Optional[Task]:
        """Postpone a task's due date by specified time."""
        from datetime import timedelta
        
        task = self.get_task(task_id)
        if not task:
            return None
        
        # If no due date exists, use current date/time
        if task.due_date is None:
            task.due_date = datetime.now()
        
        # Add the specified time to the due date
        time_delta = timedelta(days=days, hours=hours, minutes=minutes)
        task.due_date += time_delta
        
        return self.update_task(task_id, task)
    
    def list_tasks(self, completed: Optional[bool] = None, show_archived: bool = False) -> List[Task]:
        """List all tasks, optionally filtering by completion status."""
        tasks = list(self.tasks.values())
        
        if completed is not None:
            tasks = [task for task in tasks if task.completed == completed]
        
        # Sort by priority (urgent first) and then by due date
        return sorted(tasks, key=lambda t: (
            0 if t.priority == "urgent" else 
            1 if t.priority == "high" else 
            2 if t.priority == "medium" else 3,
            t.due_date if t.due_date else datetime.max
        ))
    
    def list_archived_tasks(self, completed: Optional[bool] = None) -> List[Task]:
        """List archived tasks, optionally filtering by completion status."""
        tasks = list(self.archived_tasks.values())
        
        if completed is not None:
            tasks = [task for task in tasks if task.completed == completed]
        
        # Sort by archived date (newest first)
        return sorted(tasks, key=lambda t: t.archived_at or datetime.min, reverse=True)
    
    def filter_by_tag(self, tag: str, include_archived: bool = False) -> List[Task]:
        """Filter tasks by tag."""
        tasks = [task for task in self.tasks.values() if tag in task.tags]
        
        if include_archived:
            archived_tasks = [task for task in self.archived_tasks.values() if tag in task.tags]
            tasks.extend(archived_tasks)
        
        return tasks