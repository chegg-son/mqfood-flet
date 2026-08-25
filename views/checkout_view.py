import flet as ft

import api
import models
from config import BG_COLOR, PRIMARY, SECONDARY, SURFACE_COLOR, TEXT_COLOR


def build_checkout_view(page: ft.Page, storage, on_back, on_success):
    user = storage.get_json("user", {})

    def _field(label, icon, value="", keyboard=None, multiline=False, min_lines=1, max_lines=1):
        return ft.TextField(
            label=label,
            value=value,
            prefix_icon=icon,
            border_radius=14,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=PRIMARY,
            focused_color=PRIMARY,
            label_style=ft.TextStyle(color=ft.Colors.GREY_500),
            keyboard_type=keyboard,
            multiline=multiline,
            min_lines=min_lines,
            max_lines=max_lines,
        )

    nama_field = _field("Nama", ft.Icons.BADGE_OUTLINED, value=user.get("name") or "")
    nama_field.read_only = True
    nama_field.bgcolor = ft.Colors.GREY_100
    nama_field.border_color = ft.Colors.TRANSPARENT

    kelas_field = _field("Kelas", ft.Icons.SCHOOL_OUTLINED, value=user.get("kelas") or "")
    kelas_field.read_only = True
    kelas_field.bgcolor = ft.Colors.GREY_100
    kelas_field.border_color = ft.Colors.TRANSPARENT
    telepon_field = _field("No. Telepon", ft.Icons.PHONE_OUTLINED, keyboard=ft.KeyboardType.NUMBER)
    keterangan_field = _field("Keterangan (opsional)", ft.Icons.NOTES_OUTLINED, multiline=True, min_lines=2, max_lines=4)

    error_text = ft.Text(
        "",
        size=13,
        color=ft.Colors.RED_400,
        visible=False,
        text_align=ft.TextAlign.CENTER,
    )
    loading = ft.ProgressRing(width=20, height=20, stroke_width=2.5, color=ft.Colors.WHITE, visible=False)

    fee_text = ft.Text("", size=13, color=ft.Colors.GREY_600)
    total_text = ft.Text("", size=20, weight=ft.FontWeight.BOLD, color=PRIMARY)
    subtotal_text = ft.Text("", size=13, color=ft.Colors.GREY_800, weight=ft.FontWeight.W_500)

    # ── Payment method selection ────────────────────────────────────────────
    payments = [
        ("bank", "Transfer Bank", "Midtrans", ft.Icons.ACCOUNT_BALANCE, "+Rp4.500"),
        ("qris", "QRIS", "Midtrans", ft.Icons.QR_CODE_2, "+2%"),
        ("muamalat", "Virtual Account", "Muamalat", ft.Icons.ACCOUNT_BALANCE_WALLET, "+Rp2.000"),
    ]
    selected_payment = {"value": "bank"}
    payment_cards = ft.Column(spacing=8)

    def build_payment_cards():
        cards = []
        for p_id, p_name, p_sub, p_icon, p_fee in payments:
            is_sel = selected_payment["value"] == p_id

            def make_card(pid, pname, psub, picon, pfee):
                return ft.GestureDetector(
                    on_tap=lambda e, v=pid: select_payment(v),
                    content=ft.Container(
                        padding=ft.Padding.all(14),
                        border_radius=16,
                        bgcolor=SURFACE_COLOR if selected_payment["value"] == pid else ft.Colors.WHITE,
                        border=ft.Border.all(2, PRIMARY if selected_payment["value"] == pid else ft.Colors.TRANSPARENT),
                        shadow=ft.BoxShadow(
                            blur_radius=8,
                            spread_radius=0,
                            offset=ft.Offset(0, 2),
                            color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK),
                        ),
                        content=ft.Row(
                            [
                                ft.Container(
                                    width=42,
                                    height=42,
                                    border_radius=12,
                                    bgcolor=PRIMARY if selected_payment["value"] == pid else ft.Colors.GREY_100,
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Icon(picon, size=20, color=ft.Colors.WHITE if selected_payment["value"] == pid else ft.Colors.GREY_600),
                                ),
                                ft.Column(
                                    [
                                        ft.Text(pname, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                                        ft.Text(f"{psub}  ·  biaya {pfee}", size=12, color=ft.Colors.GREY_500),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE,
                                    size=20,
                                    color=PRIMARY if selected_payment["value"] == pid else ft.Colors.TRANSPARENT,
                                ),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ),
                )

            cards.append(make_card(p_id, p_name, p_sub, p_icon, p_fee))
        payment_cards.controls = cards
        page.update()

    def select_payment(value):
        selected_payment["value"] = value
        refresh_summary()
        build_payment_cards()

    def refresh_summary():
        subtotal = storage.cart_subtotal()
        payment = selected_payment["value"]
        fee = 4500 if payment == "bank" else (round(subtotal * 0.02) if payment == "qris" else 2000)
        subtotal_text.value = models.format_price(subtotal)
        fee_text.value = models.format_price(fee)
        total_text.value = models.format_price(subtotal + fee)
        page.update()

    def submit(e):
        def _do():
            error_text.visible = False
            nama = (nama_field.value or "").strip()
            kelas = (kelas_field.value or "").strip()
            telepon = (telepon_field.value or "").strip()

            if not kelas:
                error_text.value = "Kelas harus diisi."
                error_text.visible = True
                page.update()
                return
            if not telepon.isdigit():
                error_text.value = "Nomor telepon harus berupa angka."
                error_text.visible = True
                page.update()
                return

            cart = storage.get_cart()
            if not cart:
                error_text.value = "Keranjang kosong."
                error_text.visible = True
                page.update()
                return

            submit_btn_inner.bgcolor = ft.Colors.GREY_300
            loading.visible = True
            page.update()

            payload = {
                "nama": nama,
                "kelas": kelas,
                "telepon": telepon,
                "keterangan": keterangan_field.value or "",
                "payment": selected_payment["value"],
                "items": [{"barang_id": item["barang_id"], "quantity": item["quantity"]} for item in cart],
            }

            try:
                body = api.create_order(payload)
            except api.ApiError as exc:
                error_text.value = str(exc)
                error_text.visible = True
                submit_btn_inner.bgcolor = PRIMARY
                loading.visible = False
                page.update()
                return

            storage.clear_cart()
            submit_btn_inner.bgcolor = PRIMARY
            loading.visible = False
            page.update()
            on_success(body)

        _do()



    # ── Summary card ────────────────────────────────────────────────────────
    summary_card = ft.Container(
        padding=ft.Padding.all(16),
        border_radius=20,
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            blur_radius=16,
            spread_radius=0,
            offset=ft.Offset(0, 4),
            color=ft.Colors.with_opacity(0.09, ft.Colors.BLACK),
        ),
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
                            content=ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=18, color=PRIMARY),
                        ),
                        ft.Text("Ringkasan Pesanan", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                    ],
                    spacing=10,
                ),
                ft.Container(height=12),
                ft.Row(
                    [
                        ft.Text("Subtotal", size=13, color=ft.Colors.GREY_500),
                        subtotal_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=6),
                ft.Row(
                    [
                        ft.Text("Biaya layanan", size=13, color=ft.Colors.GREY_500),
                        fee_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=10),
                ft.Container(
                    height=1,
                    bgcolor=ft.Colors.GREY_100,
                ),
                ft.Container(height=10),
                ft.Row(
                    [
                        ft.Text("Total", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                        total_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=0,
        ),
    )

    # ── Form section ────────────────────────────────────────────────────────
    def section_title(text):
        return ft.Row(
            [
                ft.Container(width=4, height=18, border_radius=2, bgcolor=PRIMARY),
                ft.Text(text, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
            ],
            spacing=8,
        )

    form_content = ft.Column(
        [
            section_title("Data Pemesan"),
            ft.Container(height=8),
            nama_field,
            ft.Container(height=8),
            kelas_field,
            ft.Container(height=8),
            telepon_field,
            ft.Container(height=8),
            keterangan_field,
            ft.Container(height=20),
            section_title("Metode Pembayaran"),
            ft.Container(height=10),
            payment_cards,
            ft.Container(height=20),
            summary_card,
            ft.Container(height=16),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    submit_btn_inner = ft.Container(
        expand=True,
        height=52,
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
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=ft.Colors.WHITE, size=20),
                ft.Text("Buat Pesanan", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                loading,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
    )

    submit_bar = ft.Container(
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(
            blur_radius=20,
            spread_radius=0,
            offset=ft.Offset(0, -4),
            color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        content=ft.Column(
            [
                error_text,
                ft.GestureDetector(
                    on_tap=submit,
                    content=submit_btn_inner,
                ),
            ],
            spacing=8,
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
                    "Checkout",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    refresh_summary()
    build_payment_cards()

    return ft.Column(
        [
            header,
            ft.Container(
                expand=True,
                bgcolor=BG_COLOR,
                padding=ft.Padding.only(left=16, right=16, top=16),
                content=ft.Column(
                    [form_content],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=0,
                    expand=True,
                ),
            ),
            submit_bar,
        ],
        expand=True,
        spacing=0,
    )