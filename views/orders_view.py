import flet as ft

import api
import models
from config import BG_COLOR, PRIMARY, SECONDARY, SURFACE_COLOR, TEXT_COLOR
from ui import PAYMENT_LABELS, STATUS_GROUP, status_badge

FILTERS = [("Semua", None), ("Menunggu", "Menunggu"), ("Selesai", "Selesai"), ("Lainnya", "Lainnya")]


def build_orders_view(page: ft.Page, storage, open_order_detail):
    state = {"orders": [], "filter": None}

    filter_row = ft.Row([], spacing=8, scroll=ft.ScrollMode.AUTO)
    list_host = ft.Container(expand=True)

    def visible_orders():
        if not state["filter"]:
            return state["orders"]
        allowed = STATUS_GROUP.get(state["filter"], [])
        return [o for o in state["orders"] if o.get("status") in allowed]

    def render_orders():
        orders = visible_orders()
        if not state["orders"]:
            list_host.content = _empty()
        elif not orders:
            list_host.content = _empty("Tidak ada pesanan pada filter ini.")
        else:
            list_host.content = ft.ListView(
                controls=[_order_card(o) for o in orders],
                spacing=10,
                padding=ft.Padding.only(left=16, right=16, top=4, bottom=20),
                expand=True,
            )
        page.update()

    def render_filters():
        filter_row.controls.clear()
        for label, value in FILTERS:
            is_sel = state["filter"] == value

            def make_chip(lbl, val):
                return ft.GestureDetector(
                    on_tap=lambda e, v=val: set_filter(v),
                    content=ft.Container(
                        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                        border_radius=20,
                        bgcolor=PRIMARY if state["filter"] == val else ft.Colors.WHITE,
                        shadow=ft.BoxShadow(
                            blur_radius=6,
                            spread_radius=0,
                            offset=ft.Offset(0, 2),
                            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                        ),
                        content=ft.Text(
                            lbl,
                            size=13,
                            weight=ft.FontWeight.W_600 if state["filter"] == val else ft.FontWeight.W_400,
                            color=ft.Colors.WHITE if state["filter"] == val else ft.Colors.GREY_700,
                        ),
                    ),
                )

            filter_row.controls.append(make_chip(label, value))
        page.update()

    def set_filter(value):
        state["filter"] = value
        render_filters()
        render_orders()

    def _order_card(order):
        date = order.get("tanggal_transaksi") or "-"
        payment = PAYMENT_LABELS.get(order.get("payment"), order.get("payment", "-"))
        status = order.get("status", "")

        return ft.GestureDetector(
            on_tap=lambda e: open_order_detail(order),
            content=ft.Container(
                bgcolor=ft.Colors.WHITE,
                border_radius=18,
                shadow=ft.BoxShadow(
                    blur_radius=14,
                    spread_radius=0,
                    offset=ft.Offset(0, 4),
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                ),
                padding=ft.Padding.all(16),
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    width=38,
                                    height=38,
                                    border_radius=12,
                                    bgcolor=SURFACE_COLOR,
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=18, color=PRIMARY),
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            order.get("order_id", "-"),
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.GREY_900,
                                        ),
                                        ft.Text(date, size=11, color=ft.Colors.GREY_500),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                status_badge(status),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        ft.Container(height=10),
                        ft.Container(
                            height=1,
                            bgcolor=ft.Colors.GREY_100,
                        ),
                        ft.Container(height=10),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text("Metode", size=11, color=ft.Colors.GREY_400),
                                        ft.Text(payment, size=12, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500),
                                    ],
                                    spacing=2,
                                ),
                                ft.Column(
                                    [
                                        ft.Text("Total", size=11, color=ft.Colors.GREY_400),
                                        ft.Text(
                                            models.format_price(int(order.get("total") or 0)),
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=PRIMARY,
                                        ),
                                    ],
                                    spacing=2,
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    spacing=0,
                ),
            ),
        )

    def _empty(message="Belum ada pesanan. Yuk belanja dulu!"):
        return ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                [
                    ft.Container(
                        width=84,
                        height=84,
                        border_radius=42,
                        bgcolor=SURFACE_COLOR,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=42, color=ft.Colors.with_opacity(0.6, PRIMARY)),
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        message,
                        size=14,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            ),
        )

    def load():
        list_host.content = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                [
                    ft.ProgressRing(width=36, height=36, stroke_width=3.5, color=PRIMARY),
                    ft.Text("Memuat pesanan...", size=13, color=ft.Colors.GREY_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
        )
        page.update()
        try:
            state["orders"] = api.orders()
        except api.ApiError as exc:
            list_host.content = ft.Container(
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
                            content=ft.Icon(ft.Icons.CLOUD_OFF, size=34, color=PRIMARY),
                        ),
                        ft.Text(str(exc), size=13, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                        ft.GestureDetector(
                            on_tap=lambda e: load(),
                            content=ft.Container(
                                padding=ft.Padding.symmetric(horizontal=24, vertical=12),
                                border_radius=14,
                                bgcolor=PRIMARY,
                                shadow=ft.BoxShadow(
                                    blur_radius=12,
                                    spread_radius=0,
                                    offset=ft.Offset(0, 4),
                                    color=f"{PRIMARY}55",
                                ),
                                content=ft.Text("Coba Lagi", size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                            ),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
            )
        render_filters()
        render_orders()

    header = ft.Container(
        padding=ft.Padding.only(top=16, left=16, right=16, bottom=12),
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            blur_radius=8,
            spread_radius=0,
            offset=ft.Offset(0, 2),
            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
        ),
        content=ft.Container(content=filter_row),
    )

    load()

    return ft.Column(
        [
            header,
            ft.Container(
                expand=True,
                bgcolor=BG_COLOR,
                padding=ft.Padding.only(top=12),
                content=list_host,
            ),
        ],
        expand=True,
        spacing=0,
    )


def build_order_detail_view(page: ft.Page, storage, order, on_back=None, on_pay=None, on_invoice=None, on_cancel=None):
    body = ft.Column(
        expand=True,
        spacing=0,
        controls=[
            ft.Container(
                expand=True,
                bgcolor=BG_COLOR,
                alignment=ft.Alignment.CENTER,
                content=ft.ProgressRing(width=36, height=36, stroke_width=3.5, color=PRIMARY),
            )
        ],
    )

    def _row(label, value, value_color=None, value_weight=None):
        return ft.Row(
            [
                ft.Text(label, size=13, color=ft.Colors.GREY_500, expand=True),
                ft.Text(
                    value,
                    size=13,
                    color=value_color or ft.Colors.GREY_900,
                    weight=value_weight or ft.FontWeight.W_600,
                ),
            ],
            spacing=8,
        )

    def _section_card(title, icon, controls):
        return ft.Container(
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            shadow=ft.BoxShadow(
                blur_radius=14,
                spread_radius=0,
                offset=ft.Offset(0, 4),
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            ),
            padding=ft.Padding.all(16),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=36,
                                height=36,
                                border_radius=10,
                                bgcolor=SURFACE_COLOR,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(icon, size=18, color=PRIMARY),
                            ),
                            ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                        ],
                        spacing=10,
                    ),
                    ft.Container(height=12),
                    ft.Container(height=1, bgcolor=ft.Colors.GREY_100),
                    ft.Container(height=12),
                    *controls,
                ],
                spacing=8,
            ),
        )

    def refresh():
        try:
            data = api.order_detail(order["id"])
        except api.ApiError as exc:
            body.controls = [
                ft.Container(
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
                                content=ft.Icon(ft.Icons.CLOUD_OFF, size=34, color=PRIMARY),
                            ),
                            ft.Text(str(exc), size=13, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                            ft.GestureDetector(
                                on_tap=lambda e: refresh(),
                                content=ft.Container(
                                    padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                                    border_radius=12,
                                    bgcolor=PRIMARY,
                                    content=ft.Text("Coba Lagi", size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                                ),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                )
            ]
            page.update()
            return

        items = data.get("items") or []
        subtotal = sum(int(i.get("price") or 0) * int(i.get("quantity") or 0) for i in items)
        fee = int(data.get("total") or 0) - subtotal
        status = data.get("status")

        item_rows = []
        for item in items:
            item_rows.append(
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(item.get("nama_barang", "-"), size=13, color=ft.Colors.GREY_900, weight=ft.FontWeight.W_500),
                                ft.Text(f"× {item.get('quantity')}", size=12, color=ft.Colors.GREY_500),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                        ft.Text(
                            models.format_price(int(item.get("price") or 0) * int(item.get("quantity") or 0)),
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=PRIMARY,
                        ),
                    ],
                    spacing=8,
                )
            )

        bukti = []
        if data.get("bukti_transfer_url"):
            bukti.append(
                ft.Container(
                    border_radius=16,
                    shadow=ft.BoxShadow(blur_radius=10, spread_radius=0, offset=ft.Offset(0, 3), color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    content=ft.Image(
                        src=data["bukti_transfer_url"],
                        height=200,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                )
            )

        actions = []
        if status == "pending":
            actions.append(
                ft.GestureDetector(
                    on_tap=lambda e: on_pay(data) if on_pay else None,
                    content=ft.Container(
                        height=50,
                        border_radius=16,
                        bgcolor=PRIMARY,
                        shadow=ft.BoxShadow(blur_radius=12, spread_radius=0, offset=ft.Offset(0, 4), color=f"{PRIMARY}55"),
                        padding=ft.Padding.symmetric(horizontal=24, vertical=0),
                        alignment=ft.Alignment.CENTER,
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.PAYMENT, color=ft.Colors.WHITE, size=18),
                                ft.Text("Bayar Sekarang", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ),
                )
            )
            actions.append(
                ft.GestureDetector(
                    on_tap=lambda e: cancel(),
                    content=ft.Container(
                        height=50,
                        border_radius=16,
                        border=ft.Border.all(1.5, ft.Colors.RED_400),
                        padding=ft.Padding.symmetric(horizontal=24, vertical=0),
                        alignment=ft.Alignment.CENTER,
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.CLOSE, color=ft.Colors.RED_400, size=18),
                                ft.Text("Batalkan", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400),
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ),
                )
            )
        actions.append(
            ft.GestureDetector(
                on_tap=lambda e: on_invoice(data) if on_invoice else None,
                content=ft.Container(
                    height=50,
                    border_radius=16,
                    border=ft.Border.all(1.5, ft.Colors.GREY_300),
                    padding=ft.Padding.symmetric(horizontal=24, vertical=0),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.GREY_600, size=18),
                            ft.Text("Lihat Invoice", size=14, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600),
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ),
            )
        )

        # Fixed bottom bar - full-width, attached to page bottom, outside the scroll area
        bottom_bar = ft.Container(
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                blur_radius=20,
                spread_radius=0,
                offset=ft.Offset(0, -4),
                color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            content=ft.Row(
                actions,
                spacing=10,
                wrap=True,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

        from ui import status_badge as _sb

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
                        on_click=lambda e: on_back() if on_back else None,
                    ),
                    ft.Text(
                        "Detail Pesanan",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_900,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        body.controls = [
            header,
            ft.Container(
                expand=True,
                padding=ft.Padding.only(left=16, right=16, top=16, bottom=16),
                content=ft.Column(
                    [
                        _section_card(
                            "Info Pesanan",
                            ft.Icons.RECEIPT_LONG_OUTLINED,
                            [
                                ft.Row(
                                    [
                                        ft.Text(data.get("order_id", "-"), size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900, expand=True),
                                        _sb(status),
                                    ],
                                    spacing=8,
                                ),
                                ft.Container(height=4),
                                _row("Faktur", str(data.get("faktur", "-"))),
                                _row("Tanggal", str(data.get("tanggal_transaksi", "-"))),
                                _row("Metode", PAYMENT_LABELS.get(data.get("payment"), data.get("payment", "-"))),
                                _row("Nama", str(data.get("nama", "-"))),
                                _row("Kelas", str(data.get("kelas", "-"))),
                            ],
                        ),
                        # Items card
                        _section_card(
                            "Rincian Item",
                            ft.Icons.SHOPPING_BAG_OUTLINED,
                            [
                                *item_rows,
                                ft.Container(height=4),
                                ft.Container(height=1, bgcolor=ft.Colors.GREY_100),
                                ft.Container(height=8),
                                _row("Subtotal", models.format_price(subtotal)),
                                _row("Biaya layanan", models.format_price(fee)),
                                ft.Container(height=4),
                                ft.Row(
                                    [
                                        ft.Text("Total", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                                        ft.Text(
                                            models.format_price(int(data.get("total") or 0)),
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                            color=PRIMARY,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ],
                        ),
                        *bukti,
                        ft.Container(height=16),
                    ],
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            bottom_bar,
        ]
        page.update()

    def cancel():
        try:
            api.cancel_order(order["id"])
            page.show_dialog(ft.SnackBar(ft.Text("Pesanan dibatalkan."), bgcolor=PRIMARY))
            if on_cancel:
                on_cancel()
        except api.ApiError as exc:
            page.show_dialog(ft.SnackBar(ft.Text(str(exc)), bgcolor=ft.Colors.RED))
        page.update()
        refresh()

    refresh()
    return body


def build_invoice_view(page: ft.Page, storage, order, on_back=None):
    data = order
    items = data.get("items") or []
    subtotal = sum(int(i.get("price") or 0) * int(i.get("quantity") or 0) for i in items)
    fee = int(data.get("total") or 0) - subtotal
    status = data.get("status")

    item_rows = []
    for item in items:
        item_rows.append(
            ft.Row(
                [
                    ft.Text(
                        f"{item.get('nama_barang', '-')} (×{item.get('quantity')})",
                        size=13,
                        color=ft.Colors.GREY_800,
                        expand=True,
                    ),
                    ft.Text(
                        models.format_price(int(item.get("price") or 0) * int(item.get("quantity") or 0)),
                        size=13,
                        color=ft.Colors.GREY_900,
                        weight=ft.FontWeight.W_600,
                    ),
                ],
                spacing=8,
            )
        )



    invoice_card = ft.Container(
        bgcolor=ft.Colors.WHITE,
        border_radius=24,
        shadow=ft.BoxShadow(
            blur_radius=24,
            spread_radius=0,
            offset=ft.Offset(0, 8),
            color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
        ),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Column(
            [
                # Invoice header gradient
                ft.Container(
                    height=80,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, -1),
                        end=ft.Alignment(1, 1),
                        colors=["#E53935", "#FF7043"],
                    ),
                    padding=ft.Padding.all(20),
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.LOCAL_MALL, size=28, color=ft.Colors.WHITE),
                            ft.Column(
                                [
                                    ft.Text("MQFood", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    ft.Text("Pemesanan makanan santri", size=11, color=ft.Colors.WHITE70),
                                ],
                                spacing=2,
                            ),
                            ft.Container(expand=True),
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                border_radius=20,
                                bgcolor=ft.Colors.WHITE24,
                                content=ft.Text("INVOICE", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                # Invoice body
                ft.Container(
                    padding=ft.Padding.all(20),
                    content=ft.Column(
                        [
                            _inv_row("No. Invoice", str(data.get("faktur", "-"))),
                            _inv_row("Tanggal", str(data.get("tanggal_transaksi", "-"))),
                            _inv_row("Metode", PAYMENT_LABELS.get(data.get("payment"), data.get("payment", "-"))),
                            _inv_row("Status", (status or "-").upper()),
                            ft.Container(height=12),
                            ft.Container(height=1, bgcolor=ft.Colors.GREY_100),
                            ft.Container(height=12),
                            ft.Text("Dibeli oleh", size=12, color=ft.Colors.GREY_500, weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            _inv_row("Nama", str(data.get("nama", "-"))),
                            _inv_row("Kelas", str(data.get("kelas", "-"))),
                            _inv_row("Telepon", str(data.get("telepon", "-"))),
                            ft.Container(height=12),
                            ft.Container(height=1, bgcolor=ft.Colors.GREY_100),
                            ft.Container(height=12),
                            ft.Text("Item", size=12, color=ft.Colors.GREY_500, weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            *item_rows,
                            ft.Container(height=12),
                            ft.Container(height=1, bgcolor=ft.Colors.GREY_100),
                            ft.Container(height=12),
                            _inv_row("Subtotal", models.format_price(subtotal)),
                            _inv_row("Biaya layanan", models.format_price(fee)),
                            ft.Container(height=8),
                            ft.Container(
                                padding=ft.Padding.all(12),
                                border_radius=12,
                                bgcolor=SURFACE_COLOR,
                                content=ft.Row(
                                    [
                                        ft.Text("TOTAL", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                                        ft.Text(
                                            models.format_price(int(data.get("total") or 0)),
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                            color=PRIMARY,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ),
                            ft.Container(height=16),
                            ft.Text(
                                f"Terima kasih telah berbelanja di MQFood!\n{data.get('order_id', '')}",
                                size=11,
                                color=ft.Colors.GREY_400,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        spacing=6,
                    ),
                ),
            ],
            spacing=0,
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
                    on_click=lambda e: on_back() if on_back else None,
                ),
                ft.Text(
                    "Invoice",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    return ft.Column(
        [
            header,
            ft.Container(
                expand=True,
                bgcolor=BG_COLOR,
                padding=ft.Padding.all(16),
                content=ft.Column(
                    [invoice_card, ft.Container(height=16)],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                    spacing=0,
                ),
            ),
        ],
        expand=True,
        spacing=0,
    )


def _inv_row(label, value):
    return ft.Row(
        [
            ft.Text(label, size=13, color=ft.Colors.GREY_500, expand=True),
            ft.Text(value, size=13, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
        ],
        spacing=8,
    )
