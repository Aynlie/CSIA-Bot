"""
CSIA Bot Configuration
-----------------------
Fill in the values below before running the bot.

HOW TO GET IDS:
1. In Discord, go to User Settings -> Advanced -> turn ON Developer Mode.
2. Right-click any role, channel, or server -> "Copy ID".
"""

# ── Server ──────────────────────────────────────────────
GUILD_ID = 1433350927989080176  # Right-click your server icon -> Copy Server ID

# ── Reaction Role Message ──────────────────────────────
# The channel where the "choose your track" message will be posted
ROLE_SELECTION_CHANNEL_ID = 1433350935480107135  # e.g. your #role-selection channel

# Map each emoji to the Role ID it should grant.
# Add/remove lines here to match your tracks (Cybersecurity, AI, Web Dev, etc.)
EMOJI_TO_ROLE = {
    "☁️": 1544627353358041179,   # Cloud & Cybersecurity -> Role ID
    "🧠": 1544627881362329720,   # AI & Data Science -> Role ID
    "💻": 1544627992217657417,   # Software Development -> Role ID
    "🌐": 1544628194622181428,   # Web & App Design -> Role ID
    "⚙️": 1544628044520489000,   # DevOps & Automation -> Role ID
    "🎨": 1544628266504298506,   # UI/UX Design -> Role ID
    "📱": 1544628327489478706,   # Mobile Development -> Role ID
    "🕹️": 1544628459509252166,   # Game Development -> Role ID
}

# ── Attendance / Activity Upgrade ──────────────────────
# Role granted once a member hits ATTENDANCE_THRESHOLD events
ACTIVE_MEMBER_ROLE_ID = 1433350927989080182
ATTENDANCE_THRESHOLD = 3  # number of events attended before auto-upgrade

# Role(s) allowed to run /markattendance (e.g. officer/exec role)
# Any member with one of these role IDs can mark attendance.
OFFICER_ROLE_IDS = [
    1544629040873213952,  # Secretariat
    1544629052122341427,  # Executive
]

# ── Announcements ───────────────────────────────────────
ANNOUNCEMENTS_CHANNEL_ID = 1433350935480107138  # your #announcements channel

# ── Embed text for the role-selection message ──────────
EMBED_TITLE = "Choose Your CSIA Track"
EMBED_DESCRIPTION = (
    "Discover your path in cybersecurity and connect with others who share your interest!\n\n"
    "React below to join discussions, projects, and events tailored to your track:\n\n"
    "☁️ — Cloud & Cybersecurity\n"
    "🧠 — AI & Data Science\n"
    "💻 — Software Development\n"
    "🌐 — Web & App Design\n"
    "⚙️ — DevOps & Automation\n"
    "🎨 — UI/UX Design\n"
    "📱 — Mobile Development\n"
    "🕹️ — Game Development\n"
)
EMBED_FOOTER = "CSIA — Cybersecurity Intelligence Alliance | Same Mission, Stronger Alliance."