import flet as ft

import api
from config import ACCENT, BG_COLOR, PRIMARY, SECONDARY, SURFACE_COLOR, TEXT_COLOR


def build_home_view(page: ft.Page, storage, on_logout=None):
    user = storage.get_json("user", {})
    name = user.get("name") or "Santri"
    kelas = user.get("kelas") or ""

    # ── Status components ──────────────────────────────────────────────────
    status_icon = ft.Icon(ft.Icons.SCHEDULE, color=ft.Colors.AMBER_700, size=22)
    status_text = ft.Text(
        "Memeriksa status toko...",
        size=15,
        weight=ft.FontWeight.W_600,
        color=ft.Colors.GREY_800,
    )
    close_info = ft.Text("", size=12, color=ft.Colors.GREY_500)
    retry_btn = ft.TextButton(
        "Coba lagi",
        icon=ft.Icons.REFRESH,
        visible=False,
        style=ft.ButtonStyle(color=PRIMARY),
        on_click=lambda e: load(),
    )

    shop_banner = ft.Container(
        padding=ft.Padding.all(20),
        border_radius=16,
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            blur_radius=12,
            spread_radius=0,
            offset=ft.Offset(0, 4),
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        ),
        content=ft.Row(
            [
                ft.Container(
                    width=52,
                    height=52,
                    border_radius=26,
                    bgcolor=SURFACE_COLOR,
                    alignment=ft.Alignment.CENTER,
                    content=status_icon,
                ),
                ft.Column(
                    [
                        status_text,
                        close_info,
                        retry_btn,
                    ],
                    spacing=4,
                    expand=True,
                ),
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    def load():
        try:
            data = api.shop_status()
        except api.ApiError as exc:
            status_icon.name = ft.Icons.ERROR_OUTLINE
            status_icon.color = ft.Colors.RED_400
            status_text.value = str(exc)
            status_text.color = ft.Colors.RED_400
            close_info.value = ""
            retry_btn.visible = True
        else:
            is_open = data.get("is_open")
            if is_open:
                status_icon.name = ft.Icons.CHECK_CIRCLE
                status_icon.color = ft.Colors.GREEN_600
                status_text.value = "Toko Sedang Buka"
                status_text.color = ft.Colors.GREEN_700
                close_info.value = f"Buka sampai {data.get('close_time', '')}"
            else:
                status_icon.name = ft.Icons.CANCEL
                status_icon.color = ft.Colors.RED_400
                status_text.value = "Toko Sedang Tutup"
                status_text.color = ft.Colors.RED_600
                close_info.value = f"Buka kembali {data.get('open_time', '')}"
            retry_btn.visible = False
        page.update()

    # ── Hero section ──────────────────────────────────────────────────────
    hero_section = ft.Container(
        height=200,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=["#E53935", "#FF7043"],
        ),
        border_radius=ft.BorderRadius(0, 0, 32, 32),
        padding=ft.Padding.only(left=20, right=20, top=12, bottom=24),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    f"Assalamu'alaikum 👋",
                                    size=13,
                                    color=ft.Colors.WHITE70,
                                ),
                                ft.Text(
                                    name,
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    kelas,
                                    size=13,
                                    color=ft.Colors.WHITE60,
                                ) if kelas else ft.Container(),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.PopupMenuButton(
                            content=ft.Container(
                                width=52,
                                height=52,
                                border_radius=26,
                                bgcolor=ft.Colors.WHITE24,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text(
                                    name[0].upper() if name else "S",
                                    size=22,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ),
                            items=[
                                ft.PopupMenuItem(
                                    content=ft.Text("Logout", size=13, weight=ft.FontWeight.W_500),
                                    icon=ft.Icons.LOGOUT_ROUNDED,
                                    on_click=lambda e: on_logout(e) if on_logout else None,
                                ),
                            ],
                            visible=on_logout is not None,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=12),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                    border_radius=12,
                    bgcolor=ft.Colors.WHITE24,
                    content=ft.Text(
                        "Mau pesan apa hari ini?",
                        size=13,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_500,
                    ),
                ),
            ],
            spacing=0,
        ),
    )

    # ── Section titles (consistent accent bar + hierarchy) ────────────────
    def section_title(text):
        return ft.Row(
            [
                ft.Container(width=4, height=18, border_radius=2, bgcolor=PRIMARY),
                ft.Text(text, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
            ],
            spacing=8,
        )

    # ── Branded empty state (featured products coming soon) ───────────────
    featured_placeholder = ft.Container(
        padding=ft.Padding.all(24),
        border_radius=16,
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            blur_radius=12,
            spread_radius=0,
            offset=ft.Offset(0, 4),
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        ),
        content=ft.Column(
            [
                ft.Container(
                    width=64,
                    height=64,
                    border_radius=32,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, -1),
                        end=ft.Alignment(1, 1),
                        colors=[PRIMARY, SECONDARY],
                    ),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.RESTAURANT_MENU, size=30, color=ft.Colors.WHITE),
                ),
                ft.Container(height=12),
                ft.Text(
                    "Produk unggulan segera hadir",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.GREY_800,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=4),
                ft.Text(
                    "Pilihan menu terbaik akan tampil di sini.",
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
    )

    # ── Content (8/16/24 spacing rhythm) ──────────────────────────────────
    content = ft.Column(
        [
            ft.Container(height=16),
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=16),
                content=ft.Column(
                    [
                        section_title("Status Toko"),
                        ft.Container(height=8),
                        shop_banner,
                        ft.Container(height=16),
                        section_title("Produk Unggulan"),
                        ft.Container(height=8),
                        featured_placeholder,
                        ft.Container(height=24),
                    ],
                    spacing=0,
                ),
            ),
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
    )

    main = ft.Column(
        [
            hero_section,
            ft.Container(expand=True, content=content),
        ],
        spacing=0,
        expand=True,
    )

    load()
    return main