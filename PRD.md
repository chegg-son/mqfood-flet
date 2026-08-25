# MQFood Mobile — Product Requirements Document

**Version:** 0.2 (Implemented M1 + M2)
**Date:** 2026-08-12
**Status:** Active development

---

## 1. Overview

MQFood Mobile is a **mobile food-ordering application** for santri, built with **Flet (Python)**. It is the mobile companion to the existing **MQFood web app** (Laravel 11 at `/media/itpiat7/Users/IT PIAT7/Documents/root/mqfood`), which acts as the **backend service**.

The web app remains the single source of truth for admin, supplier, and finance workflows. MQFood Mobile exposes a **santri-only** storefront: browse products, manage a cart, place orders, and handle payment — all against the existing Laravel database via new REST API endpoints.

---

## 2. Goals & Non-Goals

### 2.1 Goals
- Provide a mobile (and desktop-dev) storefront for **santri users** to order food from the MQFood catalog.
- Reuse the existing Laravel backend, database, product catalog (`barangs`), categories (`kategoris`), supplier relationships, order data (`transaksis`), and payment logic (Midtrans + Muamalat VA).
- Support the same three payment methods the web supports: **Midtrans bank transfer**, **Midtrans QRIS**, and **Muamalat VA** (manual transfer with upload bukti).
- Maintain the web app's business rules: shop open/closed schedule (`TokoBuka`), stock checks, order expiry, and status flows (`pending` → `paid` → `success`; `canceled`/`expired`).

### 2.2 Non-Goals (v1)
- Admin, supplier, finance, superadmin panels (remain web-only).
- Product/category/supplier management from mobile.
- Push notifications.
- Offline shopping / local catalog caching (v2 candidate).
- Multi-store / multiple `TokoBuka` schedules.

---

## 3. Users & Roles

| Role | Access | Notes |
| --- | --- | --- |
| Santri (role `user`) | Full shopping flow | Logs in with username + password |
| Admin / Superadmin / Maqsof / Keuangan | None in mobile | Web app only |
| Supplier | None in mobile | Web app only |
| Guest (not logged in) | Browsing only | Cannot place orders (login required at checkout) |

Auth is username + password, matching web login. A santri token is issued via **Laravel Sanctum**.

---

## 4. User Flows

### 4.1 Onboarding & Auth
1. Santri opens app → Login screen (username + password).
2. Valid credentials → Sanctum token stored securely → Home screen.
3. Logout → token revoked; returns to Login.

### 4.2 Browse & Product Discovery
1. Home screen: hero/banner + product carousel (like web `HomeController`).
2. Category chips → filter products.
3. Search bar → search products by name / kode.
4. Product detail sheet/page: image, name, category, supplier, price, stock, add-to-cart with quantity.

### 4.3 Cart
- Add/remove items, adjust quantity, see per-item and subtotal.
- Cart persists locally between sessions (Flet client storage).
- Only products with stock ≥ requested quantity can be added.

### 4.4 Checkout
1. Click checkout → **login required** (if guest, prompt login first).
2. Form: **nama** (≥ 3 chars), **kelas**, **telepon** (numeric), optional **keterangan**.
3. Choose payment: **bank transfer (Midtrans)**, **QRIS (Midtrans)**, or **Muamalat VA**.
4. Backend validates: store open, stock still available.
5. Creates `Transaksi` + `TransaksiDetail` records (mirrors web `KeranjangController::actionconfirm`).
6. Returns order confirmation with payment instructions.

### 4.5 Payment
- **Midtrans bank / QRIS**: backend generates snap token + order; app shows VA number / QRIS instructions from Midtrans. Payment status polled; on `settlement` the order becomes `success` (via existing status check or webhook).
- **Muamalat VA**: app shows generated `VANO` (format `9102 + 03 + 10 digit unik`), expiry based on shop close time. Santri transfers manually and **uploads bukti transfer** → status becomes `paid` (mirrors web `actionPayment`).

### 4.6 Orders
- Order list grouped by status: **pending, paid (menunggu), success, canceled, expired** (mirrors `getUserOrdersView`).
- Order detail: items, quantities, prices, total, payment method, status, expiry.
- Cancel pending orders where allowed (mirrors web cancel flow).
- View invoice.

---

## 5. Features & Requirements

### 5.1 Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-1 | Login/logout via username + password issuing Sanctum token | P0 |
| FR-2 | Fetch shop open/closed schedule (`TokoBuka`); show closed page if store closed | P0 |
| FR-3 | List categories (`Kategori`) | P0 |
| FR-4 | List active products (`Barang` active + supplier active) with image URL, price, stock | P0 |
| FR-5 | Search products (name / kode) | P1 |
| FR-6 | Product detail with add-to-cart quantity control | P0 |
| FR-7 | Client-side cart persisted locally; quantity + stock validation | P0 |
| FR-8 | Checkout creating `Transaksi` + `TransaksiDetail` | P0 |
| FR-9 | Payment methods: bank transfer, QRIS, Muamalat VA | P0 |
| FR-10 | Show payment instructions (VA number / QRIS) and poll status for Midtrans | P0 |
| FR-11 | Upload bukti transfer for Muamalat VA orders | P0 |
| FR-12 | Order list + detail + invoice | P0 |
| FR-13 | Cancel pending order | P1 |

### 5.2 Non-Functional Requirements

| ID | Requirement |
| --- | --- |
| NFR-1 | Secure token storage; token sent via `Authorization: Bearer` header |
| NFR-2 | All API calls over HTTPS in production (configurable base URL; dev may use http/ngrok) |
| NFR-3 | Mobile-first responsive styling (usable on desktop during dev) |
| NFR-4 | Indonesian UI text |
| NFR-5 | Graceful error / loading / empty states with retry |
| NFR-6 | Base URL configurable via config file (no code change needed) |

---

## 6. Backend API Contract (Implemented)

Implemented as Laravel REST endpoints in `routes/api.php` + controllers under
`app/Http/Controllers/Api/V1/`. Verified end-to-end with curl against the live
merchant (Midtrans `MIDTRANS_IS_PRODUCTION=true`).

### 6.1 Auth
- `POST /api/login` — username + password → `{ token, user: { id, username, name, role, kelas } }`
- `POST /api/logout` — revoke current token

Auth uses the same path as the web app: `Auth::attempt` against the
`portal_santri` `users` table (role must be `user`, santri `status` must be
active). A **custom Sanctum token model** (`App\Models\SanctumToken`) was
required because Eloquent writes `morphMany` records (tokens) using the parent
model's connection — tokens live on the `portal_santri` connection, while the
default Sanctum read used the local DB. Also added missing `paid` transitions
to the `TransaksiObserver` whitelist (`pending→paid→success/canceled`).

### 6.2 Catalog
- `GET /api/shop-status` — public, mirrors `CheckShopOpen`
- `GET /api/categories` — public
- `GET /api/products?kategori=&search=` — paginated active `Barang`; `gambar_url`,
  `supplier` name, `stok`, `harga`; absolute image URLs derived from the request
  host (works behind ngrok / public server URL)
- `GET /api/products/{id}` — public

### 6.3 Orders (auth: sanctum)
- `POST /api/orders` — creates `Transaksi` + `TransaksiDetail` (server-side prices),
  returns order + payment payload
- `GET /api/orders` — list current user's orders (re-checks expiry)
- `GET /api/orders/{id}` — detail with items; syncs Midtrans status
- `POST /api/orders/{id}/cancel` — cancel pending order (muamalat: local;
  bank/qris: Midtrans `/v2/{id}/cancel`)
- `POST /api/orders/{id}/payment-proof` — upload `bukti_transfer` → `status: paid`
- `GET /api/orders/{id}/status` — poll payment status

### 6.4 Payment via Midtrans Core API (no Snap webview)
`App\Services\MidtransCore` calls `/v2/charge` directly:
- **bank transfer** → VA number returned in the response (the activated merchant
  account returns a **Permata VA**; bank configurable via `MIDTRANS_VA_BANK`)
- **QRIS** → `qr_string` returned directly in the charge response (no extra fetch)
- **Muamalat** → VANO `9102 + 03 + 10-digit` generated server-side, `expires_at`
  = shop close time

**Known limitation:** Midtrans returns HTTP 500 on `/v2/{id}/cancel` for Permata
VA (same limitation as the web app's `cancelOrder`); order stays `pending`.

### 6.5 Security
- Order endpoints are `auth:sanctum`, santri-only enforced at login (role `user`).
- Reuses existing business rules: `CheckShopOpen`, stock check, `Expirable`.

---

## 7. Technical Architecture & Milestones

### 7.1 Flet App Structure
```
mqfood-flet/
├── app.py               # Flet entry point + navigation shell
├── config.py            # BASE_URL (configurable), color theme
├── api.py               # HTTP client (requests) wrapping all endpoints
├── storage.py           # secure token + cart persistence (flet storage / file)
├── models.py            # dataclasses: Product, Category, Order, CartItem
├── views/
│   ├── login_view.py
│   ├── home_view.py
│   ├── catalog_view.py      # products grid + search + category filter
│   ├── product_detail_view.py
│   ├── cart_view.py
│   ├── checkout_view.py
│   ├── payment_view.py      # VA / QRIS / proof upload + status polling
│   └── orders_view.py
└── PRD.md
```

### 7.2 Milestones

| Milestone | Scope | Deliverable | Status |
| --- | --- | --- | --- |
| M1 | Backend API (Laravel) | New API controllers + routes; tested with curl | ✅ Done |
| M2 | Flet skeleton + auth + config | Login/logout, base URL config, store-open gate | ✅ Done |
| M3 | Catalog browsing | Categories, product list/search, product detail | ✅ Done |
| M4 | Cart + checkout | Local cart, checkout form → order creation | ✅ Done |
| M5 | Payment flows | VA/QRIS display + polling; bukti upload | ✅ Done |
| M6 | Orders + polish | Order list/detail/invoice, cancel, error/empty states | ✅ Done |
| M7 | Mobile packaging | `flet build apk` (android) — follow-up | — |

### 7.3 Implementation Notes (M1/M2)

- **Midtrans:** Core API `/v2/charge` (VA + QRIS) with payment details returned
  directly — no Snap webview needed. Fee model mirrors web: bank `+4500`,
  QRIS `+2%`, Muamalat `+2000`.
- **Auth:** `Auth::attempt` on `portal_santri` users + Sanctum token.
- **Images:** API returns absolute URLs from the request host.
- **M2 files:** `app.py` (shell + nav + token gate), `config.json`/
  `config.py` (BASE_URL), `api.py`, `storage.py` (client storage), `views/`
  (login, home with store-open gate, placeholders for M3–M6).
- **M3 files:** `models.py` (dataclasses `Product`/`Category`/`CartItem`,
  `format_price`), cart persistence ops in `storage.py`,
  `views/catalog_view.py` (category chips, search, grid, loading/error/empty),
  `views/product_detail_view.py` (image, detail, qty stepper, add-to-cart with
  stock clamp). Add-to-cart persists to client storage (cart view comes in M4).
- **Built for flet 0.86** (2026 API): `Padding.all/symmetric/only`,
  `BorderRadius.all`, `BoxFit`, `Chip` (no FilterChip), dropped
  `TextInputAction`.
- **M4 files:** `views/cart_view.py` (persisted cart, qty steppers clamped to
  stock, remove, subtotal, empty state), `views/checkout_view.py` (nama/kelas/
  telepon/keterangan form, payment radio with live fee + total, client-side
  validation, `POST /api/orders`, clears cart on success). `app.py` now uses
  per-tab **builder functions** executed on navigate so cart/checkout always
  reflect the latest persisted state.
- **M5/M6 files:** `views/payment_view.py` (status card, per-method instructions:
  VA box for bank, generated QR image for QRIS, VANO + bukti upload via
  `FilePicker` for Muamalat; auto-polling via `page.run_task` every 8 s until a
  terminal status, manual refresh), `views/orders_view.py` (order list with
  status filter chips + empty/error/retry states, detail with items/totals/
  cancel + pay-again, printable-style invoice screen). Replaces
  `confirmation_view.py` (deleted). Requires `qrcode` + `pillow`.
- **Backend for M5/M6:** migration adds `va_number/va_bank/bill_key/biller_code/
  qr_string` to `transaksis`; `OrderController::store` persists the Midtrans
  charge payload and `formatOrder` exposes `payment_payload` so VA/QR can be
  re-shown later ("pay again"). Cancel now tolerates Midtrans 500 (Permata VA)
  and still cancels locally.

---

## 8. Resolved & Open Questions

### Resolved (M1)
- **Midtrans handling:** Core API `/v2/charge` — payment details returned directly
  (VA number / `qr_string`), no Snap webview. Core API is activated on the merchant.
- **Auth source:** Same as mqfood web — `Auth::attempt` against `portal_santri`
  users table; role must be `user`.
- **Images:** API builds absolute URLs from the request host (server / ngrok URL).
- **Guest account:** Not supported — mobile app is santri-only (role `user`).

### Open
- Should `bukti_transfer` upload also apply to Midtrans (bank/QRIS) orders, or is
  Midtrans auto-confirmed via webhook only? (API already allows it for any pending
  order; policy TBD.)
- Product carousel (FR, M3): mirror web's random 7-item carousel? Requires a
  random-order option in `GET /api/products`.

---

## 9. Future Ideas (v2+)
- Push notifications for order status.
- Offline catalog caching.
- Multi-jadwal store support.
- Supplier-side mobile app.