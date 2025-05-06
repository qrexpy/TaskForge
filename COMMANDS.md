# TaskForge CLI Commands Reference

This document provides a quick reference for all TaskForge CLI commands and their functions.

## Task Management Commands

| Command | Description | Example |
|---------|-------------|---------|
| `add` | Add a new task with title, optional description, priority, due date, and tags | `python taskforge.py add "Complete report" --desc "Quarterly summary" --priority high --due "2025-05-20 17:00" --tags "work,report"` |
| `list` | List pending tasks (default behavior) | `python taskforge.py list` |
| `list --all` | List all tasks including completed ones | `python taskforge.py list --all` |
| `list --completed` | List only completed tasks | `python taskforge.py list --completed` |
| `list --tag TAG` | List tasks with a specific tag | `python taskforge.py list --tag work` |
| `info` | Show detailed information about a specific task | `python taskforge.py info 20250506123456` |
| `complete` | Mark a task as completed | `python taskforge.py complete 20250506123456` |
| `uncomplete` | Mark a completed task as not completed | `python taskforge.py uncomplete 20250506123456` |
| `edit` | Edit an existing task (title, description, priority, due date, tags) | `python taskforge.py edit 20250506123456 --title "New title" --priority medium` |
| `delete` | Delete a task | `python taskforge.py delete 20250506123456` |
| `delete --force` | Delete a task without confirmation | `python taskforge.py delete 20250506123456 --force` |

## Advanced Task Management

| Command | Description | Example |
|---------|-------------|---------|
| `archive` | Archive a task to keep it for reference without cluttering the main list | `python taskforge.py archive 20250506123456` |
| `list-archived` | List all archived tasks | `python taskforge.py list-archived` |
| `list-archived --all` | List all archived tasks including completed ones | `python taskforge.py list-archived --all` |
| `list-archived --completed` | List only completed archived tasks | `python taskforge.py list-archived --completed` |
| `list-archived --tag TAG` | List archived tasks with a specific tag | `python taskforge.py list-archived --tag work` |
| `restore` | Restore an archived task to active status | `python taskforge.py restore 20250506123456` |
| `copy` | Duplicate a task | `python taskforge.py copy 20250506123456` |
| `copy --due DATE` | Duplicate a task with a new due date | `python taskforge.py copy 20250506123456 --due "2025-06-01"` |
| `copy --tags TAGS` | Duplicate a task with new tags | `python taskforge.py copy 20250506123456 --tags "newproject,urgent"` |
| `copy --no-keep-tags` | Duplicate a task without keeping original tags | `python taskforge.py copy 20250506123456 --tags "newproject" --no-keep-tags` |
| `snooze` | Postpone a task's due date by specified time | `python taskforge.py snooze 20250506123456 1d` |
| `prioritize` | Change a task's priority interactively | `python taskforge.py prioritize 20250506123456` |
| `prioritize --priority PRIORITY` | Set a task's priority directly | `python taskforge.py prioritize 20250506123456 --priority high` |
| `prioritize --bump` | Bump a task's priority up one level | `python taskforge.py prioritize 20250506123456 --bump` |
| `attach` | Attach a file to a task | `python taskforge.py attach 20250506123456 path/to/file.txt` |
| `attachments` | List all attachments for a task in a tree view | `python taskforge.py attachments 20250506123456` |
| `open-attachment` | Open an attached file (if available locally) | `python taskforge.py open-attachment 20250506123456 file.txt` |

## Reminder & Organization

| Command | Description | Example |
|---------|-------------|---------|
| `remind` | Show upcoming tasks with due dates | `python taskforge.py remind` |

## Data Management

| Command | Description | Example |
|---------|-------------|---------|
| `export` | Export tasks to a JSON file | `python taskforge.py export backup.json` |
| `import` | Import tasks from a JSON file | `python taskforge.py import backup.json` |
| `demo` | Create example tasks for demonstration | `python taskforge.py demo` |

## Task Properties

| Property | Description | Values |
|----------|-------------|--------|
| Title | The name/title of the task | Any text string |
| Description | Detailed description of the task | Any text string |
| Priority | Importance level of the task | `low`, `medium`, `high`, `urgent` |
| Due Date | When the task is due | Date string (e.g., "2025-05-20", "tomorrow") |
| Tags | Categories or labels for the task | Comma-separated list (e.g., "work,urgent,report") |
| Status | Completion status of the task | Completed (✓) or Pending (✗) |
| Archived | Whether the task is archived | Yes/No |

## Command Options

| Option | Short | Description |
|--------|-------|-------------|
| `--desc` | `-d` | Add or update task description |
| `--priority` | `-p` | Set task priority (low, medium, high, urgent) |
| `--due` | - | Set task due date |
| `--tags` | `-t` | Add tags to a task (comma-separated) |
| `--title` | `-t` | Update task title (for edit command) |
| `--all` | `-a` | Show all tasks including completed ones |
| `--completed` | `-c` | Show only completed tasks |
| `--force` | `-f` | Skip confirmation (for delete command) |
| `--bump` | `-b` | Bump priority up one level (for prioritize command) |
| `--keep-tags/--no-keep-tags` | - | Keep or discard original tags when copying a task |

## Snooze Duration Format

When using the `snooze` command, you can specify duration in the following formats:

- `1d` - Snooze for 1 day
- `2h` - Snooze for 2 hours
- `30m` - Snooze for 30 minutes
- `1d2h30m` - Snooze for 1 day, 2 hours, and 30 minutes

## Task ID
Each task is identified by a unique ID that is automatically generated. When referencing a task in commands, you only need to provide the first few characters of the ID as long as they uniquely identify the task.