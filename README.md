# TomoShiriki

**TomoShiriki** is a community-driven framework for sharing physical and virtual resources. Built with Django, it provides a modular, extensible platform where individuals and communities can manage, lend, and borrow resources.

## Features

- **Community Management** — Create and manage communities with flexible membership.
- **Flexible Resource Ownership** — Resources can belong to individual users or to a community.
- **Booking System** — Built-in booking lifecycle with status tracking (Pending, Approved, Rejected, Completed, Cancelled).
- **Admin Interface** — Full Django Admin panel for managing all entities out of the box.
- **Plugin-Ready Architecture** — Designed from the ground up to support extensions via Django Apps.

## Tech Stack

| Layer       | Technology          |
|-------------|---------------------|
| Framework   | Django 6.0          |
| Language    | Python 3.14         |
| Database    | SQLite (dev) / PostgreSQL (prod) |
| ORM         | Django ORM          |

## Getting Started

### Prerequisites

- Python 3.14+

### Installation

```bash
# Clone the repository
git clone https://github.com/TerryGolo/TomoShiriki.git
cd TomoShiriki

# Create and activate a virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create a superuser for the admin panel
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

### Usage

Once the server is running, navigate to:

- **Admin Panel:** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

From the admin panel you can create Communities, Users, Resources, and Bookings.

## Project Structure

```
TomoShiriki/
├── core/                   # Core application (models, admin, views)
│   ├── models.py           # Domain models (User, Community, Resource, Booking)
│   ├── admin.py            # Admin panel registration
│   └── migrations/         # Database migrations
├── tomoshiriki/            # Django project configuration
│   ├── settings.py         # Project settings
│   ├── urls.py             # URL routing
│   └── wsgi.py             # WSGI entry point
├── docs/
│   └── journal/            # Development session journals
├── manage.py               # Django management script
└── requirements.txt        # Python dependencies
```

## Domain Model

```
User ──┬── owns ──▶ Resource ◀── owns ──┬── Community
       │                                 │
       └── member of ───────────────────▶│
       │                                 │
       └── borrows (Booking) ──▶ Resource
```

- **Users** can exist independently of any community.
- **Resources** must be owned by exactly one user **or** one community.
- **Bookings** track the lifecycle of a resource being borrowed.

## License

TBD
