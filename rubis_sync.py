#!/usr/bin/env python3

import json
import os
import platform
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

from models import Task
from rubis_client import RubisClient

class TaskForgeRubisSync:
    """Handles synchronization of TaskForge tasks with Rubis."""
    
    def __init__(self):
        """Initialize the TaskForge Rubis synchronization."""
        self.client = RubisClient()
        self.sync_dir = self._get_appdata_dir()
        self.sync_file = os.path.join(self.sync_dir, "rubis_sync.json")
        
        # Create the sync directory if it doesn't exist
        os.makedirs(self.sync_dir, exist_ok=True)
        
        # Load saved sync information
        self.sync_info = self._load_sync_info()
    
    def _get_appdata_dir(self) -> str:
        """Get the appropriate AppData directory based on the operating system."""
        system = platform.system()
        
        if system == "Windows":
            appdata = os.environ.get("APPDATA")
            return os.path.join(appdata, "TaskForge")
        elif system == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Application Support/TaskForge")
        else:  # Linux, etc.
            return os.path.expanduser("~/.config/taskforge")
    
    def _load_sync_info(self) -> Dict[str, Any]:
        """Load saved sync information from disk."""
        if not os.path.exists(self.sync_file):
            return {
                "last_sync": None,
                "current_scrap": {
                    "id": None,
                    "owner_key": None,
                    "access_key": None,
                    "url": None
                },
                "history": []
            }
        
        try:
            with open(self.sync_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If there's an error, return default structure
            return {
                "last_sync": None,
                "current_scrap": {
                    "id": None,
                    "owner_key": None,
                    "access_key": None,
                    "url": None
                },
                "history": []
            }
    
    def _save_sync_info(self) -> None:
        """Save current sync information to disk."""
        with open(self.sync_file, "w") as f:
            json.dump(self.sync_info, f, indent=2)
    
    def sync_to_rubis(self, tasks: List[Task], public: bool = False) -> Dict[str, str]:
        """
        Sync tasks to Rubis and save the scrap information.
        
        Args:
            tasks: List of tasks to sync
            public: Whether the scrap should be public
            
        Returns:
            Dict containing scrap URLs and information
        """
        # Convert tasks to JSON for storage
        tasks_json = [task.model_dump() for task in tasks]
        content = json.dumps(tasks_json, indent=2, default=str)
        
        # Generate a random access key if not public
        access_key = None
        if not public:
            import random
            import string
            access_key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        
        # Create a title for the scrap
        title = f"TaskForge Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Create the scrap on Rubis
        try:
            response = self.client.create_scrap(
                content=content,
                title=title,
                public=public,
                access_key=access_key
            )
            
            # Check if there was an API error
            if response.get("error"):
                print(f"Warning: Sync created in offline mode - {response.get('error')}")
                url = None
                raw_url = None
                scrap_id = None
                owner_key = response.get("ownerKey")
            else:
                # Handle different field names from the API
                scrap_id = response.get("scrapID")
                owner_key = response.get("ownerKey")
                
                # Get appropriate URLs from the response
                if public:
                    url = response.get("view")
                    raw_url = response.get("raw")
                else:
                    url = response.get("view_with_key")
                    raw_url = response.get("raw_with_key")
            
            # Save the sync information
            self.sync_info["last_sync"] = datetime.now().isoformat()
            self.sync_info["current_scrap"] = {
                "id": scrap_id,
                "owner_key": owner_key,
                "access_key": access_key,
                "url": url,
                "raw_url": raw_url,
                "time": datetime.now().isoformat()
            }
            
            # Add to history (keep last 10 only)
            self.sync_info["history"].insert(0, self.sync_info["current_scrap"])
            self.sync_info["history"] = self.sync_info["history"][:10]
            
            # Save to disk
            self._save_sync_info()
            
            return {
                "id": scrap_id,
                "url": url,
                "raw_url": raw_url,
                "owner_key": owner_key,
                "access_key": access_key
            }
        except Exception as e:
            # Handle unexpected errors
            print(f"Error during sync: {e}")
            # Generate a fallback owner key if we don't have one
            import random
            import string
            fallback_owner_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            
            # Return basic info to prevent application crashes
            return {
                "id": None,
                "url": None,
                "raw_url": None,
                "owner_key": fallback_owner_key,
                "access_key": access_key
            }
    
    def update_sync(self, tasks: List[Task]) -> Dict[str, str]:
        """
        Update the existing sync scrap with new tasks.
        
        Args:
            tasks: New list of tasks to sync
            
        Returns:
            Dict containing scrap URLs and information or None if no current scrap
        """
        current = self.sync_info["current_scrap"]
        if not current["id"] or not current["owner_key"]:
            # No current scrap, create a new one
            return self.sync_to_rubis(tasks)
        
        try:
            # Convert tasks to JSON for storage
            tasks_json = [task.model_dump() for task in tasks]
            content = json.dumps(tasks_json, indent=2, default=str)
            
            # Update the existing scrap
            response = self.client.replace_scrap_content(
                scrap_id=current["id"],
                owner_key=current["owner_key"],
                content=content
            )
            
            # Check if there was an API error
            if response.get("error"):
                print(f"Warning: Sync update in offline mode - {response.get('error')}")
                # Keep existing URLs if update fails
                url = current["url"]
                raw_url = current.get("raw_url")
            else:
                # Get appropriate URLs from the response
                if "view_with_key" in response:
                    # Private scrap with access key
                    url = response.get("view_with_key")
                    raw_url = response.get("raw_with_key")
                else:
                    # Public scrap
                    url = response.get("view")
                    raw_url = response.get("raw")
            
            # Update the sync information
            self.sync_info["last_sync"] = datetime.now().isoformat()
            
            # Save to disk
            self._save_sync_info()
            
            return {
                "id": current["id"],
                "url": url,
                "raw_url": raw_url,
                "owner_key": current["owner_key"],
                "access_key": current["access_key"]
            }
        except Exception as e:
            # If update fails, create a new scrap
            print(f"Error updating sync, creating a new one: {e}")
            return self.sync_to_rubis(tasks)
    
    def get_tasks_from_scrap(self, scrap_url: str, access_key: Optional[str] = None) -> List[Task]:
        """
        Get tasks from a Rubis scrap.
        
        Args:
            scrap_url: The URL or ID of the scrap
            access_key: Optional access key for private scraps
            
        Returns:
            List of Task objects
        """
        # Extract the scrap ID from the URL
        scrap_id = self.client.extract_scrap_id_from_url(scrap_url)
        if not scrap_id:
            scrap_id = scrap_url  # Assume the URL is actually just the ID
        
        # Use access key from sync info if not provided and it's the current scrap
        if not access_key and self.sync_info["current_scrap"]["id"] == scrap_id:
            access_key = self.sync_info["current_scrap"]["access_key"]
        
        try:
            # Get the raw content of the scrap
            content = self.client.get_raw_scrap_content(
                scrap_id=scrap_id,
                access_key=access_key
            )
            
            # Parse the JSON content into Task objects
            tasks_data = json.loads(content)
            return [Task(**task_data) for task_data in tasks_data]
        except Exception as e:
            return []
    
    def get_current_sync_info(self) -> Dict[str, Any]:
        """Get information about the current sync."""
        return self.sync_info["current_scrap"]
    
    def get_sync_history(self) -> List[Dict[str, Any]]:
        """Get the sync history."""
        return self.sync_info["history"]
    
    def clear_sync_info(self) -> None:
        """Clear all saved sync information."""
        self.sync_info = {
            "last_sync": None,
            "current_scrap": {
                "id": None,
                "owner_key": None,
                "access_key": None,
                "url": None
            },
            "history": []
        }
        self._save_sync_info()