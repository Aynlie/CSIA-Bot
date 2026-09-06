# CSIA Bot (Cyberfox) — Handoff & Operations Guide

**Read this first if you're taking over Cyberfox from a previous officer.**
This document exists specifically because, as of AY 2026-2027, only one
person understood the full codebase, held the bot token, and knew how to
deploy it. That's a real risk for an org that turns over officers every
year — this file is the fix.

---

## 1. What Cyberfox does

- Reaction-role menus (Specialization, Pronouns, Year Level, Tools & Skills,
  What You Do, Linux Fundamentals Event) — `/postroles`
- Rules + verification gate — `/postrules`, `/postverification`
- Welcome-channel registration (name, email, Linux attendee / Member opt-in)
  — `/postwelcome`, granting Verified / Member / Linux Fundamentals Attendee
  as three **independent** roles (see Section 4)
- Event attendance tracking with auto-upgrade to Active Member —
  `/markattendance`, `/myevents`
- Profile/level card — `/profile`
- Officer tools for registration data — `/viewregistration`,
  `/editregistration`, `/exportregistrations`

## 2. Who has access right now

**Fill this in and keep it current — this table is the single most
important part of this document.**

| What | Who has it | Where it lives |
|---|---|---|
| Bot token | _______________ | Discord Developer Portal → CSIA app → Bot |
| GitHub repo access | _______________ | github.com/Aynlie/CSIA-Bot |
| Hosting login (Railway/Render, once set up) | _______________ | _______________ |
| Server Admin role | _______________ | Discord itself |

**When an officer with any of the above steps down, rotate that
credential to the incoming officer — don't just leave it as-is.**

## 3. Running the bot

### Locally (development/testing)
```bash
pip install -r Requirements.txt
cp .env.example .env   # then paste the real token into .env
python bot.py
```
This only stays online while the terminal is open — fine for testing,
**not fine for relying on during an actual event.**

### 24/7 hosting (what should actually be running in production)
As of this handoff, **the bot is NOT yet on 24/7 hosting** — this is the
single highest-priority gap flagged in the last review. To fix:

1. Create a free account at [railway.app](https://railway.app) or
   [render.com](https://render.com)
2. Connect it to the `github.com/Aynlie/CSIA-Bot` repo
3. In the host's dashboard (NOT in a committed file), set an environment
   variable: `DISCORD_BOT_TOKEN` = your real token
4. Deploy. The host will run `python bot.py` automatically on every push
   to the repo.
5. **Known limitation:** on some free hosting tiers, the filesystem resets
   on every redeploy — meaning `attendance.json` and `registrations.json`
   could be wiped. If this happens, the fix is swapping the storage layer
   (`attendance_store.py` / `registration_store.py`) for a real hosted
   database (e.g. a free Postgres instance) — the rest of the bot doesn't
   need to change, since those two files are the only place that touch
   storage directly.

## 4. Role architecture — read before changing anything

Three roles are **intentionally independent**, not a dependency chain:

- **Verified** — proved they read and agreed to the rules. Granted by
  either reacting ✅ in #rules-and-info OR completing the registration
  form (both call the same `grant_verified()` helper in
  `welcome_events.py` — don't add a third place that grants this role).
- **Member** — official CSIA member. Only granted if someone explicitly
  opts in on the registration form.
- **Linux Fundamentals Attendee** — event-only access, independent of
  membership. Someone can have this WITHOUT being a Member.
- **Active Member** — a separate earned tier, granted automatically by
  `/markattendance` once someone hits `ATTENDANCE_THRESHOLD` (currently 3)
  events. Requires the base Member role already exists conceptually, but
  isn't technically gated on it in code — worth being aware of.

**Do not merge these into one role** even if it seems simpler — the
whole point is that someone attending Linux Fundamentals as a guest
shouldn't be forced into CSIA's membership database.

## 5. Personal data this bot stores

`registrations.json` contains **real names and email addresses**.

- It is `.gitignore`d and should never be committed — verify this is
  still true (`git status` should never show this file as staged)
- It lives only on whichever machine/host is running the bot, in
  **plaintext, with no backup**. If that machine is lost or the file
  corrupts, this data is gone with no recovery path. Regular exports via
  `/exportregistrations` (restricted to `EXPORT_ROLE_IDS` in `config.py`)
  are the only current backup mechanism — someone should be doing this
  periodically and storing the CSV somewhere safer (e.g. a
  password-protected Google Drive folder), not just leaving it on the
  bot's host.
- Members are told, in the registration embed itself, what the data is
  used for and that only Officers can see it. If CSIA's actual data
  handling ever changes, update that notice text in
  `welcome_events.py` → `build_welcome_channel_embed()`.

## 6. Before you push any change

Run the test suite:
```bash
python -m pytest test_stores.py -v
```
This covers `attendance_store.py` and `registration_store.py` — the two
modules most likely to silently break in a way that loses data. It does
NOT cover `bot.py` itself (that requires a live Discord connection to
test meaningfully), so manual testing on a personal/test server is still
the right move for anything touching commands or the reaction handlers.

## 7. Config file map (where to change what)

Everything server-specific lives in `config.py` — IDs for roles,
channels, the guild itself, and all the text content for embeds (rules,
verification prompt, role menu descriptions). You should never need to
edit `bot.py` just to change wording or add a new role option — check
`config.py` first.

## 8. Questions this document doesn't answer

If you're stuck on something not covered here, the person who built this
(check the "Who has access" table above) is the best first contact. If
they're unreachable, the code itself is heavily commented — start with
`bot.py`'s module docstring at the top, then follow the imports.