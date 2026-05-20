# FarmPay — Trusted Agricultural Marketplace with Escrow Protection

<div align="center">

```
🌿 FarmPay.
```

**A secure farm-to-buyer marketplace built for Nigerian farmers.**
Buyers pay with confidence. Farmers get paid when they deliver.

![Python](https://img.shields.io/badge/Python-3.11+-green?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat-square)
![Squad](https://img.shields.io/badge/Payments-Squad-orange?style=flat-square)
![Vue](https://img.shields.io/badge/Frontend-Vue%203-42b883?style=flat-square)

</div>

---

## Table of Contents

- [What is FarmPay?](#what-is-farmpay)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Environment Setup](#environment-setup)
- [Running the Project](#running-the-project)
- [API Reference](#api-reference)
- [Testing the Full Flow](#testing-the-full-flow)
- [Escrow Architecture](#escrow-architecture)
- [Key Design Decisions](#key-design-decisions)

---

## What is FarmPay?

FarmPay is a gig/freelance-style agricultural marketplace that solves a real trust problem in Nigerian agri-commerce: **buyers don't trust farmers they've never met, and farmers don't trust buyers to pay after delivery.**

FarmPay fixes this with a full escrow payment system powered by [Squad by GTBank](https://squadco.com):

- Buyer pays → money is held in FarmPay's Squad merchant wallet (escrow)
- Farmer prepares and ships the order
- Dispatch rider delivers and hands the buyer an OTP
- Buyer verifies the OTP → money is released to the farmer's bank account instantly via Squad's Transfer API
- If the buyer disputes, an admin reviews evidence and decides who gets the funds

Additional feature: every product uploaded by a farmer is scanned by an AI disease detection model before it's listed — ensuring only healthy produce reaches buyers.

---

## How It Works

```
Buyer places order
        │
        ▼
Buyer pays via Squad hosted checkout
        │
        ▼
Money held in FarmPay Squad merchant wallet  ← ESCROW
        │
        ▼
Admin assigns dispatch rider
        │
        ▼
Rider marks order "in transit" → delivers to buyer
        │
        ▼
Buyer verifies OTP (proves physical receipt)
        │
        ▼
FarmPay calls Squad Transfer API
        │
        ▼
Money sent to farmer's bank account ✅
```

If the buyer disputes before OTP verification, admin reviews uploaded image evidence (also AI-scanned for disease) and either releases funds to the farmer or marks a refund.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2.x |
| Auth | JWT (python-jose), bcrypt |
| Payments | Squad by GTBank |
| AI Scan | Custom disease detection model |
| Frontend | Vue 3, Tailwind CSS |
| Maps/Delivery | Mapbox (geocoding) |

---

## Project Structure

```
farmpay/
├── main.py                        # FastAPI app entry point
├── .env                           # Environment variables (see setup below)
├── requirements.txt
│
├── db/
│   ├── database.py                # SQLAlchemy engine + session
│   ├── model.py                   # All DB models
│   └── schemas.py                 # Pydantic request/response schemas
│
├── authentication/
│   ├── OAuth2.py                  # JWT token creation + get_current_user
│   └── hashing.py                 # bcrypt password + OTP hashing
│
├── routers/
│   ├── auth.py                    # Register, login, farmer profile
│   ├── orders.py                  # Create order, verify OTP, get orders
│   ├── payment.py                 # Initiate, verify, webhook, callback
│   ├── admin.py                   # Riders, disputes, dashboard
│   ├── disputes.py                # Raise dispute with image evidence
│   ├── products.py                # Upload, list, delete products
│   └── reviews.py                 # Buyer reviews on delivered products
│
├── services/
│   ├── squad_payment.py           # Squad checkout + webhook verification
│   ├── payout.py                  # Squad Transfer API (escrow release)
│   ├── virtual_account.py         # Squad Static VA creation per farmer
│   ├── disease_detector.py        # AI crop disease scanning
│   └── mapbox_service.py          # Geocoding + delivery fee calculation
│
└── migration_add_payment_columns.py   # One-time DB migration script
```

---

## Environment Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ running locally or on a cloud host
- A [Squad developer account](https://dashboard.squadco.com) (sandbox is free)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/your-username/farmpay.git
cd farmpay
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file

Create a file named `.env` in the project root:

```env
# Database
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/farmpay

# JWT
SECRET_KEY=your-very-long-random-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Squad Payment (sandbox)
SQUAD_SECRET_KEY=sandbox_sk_your_squad_secret_key
SQUAD_PUBLIC_KEY=sandbox_pk_your_squad_public_key
SQUAD_BASE_URL=https://sandbox-api-d.squadco.com
SQUAD_CALLBACK_URL=http://localhost:8000/payments/callback
SQUAD_MERCHANT_ID=FARMPAY
```

> **Getting Squad keys:** Log in at [dashboard.squadco.com](https://dashboard.squadco.com) → API Keys → copy your sandbox secret and public keys.

### 5. Create the database

```bash
# In psql
createdb farmpay

# Or via psql shell
psql -U postgres -c "CREATE DATABASE farmpay;"
```

### 6. Run database migrations

```bash
# Create all tables from models
python -c "from db.database import Base, engine; from db.model import *; Base.metadata.create_all(bind=engine)"

# Then run the payment columns migration
python migration_add_payment_columns.py
```

### 7. Start the server

```bash
uvicorn main:app --reload --port 8000
```

The API is now running at `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

---

## Running the Project

### Setting up the Squad webhook (for local testing)

Squad needs a public URL to send payment events to. Use ngrok:

```bash
# Install ngrok from https://ngrok.com, then:
ngrok http 8000
```

Copy the ngrok HTTPS URL (e.g. `https://abc123.ngrok.io`) and:

1. Go to [Squad dashboard](https://dashboard.squadco.com) → Webhooks
2. Set webhook URL to: `https://abc123.ngrok.io/payments/webhook/payment`
3. Enable event types: `charge.completed` and `payment.completed`
4. Save

---

## API Reference

All authenticated endpoints require:
```
Authorization: Bearer <token>
```

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | None | Register a new user |
| POST | `/auth/login` | None | Login and get JWT token |
| POST | `/auth/farmer_profile` | Farmer | Create farmer profile + Squad VA |
| GET | `/auth/profile` | Farmer | Get own farmer profile |

### Orders

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/orders/create` | Buyer | Create order, returns OTP |
| GET | `/orders/my-orders` | Buyer | List buyer's orders |
| GET | `/orders/{order_id}` | Buyer/Rider/Admin | Get order details |
| POST | `/orders/verify-otp` | Buyer | Confirm delivery → triggers payout |
| PUT | `/orders/{order_id}/mark-transit` | Rider | Mark order as in transit |

### Payments

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/payments/initiate/{order_id}` | Buyer | Get Squad checkout URL |
| POST | `/payments/verify` | Buyer | Verify payment after checkout |
| POST | `/payments/webhook/payment` | None (Squad) | Squad webhook receiver |
| GET | `/payments/callback` | None | Browser redirect after checkout |

### Admin

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/admin/dashboard/counts` | Admin | All platform counts |
| POST | `/admin/create-dispatch-rider` | Admin | Create rider account |
| GET | `/admin/dispatch-riders` | Admin | List available riders |
| PUT | `/admin/assign-rider/{order_id}/{rider_id}` | Admin | Assign rider to order |
| GET | `/admin/disputes` | Admin | List disputes |
| PUT | `/admin/dispute/{dispute_id}/resolve` | Admin | Resolve dispute |
| GET | `/admin/users/details` | Admin | Paginated user list |
| GET | `/admin/orders/details` | Admin | Paginated order list |
| GET | `/admin/payments/details` | Admin | Paginated payment list |
| GET | `/admin/farmer-profiles/details` | Admin | Paginated farmer profiles |
| GET | `/admin/dispatch-riders/details` | Admin | Riders with stats |
| GET | `/admin/products/details` | Admin | Paginated product list |

### Products

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/products/upload` | Farmer | Upload product with AI scan |
| GET | `/products/all` | None | List all approved products |
| GET | `/products/specific/{product_id}` | None | Get single product |
| GET | `/products/my-products` | Farmer | Farmer's own products |
| DELETE | `/products/{product_id}` | Farmer | Delete product |

### Disputes

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/disputes/create` | Buyer | Raise dispute with images |

### Reviews

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/reviews/` | Buyer | Review a received product |
| GET | `/reviews/product/{product_id}` | None | Get product reviews |

---

## Testing the Full Flow

Follow these steps in order to test the entire payment and escrow lifecycle.

### Step 1 — Register accounts

```bash
# Register a buyer
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Amina Buyer",
    "email": "buyer@test.com",
    "password": "password123",
    "phone_number": "08012345678",
    "role": "buyer"
  }'

# Register a farmer
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Musa Farmer",
    "email": "farmer@test.com",
    "password": "password123",
    "phone_number": "08098765432",
    "role": "farmer"
  }'

# Register an admin
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Admin User",
    "email": "admin@test.com",
    "password": "password123",
    "phone_number": "08011111111",
    "role": "admin"
  }'
```

### Step 2 — Login and save tokens

```bash
# Login as farmer — save the token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "farmer@test.com", "password": "password123"}'
```

> Copy the `access_token` from the response. You'll use it as `FARMER_TOKEN`.

```bash
# Login as buyer — save the token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "buyer@test.com", "password": "password123"}'
```

> Copy the `access_token`. You'll use it as `BUYER_TOKEN`.

### Step 3 — Create farmer profile (creates Squad Virtual Account)

```bash
curl -X POST http://localhost:8000/auth/farmer_profile \
  -H "Authorization: Bearer FARMER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Musa Fresh Farms",
    "location": "kaduna_south",
    "nin": 12345678901,
    "bvn": "12345678901",
    "bank_name": "GTBank",
    "account_number": "0123456789"
  }'
```

> Response includes `virtual_account_number` — this is the farmer's Squad VA.

### Step 4 — Upload a product

```bash
curl -X POST http://localhost:8000/products/upload \
  -H "Authorization: Bearer FARMER_TOKEN" \
  -F "name=Fresh Tomatoes" \
  -F "price=1500" \
  -F "available_quantity=100" \
  -F "unit=kg" \
  -F "description=Grade A Kaduna tomatoes" \
  -F "image=@/path/to/tomato.jpg"
```

> Save the `product_id` from the response.

### Step 5 — Create an order (as buyer)

```bash
curl -X POST http://localhost:8000/orders/create \
  -H "Authorization: Bearer BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{"product_id": "YOUR_PRODUCT_ID", "quantity": 2}],
    "delivery_address": "Zaria Road, Kaduna"
  }'
```

> **Save the `otp` and `order_id` from this response.** The OTP is shown only once.

### Step 6 — Initiate payment

```bash
curl -X POST http://localhost:8000/payments/initiate/YOUR_ORDER_ID \
  -H "Authorization: Bearer BUYER_TOKEN"
```

> Open the `checkout_url` in your browser and complete the Squad test payment.
> Use Squad's sandbox test card: `4084 0840 8408 4081`, any future expiry, CVV `408`

### Step 7 — Verify payment

```bash
curl -X POST http://localhost:8000/payments/verify \
  -H "Authorization: Bearer BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transaction_ref": "YOUR_TRANSACTION_REF"}'
```

> Expected: `"escrow_status": "held"` — money is now in FarmPay's Squad wallet.

### Step 8 — Admin assigns a dispatch rider

```bash
# First create a rider (as admin)
curl -X POST http://localhost:8000/admin/create-dispatch-rider \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Rider One",
    "email": "rider@test.com",
    "password": "password123",
    "phone_number": "08022222222"
  }'

# Then assign to order
curl -X PUT http://localhost:8000/admin/assign-rider/ORDER_ID/RIDER_ID \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Step 9 — Rider marks order in transit

```bash
# Login as rider first to get RIDER_TOKEN, then:
curl -X PUT http://localhost:8000/orders/ORDER_ID/mark-transit \
  -H "Authorization: Bearer RIDER_TOKEN"
```

### Step 10 — Buyer verifies OTP (triggers escrow release)

```bash
curl -X POST http://localhost:8000/orders/verify-otp \
  -H "Authorization: Bearer BUYER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "YOUR_ORDER_ID",
    "otp_code": "YOUR_OTP_FROM_STEP_5"
  }'
```

> Expected response:
> ```json
> {
>   "message": "Delivery confirmed. Funds released to farmer.",
>   "escrow_status": "released",
>   "payout": {
>     "payout_status": "success",
>     "transaction_reference": "FARMPAY_..."
>   }
> }
> ```

**Confirm in DB:**
```sql
SELECT escrow_status, payout_status, payout_reference FROM payments WHERE order_id = 'YOUR_ORDER_ID';
-- Expected: released | success | FARMPAY_...

SELECT total_sales, escrow_balance FROM farmer_profiles WHERE user_id = 'FARMER_ID';
-- Expected: total_sales increased, escrow_balance decreased
```

---

### Testing Dispute Resolution

After Step 9 (delivery confirmed), instead of verifying OTP, the buyer can raise a dispute:

```bash
curl -X POST http://localhost:8000/disputes/create \
  -H "Authorization: Bearer BUYER_TOKEN" \
  -F "order_id=YOUR_ORDER_ID" \
  -F "reason=Received rotten tomatoes" \
  -F "images=@/path/to/evidence.jpg"
```

Admin resolves:
```bash
# Refund buyer
curl -X PUT http://localhost:8000/admin/dispute/DISPUTE_ID/resolve \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "refund_buyer"}'

# OR release to farmer
curl -X PUT http://localhost:8000/admin/dispute/DISPUTE_ID/resolve \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "release_farmer"}'
```

---

## Escrow Architecture

FarmPay does not use a third-party escrow service. The escrow is your Squad merchant wallet.

```
Buyer pays ──► Squad processes ──► Money lands in FarmPay Squad wallet
                                              │
                              DB: escrow_status = "held"
                                              │
                              (money physically sits here)
                                              │
                     OTP verified / Admin releases
                                              │
                              Squad Transfer API called
                                              │
                              Money moves to farmer's bank ✅
                              DB: escrow_status = "released"
                                  payout_status = "success"
```

The `escrow_balance` column on `FarmerProfile` tracks what is **owed** to each farmer. It is a ledger entry — the actual funds sit in the Squad merchant wallet until `payout/transfer` is called.

In sandbox mode, `payout.py` returns a mock response without hitting the Transfer API (no wallet balance needed for testing). In production, swap `SQUAD_BASE_URL` to `https://api-d.squadco.com` and ensure your Squad wallet has sufficient balance.

---

