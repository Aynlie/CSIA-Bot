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
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import config
import attendance_store

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


# ─────────────────────────────────────────────────────────
# REACTION ROLES
# ─────────────────────────────────────────────────────────

@bot.tree.command(name="postroles", description="Post the CSIA track selection message (officers only)")
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

    embed = discord.Embed(
        title=config.EMBED_TITLE,
        description=config.EMBED_DESCRIPTION,
        color=discord.Color.red(),
    )
    embed.set_footer(text=config.EMBED_FOOTER)

    message = await channel.send(embed=embed)
    for emoji in config.EMOJI_TO_ROLE:
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            print(f"Could not add reaction for emoji: {emoji}")

    await interaction.response.send_message(f"Role selection message posted in {channel.mention}.", ephemeral=True)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    role_id = config.EMOJI_TO_ROLE.get(str(payload.emoji))
    if not role_id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    role = guild.get_role(role_id)
    member = guild.get_member(payload.user_id)
    if role and member:
        await member.add_roles(role, reason="CSIA reaction role")


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    role_id = config.EMOJI_TO_ROLE.get(str(payload.emoji))
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


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN not found. Did you create a .env file from .env.example?")
    bot.run(TOKEN)