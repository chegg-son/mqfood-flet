import flet as ft

from config import PRIMARY, SURFACE_COLOR

STATUS_LABELS = {
    "pending": ("Menunggu Bayar", ft.Colors.ORANGE_700),
    "paid": ("Menunggu Konfirmasi", ft.Colors.BLUE_600),
    "success": ("Selesai", ft.Colors.GREEN_600),
    "canceled": ("Dibatalkan", ft.Colors.RED_500),
    "expired": ("Kedaluwarsa", ft.Colors.GREY_500),
}

PAYMENT_LABELS = {
    "bank": "Transfer Bank (Midtrans)",
    "qris": "QRIS (Midtrans)",
    "muamalat": "Virtual Account Muamalat",
}

STATUS_GROUP = {
    "Menunggu": ["pending", "paid"],
    "Selesai": ["success"],
    "Lainnya": ["canceled", "expired"],
}


def status_text(status, size=13, weight=None):
    label, color = STATUS_LABELS.get(status, (status, ft.Colors.GREY))
    return ft.Text(
        label,
        size=size,
        color=color,
        weight=weight or ft.FontWeight.W_700,
    )


def status_badge(status, size=12):
    label, color = STATUS_LABELS.get(status, (status, ft.Colors.GREY))
    return ft.Container(
        bgcolor=ft.Colors.with_opacity(0.12, color),
        border_radius=20,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        content=ft.Row(
            [
                ft.Container(
                    width=5,
                    height=5,
                    border_radius=3,
                    bgcolor=color,
                ),
                ft.Text(
                    label,
                    size=size,
                    color=color,
                    weight=ft.FontWeight.W_700,
                ),
            ],
            spacing=5,
            tight=True,
        ),
    )
