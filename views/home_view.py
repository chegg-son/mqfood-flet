import asyncio

import flet as ft

import api
import models
from config import ACCENT, BG_COLOR, PRIMARY, SECONDARY, SURFACE_COLOR, TEXT_COLOR
from ui import product_image, status_badge


def build_home_view(
    page: ft.Page,
    storage,
    on_logout=None,
    on_catalog=None,
    on_cart=None,
    on_orders=None,
    on_open_product=None,
    on_open_order=None,
):
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
        on_click=lambda e: page.run_task(load),
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

    categories_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
    featured_row = ft.Row(spacing=12, scroll=ft.ScrollMode.AUTO)
    recent_order_host = ft.Container()

    def action_button(icon, label, callback):
        return ft.GestureDetector(
            expand=1,
            on_tap=lambda e: callback() if callback else None,
            content=ft.Container(
                expand=True,
                padding=ft.Padding.symmetric(horizontal=8, vertical=12),
                border_radius=14,
                bgcolor=ft.Colors.WHITE,
                shadow=ft.BoxShadow(blur_radius=10, spread_radius=0, offset=ft.Offset(0, 3), color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK)),
                content=ft.Column(
                    [
                        ft.Icon(icon, color=PRIMARY, size=23),
                        ft.Text(label, size=12, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
            ),
        )

    quick_actions = ft.Row(
        [
            action_button(ft.Icons.STORE_OUTLINED, "Katalog", on_catalog),
            action_button(ft.Icons.SHOPPING_CART_OUTLINED, "Keranjang", on_cart),
            action_button(ft.Icons.RECEIPT_LONG_OUTLINED, "Pesanan", on_orders),
        ],
        spacing=12,
    )

    def section_title(text, action=None, action_label="Lihat semua"):
        heading = ft.Row(
            [
                ft.Container(width=4, height=18, border_radius=2, bgcolor=PRIMARY),
                ft.Text(text, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
            ],
            spacing=8,
        )
        if action:
            return ft.Row(
                [heading, ft.TextButton(action_label, style=ft.ButtonStyle(color=PRIMARY), on_click=lambda e: action())],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        return heading

    async def load():
        retry_btn.visible = False
        page.update()
        try:
            shop_data, categories, products_data, orders = await asyncio.gather(
                asyncio.to_thread(api.shop_status),
                asyncio.to_thread(api.categories),
                asyncio.to_thread(api.products, page=1, per_page=6),
                asyncio.to_thread(api.orders),
                return_exceptions=True,
            )
        except Exception as exc:
            status_icon.name = ft.Icons.ERROR_OUTLINE
            status_icon.color = ft.Colors.RED_400
            status_text.value = str(exc)
            status_text.color = ft.Colors.RED_400
            close_info.value = ""
            retry_btn.visible = True
        else:
            if isinstance(shop_data, Exception):
                status_icon.name = ft.Icons.ERROR_OUTLINE
                status_icon.color = ft.Colors.RED_400
                status_text.value = "Status toko tidak tersedia"
                close_info.value = "Periksa koneksi lalu coba lagi"
                retry_btn.visible = True
            else:
                is_open = shop_data.get("is_open")
                status_icon.name = ft.Icons.CHECK_CIRCLE if is_open else ft.Icons.CANCEL
                status_icon.color = ft.Colors.GREEN_600 if is_open else ft.Colors.RED_400
                status_text.value = "Toko Sedang Buka" if is_open else "Toko Sedang Tutup"
                status_text.color = ft.Colors.GREEN_700 if is_open else ft.Colors.RED_600
                close_info.value = f"Buka sampai {shop_data.get('close_time', '')}" if is_open else f"Buka kembali {shop_data.get('open_time', '')}"
            if not isinstance(categories, Exception):
                categories_row.controls = [
                    ft.GestureDetector(
                        on_tap=lambda e: on_catalog() if on_catalog else None,
                        content=ft.Container(
                            padding=ft.Padding.symmetric(horizontal=14, vertical=9),
                            border_radius=20,
                            bgcolor=ft.Colors.WHITE,
                            border=ft.Border.all(1, SURFACE_COLOR),
                            content=ft.Text(item.get("nama", "Kategori"), size=12, color=ft.Colors.GREY_700),
                        ),
                    )
                    for item in categories[:8]
                ]
            if not isinstance(products_data, Exception):
                featured_row.controls = []
                for item in products_data.get("data", [])[:6]:
                    product = models.Product.from_api(item)
                    featured_row.controls.append(
                        ft.GestureDetector(
                            on_tap=lambda e, p=product: on_open_product(p) if on_open_product else None,
                            content=ft.Container(
                                width=150,
                                bgcolor=ft.Colors.WHITE,
                                border_radius=14,
                                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                                content=ft.Column(
                                    [
                                        product_image(page, product.gambar_url, max_width=320, width=150, height=92, fit=ft.BoxFit.COVER, error_content=ft.Container(bgcolor=SURFACE_COLOR, alignment=ft.Alignment.CENTER, content=ft.Icon(ft.Icons.RESTAURANT, color=PRIMARY, size=30))),
                                        ft.Container(padding=ft.Padding.all(10), content=ft.Column([ft.Text(product.nama_barang, size=12, weight=ft.FontWeight.W_600, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS), ft.Text(models.format_price(product.harga), size=13, weight=ft.FontWeight.BOLD, color=PRIMARY)], spacing=5)),
                                    ],
                                    spacing=0,
                                ),
                            ),
                        )
                    )
            if not isinstance(orders, Exception) and orders:
                order = orders[0]
                recent_order_host.content = ft.GestureDetector(
                    on_tap=lambda e: on_open_order(order) if on_open_order else None,
                    content=ft.Container(
                        bgcolor=ft.Colors.WHITE,
                        border_radius=16,
                        padding=ft.Padding.all(16),
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, color=PRIMARY),
                                ft.Column([ft.Text(order.get("order_id", "Pesanan terakhir"), size=13, weight=ft.FontWeight.BOLD), ft.Text(models.format_price(int(order.get("total") or 0)), size=12, color=ft.Colors.GREY_500)], spacing=3, expand=True),
                                status_badge(order.get("status", "pending")),
                            ],
                            spacing=10,
                        ),
                    ),
                )
            else:
                recent_order_host.content = ft.Text("Belum ada pesanan. Yuk mulai belanja!", size=12, color=ft.Colors.GREY_500)
        page.update()

    # ── Hero section ──────────────────────────────────────────────────────
    hero_section = ft.Container(
        height=170,
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
                                    color=ft.Colors.WHITE_70,
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
                                    color=ft.Colors.WHITE_60,
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
                                bgcolor=ft.Colors.WHITE_24,
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
                ft.GestureDetector(
                    on_tap=lambda e: on_catalog() if on_catalog else None,
                    content=ft.Container(
                    padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                    border_radius=12,
                    bgcolor=ft.Colors.WHITE_24,
                    content=ft.Text(
                        "Mau pesan apa hari ini?",
                        size=13,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_500,
                    ),
                    ),
                ),
            ],
            spacing=0,
        ),
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
                        quick_actions,
                        ft.Container(height=20),
                        section_title("Status Toko"),
                        ft.Container(height=8),
                        shop_banner,
                        ft.Container(height=16),
                        section_title("Kategori", on_catalog),
                        ft.Container(height=8),
                        categories_row,
                        ft.Container(height=16),
                        section_title("Produk Unggulan", on_catalog),
                        ft.Container(height=8),
                        featured_row,
                        ft.Container(height=16),
                        section_title("Pesanan Terakhir", on_orders, "Lihat pesanan"),
                        ft.Container(height=8),
                        recent_order_host,
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

    page.run_task(load)
    return main
