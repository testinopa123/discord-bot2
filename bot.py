import discord
from discord.ext import commands
import os
import re
import random
import typing
import datetime
from datetime import timedelta
from dotenv import load_dotenv
from discord.ui import Button, View, Select, Modal, TextInput
from typing import Optional
import asyncio
from discord import ButtonStyle, TextStyle
import pytz
from flask import Flask
from threading import Thread
import json
from discord import SelectOption, ButtonStyle, Embed
from typing import Union






print("Bot script is starting...")

# Load the .env file
load_dotenv()

# Bot setup with command prefix
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=['*', '$'], intents=intents)

# Command logging system
command_logs = []

# Role IDs
PREMIUM_ROLE_ID = 1316416010076684478
BLACKLIST_ROLE_ID = 1396514687608160296
LOG_CHANNEL_ID = 1418328214589149256
PROTECTED_ROLE_ID = 1396507987253657743
TICKET_CATEGORY_ID = 1394030033043062784
SUPPORT_ROLE_ID = 1394030191659188236
MANAGEMENT_ROLE_ID = int(os.getenv('MANAGEMENT_ROLE_ID',
                                   '1315714615396794480'))

from asyncio import sleep




@bot.command(name='staffac')
async def staff_activity(ctx, time_period: Union[int, str] = None):
    """Check staff activity for a specific time period"""
    if time_period is None:
        await ctx.send("❌ Please specify a time period! Example: `$staffac 7` or `$staffac 31/01/25`")
        return

    # Parse the time period (make timezone-aware)
    now = datetime.datetime.now(datetime.timezone.utc)

    if isinstance(time_period, int):
        # Number of days ago
        start_time = now - datetime.timedelta(days=time_period)
        end_time = now
    else:
        # Specific date (DD/MM/YY format)
        try:
            day, month, year = map(int, time_period.split('/'))
            # Handle 2-digit year (assume 20XX)
            if year < 100:
                year += 2000
            # Create timezone-aware datetime
            start_time = datetime.datetime(year, month, day, tzinfo=datetime.timezone.utc)
            end_time = now
        except ValueError:
            await ctx.send("❌ Invalid date format! Use `DD/MM/YY` or number of days.")
            return

    # Get staff role
    staff_role = ctx.guild.get_role(1316405342141419611)
    if not staff_role:
        await ctx.send("❌ Staff role not found!")
        return

    # Convert to Discord timestamps
    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())

    # Create embed
    embed = discord.Embed(
        title="STAFF ACTIVITY CHECK",
        description=f"<t:{start_ts}> - <t:{end_ts}>",
        color=0xFFA500
    )

    # Count messages for each staff member
    staff_messages = {}
    total_messages = 0

    # Check each text channel
    for channel in ctx.guild.text_channels:
        try:
            async for message in channel.history(limit=None, after=start_time, before=end_time):
                # Check if author is a Member (has roles) and has staff role
                if isinstance(message.author, discord.Member) and staff_role in message.author.roles:
                    if message.author.id not in staff_messages:
                        staff_messages[message.author.id] = 0
                    staff_messages[message.author.id] += 1
                    total_messages += 1
        except discord.Forbidden:
            continue
        except discord.HTTPException:
            continue

    # Sort staff by message count
    sorted_staff = sorted(staff_messages.items(), key=lambda x: x[1], reverse=True)

    # Build staff list string
    staff_list = ""
    for user_id, count in sorted_staff:
        member = ctx.guild.get_member(user_id)
        if member:
            staff_list += f"{member.display_name} - {user_id}     >   {count}\n"

    if not staff_list:
        staff_list = "No messages found in this period"

    embed.add_field(
        name="\u200b",
        value=f"```{staff_list}```",
        inline=False
    )

    # Add total messages and MVP
    embed.add_field(
        name="**TOTAL MESSAGES**",
        value=f"`{total_messages}`",
        inline=False
    )

    if sorted_staff:
        mvp_id, mvp_count = sorted_staff[0]
        mvp_member = ctx.guild.get_member(mvp_id)
        if mvp_member:
            embed.add_field(
                name="**MVP**",
                value=f"{mvp_member.mention} with **{mvp_count}** messages",
                inline=False
            )
        else:
            embed.add_field(
                name="**MVP**",
                value=f"User with ID {mvp_id} with **{mvp_count}** messages",
                inline=False
            )
    else:
        embed.add_field(
            name="**MVP**",
            value="No messages found",
            inline=False
        )

    # Add footer with command user info
    embed.set_footer(
        text=f"invoked by {ctx.author.display_name}",
        icon_url=ctx.author.display_avatar.url
    )

    await ctx.send(embed=embed)



@bot.command(name='ms')
async def mod_stats(ctx, member: discord.Member = None):
    """Check message statistics for a user"""
    if member is None:
        await ctx.send("❌ Please mention a user! Example: `$ms @user`")
        return

    # Create embed
    embed = discord.Embed(
        title=f"MODSTATS of {member.display_name}",
        color=0xFFA500
    )

    # Calculate time periods (timezone-aware)
    now = datetime.datetime.now(datetime.timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - datetime.timedelta(days=7)

    # Count messages
    total_messages = 0
    month_messages = 0
    year_messages = 0
    week_messages = 0

    # Check each text channel
    for channel in ctx.guild.text_channels:
        try:
            async for message in channel.history(limit=None):
                # Make message time timezone-aware for comparison
                message_time = message.created_at.replace(tzinfo=datetime.timezone.utc)

                if message.author.id == member.id:
                    total_messages += 1

                    if message_time >= month_start:
                        month_messages += 1

                    if message_time >= year_start:
                        year_messages += 1

                    if message_time >= week_ago:
                        week_messages += 1
        except discord.Forbidden:
            continue
        except discord.HTTPException:
            continue

    # Build stats string
    stats = (
        f"Total Messages = {total_messages}\n\n"
        f"Total Messages Sent This Month = {month_messages}\n\n"
        f"Total Messages Sent This Year = {year_messages}\n\n"
        f"Total Messages Sent In The Last 7 Days = {week_messages}"
    )

    embed.add_field(
        name="\u200b",
        value=f"```{stats}```",
        inline=False
    )

    # Add footer with command user info
    embed.set_footer(
        text=f"invoked by {ctx.author.display_name}",
        icon_url=ctx.author.display_avatar.url
    )

    # Reply to the message
    await ctx.reply(embed=embed, mention_author=True)




# File to store banned users
BANLIST_FILE = "command_bans.json"



def load_banlist():
    """Load the banlist from file"""
    if not os.path.exists(BANLIST_FILE):
        with open(BANLIST_FILE, 'w') as f:
            json.dump([], f)
        return []

    with open(BANLIST_FILE, 'r') as f:
        return json.load(f)

def save_banlist(banlist):
    """Save the banlist to file"""
    with open(BANLIST_FILE, 'w') as f:
        json.dump(banlist, f)

def is_banned(user_id):
    """Check if a user is banned"""
    return str(user_id) in load_banlist()

# Add this check before processing any commands
@bot.check
async def check_if_banned(ctx):
    if is_banned(ctx.author.id):
        embed = discord.Embed(
            title="Command Access Denied",
            description="You have been banned from using bot commands.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return False
    return True

@bot.command(name='devban')
@commands.is_owner()
async def devban(ctx, user_id: int):
    """Ban a user from using commands (owner only)"""
    banlist = load_banlist()

    if str(user_id) in banlist:
        embed = discord.Embed(
            description=f"❌ <@{user_id}> is already command banned.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    banlist.append(str(user_id))
    save_banlist(banlist)

    embed = discord.Embed(
        title="Command Ban Issued",
        description=f"Banned <@{user_id}> from accessing any commands.",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"Invoked by {ctx.author}")
    await ctx.send(embed=embed)

@bot.command(name='devunban')
@commands.is_owner()
async def devunban(ctx, user_id: int):
    """Unban a user from using commands (owner only)"""
    banlist = load_banlist()

    if str(user_id) not in banlist:
        embed = discord.Embed(
            description=f"❌ <@{user_id}> is not command banned.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    banlist.remove(str(user_id))
    save_banlist(banlist)

    embed = discord.Embed(
        title="Command Ban Lifted",
        description=f"Unbanned <@{user_id}> from command restrictions.",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Invoked by {ctx.author}")
    await ctx.send(embed=embed)

@bot.command(name='devlist')
@commands.is_owner()  # Only the bot owner can use this command
async def devlist(ctx):
    """List all servers the bot is in"""
    # Create embed
    embed = discord.Embed(
        title=f"{bot.user.name} is in these servers:",
        color=discord.Color.blue()
    )

    # Add each server to the embed
    for guild in bot.guilds:
        embed.add_field(
            name=guild.name,
            value=f"`{guild.id}` - {len(guild.members)} members",
            inline=False
        )

    # Add footer with total count
    embed.set_footer(text=f"Total servers: {len(bot.guilds)}")

    await ctx.send(embed=embed)

MAINTENANCE_FILE = "maintenance.json"

# Default maintenance data if file doesn't exist
DEFAULT_MAINTENANCE_DATA = {
    "is_maintenance": False,
    "timestamp": None,
    "message": ""
}

# Function to load maintenance data
def load_maintenance_data():
    if not os.path.exists(MAINTENANCE_FILE):
        with open(MAINTENANCE_FILE, 'w') as f:
            json.dump(DEFAULT_MAINTENANCE_DATA, f)
        return DEFAULT_MAINTENANCE_DATA
    with open(MAINTENANCE_FILE, 'r') as f:
        return json.load(f)

# Function to save maintenance data
def save_maintenance_data(data):
    with open(MAINTENANCE_FILE, 'w') as f:
        json.dump(data, f)

# Info Command
@bot.command(name='info')
async def info(ctx):
    # Bot's ping
    bot_ping = round(bot.latency * 1000)

    # Load maintenance data
    maintenance_data = load_maintenance_data()

    # Create embed
    embed = discord.Embed(color=discord.Color.orange())

    # Set bot's image on the right side
    embed.set_thumbnail(url=str(bot.user.avatar.url))

    # Server info
    embed.add_field(name="**Op9et**", value=f"- {ctx.guild.name}", inline=False)

    # Developer info
    embed.add_field(name="Developed by", value="*[Mate.1234](https://x.com/opa_200?s=21)* using Python.", inline=False)

    # Current MS (bot's ping)
    embed.add_field(name="__ Current MS __", value=f"```{bot_ping}ms - Europe```", inline=False)

    # Scheduled Maintenance
    maintenance_text = "No maintenance periods found"
    if maintenance_data["is_maintenance"]:
        timestamp = maintenance_data["timestamp"]
        message = maintenance_data["message"]
        maintenance_text = f"Yes - <t:{timestamp}:R> / <t:{timestamp}:D>\n> due to: **{message}**"

    embed.add_field(name="__ Scheduled Maintenance __", value=maintenance_text, inline=False)

    # Client MS (client's ping)
    client_ping = "N/A"
    if isinstance(ctx.author, discord.Member) and ctx.author.voice and ctx.author.voice.voice_channel:
        client_ping = f"{round(ctx.author.voice.voice_channel.guild.voice_client.average_latency * 1000)}ms"
    embed.add_field(name="__ Client MS __", value=f"```{client_ping}```", inline=False)

    # Known Issues (example placeholder)
    known_issues = "No Known Issues"  # You can replace this with your own issue data
    embed.add_field(name="__ Known Issues __", value=known_issues, inline=False)

    # Footer with user's avatar
    embed.set_footer(text=f"invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)

    # Send the embed message
    await ctx.send(embed=embed)

# File to store custom commands
CUSTOM_CMDS_FILE = "custom_commands.json"


# Load custom commands from file
def load_custom_commands():
    if os.path.exists(CUSTOM_CMDS_FILE):
        with open(CUSTOM_CMDS_FILE, 'r') as f:
            return json.load(f)
    return {}


# Save custom commands to file
def save_custom_commands(commands):
    with open(CUSTOM_CMDS_FILE, 'w') as f:
        json.dump(commands, f)


# Initialize custom commands
custom_commands = load_custom_commands()


class CustomCommandPanel(View):

    def __init__(self):
        super().__init__(timeout=None)

    async def show_success(self, interaction: discord.Interaction,
                           message: str):
        success_embed = Embed(description=f"✅ {message}", color=0x00FF00)
        await interaction.message.edit(embed=success_embed, view=None)

    async def show_error(self, interaction: discord.Interaction, message: str):
        error_embed = Embed(description=f"❌ {message}", color=0xFF0000)
        await interaction.message.edit(embed=error_embed, view=None)

    @discord.ui.button(label="New", style=ButtonStyle.gray)
    async def new_cmd(self, interaction: discord.Interaction, button: Button):
        embed = Embed(
            title="1/2 Create Custom CMD",
            description="Please reply with the name of the trigger words.",
            color=0xFFA500)
        await interaction.response.edit_message(embed=embed, view=None)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            # Get trigger name
            name_msg = await bot.wait_for('message', check=check, timeout=60.0)
            trigger = name_msg.content

            # Delete user's message
            try:
                await name_msg.delete()
            except:
                pass

            # Get response
            embed.title = "2/2 Create Custom CMD"
            embed.description = "Please reply with the response message"
            await interaction.followup.edit_message(interaction.message.id,
                                                    embed=embed)

            response_msg = await bot.wait_for('message',
                                              check=check,
                                              timeout=60.0)
            response = response_msg.content

            # Delete user's message
            try:
                await response_msg.delete()
            except:
                pass

            # Save command
            custom_commands[trigger.lower()] = response
            save_custom_commands(custom_commands)

            await self.show_success(interaction,
                                    f"Created command `{trigger}`")

        except asyncio.TimeoutError:
            await self.show_error(interaction,
                                  "Timed out waiting for response")

    @discord.ui.button(label="Edit", style=ButtonStyle.gray)
    async def edit_cmd(self, interaction: discord.Interaction, button: Button):
        if not custom_commands:
            await self.show_error(interaction,
                                  "No custom commands found to edit")
            return

        options = [
            SelectOption(label=name, value=name)
            for name in custom_commands.keys()
        ]

        select = Select(placeholder="Choose command to edit", options=options)
        view = View()
        view.add_item(select)

        embed = Embed(title="Edit Custom CMD's",
                      description="Please choose the command to edit below.",
                      color=0xFFA500)
        await interaction.response.edit_message(embed=embed, view=view)

        async def select_callback(interaction: discord.Interaction):
            selected = select.values[0]
            embed = Embed(title=f"Edit {selected}", color=0xFFA500)

            name_btn = Button(label="Name", style=ButtonStyle.gray)
            response_btn = Button(label="Response", style=ButtonStyle.gray)
            edit_view = View()
            edit_view.add_item(name_btn)
            edit_view.add_item(response_btn)

            await interaction.response.edit_message(embed=embed,
                                                    view=edit_view)

            async def name_callback(interaction: discord.Interaction):
                embed = Embed(
                    title=f"Edit {selected} name",
                    description=
                    f"Current name → `{selected}`\nPlease reply below with the new name.",
                    color=0xFFA500)
                await interaction.response.edit_message(embed=embed, view=None)

                def check(m):
                    return m.author == interaction.user and m.channel == interaction.channel

                try:
                    msg = await bot.wait_for('message',
                                             check=check,
                                             timeout=60.0)
                    new_name = msg.content.lower()

                    try:
                        await msg.delete()
                    except:
                        pass

                    if new_name in custom_commands:
                        await self.show_error(
                            interaction,
                            "Command with this name already exists")
                        return

                    # Update command
                    custom_commands[new_name] = custom_commands.pop(selected)
                    save_custom_commands(custom_commands)

                    await self.show_success(
                        interaction, f"Renamed `{selected}` to `{new_name}`")

                except asyncio.TimeoutError:
                    await self.show_error(interaction,
                                          "Timed out waiting for response")

            async def response_callback(interaction: discord.Interaction):
                embed = Embed(
                    title=f"Edit {selected} response",
                    description=
                    f"Current response → `{custom_commands[selected]}`\nPlease reply below with the new response.",
                    color=0xFFA500)
                await interaction.response.edit_message(embed=embed, view=None)

                def check(m):
                    return m.author == interaction.user and m.channel == interaction.channel

                try:
                    msg = await bot.wait_for('message',
                                             check=check,
                                             timeout=60.0)
                    new_response = msg.content

                    try:
                        await msg.delete()
                    except:
                        pass

                    # Update command
                    custom_commands[selected] = new_response
                    save_custom_commands(custom_commands)

                    await self.show_success(
                        interaction, f"Updated response for `{selected}`")

                except asyncio.TimeoutError:
                    await self.show_error(interaction,
                                          "Timed out waiting for response")

            name_btn.callback = name_callback
            response_btn.callback = response_callback

        select.callback = select_callback

    @discord.ui.button(label="Delete", style=ButtonStyle.gray)
    async def delete_cmd(self, interaction: discord.Interaction,
                         button: Button):
        if not custom_commands:
            await self.show_error(interaction,
                                  "No custom commands found to delete")
            return

        options = [
            SelectOption(label=name, value=name)
            for name in custom_commands.keys()
        ]

        select = Select(placeholder="Choose command to delete",
                        options=options)
        view = View()
        view.add_item(select)

        embed = Embed(title="Delete Custom CMD",
                      description="Choose what CMD to delete",
                      color=0xFFA500)
        await interaction.response.edit_message(embed=embed, view=view)

        async def select_callback(interaction: discord.Interaction):
            selected = select.values[0]
            del custom_commands[selected]
            save_custom_commands(custom_commands)

            await self.show_success(interaction,
                                    f"Deleted command `{selected}`")

        select.callback = select_callback


@bot.command(name='custom')
async def custom_cmd(ctx):
    """Custom command management panel"""
    embed = Embed(
        title="Custom Command Panel",
        description=
        "Here you'll be able to create/edit/delete custom trigger words.\nChoose a category below",
        color=0xFFA500)
    embed.set_footer(text=f"Invoked by {ctx.author}",
                     icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed, view=CustomCommandPanel())


# Handle custom commands
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check for custom commands
    content = message.content.lower()
    if content in custom_commands:
        await message.delete()
        await message.channel.send(custom_commands[content])

    await bot.process_commands(message)

@bot.event
async def on_command_completion(ctx):
    """Log completed commands for admin monitoring"""
    global command_logs
    
    log_entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'command': ctx.command.name if ctx.command else 'unknown',
        'user_id': str(ctx.author.id),
        'username': str(ctx.author),
        'channel': str(ctx.channel),
        'guild': str(ctx.guild.name) if ctx.guild else 'DM',
        'guild_id': str(ctx.guild.id) if ctx.guild else 'DM',
        'message_content': ctx.message.content[:100]  # First 100 chars for privacy
    }
    
    command_logs.append(log_entry)
    
    # Keep only last 1000 logs to prevent memory issues
    if len(command_logs) > 1000:
        command_logs = command_logs[-1000:]


app = Flask(__name__)


# Basic Flask route to respond to uptime pings
@app.route('/')
def home():
    return "Bot is alive!"


# Your Discord bot code


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


# Run Flask in a separate thread
def run_flask():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))


if __name__ == "__main__":
    # Start Flask server in a background thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()


@bot.command(name='query')
async def query_user(ctx, user: typing.Union[discord.Member, discord.User, int,
                                             str]):
    """Query user information"""
    try:
        # Resolve user from input (supports ID, mention, name)
        if isinstance(user, (int, str)):
            try:
                if isinstance(user, int) or user.isdigit():
                    user = await bot.fetch_user(int(user)) if user not in [
                        m.id for m in ctx.guild.members
                    ] else ctx.guild.get_member(int(user))
                else:
                    # Try to find by name
                    user = discord.utils.find(
                        lambda m: user.lower() in m.name.lower(),
                        ctx.guild.members)
                    if not user:
                        raise commands.MemberNotFound(str(user))
            except:
                raise commands.MemberNotFound(str(user))

        # Get member object if available (for guild-specific info)
        member = user if isinstance(user, discord.Member) else None

        # Get invite data if available
        join_method = "UNAVAILABLE"
        if member:
            try:
                invites = await ctx.guild.invites()
                for invite in invites:
                    if invite.uses > 0 and member.joined_at and invite.created_at < member.joined_at:
                        if invite.inviter:
                            join_method = f"Invited by {invite.inviter.mention} ({invite.inviter.id})"
                            break
            except:
                pass

        # Get invite count for verification statusp
        verification_status = "❌"
        if member:
            invite_count = await count_invites(ctx.guild, member)
            if 1308045059756654653 in [r.id for r in member.roles]:
                verification_status = "✅"
            elif invite_count >= 1:
                verification_status = "PENDING"

        # Create embed
        embed = discord.Embed(
            title="__Query Result__",
            color=0xFFA500  # Orange
        )

        # User info with requested spacing
        embed.add_field(
            name="\u200b",
            value=f"**{user.mention}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"> User ID → `{user.id}`\n"
            f"> Server Name → `{getattr(member, 'display_name', 'N/A (not in server)')}`",
            inline=False)

        # Timestamps with F format and spacing
        creation_timestamp = int(user.created_at.timestamp())
        embed.add_field(
            name="\u200b",
            value=f"> Account Created → <t:{creation_timestamp}:F>\n"
            f"> Server Joined → {f'<t:{int(member.joined_at.timestamp())}:F>' if member else 'N/A (not in server)'}",
            inline=False)

        # Status info
        embed.add_field(
            name="\u200b",
            value=f"> Join Method → {join_method}\n"
            f"> Blacklist Status → {'✅' if member and 1393399872912363600 in [r.id for r in member.roles] else '❌'}\n"
            f"> Verification Status → {verification_status}",
            inline=False)

        # Footer with invoker info
        embed.set_footer(text=f" invoked by {ctx.author}",
                         icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    except commands.MemberNotFound:
        error_embed = discord.Embed(
            description=
            "❌ User not found. Try with ID, mention, or exact name.",
            color=0xFF0000)
        await ctx.send(embed=error_embed, delete_after=10)
    except Exception as e:
        error_embed = discord.Embed(description=f"❌ Error: {str(e)}",
                                    color=0xFF0000)
        await ctx.send(embed=error_embed, delete_after=10)


@bot.command(name='an')
async def announce_scrims(ctx, time: str, mode: str):
    """Announce scrims with start time
    Usage: $an early/late solo/duo/trio
    Example: $an early duos
    """
    # Normalize inputs
    time = time.lower()
    mode = mode.lower()

    # Validate inputs
    valid_times = ['early', 'late']
    valid_modes = ['solo', 'duo', 'trio', 'solos', 'duos', 'trios']

    if time not in valid_times:
        await ctx.send("Invalid time. Use 'early' or 'late'")
        return

    if mode not in valid_modes:
        await ctx.send(
            "Invalid mode. Use 'solo', 'duo', or 'trio' (plural accepted)")
        return

    # Clean up mode to singular form
    if mode.endswith('s'):
        mode = mode[:-1]

    # Get current date in CEST
    now = datetime.now()
    cest = pytz.timezone('Europe/Paris')  # CEST is same as Paris time
    now_cest = now.astimezone(cest)

    # Determine the hour and minute based on mode and time
    if mode == 'solo':
        if time == 'early':
            hour, minute = 13, 0  # 1:00 PM CEST
        else:  # late
            hour, minute = 14, 30  # 2:30 PM CEST
    elif mode == 'duo':
        if time == 'early':
            hour, minute = 13, 10  # 1:10 PM CEST
        else:  # late
            hour, minute = 14, 40  # 2:40 PM CEST
    elif mode == 'trio':
        if time == 'early':
            hour, minute = 13, 20  # 1:20 PM CEST
        else:  # late
            hour, minute = 14, 50  # 2:50 PM CEST

    # Create datetime object for the start time
    start_time = now_cest.replace(hour=hour,
                                  minute=minute,
                                  second=0,
                                  microsecond=0)

    # If the time has already passed today, set it for tomorrow
    if start_time < now_cest:
        start_time += timedelta(days=1)

    # Convert to timestamp for Discord's format
    timestamp = int(start_time.timestamp())

    # Create the announcement message with exact formatting
    message = (
        "```\n<@&854727975550320650>\n\n"
        f"<:ArrowRight:1398394460941062327> The **First Match** is @ <t:{timestamp}:t> ~ <t:{timestamp}:R>!\n\n"
        "• Please read the #scrim-rules before playing. :trophy:\n"
        "```")

    await ctx.send(message)


@bot.command(name='conclude')
async def conclude_scrims(ctx, time: str, mode: str):
    """Conclude scrims and show resume time
    Usage: $conclude early/late solo/duo/trio
    Example: $conclude late trios
    """
    # Normalize inputs
    time = time.lower()
    mode = mode.lower()

    # Validate inputs
    valid_times = ['early', 'late']
    valid_modes = ['solo', 'duo', 'trio', 'solos', 'duos', 'trios']

    if time not in valid_times:
        await ctx.send("Invalid time. Use 'early' or 'late'")
        return

    if mode not in valid_modes:
        await ctx.send(
            "Invalid mode. Use 'solo', 'duo', or 'trio' (plural accepted)")
        return

    # Clean up mode to singular form
    if mode.endswith('s'):
        mode = mode[:-1]

    # Get current date in CEST
    now = datetime.now()
    cest = pytz.timezone('Europe/Paris')  # CEST is same as Paris time
    now_cest = now.astimezone(cest)

    # Determine the hour and minute based on mode and time
    if mode == 'solo':
        if time == 'early':
            hour, minute = 13, 0  # 1:00 PM CEST
        else:  # late
            hour, minute = 14, 30  # 2:30 PM CEST
    elif mode == 'duo':
        if time == 'early':
            hour, minute = 13, 10  # 1:10 PM CEST
        else:  # late
            hour, minute = 14, 40  # 2:40 PM CEST
    elif mode == 'trio':
        if time == 'early':
            hour, minute = 13, 20  # 1:20 PM CEST
        else:  # late
            hour, minute = 14, 50  # 2:50 PM CEST

    # Create datetime object for the resume time
    resume_time = now_cest.replace(hour=hour,
                                   minute=minute,
                                   second=0,
                                   microsecond=0)

    # If the time has already passed today, set it for tomorrow
    if resume_time < now_cest:
        resume_time += timedelta(days=1)

    # Convert to timestamp for Discord's <t:...:t> format
    timestamp = int(resume_time.timestamp())

    # Capitalize the mode for display
    display_mode = mode.capitalize() + ('s' if mode != 'solo' else ''
                                        )  # "Solo" vs "Duos"/"Trios"

    # Create and send the message
    message = (
        f"```**The {display_mode} Scrims have __concluded__!**\n\n"
        f"<:ArrowRight:1398394460941062327> Games will resume **at <t:{timestamp}:t>** :heartcartoon:\n\n"
        "• Make sure to invite your friends over, https://discord.gg/EU```")

    await ctx.send(message)


# Invite Setup System Classes and Commands
class InviteSetupView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Post Check",
                       style=discord.ButtonStyle.gray,
                       custom_id="post_check_button")
    async def post_check_button(self, interaction: discord.Interaction,
                                button: discord.ui.Button):
        # Delete the original message
        await interaction.message.delete()

        # Ask for channel input
        embed = discord.Embed(
            description=
            "Select Channel\nPlease type the channel where the message should be posted",
            color=0x808080  # Gray
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Wait for user's channel response
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            channel_msg = await bot.wait_for('message',
                                             check=check,
                                             timeout=60.0)
            channel_input = channel_msg.content

            # Try to parse channel
            try:
                # Try to get channel by mention
                if channel_input.startswith('<#') and channel_input.endswith(
                        '>'):
                    channel_id = int(channel_input[2:-1])
                    channel = interaction.guild.get_channel(channel_id)
                # Try to get channel by ID
                elif channel_input.isdigit():
                    channel = interaction.guild.get_channel(int(channel_input))
                else:
                    await interaction.followup.send(
                        "Invalid channel format. Please use channel mention or ID.",
                        ephemeral=True)
                    return

                if not channel:
                    raise ValueError("Channel not found")

                # Create the invite check message
                embed = discord.Embed(
                    title="Invites Check",
                    description=
                    "Please press the button to check your invites, if you have enough invites to pass verification you will get the Verified role.",
                    color=0xFFA500  # Orange
                )

                view = CheckInvitesView()
                message = await channel.send(embed=embed, view=view)

                # Send success message
                success_embed = discord.Embed(
                    description=
                    f"✅ Message successfully posted in {channel.mention}\n[Go to message]({message.jump_url})",
                    color=0x00FF00  # Green
                )
                await interaction.followup.send(embed=success_embed,
                                                ephemeral=True)

            except Exception as e:
                error_embed = discord.Embed(
                    description=f"❌ Error: {str(e)}",
                    color=0xFF0000  # Red
                )
                await interaction.followup.send(embed=error_embed,
                                                ephemeral=True)

        except asyncio.TimeoutError:
            await interaction.followup.send(
                "Timed out waiting for channel input.", ephemeral=True)


class CheckInvitesView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Check",
                       style=discord.ButtonStyle.gray,
                       custom_id="check_invites_button")
    async def check_invites_button(self, interaction: discord.Interaction,
                                   button: discord.ui.Button):
        # Count the user's invites
        invite_count = await count_invites(interaction.guild, interaction.user)
        verified_role_id = 1308045059756654653
        verified_role = interaction.guild.get_role(verified_role_id)

        if invite_count >= 1:
            # Give verified role if they have enough invites
            try:
                if verified_role and verified_role not in interaction.user.roles:
                    await interaction.user.add_roles(verified_role)

                response = f"{interaction.user.mention}, you have {invite_count} invites. You will soon get the role"
            except Exception as e:
                response = f"{interaction.user.mention}, you have {invite_count} invites. (Failed to assign role: {str(e)})"
        else:
            response = f"{interaction.user.mention}, you have {invite_count} invites."

        await interaction.response.send_message(response, ephemeral=True)


@bot.command(name='invsetup')
@commands.has_permissions(administrator=True)
async def invite_setup(ctx):
    """Setup the invite check system"""
    embed = discord.Embed(
        title="Invite Check Admin Panel",
        description="Please select one of the following actions:",
        color=0xFFA500  # Orange
    )
    embed.set_footer(
        text=
        f"Invoked by {ctx.author} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    view = InviteSetupView()
    await ctx.send(embed=embed, view=view)


@bot.group(name='invites', invoke_without_command=True)
async def invites(ctx,
                  user: typing.Optional[typing.Union[discord.Member,
                                                     int]] = None):
    """Check invite counts for yourself or others (Management only)"""
    # Check if user is specified and if the author has Management role
    management_role = ctx.guild.get_role(1315714615396794480)

    if user is not None:
        if management_role not in ctx.author.roles:
            await ctx.send(
                "❌ You need the Management role to check others' invites!")
            return

        if isinstance(user, int):
            user = ctx.guild.get_member(user)
            if user is None:
                await ctx.send("❌ User not found!")
                return

        # Format for checking others' invites
        title = f"**{user.display_name}**"
        description = f"Currently has **{await count_invites(ctx.guild, user)}** invites"
    else:
        user = ctx.author
        # Format for checking own invites
        title = f"**{user.display_name}**"
        description = f"You currently have **{await count_invites(ctx.guild, user)}** invites"

    embed = discord.Embed(
        title=title,
        description=description,
        color=0xFFA500  # Orange
    )
    await ctx.send(embed=embed)


async def count_invites(guild, user):
    """Helper function to count invites for a user"""
    try:
        invites = await guild.invites()
        return sum(invite.uses for invite in invites
                   if invite.inviter and invite.inviter.id == user.id)
    except discord.Forbidden:
        return 0


@invites.command(name='leaderboard')
async def invites_leaderboard(ctx):
    """Show the invites leaderboard"""
    try:
        invites = await ctx.guild.invites()
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to view invites!")
        return

    # Create a dictionary to count invites per user
    invite_counts = {}
    for invite in invites:
        if invite.inviter:
            if invite.inviter.id in invite_counts:
                invite_counts[invite.inviter.id] += invite.uses
            else:
                invite_counts[invite.inviter.id] = invite.uses

    # Sort users by invite count
    sorted_invites = sorted(invite_counts.items(),
                            key=lambda x: x[1],
                            reverse=True)

    # Create leaderboard embed
    embed = discord.Embed(
        title="**Invites Leaderboard**",
        color=0xFFA500  # Orange
    )

    leaderboard = []
    for position, (user_id, count) in enumerate(sorted_invites[:10], start=1):
        user = ctx.guild.get_member(user_id)
        if user:
            leaderboard.append(
                f"{position}. **{user.display_name}** - {count} invites")

    if leaderboard:
        embed.description = "\n".join(leaderboard)
    else:
        embed.description = "No invite data available"

    await ctx.send(embed=embed)


@bot.group(name='list', invoke_without_command=True)
async def list_group(ctx):
    """List server members or roles"""
    await ctx.send("Available subcommands:\n"
                   "• `$list members` - List all server members\n"
                   "• `$list roles` - List all server roles")


@list_group.command(name='members')
async def list_members(ctx):
    """List all server members"""
    embed = discord.Embed(
        title="__**Member List**__",
        color=0xFFA500  # Orange
    )

    members_list = []
    for member in ctx.guild.members:
        members_list.append(f"• {member.mention} - `{member.id}`")

    # Split into chunks if too long
    if len(members_list) > 0:
        chunks = [
            members_list[i:i + 20] for i in range(0, len(members_list), 20)
        ]
        for chunk in chunks:
            embed.add_field(name="\u200b",
                            value="\n".join(chunk),
                            inline=False)
    else:
        embed.description = "No members found"

    embed.set_footer(text=f"Total members: {len(ctx.guild.members)}")
    await ctx.send(embed=embed)


@list_group.command(name='roles')
async def list_roles(ctx):
    """List all server roles"""
    embed = discord.Embed(
        title="__**Role List**__",
        color=0xFFA500  # Orange
    )

    roles_list = []
    for role in sorted(ctx.guild.roles, key=lambda r: r.position,
                       reverse=True):
        if role.name != "@everyone":
            color_hex = f"#{role.color.value:06x}" if role.color.value != 0 else "#000000"
            roles_list.append(
                f"• {role.mention} - `{role.id}` / {color_hex} - ({len(role.members)} members)"
            )

    # Split into chunks if too long
    if len(roles_list) > 0:
        chunks = [roles_list[i:i + 10] for i in range(0, len(roles_list), 10)]
        for chunk in chunks:
            embed.add_field(name="\u200b",
                            value="\n".join(chunk),
                            inline=False)
    else:
        embed.description = "No roles found"

    embed.set_footer(
        text=f"Total roles: {len(ctx.guild.roles) - 1}")  # Excluding @everyone
    await ctx.send(embed=embed)


@bot.command(name='checkrole')
async def check_role(ctx, role: discord.Role):
    """Check details about a specific role"""
    color_hex = f"#{role.color.value:06x}" if role.color.value != 0 else "#000000"

    embed = discord.Embed(
        title="__**Role Checkup**__",
        description=
        f"`role color = {color_hex}` - `members = {len(role.members)}`",
        color=0xFFA500)

    # List members with this role
    members_list = []
    for member in role.members:
        members_list.append(f"• {member.mention} - `{member.id}`")

    if members_list:
        chunks = [
            members_list[i:i + 20] for i in range(0, len(members_list), 20)
        ]
        for chunk in chunks:
            embed.add_field(name="Members with this role",
                            value="\n".join(chunk),
                            inline=False)
    else:
        embed.add_field(name="Members with this role",
                        value="No members have this role",
                        inline=False)

    # Create view with buttons
    view = View()

    # Add User button
    async def add_user_callback(interaction):
        if interaction.user != ctx.author:
            return await interaction.response.send_message(
                "You didn't run this command!", ephemeral=True)

        modal = AddUserModal(role)
        await interaction.response.send_modal(modal)

    add_button = Button(label="Add User", style=ButtonStyle.green)
    add_button.callback = add_user_callback
    view.add_item(add_button)

    # Remove User button
    async def remove_user_callback(interaction):
        if interaction.user != ctx.author:
            return await interaction.response.send_message(
                "You didn't run this command!", ephemeral=True)

        if not role.members:
            return await interaction.response.send_message(
                "No members to remove!", ephemeral=True)

        options = [
            discord.SelectOption(label=member.display_name,
                                 value=str(member.id))
            for member in role.members
        ]

        select = Select(placeholder="Select member to remove", options=options)

        async def select_callback(interaction):
            member_id = int(select.values[0])
            member = ctx.guild.get_member(member_id)
            try:
                await member.remove_roles(role)
                await interaction.response.send_message(
                    f"Removed {role.name} from {member.mention}",
                    ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(
                    f"Failed to remove role: {e}", ephemeral=True)

        select.callback = select_callback
        remove_view = View()
        remove_view.add_item(select)
        await interaction.response.send_message(
            "Select member to remove role from:",
            view=remove_view,
            ephemeral=True)

    remove_button = Button(label="Remove User", style=ButtonStyle.red)
    remove_button.callback = remove_user_callback
    view.add_item(remove_button)

    await ctx.send(embed=embed, view=view)


class AddUserModal(discord.ui.Modal):

    def __init__(self, role):
        super().__init__(title=f"Add User to {role.name}")
        self.role = role

        self.user_input = discord.ui.TextInput(
            label="User ID or Mention",
            placeholder="Enter user ID or mention",
            required=True)
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_input = self.user_input.value
            # Try to get member by ID
            try:
                user_id = int(user_input)
                member = interaction.guild.get_member(user_id)
            except ValueError:
                # Try to get member by mention
                if user_input.startswith('<@') and user_input.endswith('>'):
                    user_id = int(user_input[2:-1].replace('!', ''))
                    member = interaction.guild.get_member(user_id)
                else:
                    member = None

            if not member:
                return await interaction.response.send_message(
                    "User not found!", ephemeral=True)

            await member.add_roles(self.role)
            await interaction.response.send_message(
                f"Added {self.role.name} to {member.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to add role: {e}",
                                                    ephemeral=True)


@bot.command(name='av', aliases=['avatar'])
async def avatar(ctx, user: Optional[discord.User] = None):
    """Show a user's avatar in an embed"""
    target = user or ctx.author

    # Get avatar URL (supports animated avatars)
    avatar_url = target.display_avatar.with_size(1024).url

    # Create embed
    embed = discord.Embed(
        title=f"{target.name}'s Avatar",
        color=0x2b2d31  # Discord dark theme color
    )
    embed.set_image(url=avatar_url)
    embed.set_footer(text=f"Requested by {ctx.author}",
                     icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)


@bot.command(name='cancel')
@commands.has_permissions(manage_messages=True)
async def cancel_session(ctx, message_id: int, *, reason: str):
    """
    Cancel an announcement with exact formatting
    Usage: $cancel <message_id> <reason>
    Example: $cancel 1234567890 No available hosts
    """
    try:
        # Fetch the original message
        try:
            message = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("Message not found. Check the message ID.",
                           delete_after=10)
            return
        except discord.Forbidden:
            await ctx.send("Don't have permission to edit that message.",
                           delete_after=10)
            return

        # Edit the message with exact formatting
        cancelled_content = (f"~~{message.content}~~\n\n"
                             f"CANCELLED: {reason}")

        # Preserve the original embed if it exists
        original_embed = message.embeds[0] if message.embeds else None

        await message.edit(
            content=cancelled_content,
            embed=original_embed  # Keep original embed unchanged
        )

        # Remove all reactions if any exist
        try:
            await message.clear_reactions()
        except:
            pass

        # Send confirmation (will auto-delete)
        await ctx.send(f"Announcement {message_id} has been cancelled.",
                       delete_after=5)

    except Exception as e:
        await ctx.send(f"Error cancelling announcement: {str(e)}",
                       delete_after=10)


@bot.command(name='announce')
@commands.has_permissions(manage_messages=True)
async def announce_session(ctx, time_input: str, *, args: str = None):
    """
    Create tournament announcement with exact host formatting
    Usage: $announce HH:MM @user1 @user2 [lobby name/number]
    Examples: 
    $announce 19:30 @Gloryy @User2 @User3 @User4
    $announce 19:30 @Gloryy Lobby 3
    """
    try:
        # Parse time input
        try:
            time_obj = datetime.strptime(time_input, "%H:%M")
        except ValueError:
            await ctx.send("Invalid time format. Use HH:MM (24h format)",
                           delete_after=5)
            return

        # Separate users and lobby info from args
        users = []
        lobby_info = None

        if args:
            # Split the args into parts
            parts = args.split()

            # Process mentions first
            for part in parts:
                if part.startswith('<@') and part.endswith('>'):
                    # This is a mention, try to get the member
                    user_id = part[2:-1].replace(
                        '!', '')  # Remove <@ and >, and ! if present
                    try:
                        user = await commands.MemberConverter().convert(
                            ctx, user_id)
                        users.append(user)
                    except:
                        continue
                else:
                    # Once we hit non-mention text, treat the rest as lobby info
                    lobby_start = parts.index(part)
                    lobby_info = ' '.join(parts[lobby_start:])
                    break

        # Verify at least one host
        if not users:
            await ctx.send("Please mention at least one host", delete_after=5)
            return

        # Calculate timestamps
        now = datetime.now()
        registration_time = now.replace(hour=time_obj.hour,
                                        minute=time_obj.minute,
                                        second=0)
        if registration_time < now:
            registration_time += timedelta(days=1)

        game_start_time = registration_time + timedelta(minutes=30)

        # Format Discord timestamps
        reg_timestamp = int(registration_time.timestamp())
        game_timestamp = int(game_start_time.timestamp())

        # Format user mentions EXACTLY as specified
        if len(users) == 1:
            hosts_text = users[0].mention
        elif len(users) == 2:
            hosts_text = f"{users[0].mention} & {users[1].mention}"
        else:
            # For 3+ hosts: "1, 2, 3 & 4"
            hosts_text = ", ".join(user.mention for user in users[:-1])
            hosts_text += f" & {users[-1].mention}"

        # Create the announcement message with optional lobby info
        announcement_msg = (
            f"@everyone\n\n"
            f"**Fortnite Tournament**{f' {lobby_info}' if lobby_info else ''}\n\n"
            f"> **Registration opens <t:{reg_timestamp}:t>**\n\n"
            f"> **First Game Commences <t:{game_timestamp}:t>**\n\n"
            f" The hosts for this session are: {hosts_text} , Direct Message them for help.\n\n"
            f"• Session lasts 3 Games. **Miss a single game and you will be banned.**\n"
            f"• Required at least **110+ Reacts**")

        # Send the announcement
        message = await ctx.send(announcement_msg)

        # Add reaction emoji
        try:
            await message.add_reaction("✋")
        except:
            pass

        # Delete the command message
        try:
            await ctx.message.delete()
        except:
            pass

    except Exception as e:
        await ctx.send(f"Error creating announcement: {str(e)}",
                       delete_after=10)


@bot.command(name='ghost')
@commands.has_permissions(manage_messages=True)
async def ghost_ping(ctx, user: discord.Member, amount: int = 20):
    """
    Ghost ping a user X times (default: 20)
    Usage: $ghost @user [amount]
    """
    # Validate amount
    if amount < 1:
        await ctx.send("Amount must be at least 1", delete_after=3)
        return
    if amount > 50:  # Safety limit
        amount = 50
        await ctx.send("Capped at 50 pings for safety", delete_after=3)

    try:
        # Delete command message
        await ctx.message.delete()
    except:
        pass

    # Send confirmation that will self-destruct
    confirm = await ctx.send(
        f"Ghost pinging {user.mention} {amount} times... (this will self-destruct)",
        delete_after=3)

    # Send and delete pings
    successful_pings = 0
    for i in range(amount):
        try:
            # Random slight delay to avoid detection (0.1-0.5s)
            await asyncio.sleep(random.uniform(0.1, 0.5))

            msg = await ctx.send(user.mention)
            await msg.delete()
            successful_pings += 1
        except Exception as e:
            continue

    # Optional: Send final report that self-destructs
    if successful_pings > 0:
        report = await ctx.send(
            f"Successfully ghost pinged {user.mention} {successful_pings}/{amount} times (this will self-destruct)",
            delete_after=3)


class TicketCreationView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket",
                       style=discord.ButtonStyle.green,
                       custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction,
                            button: Button):
        # Check if user already has an open ticket
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        for channel in category.channels:
            if isinstance(
                    channel, discord.TextChannel
            ) and f"support-{interaction.user.name.lower()}" in channel.name.lower(
            ):
                await interaction.response.send_message(
                    f"You already have an open ticket: {channel.mention}",
                    ephemeral=True)
                return

        # Generate random 5-digit number
        random_number = random.randint(10000, 99999)

        # Create clean username for channel name (discord's channel name requirements)
        clean_username = ''.join(c for c in interaction.user.name.lower()
                                 if c.isalnum() or c in ('-', '_'))
        clean_username = clean_username[:20]  # Limit length

        # Create ticket channel name
        channel_name = f"support-{clean_username}-{random_number}"

        # Create overwrites
        overwrites = {
            interaction.guild.default_role:
            discord.PermissionOverwrite(read_messages=False),
            interaction.user:
            discord.PermissionOverwrite(read_messages=True,
                                        send_messages=True),
            interaction.guild.me:
            discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Add support role if it exists
        support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True)

        # Create the channel
        try:
            ticket_channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                reason=f"Ticket created by {interaction.user}")
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Failed to create ticket channel: {str(e)}", ephemeral=True)
            return

        # Send initial message
        embed = discord.Embed(
            title=f"Support Ticket - {interaction.user}",
            description=
            ("Support will be with you shortly. Please describe your issue.\n\n"
             "**Ticket Info:**\n"
             f"- User: {interaction.user.mention}\n"
             f"- Created: <t:{int(datetime.now().timestamp())}:F>\n"
             f"- Ticket ID: {random_number}"),
            color=0x00FF00)

        view = TicketManagementView()
        await ticket_channel.send(
            content=
            f"{interaction.user.mention} {support_role.mention if support_role else ''}",
            embed=embed,
            view=view)

        await interaction.response.send_message(
            f"Ticket created: {ticket_channel.mention}", ephemeral=True)


class TicketManagementView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket",
                       style=discord.ButtonStyle.red,
                       custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction,
                           button: Button):
        # Remove user's access to the channel
        for user in interaction.channel.overwrites:
            if isinstance(user,
                          discord.Member) and user != interaction.guild.me:
                await interaction.channel.set_permissions(user,
                                                          read_messages=False,
                                                          send_messages=False)

        # Disable the button
        button.disabled = True
        button.label = "Ticket Closed"
        button.style = discord.ButtonStyle.grey

        await interaction.response.edit_message(view=self)

        embed = discord.Embed(
            title="Ticket Closed",
            description=f"This ticket was closed by {interaction.user.mention}",
            color=0xFF0000)
        await interaction.channel.send(embed=embed)

    @discord.ui.button(label="Delete Ticket",
                       style=discord.ButtonStyle.danger,
                       custom_id="delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction,
                            button: Button):
        if not any(role.id == SUPPORT_ROLE_ID
                   for role in interaction.user.roles):
            await interaction.response.send_message(
                "Only support staff can delete tickets.", ephemeral=True)
            return

        await interaction.response.send_message(
            "Deleting this ticket in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete(
            reason=f"Ticket deleted by {interaction.user}")


class TicketModal(Modal):

    def __init__(self, channel: discord.TextChannel):
        super().__init__(title="Edit Ticket")
        self.channel = channel
        self.name = TextInput(label="New Channel Name",
                              placeholder="Enter new channel name...",
                              default=channel.name,
                              required=True)
        self.topic = TextInput(label="New Channel Topic",
                               placeholder="Enter new channel topic...",
                               default=channel.topic or "",
                               style=discord.TextStyle.long,
                               required=False)
        self.add_item(self.name)
        self.add_item(self.topic)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.channel.edit(
                name=self.name.value,
                topic=self.topic.value,
                reason=f"Ticket edited by {interaction.user}")
            await interaction.response.send_message(
                "Ticket updated successfully!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"Failed to update ticket: {str(e)}", ephemeral=True)


@bot.command(name="ticketsetup")
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    """Setup the ticket system in this channel"""
    embed = discord.Embed(
        title="Support Tickets",
        description="Click the button below to create a new support ticket",
        color=0x00FF00)

    await ctx.send(embed=embed, view=TicketCreationView())
    await ctx.message.delete()


@bot.command(name="ticket")
async def ticket_command(ctx):
    """Create a support ticket"""
    # This just directs users to use the button
    await ctx.send(
        "Please use the ticket button in the support channel to create a ticket."
    )


@bot.command(name="editticket")
@commands.has_permissions(manage_channels=True)
async def edit_ticket(ctx):
    """Edit the current ticket's name and topic"""
    if not ctx.channel.name.startswith("ticket-"):
        await ctx.send("This is not a ticket channel!")
        return

    modal = TicketModal(ctx.channel)
    await ctx.interaction.response.send_modal(modal)


@bot.command(name="adduser")
@commands.has_permissions(manage_channels=True)
async def add_to_ticket(ctx, member: discord.Member):
    """Add a user to the current ticket"""
    if not ctx.channel.name.startswith("ticket-"):
        await ctx.send("This is not a ticket channel!")
        return

    await ctx.channel.set_permissions(member,
                                      read_messages=True,
                                      send_messages=True)

    await ctx.send(f"Added {member.mention} to this ticket")


@bot.command(name="removeuser")
@commands.has_permissions(manage_channels=True)
async def remove_from_ticket(ctx, member: discord.Member):
    """Remove a user from the current ticket"""
    if not ctx.channel.name.startswith("ticket-"):
        await ctx.send("This is not a ticket channel!")
        return

    await ctx.channel.set_permissions(member, overwrite=None)

    await ctx.send(f"Removed {member.mention} from this ticket")


@bot.command(name="closeticket")
async def close_ticket(ctx):
    """Close the current ticket"""
    if not ctx.channel.name.startswith("ticket-"):
        await ctx.send("This is not a ticket channel!")
        return

    # Find the close button in the ticket's first message
    async for message in ctx.channel.history(limit=1, oldest_first=True):
        if message.components:  # If the message has components (buttons)
            for component in message.components:
                if isinstance(
                        component,
                        Button) and component.custom_id == "close_ticket":
                    # Simulate clicking the close button
                    view = TicketManagementView()
                    await view.close_ticket(ctx.interaction, component)
                    return

    # If no button found, close manually
    for user in ctx.channel.overwrites:
        if isinstance(user, discord.Member) and user != ctx.guild.me:
            await ctx.channel.set_permissions(user,
                                              read_messages=False,
                                              send_messages=False)

    embed = discord.Embed(
        title="Ticket Closed",
        description=f"This ticket was closed by {ctx.author.mention}",
        color=0xFF0000)
    await ctx.send(embed=embed)


@bot.command(name="deleteticket")
@commands.has_permissions(manage_channels=True)
async def delete_ticket(ctx):
    """Delete the current ticket (staff only)"""
    if not ctx.channel.name.startswith("ticket-"):
        await ctx.send("This is not a ticket channel!")
        return

    await ctx.send("Deleting this ticket in 5 seconds...")
    await asyncio.sleep(5)
    await ctx.channel.delete(reason=f"Ticket deleted by {ctx.author}")


@bot.command(name='status')
@commands.has_permissions(administrator=True)
async def set_status(ctx, activity_type: str = "playing", *, message: str):
    """Change the bot's status with different activity types
    Usage: $status <type> <message>
    Types: playing|streaming|listening|watching|competing"""

    # Convert activity type
    activity_types = {
        "playing":
        discord.Game(name=message),
        "streaming":
        discord.Streaming(name=message, url="https://twitch.tv/yourchannel"),
        "listening":
        discord.Activity(type=discord.ActivityType.listening, name=message),
        "watching":
        discord.Activity(type=discord.ActivityType.watching, name=message),
        "competing":
        discord.Activity(type=discord.ActivityType.competing, name=message)
    }

    try:
        activity = activity_types.get(activity_type.lower(),
                                      discord.Game(name=message))
        await bot.change_presence(activity=activity)

        embed = discord.Embed(
            title="✅ Status Updated",
            description=f"Now {activity_type.lower()} **{message}**",
            color=0x00FF00)
        await ctx.send(embed=embed)

    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Status Update Failed",
            description=
            f"```{str(e)}```\nValid types: playing, streaming, listening, watching, competing",
            color=0xFF0000)
        await ctx.send(embed=error_embed)


@bot.command(name='gloryy')
async def gloryy_command(ctx):
    """Displays info about Gloryy"""
    embed = discord.Embed(
        title="Who's Gloryy?",
        description="Gloryy is a random guy from Germany, he's really chill!",
        color=0x1a9f1a  # Green color
    )
    await ctx.send(embed=embed)


@bot.command(name='say')
@commands.has_permissions(manage_messages=True)
async def say_command(ctx, channel: typing.Optional[discord.TextChannel], *,
                      message: str):
    """Make the bot repeat your message in a specific channel
    Usage: $say <#channel> <message> or $say <message>"""
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    target = channel or ctx.channel
    await target.send(message)


@bot.group(name='editrole', invoke_without_command=True)
async def editrole(ctx):
    """Role editing commands"""
    await ctx.send(
        "Available subcommands:\n"
        "• `$editrole name <role> <newname>` - Rename a role\n"
        "• `$editrole color <role> <color>` - Change a role's color\n"
        "• `$editrole new <name> [color]` - Create a new role\n"
        "• `$editrole del <role>` - Delete a role")


@editrole.command(name='color')
async def change_role_color(ctx, role: typing.Union[discord.Role, int],
                            color: discord.Color):
    """Change a role's color
    Examples:
    $editrole color @Moderator #FF0000
    $editrole color 123456789 0x00FF00
    $editrole color Admin discord.Color.blue()
    """
    if isinstance(role, int):
        role = ctx.guild.get_role(role)
        if role is None:
            await ctx.send("❌ Role not found")
            return

    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("❌ I don't have permission to manage roles")
        return

    if role.position >= ctx.guild.me.top_role.position:
        await ctx.send("❌ I can't modify this role (hierarchy)")
        return

    try:
        old_color = role.color
        await role.edit(color=color)
        embed = discord.Embed(
            title="✅ Role Color Changed",
            description=f"Changed color for role {role.mention}",
            color=color)
        embed.add_field(name="Old Color", value=str(old_color))
        embed.add_field(name="New Color", value=str(color))
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to change role color: {str(e)}")


@editrole.command(name='name')
async def rename_role(ctx, role: typing.Union[discord.Role, int], *,
                      new_name: str):
    """Rename an existing role"""
    if isinstance(role, int):
        role = ctx.guild.get_role(role)
        if role is None:
            await ctx.send("❌ Role not found")
            return

    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("❌ I don't have permission to manage roles")
        return

    if role.position >= ctx.guild.me.top_role.position:
        await ctx.send("❌ I can't modify this role (hierarchy)")
        return

    try:
        old_name = role.name
        await role.edit(name=new_name)
        embed = discord.Embed(
            title="✅ Role Renamed",
            description=f"Changed role name from `{old_name}` to `{new_name}`",
            color=0x00FF00)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to rename role: {str(e)}")


@editrole.command(name='new')
async def create_role(ctx,
                      name: str,
                      color: typing.Optional[discord.Color] = None):
    """Create a new role with optional color
    Example:
    $editrole new Moderator
    $editrole new VIP #FF0000
    $editrole new Admin 0x00FF00
    $editrole new Staff discord.Color.blue()"""
    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("❌ I don't have permission to manage roles")
        return

    try:
        # Create role with optional color
        role = await ctx.guild.create_role(name=name, color=color)

        embed = discord.Embed(title="✅ Role Created",
                              description=f"Created new role: {role.mention}",
                              color=role.color if color else 0x00FF00)
        if color:
            embed.add_field(name="Color", value=str(color))
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to create role: {str(e)}")


@editrole.command(name='del')
async def delete_role(ctx, role: typing.Union[discord.Role, int]):
    """Delete a role"""
    if isinstance(role, int):
        role = ctx.guild.get_role(role)
        if role is None:
            await ctx.send("❌ Role not found")
            return

    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("❌ I don't have permission to manage roles")
        return

    if role.position >= ctx.guild.me.top_role.position:
        await ctx.send("❌ I can't delete this role (hierarchy)")
        return

    try:
        role_name = role.name
        await role.delete()
        embed = discord.Embed(title="✅ Role Deleted",
                              description=f"Deleted role: `{role_name}`",
                              color=0x00FF00)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Failed to delete role: {str(e)}")


@bot.command(name='role')
async def role_command(ctx, user: typing.Union[discord.Member, int], *,
                       role_input: str):
    """Assign or remove a role from a user"""
    # Handle user input
    if isinstance(user, int):
        try:
            user = await ctx.guild.fetch_member(user)
        except discord.NotFound:
            await ctx.send("❌ User not found in this server")
            return

    # Handle role input
    remove_role = role_input.startswith('-')
    role_name_or_id = role_input[1:] if remove_role else role_input

    # Try to get role by ID first
    if role_name_or_id.isdigit():
        role = ctx.guild.get_role(int(role_name_or_id))
    else:
        # Try to get role by mention or name
        if role_name_or_id.startswith('<@&') and role_name_or_id.endswith('>'):
            role_id = int(role_name_or_id[3:-1])
            role = ctx.guild.get_role(role_id)
        else:
            role = discord.utils.get(ctx.guild.roles, name=role_name_or_id)

    if role is None:
        await ctx.send("❌ Role not found in this server")
        return

    # Check bot permissions
    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("❌ I don't have permission to manage roles")
        return

    # Check role hierarchy
    if role.position >= ctx.guild.me.top_role.position:
        await ctx.send("❌ I can't manage this role (hierarchy)")
        return

    try:
        if remove_role:
            if role not in user.roles:
                await ctx.send(
                    f"❌ {user.mention} doesn't have the {role.mention} role")
                return
            await user.remove_roles(role, reason=f"Removed by {ctx.author}")
            action = "removed"
            color = 0xFFA500  # Orange for removal
        else:
            if role in user.roles:
                await ctx.send(
                    f"❌ {user.mention} already has the {role.mention} role")
                return
            await user.add_roles(role, reason=f"Added by {ctx.author}")
            action = "given"
            color = 0x00FF00  # Green for addition

        # Create success embed
        embed = discord.Embed(
            title="✅ Role Assignment",
            description=
            f"Successfully {action} {role.mention} to {user.mention}",
            color=color)
        embed.set_footer(text=f"Action performed by {ctx.author}")

        await ctx.send(embed=embed)

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to manage this role")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")


@bot.command(name='purge')
@commands.has_permissions(
    manage_messages=True)  # Requires message management permissions
async def purge_messages(ctx, amount: int):
    """
    Deletes a specified number of messages in the current channel
    Usage: *purge <number> (max 100 at a time)
    """
    # Validate the amount
    if amount <= 0:
        await ctx.send(
            "Please specify a positive number of messages to delete.",
            delete_after=5)
        return

    # Set a reasonable limit (Discord's API limit is 100)
    if amount > 100:
        amount = 100
        await ctx.send("Maximum purge amount is 100. Deleting 100 messages...",
                       delete_after=3)

    try:
        # Delete the command message first
        await ctx.message.delete()

        # Bulk delete messages
        deleted = await ctx.channel.purge(limit=amount)

        # Send confirmation (will auto-delete)
        confirm = await ctx.send(f"Deleted {len(deleted)} messages.",
                                 delete_after=3)

    except discord.Forbidden:
        await ctx.send("I don't have permissions to delete messages here.",
                       delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"Error deleting messages: {e}", delete_after=5)


@bot.command(name='ping_H')
async def ping_horrible_command(ctx):
    """Returns simulated poor connection metrics"""
    # Simulated poor values
    base_latency = 950
    jitter = random.randint(50, 150)
    packet_loss = random.uniform(8.0, 15.0)

    # Create professional-looking embed
    embed = discord.Embed(
        title="Network Performance Report",
        color=0xFFA500  # Orange color for warning
    )

    # Add technical fields
    embed.add_field(name="Latency",
                    value=f"{base_latency}ms ± {jitter}ms",
                    inline=True)
    embed.add_field(name="Packet Loss",
                    value=f"{packet_loss:.1f}%",
                    inline=True)
    embed.add_field(name="Region", value="EU-West (High Load)", inline=True)

    # Technical issues
    issues = [
        f"Network congestion detected (Load: {random.randint(85, 98)}%)",
        f"Route instability to {random.choice(['AMS', 'FRA', 'PAR'])} backbone",
        "Peering capacity limits reached",
        f"Hardware utilization at {random.randint(90, 100)}% capacity"
    ]

    embed.add_field(name="Identified Issues",
                    value="\n- " + "\n- ".join(issues),
                    inline=False)

    # Status with technical severity
    status_levels = [("Degraded Performance",
                      "Service available with reduced quality"),
                     ("Capacity Warning", "Approaching operational limits"),
                     ("Critical Load", "Immediate attention recommended")]
    status, description = random.choice(status_levels)

    embed.add_field(name=f"Status: {status}", value=description, inline=False)

    # Professional footer
    embed.set_footer(
        text=
        f"Requested by {ctx.author.display_name} | Diagnostic ID: {random.randint(10000, 99999)}"
    )

    await ctx.send(embed=embed)


@bot.command(name='ping')
async def ping_command(ctx):
    """Check the bot's latency and connection status"""
    # Calculate latency in milliseconds
    latency_ms = round(bot.latency * 1000)

    # Create the embed
    embed = discord.Embed(
        title="***__PONG!__***",
        color=0xFFA500  # Orange color
    )

    # Add fields to the embed
    embed.add_field(name="**Current MS**",
                    value=f"{latency_ms}ms",
                    inline=False)
    embed.add_field(name="**Ping**", value=f"{latency_ms}ms", inline=False)
    embed.add_field(name="**Region**", value="EU", inline=False)

    # Determine if there are any known issues
    known_issues = "None"
    if latency_ms > 200:
        known_issues = "High latency detected"
    elif latency_ms > 500:
        known_issues = "Severe latency issues"

    embed.add_field(name="**Known issues**", value=known_issues, inline=False)
    embed.add_field(name="**Status**",
                    value="Online and functional",
                    inline=False)

    # Set footer with current timestamp
    embed.set_footer(text=f"Requested by {ctx.author.name}")

    await ctx.send(embed=embed)


class RoleManagementView(discord.ui.View):

    def __init__(self,
                 member,
                 premium_role,
                 has_role=False,
                 original_message=None):
        super().__init__(timeout=300)
        self.member = member
        self.premium_role = premium_role
        self.has_role = has_role
        self.original_message = original_message
        if has_role:
            self.add_item(RemoveRoleButton())
            self.add_item(DoNothingButton())
        else:
            self.add_item(CustomButton())
            self.add_item(DoNothingButton())


class RemoveRoleButton(discord.ui.Button):

    def __init__(self):
        super().__init__(label="REMOVE ROLE",
                         style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        try:
            await view.member.remove_roles(
                view.premium_role,
                reason=f"Role removed by {interaction.user}")
            await view.original_message.delete()
            await interaction.response.send_message(
                f"✅ Role removed from {view.member.mention}", delete_after=10)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Permission denied",
                                                    ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}",
                                                    ephemeral=True)


class ClaimRewardView(discord.ui.View):

    def __init__(self,
                 member,
                 premium_role,
                 guild,
                 expiration_timestamp,
                 original_reason=None,
                 original_interaction=None):
        super().__init__(timeout=None)
        self.member = member
        self.premium_role = premium_role
        self.guild = guild
        self.expiration_timestamp = expiration_timestamp
        self.original_reason = original_reason
        self.original_interaction = original_interaction
        self.add_item(ClaimRewardButton())


class ClaimRewardButton(discord.ui.Button):

    def __init__(self):
        super().__init__(label="Claim reward",
                         style=discord.ButtonStyle.success,
                         custom_id="claim_reward_button")

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        self.disabled = True
        self.style = discord.ButtonStyle.secondary
        self.label = "Claimed ✓"
        await interaction.response.edit_message(view=view)

        current_timestamp = int(datetime.now().timestamp())

        if current_timestamp > view.expiration_timestamp:
            await interaction.followup.send(
                "Failed to redeem the reward | **expired**", ephemeral=True)
            return

        try:
            if view.premium_role in view.member.roles:
                await interaction.followup.send(
                    "You've already claimed this reward!", ephemeral=True)
                return

            await view.member.add_roles(view.premium_role,
                                        reason="Premium role claimed by user")

            success_embed = discord.Embed(
                description="✅ Reward has been successfully redeemed",
                color=0x00CED1)
            await interaction.followup.send(embed=success_embed)

            log_channel = view.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                reason = view.original_reason if view.original_reason else "No reason provided"
                claim_embed = discord.Embed(title="**Reward Claimed**",
                                            color=0x00FF00,
                                            timestamp=datetime.now())
                claim_embed.add_field(
                    name="User",
                    value=f"{view.member.mention} ~ `{view.member.id}`",
                    inline=False)
                claim_embed.add_field(name="Date",
                                      value=f"<t:{current_timestamp}:F>",
                                      inline=False)
                claim_embed.add_field(name="Reason",
                                      value=reason,
                                      inline=False)

                if view.original_interaction:
                    staff_member = view.original_interaction.user
                    claim_embed.add_field(
                        name="Staff",
                        value=f"{staff_member.mention} ~ `{staff_member.id}`",
                        inline=False)

                await log_channel.send(embed=claim_embed)

        except discord.Forbidden:
            await interaction.followup.send(
                "Failed to redeem the reward | **permission error**",
                ephemeral=True)
        except Exception as e:
            await interaction.followup.send(
                f"Failed to redeem the reward | **error**: {str(e)}",
                ephemeral=True)


class CustomButton(discord.ui.Button):

    def __init__(self):
        super().__init__(label="CUSTOM", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        modal = CustomReasonModal(self.view.member, self.view.premium_role,
                                  interaction, interaction.guild,
                                  self.view.original_message)
        await interaction.response.send_modal(modal)


class DoNothingButton(discord.ui.Button):

    def __init__(self):
        super().__init__(label="DO NOTHING",
                         style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        try:
            await self.view.original_message.delete()
        except:
            pass
        await interaction.response.send_message("Action cancelled",
                                                ephemeral=True)


class CustomReasonModal(discord.ui.Modal):

    def __init__(self, member, premium_role, original_interaction, guild,
                 original_message):
        super().__init__(title="Custom Premium Role Assignment")
        self.member = member
        self.premium_role = premium_role
        self.original_interaction = original_interaction
        self.guild = guild
        self.original_message = original_message
        self.reason_input = discord.ui.TextInput(
            label="Reason",
            placeholder="Enter the reason for giving premium role...",
            max_length=200,
            required=True)
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_input.value
        try:
            expiration_date = datetime.now() + timedelta(hours=48)
            expiration_timestamp = int(expiration_date.timestamp())
            embed = discord.Embed(title="Premium Access",
                                  description=reason,
                                  color=0x2b2d31)
            embed.add_field(name="Expiration Date:",
                            value=f"<t:{expiration_timestamp}:F>",
                            inline=False)
            embed.add_field(
                name="",
                value="This is an automated message sent from TEST101.",
                inline=False)

            claim_view = ClaimRewardView(
                self.member,
                self.premium_role,
                self.guild,
                expiration_timestamp,
                original_reason=reason,
                original_interaction=self.original_interaction)

            try:
                await self.member.send(embed=embed, view=claim_view)
                dm_status = "Reward DM sent"
            except discord.Forbidden:
                dm_status = "Could not send DM"

            try:
                await self.original_message.delete()
            except:
                pass

            await interaction.response.send_message(
                content=
                f"Premium reward sent to {self.member.mention} | **reason** ~ {reason}",
                delete_after=None)

        except Exception as e:
            await interaction.response.send_message(
                content=f"❌ Error: {str(e)}")


class PremiumListView(discord.ui.View):

    def __init__(self, premium_members, protected_role_id):
        super().__init__(timeout=300)
        self.premium_members = premium_members
        self.protected_role_id = protected_role_id
        self.add_item(CancelRolesButton())


class CancelRolesButton(discord.ui.Button):

    def __init__(self):
        super().__init__(label="CANCEL ROLES",
                         style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        # Disable the button immediately
        self.disabled = True
        self.label = "✓ ROLES CANCELLED"
        self.style = discord.ButtonStyle.grey

        view = self.view
        guild = interaction.guild
        premium_role = guild.get_role(PREMIUM_ROLE_ID)
        protected_role = guild.get_role(view.protected_role_id)

        if not premium_role:
            await interaction.response.edit_message(view=view)
            await interaction.followup.send("❌ Premium role not found",
                                            ephemeral=True)
            return

        results = []
        await interaction.response.edit_message(view=view)

        for member_data in view.premium_members:
            member = guild.get_member(member_data['id'])
            if member:
                if protected_role and protected_role in member.roles:
                    results.append(
                        f"🚫 Skipped {member.mention} | **protected user**")
                    continue

                try:
                    await member.remove_roles(
                        premium_role, reason="Mass role removal by admin")
                    results.append(
                        f"✅ Removed **premium** role from {member.mention}")
                except discord.Forbidden:
                    results.append(
                        f"❌ Failed to remove role from {member.mention} | **missing permissions**"
                    )
                except Exception as e:
                    results.append(
                        f"❌ Failed to remove role from {member.mention} | **error: {str(e)}**"
                    )

        result_message = "\n".join(results)
        if len(result_message) > 2000:
            result_message = result_message[:1990] + "\n[...]"

        embed = discord.Embed(title="Premium Role Removal Results",
                              description=result_message,
                              color=0xFFA500)
        await interaction.followup.send(embed=embed)


@bot.command(name='premium')
async def pizza_command(ctx, user_id: str = None):
    if user_id is None:
        await ctx.send(
            "❌ Please provide a user ID. Usage: `*premium <user_id>`")
        return

    user_id = user_id.strip('"\'')
    if not re.match(r'^\d{17,19}$', user_id):
        await ctx.send(f"❌ Invalid user ID: {user_id}")
        return

    try:
        user_id_int = int(user_id)
        guild = ctx.guild
        member = await guild.fetch_member(user_id_int)

        blacklist_role = guild.get_role(BLACKLIST_ROLE_ID)
        if blacklist_role and blacklist_role in member.roles:
            embed = discord.Embed(
                description=
                f"Failed to give Premium access to {member.mention}.\n\nUser is BLACKLISTED from getting premium features.",
                color=0xFF0000)
            await ctx.send(embed=embed)
            return

        premium_role = guild.get_role(PREMIUM_ROLE_ID)

        if not premium_role:
            await ctx.send("❌ Premium role not found")
            return

        if premium_role.position >= guild.me.top_role.position:
            await ctx.send("❌ Role hierarchy error")
            return

        has_role = premium_role in member.roles
        view = RoleManagementView(member,
                                  premium_role,
                                  has_role=has_role,
                                  original_message=ctx.message)

        if has_role:
            msg = await ctx.send(
                f"{member.mention} already has **premium** role", view=view)
        else:
            msg = await ctx.send(
                f"Role **premium** selected for {member.mention}", view=view)

    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


@bot.command(name='bl')
async def blacklist_command(ctx,
                            user: discord.Member = None,
                            *,
                            reason: str = None):
    if user is None or reason is None:
        await ctx.send("❌ Usage: `$bl @user <reason>`")
        return

    guild = ctx.guild
    blacklist_role = guild.get_role(BLACKLIST_ROLE_ID)
    premium_role = guild.get_role(PREMIUM_ROLE_ID)

    if not blacklist_role:
        await ctx.send("❌ Blacklist role not found")
        return

    if blacklist_role.position >= guild.me.top_role.position:
        await ctx.send("❌ Role hierarchy error")
        return

    if blacklist_role in user.roles:
        await ctx.send(f"{user.mention} is already blacklisted")
        return

    if premium_role and premium_role in user.roles:
        try:
            await user.remove_roles(
                premium_role,
                reason=f"Automatically removed when blacklisted by {ctx.author}"
            )
        except discord.Forbidden:
            await ctx.send(
                "⚠️ Could not remove premium role (missing permissions)")

    await user.add_roles(blacklist_role,
                         reason=f"Blacklisted by {ctx.author}: {reason}")
    embed = discord.Embed(
        description=
        f"{user.mention} has been successfully **BLACKLISTED**\n\n### Reason\n\n-# {reason}",
        color=0xFFFF00)

    if premium_role and premium_role in user.roles:
        embed.add_field(name="Premium Status",
                        value="✅ Premium role was automatically removed",
                        inline=False)

    await ctx.send(embed=embed)

    try:
        dm_embed = discord.Embed(
            description=
            f"Hello {user.mention},\n\nyou have been ***blacklisted*** from test898\n\n**reason** - {reason}\n\n-# This action is not reversable so do not dm any staff member",
            color=0xFF0000)
        await user.send(embed=dm_embed)
    except:
        pass


@bot.command(name='bll')
async def blacklist_lookup_command(ctx, user: discord.Member = None):
    if user is None:
        await ctx.send("❌ Usage: `$bll @user`")
        return

    blacklist_role = ctx.guild.get_role(BLACKLIST_ROLE_ID)
    if not blacklist_role:
        await ctx.send("❌ Blacklist role not found")
        return

    if blacklist_role in user.roles:
        await ctx.send(
            f"{ctx.author.mention}, {user.mention} is **blacklisted**")
    else:
        await ctx.send(
            f"no **blacklist** data has been found for {user.mention}")


@bot.command(name='prem')
async def list_premium_members(ctx):
    premium_role = ctx.guild.get_role(PREMIUM_ROLE_ID)
    protected_role = ctx.guild.get_role(PROTECTED_ROLE_ID)

    if not premium_role:
        embed = discord.Embed(
            title="Failed | No Roles Found",
            description="The premium role doesn't exist in this server",
            color=0xFF0000)
        await ctx.send(embed=embed)
        return

    premium_members = []
    for member in ctx.guild.members:
        if premium_role in member.roles:
            premium_members.append({
                'id':
                member.id,
                'mention':
                member.mention,
                'is_protected':
                protected_role in member.roles if protected_role else False
            })

    if not premium_members:
        embed = discord.Embed(
            title="Failed | No Roles Found",
            description="No users currently have the premium role",
            color=0xFF0000)
        await ctx.send(embed=embed)
        return

    description_lines = ["__**Premium Users**__\n"]
    for member in premium_members:
        if member['is_protected']:
            description_lines.append(
                f"•**{member['mention']}** ~ `{member['id']}` __***(no kick)***__"
            )
        else:
            description_lines.append(
                f"•**{member['mention']}** ~ `{member['id']}`")

    embed = discord.Embed(title="__**Premium Users**__",
                          description="\n".join(description_lines),
                          color=0xFFA500)

    view = PremiumListView(premium_members, PROTECTED_ROLE_ID)
    await ctx.send(embed=embed, view=view)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing argument.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument.")
    else:
        await ctx.send(f"❌ Error: {str(error)}")





if __name__ == "__main__":
    main()
