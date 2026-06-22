**Restaurant Management and Online Food Ordering System**

The Restaurant Management and Online Food Ordering System is a comprehensive full-stack web application designed to automate and streamline restaurant operations while providing customers with a convenient online food ordering experience. The system is developed using Django as the backend framework, MySQL as the database management system, and HTML, CSS, Bootstrap, and JavaScript for creating an interactive and responsive user interface.

The platform combines multiple restaurant functions into a single integrated solution, including customer ordering, restaurant operations management, kitchen workflow monitoring, and administrative control. Customers can create accounts, securely log in, browse food categories and menu items, add products to their cart, place online orders, generate invoices, and track the real-time status of their orders. This improves customer convenience and enhances overall satisfaction by providing transparency throughout the ordering process.

Restaurant operators can efficiently manage both online and walk-in customer orders through a dedicated dashboard. The system allows operators to create orders, search invoices, view order history, generate bills, and print receipts, reducing manual work and improving service speed. The integrated billing and invoice management features ensure accurate transaction records and facilitate smooth daily operations.

A specialized kitchen management module enables kitchen staff to monitor incoming orders and update their progress through different stages, such as Pending, Preparing, and Delivered. This real-time communication between operators and kitchen staff minimizes delays, improves coordination, and ensures timely order fulfillment.

The administrative panel provides centralized control over the entire system. Administrators can manage menu categories and food items, create and manage operator and kitchen user accounts, monitor orders, track revenue and sales performance, search invoices, and generate detailed reports. Additionally, the system includes a database backup feature that allows administrators to download MySQL backup files, ensuring data security and easy recovery when required.

By integrating customer services, operational management, kitchen coordination, and administrative monitoring into a unified platform, the Restaurant Management and Online Food Ordering System significantly improves efficiency, reduces operational complexity, enhances customer experience, and supports the digital transformation of modern restaurant businesses.

---

## Deployment on Render (Free Plan)

### Prerequisites

1. A [Render](https://render.com/) account
2. A [FreeSQLDatabase](https://freesqldatabase.com/) account (or any external MySQL provider)

### Step 1: Set Up MySQL Database

1. Create a free database at [FreeSQLDatabase](https://freesqldatabase.com/)
2. Note down the following details:
   - **Host** (e.g., `sql12.freesqldatabase.com`)
   - **Port** (usually `3306`)
   - **Database name** (e.g., `sql1234567`)
   - **Username** (e.g., `sql1234567`)
   - **Password**

### Step 2: Push to GitHub

```bash
git add .
git commit -m "Configure for Render deployment"
git push origin main
```

### Step 3: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** > **Web Service**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `restaurant-management-system`
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120`

### Step 4: Set Environment Variables

In the Render dashboard, go to **Environment** tab and add:

| Variable | Value | Description |
|----------|-------|-------------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` | Use production settings |
| `DJANGO_SECRET_KEY` | (generate a random key) | Django secret key |
| `DJANGO_ALLOWED_HOSTS` | `.onrender.com` | Your Render domain |
| `DJANGO_DEBUG` | `False` | Disable debug mode |
| `DB_NAME` | `sql1234567` | MySQL database name |
| `DB_USER` | `sql1234567` | MySQL username |
| `DB_PASSWORD` | (your database password) | MySQL password |
| `DB_HOST` | `sql12.freesqldatabase.com` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_ENGINE` | `django.db.backends.mysql` | Database engine |

### Step 5: Deploy

Click **Create Web Service**. Render will:
1. Install dependencies from `requirements.txt`
2. Run `build.sh` (migrations + collectstatic)
3. Start the application with gunicorn

### Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DJANGO_SETTINGS_MODULE` | Yes | Set to `config.settings.production` |
| `DJANGO_SECRET_KEY` | Yes | Random secret key for Django |
| `DJANGO_ALLOWED_HOSTS` | Yes | Your Render domain (e.g., `.onrender.com`) |
| `DB_NAME` | Yes | MySQL database name |
| `DB_USER` | Yes | MySQL username |
| `DB_PASSWORD` | Yes | MySQL password |
| `DB_HOST` | Yes | MySQL host address |
| `DB_PORT` | Yes | MySQL port (default: 3306) |
| `DB_ENGINE` | No | Default: `django.db.backends.mysql` |
| `REDIS_URL` | No | Redis URL for caching (optional) |
| `DJANGO_SECURE_SSL_REDIRECT` | No | Default: `True` |
| `DJANGO_EMAIL_BACKEND` | No | Default: console backend |

### Render Build & Start Commands

- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120`

### Features Included

- User authentication (registration, login, logout)
- QR code generation for tables and invoices
- Invoice PDF generation (thermal receipt format)
- Kitchen dashboard with real-time order management
- AJAX-based order tracking
- Admin dashboard with revenue analytics
- Database backup support
- Static file serving via WhiteNoise
- Media file storage (local filesystem)
