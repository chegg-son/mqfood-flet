import json

import flet as ft


class Storage:
    """Wrapper di atas flet SharedPreferences (tersimpan antar sesi).

    Values dicache di memori agar pembacaan tetap sinkron; tulis/lihat ditulis
    ke SharedPreferences secara fire-and-forget lewat page.run_task.
    """

    KEYS = {
        "token": "mqfood.token",
        "user": "mqfood.user",
        "cart": "mqfood.cart",
    }

    def __init__(self, page: ft.Page):
        self._page = page
        self._cache = {}

    async def init(self):
        sp = ft.SharedPreferences()
        for key in self.KEYS.values():
            try:
                value = await sp.get(key)
            except Exception:
                value = None
            if value is not None:
                self._cache[key] = value

    def set(self, key, value):
        payload = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        self._cache[self.KEYS[key]] = payload

        async def persist():
            try:
                await ft.SharedPreferences().set(self.KEYS[key], payload)
            except Exception:
                pass

        self._page.run_task(persist)

    def get(self, key, default=None):
        return self._cache.get(self.KEYS[key], default)

    def get_json(self, key, default=None):
        raw = self.get(key)
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return default

    def remove(self, key):
        self._cache.pop(self.KEYS[key], None)

        async def erase():
            try:
                await ft.SharedPreferences().remove(self.KEYS[key])
            except Exception:
                pass

        self._page.run_task(erase)

    # --- Cart ---

    def get_cart(self):
        return self.get_json("cart", [])

    def set_cart(self, items):
        self.set("cart", items)

    def add_cart_item(self, product, quantity=1):
        items = self.get_cart()
        for item in items:
            if item["barang_id"] == product.id:
                item["quantity"] = min(item["stok"], item["quantity"] + quantity)
                break
        else:
            items.append({
                "barang_id": product.id,
                "nama_barang": product.nama_barang,
                "harga": product.harga,
                "quantity": min(product.stok, quantity),
                "stok": product.stok,
                "gambar_url": product.gambar_url,
            })
        self.set_cart(items)
        return self.cart_total_items()

    def set_cart_quantity(self, barang_id, quantity):
        items = self.get_cart()
        for item in items:
            if item["barang_id"] == barang_id:
                item["quantity"] = max(0, min(quantity, item["stok"]))
                break
        if any(item["quantity"] <= 0 for item in items):
            items = [item for item in items if item["quantity"] > 0]
        self.set_cart(items)

    def remove_cart_item(self, barang_id):
        items = [item for item in self.get_cart() if item["barang_id"] != barang_id]
        self.set_cart(items)

    def clear_cart(self):
        self.remove("cart")

    def cart_total_items(self):
        return sum(item["quantity"] for item in self.get_cart())

    def cart_subtotal(self):
        return sum(item["quantity"] * item["harga"] for item in self.get_cart())
