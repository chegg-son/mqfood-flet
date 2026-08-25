import asyncio

import flet as ft

import api
from config import ACCENT, BG_COLOR, PRIMARY, PRIMARY_DARK, SECONDARY, SURFACE_COLOR


def build_login_view(page: ft.Page, storage, on_success):
    username_field = ft.TextField(
        label="Username",
        autofocus=True,
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        border_radius=14,
        filled=True,
        bgcolor=ft.Colors.WHITE,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=PRIMARY,
        focused_color=PRIMARY,
        label_style=ft.TextStyle(color=ft.Colors.GREY_600),
    )
    password_field = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        border_radius=14,
        filled=True,
        bgcolor=ft.Colors.WHITE,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=PRIMARY,
        focused_color=PRIMARY,
        label_style=ft.TextStyle(color=ft.Colors.GREY_600),
        on_submit=lambda e: submit(e),
    )
    error_text = ft.Text(
        "",
        size=13,
        color=ft.Colors.RED_400,
        visible=False,
        text_align=ft.TextAlign.CENTER,
    )
    loading = ft.ProgressRing(
        width=22,
        height=22,
        stroke_width=2.5,
        color=ft.Colors.WHITE,
        visible=False,
    )

    def set_loading(loading_state: bool):
        submit_btn.disabled = loading_state
        loading.visible = loading_state
        username_field.disabled = loading_state
        password_field.disabled = loading_state
        page.update()

    async def submit(e):
        set_loading(True)
        error_text.visible = False
        try:
            body = await asyncio.to_thread(
                api.login, username_field.value.strip(), password_field.value
            )
        except api.ApiError as exc:
            error_text.value = str(exc)
            error_text.visible = True
            set_loading(False)
            return

        storage.set("token", body["token"])
        storage.set("user", body["user"])
        set_loading(False)
        on_success(body["user"])

    submit_btn = ft.Container(
        on_click=submit,
        border_radius=14,
        bgcolor=PRIMARY,
        shadow=ft.BoxShadow(
            blur_radius=16,
            spread_radius=0,
            offset=ft.Offset(0, 6),
            color=f"{PRIMARY}66",
        ),
        content=ft.Row(
            [
                ft.Text(
                    "Masuk",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                loading,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        height=52,
        animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
    )

    # Hero section
    hero = ft.Container(
        height=260,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[PRIMARY_DARK, PRIMARY, SECONDARY],
        ),
        border_radius=ft.BorderRadius(0, 0, 36, 36),
        content=ft.Column(
            [
                ft.Container(height=24),
                ft.Container(
                    width=80,
                    height=80,
                    border_radius=40,
                    bgcolor=ft.Colors.WHITE24,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.RESTAURANT_MENU, size=44, color=ft.Colors.WHITE),
                ),
                ft.Container(height=12),
                ft.Text(
                    "MQFood",
                    size=34,
                    weight=ft.FontWeight.W_900,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    "Pemesanan makanan santri",
                    size=14,
                    color=ft.Colors.WHITE70,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
        ),
    )

    form_card = ft.Container(
        margin=ft.Margin(20, -28, 20, 24),
        padding=ft.Padding.all(24),
        bgcolor=ft.Colors.WHITE,
        border_radius=24,
        shadow=ft.BoxShadow(
            blur_radius=32,
            spread_radius=0,
            offset=ft.Offset(0, 8),
            color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
        ),
        content=ft.Column(
            [
                ft.Text(
                    "Selamat Datang",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
                ft.Text(
                    "Masuk untuk mulai memesan",
                    size=13,
                    color=ft.Colors.GREY_500,
                ),
                ft.Container(height=16),
                username_field,
                ft.Container(height=8),
                password_field,
                error_text,
                ft.Container(height=16),
                submit_btn,
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
    )

    return ft.SafeArea(
        ft.Container(
            expand=True,
            bgcolor=BG_COLOR,
            content=ft.Column(
                [
                    hero,
                    form_card,
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
    )