# ☕ Campus Café — FastAPI Demo App

A fully working college café ordering system built with FastAPI + vanilla JS frontend.

---

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python main.py
# OR
uvicorn main:app --reload
```

Open **http://localhost:8000** in your browser.

---

## Demo Accounts

| Role  | Phone      | Password  |
|-------|------------|-----------|
| Admin | 9800000000 | admin123  |
| User  | 9811111111 | user123   |

---

## Project Structure

```
cafe_app/
├── main.py                  # FastAPI app entry point
├── requirements.txt
├── models/
│   ├── database.py          # In-memory DB + Pydantic schemas
│   └── auth.py              # JWT, password hashing, OTP
├── routers/
│   ├── auth.py              # /api/auth/*  (login, register, OTP)
│   ├── menu.py              # /api/menu/*  (CRUD, history)
│   ├── orders.py            # /api/orders/* (place, manage, coins)
│   └── qr.py                # /api/qr/menu  (QR code image)
└── templates/
    └── index.html           # Single-page frontend (all views)
```

---

## API Endpoints

### Auth
| Method | Endpoint              | Description              |
|--------|-----------------------|--------------------------|
| POST   | /api/auth/register    | Register new user        |
| POST   | /api/auth/login       | Login → sets cookie      |
| POST   | /api/auth/logout      | Clear session            |
| GET    | /api/auth/me          | Current user info        |
| POST   | /api/auth/send-otp    | Send OTP (demo: returns in response) |
| POST   | /api/auth/verify-otp  | Verify OTP               |

### Menu
| Method | Endpoint                    | Access      |
|--------|-----------------------------|-------------|
| GET    | /api/menu                   | Public      |
| POST   | /api/menu                   | Admin only  |
| PUT    | /api/menu/{id}              | Admin only  |
| PATCH  | /api/menu/{id}/toggle       | Admin only  |
| DELETE | /api/menu/{id}              | Admin only  |
| GET    | /api/menu/history           | Admin only  |
| GET    | /api/menu/history/{date}    | Admin only  |

### Orders
| Method | Endpoint                        | Description              |
|--------|---------------------------------|--------------------------|
| POST   | /api/orders                     | Place an order           |
| GET    | /api/orders                     | Admin: list all orders   |
| PATCH  | /api/orders/{id}/status         | Admin: update status     |
| POST   | /api/orders/coins/load          | Admin: load user coins   |
| GET    | /api/orders/coins/balance/{phone} | Admin: check balance  |
| GET    | /api/orders/users               | Admin: list users        |

### QR Code
| Method | Endpoint        | Description              |
|--------|-----------------|--------------------------|
| GET    | /api/qr/menu    | Returns QR PNG image     |

---

## Features Implemented

- ✅ QR code → public menu (unauthenticated access)
- ✅ JWT auth via HTTP-only cookies
- ✅ Register / Login / Logout
- ✅ Menu with categories, daily admin updates
- ✅ Cart with quantity control
- ✅ OTP verification before ordering (demo: OTP shown in UI)
- ✅ 3 payment methods: Coin, Cash, Online
- ✅ Coin wallet — institution-loaded, user-spent
- ✅ Menu snapshots (7-day history, auto-delete via APScheduler)
- ✅ Admin dashboard: orders, menu CRUD, user management
- ✅ Order status workflow: confirmed → preparing → ready → delivered

---

## For Production

- Replace in-memory `db` with PostgreSQL + SQLAlchemy
- Replace demo OTP with Twilio / Fast2SMS
- Set `SECRET_KEY` from environment variable
- Add HTTPS + proper CORS origins
- Use Redis for OTP storage + Celery for background jobs
