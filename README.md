# TaskForge CLI Task Manager

TaskForge is a cross-platform command-line task manager built with Python and Typer. It provides a powerful interface for managing tasks with features like prioritization, due dates, tagging, and more.

## Features

- ✅ Create, view, edit, and delete tasks
- 🔄 Mark tasks as completed or uncompleted
- ⭐ Task prioritization (Low, Medium, High, Urgent)
- 📅 Set due dates for tasks
- 🏷️ Tag tasks for organization
- 📋 Filter tasks by completion status or tags
- ⏰ View upcoming tasks with due dates
- 📤 Export tasks to JSON files
- 📥 Import tasks from JSON files
- 📁 Archive and restore tasks
- ⏱️ Snooze tasks to postpone due dates
- 📋 Copy existing tasks
- 🔄 Sync tasks with Rubis scraps

## Installation

1. Ensure you have Python 3.8+ installed
2. Clone this repository
3. Set up a virtual environment:
   ```
   python -m venv venv
   ```
4. Activate the virtual environment:
   - Windows:
   ```
   .\venv\Scripts\activate
   ```
   - macOS/Linux:
   ```
   source venv/bin/activate
   ```
5. Install the required dependencies:
   ```
   pip install typer rich pydantic python-dateutil colorama
   ```

## Usage

TaskForge provides a simple and intuitive command-line interface. Here are some common commands:

### Adding Tasks

```
python taskforge.py add "Complete project report" --desc "Finish the quarterly report" --priority high --due "2025-05-20 17:00" --tags "work,report,urgent"
```

### Listing Tasks

```
# List pending tasks (default)
python taskforge.py list

# List all tasks
python taskforge.py list --all

# List completed tasks
python taskforge.py list --completed

# List tasks with a specific tag
python taskforge.py list --tag work
```

### Task Details

```
python taskforge.py info [TASK_ID]
```

### Completing Tasks

```
python taskforge.py complete [TASK_ID]
```

### Uncompleting Tasks

```
python taskforge.py uncomplete [TASK_ID]
```

### Editing Tasks

```
python taskforge.py edit [TASK_ID] --title "New title" --desc "New description" --priority medium --due "2025-06-01" --tags "updated,tags"
```

### Deleting Tasks

```
python taskforge.py delete [TASK_ID]
```

### Reminders

```
python taskforge.py remind
```

### Prioritizing Tasks

```
python taskforge.py prioritize [TASK_ID] --priority high
# or bump the priority up one level
python taskforge.py prioritize [TASK_ID] --bump
```

### Snoozing Tasks

```
# Postpone a task by 1 day, 2 hours, and 30 minutes
python taskforge.py snooze [TASK_ID] 1d2h30m
```

### Archiving Tasks

```
# Archive a task
python taskforge.py archive [TASK_ID]

# List archived tasks
python taskforge.py list-archived

# Restore an archived task
python taskforge.py restore [TASK_ID]
```

### Copy Tasks

```
python taskforge.py copy [TASK_ID] --due "2025-06-01" --tags "new,tags" --keep-tags
```

### Export and Import

```
# Export tasks to a JSON file
python taskforge.py export tasks_backup.json

# Import tasks from a JSON file
python taskforge.py import tasks_backup.json
```

### Task Synchronization with Rubis

```
# Create a new sync
python taskforge.py sync create

# Update an existing sync
python taskforge.py sync update

# Import tasks from a Rubis scrap
python taskforge.py sync import [SCRAP_URL]

# View sync history
python taskforge.py sync history
```

### Demo

To create some example tasks:

```
python taskforge.py demo
```

## Task Synchronization

TaskForge stores task data locally in the `data` directory and offers integration with the Rubis service for cloud-based task synchronization.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.