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

## Background Jobs (Celery vs Cron)

This project supports running background work either:

- **Via Celery workers + Celery Beat** (recommended if you have Redis and workers running), or
- **Via external cron** (e.g., Supabase scheduled jobs) calling the backend cron endpoints.

### Option A: Celery/Beat

Configured in `opportunity_finder_backend/opportunity_finder/settings.py`:

- `CELERY_ENABLED` (env `CELERY_ENABLED=true|false`) controls whether code paths enqueue tasks (`.delay()`) or run inline.
- Beat toggles/intervals (env):
  - `PROCESSING_BEAT_ENABLED`, `PROCESSING_BEAT_INTERVAL_SECONDS`, `PROCESSING_PENDING_LIMIT`
  - `MATCHING_BEAT_ENABLED`, `MATCHING_BEAT_INTERVAL_SECONDS`, `MATCHING_BATCH_SIZE`
  - `NOTIFICATIONS_BEAT_ENABLED`, `NOTIFICATIONS_BEAT_INTERVAL_SECONDS`, `NOTIFICATIONS_PROCESS_LIMIT`

### Option B: External Cron (Supabase)

The backend exposes secured cron endpoints under `/api/cron/*` (see `opportunity_finder_backend/opportunity_finder/cron_urls.py`).

All cron endpoints require:

- Header: `X-Cron-Secret: <CRON_SECRET>`
- Env: `CRON_SECRET=<your secret>`

Endpoints:

- `POST /api/cron/ingest-due/?limit=20&source_type=rss|telegram`
  - Ingest due sources using the ingestion runner.
- `POST /api/cron/process-raw/?limit=10`
  - Processes pending raw items (internally uses `processing.tasks.process_pending_raw`; when `CELERY_ENABLED=false` it runs inline).
- `POST /api/cron/match/?hours_back=24&opportunity_limit=1&user_limit=1`
  - Runs matching in a controlled manner (uses a DB advisory lock to avoid concurrent runs).
- `POST /api/cron/notifications/?limit=50`
  - Sends pending notifications (email/telegram/dashboard).

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
