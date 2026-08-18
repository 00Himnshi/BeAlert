# Assignment Alerts

A simple assignment tracker that checks your exam portal automatically and sends you a Twilio WhatsApp alert when it finds a new assignment.

## What each part does

| Folder | Purpose |
| --- | --- |
| `checker/` | Python program that logs in, checks assignments, saves them, and sends WhatsApp alerts. |
| `dashboard/` | React website that shows the assignments saved in the database. |
| `supabase/` | One SQL file used to create the database table. |
| `.github/workflows/` | GitHub Actions files. One checks assignments; the other publishes the website. |

## Your setup checklist

Follow these in order. Detailed instructions are below.

1. Create a Supabase project and run `supabase/database.sql`.
2. Create a Twilio account, phone number, and verified recipient phone number.
3. Put this project in a **public GitHub repository**.
4. Add the GitHub secrets listed below.
5. Turn on GitHub Pages.
6. Run the checker once manually, then wait for its automatic 15-minute checks.

## Step 1: Create the free Supabase database

1. Go to [Supabase](https://supabase.com/) and create a free project.
2. In the left menu choose **SQL Editor** → **New query**.
3. Open `supabase/database.sql` from this project. Replace `your-email@example.com` with the email address you will use for the dashboard, then copy everything and click **Run**.
4. Go to **Project Settings** → **API**. Keep these three values handy:
   - Project URL
   - `anon` public key
   - `service_role` secret key

The `anon` key is safe to use in the website. The `service_role` key is powerful: only place it in a GitHub secret, never in React code.

## Step 2: Prepare Twilio

In your Twilio Console, collect:

- Account SID
- Auth Token
- Your Twilio WhatsApp sender, for example `whatsapp:+14155238886`
- Your own WhatsApp recipient, for example `whatsapp:+919876543210`
- An approved Twilio WhatsApp Content Template SID (starts with `HX`)

For a Twilio trial account, join the WhatsApp Sandbox or use an approved WhatsApp sender before testing.

## Step 3: Create the GitHub repository

1. Create a new **public** GitHub repository named `assignment-alerts`.
2. Upload all files in this folder.
3. Do not upload any `.env` file with real passwords.

A public repository is intentional here: GitHub provides standard Actions runners free for public repositories. Your secrets remain private.

## Step 4: Add GitHub Secrets

In GitHub open **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Add:

| Secret name | What to paste |
| --- | --- |
| `PORTAL_USERNAME` | Your university portal username |
| `PORTAL_PASSWORD` | Your university portal password |
| `COURSE_URL` | Your course page URL, for example `http://e-exam.igdtuw.ac.in/exam/course/view.php?id=129` |
| `SUPABASE_URL` | Supabase Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase **Secret key** (`sb_secret_...`), or the older `service_role` key |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_FROM_NUMBER` | Your WhatsApp sender, such as `whatsapp:+14155238886` |
| `ALERT_TO_NUMBER` | Your WhatsApp recipient, such as `whatsapp:+919876543210` |
| `TWILIO_CONTENT_SID` | Your approved Twilio Content Template SID (starts with `HX`) |

### WhatsApp template setup

This project sends WhatsApp only. The two address secrets must include `whatsapp:`:

```text
TWILIO_FROM_NUMBER=whatsapp:+14155238886
ALERT_TO_NUMBER=whatsapp:+your-number-with-country-code
```

Set `TWILIO_CONTENT_SID` to your approved Twilio Content Template SID (it starts with `HX`). Your template must use two variables: `{{1}}` for assignment names and `{{2}}` for assignment links. If you are using the Twilio WhatsApp Sandbox, join the sandbox from your own WhatsApp account before testing.

Then add GitHub **Variables** (not secrets) with these names:

| Variable name | What to paste |
| --- | --- |
| `VITE_SUPABASE_URL` | Supabase Project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase `anon` public key |

## Step 5: Turn on the website

1. In GitHub, open the **Actions** tab and allow workflows if GitHub asks.
2. Open **Settings** → **Pages**.
3. Under **Build and deployment**, choose **GitHub Actions** as the source.
4. In **Actions**, run the `Publish dashboard` workflow once.
5. GitHub shows the website address in **Settings** → **Pages**.

The dashboard asks you to create a simple email/password login. Use the exact email you placed in `database.sql`, then confirm it through the email Supabase sends. This keeps the assignments private.

## Step 6: Test the automatic checker

1. In GitHub, open **Actions** → **Check portal for new assignments**.
2. Click **Run workflow** → **Run workflow**.
3. Open the completed run and read the final log lines.
4. The first successful run only saves current assignments. It does **not** send old assignments as new alerts.
5. After that, GitHub runs the checker about every 15 minutes. New assignments cause one Twilio WhatsApp alert.

## Run locally (optional)

### Checker

```powershell
cd checker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python check_assignments.py
```

Fill in your local `.env` file first. It is ignored by Git.

### Dashboard

```powershell
cd dashboard
npm install
Copy-Item .env.example .env.local
npm run dev
```

## If something goes wrong

- **Login failed:** confirm the portal URL and credentials. Some university portals may require extra login steps, which we can adapt after seeing the error log.
- **No WhatsApp alert:** check the Twilio WhatsApp sender, recipient, Content Template SID, and Sandbox/approved-sender setup.
- **Website says configuration is missing:** confirm the two GitHub Variables begin with `VITE_`.
- **Duplicate alert:** send the GitHub Actions log; the database unique ID is intended to prevent repeats.
