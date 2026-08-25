import asyncio

import flet as ft

import api
import models
from config import BG_COLOR, PRIMARY, SECONDARY, SURFACE_COLOR


def build_catalog_view(page: ft.Page, storage, open_detail):
    selected_kategori = {"id": None}

    search_field = ft.TextField(
        hint_text="Cari produk atau kode...",
        prefix_icon=ft.Icons.SEARCH,
        dense=True,
        filled=True,
        bgcolor=ft.Colors.WHITE,
        border_radius=16,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=PRIMARY,
        focused_color=PRIMARY,
        hint_style=ft.TextStyle(color=ft.Colors.GREY_400),
        height=50,
    )

    chips_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
    content_area = ft.Container(expand=True)
    state = {"page": 1, "has_more": True, "loading_more": False, "load_error": False}
    req_seq = {"n": 0}

    footer_progress = ft.ProgressBar(
        height=3,
        color=PRIMARY,
        bgcolor=ft.Colors.with_opacity(0.12, PRIMARY),
        visible=False,
    )
    footer_spinner = ft.Row(
        [
            ft.ProgressRing(width=18, height=18, stroke_width=2, color=PRIMARY),
            ft.Text("Memuat produk lainnya...", size=12, color=ft.Colors.GREY_500),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
        visible=False,
    )
    footer_retry = ft.Container(
        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
        content=ft.Text(
            "Gagal memuat — ketuk untuk coba lagi",
            size=12,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        ),
        visible=False,
    )
    footer_row = ft.Container(
        padding=ft.Padding.only(top=4, bottom=12),
        content=ft.Column(
            [footer_progress, footer_spinner, footer_retry],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
    )

    async def load_more():
        if state["loading_more"] or not state["has_more"]:
            return
        state["loading_more"] = True
        state["load_error"] = False
        footer_retry.visible = False
        footer_progress.visible = True
        footer_spinner.visible = True
        page.update()
        seq = req_seq["n"]
        try:
            data = await asyncio.to_thread(
                api.products,
                kategori=selected_kategori["id"],
                search=search_field.value.strip() or None,
                page=state["page"] + 1,
            )
        except api.ApiError:
            state["loading_more"] = False
            state["load_error"] = True
            footer_progress.visible = False
            footer_spinner.visible = False
            footer_retry.visible = True
            page.update()
            return
        if seq != req_seq["n"]:
            return

        items = data.get("data", [])
        grid.controls.extend([card(models.Product.from_api(item)) for item in items])
        meta = data.get("meta") or {}
        state["page"] = int(meta.get("current_page", state["page"] + 1))
        state["has_more"] = int(meta.get("current_page", 1)) < int(meta.get("last_page", 1))
        state["loading_more"] = False
        footer_progress.visible = False
        footer_spinner.visible = False
        page.update()

    async def on_scroll(e):
        if state["loading_more"] or state["load_error"] or not state["has_more"]:
            return
        max_ext = getattr(e, "max_scroll_extent", 0) or 0
        pixels = getattr(e, "pixels", 0) or 0
        if max_ext > 0 and max_ext - pixels < 300:
            await load_more()

    footer_retry.on_click = load_more

    grid = ft.GridView(
        expand=True,
        max_extent=170,
        child_aspect_ratio=0.68,
        spacing=14,
        run_spacing=14,
        padding=ft.Padding.only(left=16, right=16, top=8, bottom=16),
        on_scroll=on_scroll,
    )

    async def build_chips():
        try:
            cats = await asyncio.to_thread(api.categories)
        except api.ApiError:
            cats = []

        async def select(cat_id, name):
            selected_kategori["id"] = cat_id
            await build_chips()
            await load()

        def chip(cat_id, name):
            is_selected = selected_kategori["id"] == cat_id

            async def on_tap(e):
                await select(cat_id, name)

            return ft.GestureDetector(
                on_tap=on_tap,
                content=ft.Container(
                    padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                    border_radius=20,
                    bgcolor=PRIMARY if is_selected else ft.Colors.WHITE,
                    shadow=ft.BoxShadow(
                        blur_radius=8,
                        spread_radius=0,
                        offset=ft.Offset(0, 2),
                        color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
                    ),
                    border=ft.Border.all(
                        1, PRIMARY if is_selected else ft.Colors.TRANSPARENT
                    ),
                    content=ft.Text(
                        name,
                        size=13,
                        weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_400,
                        color=ft.Colors.WHITE if is_selected else ft.Colors.GREY_700,
                    ),
                ),
            )

        chips_row.controls = [chip(None, "Semua")] + [chip(c["id"], c["nama"]) for c in cats]
        page.update()

    def card(product: models.Product):
        in_stock = product.stok > 0
        return ft.GestureDetector(
            on_tap=lambda e: open_detail(product),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            height=120,
                            border_radius=ft.BorderRadius(14, 14, 0, 0),
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            content=ft.Stack(
                                [
                                    ft.Image(
                                        src=product.gambar_url,
                                        fit=ft.BoxFit.COVER,
                                        width=float("inf"),
                                        height=120,
                                        error_content=ft.Container(
                                            bgcolor=SURFACE_COLOR,
                                            content=ft.Icon(
                                                ft.Icons.RESTAURANT,
                                                size=44,
                                                color=ft.Colors.with_opacity(0.5, PRIMARY),
                                            ),
                                            alignment=ft.Alignment.CENTER,
                                        ),
                                    ),
                                    # Out of stock overlay
                                    ft.Container(
                                        bgcolor=ft.Colors.with_opacity(0.55, ft.Colors.BLACK),
                                        alignment=ft.Alignment.CENTER,
                                        content=ft.Text(
                                            "Habis",
                                            size=13,
                                            color=ft.Colors.WHITE,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        visible=not in_stock,
                                    ),
                                ]
                            ),
                        ),
                        ft.Container(
                            padding=ft.Padding.only(left=10, right=10, top=8, bottom=10),
                            content=ft.Column(
                                [
                                    ft.Text(
                                        product.nama_barang,
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=ft.Colors.GREY_900,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Container(height=4),
                                    ft.Text(
                                        models.format_price(product.harga),
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=PRIMARY,
                                    ),
                                ],
                                spacing=0,
                            ),
                        ),
                    ],
                    spacing=0,
                ),
                bgcolor=ft.Colors.WHITE,
                border_radius=14,
                shadow=ft.BoxShadow(
                    blur_radius=14,
                    spread_radius=0,
                    offset=ft.Offset(0, 4),
                    color=ft.Colors.with_opacity(0.09, ft.Colors.BLACK),
                ),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            ),
        )

    def loading_box():
        return ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                [
                    ft.ProgressRing(
                        width=40,
                        height=40,
                        stroke_width=3.5,
                        color=PRIMARY,
                    ),
                    ft.Text("Memuat...", size=13, color=ft.Colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
        )

    def error_box(message, on_retry):
        return ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                [
                    ft.Container(
                        width=72,
                        height=72,
                        border_radius=36,
                        bgcolor=SURFACE_COLOR,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(ft.Icons.CLOUD_OFF, size=36, color=PRIMARY),
                    ),
                    ft.Text(
                        message,
                        size=13,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(
                        on_click=on_retry,
                        border_radius=12,
                        bgcolor=PRIMARY,
                        padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                        content=ft.Text("Coba Lagi", size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
        )

    def empty_box():
        return ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                [
                    ft.Container(
                        width=72,
                        height=72,
                        border_radius=36,
                        bgcolor=SURFACE_COLOR,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(ft.Icons.MANAGE_SEARCH, size=36, color=PRIMARY),
                    ),
                    ft.Text(
                        "Produk tidak ditemukan.",
                        size=14,
                        color=ft.Colors.GREY_700,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(
                        "Coba kata kunci lain",
                        size=12,
                        color=ft.Colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
        )

    async def load():
        seq = req_seq["n"] = req_seq["n"] + 1
        content_area.content = loading_box()
        page.update()
        state["page"] = 1
        state["has_more"] = True
        state["loading_more"] = False
        state["load_error"] = False
        try:
            data = await asyncio.to_thread(
                api.products,
                kategori=selected_kategori["id"],
                search=search_field.value.strip() or None,
                page=1,
            )
        except api.ApiError as exc:
            if seq != req_seq["n"]:
                return
            content_area.content = error_box(str(exc), load)
            page.update()
            return
        if seq != req_seq["n"]:
            return

        items = data.get("data", [])
        if not items:
            content_area.content = empty_box()
        else:
            meta = data.get("meta") or {}
            state["has_more"] = int(meta.get("current_page", 1)) < int(meta.get("last_page", 1))
            grid.controls = [card(models.Product.from_api(item)) for item in items]
            footer_progress.visible = False
            footer_spinner.visible = False
            footer_retry.visible = False
            content_area.content = ft.Column(
                [grid, footer_row],
                expand=True,
                spacing=0,
            )
        page.update()

    async def on_search_submit(e):
        await load()

    search_field.on_submit = on_search_submit

    # ── Header ─────────────────────────────────────────────────────────────
    header = ft.Container(
        padding=ft.Padding.only(top=16, bottom=12, left=16, right=16),
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            blur_radius=8,
            spread_radius=0,
            offset=ft.Offset(0, 2),
            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
        ),
        content=ft.Column(
            [
                search_field,
                ft.Container(height=10),
                ft.Container(
                    content=chips_row,
                    padding=ft.Padding.symmetric(vertical=2),
                ),
            ],
            spacing=0,
        ),
    )

    page.run_task(build_chips)
    page.run_task(load)

    return ft.Column(
        [
            header,
            ft.Container(
                expand=True,
                bgcolor=BG_COLOR,
                content=content_area,
            ),
        ],
        expand=True,
        spacing=0,
    )