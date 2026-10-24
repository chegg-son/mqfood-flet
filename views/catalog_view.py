import asyncio
import time

import flet as ft

import api
import models
import ui
from config import BG_COLOR, PRIMARY, SURFACE_COLOR

# How long (seconds) a cached catalog page is considered fresh. While fresh a
# revisit renders from memory; once stale the cached grid stays visible and the
# first page is refreshed silently in the background.
_CATALOG_CACHE_TTL = 300  # 5 minutes

# Placeholder cards drawn while the first page is fetched.
_SKELETON_CARDS = 8


def build_catalog_view(page: ft.Page, storage, open_detail):
    selected_kategori = {"id": None}

    # ── Cache ──────────────────────────────────────────────────────────────
    # Keyed by (kategori_id, search) so each filter keeps its own result set
    # (including the pages pulled in by infinite scroll). Survives tab switches
    # and detail popups, so coming back never re-fetches or rebuilds the grid.
    _cache = {}
    _categories = []
    _chips = []  # [(kategori_id, container, label)] for in-place selection

    # What is currently on screen, used to skip redundant renders.
    rendered = {"key": None, "products": []}

    def entry_for(key):
        entry = _cache.get(key)
        if entry is None:
            entry = {
                "products": [],
                "page": 1,
                "has_more": False,
                "loaded": False,
                "last_loaded": 0.0,
            }
            _cache[key] = entry
        return entry

    def current_key():
        query = (search_field.value or "").strip() or None
        return (selected_kategori["id"], query)

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
        expand=True,
    )

    chips_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
    content_area = ft.Container(expand=True)
    state = {
        "page": 1,
        "has_more": True,
        "loading_more": False,
        "load_error": False,
        "scroll_triggered": False,
        "auto_filled": False,
    }
    req_seq = {"n": 0}

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
            [footer_spinner, footer_retry],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
    )

    # The GridView is recreated on every render (a fresh one per filter) so a
    # filter switch always starts at the top; revisits render nothing at all,
    # which is what keeps the scroll position intact.
    grid_holder = {"grid": None}

    def new_grid():
        return ft.GridView(
            expand=True,
            max_extent=170,
            child_aspect_ratio=0.68,
            spacing=14,
            run_spacing=14,
            padding=ft.Padding.only(left=16, right=16, top=8, bottom=16),
            on_scroll=on_scroll,
        )

    def grid_column(grid):
        return ft.Column([grid, footer_row], expand=True, spacing=0)

    async def load_more():
        key = rendered["key"]
        grid = grid_holder["grid"]
        if key is None or grid is None or state["loading_more"] or not state["has_more"]:
            return
        state["loading_more"] = True
        state["load_error"] = False
        footer_retry.visible = False
        footer_spinner.visible = True
        page.update()

        seq = req_seq["n"]
        next_page = state["page"] + 1
        try:
            data = await asyncio.to_thread(
                api.products,
                kategori=key[0],
                search=key[1],
                page=next_page,
            )
        except api.ApiError:
            if seq == req_seq["n"]:
                state["loading_more"] = False
                state["load_error"] = True
                footer_spinner.visible = False
                footer_retry.visible = True
                page.update()
            return

        if seq != req_seq["n"] or rendered["key"] != key:
            # A newer filter or search owns the grid now; drop this page.
            state["loading_more"] = False
            footer_spinner.visible = False
            page.update()
            return

        entry = entry_for(key)
        meta = data.get("meta") or {}
        known = {p.id for p in entry["products"]}
        items = data.get("data", [])
        new_products = [p for p in (models.Product.from_api(i) for i in items) if p.id not in known]

        entry["products"].extend(new_products)
        entry["page"] = int(meta.get("current_page", next_page))
        entry["has_more"] = entry["page"] < int(meta.get("last_page", 1))
        entry["last_loaded"] = time.monotonic()
        entry["loaded"] = True

        rendered["products"].extend(new_products)
        grid.controls.extend([card(p) for p in new_products])
        state["page"] = entry["page"]
        state["has_more"] = entry["has_more"]
        state["loading_more"] = False
        footer_spinner.visible = False
        page.update()

    async def on_scroll(e):
        if rendered["key"] is None:
            return
        if state["loading_more"] or state["load_error"] or not state["has_more"]:
            return
        extent_after = getattr(e, "extent_after", None)
        if extent_after is None or extent_after < 300:
            state["scroll_triggered"] = True
            await load_more()

    async def retry_more(e=None):
        await load_more()

    footer_retry.on_click = retry_more

    # ── Chip selection ─────────────────────────────────────────────────────
    def apply_chip_styles():
        for cat_id, box, label in _chips:
            is_selected = selected_kategori["id"] == cat_id
            box.bgcolor = PRIMARY if is_selected else ft.Colors.WHITE
            box.border = ft.Border.all(1, PRIMARY if is_selected else ft.Colors.TRANSPARENT)
            label.weight = ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_400
            label.color = ft.Colors.WHITE if is_selected else ft.Colors.GREY_700

    async def select_category(cat_id):
        if selected_kategori["id"] == cat_id:
            return
        selected_kategori["id"] = cat_id
        apply_chip_styles()
        page.update()
        await load()

    def chip_tap_handler(cat_id):
        # Flet only awaits handlers that are coroutine functions; a lambda that
        # returns a coroutine is dropped, so the tap would silently do nothing.
        async def handler(e):
            await select_category(cat_id)

        return handler

    def chip(cat_id, name):
        label = ft.Text(
            name,
            size=13,
            weight=ft.FontWeight.W_400,
            color=ft.Colors.GREY_700,
        )
        box = ft.Container(
            padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            border_radius=20,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                blur_radius=8,
                spread_radius=0,
                offset=ft.Offset(0, 2),
                color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
            ),
            border=ft.Border.all(1, ft.Colors.TRANSPARENT),
            content=label,
        )
        _chips.append((cat_id, box, label))
        return ft.GestureDetector(
            on_tap=chip_tap_handler(cat_id),
            content=box,
        )

    async def build_chips(force=False):
        if _chips and not force:
            return
        if not _categories or force:
            try:
                cats = await asyncio.to_thread(api.categories)
                _categories[:] = cats
            except api.ApiError:
                pass  # keep whatever categories we already have

        _chips.clear()
        chips_row.controls = [chip(None, "Semua")] + [
            chip(c["id"], c["nama"]) for c in _categories
        ]
        apply_chip_styles()
        page.update()

    # ── Cards ──────────────────────────────────────────────────────────────
    # product id -> refreshes that card's texts/overlay in place, so a
    # background refresh can update stock and prices without rebuilding the
    # grid (which re-decoded every photo and made the cards blink).
    card_updaters = {}

    def card(product: models.Product):
        current = {"product": product}

        name_text = ft.Text(
            product.nama_barang,
            size=13,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.GREY_900,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        price_text = ft.Text(
            models.format_price(product.harga),
            size=14,
            weight=ft.FontWeight.BOLD,
            color=PRIMARY,
        )
        stock_overlay = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.55, ft.Colors.BLACK),
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                "Habis",
                size=13,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD,
            ),
            visible=product.stok <= 0,
        )

        def update(fresh: models.Product):
            current["product"] = fresh
            name_text.value = fresh.nama_barang
            price_text.value = models.format_price(fresh.harga)
            stock_overlay.visible = fresh.stok <= 0

        card_updaters[product.id] = update

        return ft.GestureDetector(
            on_tap=lambda e: open_detail(current["product"]),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            height=120,
                            border_radius=ft.BorderRadius(14, 14, 0, 0),
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            content=ft.Stack(
                                [
                                    ui.product_image(
                                        page,
                                        product.gambar_url,
                                        max_width=360,
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
                                    stock_overlay,
                                ]
                            ),
                        ),
                        ft.Container(
                            padding=ft.Padding.only(left=10, right=10, top=8, bottom=10),
                            content=ft.Column(
                                [
                                    name_text,
                                    ft.Container(height=4),
                                    price_text,
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

    def skeleton_card():
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        height=120,
                        border_radius=ft.BorderRadius(14, 14, 0, 0),
                        bgcolor=ft.Colors.GREY_200,
                    ),
                    ft.Container(
                        padding=ft.Padding.only(left=10, right=10, top=10, bottom=10),
                        content=ft.Column(
                            [
                                ft.Container(
                                    height=11,
                                    border_radius=6,
                                    bgcolor=ft.Colors.GREY_200,
                                ),
                                ft.Container(
                                    height=11,
                                    width=80,
                                    border_radius=6,
                                    bgcolor=ft.Colors.GREY_200,
                                ),
                            ],
                            spacing=8,
                            horizontal_alignment=ft.CrossAxisAlignment.START,
                        ),
                    ),
                ],
                spacing=0,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=14,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
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

    # ── Rendering ──────────────────────────────────────────────────────────
    def render(key, entry):
        """Draw the cached products for *key* into a fresh grid."""
        products = entry["products"]
        rendered["key"] = key
        rendered["products"] = list(products)

        state["page"] = entry.get("page", 1)
        state["has_more"] = entry.get("has_more", False)
        state["loading_more"] = False
        state["load_error"] = False
        state["scroll_triggered"] = False
        state["auto_filled"] = False
        footer_spinner.visible = False
        footer_retry.visible = False

        card_updaters.clear()
        if products:
            grid = new_grid()
            grid.controls = [card(p) for p in products]
            grid_holder["grid"] = grid
            content_area.content = grid_column(grid)
        else:
            grid_holder["grid"] = None
            content_area.content = empty_box()
        page.update()

    def show_skeleton():
        """Placeholder grid for a filter that has never been loaded."""
        rendered["key"] = None
        rendered["products"] = []
        state["page"] = 1
        state["has_more"] = False
        state["loading_more"] = False
        state["load_error"] = False
        state["scroll_triggered"] = False
        state["auto_filled"] = False
        footer_spinner.visible = False
        footer_retry.visible = False
        card_updaters.clear()
        grid = new_grid()
        grid.controls = [skeleton_card() for _ in range(_SKELETON_CARDS)]
        grid_holder["grid"] = grid
        content_area.content = grid_column(grid)
        page.update()

    # ── Loading ────────────────────────────────────────────────────────────
    async def load(force=False):
        key = current_key()
        entry = entry_for(key)
        seq = req_seq["n"] = req_seq["n"] + 1

        is_stale = not entry["loaded"] or (
            time.monotonic() - entry["last_loaded"]
        ) >= _CATALOG_CACHE_TTL

        if entry["loaded"]:
            # Show memory content immediately; a stale entry is refreshed below
            # while it stays on screen.
            if rendered["key"] != key:
                render(key, entry)
            if not is_stale and not force:
                return  # fresh cache and already on screen: nothing to do
        else:
            show_skeleton()

        previous = rendered["products"]
        try:
            data = await asyncio.to_thread(
                api.products,
                kategori=key[0],
                search=key[1],
                page=1,
            )
        except api.ApiError as exc:
            if seq != req_seq["n"]:
                return
            if not entry["loaded"]:
                content_area.content = error_box(
                    str(exc), lambda e: page.run_task(load, True)
                )
                page.update()
            return  # stale content stays visible on a failed refresh
        if seq != req_seq["n"]:
            return

        items = data.get("data", [])
        fresh_page = [models.Product.from_api(item) for item in items]
        meta = data.get("meta") or {}
        page_no = int(meta.get("current_page", 1))

        cached = entry["products"]
        keeps_tail = (
            bool(fresh_page)
            and page_no == 1
            and len(cached) > len(fresh_page)
            and [p.id for p in cached[: len(fresh_page)]]
            == [p.id for p in fresh_page]
        )
        if keeps_tail:
            # Same first page as before: keep the extra pages that infinite
            # scroll already pulled in instead of dropping back to page 1.
            entry["products"] = fresh_page + cached[len(fresh_page):]
        else:
            entry["products"] = fresh_page
            entry["page"] = page_no
            entry["has_more"] = page_no < int(meta.get("last_page", 1))
        entry["last_loaded"] = time.monotonic()
        entry["loaded"] = True

        # A silent refresh that returned the same products in the same order is
        # applied to the mounted cards in place: no grids are rebuilt, so the
        # photos are never re-decoded (no blink) and the scroll position stays.
        same_products = rendered["key"] == key and previous == entry["products"]
        same_order = rendered["key"] == key and [p.id for p in previous] == [
            p.id for p in entry["products"]
        ]
        if not same_products:
            if same_order:
                for fresh in entry["products"]:
                    update_card = card_updaters.get(fresh.id)
                    if update_card:
                        update_card(fresh)
                rendered["products"] = list(entry["products"])
                state["page"] = entry["page"]
                state["has_more"] = entry["has_more"]
                page.update()
            else:
                render(key, entry)

        # After the first page, give the layout time to settle then check if
        # on_scroll has fired. If it hasn't (content fits the viewport — typical
        # in landscape), load the next page once so the user has something to
        # scroll. on_scroll takes over from that point.
        # Fill the viewport once per rendered grid. Without this flag every
        # refresh (tab revisit, stale cache) pulled one more page, so cards kept
        # being added — with their photos popping in — while the user just sat
        # on the catalog.
        if state["has_more"] and not state["auto_filled"]:
            state["auto_filled"] = True
            await asyncio.sleep(0.6)
            if (
                seq == req_seq["n"]
                and state["has_more"]
                and not state["loading_more"]
                and not state["load_error"]
                and not state["scroll_triggered"]
            ):
                await load_more()

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

    # Paint the loading placeholders right away instead of an empty area.
    show_skeleton()
    page.run_task(build_chips)
    page.run_task(load)

    def refresh(force=False):
        page.run_task(build_chips)
        page.run_task(load, force)

    result = ft.Column(
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
    result.refresh = refresh
    return result
