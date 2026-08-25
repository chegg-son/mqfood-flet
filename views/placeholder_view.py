import flet as ft


def build_placeholder_view(title: str, note: str):
    return ft.Container(
        alignment=ft.Alignment.CENTER,
        expand=True,
        content=ft.Column(
            [
                ft.Icon(ft.Icons.CONSTRUCTION, size=48, color=ft.Colors.GREY),
                ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Text(note, size=13, color=ft.Colors.GREY),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
    )