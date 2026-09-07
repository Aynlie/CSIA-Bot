"""
ticket_system.py — CSIA Cyberfox bot: native support tickets

Built to replace Carl-bot's ticket feature (Handoff.md Section 9 —
"consolidate instead of adding more third-party bots"), reusing the same
persistent-button + modal pattern already established in welcome_events.py:

  - TicketPanelView: posted once via /postticketpanel. Its "Open a Ticket"
    button opens a short reason modal, which creates a private channel.
  - TicketCloseView: attached to the opening message of every ticket
    channel. Its "Close Ticket" button (or the /closeticket command, for
    staff who'd rather type than click) closes that specific channel.

Both views use timeout=None + a fixed custom_id, which makes them
persistent — bot.py must call bot.add_view() on one instance of each in
on_ready, same requirement as welcome_events.RegisterView.

Pure-ish module like welcome_events.py: build_ticket_panel_embed() and
is_ticket_staff() have no side effects, everything else here talks to
config.py and ticket_store.py directly since ticket lifecycle (creating
and deleting real Discord channels) doesn't cleanly separate from those.
"""

import asyncio

import discord

import config
import ticket_store

CSIA_RED = discord.Color.from_str("#A31712")

# How long a closed ticket channel stays visible (with a "closed" notice)
# before it's actually deleted — gives everyone in it a moment to see
# the close message and screenshot anything they need first.
CLOSE_DELAY_SECONDS = 10


def staff_role_ids() -> list[int]:
    """Falls back to OFFICER_ROLE_IDS if TICKET_STAFF_ROLE_IDS is left
    empty in config.py — same pattern as EXPORT_ROLE_IDS / is_exporter()
    in bot.py, so ticket setup works out of the box with zero extra config.
    Public (no leading underscore): /postticketpanel in bot.py calls this
    too, to validate at least one staff role actually resolves before the
    panel goes live."""
    return config.TICKET_STAFF_ROLE_IDS or config.OFFICER_ROLE_IDS


def is_ticket_staff(member: discord.Member) -> bool:
    member_role_ids = {r.id for r in member.roles}
    return any(rid in member_role_ids for rid in staff_role_ids() if rid)


def build_ticket_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title=config.TICKET_PANEL_TITLE,
        description=config.TICKET_PANEL_DESCRIPTION,
        color=CSIA_RED,
    )
    embed.set_footer(text=config.EMBED_FOOTER)
    return embed


class TicketReasonModal(discord.ui.Modal, title="Open a CSIA Support Ticket"):
    reason = discord.ui.TextInput(
        label="What do you need help with?",
        style=discord.TextStyle.paragraph,
        placeholder="Briefly describe your issue or question...",
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await _open_ticket(interaction, self.reason.value.strip())


async def _open_ticket(interaction: discord.Interaction, reason: str) -> None:
    guild = interaction.guild
    member = interaction.user

    # One open ticket per member at a time — stops duplicate/spam tickets
    # for the same issue.
    existing_channel_id = ticket_store.get_open_ticket_channel_id(member.id)
    if existing_channel_id:
        existing_channel = guild.get_channel(existing_channel_id)
        if existing_channel:
            await interaction.response.send_message(
                f"You already have an open ticket: {existing_channel.mention}",
                ephemeral=True,
            )
            return
        # The channel is gone (e.g. someone deleted it manually instead of
        # using Close Ticket) but the record wasn't cleared — don't let a
        # stale record block this person from ever opening a ticket again.
        ticket_store.close_ticket(existing_channel_id)

    category = guild.get_channel(config.TICKET_CATEGORY_ID)
    if category is None or not isinstance(category, discord.CategoryChannel):
        await interaction.response.send_message(
            "TICKET_CATEGORY_ID isn't set correctly in config.py — ask an officer to fix this.",
            ephemeral=True,
        )
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, manage_channels=True
        ),
    }
    for role_id in staff_role_ids():
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )

    await interaction.response.defer(ephemeral=True)

    temp_name = f"ticket-{member.name}".lower().replace(" ", "-")[:90]
    try:
        ticket_channel = await guild.create_text_channel(
            temp_name,
            category=category,
            overwrites=overwrites,
            reason=f"Support ticket opened by {member} ({member.id})",
        )
    except discord.HTTPException as e:
        # Most likely cause: bot is missing Manage Channels, or the category
        # already has Discord's 50-channel cap. Whatever it is, the member
        # gets a clear message instead of a silently hung interaction.
        await interaction.followup.send(
            "Couldn't create your ticket channel — please ping an officer "
            f"directly. (Error: {e})",
            ephemeral=True,
        )
        return

    number = ticket_store.create_ticket(ticket_channel.id, member.id)
    # The channel was named before we had the ticket number (create_ticket
    # assigns it), so rename now for a sortable, unambiguous channel list —
    # best-effort, a failed rename isn't worth blocking the ticket over.
    try:
        await ticket_channel.edit(name=f"ticket-{number:04d}-{member.name}"[:100].lower())
    except discord.HTTPException:
        pass

    staff_mentions = " ".join(
        role.mention for rid in staff_role_ids() if (role := guild.get_role(rid))
    )

    embed = discord.Embed(
        title=f"🎫 Ticket #{number}",
        description=(
            f"Opened by {member.mention}\n\n"
            f"**Reason:**\n{reason}\n\n"
            "A staff member will be with you shortly. Click **Close Ticket** "
            "below once this is resolved."
        ),
        color=CSIA_RED,
    )
    embed.set_footer(text=config.EMBED_FOOTER)

    await ticket_channel.send(
        content=f"{member.mention}" + (f" {staff_mentions}" if staff_mentions else ""),
        embed=embed,
        view=TicketCloseView(),
    )

    await interaction.followup.send(
        f"Your ticket has been created: {ticket_channel.mention}", ephemeral=True
    )


async def close_ticket_channel(channel: discord.TextChannel, closed_by: discord.Member) -> bool:
    """
    Closes and deletes a ticket channel. Returns True if the channel was
    actually deleted; False if it wasn't (either it wasn't a tracked
    ticket, or the delete itself failed — see below).

    Order matters here: the store record is only dropped AFTER the channel
    is confirmed deleted. If the delete fails (missing permissions, API
    hiccup, channel already gone), the ticket stays marked open — that's
    the safer failure mode, since the channel likely still exists and a
    member finding they can "open a new ticket" while their old one is
    still sitting there would be worse than needing an officer to clean
    it up manually.
    """
    ticket = ticket_store.get_ticket(channel.id)
    if ticket is None:
        return False

    guild = channel.guild
    opener = guild.get_member(ticket["opener_id"])

    try:
        await channel.send(
            f"🔒 Ticket closed by {closed_by.mention}. Deleting this channel in "
            f"{CLOSE_DELAY_SECONDS} seconds..."
        )
    except discord.HTTPException:
        pass  # best-effort warning only — don't let this block the close

    await asyncio.sleep(CLOSE_DELAY_SECONDS)

    try:
        await channel.delete(reason=f"Ticket closed by {closed_by} ({closed_by.id})")
    except discord.HTTPException as e:
        try:
            await channel.send(
                f"⚠️ Couldn't delete this channel automatically ({e}). An "
                "officer will need to remove it manually — this ticket is "
                "still marked open in the meantime."
            )
        except discord.HTTPException:
            pass
        return False

    # Only drop the record — and only log — once the channel is confirmed gone.
    ticket_store.close_ticket(channel.id)

    log_channel = (
        guild.get_channel(config.TICKET_LOG_CHANNEL_ID) if config.TICKET_LOG_CHANNEL_ID else None
    )
    if log_channel:
        log_embed = discord.Embed(title=f"🎫 Ticket #{ticket['number']} Closed", color=CSIA_RED)
        log_embed.add_field(
            name="Opened by",
            value=opener.mention if opener else f"User ID {ticket['opener_id']}",
            inline=True,
        )
        log_embed.add_field(name="Closed by", value=closed_by.mention, inline=True)
        log_embed.add_field(name="Opened at", value=ticket["opened_at"], inline=False)
        try:
            await log_channel.send(embed=log_embed)
        except discord.HTTPException:
            pass  # best-effort — a broken log channel shouldn't undo a real close

    return True


class TicketPanelView(discord.ui.View):
    """Persistent — must be re-registered with bot.add_view() in on_ready."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Open a Ticket",
        style=discord.ButtonStyle.success,
        emoji="🛟",
        custom_id="csia_open_ticket",
    )
    async def open_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketReasonModal())


class TicketCloseView(discord.ui.View):
    """Persistent — must be re-registered with bot.add_view() in on_ready."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="csia_close_ticket",
    )
    async def close_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        ticket = ticket_store.get_ticket(interaction.channel.id)

        if ticket is None:
            await interaction.response.send_message(
                "This doesn't look like an active ticket channel.", ephemeral=True
            )
            return

        is_opener = member.id == ticket["opener_id"]
        if not (is_opener or is_ticket_staff(member)):
            await interaction.response.send_message(
                "Only the person who opened this ticket or CSIA staff can close it.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await close_ticket_channel(interaction.channel, member)