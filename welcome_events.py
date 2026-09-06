"""
welcome_events.py — CSIA Cyberfox bot: welcome & arrivals embeds

Pure-ish helper module. build_join_embed() and build_welcome_channel_embed()
have no dependency on the `bot` object, same as before. RegistrationModal
and RegisterView DO need `config` and `registration_store` (to grant roles
and save submissions), so those two are imported here directly.

bot.py wires this module in three ways:
  1. on_member_join listener -> build_join_embed()
  2. /postwelcome command -> build_welcome_channel_embed() + RegisterView()
  3. on_ready -> bot.add_view(RegisterView()) so the button keeps working
     after a bot restart (required for any View with timeout=None and a
     custom_id, which is what makes a view "persistent").
"""

import re

import discord

import config
import registration_store

CSIA_RED = discord.Color.from_str("#A31712")

# Reasonably strict without being pedantic — catches the "not@real" case
# that a bare "@" in personal" check lets through, without rejecting valid
# but slightly unusual real-world addresses.
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_PATTERN.match(value.strip()))


async def grant_verified(guild: discord.Guild, member: discord.Member) -> bool:
    """
    Grants the Verified role if the member doesn't already have it.
    Returns True if the role was just granted, False if they already had it
    (or the role/member couldn't be resolved).

    This is the ONLY place that should ever grant Verified — both the rules
    reaction handler (bot.py) and the registration modal (below) call this
    instead of duplicating the add_roles() call, so there's exactly one
    place to update if what "Verified" means ever changes.
    """
    role = guild.get_role(config.VERIFIED_ROLE_ID)
    if role is None:
        return False
    if role in member.roles:
        return False
    await member.add_roles(role, reason="Verified — agreed to server rules")
    return True


def build_join_embed(member: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        description=(
            "🖤⬛🖤⬛🖤⬛🖤⬛🖤⬛🖤⬛🖤⬛\n"
            "★彡 **WELCOME TO THE DEN** 彡★\n\n"
            f"**A new Cyberfox has entered the alliance!**\n"
            f"**Welcome {member.mention} to CSIA — Cybersecurity Intelligence Alliance!** 🦊🔐\n\n"
            "Grab your gear, sharpen your skills,\n"
            "and let's hunt some vulnerabilities together. 💻🕵️\n\n"
            "★彡 **SAME MISSION, STRONGER ALLIANCE** 彡★\n"
            "🖤⬛🖤⬛🖤⬛🖤⬛🖤⬛🖤⬛🖤⬛"
        ),
        color=CSIA_RED,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="CSIA AY 2026-2027")
    return embed


def build_welcome_channel_embed(guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title="🦊 Welcome to CSIA — Cybersecurity Intelligence Alliance!",
        description=(
            "Hey there, future Cyberfox! 👋\n\n"
            "We're glad you found your way here. CSIA is HAU's home for "
            "cybersecurity enthusiasts — from Red Team offense to Blue Team "
            "defense, GRC, and everything in between.\n\n"
            "Before you dive in, here's how to get started:"
        ),
        color=CSIA_RED,
    )
    embed.add_field(
        name="🛡️ Step 1 — Read the Rules",
        value="Head to #rules-and-info and react ✅ to agree. This unlocks your Verified status.",
        inline=False,
    )
    embed.add_field(
        name="🎭 Step 2 — Pick Your Roles",
        value="Visit #role-selection to choose your Year Level, Specialization, Tools & Skills, and more.",
        inline=False,
    )
    embed.add_field(
        name="💬 Step 3 — Introduce Yourself",
        value="Drop a hello in #introductions — tell us your name, course/year, and what got you into cybersecurity.",
        inline=False,
    )
    embed.add_field(
        name="📢 Step 4 — Stay Updated",
        value="Check #announcements regularly for upcoming events, workshops, and CTFs.",
        inline=False,
    )
    embed.add_field(
        name="📝 One more thing — Verify & Register",
        value=(
            "**Complete Step 1 (react ✅ in #rules-and-info) first** — it unlocks the button below. "
            "Then click **Verify & Register** and fill in your name, email, and whether you're "
            "attending Linux Fundamentals or joining as a Member.\n\n"
            "*Your name and email are collected only to confirm event attendance and "
            "process CSIA membership, and are only visible to CSIA Officers. "
            "Contact the Secretariat if you'd like your data corrected or removed.*"
        ),
        inline=False,
    )
    embed.set_footer(text="Same Mission, Stronger Alliance. | CSIA AY 2026-2027")
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    return embed


class RegistrationModal(discord.ui.Modal, title="CSIA Verification & Registration"):
    full_name = discord.ui.TextInput(
        label="Full Name",
        placeholder="Juan Dela Cruz",
        max_length=100,
    )
    personal_email = discord.ui.TextInput(
        label="Personal Email (Gmail, etc.)",
        placeholder="you@gmail.com",
        max_length=100,
    )
    hau_email = discord.ui.TextInput(
        label="HAU Student Email",
        placeholder="you@student.hau.edu.ph",
        max_length=100,
        required=False,  # not everyone may have this yet
    )
    linux_attendee = discord.ui.TextInput(
        label="Linux Fundamentals attendee? (Yes/No)",
        placeholder="Yes or No",
        max_length=10,
    )
    become_member = discord.ui.TextInput(
        label="Join CSIA as an official Member? (Yes/No)",
        placeholder="Yes or No",
        max_length=10,
    )

    async def on_submit(self, interaction: discord.Interaction):
        name = self.full_name.value.strip()
        personal = self.personal_email.value.strip()
        hau = self.hau_email.value.strip()
        attendee_raw = self.linux_attendee.value.strip().lower()
        member_raw = self.become_member.value.strip().lower()

        if not is_valid_email(personal):
            await interaction.response.send_message(
                "That personal email doesn't look valid — please click the button again and retry.",
                ephemeral=True,
            )
            return

        if hau and not is_valid_email(hau):
            await interaction.response.send_message(
                "That HAU student email doesn't look valid — please click the button again and retry, "
                "or leave it blank if you don't have one yet.",
                ephemeral=True,
            )
            return

        is_attendee = attendee_raw in ("yes", "y", "yep", "yeah")
        wants_membership = member_raw in ("yes", "y", "yep", "yeah")

        registration_store.save_registration(
            interaction.user.id, name, personal, hau, is_attendee, wants_membership
        )

        member = interaction.user
        guild = interaction.guild

        granted = []

        # Verified just confirms they went through this form — independent
        # of whether they're joining CSIA as a Member or just here for the
        # Linux Fundamentals event. Uses the same helper the rules-reaction
        # handler uses, so this logic only exists in one place.
        if await grant_verified(guild, member):
            verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
            granted.append(verified_role.name)

        # Member is now its own explicit opt-in — not everyone filling this
        # form (e.g. outside guests here only for the Linux workshop) wants
        # to join CSIA as an org.
        if wants_membership:
            member_role = guild.get_role(config.MEMBER_ROLE_ID)
            if member_role and member_role not in member.roles:
                await member.add_roles(member_role, reason="Opted in to become an official CSIA Member")
                granted.append(member_role.name)

        if is_attendee:
            attendee_role = guild.get_role(config.LINUX_FUNDAMENTALS_ATTENDEE_ROLE_ID)
            if attendee_role and attendee_role not in member.roles:
                await member.add_roles(attendee_role, reason="Self-identified as Linux Fundamentals attendee")
                granted.append(attendee_role.name)

        announcements = guild.get_channel(config.ANNOUNCEMENTS_CHANNEL_ID)
        announcements_ref = announcements.mention if announcements else "#announcements"

        confirmation = f"Thanks, {name}! You're all set."
        if granted:
            confirmation += f" Roles granted: {', '.join(granted)}."

        if wants_membership:
            confirmation += (
                "\n\nWelcome to CSIA, official Member! 🦊 A few commands to get you started:\n"
                "• `/profile` — view your CSIA profile card (specialization, level, events attended)\n"
                "• `/myevents` — check your own event attendance history\n"
                f"• Keep an eye on {announcements_ref} for upcoming events, workshops, and CTFs"
            )
        elif is_attendee:
            confirmation += (
                "\n\nThanks for registering for Linux Fundamentals! 🐧 You now have access to the "
                "event channels. If you'd like to join CSIA as a Member later, just click "
                "**Verify & Register** again — contact an officer to update your answer."
            )
        else:
            confirmation += " Thanks for verifying! Feel free to look around."

        await interaction.response.send_message(confirmation, ephemeral=True)


class RegisterView(discord.ui.View):
    """
    timeout=None + a fixed custom_id makes this a persistent view — it
    keeps working after the bot restarts, as long as bot.add_view(RegisterView())
    is called once in on_ready (see bot.py).
    """

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify & Register",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="csia_register_button",
    )
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        verified_role = interaction.guild.get_role(config.VERIFIED_ROLE_ID)
        has_verified = verified_role in interaction.user.roles if verified_role else False

        if not has_verified:
            rules_channel = interaction.guild.get_channel(config.RULES_CHANNEL_ID)
            channel_ref = rules_channel.mention if rules_channel else "#rules-and-info"
            await interaction.response.send_message(
                f"Please react ✅ in {channel_ref} to agree to the rules first — "
                "that unlocks this registration form.",
                ephemeral=True,
            )
            return

        existing = registration_store.get_registration(interaction.user.id)
        if existing:
            await interaction.response.send_message(
                f"You've already registered as **{existing['full_name']}**. "
                "Contact an officer if you need to update your info.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(RegistrationModal())