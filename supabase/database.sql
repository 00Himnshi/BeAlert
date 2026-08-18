-- Run this entire file in Supabase: SQL Editor -> New query -> Run.

create table if not exists public.assignments (
  id uuid primary key default gen_random_uuid(),
  portal_id text not null unique,
  title text not null,
  assignment_url text not null,
  course_url text not null,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now()
);

-- Before running this file, replace your-email@example.com below with the
-- email address you will use to sign in to the dashboard.
-- The React website can read assignments only after that exact user signs in.
alter table public.assignments enable row level security;

create policy "Only the owner can read assignments"
on public.assignments
for select
to authenticated
using (lower(auth.jwt() ->> 'email') = 'your-email@example.com');

-- A policy says *who* is allowed; this grant lets signed-in users use SELECT
-- at all. The policy above still limits the rows to your email address.
grant select on public.assignments to authenticated;

-- The GitHub checker acts as Supabase's server role. It needs permission to
-- read existing rows and insert/update the rows it finds.
grant select, insert, update on public.assignments to service_role;

-- The GitHub Action uses the private service-role key, so it can add and update rows.
-- There is deliberately no public insert, update, or delete policy.
