# discord-lolesports

Discord Lolesports Bot is a Discord assistant for League of Legends esports. It tracks live matches, upcoming schedules, team rosters, and delivers Riot splash art drops right into your server so fans never miss a broadcast.

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup](#setup)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Run Locally](#run-locally)
  - [Deploy](#deploy)
- [Commands](#commands)
  - [Slash Commands](#slash-commands)
  - [Prefix Commands](#prefix-commands)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)

## Features
- Live match tracking with automatic activity updates and optional push posts in a dedicated channel.
- On-demand slash commands for schedules, standings, teams, and league directories powered by the official LoL Esports API.
- Hybrid commands (`/live`, `;live`, etc.) that work as either slash or prefix commands for flexibility.
- Background reminder loop that announces new live games and the next series when broadcasts end.
- Splash-art mini game that serves random champion skins or multi-art surprises from Riot's Data Dragon CDN.

## Tech Stack
- Python 3.10+
- [discord.py 2.x](https://discordpy.readthedocs.io/en/stable/)
- Riot/LoL Esports persisted API + Data Dragon CDN
- `reactionmenu` for multi-page embeds
- Hosted via `Procfile` worker (Heroku or any process manager)

## Setup

### Prerequisites
- Python 3.10 or newer with `pip`.
- A Discord bot application with message content intent enabled and the bot invited to your server.
- Access to the LoL Esports API (`x-api-key` header). You can obtain a key from the official site or your browser devtools while visiting [lolesports.com](https://lolesports.com/).
- Riot Data Dragon CDN base URL (public, defaults provided below).

### Installation
```bash
git clone https://github.com/<you>/discord-lolesports.git
cd discord-lolesports
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Configuration
Create a `.env` file in the project root so the bot can authenticate with Discord and the Riot APIs.

```dotenv
DISCORD_BOT_TOKEN=your_bot_token
ALLOWED_SERVER_IDS=123456789012345678          # Single guild ID used to register slash commands
CHANNEL_ID=987654321098765432                 # Channel used by the background task for live updates
API_BASE=https://esports-api.lolesports.com/persisted/gw
X_API_KEY=riot_esports_api_key
CDN_API_BASE=https://ddragon.leagueoflegends.com/cdn
```

Notes:
- `ALLOWED_SERVER_IDS` should match the guild where you want slash commands to appear. Update the value (or add logic) if you need to sync globally.
- `CHANNEL_ID` is only required if you enable the background notifier cog; it posts the `/live` embed there automatically.
- The CDN base usually stays at the Data Dragon default, but you can point it at a mirror if Riot changes versions.

### Run Locally
```bash
python bot.py
```
The bot loads every cog in `cogs/`, registers slash commands for the guild listed in `ALLOWED_SERVER_IDS`, and starts the background loop defined in `backgroundTasks.py`.

### Deploy
- The repository includes a `Procfile` with `worker python bot.py`. Use it as-is for Heroku, Railway, or any platform that supports Procfile dynos or process types.
- For Docker or other platforms, run the same command and ensure the environment variables above are provided securely.

## Commands

### Slash Commands
| Command | Arguments | Description |
| --- | --- | --- |
| `/schedule` | `region` (optional: defaults to WORLDS) | Upcoming matches for the selected league with channel links if available. |
| `/leagues` | – | List of all supported leagues/regions returned by the API. |
| `/all-standings` | `timeframe` (required, e.g., `summer_2023`) | Standings snapshot for every major league in the supplied split. |
| `/standings` | `league` (defaults to LCS) | Detailed standings plus records for the specified league. |
| `/team` | `team_code` (autocomplete) | Roster, record, and highlights for the selected team. |
| `/live` | – | Shows the current live series (hybrid command: works with `;live`). |
| `/upnext` | `team_code` or `league` | Countdown and scheduling details for the next match of a team or league (also works with `;upnext`). |

### Prefix Commands
The default prefix is `;`. Hybrid commands can be triggered either by slash or prefix form.

| Command | Aliases | Description |
| --- | --- | --- |
| `;live` | – | Same as `/live`. |
| `;upnext` | – | Same as `/upnext`. |
| `;greet` | `hello`, `sup`, `hi` | Sends a friendly greeting. |
| `;intro` | – | Explains what Poro Bot can do. |
| `;ping` | – | Round-trip latency check to Discord. |
| `;splash` | `skin` | Single random splash art (champion + skin) from Data Dragon. |
| `;surprise` | `sp` | Sends four random splash arts in one drop. |
| Owner tools | `logout`, `cancel`, `start`, `stop`, `interval`, `isrunning` | Maintenance helpers for the background loop (restricted with `@commands.is_owner()`). |

## Architecture
```
discord-lolesports/
├─ bot.py                # Entrypoint: loads all cogs, syncs slash commands, and boots the client
├─ cogs/
│  ├─ basic.py           # Greetings, intro, misc utilities
│  ├─ query.py           # Slash + hybrid commands that call the LoL Esports API
│  ├─ splashArt.py       # Splash/surprise image commands from Data Dragon
│  └─ backgroundTasks.py # Live match watcher that posts updates in CHANNEL_ID
├─ utils/
│  ├─ lolesports.py      # API wrapper with helpers for schedules, standings, teams, etc.
│  └─ constants.py       # Shared constants/enums
├─ requirements.txt
└─ Procfile
```

## Troubleshooting
- **Slash commands are missing**: confirm the bot has the `applications.commands` scope, `ALLOWED_SERVER_IDS` matches the guild ID, and restart the bot so it can sync.
- **Live updates are silent**: ensure `CHANNEL_ID` points to a channel the bot can read/write and that the background task is still running (`;isrunning`).
- **API calls fail**: the LoL Esports API rotates keys periodically. Grab a fresh `x-api-key` and restart.
- **Splash art errors**: Data Dragon patches often change. Update `self.patch` in `splashArt.py` or edit `CDN_API_BASE` if Riot releases a new CDN path.
