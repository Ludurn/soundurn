# Soundurn
A Discord bot written in Python that plays locally stored sounds.

## Features
- Play custom `.mp3` sounds from the local sounds/ directory.
- Enable or disable sound looping.
- Connect to and disconnect from voice channels.
- Basic moderation commands.
- Voice moderation (mute, deafen, silence).
---

## Requirements

### Local Execution
- Python 3.9+
- FFmpeg

### Containerized Execution
- Docker

## Configuration

Create an `.env` file.

Place your Discord bot token in it. The bot reads this file on startup and will fail to log in if the file is missing or the token is invalid.

```env
  DISCORD_TOKEN=your_token_here
```
> Never share your bot token or commit .env to source control.

## Setup

### Local Execution

It is recommended to use a virtual environment.

In the root directory of the project, create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the bot:

```bash
python main.py
```

Deactivate the virtual environment when finished:

```bash
deactivate
```

### Containerized Execution

Build the image:
```bash
docker build -t soundurn .
```

Run the container:
```bash
docker run --env-file .env soundurn
```

## Commands

### Audio
- `$play <sound>`: Plays a sound from the `sounds/` directory in your voice channel.
- `$stop`: Stops the current sound with a fade-out effect.
- `$loop`: Toggles sound looping on/off.
- `$soundls`: Lists all available sounds.
- `$con`: Connects the bot to your current voice channel.
- `$dcon`: Disconnects the bot from the voice channel.
 
### Moderation
- `$clear`: Deletes up to 100 messages from the current channel. Requires **Manage Messages** permission.
- `$mute @user`: Mutes the mentioned user(s).
- `$unmute @user`: Unmutes the mentioned user(s).
- `$deafen @user`: Deafens the mentioned user(s).
- `$undeafen @user`: Removes deafen from the mentioned user(s).
- `$silence @user`: Mutes and deafens the mentioned user(s).
- `$unsilence @user`: Unmutes and undeafens the mentioned user(s).
 
### Utility
- `$help`: Displays the list of available commands.
 
## Sounds

Place your `.mp3` files inside the `sounds/` directory.

Example:

```text
sounds/
├── airhorn.mp3
├── bruh.mp3
└── vineboom.mp3
```
 
Then play them with:
 
```text
$play airhorn
$play bruh
$play vineboom
```

## Shoutout

Tutorial that helped me get started with this project:

- [How to Make a Discord Bot That Plays Random Pipe Sounds - Luke](https://www.youtube.com/watch?v=icfy4ACzpgE)

## License

MIT
