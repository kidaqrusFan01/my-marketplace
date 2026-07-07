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
- **Careers / Jobs** — public job listings filterable by type, and a job application form
  with resume upload (PDF/DOC/DOCX, 5MB max).
- **Superuser admin** — full Django admin access to every model (users, products, orders,
  jobs, applications, reviews) for the site owner.

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

### 3. Database — already set up and seeded!

To make this easy to test immediately, this zip **includes a ready-to-use `db.sqlite3`**
already migrated and pre-loaded with demo data: 6 categories, 12 demo products, 4 job
postings, a demo seller account, and a superuser account. You can skip straight to
step 6 (`runserver`) and start clicking around.

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
