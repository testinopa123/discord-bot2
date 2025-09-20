from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import discord
from datetime import datetime, timedelta
import asyncio
import threading
import os
import requests
import secrets
from functools import wraps

def create_web_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')
    if not app.secret_key:
        raise ValueError('SECRET_KEY environment variable is required for security')
    
    # Discord OAuth2 configuration
    DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
    DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
    ADMIN_USER_IDS = set(filter(None, os.getenv('ADMIN_USER_IDS', '').split(',')))
    REDIRECT_URI = f"https://{os.getenv('REPLIT_DEV_DOMAIN', 'localhost:5000')}/auth/callback"
    
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def require_admin(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session or session['user']['id'] not in ADMIN_USER_IDS:
                return jsonify({'error': 'Admin access required'}), 403
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/')
    def index():
        return render_template('index.html', user=session.get('user'), discord_client_id=DISCORD_CLIENT_ID)
    
    @app.route('/commands')
    def commands():
        return render_template('commands.html', user=session.get('user'))
    
    @app.route('/admin')
    @require_auth
    @require_admin
    def admin_panel():
        return render_template('admin.html', user=session.get('user'))
    
    @app.route('/login')
    def login():
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        auth_url = f"https://discord.com/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify&state={state}"
        return redirect(auth_url)
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('index'))
    
    @app.route('/auth/callback')
    def auth_callback():
        code = request.args.get('code')
        state = request.args.get('state')
        
        # Verify state parameter for CSRF protection
        if not state or state != session.get('oauth_state'):
            return 'Invalid state parameter', 400
            
        if not code:
            return 'Authorization failed', 400
            
        # Clear the state from session
        session.pop('oauth_state', None)
        
        # Exchange code for access token
        token_data = {
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        token_response = requests.post('https://discord.com/api/oauth2/token', data=token_data, headers=headers)
        
        if token_response.status_code != 200:
            return 'Token exchange failed', 400
        
        access_token = token_response.json()['access_token']
        
        # Get user info
        user_headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get('https://discord.com/api/users/@me', headers=user_headers)
        
        if user_response.status_code != 200:
            return 'Failed to get user info', 400
        
        user_data = user_response.json()
        
        # Regenerate session to prevent session fixation
        old_session_data = dict(session)
        session.clear()
        
        session['user'] = {
            'id': user_data['id'],
            'username': user_data['username'],
            'discriminator': user_data.get('discriminator', '0'),
            'avatar': user_data['avatar'],
            'is_admin': user_data['id'] in ADMIN_USER_IDS
        }
        
        return redirect(url_for('index'))

    

    @app.route('/get-channels')
    @require_auth
    @require_admin
    def get_channels():
        """Endpoint to get available channels"""
        try:
            from bot import bot

            if not bot.is_ready():
                return jsonify({'status': 'error', 'message': 'Bot is not ready'})

            channels = []
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        channels.append({
                            'id': str(channel.id),
                            'name': f"{guild.name} - #{channel.name}",
                            'guild_icon': str(guild.icon.url) if guild.icon else None
                        })

            return jsonify({'status': 'success', 'channels': channels})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})

    @app.route('/api/commands')
    def api_commands():
        """API endpoint for bot commands with permission categorization"""
        try:
            from bot import bot
            
            if not bot.is_ready():
                return jsonify({'status': 'error', 'message': 'Bot is not ready'})
            
            commands_data = []
            for cmd in bot.commands:
                # Categorize permissions
                permission_level = 'everyone'
                if hasattr(cmd, 'checks') and cmd.checks:
                    for check in cmd.checks:
                        check_name = getattr(check, '__name__', str(check))
                        if 'owner' in check_name.lower() or 'admin' in check_name.lower():
                            permission_level = 'admin'
                            break
                        elif 'staff' in check_name.lower() or 'mod' in check_name.lower():
                            permission_level = 'staff'
                            break
                
                commands_data.append({
                    'name': cmd.name,
                    'description': cmd.help or cmd.brief or 'No description available',
                    'aliases': list(cmd.aliases) if cmd.aliases else [],
                    'permission_level': permission_level,
                    'usage': f"*{cmd.name} {cmd.signature}" if cmd.signature else f"*{cmd.name}",
                    'category': getattr(cmd, 'cog_name', 'General')
                })
            
            return jsonify({'status': 'success', 'commands': commands_data})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    
    @app.route('/api/guilds')
    @require_admin
    def api_guilds():
        """API endpoint for guild information (admin only)"""
        try:
            from bot import bot
            
            if not bot.is_ready():
                return jsonify({'status': 'error', 'message': 'Bot is not ready'})
            
            guilds_data = []
            for guild in bot.guilds:
                guilds_data.append({
                    'id': str(guild.id),
                    'name': guild.name,
                    'icon': str(guild.icon.url) if guild.icon else None,
                    'member_count': guild.member_count,
                    'owner': str(guild.owner) if guild.owner else 'Unknown',
                    'created_at': guild.created_at.isoformat()
                })
            
            return jsonify({'status': 'success', 'guilds': guilds_data})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
            
    @app.route('/status')
    def bot_status():
        """API endpoint for bot status"""
        try:
            # Import bot here to avoid circular imports
            from bot import bot
            try:
                from bot import bot_start_time
            except (ImportError, AttributeError):
                # Fallback if bot_start_time is not available
                bot_start_time = datetime.utcnow() - timedelta(seconds=bot.latency * 1000 if hasattr(bot, 'latency') and bot.latency else 0)
            
            if bot.is_ready():
                uptime = datetime.utcnow() - bot_start_time
                status_data = {
                    'status': 'online',
                    'uptime': f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m",
                    'latency': round(bot.latency * 1000) if hasattr(bot, 'latency') else 'N/A',
                    'guilds': len(bot.guilds) if bot.guilds else 0,
                    'users': len(bot.users) if bot.users else 0,
                    'commands': len([cmd for cmd in bot.commands])
                }
            else:
                status_data = {
                    'status': 'offline',
                    'uptime': 'N/A',
                    'latency': 'N/A',
                    'guilds': 0,
                    'users': 0,
                    'commands': 0
                }
        except Exception as e:
            status_data = {
                'status': 'error',
                'error': str(e),
                'uptime': 'N/A',
                'latency': 'N/A',
                'guilds': 0,
                'users': 0,
                'commands': 0
            }
        
        return jsonify(status_data)
    
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
    
    @app.route('/api/command-logs')
    @require_admin
    def api_command_logs():
        """API endpoint for command logs (admin only)"""
        try:
            from bot import command_logs
            
            # Return last 100 logs, newest first
            recent_logs = command_logs[-100:] if command_logs else []
            recent_logs.reverse()
            
            return jsonify({'status': 'success', 'logs': recent_logs})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    
    @app.route('/api/servers-channels')
    @require_admin
    def api_servers_channels():
        """API endpoint for server and channel lists (admin only)"""
        try:
            from bot import bot
            
            if not bot.is_ready():
                return jsonify({'status': 'error', 'message': 'Bot is not ready'})
            
            servers_data = []
            for guild in bot.guilds:
                channels_data = []
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        channels_data.append({
                            'id': str(channel.id),
                            'name': channel.name,
                            'category': channel.category.name if channel.category else 'No Category'
                        })
                
                servers_data.append({
                    'id': str(guild.id),
                    'name': guild.name,
                    'channels': channels_data
                })
            
            return jsonify({'status': 'success', 'servers': servers_data})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    
    @app.route('/api/execute-command', methods=['POST'])
    @require_admin
    def api_execute_command():
        """API endpoint to execute commands remotely (admin only)"""
        try:
            from bot import bot
            data = request.get_json()
            
            if not bot.is_ready():
                return jsonify({'status': 'error', 'message': 'Bot is not ready'})
            
            if not data or 'channel_id' not in data or 'command' not in data:
                return jsonify({'status': 'error', 'message': 'Channel ID and command are required'})
            
            channel = bot.get_channel(int(data['channel_id']))
            if not channel:
                return jsonify({'status': 'error', 'message': 'Channel not found'})
            
            if not channel.permissions_for(channel.guild.me).send_messages:
                return jsonify({'status': 'error', 'message': 'Bot cannot send messages in this channel'})
            
            command = data['command'].strip()
            if not command.startswith(('*', '$')):
                command = '*' + command
            
            # Execute the command
            asyncio.run_coroutine_threadsafe(
                channel.send(command),
                bot.loop
            )
            
            return jsonify({
                'status': 'success',
                'message': f'Command "{command}" sent to #{channel.name} in {channel.guild.name}'
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    
    @app.route('/api/admin-users', methods=['GET', 'POST', 'DELETE'])
    @require_admin
    def api_admin_users():
        """API endpoint for managing admin users (admin only)"""
        try:
            current_admins = list(ADMIN_USER_IDS)
            
            if request.method == 'GET':
                # Return current admin list with user info
                admin_info = []
                for admin_id in current_admins:
                    if admin_id:  # Skip empty strings
                        admin_info.append({
                            'id': admin_id,
                            'username': f'User {admin_id}'  # Could be enhanced to fetch actual usernames
                        })
                return jsonify({'status': 'success', 'admins': admin_info})
            
            elif request.method == 'POST':
                # Add new admin
                data = request.get_json()
                if not data or 'user_id' not in data:
                    return jsonify({'status': 'error', 'message': 'User ID is required'})
                
                user_id = str(data['user_id']).strip()
                if not user_id.isdigit():
                    return jsonify({'status': 'error', 'message': 'Invalid user ID format'})
                
                if user_id in ADMIN_USER_IDS:
                    return jsonify({'status': 'error', 'message': 'User is already an admin'})
                
                # Note: In production, this would update the environment variable
                # For now, we'll just add to the runtime set
                ADMIN_USER_IDS.add(user_id)
                return jsonify({
                    'status': 'success',
                    'message': f'User {user_id} added as admin (session only - add to ADMIN_USER_IDS env var for permanent)'
                })
            
            elif request.method == 'DELETE':
                # Remove admin
                data = request.get_json()
                if not data or 'user_id' not in data:
                    return jsonify({'status': 'error', 'message': 'User ID is required'})
                
                user_id = str(data['user_id']).strip()
                if user_id in ADMIN_USER_IDS:
                    ADMIN_USER_IDS.discard(user_id)
                    return jsonify({
                        'status': 'success',
                        'message': f'User {user_id} removed from admins (session only)'
                    })
                else:
                    return jsonify({'status': 'error', 'message': 'User is not an admin'})
                    
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    
    return app
