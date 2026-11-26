import asyncio
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import flet as ft

import main


def controls(root):
    yield root
    for child in getattr(root, "controls", []) or []:
        yield from controls(child)
    for name in ("columns", "rows", "cells"):
        for child in getattr(root, name, []) or []:
            yield from controls(child)
    child = getattr(root, "content", None)
    if child is not None:
        yield from controls(child)


class FakePage:
    def __init__(self):
        self.controls = []

    def add(self, control):
        self.controls.append(control)

    def update(self):
        pass


class LaravelFormTests(unittest.TestCase):
    def test_laravel_index_shows_frontend_packages_and_database_columns(self):
        page = FakePage()
        with patch.object(main, "import_module") as import_module:
            import_module.return_value.index_laravel.return_value = [
                {"id": 7, "project_name": "shop", "path": "/projects/shop", "frontend": "React", "packages": ["axios", "vite"], "database": "MySQL"},
                {"id": 8, "project_name": "api", "path": "/projects/api"},
            ]
            main.main(page)
            next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Laravel").on_click(None)

        table = next(control for control in controls(page) if isinstance(control, ft.DataTable))
        self.assertEqual([column.label for column in table.columns], ["Project", "Frontend", "Packages", "Database", "Path", "Action"])
        self.assertEqual([cell.content.value for cell in table.rows[0].cells[:5]], ["shop", "React", "axios, vite", "MySQL", "/projects/shop"])
        self.assertEqual([cell.content.value for cell in table.rows[1].cells[:5]], ["api", "—", "—", "—", "/projects/api"])
        self.assertEqual(table.rows[0].cells[5].content.content, "Open")

    def test_frontend_can_be_left_empty(self):
        page = FakePage()
        with patch.object(main, "import_module") as import_module:
            brain = import_module.return_value
            brain.index_laravel.side_effect = lambda: ([{"id": 1, "project_name": "optional-frontend-test", "path": "/tmp/optional-frontend-test"}] if brain.mydb.commit.called else [])
            main.main(page)
            button = next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Laravel")
            button.on_click(None)
            button = next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Create")
            button.on_click(None)

            fields = [control for control in controls(page) if isinstance(control, (ft.TextField, ft.Dropdown)) and control.label]
            field = lambda label: next(control for control in fields if control.label == label)
            field("Project name").value = "optional-frontend-test"
            field("Database").value = "sqlite"
            field("PHP testing: Pest of PHPUnit").value = "phpunit"
            self.assertFalse(field("Frontend (optional)").value)

            async def fake_command(command, output, cwd=None):
                output("> command completed")

            with patch.object(main, "run_status_command_async", side_effect=fake_command) as command, patch.object(main.os.path, "isfile", return_value=True):
                button = next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Create Laravel project")
                asyncio.run(button.on_click(None))

            self.assertEqual(command.call_count, 2)
            brain.mydb.cursor.return_value.execute.assert_called_once_with(
                "INSERT INTO backend_projects (project_name, path) VALUES (%s, %s)",
                ("optional-frontend-test", main.os.path.abspath("optional-frontend-test")),
            )
            brain.mydb.commit.assert_called_once()
            terminal = next(control for control in controls(page) if isinstance(control, ft.TextField) and "project saved in database" in (control.value or ""))
            self.assertIn("KLAAR", terminal.value)

            button = next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Back to projects")
            button.on_click(None)
            self.assertTrue(any(isinstance(control, ft.Text) and control.value == "optional-frontend-test" for control in controls(page)))

    def test_database_failure_is_not_reported_as_complete(self):
        page = FakePage()
        with patch.object(main, "import_module") as import_module:
            brain = import_module.return_value
            brain.index_laravel.return_value = []
            brain.mydb.cursor.return_value.execute.side_effect = RuntimeError("database unavailable")
            main.main(page)
            next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Laravel").on_click(None)
            next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Create").on_click(None)
            fields = [control for control in controls(page) if isinstance(control, (ft.TextField, ft.Dropdown)) and control.label]
            next(control for control in fields if control.label == "Project name").value = "database-failure-test"
            next(control for control in fields if control.label == "Database").value = "sqlite"
            next(control for control in fields if control.label == "PHP testing: Pest of PHPUnit").value = "pest"

            async def fake_command(command, output, cwd=None):
                pass

            with patch.object(main, "run_status_command_async", side_effect=fake_command), patch.object(main.os.path, "isfile", return_value=True):
                button = next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Create Laravel project")
                asyncio.run(button.on_click(None))

            terminal = next(control for control in controls(page) if isinstance(control, ft.TextField) and "database unavailable" in (control.value or ""))
            self.assertNotIn("KLAAR", terminal.value)
            self.assertTrue(any(isinstance(control, ft.Text) and control.value == "Project aangemaakt, databaseopslag mislukt" for control in controls(page)))
            brain.mydb.commit.assert_not_called()

    def test_generated_model_is_saved_for_selected_project(self):
        page = FakePage()
        with patch.object(main, "import_module") as import_module:
            backend = import_module.return_value
            backend.index_laravel.return_value = [
                {"id": 7, "project_name": "shop", "path": "/tmp/shop"}
            ]
            backend.select_laravel.return_value = (
                [], {"id": 7, "project_name": "shop", "path": "/tmp/shop"}
            )
            main.main(page)
            next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Laravel").on_click(None)
            next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Open").on_click(None)
            backend.mydb.cursor.return_value.reset_mock()
            next(control for control in controls(page) if isinstance(control, ft.TextField) and control.label == "Model name").value = "Task"

            async def fake_command(command, output, cwd=None):
                pass

            with patch.object(main, "run_status_command_async", side_effect=fake_command), patch.object(main.os.path, "isfile", return_value=True):
                button = next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Generate CRUD")
                asyncio.run(button.on_click(None))

            backend.mydb.cursor.return_value.execute.assert_called_once_with(
                "INSERT INTO model_projects (model_name, backend_project_id) VALUES (%s, %s)",
                ("Task", 7),
            )
            backend.mydb.commit.assert_called_once()
            next(control for control in controls(page) if isinstance(control, ft.Button)
                 and control.content == "View existing models").on_click(None)
            self.assertTrue(any(isinstance(control, ft.Button) and control.content == "Open Task"
                                for control in controls(page)))

    def test_project_shows_crud_details_and_database_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            for filename, content in {
                "artisan": "",
                "app/Models/Task.php": "class Task extends Model {}",
                "app/Http/Controllers/Api/TaskController.php": "function index() {}",
                "database/seeders/TaskSeeder.php": "class TaskSeeder {}",
                "database/migrations/2026_11_09_create_tasks_table.php": "Schema::create('tasks', function () {});",
                "routes/web.php": "Route::get('/', fn () => 'home');",
                ".env": "DB_CONNECTION=sqlite\n",
            }.items():
                path = project / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            sqlite_path = project / "database/database.sqlite"
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            sqlite3.connect(sqlite_path).close()

            page = FakePage()
            with patch.object(main, "import_module") as import_module:
                backend = import_module.return_value
                backend.index_laravel.return_value = [
                    {"id": 7, "project_name": "shop", "path": str(project)}
                ]
                backend.select_laravel.return_value = (
                    [], {"id": 7, "project_name": "shop", "path": str(project)}
                )
                backend.mydb.cursor.return_value.fetchall.return_value = [
                    {"id": 12, "model_name": "Task", "backend_project_id": 7}
                ]
                main.main(page)
                next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Laravel").on_click(None)
                next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Open").on_click(None)
                next(control for control in controls(page) if isinstance(control, ft.Button)
                     and control.content == "View existing models").on_click(None)
                next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Open Task").on_click(None)

            texts = [control.value for control in controls(page) if isinstance(control, ft.Text)]
            self.assertIn("Task CRUD details", texts)
            self.assertTrue(any("class Task extends Model" in str(value) for value in texts))
            self.assertTrue(any("Schema::create('tasks'" in str(value) for value in texts))
            self.assertTrue(any("tasks" in str(value) and "not migrated" in str(value) for value in texts))

    def test_project_shows_only_its_frontends_and_models(self):
        with tempfile.TemporaryDirectory() as temporary:
            frontend_path = Path(temporary) / "shop-ui"
            frontend_path.mkdir()
            (frontend_path / "package.json").write_text('{"name": "shop-ui"}')
            page = FakePage()
            with patch.object(main, "import_module") as import_module:
                backend = import_module.return_value
                backend.index_laravel.return_value = [{"id": 7, "project_name": "shop", "path": temporary}]
                backend.select_laravel.return_value = ([
                    {"id": 10, "backend_project_id": 7, "project_name": "shop-ui", "path": str(frontend_path)},
                    {"id": 11, "backend_project_id": 8, "project_name": "other-ui", "path": "/tmp/other-ui"},
                ], {"id": 7, "project_name": "shop", "path": temporary})
                backend.mydb.cursor.return_value.fetchall.return_value = [
                    {"id": 12, "backend_project_id": 7, "model_name": "Task"},
                    {"id": 13, "backend_project_id": 8, "model_name": "Invoice"},
                ]
                main.main(page)
                next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Laravel").on_click(None)
                next(control for control in controls(page) if isinstance(control, ft.Button) and control.content == "Open").on_click(None)

                backend.mydb.cursor.return_value.execute.assert_called_once_with(
                    "SELECT id, model_name, backend_project_id FROM model_projects WHERE backend_project_id = %s ORDER BY id",
                    (7,),
                )
                buttons = [control.content for control in controls(page) if isinstance(control, ft.Button)]
                self.assertIn("Generate CRUD", buttons)
                self.assertIn("Create frontend", buttons)
                self.assertIn("View existing models", buttons)
                self.assertIn("View existing frontends", buttons)
                self.assertNotIn("Open Task", buttons)
                self.assertNotIn("Open frontend shop-ui", buttons)
                next(control for control in controls(page) if isinstance(control, ft.Button)
                     and control.content == "View existing models").on_click(None)
                buttons = [control.content for control in controls(page) if isinstance(control, ft.Button)]
                self.assertIn("Open Task", buttons)
                self.assertNotIn("Open Invoice", buttons)
                next(control for control in controls(page) if isinstance(control, ft.Button)
                     and control.content == "Back to project").on_click(None)
                next(control for control in controls(page) if isinstance(control, ft.Button)
                     and control.content == "View existing frontends").on_click(None)
                buttons = [control.content for control in controls(page) if isinstance(control, ft.Button)]
                self.assertIn("Open frontend shop-ui", buttons)
                self.assertNotIn("Open frontend other-ui", buttons)
                next(control for control in controls(page) if isinstance(control, ft.Button)
                     and control.content == "Open frontend shop-ui").on_click(None)

            texts = [control.value for control in controls(page) if isinstance(control, ft.Text)]
            self.assertIn("shop-ui frontend details", texts)
            self.assertTrue(any('"name": "shop-ui"' in str(value) for value in texts))


if __name__ == "__main__":
    unittest.main()
