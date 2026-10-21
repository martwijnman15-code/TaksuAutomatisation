
import flet as ft
import subprocess

def main(page: ft.Page):
    page.title = "Taksu Automation"
    page.theme_mode = ft.ThemeMode.DARK

    def clicked(e):
        subprocess.call(".sh")
        page.update()

    message = ft.Text("Welcome to Taksu Automation", size=24)

    page.add(
        message,
        ft.Button("Start Automation", on_click=clicked)
    )

ft.run(main)
