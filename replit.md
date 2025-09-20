# Discord Bot Project

## Overview

This is a comprehensive Discord community management and moderation bot built with Python using the discord.py library. The bot provides extensive moderation capabilities, user management features, and includes a modern glassmorphism web dashboard for monitoring and administration. It's designed to handle large Discord servers with role-based permissions, ticket systems, invite tracking, and automated moderation features.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

### September 20, 2025 - Advanced Admin Panel Features
- **Command Logging System**: Comprehensive tracking of all bot command usage with user details, timestamps, and context
- **Remote Command Execution**: Admin interface for executing bot commands remotely via web dashboard with server/channel selection
- **Admin User Management**: Dynamic addition and removal of admin users with session-based controls
- **Enhanced API Endpoints**: Added `/api/command-logs`, `/api/servers-channels`, `/api/execute-command`, and `/api/admin-users`
- **Real-time Monitoring**: Live command logs display with automatic refresh functionality

### September 20, 2025 - Modern Glassmorphism Dashboard
- **Complete UI Overhaul**: Implemented modern glassmorphism design with Tailwind CSS + DaisyUI
- **Discord OAuth2 Authentication**: Secure login system with CSRF protection and session management
- **Three Main Sections**: Landing page, interactive commands showcase, and admin-only server management panel
- **Security Enhancements**: Added OAuth state validation, session regeneration, and admin route protection
- **API Endpoints**: Created `/api/commands` for command categorization and `/api/guilds` for server management
- **Interactive Features**: Hover effects, search/filtering, server ID copying, and real-time statistics

## System Architecture

### Core Bot Framework
- **Discord.py Library**: Built on discord.py with command extensions for structured command handling
- **Dual Command Prefixes**: Supports both '*' and '$' prefixes for flexibility
- **Intent-Based Architecture**: Utilizes specific Discord intents for message content, guilds, and member management
- **Global Error Handling**: Centralized error management with user-friendly error messages

### Application Structure
- **Modular Design**: Main application (`main.py`) orchestrates both bot and web interface
- **Threading Model**: Web interface runs in separate daemon thread to avoid blocking bot operations
- **Environment Configuration**: Role IDs and sensitive data configured via environment variables for security

### Role-Based Permission System
The bot implements a hierarchical permission system using Discord role IDs:
- **Premium Role**: Special privileges for premium users
- **Management Role**: Administrative access to sensitive commands like invite checking
- **Support Role**: Access to ticket system management
- **Protected Role**: Users immune from certain moderation actions
- **Blacklist Role**: Restricted users with limited permissions

### Modern Web Dashboard Architecture
- **Flask Framework**: Secure web interface with OAuth2 authentication
- **Glassmorphism UI**: Modern design with backdrop-blur effects, translucent cards, and smooth animations
- **Discord OAuth Integration**: Secure login using Discord OAuth2 with CSRF protection
- **Admin Access Control**: Role-based access to sensitive server management features
- **RESTful APIs**: Secure endpoints for commands (`/api/commands`) and server data (`/api/guilds`)
- **Responsive Design**: Mobile-friendly interface with adaptive layouts
- **Real-time Updates**: Live bot statistics and server monitoring

### Security Features
- **OAuth2 State Validation**: CSRF protection with cryptographically secure state parameters
- **Session Management**: Secure session handling with regeneration to prevent fixation attacks
- **Admin Route Protection**: Multi-layer authentication for sensitive endpoints
- **Environment Security**: Required SECRET_KEY validation and secure credential handling

### Command Architecture
- **Group Commands**: Structured command groups (e.g., `invites` group with subcommands)
- **Type Hinting**: Comprehensive type annotations for better code maintainability
- **Async/Await Pattern**: Non-blocking command execution using asyncio
- **Invite Verification System**: Automated role assignment based on invite counts with interactive setup panels
- **Permission Categorization**: Automatic command permission classification (everyone/staff/admin)

### UI Components
- **Discord UI Framework**: Utilizes Discord's native UI components (Buttons, Views, Selects, Modals)
- **Interactive Elements**: Support for button interactions, select menus, and modal forms
- **Custom Text Inputs**: Modal-based forms for complex user input scenarios
- **Glassmorphism Effects**: Modern web UI with hover animations and translucent elements

### Logging and Monitoring
- **Dedicated Log Channel**: Centralized logging to specific Discord channel
- **Startup Diagnostics**: Comprehensive connection reporting with guild information
- **Error Tracking**: Detailed error logging with context preservation
- **Web Dashboard Analytics**: Real-time metrics and performance monitoring

## External Dependencies

### Core Dependencies
- **discord.py**: Primary Discord API wrapper for bot functionality
- **Flask**: Web framework for dashboard interface with session support
- **flask-session**: Secure server-side session management
- **requests**: HTTP client for Discord OAuth2 integration
- **asyncio**: Asynchronous programming support for concurrent operations
- **threading**: Multi-threading support for running web interface alongside bot

### Security Dependencies
- **secrets**: Cryptographically secure random generation for OAuth state
- **functools**: Decorator support for authentication middleware
- **pytz**: Timezone handling for accurate timestamp operations

### Development Dependencies
- **typing**: Enhanced type hinting capabilities
- **datetime**: Time-based operations for uptime tracking and moderation features
- **os**: Environment variable access for configuration management
- **re**: Regular expression support for text processing
- **random**: Randomization utilities for bot features

### Discord Platform Integration
- **Discord Gateway**: Real-time event streaming from Discord servers
- **Discord REST API**: HTTP-based operations for message management and user interactions
- **Discord OAuth2**: Secure authentication and user authorization
- **Discord Permissions API**: Fine-grained permission checking and role management

### Modern Web Interface Assets
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **DaisyUI**: Component library for enhanced Tailwind components
- **Font Awesome**: Comprehensive icon library for modern UI elements
- **Alpine.js**: Lightweight JavaScript framework for reactive components
- **CSS3**: Advanced styling with glassmorphism effects, gradients, and animations
- **HTML5**: Modern web standards for responsive dashboard interface

## Project Structure

### Templates
- **base.html**: Responsive glassmorphism layout with navigation and authentication
- **index.html**: Landing page with real-time bot statistics and feature showcase
- **commands.html**: Interactive command browser with search, filtering, and hover effects
- **admin.html**: Secure admin panel for server management and ID copying

### Static Assets
- **style.css**: Custom glassmorphism styles with hover animations and responsive design

### Core Application Files
- **bot.py**: Main Discord bot with all commands and features
- **main.py**: Application entry point orchestrating bot and web interface
- **web_interface.py**: Secure Flask application with OAuth2 and API endpoints
- **discord_bot_complete.py**: Standalone downloadable version for manual deployment