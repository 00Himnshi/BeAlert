# Assignment Alerts

Assignment Alerts is a personal automation that watches a  university course website and sends a WhatsApp notification when a new assignment appears. It also keeps a private dashboard of everything it has found.

I built it to solve a practical problem: Manually checking the portal required repeatedly logging in, navigating through multiple pages, and remembering to check for updates—creating a simple but real risk of missing newly posted assignments or deadlines. The project turns that repeated manual check into a scheduled background job.

## What it does

1. GitHub Actions runs the checker every eight hours (and it can also be run manually).
2. The Python checker signs in to the course portal and looks for assignment activities.
3. It compares the current results with the assignments already stored in Supabase.
4. When it detects something new, it sends a single WhatsApp message through Twilio.
5. A React dashboard lets the owner sign in and review the saved assignments.

## Architecture

```text
GitHub Actions (every 8 hours)
            |
            v
Python checker ---> University Moodle portal
      |                    |
      |                    v
      +--> Supabase <--- React dashboard (GitHub Pages)
      |
      +--> Twilio WhatsApp alert (new assignments only)
```

## Project structure

| Path | Responsibility |
| --- | --- |
| `checker/check_assignments.py` | Logs in, finds assignments, detects changes, saves data, and sends alerts. |
| `dashboard/` | Vite + React dashboard for viewing assignments after signing in. |
| `supabase/database.sql` | Database table and Row Level Security policy. |
| `.github/workflows/check-assignments.yml` | Runs the checker on its eight-hour schedule. |
| `.github/workflows/publish-dashboard.yml` | Builds and publishes the dashboard to GitHub Pages. |

## Design decisions worth discussing

- **Stable duplicate detection:** Moodle activity IDs are used where available. If an ID is absent, a SHA-256 hash of the URL becomes the identifier. Supabase enforces uniqueness on that ID, so the same assignment is not alerted repeatedly.
- **One alert per run:** If several assignments appear between checks, the checker groups them into one WhatsApp message instead of sending several messages.
- **Safe first run:** The initial run stores current assignments as a baseline, preventing historical work from being reported as new.
- **Retry-friendly ordering:** A newly detected assignment is stored only after Twilio accepts the alert. If delivery fails, it remains unsaved and the next scheduled run can try again.
- **Secrets stay out of the repository:** Portal credentials, database server key, and Twilio credentials live in GitHub Actions secrets. The public dashboard receives only Supabase's publishable `anon` key.
- **Private dashboard:** Supabase Row Level Security limits reads to the email address configured in the SQL file. The browser cannot write assignments.

## Stack

- Python, Requests, Beautiful Soup, and Twilio
- Supabase (Postgres + authentication + Row Level Security)
- React, Vite, and GitHub Pages
- GitHub Actions for scheduling and deployment

## Setup

### 1. Create the database

1. Create a Supabase project.
2. In the SQL Editor, open and run `supabase/database.sql`.
3. Before running it, replace `your-email@example.com` with the email that will use the dashboard.
4. From **Project Settings → API**, copy the Project URL, the `anon` key, and the server-side secret/service-role key.

### 2. Configure Twilio WhatsApp

Create or use an approved WhatsApp sender and an approved Content Template. The template needs two variables: `{{1}}` for assignment names and `{{2}}` for their links. Trial accounts must use the Twilio WhatsApp Sandbox or another approved configuration.

### 3. Add GitHub Actions secrets

In the repository, open **Settings → Secrets and variables → Actions** and add these repository secrets:

| Secret | Value |
| --- | --- |
| `PORTAL_USERNAME` | University portal username |
| `PORTAL_PASSWORD` | University portal password |
| `COURSE_URL` | Course page URL |
| `SUPABASE_URL` | Supabase Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase secret key (`sb_secret_...`) or older service-role key |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_FROM_NUMBER` | Sender, for example `whatsapp:+1246543e734` |
| `ALERT_TO_NUMBER` | Recipient, for example `whatsapp:+0987dwe5543` |
| `TWILIO_CONTENT_SID` | Approved WhatsApp template SID  |

Also add these GitHub **Variables** for the dashboard build:

| Variable | Value |
| --- | --- |
| `VITE_SUPABASE_URL` | Supabase Project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase `anon` key |

### 4. Publish and test

1. Enable GitHub Pages with **GitHub Actions** as its source.
2. Run the **Publish dashboard** workflow once.
3. Run **Check portal for new assignments** manually once to establish the baseline.
4. After that, GitHub Actions checks automatically every eight hours.

## Run locally

### Checker

```powershell
cd checker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python check_assignments.py
```
### Dashboard

```powershell
cd dashboard
npm install
Copy-Item .env.example .env.local
npm run dev
```

## Known limitations

- The parser is intentionally tailored to the current Moodle page structure. A portal redesign may require updating its selectors.
- This version watches one course URL. Supporting many courses would mean storing course configuration and checking each course in the same run.
