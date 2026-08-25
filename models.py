import locale
from dataclasses import asdict, dataclass, field

locale.setlocale(locale.LC_ALL, "")


def format_price(value: int) -> str:
    return f"Rp{value:,.0f}".replace(",", ".")


@dataclass
class Category:
    id: int
    nama: str

    @classmethod
    def from_api(cls, data: dict) -> "Category":
        return cls(id=int(data["id"]), nama=data["nama"])


@dataclass
class Product:
    id: int
    kode_barang: str
    nama_barang: str
    kategori: str
    supplier: str
    stok: int
    harga: int
    gambar_url: str

    @classmethod
    def from_api(cls, data: dict) -> "Product":
        return cls(
            id=int(data["id"]),
            kode_barang=data.get("kode_barang", ""),
            nama_barang=data.get("nama_barang", ""),
            kategori=data.get("kategori", ""),
            supplier=data.get("supplier", ""),
            stok=int(data.get("stok") or 0),
            harga=int(data.get("harga") or 0),
            gambar_url=data.get("gambar_url", ""),
        )


@dataclass
class CartItem:
    barang_id: int
    nama_barang: str
    harga: int
    quantity: int
    stok: int
    gambar_url: str = ""

    @classmethod
    def from_product(cls, product: Product, quantity: int) -> "CartItem":
        return cls(
            barang_id=product.id,
            nama_barang=product.nama_barang,
            harga=product.harga,
            quantity=quantity,
            stok=product.stok,
            gambar_url=product.gambar_url,
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CartItem":
        return cls(**{k: data[k] for k in cls.__dataclass_fields__ if k in data})