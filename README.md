# Opportunity Finder (Findra)

Full-stack app for discovering opportunities, matching them to user profiles/preferences, and providing AI-assisted tools (CV extraction, cover letters, skill gap analysis).

## Repo Layout

- `opportunity_finder_frontend/` Next.js (React) web app
- `opportunity_finder_backend/` Django REST API + Celery workers
- `opportunity_finder_bot/` Telegram bot service (separate deployable)

## Main Features

- **Authentication & accounts**
  - Email/password registration + JWT login
  - Password reset flow
  - Session management (logout, logout-all)
  - Account deletion

- **Opportunities (public + dashboard)**
  - Public browse + detail pages
  - Authenticated dashboard browse + detail pages
  - Search/filter (remote/work mode/experience/status)

- **Profiles**
  - User profile with skills/interests/languages/academic info
  - CV text/file support

- **AI tools (premium-gated with daily limits for STANDARD)**
  - CV extraction sessions (upload, processing, review, apply to profile)
  - Cover letter generation + regeneration + editing
  - Skill gap analysis per opportunity
  - Centralized sanitization of AI provider errors (no raw quota/provider messages)

- **Matching**
  - Generates scored matches between users and opportunities
  - Match list/detail views in dashboard
  - Background matching tasks with anti-burst throttling

- **Preferences**
  - Matching threshold
  - Work preferences (mode/type/experience/compensation/deadlines)
  - Taxonomy-based preferences (types/domains/specializations/locations)
  - Notification preferences (frequency, quiet hours, max alerts/day)

- **Notifications**
  - Web dashboard notifications
  - Email notifications (Brevo integration)
  - Telegram notifications (Bot API)

- **Premium upgrade workflow**
  - Users submit upgrade requests with payment proof
  - Admin review approves/rejects and upgrades subscription

- **Admin**
  - Django admin enabled (`/admin/`)
  - Frontend admin area shell at `/admin` (role-gated)

## Core API Routes (Backend)

Base URL (local): `http://localhost:8000`

- **Auth**: `/api/auth/*`
- **Profile**: `/api/profile/me/`
- **Config/Preferences**: `/api/config/me/`
- **Opportunities**: `/api/opportunities/` and `/api/opportunities/<id>/`
- **Taxonomy**: `/api/opportunities/taxonomy/*`
- **Matches**: `/api/matches/`
- **Notifications**: `/api/notifications/`
- **CV Extraction**: `/api/cv-extraction/*`
- **Cover letters**: `/api/cover-letters/*`
- **Skill gap**: `/api/skill-gap-analysis/*`
- **Docs**: `/api/docs/` (Swagger UI)

## Running Locally (quick)

### Backend (Django)

1. Create and activate a venv
2. Install deps:

```bash
pip install -r opportunity_finder_backend/requirements.txt
```

3. Run migrations (from the backend folder):

```bash
python manage.py migrate
```

4. Start server:

```bash
python manage.py runserver
```

### Frontend (Next.js)

```bash
npm --prefix opportunity_finder_frontend install
npm --prefix opportunity_finder_frontend run dev
```

App runs on `http://localhost:3000`.

### Bot (Telegram)

See `opportunity_finder_bot/README.md`.

## Environment Notes

Backend config is read from `opportunity_finder_backend/.env` (not committed). Notable integrations:

- AI providers: Gemini / Groq / HuggingFace (via env settings)
- Email provider: Brevo
- Telegram: bot token + optional ingestion settings
