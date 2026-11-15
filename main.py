import asyncio
import os

import disnake as discord
from disnake.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError

os.makedirs("sounds", exist_ok=True)

command_sync_flags = commands.CommandSyncFlags.default()

bot = commands.InteractionBot(command_sync_flags=command_sync_flags)

bot_voice = None
loop_sound = False
sound = None


def play_sound(bot_voice, loop_sound, sound):
    if bot_voice is None or not bot_voice.is_connected():
        return "*Bot is not connected to a voice channel 'v'*"

    path = os.path.join("sounds", f"{sound}.mp3")

    if not os.path.isfile(path):
        return f"*'{sound}' sound source not found -_-*"

    audio = discord.FFmpegPCMAudio(
        path, before_options="-stream_loop -1" if loop_sound else None
    )

    bot_voice.play(discord.PCMVolumeTransformer(audio, volume=1.0))
    return f"*Playing {sound} for ya ~.~*"


async def fade_out(vClient):
    src = vClient.source
    while src.volume > 0:
        src.volume -= 0.1
        await asyncio.sleep(0.3)
    vClient.stop()


async def send_msg(inter, message):
    if inter.response.is_done():
        await inter.edit_original_response(content=f"{message}")
    else:
        await inter.response.send_message(f"{message}")


async def send_ephemeral(inter, message):
    if inter.response.is_done():
        await inter.followup.send(f"{message}", ephemeral=True, delete_after=5.0)
    else:
        await inter.response.send_message(
            f"{message}", ephemeral=True, delete_after=5.0
        )


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}")


@bot.slash_command(name="play", description="Plays a sound")
async def play(inter, sound: str):
    global bot_voice

    user_voice = inter.user.voice

    if user_voice is None or not user_voice.channel:
        await send_ephemeral(
            inter, "*You must be in a voice channel to play the sound 'v'*"
        )
        return

    if not sound.strip():
        await send_ephemeral(inter, "*You must specify a available source -_-*")

    bot_voice = inter.guild.voice_client

    if bot_voice:
        if bot_voice.channel.id != user_voice.channel.id:
            await bot_voice.move_to(user_voice.channel)
    else:
        bot_voice = await user_voice.channel.connect()

    player_output = play_sound(bot_voice, loop_sound, sound)
    await send_msg(inter, player_output)


@bot.event
async def on_message(message):
    global vClient, loop_sound

    if message.content.startswith("$stop"):
        if not vClient:
            return
        if not vClient.is_connected():
            await message.channel.send("*I'm not connected to a voice channel ;-;*")
            return
        if not vClient.is_playing():
            await message.channel.send("*No sound is playing right now 0-0*")
            return
        else:
            # vClient.stop()
            await fade_out(vClient)
            await message.channel.send("*The sound has been stopped (-v-)*")

    if message.content.startswith("$loop"):
        loop_sound = not loop_sound
        if loop_sound:
            await message.channel.send("*Loop is activated :D*")
        else:
            await message.channel.send("*Loop is desactivated :c*")

    if message.content.startswith("$clear"):
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send(
                "*You don't have the permission to clear messages. '-'*"
            )
            return
        deleted = await message.channel.purge(limit=100)
        await message.channel.send(
            f"*Cleared {len(deleted)} messages :P*", delete_after=5
        )

    if message.content.startswith("$soundls"):
        await message.channel.send("*The available sounds are:*")
        for filename in os.listdir("sounds"):
            filepath = os.path.join("sounds", filename)
            if os.path.isfile(filepath) and filename.lower().endswith(".mp3"):
                await message.channel.send(f"\n**{filename.removesuffix('.mp3')}**")

    if message.content.startswith("$mute"):
        if not message.mentions:
            await message.channel.send(
                "*Nobody was muted, you need to mention someone ._.*"
            )
        for member in message.mentions:
            if member.voice and member.voice.channel:
                await member.edit(mute=True)
                await message.channel.send(
                    f"_**{member.display_name}** has been muted :x_"
                )
            else:
                await message.channel.send(
                    f"_{member.display_name} is not in a voice channel T-T_"
                )

    if message.content.startswith("$unmute"):
        if not message.mentions:
            await message.channel.send(
                "*Nobody was unmuted, you need to mention someone ._.*"
            )
        for member in message.mentions:
            if member.voice and member.voice.channel:
                await member.edit(mute=False)
                await message.channel.send(
                    f"_**{member.display_name}** has been unmuted :0_"
                )
            else:
                await message.channel.send(
                    f"_**{member.display_name}** is not in a voice channel T-T_"
                )

    if message.content.startswith("$deafen"):
        if not message.mentions:
            await message.channel.send(
                "*Nobody was deafen, you need to mention someone ._.*"
            )
        for member in message.mentions:
            if member.voice and member.voice.channel:
                await member.edit(deafen=True)
                await message.channel.send(
                    f"_**{member.display_name}** has been deafened :x_"
                )
            else:
                await message.channel.send(
                    f"_{member.display_name} is not in a voice channel T-T_"
                )

    if message.content.startswith("$undeafen"):
        if not message.mentions:
            await message.channel.send(
                "*Nobody was undeafened, you need to mention someone ._.*"
            )
        for member in message.mentions:
            if member.voice and member.voice.channel:
                await member.edit(deafen=False)
                await message.channel.send(
                    f"_**{member.display_name}** has been undeafened :0_"
                )
            else:
                await message.channel.send(
                    f"_**{member.display_name}** is not in a voice channel T-T_"
                )

    if message.content.startswith("$silence"):
        if not message.mentions:
            await message.channel.send(
                "*Nobody was silenced, you need to mention someone ._.*"
            )
        for member in message.mentions:
            if member.voice and member.voice.channel:
                await member.edit(mute=True)
                await member.edit(deafen=True)
                await message.channel.send(
                    f"_**{member.display_name}** has been silenced :x_"
                )
            else:
                await message.channel.send(
                    f"_**{member.display_name}** is not in voice channel T-T_"
                )

    if message.content.startswith("$unsilence"):
        if not message.mentions:
            await message.channel.send(
                "*Nobody was unsilenced, you need to mention someone ._.*"
            )
        for member in message.mentions:
            if member.voice and member.voice.channel:
                await member.edit(mute=False)
                await member.edit(deafen=False)
                await message.channel.send(
                    f"_**{member.display_name}** has been unsilenced :0_"
                )
            else:
                await message.channel.send(
                    f"_**{member.display_name}** is not in voice channel T-T_"
                )

    if message.content.startswith("$con"):
        if not message.author.voice:
            await message.channel.send(
                "*You must be in a voice channel to play the sound 'v'*"
            )
            return
        vChannel = message.author.voice.channel
        if message.guild.voice_client:
            vClient = message.guild.voice_client
            if vClient.channel != vChannel:
                await vClient.move_to(vChannel)
        else:
            vClient = await vChannel.connect()

    if message.content.startswith("$dcon") and vClient and vClient.is_connected():
        vClient.stop()
        await vClient.disconnect()

    if message.content.startswith("$help"):
        await message.channel.send(
            "*The commands I can run are:*\n"
            "**__Audio__**\n"
            "   **$play** <sound>\n"
            "   **$stop**\n"
            "   **$loop**\n"
            "   **$soundls**\n"
            "   **$con**\n"
            "   **$dcon**\n"
            "**__Moderation__**\n"
            "   **$clear**\n"
            "   **$mute** @user\n"
            "   **$unmute** @user\n"
            "   **$deafen** @user\n"
            "   **$undeafen** @user\n"
            "   **$silence** @user\n"
            "   **$unsilence** @user\n"
            "**__Utility__**\n"
            "   **$help**\n"
        )


bot.run(TOKEN)
