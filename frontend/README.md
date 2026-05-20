# 🌿 FarmPay.ng — Frontend

```
  ●  https://farmpay-gold.vercel.app/
```

[![Vue](https://img.shields.io/badge/Vue-3.x-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.x-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.x-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Squad by GTBank](https://img.shields.io/badge/Payments-Squad_by_GTBank-green?style=for-the-badge)](https://squadco.com/)

---

## 📖 Product Overview

FarmPay is a gig/freelance-style agricultural marketplace that solves a real trust problem in Nigerian agri-commerce: buyers don't trust farmers they've never met, and farmers don't trust buyers to pay after delivery.

FarmPay fixes this with a full escrow payment system powered by Squad by GTBank:

Buyer pays → money is held in FarmPay's Squad merchant wallet (escrow)
Farmer prepares and ships the order
Dispatch rider delivers and hands the buyer an OTP
Buyer verifies the OTP → money is released to the farmer's bank account instantly via Squad's Transfer API
If the buyer disputes, an admin reviews evidence and decides who gets the funds
Additional feature: every product uploaded by a farmer is scanned by an AI disease detection model before it's listed — ensuring only healthy produce reaches buyers.

---

## 💡 How It Works

```
┌─────────────┐     pays      ┌──────────────────────┐
│    BUYER    │ ────────────► │  FarmPay Escrow       │
│             │               │  (Squad Merchant      │
└─────────────┘               │   Wallet)             │
                              └──────────┬───────────┘
                                         │ farmer prepares
                                         ▼
                              ┌──────────────────────┐
                              │      FARMER          │
                              │  ships the order     │
                              └──────────┬───────────┘
                                         │ hands OTP to buyer
                                         ▼
                              ┌──────────────────────┐
                              │   DISPATCH RIDER     │
                              │   delivers order     │
                              └──────────┬───────────┘
                                         │ buyer verifies OTP
                                         ▼
                              ┌──────────────────────┐
                              │  FUNDS RELEASED      │
                              │  to farmer's bank    │
                              │  via Squad Transfer  │
                              │  API instantly ✅    │
                              └──────────────────────┘
```

| Step | Actor | Action |
|------|-------|--------|
| 1 | 🛒 Buyer | Pays for order — funds held in FarmPay's Squad escrow wallet |
| 2 | 🌾 Farmer | Prepares and ships the order |
| 3 | 🏍️ Dispatch Rider | Delivers order and hands buyer an OTP |
| 4 | 🛒 Buyer | Verifies OTP → funds instantly released to farmer |
| 5 | ⚖️ Admin | Reviews disputes and decides fund allocation if contested |

---

## 🤖 AI Disease Detection

Every product uploaded by a farmer is **scanned by an AI disease detection model** before it's listed — ensuring only healthy produce reaches buyers.

```
Farmer uploads product image
        ↓
AI Disease Detection Model scans image
        ↓
    ┌───┴───┐
  Healthy  Diseased
    ↓          ↓
  Listed    Rejected ❌
  on         (farmer notified)
marketplace ✅
```

---

## 🏗️ Project Structure

```
src/
├── api/                    # Axios API calls and interceptors
├── assets/                 # Static assets (images, icons, fonts)
├── components/
│   ├── dashboard/          # Shared dashboard components
│   ├── farmer/             # Farmer-specific components
│   ├── marketplace/        # Marketplace UI components
│   └── PaymentModal.vue    # Squad payment integration modal
├── composables/            # Vue composables (reusable logic)
├── pages/
│   ├── admin/              # Admin panel pages
│   ├── auth/               # Login, register, OTP pages
│   ├── buyer/              # Buyer-facing pages
│   ├── farmer/             # Farmer dashboard pages
│   ├── rider/              # Dispatch rider pages
│   └── shared/             # Shared pages (404, etc.)
├── router/                 # Vue Router configuration
├── stores/                 # Pinia state management
├── App.vue                 # Root component
└── main.js                 # App entry point
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| [Vue 3](https://vuejs.org/) | Frontend framework (Composition API) |
| [Vite](https://vitejs.dev/) | Build tool and dev server |
| [Tailwind CSS](https://tailwindcss.com/) | Utility-first styling |
| [Vue Router](https://router.vuejs.org/) | Client-side routing |
| [Pinia](https://pinia.vuejs.org/) | State management |
| [Axios](https://axios-http.com/) | HTTP client |
| [Squad by GTBank](https://squadco.com/) | Escrow payments & bank transfers |

---

## ⚙️ Prerequisites

Make sure you have the following installed before proceeding:

- **Node.js** v18 or higher → [Download](https://nodejs.org/)
- **npm** v9+ or **yarn** v1.22+
- **Git** → [Download](https://git-scm.com/)

Check your versions:
```bash
node --version
npm --version
git --version
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/AbdulazeezOlawale/FarmPay.git
```

```bash
cd FarmPay
```

### 2. Install Dependencies

Using npm:
```bash
npm install
```

Or using yarn:
```bash
yarn install
```

### 3. Set Up Environment Variables

Create a `.env` file in the root of the project:

```bash
cp .env.example .env
```

Then fill in your values:

```env
VITE_API_BASE_URL=https://your-backend-api-url.com
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

### 4. Run the Development Server

```bash
npm run dev
```

Or with yarn:
```bash
yarn dev
```

The app will be running at **http://localhost:5173**

---

## 🏗️ Build for Production

```bash
npm run build
```

Preview the production build locally:
```bash
npm run preview
```

---

## 👥 User Roles

| Role | Description |
|------|-------------|
| 🛒 **Buyer** | Browse marketplace, place orders, verify OTP on delivery |
| 🌾 **Farmer** | List produce, manage orders, receive payments |
| 🏍️ **Rider** | Accept delivery jobs, generate and hand OTP to buyer |
| ⚖️ **Admin** | Manage disputes, review evidence, oversee platform |

---

## 💳 Payment Flow (Squad Escrow)

```
1. Buyer initiates payment via Squad checkout
2. Funds held in FarmPay's Squad merchant wallet
3. Farmer fulfills and ships order
4. Rider delivers — generates OTP for buyer
5. Buyer enters OTP to confirm delivery
6. Backend verifies OTP → triggers Squad Transfer API
7. Funds sent directly to farmer's bank account
```

If a dispute is raised at step 5, an **admin** reviews and manually releases or refunds the funds.
