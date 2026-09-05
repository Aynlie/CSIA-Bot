"""
CSIA Bot — main entry point.

Features:
1. Reaction-role message for track/interest selection (posted via /postroles)
2. /markattendance — officers mark a member present at an event
3. Auto-upgrade a member to "Active Member" once they hit the attendance threshold
4. /myevents — members check their own attendance history

SETUP:
1. pip install -r requirements.txt
2. Copy .env.example to .env and fill in DISCORD_BOT_TOKEN
3. Fill in all the IDs in config.py
4. python bot.py
"""

import os
import csv
import io
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import config
import attendance_store
import profile_card
import welcome_events
import registration_store

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)


def is_officer(member: discord.Member) -> bool:
    member_role_ids = {r.id for r in member.roles}
    return any(rid in member_role_ids for rid in config.OFFICER_ROLE_IDS if rid)


def is_member(member: discord.Member) -> bool:
    if not config.MEMBER_ROLE_ID:
        return True  # if not configured, don't block anyone
    member_role_ids = {r.id for r in member.roles}
    return config.MEMBER_ROLE_ID in member_role_ids


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            # Copy globally-defined commands into this guild's command tree
            # so they sync instantly instead of waiting up to an hour for
            # Discord's global command propagation.
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
        else:
            synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Slash command sync failed: {e}")

    # Re-attach the persistent Verify & Register button so it keeps working
    # across restarts (needed because RegisterView uses timeout=None + a
    # fixed custom_id).
    bot.add_view(welcome_events.RegisterView())


# ─────────────────────────────────────────────────────────
# REACTION ROLES (supports multiple menus)
# ─────────────────────────────────────────────────────────

# Flatten every menu's emoji->role mapping into one lookup table.
# Assumes emojis don't repeat across menus (they don't, in config.py).
_EMOJI_TO_ROLE = {}
for _menu in config.ROLE_MENUS:
    _EMOJI_TO_ROLE.update(_menu["roles"])


@bot.tree.command(name="postroles", description="Post all CSIA role-selection menus (officers only)")
async def postroles(interaction: discord.Interaction):
    if not is_officer(interaction.user):
        await interaction.response.send_message("Only officers can use this command.", ephemeral=True)
        return

    channel = bot.get_channel(config.ROLE_SELECTION_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "ROLE_SELECTION_CHANNEL_ID isn't set correctly in config.py.", ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Posting {len(config.ROLE_MENUS)} role menu(s) in {channel.mention}...", ephemeral=True
    )

    for menu in config.ROLE_MENUS:
        embed = discord.Embed(
            title=menu["title"],
            description=menu["description"],
            color=discord.Color.red(),
        )
        if menu.get("image"):
            embed.set_image(url=menu["image"])
        embed.set_footer(text=config.EMBED_FOOTER)

        message = await channel.send(embed=embed)
        for emoji in menu["roles"]:
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                print(f"Could not add reaction for emoji: {emoji}")


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    member = guild.get_member(payload.user_id)
    if member is None:
        return

    # Verification gate — separate, single-emoji reaction on its own tracked message
    if payload.message_id == _verification_message_id and str(payload.emoji) == config.VERIFICATION_EMOJI:
        role = guild.get_role(config.VERIFIED_ROLE_ID)
        if role and role not in member.roles:
            await member.add_roles(role, reason="Verified — agreed to server rules")
        return

    # Role-menu reactions (Specialization, Pronouns, Year Level, etc.)
    role_id = _EMOJI_TO_ROLE.get(str(payload.emoji))
    if not role_id:
        return

    role = guild.get_role(role_id)
    if role:
        await member.add_roles(role, reason="CSIA reaction role")


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    role_id = _EMOJI_TO_ROLE.get(str(payload.emoji))
    if not role_id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    role = guild.get_role(role_id)
    member = guild.get_member(payload.user_id)
    if role and member:
        await member.remove_roles(role, reason="CSIA reaction role removed")


# ─────────────────────────────────────────────────────────
# RULES MESSAGE
# ─────────────────────────────────────────────────────────

@bot.tree.command(
    name="postrules",
    description="Post the CSIA rules + verification messages, back-to-back (officers only)",
)
async def postrules(interaction: discord.Interaction):
    global _verification_message_id

    if not is_officer(interaction.user):
        await interaction.response.send_message("Only officers can use this command.", ephemeral=True)
        return

    channel = bot.get_channel(config.RULES_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "RULES_CHANNEL_ID isn't set correctly in config.py.", ephemeral=True
        )
        return

    # 1) Rules embed
    rules_embed = discord.Embed(
        title=config.RULES_TITLE,
        description=config.RULES_DESCRIPTION,
        color=discord.Color.red(),
    )
    rules_embed.set_footer(text=config.EMBED_FOOTER)
    if config.RULES_IMAGE:
        rules_embed.set_image(url=config.RULES_IMAGE)
    await channel.send(embed=rules_embed)

    # 2) Verification embed — sent immediately after, same channel, so it always
    # lands directly under the rules message with nothing able to get between them.
    verification_channel = bot.get_channel(config.VERIFICATION_CHANNEL_ID)
    if verification_channel is None:
        await interaction.response.send_message(
            f"Rules posted in {channel.mention}, but VERIFICATION_CHANNEL_ID isn't set "
            "correctly in config.py — verification message was not posted.",
            ephemeral=True,
        )
        return

    verification_embed = discord.Embed(
        title=config.VERIFICATION_TITLE,
        description=config.VERIFICATION_DESCRIPTION,
        color=discord.Color.red(),
    )
    verification_embed.set_footer(text=config.EMBED_FOOTER)

    verification_message = await verification_channel.send(embed=verification_embed)
    await verification_message.add_reaction(config.VERIFICATION_EMOJI)
    _verification_message_id = verification_message.id

    await interaction.response.send_message(
        f"Rules + verification posted in {channel.mention}.", ephemeral=True
    )


# ─────────────────────────────────────────────────────────
# VERIFICATION GATE
# ─────────────────────────────────────────────────────────

_verification_message_id = None  # tracked so reaction handler only fires on this message


@bot.tree.command(
    name="postverification",
    description="Re-post ONLY the verification message (officers only) — /postrules already posts this automatically",
)
async def postverification(interaction: discord.Interaction):
    global _verification_message_id

    if not is_officer(interaction.user):
        await interaction.response.send_message("Only officers can use this command.", ephemeral=True)
        return

    channel = bot.get_channel(config.VERIFICATION_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "VERIFICATION_CHANNEL_ID isn't set correctly in config.py.", ephemeral=True
        )
        return

    embed = discord.Embed(
        title=config.VERIFICATION_TITLE,
        description=config.VERIFICATION_DESCRIPTION,
        color=discord.Color.red(),
    )
    embed.set_footer(text=config.EMBED_FOOTER)

    message = await channel.send(embed=embed)
    await message.add_reaction(config.VERIFICATION_EMOJI)
    _verification_message_id = message.id

    await interaction.response.send_message(
        f"Verification message posted in {channel.mention}.", ephemeral=True
    )


# ─────────────────────────────────────────────────────────
# ATTENDANCE TRACKING
# ─────────────────────────────────────────────────────────

@bot.tree.command(name="markattendance", description="Mark a member as having attended an event (officers only)")
@app_commands.describe(member="The member who attended", event_name="Name of the event")
async def markattendance(interaction: discord.Interaction, member: discord.Member, event_name: str):
    if not is_officer(interaction.user):
        await interaction.response.send_message("Only officers can use this command.", ephemeral=True)
        return

    new_count = attendance_store.record_attendance(member.id, event_name)
    response = f"✅ Recorded: **{member.display_name}** attended **{event_name}**. Total events: {new_count}."

    # Auto-upgrade check
    upgraded = False
    if new_count >= config.ATTENDANCE_THRESHOLD and config.ACTIVE_MEMBER_ROLE_ID:
        active_role = interaction.guild.get_role(config.ACTIVE_MEMBER_ROLE_ID)
        if active_role and active_role not in member.roles:
            await member.add_roles(active_role, reason="Reached attendance threshold")
            upgraded = True

    if upgraded:
        response += f"\n🎉 {member.mention} has been upgraded to **{active_role.name}**!"
        announce_channel = bot.get_channel(config.ANNOUNCEMENTS_CHANNEL_ID)
        if announce_channel:
            await announce_channel.send(
                f"🎉 Congrats {member.mention} — you've been promoted to **{active_role.name}** "
                f"for attending {new_count} CSIA events!"
            )

    await interaction.response.send_message(response, ephemeral=True)


@bot.tree.command(name="myevents", description="Check your own CSIA event attendance history")
async def myevents(interaction: discord.Interaction):
    if not is_member(interaction.user):
        await interaction.response.send_message(
            "This command is for official CSIA Members only.", ephemeral=True
        )
        return

    history = attendance_store.get_event_history(interaction.user.id)
    if not history:
        await interaction.response.send_message("You haven't been marked present at any events yet.", ephemeral=True)
        return

    lines = [f"• {e['event']}" for e in history]
    remaining = max(0, config.ATTENDANCE_THRESHOLD - len(history))
    text = (
        f"**Your CSIA Attendance ({len(history)} event(s)):**\n" + "\n".join(lines)
    )
    if remaining > 0:
        text += f"\n\nAttend {remaining} more event(s) to be upgraded to Active Member!"

    await interaction.response.send_message(text, ephemeral=True)




# ─────────────────────────────────────────────────────────
# WELCOME / ARRIVALS
# ─────────────────────────────────────────────────────────

@bot.event
async def on_member_join(member: discord.Member):
    channel = bot.get_channel(config.ARRIVALS_CHANNEL_ID)
    if channel is None:
        return  # ARRIVALS_CHANNEL_ID not set yet in config.py
    await channel.send(embed=welcome_events.build_join_embed(member))


@bot.tree.command(
    name="postwelcome",
    description="Post the CSIA welcome guide embed in #welcome-to-csia (officers only)",
)
async def postwelcome(interaction: discord.Interaction):
    if not is_officer(interaction.user):
        await interaction.response.send_message("Only officers can use this command.", ephemeral=True)
        return

    channel = bot.get_channel(config.WELCOME_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "WELCOME_CHANNEL_ID isn't set correctly in config.py.", ephemeral=True
        )
        return

    await channel.send(
        embed=welcome_events.build_welcome_channel_embed(interaction.guild),
        view=welcome_events.RegisterView(),
    )
    await interaction.response.send_message(f"Posted the welcome guide in {channel.mention}.", ephemeral=True)


# ─────────────────────────────────────────────────────────
# PROFILE CARD
# ─────────────────────────────────────────────────────────

@bot.tree.command(name="profile", description="View your CSIA profile card")
@app_commands.describe(member="Whose profile to view (defaults to yourself)")
async def profile(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    await interaction.response.defer()
    file = await profile_card.build_profile_card(target)
    await interaction.followup.send(file=file)




@bot.tree.command(name="viewregistration", description="View a member's welcome-channel registration info (officers only)")
@app_commands.describe(member="The member whose registration to view")
async def viewregistration(interaction: discord.Interaction, member: discord.Member):
    if not is_officer(interaction.user):
        await interaction.response.send_message("Only officers can use this command.", ephemeral=True)
        return

    reg = registration_store.get_registration(member.id)
    if reg is None:
        await interaction.response.send_message(f"{member.display_name} hasn't registered yet.", ephemeral=True)
        return

    text = (
        f"**Registration for {member.display_name}:**\n"
        f"Full Name: {reg['full_name']}\n"
        f"Personal Email: {reg['personal_email']}\n"
        f"HAU Student Email: {reg['hau_email'] or '(not provided)'}\n"
        f"Linux Fundamentals Attendee: {'Yes' if reg['is_linux_attendee'] else 'No'}\n"
        f"Submitted: {reg['submitted_at']}"
    )
    await interaction.response.send_message(text, ephemeral=True)


@bot.tree.command(name="exportregistrations", description="Export all welcome-channel registrations as a CSV (officers only)")
async def exportregistrations(interaction: discord.Interaction):
    if not is_officer(interaction.user):
        await interaction.response.send_message("Only officers can use this command.", ephemeral=True)
        return

    data = registration_store.get_all_registrations()
    if not data:
        await interaction.response.send_message("No registrations recorded yet.", ephemeral=True)
        return

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Discord User ID", "Discord Username", "Full Name", "Personal Email",
        "HAU Student Email", "Linux Fundamentals Attendee", "Submitted At",
    ])

    for user_id_str, reg in data.items():
        member = interaction.guild.get_member(int(user_id_str))
        discord_username = member.name if member else "(left server)"
        writer.writerow([
            user_id_str,
            discord_username,
            reg["full_name"],
            reg["personal_email"],
            reg["hau_email"] or "",
            "Yes" if reg["is_linux_attendee"] else "No",
            reg["submitted_at"],
        ])

    buffer.seek(0)
    file_bytes = io.BytesIO(buffer.getvalue().encode("utf-8"))
    filename = f"csia_registrations_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    discord_file = discord.File(file_bytes, filename=filename)

    await interaction.response.send_message(
        f"Exported {len(data)} registration(s).", file=discord_file, ephemeral=True,
    )


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN not found. Did you create a .env file from .env.example?")
    bot.run(TOKEN)