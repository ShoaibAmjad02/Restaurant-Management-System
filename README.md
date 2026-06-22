**Restaurant Management and Online Food Ordering System**

The Restaurant Management and Online Food Ordering System is a comprehensive full-stack web application designed to automate and streamline restaurant operations while providing customers with a convenient online food ordering experience. The system is developed using Django as the backend framework, MySQL as the database management system, and HTML, CSS, Bootstrap, and JavaScript for creating an interactive and responsive user interface.

The platform combines multiple restaurant functions into a single integrated solution, including customer ordering, restaurant operations management, kitchen workflow monitoring, and administrative control. Customers can create accounts, securely log in, browse food categories and menu items, add products to their cart, place online orders, generate invoices, and track the real-time status of their orders. This improves customer convenience and enhances overall satisfaction by providing transparency throughout the ordering process.

Restaurant operators can efficiently manage both online and walk-in customer orders through a dedicated dashboard. The system allows operators to create orders, search invoices, view order history, generate bills, and print receipts, reducing manual work and improving service speed. The integrated billing and invoice management features ensure accurate transaction records and facilitate smooth daily operations.

A specialized kitchen management module enables kitchen staff to monitor incoming orders and update their progress through different stages, such as Pending, Preparing, and Delivered. This real-time communication between operators and kitchen staff minimizes delays, improves coordination, and ensures timely order fulfillment.

The administrative panel provides centralized control over the entire system. Administrators can manage menu categories and food items, create and manage operator and kitchen user accounts, monitor orders, track revenue and sales performance, search invoices, and generate detailed reports. Additionally, the system includes a database backup feature that allows administrators to download MySQL backup files, ensuring data security and easy recovery when required.

By integrating customer services, operational management, kitchen coordination, and administrative monitoring into a unified platform, the Restaurant Management and Online Food Ordering System significantly improves efficiency, reduces operational complexity, enhances customer experience, and supports the digital transformation of modern restaurant businesses.

---

## Deployment on Railway

### Prerequisites

1. A [Railway](https://railway.app/) account
2. Railway CLI installed (optional, for local management)

### Step 1: Create Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **New Project**
3. Select **Deploy from GitHub Repo** (or paste your repo URL)

### Step 2: Add MySQL Database

1. In your Railway project, click **New**
2. Select **Database** > **MySQL**
3. Railway will provision a MySQL database automatically
4. Note the environment variables provided:
   - `MYSQLHOST`
   - `MYSQLPORT`
   - `MYSQLUSER`
   - `MYSQLPASSWORD`
   - `MYSQLDATABASE`

### Step 3: Set Environment Variables

In the Railway dashboard, go to your web service **Variables** tab and add:

| Variable | Value | Description |
|----------|-------|-------------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` | Use production settings |
| `DJANGO_SECRET_KEY` | (generate a random key) | Django secret key |
| `DJANGO_ALLOWED_HOSTS` | `*` | Allow all hosts (or specify your domain) |
| `DJANGO_DEBUG` | `False` | Disable debug mode |

> **Note:** Railway automatically provides `MYSQLDATABASE`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLHOST`, and `MYSQLPORT` when you add a MySQL database plugin. These are used automatically by the application.

### Step 4: Deploy

Railway will automatically:
1. Install dependencies from `requirements.txt`
2. Run the `start.sh` script which:
   - Waits for database connection
   - Runs migrations
   - Collects static files
   - Starts Gunicorn

### Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DJANGO_SETTINGS_MODULE` | Yes | Set to `config.settings.production` |
| `DJANGO_SECRET_KEY` | Yes | Random secret key for Django |
| `DJANGO_ALLOWED_HOSTS` | Yes | Your Railway domain or `*` |
| `DJANGO_DEBUG` | No | Default: `False` |
| `MYSQLDATABASE` | Auto | Provided by Railway MySQL plugin |
| `MYSQLUSER` | Auto | Provided by Railway MySQL plugin |
| `MYSQLPASSWORD` | Auto | Provided by Railway MySQL plugin |
| `MYSQLHOST` | Auto | Provided by Railway MySQL plugin |
| `MYSQLPORT` | Auto | Provided by Railway MySQL plugin |
| `REDIS_URL` | No | Railway Redis plugin URL (optional) |

### Railway Build & Start Commands

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `bash start.sh`

### Database Setup

#### Import Existing Database Backup

If you have an existing `database_backup.sql` file:

1. Connect to your Railway MySQL database:
   ```bash
   mysql -h MYSQLHOST -P MYSQLPORT -u MYSQLUSER -p MYSQLDATABASE < "database_backup (1).sql"
   ```

2. Or use Railway CLI:
   ```bash
   railway connect mysql
   mysql> source /path/to/database_backup.sql
   ```

#### Run Migrations

Migrations run automatically on deployment via `start.sh`. To run manually:

```bash
railway run python manage.py migrate --noinput
```

#### Create Superuser

```bash
railway run python manage.py createsuperuser
```

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

### Project Structure

```
restaurant-management-system/
├── config/                 # Django project configuration
│   ├── settings/
│   │   ├── base.py        # Base settings
│   │   ├── production.py  # Production settings (Railway)
│   │   └── local.py       # Local development settings
│   ├── urls.py
│   └── wsgi.py
├── megaone/               # Main application directory
│   ├── apps/
│   │   └── food_delivery/
│   ├── users/             # User management, auth, admin
│   ├── static/            # Static files
│   ├── media/             # Media uploads
│   └── templates/         # HTML templates
├── menu/                  # Menu app
├── orders/                # Orders app
├── requirements.txt       # Python dependencies
├── railway.json           # Railway deployment config
├── Procfile               # Process file
├── start.sh               # Startup script
├── gunicorn.conf.py       # Gunicorn configuration
└── database_backup.sql    # Database backup (if available)
```
