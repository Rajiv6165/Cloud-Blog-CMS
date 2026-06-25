# Django Blog CMS

A modern blog Content Management System built with Django and SQLite. Features post creation/editing, tagging, comments, Django admin, and authentication. Includes a polished responsive UI using Tailwind CDN + custom CSS/JS.

## Quickstart

- Requirements: Python 3.11+ (Windows), PowerShell

```bash
# 1) Create and activate venv (already created as .venv)
py -m venv .venv
.\.venv\Scripts\activate

# 2) Install dependencies
pip install "Django>=5,<6"

# 3) Run DB migrations
python manage.py migrate

# 4) Create superuser
python manage.py createsuperuser

# 5) Start dev server
python manage.py runserver
```

Open http://127.0.0.1:8000

Admin: http://127.0.0.1:8000/admin/

## Default admin (for local dev)

- Username: admin
- Password: ChangeMe123!

Change it immediately:

```bash
python manage.py changepassword admin
```

## Apps and Features

- Blog
  - Models: Post, Tag, Comment
  - CRUD for posts (create/edit/delete)
  - Tag pages and filters
  - Search across title/summary/content
  - Comments with basic moderation
- Auth
  - Login/Logout via Django auth URLs
  - Permissions: only authors/staff can edit/delete their posts
- Admin
  - Customized admin for posts/tags/comments

## Frontend

- Tailwind CSS via CDN in `templates/base.html`
- Custom CSS/JS in `static/css/app.css` and `static/js/app.js`
- Responsive layout, accessible components

## Project Structure

- `cms/` project config and settings
- `blog/` app code: models, views, urls, admin, forms
- `templates/` HTML templates (base + blog + auth)
- `static/` static assets
- `media/` user-uploaded files (if added later)

## Notes

- DEBUG is on for development. Set `DEBUG=False` and configure `ALLOWED_HOSTS` for production.
- Static files are served by Django in dev. In production, use a proper static files server.
