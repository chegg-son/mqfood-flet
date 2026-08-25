import flet as ft

import models
from config import BG_COLOR, PRIMARY, SECONDARY, SURFACE_COLOR, TEXT_COLOR


def build_cart_view(page: ft.Page, storage, go_checkout, go_browse):
    list_col = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)

    empty_state = ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            [
                ft.Container(
                    width=100,
                    height=100,
                    border_radius=50,
                    bgcolor=SURFACE_COLOR,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(
                        ft.Icons.SHOPPING_CART_OUTLINED,
                        size=48,
                        color=ft.Colors.with_opacity(0.6, PRIMARY),
                    ),
                ),
                ft.Container(height=16),
                ft.Text(
                    "Keranjangmu kosong",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_800,
                ),
                ft.Text(
                    "Yuk, pilih menu favoritmu!",
                    size=13,
                    color=ft.Colors.GREY_500,
                ),
                ft.Container(height=16),
                ft.GestureDetector(
                    on_tap=lambda e: go_browse(),
                    content=ft.Container(
                        padding=ft.Padding.symmetric(horizontal=28, vertical=14),
                        border_radius=16,
                        bgcolor=PRIMARY,
                        shadow=ft.BoxShadow(
                            blur_radius=16,
                            spread_radius=0,
                            offset=ft.Offset(0, 6),
                            color=f"{PRIMARY}55",
                        ),
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.STOREFRONT_OUTLINED, color=ft.Colors.WHITE, size=18),
                                ft.Text(
                                    "Mulai Belanja",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                            spacing=8,
                        ),
                    ),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
    )

    subtotal_text = ft.Text(
        models.format_price(0),
        size=20,
        weight=ft.FontWeight.BOLD,
        color=PRIMARY,
    )
    item_count_text = ft.Text("0 item", size=12, color=ft.Colors.GREY_500)

    footer = ft.Container(
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            blur_radius=20,
            spread_radius=0,
            offset=ft.Offset(0, -4),
            color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        visible=False,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("Total Pembayaran", size=12, color=ft.Colors.GREY_500),
                                subtotal_text,
                                item_count_text,
                            ],
                            spacing=2,
                        ),
                        ft.GestureDetector(
                            on_tap=lambda e: go_checkout(),
                            content=ft.Container(
                                padding=ft.Padding.symmetric(horizontal=24, vertical=14),
                                border_radius=16,
                                bgcolor=PRIMARY,
                                shadow=ft.BoxShadow(
                                    blur_radius=14,
                                    spread_radius=0,
                                    offset=ft.Offset(0, 4),
                                    color=f"{PRIMARY}55",
                                ),
                                content=ft.Row(
                                    [
                                        ft.Text(
                                            "Checkout",
                                            size=15,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE,
                                        ),
                                        ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=14, color=ft.Colors.WHITE),
                                    ],
                                    spacing=6,
                                ),
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=0,
        ),
    )

    def item_row(item):
        qty_text = ft.Text(
            str(item["quantity"]),
            size=15,
            weight=ft.FontWeight.BOLD,
            color=TEXT_COLOR,
        )
        line_total = ft.Text(
            models.format_price(item["harga"] * item["quantity"]),
            size=14,
            weight=ft.FontWeight.BOLD,
            color=PRIMARY,
        )

        def change(delta):
            new_qty = item["quantity"] + delta
            if new_qty > item["stok"]:
                page.show_dialog(
                    ft.SnackBar(
                        ft.Text(f"Stok maksimal {item['stok']} untuk {item['nama_barang']}."),
                        bgcolor=ft.Colors.GREY_900,
                    )
                )
                page.update()
                return
            storage.set_cart_quantity(item["barang_id"], new_qty)
            refresh()

        def remove_item(e):
            storage.remove_cart_item(item["barang_id"])
            refresh()

        qty_control = ft.Container(
            border_radius=12,
            bgcolor=SURFACE_COLOR,
            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
            content=ft.Row(
                [
                    ft.GestureDetector(
                        on_tap=lambda e: change(-1),
                        content=ft.Container(
                            width=30,
                            height=30,
                            border_radius=10,
                            bgcolor=ft.Colors.WHITE,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.Icons.REMOVE, size=16, color=ft.Colors.GREY_700),
                        ),
                    ),
                    ft.Container(
                        width=32,
                        alignment=ft.Alignment.CENTER,
                        content=qty_text,
                    ),
                    ft.GestureDetector(
                        on_tap=lambda e: change(1),
                        content=ft.Container(
                            width=30,
                            height=30,
                            border_radius=10,
                            bgcolor=PRIMARY,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.Icons.ADD, size=16, color=ft.Colors.WHITE),
                        ),
                    ),
                ],
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        return ft.Container(
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=12,
                spread_radius=0,
                offset=ft.Offset(0, 4),
                color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK),
            ),
            padding=ft.Padding.all(12),
            content=ft.Row(
                [
                    ft.Container(
                        width=68,
                        height=68,
                        border_radius=14,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=ft.Image(
                            src=item["gambar_url"],
                            fit=ft.BoxFit.COVER,
                            error_content=ft.Container(
                                bgcolor=SURFACE_COLOR,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(ft.Icons.RESTAURANT, size=32, color=ft.Colors.with_opacity(0.5, PRIMARY)),
                            ),
                        ),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                item["nama_barang"],
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.GREY_900,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                models.format_price(item["harga"]),
                                size=12,
                                color=ft.Colors.GREY_500,
                            ),
                            ft.Container(height=4),
                            ft.Row(
                                [
                                    qty_control,
                                    line_total,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.GestureDetector(
                        on_tap=remove_item,
                        content=ft.Container(
                            width=32,
                            height=32,
                            border_radius=10,
                            bgcolor=ft.Colors.RED_50,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.Icons.DELETE_OUTLINE, size=17, color=ft.Colors.RED_400),
                        ),
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def refresh():
        items = storage.get_cart()
        if not items:
            empty_state.visible = True
            footer.visible = False
            list_col.controls = []
        else:
            empty_state.visible = False
            footer.visible = True
            subtotal_text.value = models.format_price(storage.cart_subtotal())
            item_count_text.value = f"{len(items)} item"
            list_col.controls = [item_row(item) for item in items]
        page.update()

    refresh()

    return ft.Column(
        [
            ft.Container(
                expand=True,
                bgcolor=BG_COLOR,
                padding=ft.Padding.only(left=16, right=16, top=12),
                content=ft.Stack(
                    [
                        ft.Container(expand=True, content=list_col),
                        empty_state,
                    ],
                    expand=True,
                ),
            ),
            footer,
        ],
        expand=True,
        spacing=0,
    )