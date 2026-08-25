import flet as ft

import models
from config import BG_COLOR, PRIMARY, SECONDARY, SURFACE_COLOR, TEXT_COLOR


def build_product_detail_view(page: ft.Page, storage, product: models.Product, on_back, on_add_to_cart=None):
    qty_state = {"value": 1}
    in_stock = product.stok > 0

    qty_text = ft.Text("1", size=18, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)

    def refresh_qty():
        if qty_state["value"] <= 1:
            qty_state["value"] = 1
        if qty_state["value"] >= product.stok:
            qty_state["value"] = product.stok
        qty_text.value = str(qty_state["value"])
        minus_container.bgcolor = ft.Colors.GREY_200 if qty_state["value"] <= 1 else SURFACE_COLOR
        plus_container.bgcolor = ft.Colors.GREY_200 if qty_state["value"] >= product.stok else PRIMARY
        page.update()

    def change_quantity(delta):
        qty_state["value"] += delta
        refresh_qty()

    minus_container = ft.Container(
        width=36,
        height=36,
        border_radius=10,
        bgcolor=ft.Colors.GREY_200,
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(ft.Icons.REMOVE, size=18, color=ft.Colors.GREY_700),
    )
    plus_container = ft.Container(
        width=36,
        height=36,
        border_radius=10,
        bgcolor=PRIMARY,
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(ft.Icons.ADD, size=18, color=ft.Colors.WHITE),
    )

    qty_control = ft.Container(
        border_radius=14,
        bgcolor=SURFACE_COLOR,
        padding=ft.Padding.symmetric(horizontal=6, vertical=6),
        content=ft.Row(
            [
                ft.GestureDetector(
                    on_tap=lambda e: change_quantity(-1),
                    content=minus_container,
                ),
                ft.Container(
                    width=44,
                    alignment=ft.Alignment.CENTER,
                    content=qty_text,
                ),
                ft.GestureDetector(
                    on_tap=lambda e: change_quantity(1),
                    content=plus_container,
                ),
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    def add_to_cart(e):
        storage.add_cart_item(product, qty_state["value"])
        if on_add_to_cart:
            on_add_to_cart()
        page.show_dialog(
            ft.SnackBar(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_300, size=18),
                        ft.Text(
                            f"{product.nama_barang} (×{qty_state['value']}) ditambahkan!",
                            color=ft.Colors.WHITE,
                            size=13,
                        ),
                    ],
                    spacing=8,
                ),
                bgcolor=ft.Colors.GREY_900,
            )
        )
        page.update()



    # ── Product image ──────────────────────────────────────────────────────
    product_image = ft.Container(
        height=260,
        border_radius=24,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        shadow=ft.BoxShadow(
            blur_radius=24,
            spread_radius=0,
            offset=ft.Offset(0, 8),
            color=ft.Colors.with_opacity(0.14, ft.Colors.BLACK),
        ),
        content=ft.Stack(
            [
                ft.Image(
                    src=product.gambar_url,
                    fit=ft.BoxFit.COVER,
                    width=float("inf"),
                    height=260,
                    error_content=ft.Container(
                        bgcolor=SURFACE_COLOR,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(ft.Icons.RESTAURANT, size=72, color=ft.Colors.with_opacity(0.5, PRIMARY)),
                    ),
                ),
                # Gradient overlay at bottom
                ft.Container(
                    alignment=ft.Alignment.BOTTOM_LEFT,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(0, 0.3),
                        end=ft.Alignment(0, 1),
                        colors=[ft.Colors.TRANSPARENT, ft.Colors.with_opacity(0.45, ft.Colors.BLACK)],
                    ),
                ),
            ]
        ),
    )

    # ── Meta info ──────────────────────────────────────────────────────────
    category_badge = ft.Container(
        padding=ft.Padding.symmetric(horizontal=12, vertical=5),
        border_radius=20,
        bgcolor=SURFACE_COLOR,
        content=ft.Text(
            product.kategori,
            size=12,
            color=PRIMARY,
            weight=ft.FontWeight.W_600,
        ),
    )

    stock_badge = ft.Container(
        padding=ft.Padding.symmetric(horizontal=12, vertical=5),
        border_radius=20,
        bgcolor=ft.Colors.GREEN_50 if in_stock else ft.Colors.RED_50,
        content=ft.Row(
            [
                ft.Container(
                    width=6,
                    height=6,
                    border_radius=3,
                    bgcolor=ft.Colors.GREEN_500 if in_stock else ft.Colors.RED_400,
                ),
                ft.Text(
                    "Tersedia" if in_stock else "Stok Habis",
                    size=12,
                    color=ft.Colors.GREEN_700 if in_stock else ft.Colors.RED_600,
                    weight=ft.FontWeight.W_600,
                ),
            ],
            spacing=4,
        ),
    )

    meta = ft.Column(
        [
            ft.Row([category_badge, stock_badge], spacing=8),
            ft.Container(height=8),
            ft.Text(
                product.nama_barang,
                size=22,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREY_900,
            ),
            ft.Text(
                f"Kode: {product.kode_barang}  ·  {product.supplier}",
                size=12,
                color=ft.Colors.GREY_500,
            ),
            ft.Container(height=4),
            ft.Text(
                models.format_price(product.harga),
                size=26,
                weight=ft.FontWeight.BOLD,
                color=PRIMARY,
            ),
        ],
        spacing=4,
    )

    # ── Description divider ─────────────────────────────────────────────────
    desc_section = ft.Container(
        padding=ft.Padding.all(16),
        border_radius=16,
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            blur_radius=10,
            spread_radius=0,
            offset=ft.Offset(0, 3),
            color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK),
        ),
        content=ft.Column(
            [
                ft.Text("Informasi Produk", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Container(height=8),
                ft.Row(
                    [
                        ft.Text("Kategori", size=13, color=ft.Colors.GREY_500, expand=True),
                        ft.Text(product.kategori, size=13, color=ft.Colors.GREY_800, weight=ft.FontWeight.W_500),
                    ]
                ),
                ft.Divider(height=12, color=ft.Colors.GREY_100),
                ft.Row(
                    [
                        ft.Text("Supplier", size=13, color=ft.Colors.GREY_500, expand=True),
                        ft.Text(product.supplier, size=13, color=ft.Colors.GREY_800, weight=ft.FontWeight.W_500),
                    ]
                ),
                ft.Divider(height=12, color=ft.Colors.GREY_100),
                ft.Row(
                    [
                        ft.Text("Kode", size=13, color=ft.Colors.GREY_500, expand=True),
                        ft.Text(product.kode_barang, size=13, color=ft.Colors.GREY_800, weight=ft.FontWeight.W_500),
                    ]
                ),
            ],
            spacing=0,
        ),
    )

    # ── Bottom bar ─────────────────────────────────────────────────────────
    add_btn = ft.GestureDetector(
        on_tap=add_to_cart if in_stock else None,
        content=ft.Container(
            height=50,
            border_radius=16,
            bgcolor=PRIMARY if in_stock else ft.Colors.GREY_300,
            alignment=ft.Alignment.CENTER,
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ADD_SHOPPING_CART, color=ft.Colors.WHITE, size=20),
                    ft.Text(
                        "Tambah ke Keranjang" if in_stock else "Stok Habis",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ),
    )

    bottom_bar = ft.Container(
        padding=ft.Padding.symmetric(horizontal=16, vertical=16),
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            blur_radius=20,
            spread_radius=0,
            offset=ft.Offset(0, -4),
            color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
        ),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Jumlah", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
                        qty_control,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=12),
                add_btn,
            ],
            spacing=0,
            tight=True,
        ),
    )

    header = ft.Container(
        padding=ft.Padding.only(left=8, right=16, top=12, bottom=12),
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            blur_radius=8,
            spread_radius=0,
            offset=ft.Offset(0, 2),
            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
        ),
        content=ft.Row(
            [
                ft.IconButton(
                    ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                    icon_color=ft.Colors.GREY_800,
                    icon_size=16,
                    on_click=lambda e: on_back(),
                ),
                ft.Text(
                    "Detail Produk",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    refresh_qty()

    return ft.Column(
        [
            header,
            ft.Container(
                expand=True,
                bgcolor=BG_COLOR,
                padding=ft.Padding.only(left=16, right=16, top=16),
                content=ft.Column(
                    [
                        product_image,
                        ft.Container(height=16),
                        meta,
                        ft.Container(height=16),
                        desc_section,
                        ft.Container(height=16),
                    ],
                    spacing=0,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            bottom_bar,
        ],
        expand=True,
        spacing=0,
    )