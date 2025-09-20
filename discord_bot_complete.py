import discord
from discord.ext import commands
import os
import re
import random
import typing
from datetime import datetime, timedelta
from discord.ui import Button, View, Select, Modal, TextInput
from typing import Optional
import asyncio
from discord import ButtonStyle, TextStyle

print("Bot script is starting...")

# Bot setup with command prefix
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=['*', '$'], intents=intents, help_command=None)

# Role IDs - Update these with your server's role IDs
PREMIUM_ROLE_ID = 1316416010076684478
BLACKLIST_ROLE_ID = 1393399872912363600
LOG_CHANNEL_ID = 1390407710335307877
PROTECTED_ROLE_ID = 1396507987253657743
TICKET_CATEGORY_ID = 1394030033043062784
SUPPORT_ROLE_ID = 1394030191659188236
MANAGEMENT_ROLE_ID = 1315714615396794480
VERIFIED_ROLE_ID = 1308045059756654653

# Bot start time for uptime tracking
bot_start_time = datetime.utcnow()

@bot.event
async def on_ready():
    print(f'✅ {bot.user} has connected to Discord!')
    print(f'📊 Connected to {len(bot.guilds)} guild(s)')
    for guild in bot.guilds:
        print(f'   - {guild.name} (id: {guild.id})')
    
    # Log to designated channel if available
    for guild in bot.guilds:
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="✅ Bot Connected",
                description=f"Bot successfully connected to {guild.name}",
                color=0x00FF00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Guilds", value=len(bot.guilds), inline=True)
            embed.add_field(name="Users", value=len(bot.users), inline=True)
            embed.add_field(name="Commands", value=len(bot.commands), inline=True)
            try:
                await log_channel.send(embed=embed)
            except:
                pass

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ I don't have the required permissions to execute this command!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found!")
    elif isinstance(error, commands.RoleNotFound):
        await ctx.send("❌ Role not found!")
    else:
        print(f"Unhandled error: {error}")
        await ctx.send(f"❌ An error occurred: {str(error)}")

# Helper function for counting invites
async def count_invites(guild, user):
    """Helper function to count invites for a user"""
    try:
        invites = await guild.invites()
        return sum(invite.uses for invite in invites if invite.inviter and invite.inviter.id == user.id)
    except discord.Forbidden:
        return 0

# INVITE COMMANDS
@bot.group(name='invites', invoke_without_command=True)
async def invites(ctx, user: typing.Optional[typing.Union[discord.Member, int]] = None):
    """Check invite counts for yourself or others (Management only)"""
    management_role = ctx.guild.get_role(MANAGEMENT_ROLE_ID)
    
    if user is not None:
        if management_role not in ctx.author.roles:
            await ctx.send("❌ You need the Management role to check others' invites!")
            return
        
        if isinstance(user, int):
            user = ctx.guild.get_member(user)
            if user is None:
                await ctx.send("❌ User not found!")
                return
        
        title = f"**{user.display_name}**"
        description = f"Currently has **{await count_invites(ctx.guild, user)}** invites"
    else:
        user = ctx.author
        title = f"**{user.display_name}**"
        description = f"You currently have **{await count_invites(ctx.guild, user)}** invites"

    embed = discord.Embed(
        title=title,
        description=description,
        color=0xFFA500
    )
    await ctx.send(embed=embed)

@invites.command(name='leaderboard')
async def invites_leaderboard(ctx):
    """Show the invites leaderboard"""
    try:
        invites = await ctx.guild.invites()
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to view invites!")
        return

    invite_counts = {}
    for invite in invites:
        if invite.inviter:
            if invite.inviter.id in invite_counts:
                invite_counts[invite.inviter.id] += invite.uses
            else:
                invite_counts[invite.inviter.id] = invite.uses

    sorted_invites = sorted(invite_counts.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="**Invites Leaderboard**",
        color=0xFFA500
    )

    leaderboard = []
    for position, (user_id, count) in enumerate(sorted_invites[:10], start=1):
        user = ctx.guild.get_member(user_id)
        if user:
            leaderboard.append(f"{position}. **{user.display_name}** - {count} invites")

    if leaderboard:
        embed.description = "\n".join(leaderboard)
    else:
        embed.description = "No invite data available"

    await ctx.send(embed=embed)

# INVITE SETUP SYSTEM
class InviteSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Post Check", style=discord.ButtonStyle.gray, custom_id="post_check_button")
    async def post_check_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        
        embed = discord.Embed(
            description="Select Channel\nPlease type the channel where the message should be posted",
            color=0x808080
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
            
        try:
            channel_msg = await bot.wait_for('message', check=check, timeout=60.0)
            channel_input = channel_msg.content
            
            try:
                if channel_input.startswith('<#') and channel_input.endswith('>'):
                    channel_id = int(channel_input[2:-1])
                    channel = interaction.guild.get_channel(channel_id)
                elif channel_input.isdigit():
                    channel = interaction.guild.get_channel(int(channel_input))
                else:
                    await interaction.followup.send("Invalid channel format. Please use channel mention or ID.", ephemeral=True)
                    return
                
                if not channel:
                    raise ValueError("Channel not found")
                    
                embed = discord.Embed(
                    title="Invites Check",
                    description="Please press the button to check your invites, if you have enough invites to pass verification you will get the Verified role.",
                    color=0xFFA500
                )
                
                view = CheckInvitesView()
                message = await channel.send(embed=embed, view=view)
                
                success_embed = discord.Embed(
                    description=f"✅ Message successfully posted in {channel.mention}\n[Go to message]({message.jump_url})",
                    color=0x00FF00
                )
                await interaction.followup.send(embed=success_embed, ephemeral=True)
                
            except Exception as e:
                error_embed = discord.Embed(
                    description=f"❌ Error: {str(e)}",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                
        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out waiting for channel input.", ephemeral=True)

class CheckInvitesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Check", style=discord.ButtonStyle.gray, custom_id="check_invites_button")
    async def check_invites_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        invite_count = await count_invites(interaction.guild, interaction.user)
        verified_role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        
        if invite_count >= 1:
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
        color=0xFFA500
    )
    embed.set_footer(text=f"Invoked by {ctx.author} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    view = InviteSetupView()
    await ctx.send(embed=embed, view=view)

# LIST COMMANDS
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
        color=0xFFA500
    )
    
    members_list = []
    for member in ctx.guild.members:
        members_list.append(f"• {member.mention} - `{member.id}`")
    
    if len(members_list) > 0:
        chunks = [members_list[i:i + 20] for i in range(0, len(members_list), 20)]
        for chunk in chunks:
            embed.add_field(name="\u200b", value="\n".join(chunk), inline=False)
    else:
        embed.description = "No members found"
    
    embed.set_footer(text=f"Total members: {len(ctx.guild.members)}")
    await ctx.send(embed=embed)

@list_group.command(name='roles')
async def list_roles(ctx):
    """List all server roles"""
    embed = discord.Embed(
        title="__**Role List**__",
        color=0xFFA500
    )
    
    roles_list = []
    for role in sorted(ctx.guild.roles, key=lambda r: r.position, reverse=True):
        if role.name != "@everyone":
            color_hex = f"#{role.color.value:06x}" if role.color.value != 0 else "#000000"
            roles_list.append(f"• {role.mention} - `{role.id}` / {color_hex} - ({len(role.members)} members)")
    
    if len(roles_list) > 0:
        chunks = [roles_list[i:i + 10] for i in range(0, len(roles_list), 10)]
        for chunk in chunks:
            embed.add_field(name="\u200b", value="\n".join(chunk), inline=False)
    else:
        embed.description = "No roles found"
    
    embed.set_footer(text=f"Total roles: {len(ctx.guild.roles) - 1}")
    await ctx.send(embed=embed)

# ROLE MANAGEMENT
class AddUserModal(discord.ui.Modal):
    def __init__(self, role):
        super().__init__(title=f"Add User to {role.name}")
        self.role = role
        
        self.user_input = discord.ui.TextInput(
            label="User ID or Mention",
            placeholder="Enter user ID or mention",
            required=True
        )
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_input = self.user_input.value
            try:
                user_id = int(user_input)
                member = interaction.guild.get_member(user_id)
            except ValueError:
                if user_input.startswith('<@') and user_input.endswith('>'):
                    user_id = int(user_input[2:-1].replace('!', ''))
                    member = interaction.guild.get_member(user_id)
                else:
                    member = None
            
            if not member:
                return await interaction.response.send_message("User not found!", ephemeral=True)
            
            await member.add_roles(self.role)
            await interaction.response.send_message(f"Added {self.role.name} to {member.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to add role: {e}", ephemeral=True)

@bot.command(name='checkrole')
async def check_role(ctx, role: discord.Role):
    """Check details about a specific role"""
    color_hex = f"#{role.color.value:06x}" if role.color.value != 0 else "#000000"
    
    embed = discord.Embed(
        title="__**Role Checkup**__",
        description=f"`role color = {color_hex}` - `members = {len(role.members)}`",
        color=0xFFA500
    )
    
    members_list = []
    for member in role.members:
        members_list.append(f"• {member.mention} - `{member.id}`")
    
    if members_list:
        chunks = [members_list[i:i + 20] for i in range(0, len(members_list), 20)]
        for chunk in chunks:
            embed.add_field(name="Members with this role", value="\n".join(chunk), inline=False)
    else:
        embed.add_field(name="Members with this role", value="No members have this role", inline=False)
    
    view = View()
    
    async def add_user_callback(interaction):
        if interaction.user != ctx.author:
            return await interaction.response.send_message("You didn't run this command!", ephemeral=True)
        
        modal = AddUserModal(role)
        await interaction.response.send_modal(modal)
    
    add_button = Button(label="Add User", style=ButtonStyle.green)
    add_button.callback = add_user_callback
    view.add_item(add_button)
    
    async def remove_user_callback(interaction):
        if interaction.user != ctx.author:
            return await interaction.response.send_message("You didn't run this command!", ephemeral=True)
        
        if not role.members:
            return await interaction.response.send_message("No members to remove!", ephemeral=True)
        
        options = [
            discord.SelectOption(label=member.display_name, value=str(member.id))
            for member in role.members[:25]
        ]
        
        select = Select(placeholder="Select member to remove", options=options)
        
        async def select_callback(interaction):
            member_id = int(select.values[0])
            member = ctx.guild.get_member(member_id)
            try:
                await member.remove_roles(role)
                await interaction.response.send_message(f"Removed {role.name} from {member.mention}", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Failed to remove role: {e}", ephemeral=True)
        
        select.callback = select_callback
        remove_view = View()
        remove_view.add_item(select)
        await interaction.response.send_message("Select member to remove role from:", view=remove_view, ephemeral=True)
    
    remove_button = Button(label="Remove User", style=ButtonStyle.red)
    remove_button.callback = remove_user_callback
    view.add_item(remove_button)
    
    await ctx.send(embed=embed, view=view)

# UTILITY COMMANDS
@bot.command(name='av', aliases=['avatar'])
async def avatar(ctx, user: Optional[discord.User] = None):
    """Show a user's avatar in an embed"""
    target = user or ctx.author
    
    avatar_url = target.display_avatar.with_size(1024).url
    
    embed = discord.Embed(
        title=f"{target.name}'s Avatar",
        color=0x2b2d31
    )
    embed.set_image(url=avatar_url)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping_command(ctx):
    """Check the bot's latency and connection status"""
    latency_ms = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="***__PONG!__***",
        color=0xFFA500
    )
    
    embed.add_field(name="**Current MS**", value=f"{latency_ms}ms", inline=False)
    embed.add_field(name="**Ping**", value=f"{latency_ms}ms", inline=False)
    embed.add_field(name="**Region**", value="EU", inline=False)
    
    known_issues = "None"
    if latency_ms > 200:
        known_issues = "High latency detected"
    elif latency_ms > 500:
        known_issues = "Severe latency issues"
    
    embed.add_field(name="**Known issues**", value=known_issues, inline=False)
    embed.add_field(name="**Status**", value="Online and functional", inline=False)
    
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    
    await ctx.send(embed=embed)

@bot.command(name='status')
async def status_command(ctx):
    """Show bot status information"""
    uptime = datetime.utcnow() - bot_start_time
    
    embed = discord.Embed(
        title="🤖 Bot Status",
        color=0x00FF00
    )
    
    embed.add_field(
        name="Uptime",
        value=f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m",
        inline=True
    )
    
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Guilds", value=len(bot.guilds), inline=True)
    embed.add_field(name="Users", value=len(bot.users), inline=True)
    embed.add_field(name="Commands", value=len(bot.commands), inline=True)
    embed.add_field(name="Version", value="1.0.0", inline=True)
    
    await ctx.send(embed=embed)

# ANNOUNCEMENT COMMANDS
@bot.command(name='announce')
@commands.has_permissions(manage_messages=True)
async def announce_session(ctx, time_input: str, *, args: str = None):
    """Create tournament announcement with exact host formatting"""
    try:
        try:
            time_obj = datetime.strptime(time_input, "%H:%M")
        except ValueError:
            await ctx.send("Invalid time format. Use HH:MM (24h format)", delete_after=5)
            return

        users = []
        lobby_info = None
        
        if args:
            parts = args.split()
            
            for part in parts:
                if part.startswith('<@') and part.endswith('>'):
                    user_id = part[2:-1].replace('!', '')
                    try:
                        user = await commands.MemberConverter().convert(ctx, user_id)
                        users.append(user)
                    except:
                        continue
                else:
                    lobby_start = parts.index(part)
                    lobby_info = ' '.join(parts[lobby_start:])
                    break

        if not users:
            await ctx.send("Please mention at least one host", delete_after=5)
            return

        now = datetime.now()
        registration_time = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0)
        if registration_time < now:
            registration_time += timedelta(days=1)

        game_start_time = registration_time + timedelta(minutes=30)
        
        reg_timestamp = int(registration_time.timestamp())
        game_timestamp = int(game_start_time.timestamp())

        if len(users) == 1:
            hosts_text = users[0].mention
        elif len(users) == 2:
            hosts_text = f"{users[0].mention} & {users[1].mention}"
        else:
            hosts_text = ", ".join(user.mention for user in users[:-1])
            hosts_text += f" & {users[-1].mention}"

        announcement_msg = (
            f"@everyone\n\n"
            f"**Fortnite Tournament**{f' {lobby_info}' if lobby_info else ''}\n\n"
            f"> **Registration opens <t:{reg_timestamp}:t>**\n\n"
            f"> **First Game Commences <t:{game_timestamp}:t>**\n\n"
            f" The hosts for this session are: {hosts_text} , Direct Message them for help.\n\n"
            f"• Session lasts 3 Games. **Miss a single game and you will be banned.**\n"
            f"• Required at least **110+ Reacts**"
        )
        
        message = await ctx.send(announcement_msg)
        
        try:
            await message.add_reaction("✋")
        except:
            pass

        try:
            await ctx.message.delete()
        except:
            pass

    except Exception as e:
        await ctx.send(f"Error creating announcement: {str(e)}", delete_after=10)

@bot.command(name='cancel')
@commands.has_permissions(manage_messages=True)
async def cancel_session(ctx, message_id: int, *, reason: str):
    """Cancel an announcement with exact formatting"""
    try:
        try:
            message = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("Message not found. Check the message ID.", delete_after=10)
            return
        except discord.Forbidden:
            await ctx.send("Don't have permission to edit that message.", delete_after=10)
            return

        cancelled_content = (
            f"~~{message.content}~~\n\n"
            f"CANCELLED: {reason}"
        )
        
        original_embed = message.embeds[0] if message.embeds else None
        
        await message.edit(
            content=cancelled_content,
            embed=original_embed
        )
        
        try:
            await message.clear_reactions()
        except:
            pass
            
        await ctx.send(f"Announcement {message_id} has been cancelled.", delete_after=5)

    except Exception as e:
        await ctx.send(f"Error cancelling announcement: {str(e)}", delete_after=10)

# MODERATION COMMANDS
@bot.command(name='ghost')
@commands.has_permissions(manage_messages=True)
async def ghost_ping(ctx, user: discord.Member, amount: int = 20):
    """Ghost ping a user X times (default: 20)"""
    if amount < 1:
        await ctx.send("Amount must be at least 1", delete_after=3)
        return
    if amount > 50:
        amount = 50
        await ctx.send("Capped at 50 pings for safety", delete_after=3)

    try:
        await ctx.message.delete()
    except:
        pass

    confirm = await ctx.send(
        f"Ghost pinging {user.mention} {amount} times... (this will self-destruct)",
        delete_after=3
    )

    successful_pings = 0
    for i in range(amount):
        try:
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            msg = await ctx.send(user.mention)
            await msg.delete()
            successful_pings += 1
        except Exception as e:
            continue

    if successful_pings > 0:
        report = await ctx.send(
            f"Successfully ghost pinged {user.mention} {successful_pings}/{amount} times (this will self-destruct)",
            delete_after=3
        )

@bot.command(name='purge')
@commands.has_permissions(manage_messages=True)
async def purge_messages(ctx, amount: int):
    """Delete a specified number of messages in the current channel"""
    if amount <= 0:
        await ctx.send("Please specify a positive number of messages to delete.", delete_after=5)
        return
    
    if amount > 100:
        amount = 100
        await ctx.send("Maximum purge amount is 100. Deleting 100 messages...", delete_after=3)
    
    try:
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=amount)
        confirm = await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=3)
        
    except discord.Forbidden:
        await ctx.send("I don't have permissions to delete messages here.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"Error deleting messages: {e}", delete_after=5)

@bot.command(name='say')
@commands.has_permissions(manage_messages=True)
async def say_command(ctx, channel: typing.Optional[discord.TextChannel], *, message: str):
    """Make the bot repeat your message in a specific channel"""
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
    
    target = channel or ctx.channel
    await target.send(message)

# TICKET SYSTEM
class TicketCreationView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if category:
            for channel in category.channels:
                if isinstance(channel, discord.TextChannel) and f"support-{interaction.user.name.lower()}" in channel.name.lower():
                    await interaction.response.send_message(
                        f"You already have an open ticket: {channel.mention}",
                        ephemeral=True
                    )
                    return
        
        random_number = random.randint(10000, 99999)
        
        clean_username = ''.join(c for c in interaction.user.name.lower() if c.isalnum() or c in ('-', '_'))
        clean_username = clean_username[:20]
        
        channel_name = f"support-{clean_username}-{random_number}"
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        try:
            if category:
                ticket_channel = await category.create_text_channel(
                    name=channel_name,
                    overwrites=overwrites,
                    reason=f"Ticket created by {interaction.user}"
                )
            else:
                ticket_channel = await interaction.guild.create_text_channel(
                    name=channel_name,
                    overwrites=overwrites,
                    reason=f"Ticket created by {interaction.user}"
                )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Failed to create ticket channel: {str(e)}",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"Support Ticket - {interaction.user}",
            description=(
                "Support will be with you shortly. Please describe your issue.\n\n"
                "**Ticket Info:**\n"
                f"- User: {interaction.user.mention}\n"
                f"- Created: <t:{int(datetime.now().timestamp())}:F>\n"
                f"- Ticket ID: {random_number}"
            ),
            color=0x00FF00
        )
        
        view = TicketManagementView()
        await ticket_channel.send(
            content=f"{interaction.user.mention} {support_role.mention if support_role else ''}",
            embed=embed,
            view=view
        )
        
        await interaction.response.send_message(
            f"Ticket created: {ticket_channel.mention}",
            ephemeral=True
        )

class TicketManagementView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        for user in interaction.channel.overwrites:
            if isinstance(user, discord.Member) and user != interaction.guild.me:
                await interaction.channel.set_permissions(
                    user,
                    read_messages=False,
                    send_messages=False
                )
        
        button.disabled = True
        button.label = "Ticket Closed"
        button.style = discord.ButtonStyle.grey
        
        await interaction.response.edit_message(view=self)
        
        embed = discord.Embed(
            title="Ticket Closed",
            description=f"This ticket was closed by {interaction.user.mention}",
            color=0xFF0000
        )
        await interaction.channel.send(embed=embed)
        
    @discord.ui.button(label="Delete Ticket", style=discord.ButtonStyle.danger, custom_id="delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        if not any(role.id == SUPPORT_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("Only support staff can delete tickets.", ephemeral=True)
            return
            
        await interaction.response.send_message("Deleting this ticket in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete(reason=f"Ticket deleted by {interaction.user}")

@bot.command(name="ticketsetup")
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    """Setup the ticket system in this channel"""
    embed = discord.Embed(
        title="Support Tickets",
        description="Click the button below to create a new support ticket",
        color=0x00FF00
    )
    
    await ctx.send(embed=embed, view=TicketCreationView())
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command(name="closeticket")
async def close_ticket_cmd(ctx):
    """Close the current ticket"""
    if not ctx.channel.name.startswith("support-"):
        await ctx.send("This is not a ticket channel!")
        return
    
    for user in ctx.channel.overwrites:
        if isinstance(user, discord.Member) and user != ctx.guild.me:
            await ctx.channel.set_permissions(
                user,
                read_messages=False,
                send_messages=False
            )
    
    embed = discord.Embed(
        title="Ticket Closed",
        description=f"This ticket was closed by {ctx.author.mention}",
        color=0xFF0000
    )
    await ctx.send(embed=embed)

@bot.command(name="deleteticket")
@commands.has_permissions(manage_channels=True)
async def delete_ticket_cmd(ctx):
    """Delete the current ticket (staff only)"""
    if not ctx.channel.name.startswith("support-"):
        await ctx.send("This is not a ticket channel!")
        return
    
    await ctx.send("Deleting this ticket in 5 seconds...")
    await asyncio.sleep(5)
    await ctx.channel.delete(reason=f"Ticket deleted by {ctx.author}")

# PREMIUM ROLE MANAGEMENT
class RoleManagementView(discord.ui.View):
    def __init__(self, member, premium_role, has_role=False, original_message=None):
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
        super().__init__(label="REMOVE ROLE", style=discord.ButtonStyle.secondary)
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        try:
            await view.member.remove_roles(view.premium_role, reason=f"Role removed by {interaction.user}")
            if view.original_message:
                await view.original_message.delete()
            await interaction.response.send_message(
                f"✅ Role removed from {view.member.mention}",
                delete_after=10
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ Permission denied", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

class CustomButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="CUSTOM", style=discord.ButtonStyle.secondary)
    
    async def callback(self, interaction: discord.Interaction):
        modal = CustomReasonModal(
            self.view.member, 
            self.view.premium_role, 
            interaction, 
            interaction.guild,
            self.view.original_message
        )
        await interaction.response.send_modal(modal)

class DoNothingButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="DO NOTHING", style=discord.ButtonStyle.secondary)
    
    async def callback(self, interaction: discord.Interaction):
        try:
            if self.view.original_message:
                await self.view.original_message.delete()
        except:
            pass
        await interaction.response.send_message("Action cancelled", ephemeral=True)

class CustomReasonModal(discord.ui.Modal):
    def __init__(self, member, premium_role, original_interaction, guild, original_message):
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
            required=True
        )
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_input.value
        try:
            expiration_date = datetime.now() + timedelta(hours=48)
            expiration_timestamp = int(expiration_date.timestamp())
            embed = discord.Embed(title="Premium Access", description=reason, color=0x2b2d31)
            embed.add_field(name="Expiration Date:", value=f"<t:{expiration_timestamp}:F>", inline=False)
            embed.add_field(name="", value="This is an automated message sent from TEST101.", inline=False)
            
            claim_view = ClaimRewardView(
                self.member, 
                self.premium_role, 
                self.guild, 
                expiration_timestamp,
                original_reason=reason,
                original_interaction=self.original_interaction
            )
            
            try:
                await self.member.send(embed=embed, view=claim_view)
            except discord.Forbidden:
                pass
            
            try:
                if self.original_message:
                    await self.original_message.delete()
            except:
                pass
            
            await interaction.response.send_message(
                content=f"Premium reward sent to {self.member.mention} | **reason** ~ {reason}",
                delete_after=None
            )
            
        except Exception as e:
            await interaction.response.send_message(content=f"❌ Error: {str(e)}")

class ClaimRewardView(discord.ui.View):
    def __init__(self, member, premium_role, guild, expiration_timestamp, original_reason=None, original_interaction=None):
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
        super().__init__(label="Claim reward", style=discord.ButtonStyle.success, custom_id="claim_reward_button")
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        
        self.disabled = True
        self.style = discord.ButtonStyle.secondary
        self.label = "Claimed ✓"
        await interaction.response.edit_message(view=view)
        
        current_timestamp = int(datetime.now().timestamp())
        
        if current_timestamp > view.expiration_timestamp:
            await interaction.followup.send("Failed to redeem the reward | **expired**", ephemeral=True)
            return
        
        try:
            if view.premium_role in view.member.roles:
                await interaction.followup.send("You've already claimed this reward!", ephemeral=True)
                return
                
            await view.member.add_roles(view.premium_role, reason="Premium role claimed by user")
            
            success_embed = discord.Embed(
                description="✅ Reward has been successfully redeemed",
                color=0x00CED1
            )
            await interaction.followup.send(embed=success_embed)
            
            log_channel = view.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                reason = view.original_reason if view.original_reason else "No reason provided"
                claim_embed = discord.Embed(
                    title="**Reward Claimed**",
                    color=0x00FF00,
                    timestamp=datetime.now()
                )
                claim_embed.add_field(name="User", value=f"{view.member.mention} ~ `{view.member.id}`", inline=False)
                claim_embed.add_field(name="Date", value=f"<t:{current_timestamp}:F>", inline=False)
                claim_embed.add_field(name="Reason", value=reason, inline=False)
                
                if view.original_interaction:
                    staff_member = view.original_interaction.user
                    claim_embed.add_field(name="Staff", value=f"{staff_member.mention} ~ `{staff_member.id}`", inline=False)
                
                try:
                    await log_channel.send(embed=claim_embed)
                except:
                    pass
                
        except discord.Forbidden:
            await interaction.followup.send("Failed to redeem the reward | **permission error**", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to redeem the reward | **error**: {str(e)}", ephemeral=True)

@bot.command(name='premium')
async def premium_command(ctx, user_id: str = None):
    if user_id is None:
        await ctx.send("❌ Please provide a user ID. Usage: `*premium <user_id>`")
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
                description=f"Failed to give Premium access to {member.mention}.\n\nUser is BLACKLISTED from getting premium features.",
                color=0xFF0000
            )
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
        view = RoleManagementView(member, premium_role, has_role=has_role, original_message=ctx.message)
        
        if has_role:
            msg = await ctx.send(f"{member.mention} already has **premium** role", view=view)
        else:
            msg = await ctx.send(f"Role **premium** selected for {member.mention}", view=view)
            
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# BLACKLIST COMMANDS
@bot.command(name='bl')
async def blacklist_command(ctx, user: discord.Member = None, *, reason: str = None):
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
            await user.remove_roles(premium_role, reason=f"Automatically removed when blacklisted by {ctx.author}")
        except discord.Forbidden:
            await ctx.send("⚠️ Could not remove premium role (missing permissions)")
    
    await user.add_roles(blacklist_role, reason=f"Blacklisted by {ctx.author}: {reason}")
    embed = discord.Embed(
        description=f"{user.mention} has been successfully **BLACKLISTED**\n\n### Reason\n\n-# {reason}",
        color=0xFFFF00)
    
    if premium_role and premium_role in user.roles:
        embed.add_field(name="Premium Status", value="✅ Premium role was automatically removed", inline=False)
    
    await ctx.send(embed=embed)
    
    try:
        dm_embed = discord.Embed(
            description=f"Hello {user.mention},\n\nyou have been ***blacklisted*** from test898\n\n**reason** - {reason}\n\n-# This action is not reversable so do not dm any staff member",
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
    
    if blacklist_role and blacklist_role in user.roles:
        embed = discord.Embed(
            description=f"{user.mention} is **BLACKLISTED**",
            color=0xFF0000
        )
    else:
        embed = discord.Embed(
            description=f"{user.mention} is **NOT BLACKLISTED**",
            color=0x00FF00
        )
    
    await ctx.send(embed=embed)

# HELP COMMAND
@bot.command(name='help')
async def help_command(ctx):
    """Show available commands"""
    embed = discord.Embed(
        title="🤖 Bot Commands",
        description="Here are all available commands:",
        color=0xFFA500
    )
    
    embed.add_field(
        name="📊 Invite Commands",
        value="• `$invites` - Check your invite count\n• `$invites @user` - Check someone's invites (Management)\n• `$invites leaderboard` - Show invite leaderboard\n• `$invsetup` - Setup invite verification (Admin)",
        inline=False
    )
    
    embed.add_field(
        name="📋 List Commands",
        value="• `$list members` - List all server members\n• `$list roles` - List all server roles",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Role Management",
        value="• `$checkrole @role` - Check role details and manage members",
        inline=False
    )
    
    embed.add_field(
        name="🖼️ Utility Commands",
        value="• `$av [@user]` - Show user's avatar\n• `$ping` - Check bot latency\n• `$status` - Bot status",
        inline=False
    )
    
    embed.add_field(
        name="📢 Moderation Commands",
        value="• `$announce <time> <hosts> [lobby]` - Create tournament announcement\n• `$cancel <message_id> <reason>` - Cancel an announcement\n• `$purge <amount>` - Delete messages\n• `$ghost @user [amount]` - Ghost ping user\n• `$say [#channel] <message>` - Make bot say something",
        inline=False
    )
    
    embed.add_field(
        name="🎫 Ticket Commands",
        value="• `$ticketsetup` - Setup ticket system\n• `$closeticket` - Close current ticket\n• `$deleteticket` - Delete current ticket",
        inline=False
    )
    
    embed.add_field(
        name="⭐ Premium Commands",
        value="• `$premium <user_id>` - Manage premium role\n• `$bl @user <reason>` - Blacklist user\n• `$bll @user` - Check blacklist status",
        inline=False
    )
    
    embed.set_footer(text="Use $ or * as command prefix")
    
    await ctx.send(embed=embed)

@bot.command(name='gloryy')
async def gloryy_command(ctx):
    """Displays info about Gloryy"""
    embed = discord.Embed(
        title="Who's Gloryy?",
        description="Gloryy is a random guy from Germany, he's really chill!",
        color=0x1a9f1a
    )
    await ctx.send(embed=embed)

# Start the bot - Replace 'YOUR_BOT_TOKEN_HERE' with your actual Discord bot token
if __name__ == "__main__":
    token = "YOUR_BOT_TOKEN_HERE"  # Replace this with your Discord bot token
    
    if token == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please replace 'YOUR_BOT_TOKEN_HERE' with your actual Discord bot token!")
        print("You can get your token from: https://discord.com/developers/applications")
        print("1. Create an application")
        print("2. Go to the 'Bot' section") 
        print("3. Copy the token and replace 'YOUR_BOT_TOKEN_HERE' in this file")
    else:
        try:
            bot.run(token)
        except discord.LoginFailure:
            print("❌ Invalid bot token! Please check your token and try again.")
        except Exception as e:
            print(f"❌ Error starting bot: {e}")