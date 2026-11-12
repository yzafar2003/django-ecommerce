# Django Shop

A small but complete e-commerce site built with Django 5.2. No JavaScript framework and no third party Django packages, just Django, SQLite and Pillow for product images.

## Features

- **Catalogue**: categories, product pages, search, pagination, product images.
- **Cart**: session based, works for guests, survives signing up or logging in. Prices always come from the database, never from the session.
- **Checkout**: guest or logged in. Stock is checked and decremented inside a transaction with row locks, so two people can't buy the last item at the same time. If something sold out in the meantime nothing is charged against stock and the cart is trimmed to what's left.
- **Orders**: confirmation page, confirmation email, order history for logged in users, customers can cancel pending orders (stock goes back).
- **Accounts**: sign up, log in, log out using Django's built in auth.
- **Admin**: manage products and stock inline, see orders with their items, bulk mark orders as paid / shipped.

Payment is not wired up. Orders are created as *Pending* and staff mark them paid from the admin. That's the place to plug in Stripe or similar.

## Quick start

Needs Python 3.10+.

```bash
git clone https://github.com/yzafar2003/django-ecommerce.git
cd django-ecommerce
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_store          # demo categories and products
python manage.py createsuperuser     # for /admin
python manage.py runserver
```

Open http://127.0.0.1:8000. The admin is at http://127.0.0.1:8000/admin/.

Order confirmation emails are printed to the terminal running `runserver`.

## Tests

```bash
python manage.py test
```

Covers browsing, the cart (stock caps, price changes, removed products), checkout (guest and logged in, sold out mid-checkout, price snapshot), order access rules, cancelling, and signup/login.

## Project layout

| App        | What's in it                                                        |
| ---------- | ------------------------------------------------------------------- |
| `store`    | `Category`, `Product`, listing / detail views, `seed_store` command |
| `cart`     | Session cart class, add / update / remove views                     |
| `orders`   | `Order`, `OrderItem`, checkout, history, cancel, admin actions      |
| `accounts` | Signup form and view (login/logout come from `django.contrib.auth`) |

Templates are in `templates/`, the stylesheet in `static/css/style.css`. It has a dark mode that follows the OS setting.

## Configuration

Settings read a few environment variables so the same code can run outside dev:

| Variable               | Default                          |
| ---------------------- | -------------------------------- |
| `DJANGO_SECRET_KEY`    | a dev-only placeholder, change it |
| `DJANGO_DEBUG`         | `1`                              |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1`            |
| `DJANGO_EMAIL_BACKEND` | console backend                  |

For production set a real secret key, `DJANGO_DEBUG=0`, your hostnames, run `python manage.py collectstatic`, and put it behind gunicorn/uvicorn with a proper database (Postgres works without code changes apart from `DATABASES`). Media uploads are only served by Django when `DEBUG` is on.
