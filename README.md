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

### Export and Import

```
# Export tasks to a JSON file
python taskforge.py export tasks_backup.json

# Import tasks from a JSON file
python taskforge.py import tasks_backup.json
```

### Demo

To create some example tasks:

```
python taskforge.py demo
```

## Task Synchronization

TaskForge stores task data locally in the `data` directory. For task synchronization across devices, you can use:

1. A cloud storage service (like Dropbox, Google Drive) to sync the `data` directory
2. Version control systems like Git
3. Export/import functionality for manual syncing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.