# MQFood Mobile

Mobile food-ordering app for santri, built with [Flet](https://flet.dev) (Python). Companion to the existing [MQFood web app](https://mqfood.pesantrenalirsyad7.org) (Laravel 11).

## Features

- Browse products by category with search
- Product detail with stock info
- Local cart with quantity controls
- Checkout with customer info form
- Payment via Midtrans bank transfer, QRIS, or Muamalat VA
- Upload payment proof (Muamalat)
- Order list with status tracking
- Printable invoice

## Tech Stack

- **Frontend:** Flet 0.86 (Python)
- **Backend:** Laravel 11 (existing MQFood web app)
- **Auth:** Laravel Sanctum
- **Payment:** Midtrans Core API + Muamalat VA

## Project Structure

```
mqfood-flet/
├── app.py               # Entry point + navigation
├── config.py            # Theme colors, base URL
├── config.json          # API base URL config
├── api.py               # HTTP client for all endpoints
├── storage.py           # Token + cart persistence
├── models.py            # Dataclasses (Product, Order, CartItem)
├── views/
│   ├── login_view.py
│   ├── home_view.py
│   ├── catalog_view.py
│   ├── product_detail_view.py
│   ├── cart_view.py
│   ├── checkout_view.py
│   ├── payment_view.py
│   └── orders_view.py
└── PRD.md
```

## Setup

1. Install dependencies:
   ```bash
   pip install flet requests qrcode pillow
   ```

2. Configure API endpoint in `config.json`:
   ```json
   {
     "base_url": "https://mqfood.pesantrenalirsyad7.org",
     "timeout_seconds": 15
   }
   ```

3. Run the app:
   ```bash
   python app.py
   ```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/login` | No | Login with username + password |
| POST | `/api/logout` | Yes | Revoke token |
| GET | `/api/shop-status` | No | Check if store is open |
| GET | `/api/categories` | No | List categories |
| GET | `/api/products` | No | List products (paginated, filterable) |
| GET | `/api/products/{id}` | No | Product detail |
| POST | `/api/orders` | Yes | Create order |
| GET | `/api/orders` | Yes | List user orders |
| GET | `/api/orders/{id}` | Yes | Order detail |
| POST | `/api/orders/{id}/cancel` | Yes | Cancel pending order |
| POST | `/api/orders/{id}/payment-proof` | Yes | Upload payment proof |
| GET | `/api/orders/{id}/status` | Yes | Poll payment status |

## License

MIT
