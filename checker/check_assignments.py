"""Check one course page and text you when a new assignment appears.

This file is run by GitHub Actions. All passwords and API keys come from
environment variables, never from this source code.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

# The university portal currently serves this login page over HTTP.
# This is less secure than HTTPS; see the README before using cloud automation.
LOGIN_URL = "http://e-exam.igdtuw.ac.in/exam/login/index.php"


@dataclass
class Assignment:
    """The small amount of information we need about an assignment."""

    portal_id: str
    title: str
    assignment_url: str


def required_setting(name: str) -> str:
    """Stop early with a clear message if a required setting is missing."""
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required setting: {name}")
    return value


def make_portal_id(assignment_url: str) -> str:
    """Use Moodle's activity id when present; otherwise create a stable ID."""
    query = parse_qs(urlparse(assignment_url).query)
    if "id" in query:
        return f"moodle-{query['id'][0]}"
    return hashlib.sha256(assignment_url.encode("utf-8")).hexdigest()


def log_in(session: requests.Session) -> None:
    """Log in, including any hidden form fields Moodle requires."""
    username = required_setting("PORTAL_USERNAME")
    password = required_setting("PORTAL_PASSWORD")

    login_page = session.get(LOGIN_URL, timeout=30)
    login_page.raise_for_status()
    soup = BeautifulSoup(login_page.text, "html.parser")

    # Moodle may add hidden security fields. Sending them back makes this work
    # on more Moodle configurations than username/password alone.
    form_values = {
        field.get("name"): field.get("value", "")
        for field in soup.select("form input[type='hidden'][name]")
    }
    form_values["username"] = username
    form_values["password"] = password

    response = session.post(LOGIN_URL, data=form_values, timeout=30)
    response.raise_for_status()

    # A login page after submitting credentials normally means login failed.
    if "login/index.php" in response.url:
        raise RuntimeError("Portal login failed. Check PORTAL_USERNAME and PORTAL_PASSWORD.")


def find_assignments(session: requests.Session, course_url: str) -> list[Assignment]:
    """Read assignment-looking activities from the course page."""
    response = session.get(course_url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    assignments: list[Assignment] = []
    for activity in soup.select("li.activity a[href]"):
        title = activity.get_text(" ", strip=True)
        url = activity["href"]
        is_assignment = "assignment" in title.lower() or "lab exercise" in title.lower()
        if title and is_assignment:
            assignments.append(Assignment(make_portal_id(url), title, url))

    return assignments


def supabase_headers() -> dict[str, str]:
    """Return headers for both current and older Supabase server keys."""
    key = required_setting("SUPABASE_SERVICE_ROLE_KEY")
    headers = {"apikey": key, "Content-Type": "application/json"}

    # New Supabase secret keys begin with sb_secret_. They must only be sent
    # as the apikey header. Older service_role keys are JWTs and also need the
    # Authorization header to bypass Row Level Security.
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {key}"
    return headers


def existing_portal_ids() -> set[str]:
    """Ask Supabase which assignments are already known."""
    database_url = required_setting("SUPABASE_URL").rstrip("/")
    response = requests.get(
        f"{database_url}/rest/v1/assignments?select=portal_id",
        headers=supabase_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return {row["portal_id"] for row in response.json()}


def save_assignments(assignments: list[Assignment], course_url: str) -> None:
    """Insert new assignments and update the last-seen time for existing ones."""
    if not assignments:
        return

    database_url = required_setting("SUPABASE_URL").rstrip("/")
    rows = [
        {
            "portal_id": assignment.portal_id,
            "title": assignment.title,
            "assignment_url": assignment.assignment_url,
            "course_url": course_url,
            "last_seen_at": datetime.now(timezone.utc).isoformat(),
        }
        for assignment in assignments
    ]
    response = requests.post(
        f"{database_url}/rest/v1/assignments?on_conflict=portal_id",
        headers={**supabase_headers(), "Prefer": "resolution=merge-duplicates"},
        json=rows,
        timeout=30,
    )
    response.raise_for_status()


def send_whatsapp_message(new_assignments: list[Assignment]) -> None:
    """Send one approved WhatsApp template message for new assignments."""
    if not new_assignments:
        return

    client = Client(required_setting("TWILIO_ACCOUNT_SID"), required_setting("TWILIO_AUTH_TOKEN"))
    from_address = required_setting("TWILIO_FROM_NUMBER")
    to_address = required_setting("ALERT_TO_NUMBER")
    content_sid = required_setting("TWILIO_CONTENT_SID")

    if not from_address.startswith("whatsapp:") or not to_address.startswith("whatsapp:"):
        raise RuntimeError("WhatsApp addresses must begin with whatsapp:+, for example whatsapp:+14155238886")

    # WhatsApp starts new conversations with an approved Twilio template.
    # In your template, {{1}} becomes assignment names and {{2}} becomes
    # their links. Create the template wording to match those values.
    client.messages.create(
        from_=from_address,
        to=to_address,
        content_sid=content_sid,
        content_variables=json.dumps(
            {
                "1": "\n".join(item.title for item in new_assignments),
                "2": "\n".join(item.assignment_url for item in new_assignments),
            }
        ),
    )


def main() -> None:
    course_url = required_setting("COURSE_URL")
    session = requests.Session()
    session.headers["User-Agent"] = "AssignmentAlerts/1.0 (personal academic notifier)"

    log_in(session)
    found_assignments = find_assignments(session, course_url)
    known_ids = existing_portal_ids()
    new_assignments = [item for item in found_assignments if item.portal_id not in known_ids]

    # The first run is a baseline. It saves existing work without treating the
    # whole course history as an urgent new WhatsApp notification.
    is_first_run = not known_ids
    save_assignments(found_assignments, course_url)

    if is_first_run:
        print(f"Baseline saved: {len(found_assignments)} assignment(s). No WhatsApp alert sent.")
    elif new_assignments:
        send_whatsapp_message(new_assignments)
        print(f"Sent one WhatsApp alert for {len(new_assignments)} new assignment(s).")
    else:
        print("No new assignments found.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Checker failed: {error}", file=sys.stderr)
        raise
