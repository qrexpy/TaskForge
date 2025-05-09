#!/usr/bin/env python3

import os
import sys
import time
from datetime import datetime
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from dateutil import parser
from pydantic import ValidationError

import shutil
import platform
import pathlib

from models import Task, Priority
from storage import TaskStorage
from rubis_sync import TaskForgeRubisSync

app = typer.Typer(help="TaskForge: A Cross-Platform CLI Task Manager")
console = Console()
storage = TaskStorage()
rubis_sync = TaskForgeRubisSync()

# Date format for displaying dates
DATE_FORMAT = "%Y-%m-%d %H:%M"

# Add a sync command group for all Rubis-related functionality
sync_app = typer.Typer(help="Sync tasks with Rubis scraps")
app.add_typer(sync_app, name="sync")


def parse_date(date_str: str) -> datetime:
    """Parse a date string into a datetime object."""
    try:
        return parser.parse(date_str)
    except Exception as e:
        raise typer.BadParameter(f"Invalid date format. Please use a standard date format like 'YYYY-MM-DD' or 'MM/DD/YYYY': {e}")


def parse_tags(tags_str: str) -> List[str]:
    """Parse a comma-separated string of tags into a list."""
    if not tags_str:
        return []
    return [tag.strip() for tag in tags_str.split(",")]


def format_task_for_display(task: Task) -> str:
    """Format a task for display in the terminal."""
    priority_colors = {
        Priority.LOW: "blue",
        Priority.MEDIUM: "green",
        Priority.HIGH: "yellow",
        Priority.URGENT: "red",
    }
    
    completion_status = "[green]✓[/green]" if task.completed else "[red]✗[/red]"
    
    priority_text = f"[{priority_colors[task.priority]}]{task.priority.value.upper()}[/{priority_colors[task.priority]}]"
    
    due_date_text = f"Due: [yellow]{task.due_date.strftime(DATE_FORMAT)}[/yellow]" if task.due_date else ""
    completed_text = f"Completed: [green]{task.completed_at.strftime(DATE_FORMAT)}[/green]" if task.completed_at else ""
    
    tags_text = ""
    if task.tags:
        tags_text = " ".join([f"[cyan]#{tag}[/cyan]" for tag in task.tags])
    
    # Build the task display line
    parts = [
        f"{completion_status} {task.id[:8]}",
        f"[bold]{task.title}[/bold]",
        priority_text
    ]
    
    if due_date_text:
        parts.append(due_date_text)
    if completed_text:
        parts.append(completed_text)
    if tags_text:
        parts.append(tags_text)
    
    return " | ".join(parts)


def display_tasks(tasks: List[Task], title: str) -> None:
    """Display a list of tasks in a formatted table."""
    if not tasks:
        console.print(Panel(f"[bold]No tasks found.[/bold]", title=title))
        return
    
    table = Table(title=title, box=box.ROUNDED, show_lines=True)
    table.add_column("Status", justify="center", no_wrap=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Priority", justify="center")
    table.add_column("Due Date")
    table.add_column("Tags")
    
    for task in tasks:
        status = "✓" if task.completed else "✗"
        status_style = "green" if task.completed else "red"
        
        priority_styles = {
            Priority.LOW: "blue",
            Priority.MEDIUM: "green",
            Priority.HIGH: "yellow",
            Priority.URGENT: "red bold",
        }
        
        due_date = task.due_date.strftime(DATE_FORMAT) if task.due_date else ""
        tags = ", ".join([f"#{tag}" for tag in task.tags]) if task.tags else ""
        
        table.add_row(
            f"[{status_style}]{status}[/{status_style}]",
            task.id[:8],
            task.title,
            f"[{priority_styles[task.priority]}]{task.priority.value.upper()}[/{priority_styles[task.priority]}]",
            due_date,
            Text.from_markup(", ".join([f"[cyan]#{tag}[/cyan]" for tag in task.tags]) if task.tags else "")
        )
    
    console.print(table)


def get_attachments_dir(task_id: str) -> str:
    """Get the directory for attachments of a task."""
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        base_dir = os.path.join(appdata, "TaskForge", "attachments")
    else:
        base_dir = os.path.expanduser("~/.config/taskforge/attachments")
    return os.path.join(base_dir, task_id)


@app.command("attach")
def attach_file(task_id: str = typer.Argument(..., help="Task ID to attach file to"),
                file_path: str = typer.Argument(..., help="Path to file to attach")):
    """Attach a file to a task."""
    task = storage.get_task(task_id)
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    attachments_dir = get_attachments_dir(task.id)
    os.makedirs(attachments_dir, exist_ok=True)
    file_name = os.path.basename(file_path)
    dest_path = os.path.join(attachments_dir, file_name)
    try:
        shutil.copy2(file_path, dest_path)
        if file_name not in task.attachments:
            task.attachments.append(file_name)
            storage.update_task(task)
        console.print(f"[green]Attached {file_name} to task {task_id}.[/green]")
    except Exception as e:
        console.print(f"[red]Failed to attach file: {e}[/red]")


@app.command("attachments")
def list_attachments(task_id: str = typer.Argument(..., help="Task ID to list attachments for")):
    """List all attachments for a task in a tree view, including remote (missing) attachments."""
    task = storage.get_task(task_id)
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    attachments_dir = get_attachments_dir(task.id)
    from rich.tree import Tree
    from rich import box
    tree = Tree(f"[bold cyan]Attachments for Task {task_id}[/bold cyan]", guide_style="bold bright_blue")
    # Prefer attachments_tree if present (from sync/import)
    attachments_tree = getattr(task, '_attachments_tree', None)
    if attachments_tree:
        for fname, present in attachments_tree.items():
            fpath = os.path.join(attachments_dir, fname)
            if present and os.path.exists(fpath):
                tree.add(f"[green]{fname}[/green]")
            elif present:
                tree.add(f"[yellow]{fname} (missing locally)[/yellow]")
            else:
                tree.add(f"[dim]{fname} (not available)[/dim]")
    elif not task.attachments:
        tree.add("[dim]No attachments found.[/dim]")
    else:
        for fname in task.attachments:
            fpath = os.path.join(attachments_dir, fname)
            if os.path.exists(fpath):
                tree.add(f"[green]{fname}[/green]")
            else:
                tree.add(f"[yellow]{fname} (not available locally)[/yellow]")
    console.print(tree)


@app.command("open-attachment")
def open_attachment(task_id: str = typer.Argument(..., help="Task ID"),
                   file_name: str = typer.Argument(..., help="Attachment file name")):
    """Open an attached file if available locally."""
    import subprocess
    task = storage.get_task(task_id)
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    if file_name not in task.attachments:
        console.print(f"[red]No such attachment: {file_name}[/red]")
        return
    attachments_dir = get_attachments_dir(task.id)
    file_path = os.path.join(attachments_dir, file_name)
    if not os.path.exists(file_path):
        console.print(f"[yellow]Attachment not available locally.[/yellow]")
        return
    try:
        os.startfile(file_path)
        console.print(f"[green]Opened {file_name}.[/green]")
    except Exception as e:
        console.print(f"[red]Failed to open attachment: {e}[/red]")


@app.command("add")
def add_task(
    title: str = typer.Argument(..., help="The title of the task"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Task description"),
    priority: Priority = typer.Option(Priority.MEDIUM, "--priority", "-p", help="Task priority"),
    due: Optional[str] = typer.Option(None, "--due", help="Due date (e.g., '2025-05-10 14:00', 'tomorrow')"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated list of tags")
):
    """Add a new task."""
    try:
        due_date = parse_date(due) if due else None
        tag_list = parse_tags(tags) if tags else []
        
        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tag_list
        )
        
        storage.add_task(task)
        
        console.print(f"[green]Task added successfully with ID: {task.id[:8]}[/green]")
        console.print(Panel(format_task_for_display(task)))
        
    except ValidationError as e:
        console.print(f"[red]Error creating task: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


@app.command("list")
def list_tasks(
    all: bool = typer.Option(False, "--all", "-a", help="Show all tasks including completed ones"),
    completed: bool = typer.Option(False, "--completed", "-c", help="Show only completed tasks"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter tasks by tag")
):
    """List tasks."""
    filter_completed = None
    if not all:
        filter_completed = True if completed else False
    
    if tag:
        tasks = storage.filter_by_tag(tag)
        title = f"Tasks with tag #{tag}"
        if filter_completed is not None:
            tasks = [t for t in tasks if t.completed == filter_completed]
            status = "completed" if filter_completed else "pending"
            title = f"{status.capitalize()} tasks with tag #{tag}"
    else:
        tasks = storage.list_tasks(completed=filter_completed)
        title = "All Tasks" if all else "Completed Tasks" if completed else "Pending Tasks"
    
    display_tasks(tasks, title)


@app.command("info")
def task_info(task_id: str = typer.Argument(..., help="ID of the task to show")):
    """Show detailed information about a task."""
    task = storage.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    
    # Create a rich panel with task details
    content = []
    content.append(f"[bold]Title:[/bold] {task.title}")
    
    if task.description:
        content.append(f"[bold]Description:[/bold] {task.description}")
    
    content.append(f"[bold]Status:[/bold] {'[green]Completed[/green]' if task.completed else '[yellow]Pending[/yellow]'}")
    
    priority_colors = {
        Priority.LOW: "blue",
        Priority.MEDIUM: "green",
        Priority.HIGH: "yellow",
        Priority.URGENT: "red",
    }
    content.append(f"[bold]Priority:[/bold] [{priority_colors[task.priority]}]{task.priority.value.upper()}[/{priority_colors[task.priority]}]")
    
    content.append(f"[bold]Created:[/bold] {task.created_at.strftime(DATE_FORMAT)}")
    
    if task.due_date:
        content.append(f"[bold]Due Date:[/bold] {task.due_date.strftime(DATE_FORMAT)}")
    
    if task.completed and task.completed_at:
        content.append(f"[bold]Completed At:[/bold] {task.completed_at.strftime(DATE_FORMAT)}")
    
    if task.tags:
        tags_text = " ".join([f"[cyan]#{tag}[/cyan]" for tag in task.tags])
        content.append(f"[bold]Tags:[/bold] {tags_text}")
    
    if task.attachments:
        attachments_text = ", ".join(task.attachments)
        content.append(f"[bold]Attachments:[/bold] {attachments_text}")
    
    panel = Panel("\n".join(content), title=f"Task {task_id[:8]}", expand=False)
    console.print(panel)


@app.command("complete")
def complete_task(task_id: str = typer.Argument(..., help="ID of the task to mark as completed")):
    """Mark a task as completed."""
    task = storage.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    
    if task.completed:
        console.print(f"[yellow]Task {task_id[:8]} is already marked as completed.[/yellow]")
        return
    
    task.complete()
    storage.update_task(task)
    console.print(f"[green]Task {task_id[:8]} marked as completed.[/green]")


@app.command("uncomplete")
def uncomplete_task(task_id: str = typer.Argument(..., help="ID of the task to mark as not completed")):
    """Mark a task as not completed."""
    task = storage.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    
    if not task.completed:
        console.print(f"[yellow]Task {task_id[:8]} is already marked as not completed.[/yellow]")
        return
    
    task.uncomplete()
    storage.update_task(task)
    console.print(f"[green]Task {task_id[:8]} marked as not completed.[/green]")


@app.command("edit")
def edit_task(
    task_id: str = typer.Argument(..., help="ID of the task to edit"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title for the task"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="New description for the task"),
    priority: Optional[Priority] = typer.Option(None, "--priority", "-p", help="New priority for the task"),
    due: Optional[str] = typer.Option(None, "--due", help="New due date (e.g., '2025-05-10 14:00', 'tomorrow')"),
    tags: Optional[str] = typer.Option(None, "--tags", help="New comma-separated list of tags")
):
    """Edit an existing task."""
    task = storage.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    
    try:
        if title is not None:
            task.title = title
        
        if description is not None:
            task.description = description
        
        if priority is not None:
            task.priority = priority
        
        if due is not None:
            if due.lower() == "none":
                task.due_date = None
            else:
                task.due_date = parse_date(due)
        
        if tags is not None:
            if tags.lower() == "none":
                task.tags = []
            else:
                task.tags = parse_tags(tags)
        
        storage.update_task(task)
        console.print(f"[green]Task {task_id[:8]} updated successfully.[/green]")
        console.print(Panel(format_task_for_display(task)))
        
    except ValidationError as e:
        console.print(f"[red]Error updating task: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


@app.command("delete")
def delete_task(
    task_id: str = typer.Argument(..., help="ID of the task to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Delete without confirmation")
):
    """Delete a task."""
    task = storage.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    
    if not force:
        console.print(Panel(format_task_for_display(task)))
        confirm = typer.confirm(f"Are you sure you want to delete this task?")
        if not confirm:
            console.print("[yellow]Task deletion cancelled.[/yellow]")
            return
    
    if storage.delete_task(task_id):
        console.print(f"[green]Task {task_id[:8]} deleted successfully.[/green]")
    else:
        console.print(f"[red]Failed to delete task {task_id[:8]}.[/red]")


@app.command("remind")
def list_reminders():
    """Show upcoming tasks with due dates."""
    now = datetime.now()
    tasks = storage.list_tasks(completed=False)
    
    # Filter tasks with due dates and sort by due date
    due_tasks = [t for t in tasks if t.due_date and t.due_date > now]
    due_tasks.sort(key=lambda t: t.due_date)
    
    if not due_tasks:
        console.print("[yellow]No upcoming tasks with due dates.[/yellow]")
        return
    
    display_tasks(due_tasks, "Upcoming Tasks")


@app.command("archive")
def archive_task(task_id: str = typer.Argument(..., help="ID of the task to archive")):
    """Archive a task to keep it for historical reference without cluttering the main list."""
    task = storage.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    
    archived_task = storage.archive_task(task_id)
    if archived_task:
        console.print(f"[green]Task {task_id[:8]} archived successfully.[/green]")
        console.print(Panel(f"[dim]{format_task_for_display(archived_task)}[/dim]"))
    else:
        console.print(f"[red]Failed to archive task {task_id[:8]}.[/red]")


@app.command("list-archived")
def list_archived_tasks(
    all: bool = typer.Option(False, "--all", "-a", help="Show all archived tasks including completed ones"),
    completed: bool = typer.Option(False, "--completed", "-c", help="Show only completed archived tasks"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter archived tasks by tag")
):
    """List archived tasks."""
    filter_completed = None
    if not all:
        filter_completed = True if completed else False
    
    if tag:
        tasks = storage.filter_by_tag(tag, include_archived=True)
        tasks = [t for t in tasks if t.archived]
        title = f"Archived tasks with tag #{tag}"
        if filter_completed is not None:
            tasks = [t for t in tasks if t.completed == filter_completed]
            status = "completed" if filter_completed else "pending"
            title = f"Archived {status} tasks with tag #{tag}"
    else:
        tasks = storage.list_archived_tasks(completed=filter_completed)
        title = "All Archived Tasks" if all else "Archived Completed Tasks" if completed else "Archived Pending Tasks"
    
    if not tasks:
        console.print(Panel(f"[bold]No archived tasks found.[/bold]", title=title))
        return
    
    table = Table(title=title, box=box.ROUNDED, show_lines=True)
    table.add_column("Status", justify="center", no_wrap=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Priority", justify="center")
    table.add_column("Archived On")
    table.add_column("Tags")
    
    for task in tasks:
        status = "✓" if task.completed else "✗"
        status_style = "green" if task.completed else "red"
        
        priority_styles = {
            Priority.LOW: "blue",
            Priority.MEDIUM: "green",
            Priority.HIGH: "yellow",
            Priority.URGENT: "red bold",
        }
        
        archived_at = task.archived_at.strftime(DATE_FORMAT) if task.archived_at else ""
        
        table.add_row(
            f"[{status_style}]{status}[/{status_style}]",
            task.id[:8],
            task.title,
            f"[{priority_styles[task.priority]}]{task.priority.value.upper()}[/{priority_styles[task.priority]}]",
            archived_at,
            Text.from_markup(", ".join([f"[cyan]#{tag}[/cyan]" for tag in task.tags]) if task.tags else "")
        )
    
    console.print(table)


@app.command("restore")
def restore_task(task_id: str = typer.Argument(..., help="ID of the task to restore from archive")):
    """Restore an archived task to active status."""
    task = storage.get_archived_task(task_id)
    
    if not task:
        console.print(f"[red]Archived task with ID {task_id} not found.[/red]")
        return
    
    restored_task = storage.restore_task(task_id)
    if restored_task:
        console.print(f"[green]Task {task_id[:8]} restored successfully.[/green]")
        console.print(Panel(format_task_for_display(restored_task)))
    else:
        console.print(f"[red]Failed to restore task {task_id[:8]}.[/red]")


@app.command("copy")
def copy_task(
    task_id: str = typer.Argument(..., help="ID of the task to copy"),
    due: Optional[str] = typer.Option(None, "--due", help="New due date for the copied task"),
    tags: Optional[str] = typer.Option(None, "--tags", help="New comma-separated list of tags for the copied task"),
    keep_tags: bool = typer.Option(True, "--keep-tags/--no-keep-tags", help="Keep the original task's tags")
):
    """Duplicate a task, optionally with a new due date or tags."""
    task = storage.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    
    try:
        # Parse due date if provided
        due_date = parse_date(due) if due else None
        
        # Handle tags
        new_tags = None
        if tags:
            new_tags = parse_tags(tags)
            if keep_tags:
                # Combine original tags with new tags, removing duplicates
                new_tags = list(set(task.tags + new_tags))
        
        copied_task = storage.copy_task(task_id, due_date, new_tags)
        if copied_task:
            console.print(f"[green]Task copied successfully with new ID: {copied_task.id[:8]}[/green]")
            console.print(Panel(format_task_for_display(copied_task)))
        else:
            console.print(f"[red]Failed to copy task {task_id[:8]}.[/red]")
    except Exception as e:
        console.print(f"[red]Error copying task: {e}[/red]")


@app.command("snooze")
def snooze_task(
    task_id: str = typer.Argument(..., help="ID of the task to snooze"),
    duration: str = typer.Argument(..., help="Duration to postpone (e.g., 1d, 2h, 30m, 1d2h30m)")
):
    """Postpone a task's due date by a specified time."""
    task = storage.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    
    try:
        # Parse the duration string (e.g., "1d2h30m")
        import re
        
        days = 0
        hours = 0
        minutes = 0
        
        day_match = re.search(r'(\d+)d', duration)
        if day_match:
            days = int(day_match.group(1))
        
        hour_match = re.search(r'(\d+)h', duration)
        if hour_match:
            hours = int(hour_match.group(1))
        
        minute_match = re.search(r'(\d+)m', duration)
        if minute_match:
            minutes = int(minute_match.group(1))
        
        if days == 0 and hours == 0 and minutes == 0:
            console.print("[yellow]No valid duration specified. Use format like 1d, 2h, 30m, or 1d2h30m.[/yellow]")
            return
        
        old_due_date = task.due_date
        updated_task = storage.snooze_task(task_id, days, hours, minutes)
        
        if updated_task:
            old_due_str = old_due_date.strftime(DATE_FORMAT) if old_due_date else "None"
            new_due_str = updated_task.due_date.strftime(DATE_FORMAT) if updated_task.due_date else "None"
            
            console.print(f"[green]Task {task_id[:8]} snoozed successfully.[/green]")
            console.print(f"Due date changed from [yellow]{old_due_str}[/yellow] to [yellow]{new_due_str}[/yellow]")
            console.print(Panel(format_task_for_display(updated_task)))
        else:
            console.print(f"[red]Failed to snooze task {task_id[:8]}.[/red]")
    except Exception as e:
        console.print(f"[red]Error snoozing task: {e}[/red]")


@app.command("prioritize")
def prioritize_task(
    task_id: str = typer.Argument(..., help="ID of the task to prioritize"),
    priority: Optional[Priority] = typer.Option(None, "--priority", "-p", help="Set task priority directly"),
    bump: bool = typer.Option(False, "--bump", "-b", help="Bump task priority up one level")
):
    """Change a task's priority level."""
    task = storage.get_task(task_id)
    
    if not task:
        console.print(f"[red]Task with ID {task_id} not found.[/red]")
        return
    
    old_priority = task.priority
    
    try:
        if priority:
            # Set specific priority
            task.priority = priority
        elif bump:
            # Bump priority up one level
            if task.priority == Priority.LOW:
                task.priority = Priority.MEDIUM
            elif task.priority == Priority.MEDIUM:
                task.priority = Priority.HIGH
            elif task.priority == Priority.HIGH:
                task.priority = Priority.URGENT
            else:
                console.print(f"[yellow]Task {task_id[:8]} is already at the highest priority (URGENT).[/yellow]")
                return
        else:
            # Interactive mode
            console.print("[bold]Select new priority:[/bold]")
            console.print("1. [blue]LOW[/blue]")
            console.print("2. [green]MEDIUM[/green]")
            console.print("3. [yellow]HIGH[/yellow]")
            console.print("4. [red]URGENT[/red]")
            
            choice = typer.prompt("Enter choice (1-4)")
            try:
                choice_num = int(choice)
                if choice_num == 1:
                    task.priority = Priority.LOW
                elif choice_num == 2:
                    task.priority = Priority.MEDIUM
                elif choice_num == 3:
                    task.priority = Priority.HIGH
                elif choice_num == 4:
                    task.priority = Priority.URGENT
                else:
                    console.print("[red]Invalid choice. Please enter a number between 1 and 4.[/red]")
                    return
            except ValueError:
                console.print("[red]Invalid input. Please enter a number.[/red]")
                return
        
        updated_task = storage.update_task(task)
        
        if updated_task:
            priority_colors = {
                Priority.LOW: "blue",
                Priority.MEDIUM: "green",
                Priority.HIGH: "yellow",
                Priority.URGENT: "red",
            }
            
            console.print(f"[green]Task {task_id[:8]} priority updated successfully.[/green]")
            console.print(
                f"Priority changed from [{priority_colors[old_priority]}]{old_priority.value.upper()}[/{priority_colors[old_priority]}] "
                f"to [{priority_colors[task.priority]}]{task.priority.value.upper()}[/{priority_colors[task.priority]}]"
            )
            console.print(Panel(format_task_for_display(updated_task)))
        else:
            console.print(f"[red]Failed to update task {task_id[:8]} priority.[/red]")
    except Exception as e:
        console.print(f"[red]Error updating task priority: {e}[/red]")


@app.command("examples")
def create_examples():
    """Create example tasks with unique IDs."""
    storage.tasks.clear()
    now = datetime.now()
    try:
        task1 = Task(
            title="Complete TaskForge project",
            description="Implement all features for the TaskForge CLI application",
            priority=Priority.HIGH,
            due_date=now.replace(hour=23, minute=59, second=0),
            tags=["coding", "project"]
        )
        storage.add_task(task1)
        time.sleep(0.01)
        task2 = Task(
            title="Buy groceries",
            description="Milk, eggs, bread, fruits",
            priority=Priority.MEDIUM,
            tags=["shopping", "home"]
        )
        storage.add_task(task2)
        time.sleep(0.01)
        task3 = Task(
            title="Call mom",
            priority=Priority.LOW,
            tags=["personal"]
        )
        storage.add_task(task3)
        storage.save_tasks()
        console.print("[green]Example tasks created with unique IDs.[/green]")
    except Exception as e:
        console.print(f"[red]Error creating example tasks: {e}[/red]")


def add_to_path():
    """Add the current file's directory to the system PATH (Windows only)."""
    import subprocess
    dir_path = os.path.dirname(os.path.abspath(__file__))
    command = f'setx PATH "%PATH%;{dir_path}"'
    try:
        subprocess.run(command, shell=True, check=True)
        console.print("[green]TaskForge directory added to PATH successfully.[/green]")
        console.print("[yellow]Note: If the file's path is altered, the command will not work and you will have to re-add the file to PATH with the new file path.[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to add TaskForge to PATH: {e}[/red]")


@app.command("export")
def export_tasks(
    output_file: str = typer.Argument(..., help="Path to export the tasks (JSON format)")
):
    """Export tasks to a JSON file."""
    try:
        storage.save_tasks()
        import shutil
        shutil.copy(storage.storage_file, output_file)
        console.print(f"[green]Tasks exported to {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error exporting tasks: {e}[/red]")


@app.command("import")
def import_tasks(
    input_file: str = typer.Argument(..., help="Path to import tasks from (JSON format)")
):
    """Import tasks from a JSON file."""
    try:
        import shutil
        shutil.copy(input_file, storage.storage_file)
        storage.load_tasks()
        task_count = len(storage.tasks)
        console.print(f"[green]Successfully imported {task_count} tasks from {input_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error importing tasks: {e}[/red]")


# Sync commands
@sync_app.callback(invoke_without_command=True)
def sync(ctx: typer.Context):
    """Sync tasks with Rubis scraps."""
    if ctx.invoked_subcommand is None:
        # Show sync status if no subcommand is provided
        current_sync = rubis_sync.get_current_sync_info()
        
        if current_sync["id"]:
            console.print("[bold]Current Sync Status:[/bold]")
            console.print(f"Scrap ID: [cyan]{current_sync['id']}[/cyan]")
            console.print(f"URL: [link={current_sync['url']}]{current_sync['url']}[/link]")
            console.print(f"Last synced: {current_sync.get('time', 'Unknown')}")
            
            if current_sync.get('access_key'):
                console.print(f"Access Key: [yellow]{current_sync['access_key']}[/yellow] (keep this private)")
        else:
            console.print("[yellow]No active sync found. Use 'create' to start a new sync.[/yellow]")


@sync_app.command("create")
def create_sync(
    public: bool = typer.Option(False, "--public", help="Make the scrap publicly accessible"),
    show_keys: bool = typer.Option(False, "--show-keys", help="Show owner and access keys")
):
    """Create a new sync to Rubis."""
    tasks = storage.list_tasks(show_archived=True)
    
    if not tasks:
        console.print("[yellow]No tasks to sync. Add some tasks first.[/yellow]")
        return
    
    try:
        console.print("[cyan]Creating sync to Rubis...[/cyan]")
        result = rubis_sync.sync_to_rubis(tasks, public=public)
        
        if result.get("url") is None:
            console.print("[yellow]Sync created in offline mode. The Rubis service seems to be unavailable.[/yellow]")
            console.print("[yellow]Your sync information has been saved locally, but the online sync was not completed.[/yellow]")
            console.print("[yellow]Try again later when the Rubis service is available.[/yellow]")
        else:
            console.print("[green]Sync created successfully![/green]")
            console.print(f"Scrap URL: [link={result['url']}]{result['url']}[/link]")
        
        if show_keys:
            console.print()
            console.print("[bold yellow]Keep these keys private:[/bold yellow]")
            console.print(f"Owner Key: [yellow]{result['owner_key']}[/yellow]")
            if result['access_key']:
                console.print(f"Access Key: [yellow]{result['access_key']}[/yellow]")
        else:
            console.print("[dim](Use --show-keys to display owner and access keys)[/dim]")
        
        console.print("\n[bold green]Sync information saved to AppData/TaskForge[/bold green]")
    except Exception as e:
        console.print(f"[red]Error creating sync: {e}[/red]")


@sync_app.command("update")
def update_sync(show_keys: bool = typer.Option(False, "--show-keys", help="Show owner and access keys")):
    """Update an existing sync with current tasks."""
    current_sync = rubis_sync.get_current_sync_info()
    
    if not current_sync["id"]:
        console.print("[yellow]No active sync found. Use 'create' to start a new sync.[/yellow]")
        return
    
    tasks = storage.list_tasks(show_archived=True)
    
    if not tasks:
        console.print("[yellow]No tasks to sync. Add some tasks first.[/yellow]")
        return
    
    try:
        console.print("[cyan]Updating sync on Rubis...[/cyan]")
        result = rubis_sync.update_sync(tasks)
        
        console.print("[green]Sync updated successfully![green]")
        console.print(f"Scrap URL: [link={result['url']}]{result['url']}[/link]")
        
        if show_keys:
            console.print()
            console.print("[bold yellow]Keep these keys private:[/bold yellow]")
            console.print(f"Owner Key: [yellow]{result['owner_key']}[/yellow]")
            if result['access_key']:
                console.print(f"Access Key: [yellow]{result['access_key']}[/yellow]")
    except Exception as e:
        console.print(f"[red]Error updating sync: {e}[/red]")


@sync_app.command("import")
def import_sync(
    scrap_url: Optional[str] = typer.Argument(None, help="URL or ID of the scrap to import"),
    access_key: Optional[str] = typer.Option(None, "--key", "-k", help="Access key for private scraps"),
    merge: bool = typer.Option(False, "--merge", "-m", help="Merge with existing tasks instead of replacing"),
    force: bool = typer.Option(False, "--force", "-f", help="Import without confirmation")
):
    """Import tasks from a Rubis scrap."""
    # If no URL provided, use the saved sync if available
    if not scrap_url:
        current_sync = rubis_sync.get_current_sync_info()
        if current_sync["id"]:
            scrap_url = current_sync["id"]
            access_key = current_sync.get("access_key")
            
            console.print(f"Using saved sync: [cyan]{current_sync['url']}[/cyan]")
        else:
            console.print("[yellow]No URL provided and no saved sync found.[/yellow]")
            return
    
    try:
        console.print("[cyan]Importing tasks from Rubis...[/cyan]")
        imported_tasks = rubis_sync.get_tasks_from_scrap(scrap_url, access_key)
        
        if not imported_tasks:
            console.print("[red]No tasks found in the scrap or unable to access the scrap.[/red]")
            return
        
        console.print(f"[green]Found {len(imported_tasks)} tasks in the scrap.[/green]")
        
        if not force:
            if merge:
                confirm = typer.confirm("Are you sure you want to merge these tasks with your existing tasks?")
            else:
                confirm = typer.confirm("Are you sure you want to replace your current tasks with these?")
            
            if not confirm:
                console.print("[yellow]Import cancelled.[/yellow]")
                return
        
        if merge:
            # Add each imported task to storage
            for task in imported_tasks:
                if not storage.get_task(task.id):
                    storage.add_task(task)
            
            storage.save_tasks()
            console.print(f"[green]Successfully merged {len(imported_tasks)} tasks from Rubis.[/green]")
        else:
            # Replace all tasks
            storage.tasks = {task.id: task for task in imported_tasks}
            storage.save_tasks()
            console.print(f"[green]Successfully replaced local tasks with {len(imported_tasks)} tasks from Rubis.[/green]")
    
    except Exception as e:
        console.print(f"[red]Error importing from Rubis: {e}[/red]")


@sync_app.command("history")
def sync_history():
    """Show sync history."""
    history = rubis_sync.get_sync_history()
    
    if not history:
        console.print("[yellow]No sync history found.[/yellow]")
        return
    
    table = Table(title="Sync History", box=box.ROUNDED)
    table.add_column("Date", style="cyan")
    table.add_column("Scrap ID", style="green")
    table.add_column("URL", style="blue")
    
    for entry in history:
        if entry.get("id"):
            table.add_row(
                entry.get("time", "Unknown"),
                entry["id"],
                f"[link={entry['url']}]{entry['url']}[/link]"
            )
    
    console.print(table)


@sync_app.command("clear")
def clear_sync(force: bool = typer.Option(False, "--force", "-f", help="Clear without confirmation")):
    """Clear saved sync information."""
    if not force:
        confirm = typer.confirm("Are you sure you want to clear all saved sync information?")
        if not confirm:
            console.print("[yellow]Clear operation cancelled.[/yellow]")
            return
    
    rubis_sync.clear_sync_info()
    console.print("[green]Sync information cleared successfully.[/green]")


if __name__ == "__main__":
    app()