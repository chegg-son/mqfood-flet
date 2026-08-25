import requests

from config import BASE_URL, TIMEOUT


class ApiError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


_session = requests.Session()
_session.headers["Accept"] = "application/json"
_token = None


def set_token(token):
    global _token
    _token = token
    if token:
        _session.headers["Authorization"] = f"Bearer {token}"
    else:
        _session.headers.pop("Authorization", None)


def get_token():
    return _token


def _message(body):
    if isinstance(body, dict):
        if body.get("message"):
            return body["message"]
        errors = body.get("errors")
        if isinstance(errors, dict):
            return "; ".join(f"{k}: {', '.join(v)}" for k, v in errors.items())
    return "Terjadi kesalahan."


def _request(method, path, **kwargs):
    url = f"{BASE_URL}/api/{path.lstrip('/')}"
    kwargs.setdefault("timeout", TIMEOUT)

    try:
        resp = _session.request(method, url, **kwargs)
    except requests.RequestException as exc:
        raise ApiError(f"Tidak dapat terhubung ke server ({exc.__class__.__name__}).")

    try:
        body = resp.json() if resp.content else {}
    except ValueError:
        raise ApiError(f"Respons tidak valid dari server (HTTP {resp.status_code}).", resp.status_code)

    if not resp.ok:
        raise ApiError(_message(body), resp.status_code)

    return body


# --- Auth ---

def login(username, password):
    body = _request("POST", "/login", json={"username": username, "password": password})
    set_token(body["token"])
    return body


def logout():
    try:
        _request("POST", "/logout")
    finally:
        set_token(None)


# --- Catalog ---

def shop_status():
    return _request("GET", "/shop-status")


def categories():
    return _request("GET", "/categories").get("data", [])


def products(kategori=None, search=None, page=1, per_page=20):
    params = {"page": page, "per_page": per_page}
    if kategori:
        params["kategori"] = kategori
    if search:
        params["search"] = search
    return _request("GET", "/products", params=params)


def product_detail(product_id):
    return _request("GET", f"/products/{product_id}").get("data")


# --- Orders ---

def create_order(payload):
    return _request("POST", "/orders", json=payload)


def orders():
    return _request("GET", "/orders").get("data", [])


def order_detail(order_id):
    return _request("GET", f"/orders/{order_id}").get("data")


def order_status(order_id):
    return _request("GET", f"/orders/{order_id}/status").get("data")


def cancel_order(order_id):
    return _request("POST", f"/orders/{order_id}/cancel")


def upload_payment_proof(order_id, file_path):
    with open(file_path, "rb") as f:
        return _request(
            "POST",
            f"/orders/{order_id}/payment-proof",
            files={"bukti_transfer": f},
        )