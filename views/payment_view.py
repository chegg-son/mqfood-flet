import asyncio
import base64
import io

import flet as ft
import qrcode

import api
import models
from config import BG_COLOR, PRIMARY, SECONDARY, SURFACE_COLOR, TEXT_COLOR
from ui import PAYMENT_LABELS, status_text

TERMINAL = {"success", "canceled", "expired"}


def _qr_image(qr_string, size=200):
    img = qrcode.make(qr_string)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return ft.Image(src=f"data:image/png;base64,{b64}", width=size, height=size)


def _instruction_card(title, body_controls):
    return ft.Container(
        bgcolor=ft.Colors.WHITE,
        border_radius=20,
        padding=ft.Padding.all(20),
        shadow=ft.BoxShadow(
            blur_radius=16,
            spread_radius=0,
            offset=ft.Offset(0, 4),
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        ),
        content=ft.Column(
            [
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Container(height=8),
                *body_controls
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def _value_box(label, value):
    return ft.Column(
        [
            ft.Text(label, size=12, color=ft.Colors.GREY_500),
            ft.Container(
                bgcolor=SURFACE_COLOR,
                padding=ft.Padding.symmetric(horizontal=24, vertical=12),
                border_radius=12,
                content=ft.Text(
                    value,
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=PRIMARY,
                    selectable=True,
                ),
            ),
        ],
        spacing=4,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


def build_payment_view(page: ft.Page, storage, order, payment=None, on_back=None, on_done=None):
    order_id = order["id"]
    payment = payment or order.get("payment_payload")
    method = (payment or {}).get("method", order.get("payment"))
    order_status = order.get("status", "pending")

    status_el = status_text(order_status, size=18, weight=ft.FontWeight.BOLD)
    status_hint = ft.Text(
        _hint(order_status), size=13, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER
    )
    


    from ui import status_badge
    
    status_card = ft.Container(
        bgcolor=ft.Colors.WHITE,
        border_radius=20,
        padding=ft.Padding.all(20),
        shadow=ft.BoxShadow(
            blur_radius=16,
            spread_radius=0,
            offset=ft.Offset(0, 4),
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        ),
        content=ft.Column(
            [
                status_badge(order_status, size=14),
                ft.Container(height=4),
                status_hint
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    payment_label = PAYMENT_LABELS.get(method, method or "-")
    order_card = ft.Container(
        bgcolor=ft.Colors.WHITE,
        border_radius=20,
        padding=ft.Padding.all(20),
        shadow=ft.BoxShadow(
            blur_radius=16,
            spread_radius=0,
            offset=ft.Offset(0, 4),
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        ),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("No. Pesanan", size=13, color=ft.Colors.GREY_500),
                        ft.Text(order.get("order_id", "-"), size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=4),
                ft.Row(
                    [
                        ft.Text("Metode Pembayaran", size=13, color=ft.Colors.GREY_500),
                        ft.Text(payment_label, size=13, weight=ft.FontWeight.W_600, color=TEXT_COLOR),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=8),
                ft.Container(height=1, bgcolor=ft.Colors.GREY_100),
                ft.Container(height=8),
                ft.Row(
                    [
                        ft.Text("Total Tagihan", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.Text(models.format_price(int(order.get("total") or 0)), size=18, weight=ft.FontWeight.BOLD, color=PRIMARY),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=4,
        ),
    )

    instruction_card = ft.Container(
        visible=order_status == "pending",
        content=_build_instructions(method, payment, page, order_id),
    )

    action_btn_inner = ft.Container(
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
                ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.WHITE, size=20),
                ft.Text("Lihat Pesanan Saya", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
    )

    actions_row = ft.Row(
        [
            ft.GestureDetector(
                on_tap=lambda e: on_done() if on_done else None,
                content=action_btn_inner,
            )
        ],
        spacing=8,
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
                    "Pembayaran",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_900,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    root = ft.Column(
        [
            header,
            ft.Container(
                expand=True,
                bgcolor=BG_COLOR,
                padding=ft.Padding.only(left=16, right=16, top=16),
                content=ft.Column(
                    [
                        status_card,
                        ft.Container(height=4),
                        order_card,
                        ft.Container(height=4),
                        instruction_card,
                        ft.Container(height=16),
                    ],
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            ),
            ft.Container(
                bgcolor=ft.Colors.WHITE,
                shadow=ft.BoxShadow(
                    blur_radius=20,
                    spread_radius=0,
                    offset=ft.Offset(0, -4),
                    color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
                ),
                padding=ft.Padding.all(16),
                content=actions_row,
            ),
        ],
        spacing=0,
        expand=True,
    )

    if order_status == "pending" and method in ("bank", "qris", "muamalat"):
        polling = {"active": True, "refreshing": False}

        async def poll():
            while polling["active"]:
                await asyncio.sleep(8)
                try:
                    data = api.order_status(order_id)
                except api.ApiError:
                    continue
                if data.get("status") in TERMINAL:
                    polling["active"] = False
                    _set_status(data["status"])
                    instruction_card.visible = False
                    page.update()
                    return

        def _set_status(status):
            label, color = _status_label(status)
            status_el.value = label
            status_el.color = color
            status_hint.value = _hint(status)
            nonlocal order_status
            order_status = status

        page.run_task(poll)

    return root


def _status_label(status):
    from ui import STATUS_LABELS

    label, color = STATUS_LABELS.get(status, (status, ft.Colors.GREY))
    return label, color


def _hint(status):
    return {
        "pending": "Menunggu Pembayaran. Silakan selesaikan pembayaran sesuai panduan berikut.",
        "paid": "Bukti transfer terkirim. Mohon tunggu konfirmasi admin.",
        "success": "Pembayaran Sukses! Pesanan sedang disiapkan untukmu.",
        "canceled": "Pesanan ini telah dibatalkan.",
        "expired": "Waktu pembayaran habis. Silakan pesan kembali.",
    }.get(status, "")


def _build_instructions(method, payment, page, order_id):
    if not payment:
        return ft.Container(
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            padding=ft.Padding.all(20),
            content=ft.Text(
                "Instruksi pembayaran tidak tersedia. Silakan hubungi admin.",
                size=13,
                color=ft.Colors.GREY_700,
                text_align=ft.TextAlign.CENTER,
            ),
        )

    if method == "bank":
        va = payment.get("va_number")
        rows = [
            _value_box(payment.get("bank", "VA Bank").upper(), va or "-"),
            ft.Text(
                "Salin nomor Virtual Account di atas dan transfer menggunakan ATM, Mobile Banking, atau Internet Banking. Sistem akan melakukan pengecekan otomatis.",
                size=13,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER,
            ),
        ]
        if payment.get("bill_key") or payment.get("biller_code"):
            extra = []
            if payment.get("bill_key"):
                extra.append(ft.Text(f"Bill Key: {payment['bill_key']}", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_600))
            if payment.get("biller_code"):
                extra.append(ft.Text(f"Biller Code: {payment['biller_code']}", size=13, color=TEXT_COLOR, weight=ft.FontWeight.W_600))
            rows.append(ft.Container(
                bgcolor=ft.Colors.GREY_50,
                padding=ft.Padding.all(12),
                border_radius=12,
                content=ft.Column(extra, spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ))
        return _instruction_card("Petunjuk Transfer Virtual Account", rows)

    if method == "qris":
        qr = payment.get("qr_string")
        if qr:
            return _instruction_card(
                "Scan QRIS",
                [
                    _qr_image(qr),
                    ft.Container(height=4),
                    ft.Text(
                        "Scan kode QRIS di atas menggunakan dompet digital favoritmu (Gopay, OVO, Dana, LinkAja, BCA, dll).",
                        size=13,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            )
        return _instruction_card(
            "Scan QRIS",
            [ft.Text("Kode QRIS tidak tersedia. Hubungi admin.", size=13, color=ft.Colors.GREY_700)],
        )

    if method == "muamalat":
        expiry = payment.get("expires_at")
        upload_state = ft.Text("", size=13, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER, visible=False)
        
        upload_btn_inner = ft.Container(
            height=46,
            border_radius=12,
            bgcolor=PRIMARY,
            alignment=ft.Alignment.CENTER,
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, color=ft.Colors.WHITE, size=18),
                    ft.Text("Unggah Bukti Transfer", size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

        def on_file(e):
            if not e.files:
                return
            path = getattr(e.files[0], "path", None)
            if not path:
                upload_state.value = "File tidak dapat diakses."
                upload_state.color = ft.Colors.RED
                upload_state.visible = True
                page.update()
                return
            upload_btn_inner.bgcolor = ft.Colors.GREY_300
            upload_state.value = "Mengunggah..."
            upload_state.color = ft.Colors.GREY_700
            upload_state.visible = True
            page.update()
            try:
                api.upload_payment_proof(order_id, path)
                upload_state.value = "Bukti berhasil dikirim. Menunggu konfirmasi admin."
                upload_state.color = ft.Colors.GREEN_600
            except api.ApiError as exc:
                upload_state.value = str(exc)
                upload_state.color = ft.Colors.RED
            finally:
                upload_btn_inner.bgcolor = PRIMARY
                page.update()

        file_picker = getattr(page, "_mq_file_picker", None)
        if file_picker is None:
            file_picker = ft.FilePicker()
            page._mq_file_picker = file_picker
            page.overlay.append(file_picker)
        file_picker.on_result = on_file

        rows = [
            _value_box("VIRTUAL ACCOUNT MUAMALAT", payment.get("vano") or "-"),
            ft.Text(
                "Transfer tepat ke nomor Virtual Account Muamalat di atas. Setelah transfer, silakan unggah foto bukti transfer di bawah.",
                size=13,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER,
            ),
        ]
        if expiry:
            rows.append(ft.Text(f"Berlaku sampai: {expiry}", size=12, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER))
        
        rows.extend([
            ft.Container(height=8),
            ft.GestureDetector(
                on_tap=lambda e: file_picker.pick_files(
                    allow_multiple=False,
                    dialog_title="Pilih bukti transfer",
                    file_type=ft.FilePickerFileType.IMAGE,
                ),
                content=upload_btn_inner,
            ),
            upload_state
        ])
        return _instruction_card("Virtual Account Muamalat", rows)

    return ft.Container(
        bgcolor=ft.Colors.WHITE,
        border_radius=20,
        padding=ft.Padding.all(20),
        content=ft.Text(
            "Metode pembayaran tidak dikenal. Hubungi admin.",
            size=13,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        ),
    )
