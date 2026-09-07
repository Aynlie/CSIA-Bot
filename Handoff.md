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
- Rules + verification gate — `/postrules` (posts both the rules embed and
  the verification embed together; there is no separate command anymore —
  see Section 4 for why)
- Welcome-channel registration (name, email, Linux attendee opt-in)
  — `/postwelcome`, granting Verified / Linux Fundamentals Attendee as
  independent roles (see Section 4)
- CSIA Membership verification — `/verifymember` (see Section 4)
- Event attendance tracking with auto-upgrade to Active Member —
  `/markattendance`, `/myevents`
- Profile/level card — `/profile`
- Native support tickets — `/postticketpanel`, `/closeticket` (see
  Section 5 — replaces Carl-bot)
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
  either reacting ✅ on the verification message in #rules-and-info OR
  completing the Verify & Register form (both call the same
  `grant_verified()` helper in `welcome_events.py` — don't add a third
  place that grants this role).
- **Linux Fundamentals Attendee** — event-only access, independent of
  membership. Someone can have this WITHOUT being a Member. Granted by
  the Verify & Register form when someone answers "Yes" to attending.
- **Member** — official CSIA member. **Not granted automatically by the
  bot's own form anymore.** The flow is now:
  1. Someone completes the Verify & Register form in Discord (name,
     email, Linux attendee status only — no membership question).
  2. The bot automatically posts a notification embed of that submission
     to the channel configured as `REGISTRATION_LOG_CHANNEL_ID`.
  3. An officer cross-checks the submission against CSIA's official
     membership Google Form (`config.MEMBERSHIP_FORM_URL`) or member
     database to confirm the person actually registered as a member
     there.
  4. The officer runs `/verifymember @person`, answering the "Are they a
     Member?" Yes/No prompt. **Yes** grants the Member role and posts a
     welcome message in #announcements. **No** just logs that they were
     checked and aren't confirmed yet — no role change, but there's a
     record it was looked at.

  This exists because CSIA's actual membership records live in the
  Google Form / database, not in Discord — the bot's job is to flag new
  people to check, not to decide membership on its own.
- **Active Member** — a separate earned tier, granted automatically by
  `/markattendance` once someone hits `ATTENDANCE_THRESHOLD` (currently 3)
  events. Requires the base Member role already exists conceptually, but
  isn't technically gated on it in code — worth being aware of.

**Do not merge these into one role** even if it seems simpler — the
whole point is that someone attending Linux Fundamentals as a guest
shouldn't be forced into CSIA's membership database, and someone
verifying (agreeing to rules) shouldn't automatically become a Member
either.

### Setup this flow needs
- `config.MEMBERSHIP_FORM_URL` — paste the real Google Form link here.
  It's shown to people after they submit the in-Discord form, and in the
  welcome-channel embed.
- `config.REGISTRATION_LOG_CHANNEL_ID` — create an officer-only channel
  (e.g. `#registration-log`), copy its ID, and paste it in. Left at `0`
  it's a no-op (the bot just won't post there), so nothing breaks if you
  haven't set this up yet — but officers won't see new submissions
  either.

## 5. Support Tickets — read before changing anything

Native ticket system (`ticket_store.py` + `ticket_system.py`), built this
session to replace Carl-bot per the consolidation idea in the old "Section
8" backlog — one less third-party bot to maintain, and it reuses the same
persistent-button + modal pattern as Verify & Register.

### Flow

1. An officer runs `/postticketpanel` (once) — posts a "🛟 Open a Ticket"
   button embed in `config.TICKET_PANEL_CHANNEL_ID`.
2. A member clicks it, fills a one-field modal (what they need help with),
   and the bot creates a private text channel under
   `config.TICKET_CATEGORY_ID`, visible only to that member, the bot, and
   `TICKET_STAFF_ROLE_IDS` (falls back to `OFFICER_ROLE_IDS` if left
   empty — same pattern as `EXPORT_ROLE_IDS`).
3. A member can only have **one open ticket at a time** — clicking the
   panel button again just links them back to their existing ticket
   channel instead of creating a duplicate.
4. Either the opener or ticket staff clicks **Close Ticket** in the
   channel (or staff runs `/closeticket` inside it) — the bot posts a
   10-second warning, then deletes the channel.
5. If `config.TICKET_LOG_CHANNEL_ID` is set, a summary embed (opener,
   closed by, opened-at timestamp) is posted there right before the
   channel is deleted — since the channel itself is the only other record
   of what was discussed, and it's gone after close.

### Setup this needs (all placeholders in `config.py` right now)

- `TICKET_CATEGORY_ID` — create a category (e.g. **Tickets**) with no
  default permissions (so it starts fully private), copy its ID.
- `TICKET_PANEL_CHANNEL_ID` — the public channel the "Open a Ticket"
  button gets posted in, e.g. `#support`.
- `TICKET_STAFF_ROLE_IDS` — optional; leave empty to reuse
  `OFFICER_ROLE_IDS`, or narrow it to a dedicated "Support" role.
- `TICKET_LOG_CHANNEL_ID` — optional; leave at `0` to skip logging closed
  tickets entirely.

`/postticketpanel` checks `TICKET_CATEGORY_ID` and that at least one
staff role actually resolves (`TICKET_STAFF_ROLE_IDS` or a fallback to
`OFFICER_ROLE_IDS`) before it'll post the panel — a bad config shows up
as a clear error to the officer running the command, not as a
silently-broken ticket button members discover on their own.

### Failure handling

- If Discord rejects channel creation (missing Manage Channels, category
  hit the 50-channel cap, etc.), the member gets a clear ephemeral error
  telling them to ping an officer directly — not a silently hung
  interaction.
- If closing a ticket fails to actually delete the channel, the ticket
  stays marked **open** in `tickets.json` rather than being silently
  dropped — an orphaned-but-untracked channel would be worse than one
  that still shows as open and needs an officer to clean up manually.

### Why the channel gets deleted instead of archived

Kept intentionally simple for this first version — no transcript export,
no archive category. If CSIA wants transcripts kept, the place to add
that is `close_ticket_channel()` in `ticket_system.py` (e.g. dump the
channel's message history to a file and attach it to the
`TICKET_LOG_CHANNEL_ID` post before deleting) — flagged here rather than
built now since it wasn't asked for.

## 6. Personal data this bot stores

`registrations.json` contains **real names and email addresses** (no
longer a membership flag — that decision lives in the Google Form now,
not this file).

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
- New submissions are also posted live to `REGISTRATION_LOG_CHANNEL_ID`
  (see Section 4) — that channel will accumulate the same name/email
  data over time as regular chat history, so it should be officer-only
  and probably cleared out periodically, same caution as the JSON file.

## 7. Before you push any change

Run the test suite:
```bash
python -m pytest test_stores.py -v
```
This covers `attendance_store.py`, `registration_store.py`, and
`ticket_store.py` — the storage modules most likely to silently break in
a way that loses data. It does NOT cover `bot.py`, `welcome_events.py`,
or `ticket_system.py` (those need a live Discord connection to test
meaningfully), so manual testing on a personal/test server is still the
right move for anything touching commands, reaction handlers, or the
ticket buttons.

## 8. Config file map (where to change what)

Everything server-specific lives in `config.py` — IDs for roles,
channels, the guild itself, and all the text content for embeds (rules,
verification prompt, role menu descriptions). You should never need to
edit `bot.py` just to change wording or add a new role option — check
`config.py` first.

## 9. Questions this document doesn't answer

If you're stuck on something not covered here, the person who built this
(check the "Who has access" table above) is the best first contact. If
they're unreachable, the code itself is heavily commented — start with
`bot.py`'s module docstring at the top, then follow the imports.