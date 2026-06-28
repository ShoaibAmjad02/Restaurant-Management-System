# Restaurant Management & Online Food Ordering System

A full-stack restaurant management system with QR-based table ordering, kitchen display integration, loyalty program, time-based offers, and administrative controls. Built with Django 5.0 and MySQL.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Django 5.0.10 |
| Database | MySQL 8.0 |
| Frontend | Bootstrap 5.3, HTML5, CSS3, JavaScript (ES6) |
| Authentication | django-allauth (email-only, MFA ready) |
| PDF Generation | ReportLab (thermal 60mm receipts + loyalty cards) |
| QR Generation | qrcode (Pillow) |
| Caching | Redis (production), LocMemCache (development) |
| Payment | Cash / Card / Loyalty Points |
| Dev Tools | pytest, ruff, pre-commit, djlint, debug-toolbar |
| CI/Quality | pre-commit hooks, mypy, coverage, isort |

---

## Features

### Customer Features
- **User Registration & Login** — email-based authentication with django-allauth, mandatory email verification
- **Browse Food Menu** — browse by 8 categories (Fast Food, Drinks, Desserts, Burger, Pizza, BBQ, Sandwich, Chinese)
- **Popular Products** — curated popular items displayed on homepage
- **Product Cards** — image, name, description, price, reward points, add-to-cart
- **Shopping Cart** — localStorage-based cart (`qr_cart_<tableNo>`), persists across page reloads
- **Guest Checkout** — no account required for ordering; session-based identification
- **QR Table Ordering** — scan table QR code to open menu; cart tied to table number
- **Secure Checkout** — login-required and guest checkout flows, tax calculation, deal/offer application
- **Invoice Generation** — secure token-based PDF invoice (58mm thermal format) with QR verification
- **Order Tracking** — real-time order status tracking (Pending → Preparing → Ready → Delivered)
- **Loyalty Program** — auto-created loyalty card on login, earn/redeem points, PDF/PNG card download
- **Today's Deals** — special combo pricing, free product offers, percentage discounts
- **Time-Based Offers** — popup and banner offers with scheduled start/end times
- **Customer Timezone** — auto-detected via JavaScript `Intl.DateTimeFormat()`, stored per user

### Admin Features
- **Dashboard** — 18 KPI cards: total revenue, order counts, active/pending/delivered stats, food items, tables, customers, tax analytics
- **Product Management** — CRUD for food items (name, price, category, image, availability, popular flag, reward points)
- **Table Management** — CRUD for restaurant tables, QR code generation per table
- **Invoice Management** — search invoices by number/email/name, view details, re-print PDF
- **Order Management** — view orders by status, by date, kitchen user assignment
- **Kitchen User Management** — create/edit/delete kitchen staff accounts
- **Offer Management** — CRUD for time-based offers with banner images, scheduling
- **Deal Management** — CRUD for today's deals (free product, combo price, percentage), product assignment
- **Loyalty Management** — view all loyalty cards, card details, toggle active/blocked, reset points, export CSV, reports
- **MySQL Backup** — one-click database dump download
- **Revenue Filtering** — filter revenue by date range
- **Tax Analytics** — breakdown of card/cash tax collections

### Kitchen Features
- **Kitchen Dashboard** — real-time view of incoming orders with status cards
- **Order Status Updates** — toggle orders through Pending → Preparing → Ready → Delivered
- **Auto Loyalty Earning** — points automatically awarded when order status reaches "Delivered"
- **Order Search** — search kitchen orders by order number

---

## Implemented Workflow

### Homepage
- Renders `index.html` with popular products (up to 6, filtered by `is_popular=True`, fallback to recent)
- Displays active time-based offer and today's deal banners
- Navigation: Browse Food, Download App, About Us sections

### Browse Food
- Access via `restaurant-detail` page (requires login)
- All food items displayed by category with product cards
- Each card shows image, name, description, price, reward points

### Popular Products
- Admin marks items as `is_popular = True` in product edit
- Homepage fetches latest 6 popular items via `Food.objects.filter(available=1, is_popular=True)[:6]`
- Fallback to most recently created items if none marked popular

### Add to Cart Flow
- Cart stored in `localStorage` under key `qr_cart_<tableNo>`
- Product cards have "Add to Cart" button
- Cart sidebar shows items with quantity controls (+/-) and subtotal
- Cart includes tax (configurable percentage), deal discounts, QR offer discounts
- Minicart dropdown in header shows cart summary

### Login Flow
- Login URL set to `food-delivery:food_delivery_login`
- `?next=` parameter supported for redirect after login
- On successful login:
  - Loyalty card auto-created if not existing
  - First-time login redirects to loyalty card page
  - Staff → admin dashboard, kitchen → kitchen dashboard, others → home
- Unauthenticated cart items preserved via session/table association

### Restaurant Detail Flow
- QR code scan: `/menu/?table=<no>&token=<token>` validates table token
- Session stores `table_no` and `menu_accessed` flags
- Guest users can browse; checkout requires login or uses guest checkout

### Checkout Process
1. Cart data submitted via POST (login-required `checkout_invoice`) or AJAX (guest `guest_checkout`)
2. `_create_order_from_cart()` processes:
   - Product validation and pricing
   - Deals/offers discount application
   - Tax calculation
   - Loyalty point validation and deduction
   - Invoice creation with UUID token
   - KitchenOrder + KitchenOrderItem creation
   - Invoice QR code generation
   - Cart clearing
3. Response returns invoice UUID for PDF generation and order tracking

### Loyalty Points Protection
- `loyalty_points_processed` boolean on Invoice prevents duplicate processing
- Points only awarded once when kitchen order status changes to "Delivered"
- `LoyaltyTransaction` records each earn/redeem event with running balance

---

## Backend Documentation

### Framework
Django 5.0.10 with 3 settings modules (base, local, production), django-environ for configuration, Argon2 password hashing.

### Apps / Modules

| App | Purpose |
|-----|---------|
| `megaone.users` | Core app: users, auth, orders, admin, loyalty, offers, deals, kitchen |
| `menu` | Menu management: Category and Food models |
| `orders` | Legacy cart/order models (unused in active ordering flow) |
| `megaone.apps.food_delivery` | Static template views for food delivery pages |

### Models (17 total)

| Model | App | Fields |
|-------|-----|--------|
| `User` | users | email, name, phone, is_active, is_staff, is_operator, is_kitchen, timezone |
| `Category` | menu | name |
| `Food` | menu | category (FK), name, description, price, reward_points, image, available, is_popular |
| `RestaurantTable` | users | table_no, qr_code_image, qr_token |
| `Invoice` | users | uuid_token, user (FK), customer_name/email/table_no/session_id, payment_method, tax, subtotal, total, loyalty fields, offer/deal discounts |
| `InvoiceItem` | users | invoice (FK), product_name, price, quantity, subtotal |
| `KitchenOrder` | users | uuid_token, invoice (O2O), order_number, table_no, status (pending/preparing/ready/delivered) |
| `KitchenOrderItem` | users | order (FK), product_name, quantity |
| `LoyaltyCard` | users | card_number, user (FK), total/used/remaining points, qr_token, card_pdf, card_image, status |
| `LoyaltyTransaction` | users | card (FK), order_number, earned/redeemed points, remaining_balance, transaction_type |
| `QRTableOffer` | users | is_active, discount_percentage, start/end_datetime |
| `TimeBasedOffer` | users | title, description, discount%, banner_image, background_color, popup_image, schedule, usage_count |
| `TodayDeal` | users | title, description, products (M2M→Food), free_product (FK), combo_price, discount%, images, schedule, deal_type (property) |
| `Cart` (legacy) | orders | user (FK), food (FK), quantity |
| `Order` (legacy) | orders | user (FK), total_amount, status |
| `OrderItem` (legacy) | orders | order (FK), food (FK), quantity, price |

### APIs (JSON Endpoints)

All endpoints are Django views returning `JsonResponse` — no Django REST Framework.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/users/offers/active-data/` | GET | Active time-based offer data |
| `/users/deals/active-data/` | GET | Active today's deal data |
| `/users/offers/banner-data/` | GET | Offer banner image/data |
| `/users/loyalty-card/data/` | GET | Current user's loyalty card data |
| `/users/loyalty-card/checkout-info/` | GET | Loyalty points available for checkout |
| `/users/loyalty-card/checkout-validate/` | POST | Validate loyalty points redemption |
| `/users/guest-checkout/` | POST | Guest order creation (CSRF exempt) |
| `/users/order-tracking-data/<invoice_no>/` | GET | Order tracking status data |
| `/users/set-timezone/` | POST | Save user timezone |

### Authentication
- Custom `User` model with email as unique identifier (`USERNAME_FIELD = "email"`)
- django-allauth for authentication pipeline (email-only, no username)
- Mandatory email verification (`ACCOUNT_EMAIL_VERIFICATION = "mandatory"`)
- Argon2 hashing (primary), PBKDF2 + BCrypt fallbacks
- Custom `AccountAdapter` checks `ACCOUNT_ALLOW_REGISTRATION` setting

### Authorization
- `@staff_member_required` for admin dashboard
- `@login_required` for checkout, restaurant detail, loyalty pages
- User flags: `is_staff` (admin), `is_operator`, `is_kitchen`
- All admin views check `staff_member_required` decorator
- Session cookie: `restaurant_sessionid`, HTTP-only

### Database Relationships
```
User 1──* Invoice
User 1──* LoyaltyCard
LoyaltyCard 1──* LoyaltyTransaction
Invoice 1──* InvoiceItem
Invoice 1──1 KitchenOrder
KitchenOrder 1──* KitchenOrderItem
Category 1──* Food
Food *──M──* TodayDeal (M2M)
Food 1──* TodayDeal (free_product FK)
Invoice *──1 TodayDeal
```

---

## Frontend Documentation

### Customer Pages

| Template | Route | Description |
|----------|-------|-------------|
| `index.html` | `/` | Homepage with popular products, offers, deals |
| `food-delivery/login.html` | `/food-delivery/login` | Customer login page |
| `food-delivery/registration.html` | `/food-delivery/registration` | Customer registration page |
| `food-delivery/accounts.html` | `/food-delivery/accounts` | User accounts page |
| `food-delivery/restaurant-detail.html` | `/food-delivery/restaurant-detail` | Main menu browsing + cart + checkout |
| `food-delivery/restaurant-listing.html` | `/food-delivery/restaurant-listing` | Restaurant listings |
| `food-delivery/order_tracking.html` | `/users/order-tracking/<invoice_no>/` | Real-time order status tracking |
| `food-delivery/invoice_verify.html` | `/users/invoice/<uuid_token>/verify/` | QR-scanned invoice verification |
| `food-delivery/deal_detail.html` | `/users/deals/<pk>/public/` | Public deal detail page |
| `food-delivery/offers_popup.html` | (modal partial) | Time-based offer popup |
| `food-delivery/menu_banner.html` | (header partial) | Active offer/deal banner |

### Admin Pages

| Template | Route | Description |
|----------|-------|-------------|
| `admin/dashboard.html` | `/users/dashboard/` | Admin dashboard with 18 KPI cards |
| `admin/products.html` | `/users/products/` | Product listing |
| `admin/add_product.html` | `/users/products/add/` | Add product form |
| `admin/edit_product.html` | `/users/products/<pk>/edit/` | Edit product form |
| `admin/tables.html` | `/users/tables/` | Table management |
| `admin/invoices.html` | `/users/invoices/` | Invoice search |
| `admin/kitchen_users.html` | `/users/kitchen-users/` | Kitchen user management |
| `admin/offer_list.html` | `/users/offers/` | Offer listing |
| `admin/offer_form.html` | `/users/offers/add/` `/offers/<pk>/edit/` | Offer create/edit |
| `admin/offer_detail.html` | `/users/offers/<pk>/` | Offer detail view |
| `admin/deal_list.html` | `/users/deals/` | Deal listing |
| `admin/deal_form.html` | `/users/deals/add/` `/deals/<pk>/edit/` | Deal create/edit |
| `admin/deal_detail.html` | `/users/deals/<pk>/` | Deal detail view |
| `admin/base_admin.html` | — | Admin layout with sidebar |

### Kitchen Pages
| Template | Route | Description |
|----------|-------|-------------|
| `kitchen/dashboard.html` | `/users/kitchen/dashboard/` | Kitchen order display with status controls |

### User Pages
| Template | Route | Description |
|----------|-------|-------------|
| `users/operator_dashboard.html` | — | Operator dashboard |
| `users/loyalty_card.html` | `/users/loyalty-card/` | Customer loyalty card view |
| `users/admin_loyalty_list.html` | `/users/loyalty-card/admin/list/` | Admin loyalty card listing |
| `users/admin_loyalty_detail.html` | `/users/loyalty-card/admin/card/<card_no>/` | Admin card detail |
| `users/admin_loyalty_reports.html` | `/users/loyalty-card/admin/reports/` | Loyalty reports |

### Components
- **Preloader** — animated spinner on page load
- **Cart** — localStorage-based with minicart dropdown, quantity controls, subtotal display
- **Order status tracking** — real-time polling (3-second interval) with 4-step visual progress (Pending/Preparing/Ready/Delivered)
- **Product cards** — image, name, description, price, reward points badge, add-to-cart button
- **Offer popup** — modal with time-based offer details
- **Invoice receipt** — 58mm thermal PDF format, includes QR code for verification
- **Loyalty card** — generated as 86×54mm PDF and 600×376px PNG with gradient background, QR code, customer details
- **Notifications** — SweetAlert2 for order success, payment, and status updates

### Admin Panel UI
- Dark theme sidebar (`#0f172a` background) with gradient cards
- Responsive: sidebar collapses to 60px on mobile
- DataTables integration for sortable/searchable tables
- AOS (Animate on Scroll) animations
- Gradient stat cards with icons for KPIs

### Navigation Structure (Customer)

```
- Home (/)
  - Browse Food (→ restaurant-detail, login required)
  - Download App (→ #app-sec)
  - About Us (→ #about-sec)
  - Cart (header dropdown)
  - Orders (header dropdown, real-time status)
  - Login/Logout
```

### Admin Sidebar

```
- Dashboard
- Products (list, add, edit, delete)
- Tables (list, add, edit, delete, generate QR)
- Invoices (search, view, print)
- Loyalty Cards (list, detail, toggle, reset, reports, export CSV)
- Offers (time-based: list, add, edit, delete)
- Deals (today's deals: list, add, edit, delete)
- Kitchen Users (list, create, edit, delete)
- MySQL Backup
- Logout
```

### Responsive Behavior
- Admin sidebar collapses to icon-only mode at ≤768px
- Customer templates use Bootstrap 5 grid (col-6, col-lg-3, etc.)
- Cart minicart scrollable (max-height 350px)
- Order tracking page adapts to mobile with stacked status cards
- Product cards in grid layout using Bootstrap 5 responsive columns

---

## Setup Guide

### Requirements
- Python 3.12+
- MySQL 8.0+
- Redis (optional, for production caching)
- pip + virtualenv

### Environment Variables
Create a `.env` file in the project root (optional, read when `DJANGO_READ_DOT_ENV_FILE=True`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_DEBUG` | `False` | Debug mode |
| `DJANGO_SECRET_KEY` | *(hardcoded in local)* | Secret key |
| `DJANGO_ALLOWED_HOSTS` | `example.com` | Production allowed hosts |
| `DATABASE_URL` | — | Database URL (production) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `DJANGO_EMAIL_BACKEND` | SMTP | Email backend |
| `DJANGO_ACCOUNT_ALLOW_REGISTRATION` | `True` | Allow new registrations |
| `AWS_ACCESS_KEY_ID` | — | S3 static/media (production) |
| `AWS_SECRET_ACCESS_KEY` | — | S3 static/media (production) |
| `AWS_STORAGE_BUCKET_NAME` | — | S3 bucket name |
| `MAILGUN_API_KEY` | — | Mailgun email (production) |
| `MAILGUN_API_URL` | `https://api.mailgun.net/v3` | Mailgun URL |

### Installation

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd Restaurant Management System

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements/local.txt

# 4. Create MySQL database
mysql -u root -p -e "CREATE DATABASE cafe CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 5. Run migrations
python manage.py migrate

# 6. Seed categories (optional)
python manage.py migrate menu 0003

# 7. Create superuser
python manage.py createsuperuser

# 8. Collect static files
python manage.py collectstatic

# 9. Run development server
python manage.py runserver
```

### Running Tests
```bash
pytest
```

---

## Project Structure

```
Restaurant Management System/
├── config/                          # Django project configuration
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                  # Shared settings (DB, apps, auth, etc.)
│   │   ├── local.py                 # Development settings
│   │   ├── production.py            # Production settings (S3, Redis, SSL)
│   │   └── test.py                  # Test settings
│   ├── __init__.py
│   ├── urls.py                      # Root URL dispatcher
│   └── wsgi.py
├── megaone/                         # Main application package
│   ├── apps/
│   │   └── food_delivery/           # Static template views
│   │       ├── urls.py (6 routes)
│   │       └── views.py (6 TemplateViews)
│   ├── contrib/sites/               # Custom sites migrations
│   ├── static/                      # Static assets
│   │   └── food-delivery/
│   │       ├── css/
│   │       ├── js/
│   │       ├── fonts/
│   │       └── img/
│   ├── templates/
│   │   ├── base.html                # Base template with timezone detection
│   │   ├── index.html               # Homepage
│   │   ├── admin/                   # 14 admin panel templates
│   │   ├── food-delivery/           # 10 customer-facing templates
│   │   ├── kitchen/                 # Kitchen dashboard
│   │   ├── operator/                # Operator dashboard
│   │   ├── users/                   # User/loyalty templates
│   │   └── error pages (403, 404, 500)
│   ├── users/                       # Core app (models, views, URLs)
│   │   ├── models.py                # 11 models
│   │   ├── views.py                 # 57+ view functions (2228 lines)
│   │   ├── urls.py                  # 75 URL patterns
│   │   ├── admin.py                 # 9 models registered in admin
│   │   ├── forms.py                 # Custom auth forms
│   │   ├── managers.py              # UserManager
│   │   ├── adapters.py              # allauth adapters
│   │   ├── middleware.py            # Session + timezone middleware
│   │   ├── context_processors.py
│   │   ├── loyalty_utils.py         # QR, PDF, PNG card generation (288 lines)
│   │   └── tests/
│   │       ├── factories.py
│   │       ├── test_views.py
│   │       ├── test_urls.py
│   │       ├── test_models.py
│   │       ├── test_managers.py
│   │       ├── test_forms.py
│   │       └── test_admin.py
│   ├── media/                       # User-uploaded media
│   │   └── table_qrcodes/
│   ├── __init__.py
│   └── conftest.py
├── menu/                            # Menu management app
│   ├── models.py                    # Category, Food
│   ├── admin.py                     # FoodAdmin
│   ├── signals.py                   # Image cleanup
│   └── migrations/                  # 5 migrations
├── orders/                          # Legacy orders app
│   ├── models.py                    # Cart, Order, OrderItem (legacy)
│   ├── admin.py                     # CartAdmin, OrderAdmin, OrderItemAdmin
│   └── migrations/                  # 1 migration
├── locale/                          # Translations
│   ├── en_US/LC_MESSAGES/django.po
│   ├── fr_FR/LC_MESSAGES/django.po  # French (~40 strings)
│   └── pt_BR/LC_MESSAGES/django.po  # Brazilian Portuguese (~40 strings)
├── requirements/
│   ├── base.txt                     # Core: Django 5.0.10, allauth, Pillow, etc.
│   ├── local.txt                    # Dev: pytest, ruff, debug-toolbar, etc.
│   └── production.txt               # Prod: gunicorn, S3, Mailgun, Redis
├── utility/                         # Shell scripts for OS/Python setup
├── manage.py
├── pyproject.toml                   # Pytest, coverage, mypy, ruff, djlint config
├── .pre-commit-config.yaml          # Pre-commit hooks
├── .editorconfig
├── .gitignore
├── docker-compose.docs.yml          # Docs-only Docker setup
└── README.md
```

---

## Changelog

### Latest Updates (from git history)
- **Update login URL** for authentication flow, add warning message for unauthenticated users on loyalty card view
- **Add popular products feature** to homepage, enhance Food model with `is_popular` field
- **Update navigation** links to point to restaurant detail page and gallery section
- **Implement home view** with active offers and deals integration into templates
- **Browse Food navigation** — direct link to restaurant-detail page
- **Popular Products system** — homepage shows up to 6 popular items with fallback to recent
- **Product cards** — enhanced with reward points display
- **Authentication redirect flow** — `?next=` parameter support, role-based redirects (admin/kitchen/customer)
- **QR Table Menu** — menu access via table QR codes with token validation
- **Guest Checkout** — order without account via session-based customer identification
- **Invoice PDF generation** — 58mm thermal format with QR verification
- **Order Tracking** — real-time polling with 4-step status visualizer
- **Loyalty system** — auto card creation, earn/redeem points, PDF/PNG card generation
- **Time-Based Offers** — scheduled offers with popup/banner display
- **Today's Deals** — combo price, free product, percentage discount types
- **Admin Dashboard** — 18 KPI cards with revenue, tax, order analytics
- **Database backup** — one-click MySQL dump download
- **Multi-language support** — French, Brazilian Portuguese translations

---

## Future Improvements

- [ ] **REST API layer** — migrate JSON endpoints to Django REST Framework with versioned API
- [ ] **Real-time WebSocket** — replace 3-second polling in kitchen/order tracking with Django Channels
- [ ] **Payment gateway integration** — add Stripe/PayPal/SSLCommerz for online payments
- [ ] **Docker production setup** — create Dockerfile and docker-compose.yml with Nginx + Gunicorn
- [ ] **SMS notifications** — order status updates via Twilio or similar
- [ ] **Email notifications** — order confirmation and invoice email delivery
- [ ] **Unit test expansion** — increase coverage beyond current user-model tests
- [ ] **CI/CD pipeline** — GitHub Actions for automated testing and deployment
- [ ] **Image optimization** — automatic thumbnail generation for food images
- [ ] **Export reports** — CSV/PDF export for revenue, orders, and loyalty reports
- [ ] **Multi-restaurant support** — tenant architecture for multiple restaurant branches
- [ ] **Mobile app** — React Native or Flutter companion app for customers
- [ ] **Inventory management** — stock tracking and low-stock alerts
- [ ] **Review and rating system** — customer feedback on products
