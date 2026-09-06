"""
CSIA Bot Configuration
-----------------------
Fill in the values below before running the bot.

HOW TO GET IDS:
1. In Discord, go to User Settings -> Advanced -> turn ON Developer Mode.
2. Right-click any role, channel, or server -> "Copy ID".
"""

# ── Server ──────────────────────────────────────────────
GUILD_ID = 1541786235570364539  # CSIA 26-27 (real server)

# ── Reaction Role Menus ─────────────────────────────────
# The channel where ALL role-selection messages will be posted
ROLE_SELECTION_CHANNEL_ID = 1541787234586591294  # #role-selection

# Each menu becomes its own embed message with its own reactions.
# Add/remove/edit menus and roles here freely — /postroles posts all of them.
# Optional "image" key: paste a direct GIF/image URL to show it in that menu's embed.
ROLE_MENUS = [
    {
        "title": "Choose Your CSIA Specialization",
        "description": (
            "React below to join discussions, projects, and events tailored "
            "to your specialization:\n\n"
            "<:guyfawkesanonmask:1544963365946785842> — Red Team / Offensive Security\n"
            "<:malwarebytes:1544963429217861662> — Blue Team / Defensive Security\n"
            "🟣 — Purple Team\n"
            "📜 — GRC (Governance, Risk & Compliance)\n"
        ),
        "image": "",
        "roles": {
            "<:guyfawkesanonmask:1544963365946785842>": 1544911591521132615,   # Red Team / Offensive Security
            "<:malwarebytes:1544963429217861662>": 1544911921004937286,   # Blue Team / Defensive Security
            "🟣": 1544915250523021412,   # Purple Team
            "📜": 1544912052143788113,   # GRC
        },
    },
    {
        "title": "Pronouns",
        "description": (
            "💗 — She/Her\n"
            "💙 — He/Him\n"
            "💛 — Other/Ask\n"
        ),
        "image": "",
        "roles": {
            "💗": 1544910732343246988,   # She/Her
            "💙": 1544911137303306270,   # He/Him
            "💛": 1544910843714478170,   # Other/Ask
        },
    },
    {
        "title": "Year Level",
        "description": (
            "1️⃣ — 1st Year\n"
            "2️⃣ — 2nd Year\n"
            "3️⃣ — 3rd Year\n"
            "4️⃣ — 4th Year\n"
            "🎓 — Graduate School\n"
        ),
        "image": "",
        "roles": {
            "1️⃣": 1541792397019586560,   # 1st Year
            "2️⃣": 1541792444931252284,   # 2nd Year
            "3️⃣": 1541792439927447605,   # 3rd Year
            "4️⃣": 1541792450270461952,   # 4th Year
            "🎓": 1541792594386882660,   # Graduate School
        },
    },
    {
        "title": "Tools & Skills",
        "description": (
            "🐍 — Python\n"
            "<:linux:1544962835107545129> — Bash/Linux\n"
            "<:powershell:1544963030465519698> — PowerShell\n"
        ),
        "image": "",
        "roles": {
            "🐍": 1544912390909337640,   # Python
            "<:linux:1544962835107545129>": 1544912708355235850,   # Bash/Linux
            "<:powershell:1544963030465519698>": 1544912393417662484,   # PowerShell
        },
    },
    {
        "title": "What You Do",
        "description": (
            "<:kali:1544962950501105745> — Kali Linux/Parrot OS user\n"
            "<:incognito:1544963233360912424> — Bug Bounty Hunter\n"
            "<:Hackerman:1544963152037290025> — CTF Competitor\n"
            "❓ — Idk yet\n"
        ),
        "image": "",
        "roles": {
            "<:kali:1544962950501105745>": 1544912941113938010,   # Kali Linux/Parrot OS user
            "<:incognito:1544963233360912424>": 1544913100417798164,   # Bug Bounty Hunter
            "<:Hackerman:1544963152037290025>": 1541792311543992340,   # CTF Competitor
            "❓": 1544913248061759578,   # Idk yet
        },
    },
    {
        "title": "Linux Fundamentals Event — Sept 5",
        "description": (
            "React to get access to the event's dedicated channels "
            "(chat, resources, and support) for the Kali Linux Fundamentals workshop:\n\n"
            "🎫 — Linux Fundamentals Attendee\n"
        ),
        "image": "",
        "roles": {
            "🎫": 1545381398313963660,   # Linux Fundamentals Attendee
        },
    },
]

# ── Attendance / Activity Upgrade ──────────────────────
# Role granted once a member hits ATTENDANCE_THRESHOLD events
ACTIVE_MEMBER_ROLE_ID = 1544918348792467537  # Active Member (real server)
ATTENDANCE_THRESHOLD = 3  # number of events attended before auto-upgrade

# Role(s) allowed to run /markattendance and /postroles (e.g. officer/exec role)
OFFICER_ROLE_IDS = [
    1544650616863989820,  # Admin (real server)
]

# Role(s) allowed to run /exportregistrations — a stricter subset of officers,
# since this exports real names + personal emails as a downloadable file.
# Defaults to the same as OFFICER_ROLE_IDS below if left empty, so nothing
# breaks if you don't touch this — but you can narrow it (e.g. Secretary only)
# without any code changes.
EXPORT_ROLE_IDS: list[int] = [
    1544650616863989820,  # Admin (real server) — narrow this to just Secretary if desired
]

# ── Announcements ───────────────────────────────────────
ANNOUNCEMENTS_CHANNEL_ID = 1541803426139082833  # #announcements

# ── Membership ──────────────────────────────────────────
# Base "official CSIA member" role — required for /myevents.
# Separate from ACTIVE_MEMBER_ROLE_ID, which is an earned upgrade tier.
MEMBER_ROLE_ID = 1541802082816888902

# ── Rules Message ───────────────────────────────────────
RULES_CHANNEL_ID = 1541787264496046240  # #rules-and-info

# Optional: paste a direct image/GIF URL to show it inside the rules embed.
# Leave as "" for no image.
RULES_IMAGE = "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExajJ0bmRyb2xqNnlxODZ0MXBheDh0MmdyMnVqY3VtOXo2eGlncmxvNyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/tbR96Du7D7kRqodBVp/giphy.gif"

RULES_TITLE = "RULES AND REGULATIONS"
RULES_DESCRIPTION = (
    "CSIA — Cybersecurity Intelligence Alliance — is a space where students can "
    "build real skills, connect with others in the field, and grow together "
    "through hands-on cybersecurity work, CTFs, and community. To keep this a "
    "safe and productive space for everyone, please read and follow the rules "
    "below.\n\n"
    "**Disclaimer:** Anything posted in this server is visible within the "
    "community. CSIA is not responsible for content shared by individual "
    "members, including copyright issues arising from shared material.\n\n"
    "**Rules:**\n"
    "1. Be respectful at all times — harassment, discrimination, offensive "
    "remarks, or toxic behavior will not be tolerated.\n"
    "2. NSFW, unsafe, or disturbing content is strictly prohibited.\n"
    "3. Use each channel for its intended purpose to keep the server organized.\n"
    "4. Network and collaborate freely, as long as it's done respectfully and "
    "professionally.\n"
    "5. Do not impersonate another member, officer, or organization to gain "
    "access or mislead others.\n"
    "6. All hacking/security discussion is for educational and authorized "
    "purposes only — no facilitating unauthorized access to real systems.\n"
    "7. Give constructive, respectful feedback when commenting on someone's "
    "work, writeups, or projects.\n"
    "8. Be honest during CTFs and events — no cheating, flag sharing outside "
    "your team, or exploiting bugs in event infrastructure.\n"
    "9. And most importantly — have fun, learn something new, and support "
    "each other!\n\n"
    "**Monitoring & Escalation:**\n"
    "This server is monitored by CSIA Secretariat and Officers, who will "
    "review reports of rule violations. Sanctions depend on the severity of "
    "the infringement — minor issues may result in a warning, while serious "
    "violations (harassment, unauthorized access attempts, explicit content, "
    "or repeated bullying) will result in an immediate kick or ban without "
    "prior warning."
)

# ── Verification ─────────────────────────────────────────
# Independent gate role — proves someone read and agreed to the rules.
# Does NOT imply Member or Linux Fundamentals Attendee status.
# Posted to the SAME channel as the rules message, right after it —
# /postrules sends both embeds back-to-back automatically.
VERIFICATION_CHANNEL_ID = RULES_CHANNEL_ID
VERIFIED_ROLE_ID = 1545401144640143360
VERIFICATION_EMOJI = "✅"

VERIFICATION_TITLE = "Do you agree to follow the rules?"
VERIFICATION_DESCRIPTION = (
    f"By reacting with {VERIFICATION_EMOJI} you agree to follow all CSIA server "
    "rules and keep things respectful for everyone.\n\n"
    "Make sure you've read #rules-and-info before confirming."
)

# ── Shared footer for every role menu embed ────────────
EMBED_FOOTER = "CSIA — Cybersecurity Intelligence Alliance | Same Mission, Stronger Alliance."
# ── Welcome / Arrivals ──────────────────────────────────
ARRIVALS_CHANNEL_ID = 1541801118949056673  # TODO: fill in #arrivals channel ID
WELCOME_CHANNEL_ID = 1541801587889016894   # TODO: fill in #welcome-to-csia channel ID

# Officer-only channel where a notification is posted every time someone
# submits the Verify & Register form — lets officers spot new submissions
# and cross-check them against the membership Google Form without having
# to run /viewregistration on everyone manually.
REGISTRATION_LOG_CHANNEL_ID = 1544657009193000970 # TODO: fill in your officer-only log channel ID

# ── Specialization roles, for the /profile card ─────────
# Reuses the same role IDs already wired into ROLE_MENUS above
# (Specialization menu) — maps role ID -> (display label, hex accent color).
SPECIALIZATION_ROLE_STYLES = {
    1544911591521132615: ("Red Team", "#C83C3C"),     # Red Team / Offensive Security
    1544911921004937286: ("Blue Team", "#3C6EC8"),    # Blue Team / Defensive Security
    1544915250523021412: ("Purple Team", "#9646BE"),  # Purple Team
    1544912052143788113: ("GRC", "#C8A03C"),          # GRC
}

# ── Membership (handled externally) ─────────────────────
# CSIA membership is no longer auto-granted by the bot's registration form.
# Officers check submissions against this Google Form / the member database
# and manually assign MEMBER_ROLE_ID in Discord.
MEMBERSHIP_FORM_URL = "https://forms.gle/REPLACE_WITH_REAL_LINK"  # TODO: paste real form link

# ── Registration (welcome-channel verify & register button) ─────
# Same role ID already used for the 🎫 reaction in ROLE_MENUS above —
# exposed as its own named constant so welcome_events.py can reference it
# without digging through the ROLE_MENUS list.
LINUX_FUNDAMENTALS_ATTENDEE_ROLE_ID = 1545381398313963660