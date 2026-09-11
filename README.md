# Sahyog — Cooperative Service Network MVP

A Django MVP for a cooperative-owned marketplace connecting customers with verified local workers.

# Sahyog — Cooperative Service Network MVP

A Django MVP for a cooperative-owned marketplace connecting customers with verified local workers.

## Included
- Customer + worker accounts, plus optional "Continue with Google" login
- Worker profile, services and availability
- Cooperative verification workflow
- Location-aware matching with Haversine fallback + Leaflet/OpenStreetMap map (no API key)
- Emergency booking flag
- Booking lifecycle: pending → accepted → on the way → arrived → in progress → completed
- 60-second worker accept/reject window, tracked in the database (not just JavaScript) and auto-expired on dashboard load
- Cash and UPI/Online payment, both feeding the same invoice + cooperative verification flow
- Cooperative payment verification ledger
- Invoice generation with configurable platform fee
- Ratings and worker rating aggregation
- Worker welfare preferences
- Cooperative control center
- Explainable demand forecasting baseline
- Responsive Bootstrap UI + role-aware side drawer with dark/light theme toggle
- English + Hindi + Bengali UI with a visible language switcher (Django i18n)

## Tech stack
- Django, Python
- Database: SQLite by default; Oracle 21c supported (see below)
- Leaflet + OpenStreetMap tiles for maps (no Mapbox, no Google Maps key required)
- Optional Google OAuth2 login (falls back to username/password if not configured)

## Run locally
```bash
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Database: SQLite (default) or Oracle 21c
By default the app uses SQLite — nothing to configure. To use Oracle 21c instead, set:
```
DJANGO_DB_ENGINE=oracle
ORACLE_DSN=localhost:1521/ORCLPDB
ORACLE_USER=your_oracle_user
ORACLE_PASSWORD=your_oracle_password
```
`oracledb` is already in `requirements.txt`. If `DJANGO_DB_ENGINE` is unset or anything other than `oracle`, SQLite is used automatically — the app never fails to start for a missing Oracle connection.

## Environment variables
Copy `.env.example` to `.env` and set keys as needed. Everything below is optional — the app runs with sensible defaults if unset.

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` | Standard Django settings |
| `DJANGO_DB_ENGINE`, `ORACLE_DSN`, `ORACLE_USER`, `ORACLE_PASSWORD` | Database (see above) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI` | Google login (see below) |
| `PLATFORM_FEE_PERCENT` | Cooperative platform fee used in invoices |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` | Legacy Razorpay fields, unused by the current UPI/cash flow |

## Google OAuth setup
1. In Google Cloud Console, create an OAuth 2.0 Client ID (Web application).
2. Add an authorized redirect URI: `http://127.0.0.1:8000/accounts/google/callback/` (adjust host for production).
3. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`.
4. If these are not set, the "Continue with Google" button is hidden and username/password login works exactly as before — the app never crashes because of missing OAuth credentials.

## Map / OpenStreetMap
No setup required — the app loads Leaflet from a public CDN and OpenStreetMap tiles directly. If the browser denies location permission, the map/nearby-workers view simply doesn't appear; the rest of the site (manual address entry, search, booking) keeps working.

## Cooperative dashboard
Create a superuser and open `/dashboard/cooperative/`.

## Payment flow
Customer chooses **Cash** or **Online/UPI** after job completion:
- **UPI**: customer scans the QR code, submits a transaction ID (+ optional screenshot), and a cooperative administrator manually verifies it.
- **Cash**: customer confirms cash was paid directly to the worker; a cooperative administrator marks it collected in the same verification queue.
No automatic bank/UPI verification is claimed in either case.

## Language switcher
Use the dropdown in the top navigation bar (or the hamburger menu) to switch between English, हिन्दी and বাংলা. Translations live in `locale/<lang>/LC_MESSAGES/django.po`. After editing translatable strings, regenerate and compile catalogs:
```bash
python manage.py makemessages -l hi -l bn
python manage.py compilemessages
```
**Note:** the Bengali `.po` file included in this build has not been compiled to `.mo` yet (no `gettext`/network access in the build environment) — run `compilemessages` locally before Bengali strings will actually render.

## Dark / light theme
Toggle in the hamburger menu. Preference is stored in the browser's `localStorage` (no database changes needed) and applied instantly on page load to avoid a flash of the wrong theme.

## Demo data
```bash
python manage.py seed_demo
```
Creates 3 verified demo workers (electrician, plumber, carpenter), a demo customer and a cooperative admin superuser. It is safe to re-run; it will not duplicate or destroy existing data.

## Superuser / cooperative admin access
Any user with `is_staff=True` can access `/dashboard/cooperative/`. Create one with:
```bash
python manage.py createsuperuser
```

## Hackathon demo flow
1. **Customer**: login → dashboard → tap a service category (or search) → allow location → see nearby verified workers on the map, sorted by distance/rating → book a worker.
2. **Worker**: sees the new request with a live 60-second countdown → Accept.
3. **Customer**: sees status flip to Accepted, distance/ETA shown.
4. **Worker**: On the Way → Arrived → Start → Complete.
5. **Customer**: choose Cash or Online, pay, view invoice, leave a rating.
6. **Admin**: verify the worker (if not already verified) and verify the payment from `/dashboard/cooperative/`.
7. Also show: Google login, English/Hindi/Bengali switch, dark/light toggle, emergency booking (the lightning-bolt button next to "Book").

## Notes on location permissions
If a customer or worker denies browser location permission, the "Use my location" buttons simply show an alert and the rest of the flow (manual address entry, browsing, booking) continues to work — the site never becomes unusable because of a denied permission.

## Verifying this build
This build was produced without network/Django access in the build sandbox. Before relying on it, run:
```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate --plan
python manage.py compilemessages
```
```bash
python manage.py seed_demo
```
Creates 3 verified demo workers (electrician, plumber, carpenter), a demo customer and a cooperative admin superuser. It is safe to re-run; it will not duplicate or destroy existing data.

## Superuser / cooperative admin access
Any user with `is_staff=True` can access `/dashboard/cooperative/`. Create one with:
```bash
python manage.py createsuperuser
```
