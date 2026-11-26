from __future__ import annotations

import asyncio
from contextlib import closing
from datetime import datetime
from importlib import import_module
import os
import re
import subprocess
import sys
import json
from pathlib import Path
import sqlite3

import flet as ft


def run_status_command(command, output, cwd=None) -> None:
    """Forward stdout and stderr while the command is still running."""
    with subprocess.Popen(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", bufsize=1,
    ) as process:
        for line in process.stdout:
            output(line.rstrip("\n"))
        returncode = process.wait()
    if returncode:
        raise subprocess.CalledProcessError(returncode, command)


async def run_status_command_async(command, output, cwd=None) -> None:
    """Stream command output without blocking Flet's event loop."""
    process = await asyncio.create_subprocess_exec(
        *command, cwd=cwd, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    async for line in process.stdout:
        output(line.decode("utf-8", errors="replace").rstrip("\n"))
    returncode = await process.wait()
    if returncode:
        raise subprocess.CalledProcessError(returncode, command)


def run_automation_action(add_message, label: str, function_name: str, *args) -> str | None:
    """Run one explicitly allowed Laravel automation action safely."""
    print(f"[Taksu] START {label}: automation.laravel.{function_name}({', '.join(map(repr, args))})", flush=True)
    try:
        laravel = import_module("automation.laravel")
        function = getattr(laravel, function_name)
        function(*args)
    except Exception as exc:
        print(f"[Taksu] ERROR {label}: {type(exc).__name__}: {exc}", flush=True)
        add_message(f"{label} failed: {exc}", tag="Backend action error")
        return f"{type(exc).__name__}: {exc}"
    else:
        print(f"[Taksu] DONE  {label}", flush=True)
        add_message(f"{label} completed.", tag="Backend action completed")
        return None



def database_pairs(text: str) -> list[tuple[str, str]]:
    """Read one column=value pair per line for the database forms."""
    pairs = []
    for line in text.splitlines():
        if not line.strip():
            continue
        name, separator, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) or not value:
            raise ValueError("Use one column = value per line, with a valid column name and value.")
        pairs.append((name, value))
    if not pairs:
        raise ValueError("Enter at least one column = value pair.")
    return pairs


def run_database_action(function_name: str, *args):
    """Invoke the existing database module only when a user runs an action."""
    return getattr(import_module("automation.database"), function_name)(*args)

def main(page: ft.Page) -> None:
    page.title = "Taksu AI Workspace"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0b0d12"
    page.padding = 0
    page.window_min_width = 1050
    page.window_min_height = 700

    accent = "#8b5cf6"
    muted = "#8b93a7"
    panel = "#11141b"
    border = "#242936"
    messages = ft.ListView(expand=True, spacing=22, auto_scroll=True)
    workspace_body = ft.Container(expand=True)
    file_picker = ft.FilePicker()
    workspace_title = ft.Text("Overview", size=14, weight=ft.FontWeight.W_600)
    workspace_hint = ft.Text("Taksu Automation workspace", size=12, color=muted)
    composer = ft.TextField(
        hint_text="Ask Taksu anything…",
        multiline=True,
        min_lines=1,
        max_lines=5,
        shift_enter=True,
        expand=True,
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        text_size=14,
    )

    def add_message(text: str, user: bool = False, tag: str = "") -> None:
        now = datetime.now().strftime("%H:%M")
        messages.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Jij" if user else "Taksu", size=12, weight=ft.FontWeight.BOLD, color="#e8eaf0"),
                            ft.Text(now, size=11, color="#626a7d"),
                        ], spacing=8),
                        ft.Text(text, size=14, color="#d8dbe5", selectable=True),
                        ft.Container(ft.Text(tag, size=11, color="#b9a7ff"), padding=8, bgcolor="#211b36", border_radius=8) if tag else ft.Container(height=0),
                    ], spacing=8),
                    padding=ft.Padding(left=16, top=14, right=16, bottom=14),
                    bgcolor="#171a22" if user else "transparent",
                    border_radius=14,
                    border=ft.Border(left=ft.BorderSide(1, border), top=ft.BorderSide(1, border), right=ft.BorderSide(1, border), bottom=ft.BorderSide(1, border)) if user else None,
                ),
            ], alignment=ft.MainAxisAlignment.END if user else ft.MainAxisAlignment.START)
        )
        page.update()

    def send_message(_: ft.ControlEvent | None = None) -> None:
        text = (composer.value or "").strip()
        if not text:
            return
        add_message(text, user=True)
        composer.value = ""
        add_message("I received your request. The automation connection is intentionally disabled. Once your server is ready, we can safely run this request here.", tag="Preview mode · no backend actions executed")
        page.update()

    def preview_action(label: str) -> None:
        add_message(f"{label} is ready, but has not been executed.", tag="Preview mode · automation remains disabled")

    def input_field(label: str, hint: str = "") -> ft.TextField:
        return ft.TextField(label=label, hint_text=hint, dense=True, expand=True, border_radius=10)

    def tool_card(title: str, description: str, fields: list[ft.Control], actions: list[tuple[str, str]], action_handlers: dict[str, object] | None = None) -> ft.Container:
        action_handlers = action_handlers or {}
        buttons = [ft.Button(label, icon=icon, on_click=lambda _, value=label: action_handlers.get(value, lambda: preview_action(value))(), bgcolor="#242032" if index else accent, color="white") for index, (label, icon) in enumerate(actions)]
        return ft.Container(content=ft.Column([ft.Text(title, size=19, weight=ft.FontWeight.W_600), ft.Text(description, size=13, color=muted), ft.Divider(color=border), ft.Row(fields), ft.Row(buttons, wrap=True)], spacing=14), padding=22, bgcolor=panel, border_radius=16, border=ft.Border(left=ft.BorderSide(1, border), top=ft.BorderSide(1, border), right=ft.BorderSide(1, border), bottom=ft.BorderSide(1, border)))

    def render_workspace(name: str) -> None:
        if name == "Overview":
            workspace_body.content = ft.Column([ft.Container(content=ft.Column([ft.Icon(ft.Icons.AUTO_AWESOME, color=accent, size=30), ft.Text("What would you like to automate?", size=27, weight=ft.FontWeight.BOLD), ft.Text("Work with Taksu in a calm, conversational workspace.", size=14, color=muted)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), padding=ft.Padding(left=20, top=85, right=20, bottom=35)), messages, suggestions], expand=True, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        elif name == "Database":
            result = ft.Text("Choose an action and fill in its fields.", selectable=True, color="#52616b")

            def field(label: str, hint: str = "", multiline: bool = False) -> ft.TextField:
                return ft.TextField(label=label, hint_text=hint, multiline=multiline,
                                    min_lines=3 if multiline else 1, expand=True, border_radius=3,
                                    color="#253341", bgcolor="white", border_color="#aab8c4",
                                    label_style=ft.TextStyle(color="#465969"), text_size=13)

            def required(control: ft.TextField) -> str:
                value = (control.value or "").strip()
                if not value:
                    raise ValueError(f"{control.label} is required.")
                return value

            def identifier(control: ft.TextField) -> str:
                value = required(control)
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
                    raise ValueError(f"{control.label} must be a valid identifier (letters, digits, underscore).")
                return value

            def record_id(control: ft.TextField) -> str:
                value = required(control)
                if not value.isdigit():
                    raise ValueError("ID must be a non-negative integer.")
                return value

            def action(label: str, function: str, arguments, show_rows: bool = False):
                def run(_):
                    try:
                        output = run_database_action(function, *arguments())
                        if show_rows:
                            result.value = "\n".join(str(row) for row in output) if output else "No rows found."
                        else:
                            result.value = f"{label}: backend returned without an error."
                        result.color = "#286541"
                    except Exception as exc:
                        result.value = f"{label} failed: {type(exc).__name__}: {exc}"
                        result.color = "#a32929"
                    page.update()
                return run

            def card(title: str, description: str, fields: list[ft.Control], function: str, arguments, show_rows: bool = False) -> ft.Container:
                return ft.Container(content=ft.Column([
                    ft.Container(ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color="#334d60"),
                                 bgcolor="#e5edf3", padding=12),
                    ft.Container(content=ft.Column([
                        ft.Text(description, size=12, color="#52616b"),
                        *fields,
                        ft.Row([ft.Button(title, icon=ft.Icons.PLAY_ARROW,
                                          on_click=action(title, function, arguments, show_rows),
                                          bgcolor="#527995", color="white")], alignment=ft.MainAxisAlignment.END),
                    ], spacing=16), padding=16),
                ], spacing=0), bgcolor="white", border=ft.Border.all(1, "#c5d0d8"))

            sql = field("SQL query", "SELECT * FROM users", True)
            columns = field("Columns", "* or id, name")
            table = field("Table", "users")
            new_database = field("Database name", "my_database")
            new_table = field("Table name", "users")
            definitions = field("Column definitions", "id = INT PRIMARY KEY\nname = VARCHAR(255)", True)
            insert_db, insert_table = field("Database name", "laravel_projects"), field("Table", "users")
            insert_values = field("Column values", "name = Alice\nemail = alice@example.com", True)
            update_db, update_table, update_id = field("Database name", "laravel_projects"), field("Table", "users"), field("ID", "1")
            update_values = field("Column values", "name = Alice", True)
            delete_db, delete_table, delete_id = field("Database name", "laravel_projects"), field("Table", "users"), field("ID", "1")

            sections = {
                "Browse": card("Index table", "View rows from a table in the configured database.", [ft.Row([columns, table])], "index_database", lambda: (required(columns), identifier(table)), True),
                "SQL": card("Run query", "Run SQL using the existing connection. The query function does not return rows or commit changes.", [sql], "query", lambda: (required(sql),)),
                "Structure": card("Create table", "Enter one column = SQL type per line.", [new_table, definitions], "create_table", lambda: (identifier(new_table), database_pairs(required(definitions)))),
                "Insert": card("Insert record", "Enter one column = value per line. Uses the configured database.", [ft.Row([insert_db, insert_table]), insert_values], "insert", lambda: (identifier(insert_db), identifier(insert_table), database_pairs(required(insert_values)))),
                "Update": card("Update record", "Enter the record ID and one column = value per line.", [ft.Row([update_db, update_table, update_id]), update_values], "update", lambda: (identifier(update_db), identifier(update_table), record_id(update_id), database_pairs(required(update_values)))),
                "Delete": card("Delete record", "The existing delete function currently contains an error.", [ft.Row([delete_db, delete_table, delete_id])], "delete", lambda: (identifier(delete_db), identifier(delete_table), record_id(delete_id))),
                "Databases": card("Create database", "The existing backend may report an error after creating a database.", [new_database], "create_database", lambda: (identifier(new_database),)),
            }
            content = ft.Container(content=sections["Browse"], expand=True)
            breadcrumb = ft.Text("Server: configured connection  ›  Browse", size=12, color="#617786")
            tab_buttons = []

            def select_database_section(section: str) -> None:
                content.content = sections[section]
                breadcrumb.value = f"Server: configured connection  ›  {section}"
                for button in tab_buttons:
                    selected = button.content == section
                    button.bgcolor = "#ffffff" if selected else "#d5e0e8"
                    button.color = "#253e51" if selected else "#4d6575"
                page.update()

            for section in sections:
                tab_buttons.append(ft.Button(section, on_click=lambda _, value=section: select_database_section(value),
                                             bgcolor="white" if section == "Browse" else "#d5e0e8",
                                             color="#253e51" if section == "Browse" else "#4d6575"))

            sidebar = ft.Container(width=185, bgcolor="#e2e9ee", padding=16, content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.STORAGE, color="#e58b24", size=25),
                        ft.Text("Database", size=19, weight=ft.FontWeight.BOLD, color="#3d617b")]),
                ft.Divider(color="#c6d2db"),
                ft.Text("SERVER", size=10, weight=ft.FontWeight.BOLD, color="#718796"),
                ft.Row([ft.Icon(ft.Icons.DNS, size=17, color="#6d899c"),
                        ft.Text("Configured connection", size=11, color="#405968", expand=True)]),
                ft.Text("Use the tabs to manage data and tables.", size=11, color="#71818d"),
            ], spacing=14))
            main_panel = ft.Container(expand=True, bgcolor="#f6f8f9", content=ft.Column([
                ft.Container(breadcrumb, bgcolor="#eef2f5", padding=12),
                ft.Container(ft.Row(tab_buttons, wrap=True, spacing=3, run_spacing=3), bgcolor="#c9d7e1", padding=8),
                ft.Container(content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.STORAGE, color="#e19b38", size=23),
                            ft.Text("Database administration", size=21, weight=ft.FontWeight.BOLD, color="#39576b")]),
                    ft.Container(content=ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, size=17, color="#55798e"), result]),
                                 bgcolor="#e5f0f7", padding=12, border=ft.Border.all(1, "#c3dbe9")),
                    content,
                ], spacing=18, scroll=ft.ScrollMode.AUTO, expand=True), padding=20, expand=True),
            ], spacing=0, expand=True))
            workspace_body.content = ft.Row([sidebar, main_panel], spacing=0, expand=True,
                                            vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        elif name == "Laravel":
            project_name = input_field("Project name", "my-laravel-app")
            laravel_frontend = ft.Dropdown(
                label="Frontend (optional)",
                hint_text="Leave blank if no frontend is needed",
                options=[ft.DropdownOption(key=value.lower(), text=value) for value in ["React", "Vue", "Livewire", "Svelte"]],
                expand=True,
            )
            database_select = ft.Dropdown(
                label="Database",
                hint_text="Choose a database",
                options=[ft.DropdownOption(key=value.lower(), text=value) for value in ["MySQL", "PostgreSQL", "SQLite"]],
                expand=True,
            )
            test_select = ft.Dropdown(
                label="PHP testing: Pest of PHPUnit",
                hint_text="Choose Pest or PHPUnit",
                options=[ft.DropdownOption(key=value.lower(), text=value) for value in ["Pest", "PHPUnit"]],
                expand=True,
            )
            status_terminal = ft.TextField(
                value="> Laravel form ready",
                multiline=True,
                read_only=True,
                min_lines=4,
                max_lines=6,
                text_size=12,
                color="#86efac",
                bgcolor="#080b0f",
                border_color="#263238",
            )
            laravel_status = ft.Text("Klaar om te starten", size=13, color=muted)
            terminal_lines = ["> Laravel form ready"]

            def append_laravel_output(line: str) -> None:
                print(f"[Taksu] {line}", flush=True)
                terminal_lines.append(line)
                status_terminal.value = "\n".join(terminal_lines[-6:])
                page.update()

            async def create_laravel_from_form(_: ft.ControlEvent) -> None:
                project = (project_name.value or "").strip()
                frontend = laravel_frontend.value or ""
                database = database_select.value or ""
                test_framework = test_select.value or ""
                terminal_lines[:] = [
                    "> Laravel project requested",
                    f"> project={project or 'none'}",
                    f"> database={database or 'none'}",
                    f"> testing={test_framework or 'none'}",
                    f"> frontend={frontend or 'none'}",
                ]
                status_terminal.value = "\n".join(terminal_lines)
                laravel_status.value = "Bezig met aanmaken…"
                laravel_status.color = "#f4d06f"
                page.update()
                if not project or not database or not test_framework:
                    append_laravel_output("> ERROR: fill in the project name, database and test framework")
                    laravel_status.value = "Formulier onvolledig"
                    laravel_status.color = "#ff756d"
                    page.update()
                    add_message("Fill in the project name and choose a database and test framework.", tag="Laravel form incomplete")
                    return
                create_button.disabled = True
                page.update()
                project_created = False
                try:
                    print(f"[Taksu] START Laravel project: composer create-project laravel/laravel {project}", flush=True)
                    append_laravel_output("> composer create-project laravel/laravel " + project)
                    await run_status_command_async(["composer", "create-project", "laravel/laravel", project, "--no-interaction"], append_laravel_output)
                    if test_framework == "pest":
                        command = ["composer", "require", "pestphp/pest", "--dev"]
                    else:
                        command = ["composer", "require", "phpunit/phpunit", "--dev"]
                    print(f"[Taksu] START testing dependency: {' '.join(command)}", flush=True)
                    append_laravel_output("> installing " + test_framework)
                    await run_status_command_async(command + ["--no-interaction"], append_laravel_output, cwd=os.path.abspath(project))
                    if not os.path.isfile(os.path.join(os.path.abspath(project), "artisan")):
                        raise FileNotFoundError(f"Laravel artisan file missing in {project}")
                    project_created = True
                    append_laravel_output("> saving project in backend_projects")
                    connection = import_module("automation.runtime").mydb
                    cursor = connection.cursor()
                    try:
                        cursor.execute(
                            "INSERT INTO backend_projects (project_name, path) VALUES (%s, %s)",
                            (project, os.path.abspath(project)),
                        )
                        connection.commit()
                    finally:
                        cursor.close()
                    append_laravel_output("> project saved in database")
                except Exception as exc:
                    print(f"[Taksu] ERROR Laravel project: {type(exc).__name__}: {exc}", flush=True)
                    append_laravel_output(f"> ERROR: {exc}")
                    laravel_status.value = "Project aangemaakt, databaseopslag mislukt" if project_created else "Aanmaken mislukt"
                    laravel_status.color = "#ff756d"
                    add_message(f"Laravel project {'database save' if project_created else 'creation'} failed: {exc}", tag="Laravel action error")
                else:
                    print("[Taksu] DONE Laravel project", flush=True)
                    append_laravel_output(f"> KLAAR: Laravel-project {project} is aangemaakt")
                    laravel_status.value = f"Laravel-project {project} is klaar"
                    laravel_status.color = "#52dbc1"
                    add_message("Laravel project created.", tag="Laravel action completed")
                finally:
                    create_button.disabled = False
                    page.update()

            create_button = ft.Button(
                "Create Laravel project", icon=ft.Icons.ADD_BOX,
                on_click=create_laravel_from_form, bgcolor=accent, color="white",
            )

            def show_laravel_form() -> None:
                workspace_body.content = ft.Column([
                    ft.Row([
                        ft.Text("New Laravel project", size=24, weight=ft.FontWeight.BOLD, expand=True),
                        ft.Button("Back to projects", icon=ft.Icons.ARROW_BACK, on_click=lambda _: show_laravel_index()),
                    ]),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Choose a database and test framework. Frontend is optional.", size=13, color=muted),
                            ft.Divider(color=border),
                            ft.Row([project_name, laravel_frontend], spacing=14),
                            ft.Row([database_select, test_select], spacing=14),
                            laravel_status,
                            create_button,
                            ft.Text("Status terminal", size=13, weight=ft.FontWeight.BOLD),
                            status_terminal,
                        ], spacing=14),
                        padding=22, bgcolor=panel, border_radius=16,
                        border=ft.Border.all(1, border),
                    ),
                ], spacing=18, scroll=ft.ScrollMode.AUTO)
                page.update()

            def show_laravel_details(project_id: str) -> None:
                backend_project = None
                frontend_projects = []
                model_projects = []
                model_error = None
                try:
                    frontend_projects, backend_project = import_module("automation.laravel").select_laravel(project_id)
                except Exception as exc:
                    print(f"[Taksu] ERROR select_laravel({project_id}): {type(exc).__name__}: {exc}", flush=True)
                    project_details = [ft.Text(f"Project could not be loaded: {exc}", color="#ff756d", selectable=True)]
                else:
                    project_details = [
                        ft.Text("Backend project", size=17, weight=ft.FontWeight.BOLD),
                        ft.Text(str(backend_project.get("project_name", "")), selectable=True),
                        ft.Text(str(backend_project.get("path", "")), selectable=True),
                    ]
                    frontend_projects = [project for project in (frontend_projects or [])
                                         if int(project.get("backend_project_id", -1)) == int(project_id)]
                    cursor = None
                    try:
                        cursor = import_module("automation.runtime").mydb.cursor(dictionary=True)
                        cursor.execute(
                            "SELECT id, model_name, backend_project_id FROM model_projects WHERE backend_project_id = %s ORDER BY id",
                            (int(project_id),),
                        )
                        model_projects = [model for model in cursor.fetchall()
                                          if int(model.get("backend_project_id", -1)) == int(project_id)]
                    except Exception as exc:
                        model_error = str(exc)
                    finally:
                        if cursor is not None:
                            cursor.close()

                def project_path() -> Path:
                    return (Path(__file__).resolve().parent / str(backend_project["path"])).resolve()

                def show_model_details(model: dict) -> None:
                    name = str(model["model_name"])
                    root = project_path()
                    detail_controls = [
                        ft.Row([
                            ft.Text(f"{name} CRUD details", size=24, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Button("Back to models", icon=ft.Icons.ARROW_BACK,
                                      on_click=lambda _: show_model_list()),
                        ]),
                        ft.Text(f"Model ID: {model.get('id', '—')} · Laravel project: {backend_project.get('project_name', project_id)}"),
                    ]
                    files = [
                        ("Model", root / "app" / "Models" / f"{name}.php"),
                        ("API controller", root / "app" / "Http" / "Controllers" / "Api" / f"{name}Controller.php"),
                        ("Seeder", root / "database" / "seeders" / f"{name}Seeder.php"),
                        ("API routes", root / "routes" / "api.php"),
                        ("Web routes", root / "routes" / "web.php"),
                    ]
                    migration_dir = root / "database" / "migrations"
                    migration_files = sorted(migration_dir.glob("*.php")) if migration_dir.is_dir() else []
                    table_names = set()
                    for path in migration_files:
                        content = path.read_text(encoding="utf-8", errors="replace")
                        if name.lower() in path.name.lower() or re.search(rf"\b{re.escape(name)}\b", content):
                            files.append((f"Migration: {path.name}", path))
                            table_names.update(re.findall(r"Schema::create\(['\"]([^'\"]+)", content))
                    for label, path in files:
                        detail_controls.append(ft.Container(content=ft.Column([
                            ft.Text(label, size=17, weight=ft.FontWeight.BOLD),
                            ft.Text(str(path), size=12, color=muted, selectable=True),
                            ft.Text(path.read_text(encoding="utf-8", errors="replace") if path.is_file() else "File not found.",
                                    selectable=True),
                        ], spacing=8), padding=18, bgcolor=panel, border_radius=12))
                    env_path = root / ".env"
                    env_text = env_path.read_text(encoding="utf-8", errors="replace") if env_path.is_file() else ""
                    if re.search(r"^DB_CONNECTION\s*=\s*['\"]?sqlite['\"]?\s*$", env_text, re.MULTILINE):
                        sqlite_path = root / "database" / "database.sqlite"
                        if sqlite_path.is_file():
                            with closing(sqlite3.connect(sqlite_path.as_uri() + "?mode=ro", uri=True)) as connection:
                                tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                            statuses = [f"{table}: {'migrated' if table in tables else 'not migrated'}" for table in sorted(table_names)]
                        else:
                            statuses = [f"{table}: database file not found" for table in sorted(table_names)]
                    else:
                        statuses = ["Database status available for SQLite projects only."]
                    detail_controls.append(ft.Container(content=ft.Column([
                        ft.Text("Database tables", size=17, weight=ft.FontWeight.BOLD),
                        *[ft.Text(status, selectable=True) for status in (statuses or ["No model migration found."])],
                    ]), padding=18, bgcolor=panel, border_radius=12))
                    workspace_body.content = ft.Column(detail_controls, spacing=18, scroll=ft.ScrollMode.AUTO)
                    page.update()

                def show_frontend_details(frontend: dict) -> None:
                    name = str(frontend.get("project_name", "Unnamed frontend"))
                    path = Path(str(frontend.get("path", "")))
                    if not path.is_absolute():
                        path = Path(__file__).resolve().parent / path
                    package_file = path / "package.json"
                    workspace_body.content = ft.Column([
                        ft.Row([
                            ft.Text(f"{name} frontend details", size=24, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Button("Back to frontends", icon=ft.Icons.ARROW_BACK,
                                      on_click=lambda _: show_frontend_list()),
                        ]),
                        ft.Text(f"Frontend ID: {frontend.get('id', '—')} · Laravel project: {backend_project.get('project_name', project_id)}"),
                        ft.Text(f"Path: {path}", selectable=True),
                        ft.Container(content=ft.Column([
                            ft.Text("package.json", size=17, weight=ft.FontWeight.BOLD),
                            ft.Text(package_file.read_text(encoding="utf-8", errors="replace")
                                    if package_file.is_file() else "File not found.", selectable=True),
                        ]), padding=18, bgcolor=panel, border_radius=12),
                    ], spacing=18, scroll=ft.ScrollMode.AUTO)
                    page.update()

                def show_model_list() -> None:
                    rows = [ft.Text("Previously generated CRUD models", size=24, weight=ft.FontWeight.BOLD)]
                    if model_error:
                        rows.append(ft.Text(f"Models could not be loaded: {model_error}", color="#ff756d"))
                    elif model_projects:
                        for model in model_projects:
                            rows.append(ft.Row([
                                ft.Text(str(model["model_name"]), expand=True),
                                ft.Button(f"Open {model['model_name']}",
                                          on_click=lambda _, item=model: show_model_details(item)),
                            ]))
                    else:
                        rows.append(ft.Text("No models linked to this Laravel project.", color=muted))
                    workspace_body.content = ft.Column([
                        ft.Button("Back to project", icon=ft.Icons.ARROW_BACK,
                                  on_click=lambda _: show_laravel_details(project_id)),
                        ft.Container(content=ft.Column(rows, spacing=12), padding=22,
                                     bgcolor=panel, border_radius=16),
                    ], spacing=18, scroll=ft.ScrollMode.AUTO)
                    page.update()

                def show_frontend_list() -> None:
                    rows = [ft.Text("Previously created frontends", size=24, weight=ft.FontWeight.BOLD)]
                    try:
                        linked_frontends, _ = import_module("automation.laravel").select_laravel(project_id)
                        linked_frontends = [frontend for frontend in (linked_frontends or [])
                                            if int(frontend.get("backend_project_id", -1)) == int(project_id)]
                    except Exception as exc:
                        rows.append(ft.Text(f"Frontends could not be loaded: {exc}", color="#ff756d"))
                    else:
                        if linked_frontends:
                            for frontend in linked_frontends:
                                rows.append(ft.Row([
                                    ft.Column([
                                        ft.Text(str(frontend.get("project_name", "Unnamed frontend"))),
                                        ft.Text(str(frontend.get("path", "")), size=12, color=muted, selectable=True),
                                    ], expand=True),
                                    ft.Button(f"Open frontend {frontend.get('project_name', '')}",
                                              on_click=lambda _, item=frontend: show_frontend_details(item)),
                                ]))
                        else:
                            rows.append(ft.Text("No frontend projects linked.", color=muted))
                    workspace_body.content = ft.Column([
                        ft.Button("Back to project", icon=ft.Icons.ARROW_BACK,
                                  on_click=lambda _: show_laravel_details(project_id)),
                        ft.Container(content=ft.Column(rows, spacing=12), padding=22,
                                     bgcolor=panel, border_radius=16),
                    ], spacing=18, scroll=ft.ScrollMode.AUTO)
                    page.update()
                crud_model_name = input_field("Model name", "Task")
                crud_status = ft.Text("", size=13, color=muted)

                async def generate_selected_crud(_: ft.ControlEvent) -> None:
                    model = (crud_model_name.value or "").strip()
                    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", model):
                        crud_status.value = "Enter a valid model name."
                        crud_status.color = "#ff756d"
                        page.update()
                        return
                    if not backend_project or not backend_project.get("path"):
                        crud_status.value = "The selected project has no saved path."
                        crud_status.color = "#ff756d"
                        page.update()
                        return
                    project_path = os.path.abspath(os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), str(backend_project["path"])
                    ))
                    if not os.path.isfile(os.path.join(project_path, "artisan")):
                        crud_status.value = "Laravel artisan file not found in the selected project."
                        crud_status.color = "#ff756d"
                        page.update()
                        return
                    crud_button.disabled = True
                    crud_status.value = f"Generating CRUD for {model}…"
                    crud_status.color = "#f4d06f"
                    page.update()
                    files_created = False
                    try:
                        await run_status_command_async(
                            ["php", "artisan", "make:model", model, "-m", "-s"],
                            lambda line: print(f"[Taksu] {line}", flush=True), cwd=project_path,
                        )
                        await run_status_command_async(
                            ["php", "artisan", "make:controller", f"Api/{model}Controller", "--api", f"--model={model}"],
                            lambda line: print(f"[Taksu] {line}", flush=True), cwd=project_path,
                        )
                        files_created = True
                        connection = import_module("automation.runtime").mydb
                        cursor = connection.cursor()
                        try:
                            cursor.execute(
                                "INSERT INTO model_projects (model_name, backend_project_id) VALUES (%s, %s)",
                                (model, int(project_id)),
                            )
                            connection.commit()
                        except Exception:
                            connection.rollback()
                            raise
                        finally:
                            cursor.close()
                    except Exception as exc:
                        crud_status.value = (
                            f"CRUD files created, database save failed: {exc}"
                            if files_created else f"CRUD generation failed: {exc}"
                        )
                        crud_status.color = "#ff756d"
                        add_message(f"Laravel CRUD failed: {exc}", tag="Laravel action error")
                    else:
                        crud_status.value = f"CRUD files for {model} created and model saved."
                        crud_status.color = "#52dbc1"
                        saved_model = {"id": cursor.lastrowid, "model_name": model,
                                       "backend_project_id": int(project_id)}
                        model_projects.append(saved_model)
                        add_message(f"Laravel CRUD files for {model} created and model saved.", tag="Laravel action completed")
                    finally:
                        crud_button.disabled = False
                        page.update()

                crud_button = ft.Button(
                    "Generate CRUD", icon=ft.Icons.BUILD,
                    on_click=generate_selected_crud, bgcolor=accent, color="white",
                )
                selected_framework = ft.Dropdown(
                    label="Framework",
                    hint_text="Choose a framework",
                    options=[
                        ft.DropdownOption(key="react", text="React"),
                        ft.DropdownOption(key="react-admin", text="React Admin"),
                        ft.DropdownOption(key="expo", text="Expo"),
                        ft.DropdownOption(key="nextJS", text="Next.js"),
                    ],
                    expand=True,
                )
                frontend_name = input_field("Frontend project name", "frontend-app")
                frontend_status = ft.TextField(
                    value="> Frontend form ready", multiline=True, read_only=True,
                    min_lines=4, max_lines=6, text_size=12, color="#86efac",
                    bgcolor="#080b0f", border_color="#263238",
                )
                frontend_lines = ["> Frontend form ready"]

                def append_frontend_output(line: str) -> None:
                    print(f"[Taksu] {line}", flush=True)
                    frontend_lines.append(line)
                    frontend_status.value = "\n".join(frontend_lines[-6:])
                    page.update()

                async def create_selected_frontend(_: ft.ControlEvent) -> None:
                    name = (frontend_name.value or "").strip()
                    framework = selected_framework.value or ""
                    if not framework or not name:
                        append_frontend_output("> ERROR: choose a framework and enter a project name")
                        return
                    frontend_button.disabled = True
                    frontend_lines[:] = [f"> Creating {name} for selected Laravel project #{project_id}"]
                    frontend_status.value = frontend_lines[0]
                    page.update()
                    try:
                        await run_status_command_async(
                            [sys.executable, "-u", "-c",
                             "import json, sys; from automation import frontend; frontend.create_frontend(*json.loads(sys.argv[1]))",
                             json.dumps([
                                framework,
                                int(project_id),
                                name,
                                os.path.join(
                                    os.path.dirname(os.path.abspath(__file__)),
                                    "projects",
                                    "frontend_projects"
                                )
                            ])],
                            append_frontend_output,
                            cwd=os.path.dirname(os.path.abspath(__file__)),
                        )
                    except (OSError, subprocess.CalledProcessError) as exc:
                        append_frontend_output(f"> ERROR: {exc}")
                        add_message(f"Frontend project failed: {exc}", tag="Frontend action error")
                    else:
                        append_frontend_output(f"> KLAAR: frontend project {name} created")
                        add_message(f"Frontend project {name} created.", tag="Frontend action completed")
                    finally:
                        frontend_button.disabled = False
                        page.update()

                frontend_button = ft.Button(
                    "Create frontend", icon=ft.Icons.ADD_BOX,
                    on_click=create_selected_frontend, bgcolor=accent, color="white",
                )
                workspace_body.content = ft.Column([
                    ft.Row([
                        ft.Text(f"Laravel project #{project_id}", size=24, weight=ft.FontWeight.BOLD, expand=True),
                        ft.Button("Refresh project", on_click=lambda _: show_laravel_details(project_id)),
                        ft.Button("Back to projects", icon=ft.Icons.ARROW_BACK, on_click=lambda _: show_laravel_index()),
                    ]),
                    ft.Container(content=ft.Column(project_details, spacing=12), padding=22, bgcolor=panel, border_radius=16),
                    *([ft.Container(
                        content=ft.Column([
                            ft.Text("Generate CRUD", size=19, weight=ft.FontWeight.W_600),
                            ft.Text("Generate a model, migration, seeder and API controller for this Laravel project.", color=muted),
                            crud_model_name,
                            ft.Row([
                                crud_button,
                                ft.Button("View existing models", on_click=lambda _: show_model_list()),
                            ], spacing=12),
                            crud_status,
                        ], spacing=14),
                        padding=22, bgcolor=panel, border_radius=16,
                        border=ft.Border.all(1, border),
                    )] if backend_project else []),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Create frontend", size=19, weight=ft.FontWeight.W_600),
                            ft.Row([selected_framework, frontend_name], spacing=14),
                            ft.Row([
                                frontend_button,
                                ft.Button("View existing frontends", on_click=lambda _: show_frontend_list()),
                            ], spacing=12),
                            ft.Text("Status terminal", size=13, weight=ft.FontWeight.BOLD),
                            frontend_status,
                        ], spacing=14),
                        padding=22, bgcolor=panel, border_radius=16,
                        border=ft.Border.all(1, border),
                    ),
                ], spacing=18, scroll=ft.ScrollMode.AUTO)
                page.update()

            laravel_setup_status = ft.Text("", size=12, color=muted)

            def initialize_laravel_database(_: ft.ControlEvent) -> None:
                laravel_setup_status.value = "Initializing Laravel database…"
                laravel_setup_status.color = "#f4d06f"
                setup_button.disabled = True
                page.update()
                try:
                    error = run_automation_action(add_message, "Laravel database", "insert_laravel_database")
                    if error:
                        laravel_setup_status.value = f"Database setup failed: {error}"
                        laravel_setup_status.color = "#ff756d"
                    else:
                        laravel_setup_status.value = "Laravel database initialized."
                        laravel_setup_status.color = "#52dbc1"
                        show_laravel_index()
                finally:
                    setup_button.disabled = False
                    page.update()

            setup_button = ft.Button(
                "Initialize database", icon=ft.Icons.STORAGE_OUTLINED,
                on_click=initialize_laravel_database, bgcolor="#242032", color="white",
            )

            def show_laravel_index() -> None:
                try:
                    projects = import_module("automation.laravel").index_laravel()
                except Exception as exc:
                    print(f"[Taksu] ERROR index_laravel: {type(exc).__name__}: {exc}", flush=True)
                    project_rows = [ft.Text(f"Projects could not be loaded: {exc}", color="#ff756d", selectable=True)]
                else:
                    def display_value(value) -> str:
                        if isinstance(value, (list, tuple, set)):
                            return ", ".join(map(str, value)) or "—"
                        return str(value) if value is not None and value != "" else "—"

                    project_rows = [ft.Row([
                        ft.DataTable(
                            columns=[ft.DataColumn(label) for label in ["Project", "Frontend", "Packages", "Database", "Path", "Action"]],
                            rows=[ft.DataRow(cells=[
                                ft.DataCell(ft.Text(display_value(project.get("project_name")))),
                                ft.DataCell(ft.Text(display_value(project.get("frontend")))),
                                ft.DataCell(ft.Text(display_value(project.get("packages")))),
                                ft.DataCell(ft.Text(display_value(project.get("database")))),
                                ft.DataCell(ft.Text(display_value(project.get("path")))),
                                ft.DataCell(ft.Button("Open", on_click=lambda _, project_id=str(project["id"]): show_laravel_details(project_id))),
                            ]) for project in projects],
                            bgcolor=panel,
                            border_radius=12,
                        ),
                    ], scroll=ft.ScrollMode.AUTO)] if projects else [ft.Text("No Laravel projects found.", color=muted)]
                workspace_body.content = ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text("Laravel projects", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("Projects from automation.laravel.index_laravel().", color=muted),
                        ], expand=True),
                        ft.Button("Refresh", icon=ft.Icons.REFRESH, on_click=lambda _: show_laravel_index()),
                        setup_button,
                        ft.Button("Create", icon=ft.Icons.ADD, on_click=lambda _: show_laravel_form(), bgcolor=accent, color="white"),
                    ]),
                    laravel_setup_status,
                    *project_rows,
                ], spacing=16, scroll=ft.ScrollMode.AUTO)
                page.update()

            show_laravel_index()
        elif name == "Git":
            branch_select = ft.Dropdown(label="Branch", value="main", options=[ft.DropdownOption(key="main", text="main"), ft.DropdownOption(key="develop", text="develop")], width=220)
            selected_files: list[str] = []
            selected_files_view = ft.Column(spacing=6)
            async def choose_files(_: ft.ControlEvent) -> None:
                files = await file_picker.pick_files(dialog_title="Select files to commit", allow_multiple=True, file_type=ft.FilePickerFileType.ANY)
                if files:
                    selected_files.clear()
                    selected_files.extend(file.name for file in files)
                    selected_files_view.controls = [ft.Row([ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=15, color="#a78bfa"), ft.Text(file, size=12, color="#d8dbe5")], spacing=8) for file in selected_files]
                    page.update()
            def commit_selected() -> None:
                if not selected_files:
                    add_message("Select at least one file before creating a commit.", tag="Git · files required")
                    return
                preview_action(f"Commit {len(selected_files)} selected file(s)")
            repo_header = ft.Container(content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.ACCOUNT_TREE, color="#8b93a7", size=24), ft.Column([ft.Text("TaksuAutomatisation", size=21, weight=ft.FontWeight.W_600), ft.Text("musa / TaksuAutomatisation", size=12, color=muted)], spacing=3, expand=True), ft.Container(content=ft.Text("Public", size=11, color="#a78bfa"), padding=ft.Padding(left=10, top=5, right=10, bottom=5), border_radius=20, bgcolor="#211b36")]),
                ft.Text("Automation workspace for database, Laravel, Git and frontend tasks.", size=13, color=muted),
                ft.Row([ft.Text("★ 0", color="#b9c0cf", size=12), ft.Text("⑂ 0 forks", color="#b9c0cf", size=12), ft.Text("◉ Python", color="#b9c0cf", size=12)], spacing=18),
            ], spacing=13), padding=22, bgcolor=panel, border_radius=16, border=ft.Border(left=ft.BorderSide(1, border), top=ft.BorderSide(1, border), right=ft.BorderSide(1, border), bottom=ft.BorderSide(1, border)))
            repo_tabs = ft.Row([ft.Button("Code", icon=ft.Icons.CODE, bgcolor="#242032", color="white"), ft.Button("Issues  0", icon=ft.Icons.ERROR_OUTLINE, bgcolor="transparent", color="#abb2c3"), ft.Button("Pull requests  0", icon=ft.Icons.MERGE, bgcolor="transparent", color="#abb2c3")], spacing=4)
            sync_card = ft.Container(content=ft.Row([ft.Column([ft.Text("Repository status", size=15, weight=ft.FontWeight.W_600), ft.Text("Working tree clean · last sync not connected", size=12, color=muted)], expand=True), branch_select, ft.Button("Fetch", icon=ft.Icons.DOWNLOAD, on_click=lambda _: preview_action("Fetch repository"), bgcolor="#242032", color="white"), ft.Button("Pull", icon=ft.Icons.SYNC, on_click=lambda _: preview_action(f"Pull {branch_select.value or 'main'}"), bgcolor=accent, color="white")], alignment=ft.MainAxisAlignment.CENTER), padding=16, bgcolor=panel, border_radius=14, border=ft.Border(left=ft.BorderSide(1, border), top=ft.BorderSide(1, border), right=ft.BorderSide(1, border), bottom=ft.BorderSide(1, border)))
            commit_card = ft.Container(content=ft.Column([ft.Row([ft.Column([ft.Text("Recent commits", size=16, weight=ft.FontWeight.W_600), ft.Text("main · 3 commits", size=12, color=muted)], expand=True), ft.Button("View all", bgcolor="transparent", color="#a78bfa")]), ft.Divider(color=border), ft.Row([ft.Container(width=28, height=28, border_radius=20, bgcolor="#2d3342", content=ft.Icon(ft.Icons.PERSON_OUTLINE, size=16, color="#cbd5e1")), ft.Column([ft.Text("Initial automation workspace", size=13), ft.Text("musa · just now", size=11, color=muted)], spacing=2, expand=True), ft.Text("main", size=11, color="#a78bfa")]), ft.Row([ft.Container(width=28, height=28, border_radius=20, bgcolor="#2d3342", content=ft.Icon(ft.Icons.PERSON_OUTLINE, size=16, color="#cbd5e1")), ft.Column([ft.Text("Add project structure", size=13), ft.Text("musa · earlier", size=11, color=muted)], spacing=2, expand=True), ft.Text("main", size=11, color="#a78bfa")])], spacing=14), padding=20, bgcolor=panel, border_radius=14, border=ft.Border(left=ft.BorderSide(1, border), top=ft.BorderSide(1, border), right=ft.BorderSide(1, border), bottom=ft.BorderSide(1, border)))
            commit_message = input_field("Commit message", "Describe your changes")
            file_selection = ft.Container(content=ft.Column([ft.Row([ft.Column([ft.Text("Changes to commit", size=15, weight=ft.FontWeight.W_600), ft.Text("Select the documents you want included in this commit.", size=12, color=muted)], expand=True), ft.Button("Select files", icon=ft.Icons.FOLDER_OPEN, on_click=choose_files, bgcolor="#242032", color="white")]), selected_files_view], spacing=12), padding=16, bgcolor=panel, border_radius=14, border=ft.Border(left=ft.BorderSide(1, border), top=ft.BorderSide(1, border), right=ft.BorderSide(1, border), bottom=ft.BorderSide(1, border)))
            commit_action = ft.Container(content=ft.Row([commit_message, ft.Button("Commit selected files", icon=ft.Icons.SAVE, on_click=lambda _: commit_selected(), bgcolor=accent, color="white")]), padding=16, bgcolor=panel, border_radius=14, border=ft.Border(left=ft.BorderSide(1, border), top=ft.BorderSide(1, border), right=ft.BorderSide(1, border), bottom=ft.BorderSide(1, border)))
            workspace_body.content = ft.Column([ft.Row([ft.Column([ft.Text("GitHub", size=24, weight=ft.FontWeight.BOLD), ft.Text("A familiar repository view for your automation project.", color=muted)], expand=True), ft.Button("New pull request", icon=ft.Icons.ADD, on_click=lambda _: preview_action("Open pull request"), bgcolor="#242032", color="white")]), repo_header, repo_tabs, sync_card, commit_card, file_selection, commit_action], spacing=16, scroll=ft.ScrollMode.AUTO)
        else:
            print("[Taksu] Frontend workspace loaded: install and run controls ready", flush=True)
            package_name = input_field("Package", "flet")
            frontend_path = input_field("Project path", "./frontend")
            frontend_status = ft.TextField(
                value="> Frontend tools ready",
                multiline=True,
                read_only=True,
                min_lines=4,
                max_lines=6,
                text_size=12,
                color="#86efac",
                bgcolor="#080b0f",
                border_color="#263238",
            )

            def frontend_action(label: str, function_name: str, *args) -> None:
                frontend_status.value = f"> START {label}"
                page.update()
                def output(line: str) -> None:
                    frontend_status.value += "\n" + line
                    page.update()

                try:
                    run_status_command(
                        [sys.executable, "-u", "-c",
                         "import json, sys; from automation import frontend; getattr(frontend, sys.argv[1])(*json.loads(sys.argv[2]))",
                         function_name, json.dumps(args)],
                        output,
                        cwd=os.path.dirname(os.path.abspath(__file__)),
                    )
                except (OSError, subprocess.CalledProcessError) as exc:
                    output(f"> ERROR {exc}")
                    add_message(f"{label} failed: {exc}", tag="Backend action error")
                else:
                    output(f"> DONE {label}")
                    add_message(f"{label} completed.", tag="Backend action completed")

            workspace_body.content = ft.Column([
                ft.Text("Frontend tools", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Create a frontend from a selected Laravel project. Manage packages and run it here.", color=muted),
                tool_card(
                    "Install package",
                    "Calls automation.frontend.download_package_frontend(name).",
                    [package_name],
                    [("Install", ft.Icons.DOWNLOAD)],
                    {"Install": lambda: frontend_action("Frontend package", "download_package_frontend", package_name.value)},
                ),
                tool_card(
                    "Start frontend",
                    "Calls automation.frontend.run_frontend().",
                    [frontend_path],
                    [("Start", ft.Icons.PLAY_ARROW)],
                    {"Start": lambda: frontend_action("Frontend server", "run_frontend")},
                ),
                ft.Text("Status terminal", size=13, weight=ft.FontWeight.BOLD),
                frontend_status,
            ], spacing=18, scroll=ft.ScrollMode.AUTO)
        page.update()

    def select_workspace(name: str, description: str) -> None:
        workspace_title.value = name
        workspace_hint.value = description
        render_workspace(name)

    def suggested(text: str) -> None:
        composer.value = text
        composer.focus()
        page.update()

    def sidebar_button(label: str, icon: str, handler, active: bool = False) -> ft.Control:
        return ft.Button(label, icon=icon, on_click=lambda _: handler(), bgcolor="#242032" if active else "transparent", color="#eeeaff" if active else "#abb2c3", expand=True)

    sidebar = ft.Container(
        content=ft.Column([
            ft.Row([ft.Container(width=28, height=28, bgcolor=accent, border_radius=9, content=ft.Icon(ft.Icons.AUTO_AWESOME, color="white", size=16)), ft.Text("Taksu", size=18, weight=ft.FontWeight.BOLD)], spacing=10),
            ft.Button("+  New chat", icon=ft.Icons.ADD, on_click=lambda _: messages.controls.clear(), bgcolor="#f4f1ff", color="#17131f", expand=True),
            ft.Text("WORKSPACES", size=10, color="#626a7d", weight=ft.FontWeight.BOLD),
            sidebar_button("Overview", ft.Icons.HOME_OUTLINED, lambda: select_workspace("Overview", "Taksu Automation workspace"), True),
            sidebar_button("Database", ft.Icons.STORAGE_OUTLINED, lambda: select_workspace("Database", "Queries, tables and data workflows")),
            sidebar_button("Laravel", ft.Icons.CODE_OUTLINED, lambda: select_workspace("Laravel", "Projects and CRUD scaffolding")),
            sidebar_button("Git", ft.Icons.ACCOUNT_TREE_OUTLINED, lambda: select_workspace("Git", "Branches, commits and repository workflows")),
            ft.Container(expand=True),
            ft.Text("SERVER", size=10, color="#626a7d", weight=ft.FontWeight.BOLD),
            ft.Button("Start server", icon=ft.Icons.PLAY_CIRCLE_OUTLINE, on_click=lambda _: add_message("The server button is ready, but not connected yet. Add your server command later.", tag="Server · coming soon"), bgcolor="#171a22", color="#9da5b8", expand=True),
            ft.Text("Preview mode", size=11, color="#6f778a"),
        ], spacing=12),
        width=240,
        padding=22,
        bgcolor="#0f1117",
        border=ft.Border(right=ft.BorderSide(1, border)),
    )

    suggestions = ft.Row([
        ft.Button("Plan a Laravel CRUD", icon=ft.Icons.CODE, on_click=lambda _: suggested("Plan a Laravel CRUD for a Task model"), bgcolor="#171a22", color="#c9c1ff"),
        ft.Button("Check Git status", icon=ft.Icons.ACCOUNT_TREE, on_click=lambda _: suggested("Check the Git status"), bgcolor="#171a22", color="#c9c1ff"),
        ft.Button("Create frontend plan", icon=ft.Icons.WEB, on_click=lambda _: suggested("Create a plan for the frontend"), bgcolor="#171a22", color="#c9c1ff"),
    ], wrap=True, spacing=8)
    render_workspace("Overview")

    composer_shell = ft.Container(
        content=ft.Row([composer, ft.Container(width=40, height=40, border_radius=12, bgcolor=accent, content=ft.IconButton(icon=ft.Icons.ARROW_UPWARD, icon_color="white", on_click=send_message))], spacing=8),
        padding=ft.Padding(left=16, top=8, right=8, bottom=8),
        bgcolor="#151821",
        border_radius=16,
        border=ft.Border(left=ft.BorderSide(1, "#303546"), top=ft.BorderSide(1, "#303546"), right=ft.BorderSide(1, "#303546"), bottom=ft.BorderSide(1, "#303546")),
    )

    main_content = ft.Container(
        content=ft.Column([
            ft.Row([ft.Column([workspace_title, workspace_hint], spacing=2, expand=True), ft.Container(content=ft.Row([ft.Icon(ft.Icons.CIRCLE, color="#f59e0b", size=9), ft.Text("Preview mode", size=12, color="#b4bbc9")], spacing=7), padding=ft.Padding(left=10, top=7, right=10, bottom=7), bgcolor="#211d13", border_radius=9)]),
            ft.Divider(color=border, height=1),
            workspace_body,
            composer_shell,
            ft.Text("Taksu can make mistakes. Review actions before running them.", size=11, color="#626a7d", text_align=ft.TextAlign.CENTER),
        ], spacing=14, expand=True),
        padding=ft.Padding(left=46, top=24, right=46, bottom=20),
        expand=True,
    )
    page.add(ft.Row([sidebar, main_content], expand=True, spacing=0))


if __name__ == "__main__":
    ft.run(main)
