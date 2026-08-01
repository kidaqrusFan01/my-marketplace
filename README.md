# Corazon Marketplace

A full-featured, mobile-responsive e-commerce website built with Django, styled after
Amazon's look and feel. Includes product browsing & search, a shopping cart, checkout,
seller product management (via a scoped Django admin), user accounts, and a careers
section where applicants can apply for jobs.

---

## Features

- **Amazon-style storefront** — dark navy header, orange accents, product grid, search bar.
- **Mobile responsive** — a slide-out hamburger sidebar navigation on mobile/tablet, full
  top navigation on desktop.
- **Product catalog** — categories, search, pagination, discount pricing, stock tracking,
  product detail pages with related products and customer reviews.
- **Shopping cart** — session-based cart (works for logged-in and anonymous users),
  add/update/remove items, live item count badge in the navbar.
- **Checkout & orders** — shipping details form, order confirmation page, order history,
  automatic stock decrement on purchase.
- **Accounts** — separate sign-up flows for **Customers** and **Sellers**, login/logout,
  editable profile page with order history.
- **Seller admin** — sellers get a lightweight dashboard (`/seller/dashboard/`) to add,
  edit, and delete their own products, PLUS scoped access to the full Django admin
  (`/admin/`) where they can only ever see and manage *their own* products (never other
  sellers' or platform data).
- **Careers / Jobs** — public job listings filterable by type, with salary, work days, and
  work hours shown; job application form with resume upload (PDF/DOC/DOCX, 5MB max).
- **Loyalty Coin** — customers and sellers earn points for purchases and for sharing
  products via a personal referral link, with bigger bonuses when a shared link brings in
  a new buyer. Points redeem for an order discount, a delivery-fee credit, or a
  staff-reviewed request to convert to airtime/data/cash.
- **Deal of the Day** — an admin-scheduled, time-boxed featured deal shown front-and-center
  on the homepage with a live countdown; buying or sharing it earns bonus loyalty points.
- **Shop by Category** — a tile grid on the homepage for quick category navigation, the
  way most large marketplaces (Amazon, Jumia, Konga) surface categories up front.
- **"Feels alive" touches** — a pulsing live indicator, a scrolling promo ticker (flash
  sale / delivery / loyalty coin), and toast notifications built from **real recent order
  activity** (never fabricated) with a graceful fallback message set for a fresh install.
- **Advertising** — a mid-homepage ad-break section (static banner or auto-scrolling strip,
  admin-managed), an "Advertise With Us" page with a real inquiry form, and a matching
  banner on the Careers page inviting employers to post jobs through the same form.
- **Site content pages** — About, Return Policy, and Terms & Conditions, all linked from
  a proper multi-column footer.
- **Superuser admin** — full Django admin access to every model (users, products, orders,
  jobs, applications, reviews, loyalty accounts/transactions, redemption requests,
  advertisements, business inquiries) for the site owner.

---

## Project Structure

```
corazon_marketplace/
├── manage.py
├── requirements.txt
├── db.sqlite3                # SQLite database (created after migrate)
├── corazon/                  # Project settings, root urls
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── accounts/                 # Custom user model, signup/login, profile
├── products/                 # Categories, products, reviews, seller dashboard, admin scoping
│   └── management/commands/seed_demo_data.py   # Demo data seeder
├── cart/                     # Session-based shopping cart
├── orders/                   # Checkout, order history
├── jobs/                     # Job postings & applications
├── templates/                # All HTML templates (base.html + per-app folders)
├── static/
│   ├── css/style.css         # Full site stylesheet (Amazon-style theme, responsive)
│   └── js/script.js          # Mobile sidebar toggle + message auto-dismiss
└── media/                    # Uploaded product images & resumes (created at runtime)
```

Every piece of source code (models, views, forms, urls, templates, static files,
migrations) is included in this folder, so the whole project can be version-controlled,
edited, and re-run at any time — nothing was generated "on the fly" and thrown away.

---

## Setup Instructions

### 1. Requirements
- Python 3.10+ (tested with Python 3.13)
- pip

### 2. Create a virtual environment and install dependencies

```bash
cd corazon_marketplace
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Database — run migrations every time you update (important!)

> ⚠️ **This project has been updated with new database tables again** — this round adds
> the `marketing` app (Advertisements, Business/Advertising inquiries) on top of last
> round's Loyalty Coin and Deal of the Day tables. The `db.sqlite3` shipped in this zip
> has **not** been migrated to match — running the app without migrating first will
> throw errors like `no such table: marketing_advertisement`.

Run this before anything else:

```bash
python manage.py migrate
```

That's it — your existing demo products, seller, and superuser accounts are preserved;
this only adds the new tables/columns on top of them.

**Default logins (change these before any real/public use):**

| Role | Username | Password |
|---|---|---|
| Superuser (full admin) | `admin` | `admin12345` |
| Demo seller | `demo_seller` | `sellerpass123` |

If you'd rather start from a completely clean database, just delete `db.sqlite3` and
run the commands below instead.

### 4. (If starting fresh) Apply migrations

```bash
python manage.py migrate
```

### 5. (If starting fresh) Create your own admin (superuser) account

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password.

### 6. (If starting fresh, optional) Seed demo data

This populates 6 categories, 12 demo products (with a demo seller account), and
4 job postings, so the site isn't empty when you first look at it:

```bash
python manage.py seed_demo_data
```

This creates a demo seller login: **username:** `demo_seller` **password:** `sellerpass123`.

### 7. Run the development server

```bash
python manage.py runserver
```

Visit:
- **Storefront:** http://127.0.0.1:8000/
- **Careers:** http://127.0.0.1:8000/jobs/
- **Django admin:** http://127.0.0.1:8000/admin/ (log in with your superuser)

---

## How Each Feature Works / How to Test It

| Feature | How to try it |
|---|---|
| Browse & search products | Go to `/`, use the search bar or category links in the sidebar (hamburger icon on mobile) |
| Add to cart | Click "Add to Cart" on any product card or detail page |
| View/update cart | Click the cart icon top-right — update quantities or remove items |
| Checkout | From the cart, click "Proceed to Checkout" (requires login) — fill shipping info and place the order |
| Customer sign-up | `/accounts/signup/customer/` |
| Seller sign-up | `/accounts/signup/seller/` — after signing up you're redirected to your Seller Dashboard |
| Seller dashboard | `/seller/dashboard/` (only visible/accessible to accounts with `is_seller=True`) — add/edit/delete products |
| Seller in Django admin | Log in as a seller at `/admin/` — you'll only see **your own** products under "Products", nothing from other sellers and no other app data |
| Superuser in Django admin | Log in as your superuser at `/admin/` — full access to Users, Products, Orders, Jobs, Applications, Reviews |
| Product reviews | Log in, open any product detail page, scroll to "Write a Review" |
| Job listings | `/jobs/` — filter by job type |
| Job application | Open any job, fill out the form and upload a resume (PDF/DOC/DOCX) |
| Mobile sidebar | Resize your browser below ~900px width (or open on a phone) and tap the ☰ icon top-left |
| Loyalty wallet | Log in, then visit `/loyalty/wallet/` (or tap 🪙 in the nav) — balance, referral link, points history, redemption form |
| Earn points by sharing | Open any product, click Share, then click an actual platform link or "Copy Link" (opening the menu alone doesn't award points — only a completed share does) |
| Earn points via referral | Copy your referral link from the wallet page, open it in a private/incognito window, sign up as a new account, then place an order from that account — check the *original* account's wallet for the referral + new-buyer bonus |
| Redeem points at checkout | Add points to your account first (buy something, or share a few products), then at checkout enter a points amount in "Redeem loyalty points" |
| Redeem for airtime/data/cash | From the wallet page (needs 100+ points), submit a redemption request, then approve/reject it from `/admin/` → Loyalty Coin → Redemption requests |
| Deal of the Day | Visible automatically on `/` if `seed_demo_data` was run (see below) — or create/edit one at `/admin/` → Products → Deals of the Day |
| Shop by Category | Automatically shown on `/` right below the hero banner, built from your existing categories — nothing to set up |
| Promo ticker & live indicator | Visible on every page, right above the header — scrolls automatically, no setup needed |
| Live activity toast | Appears bottom-left a few seconds after page load, then every ~9 seconds. Shows real recent orders if any exist, otherwise rotates friendly tips |
| Ad break (homepage) | Empty until you add at least one banner: `/admin/` → Marketing & Site Content → Advertisements → add one (static) or two+ (auto-scrolling) |
| Advertise With Us | `/advertise/` — submit the form, then check `/admin/` → Marketing & Site Content → Business inquiries |
| Careers page recruitment banner | Visible at the top of `/jobs/` — "Post a Job With Us" links to the advertise form pre-set to job postings |
| About / Return Policy / Terms | Linked from the footer on every page (`/about/`, `/returns/`, `/terms/`) |

---

## Loyalty Coin — how the economy works

All the point values live in one file, `loyalty/constants.py`, so you can retune the
whole economy without hunting through views:

| Action | Points |
|---|---|
| Spend money (any purchase) | 1 point per ₦100 spent |
| Share a product's link (max once per product per day) | 20 points |
| Someone you referred makes their first purchase | 200 points |
| ...and that purchase was their very first order ever (new buyer) | +300 points |
| Buying or sharing the current Deal of the Day | All of the above, doubled |

**Redemption**: 1 point = ₦1. Points can be applied as a discount at checkout instantly
(no approval needed — it's just money off an order you're already placing). Converting
points to **airtime, a data bundle, or cash** is different: this project doesn't wire up
a live telco/payment API (that needs real provider credentials and isn't something to
fake), so those requests land in a `pending` queue at `/admin/` → Loyalty Coin →
Redemption requests, for a staff member to actually fulfill and mark complete — the same
way a small business would handle it by hand before automating it later. Points are
deducted the moment the request is submitted and automatically refunded if you reject one
from admin.

**Referral links**: every user (customer or seller) gets a permanent code
(`user.referral_code`), and any page visited with `?ref=CODE` in the URL remembers it for
that browser session — so sharing a specific product's link still attributes a signup to
the right referrer. A dedicated "seller agent" referral dashboard (with e.g. marketing
materials, richer analytics) was mentioned as a future page and isn't built yet — the
underlying point/referral system above is ready for it to plug into whenever you are.

---

## Notes on Design Decisions

- **Seller "admin"**: rather than build a second, separate admin panel, sellers are
  given `is_staff=True` plus scoped model permissions on sign-up, so Django's own admin
  becomes their product-management console. `ProductAdmin.get_queryset()` and the
  permission methods ensure a seller can never see or touch another seller's products,
  orders, or the user list — while a superuser retains full visibility. This satisfies
  "an admin where a seller can upload their products" without duplicating Django's admin UI.
- **Cart**: implemented with Django sessions (no login required to add items), so
  anonymous visitors can shop and only need to sign in at checkout.
- **Styling**: hand-written CSS (`static/css/style.css`) modeled on Amazon's navy/orange
  palette and card-based product grid, fully responsive with a slide-out sidebar for
  small screens (no external CSS framework dependency, so nothing to break from a CDN
  going down).

## Going to Production

This project ships with development-friendly defaults (SQLite, `DEBUG=True`, a
committed `SECRET_KEY`). Before deploying publicly:

1. Set `DJANGO_DEBUG=False` and provide a real `DJANGO_SECRET_KEY` via environment
   variables (already wired up in `settings.py` via `os.environ.get(...)`).
2. Switch `DATABASES` to Postgres/MySQL for concurrent traffic.
3. Set `DJANGO_ALLOWED_HOSTS` to your real domain(s).
4. Serve `static/` and `media/` via a proper web server or storage bucket (e.g. WhiteNoise,
   S3) instead of Django's dev-server file serving.
5. Put the whole thing behind HTTPS and enable the security settings Django's
   `manage.py check --deploy` recommends (HSTS, secure cookies, SSL redirect).

---

Enjoy building on Corazon Marketplace! Every file here is plain Django/HTML/CSS/JS —
no build step, no bundler — so you can open any file and edit it directly.
