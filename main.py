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

guild_settings = {}


class UserPicker(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60.0)
        self.selected_users = []

    @discord.ui.user_select(placeholder="Select users", min_values=1, max_values=25)
    async def select_users(self, select, inter):
        self.selected_users.extend(select.values)

        await inter.response.defer()

        self.stop()


def get_guild_settings(guild_id):
    if guild_id not in guild_settings:
        guild_settings[guild_id] = {
            "loop": False,
            "current_sound": None,
        }
    return guild_settings[guild_id]


def play_sound(bot_voice, settings, sound):
    if bot_voice is None or not bot_voice.is_connected():
        return "*Bot is not connected to a voice channel 'v'*"

    path = ""

    for pack in os.listdir("sounds"):
        packpath = os.path.join("sounds", pack)

        if not os.path.isdir(packpath):
            continue

        for filename in os.listdir(packpath):
            filepath = os.path.join(packpath, filename)

            if (
                os.path.isfile(filepath)
                and filename.endswith(".mp3")
                and (filename.removesuffix(".mp3") == sound)
            ):
                path = filepath
                break

        if path:
            break

    if not path:
        return f"***{sound}** sound source not found -_-*"

    settings["current_sound"] = sound
    event_loop = asyncio.get_running_loop()

    def after_playing(error):
        if error:
            print(f"Player error: {error}")
            return

        if (
            settings["loop"]
            and settings["current_sound"] == sound
            and bot_voice.is_connected()
        ):
            event_loop.call_soon_threadsafe(
                play_sound,
                bot_voice,
                settings,
                sound,
            )

    audio = discord.FFmpegPCMAudio(path)

    bot_voice.play(
        discord.PCMVolumeTransformer(audio, volume=1.0),
        after=after_playing,
    )
    return f"*Playing {sound} for ya ~.~*"


async def fade_out(bot_voice, pause):
    source = bot_voice.source

    if source is None or not hasattr(source, "volume"):
        bot_voice.pause() if pause else bot_voice.stop()
        return

    while bot_voice.is_playing() and source.volume > 0:
        source.volume = max(0.0, source.volume - 0.1)
        await asyncio.sleep(0.3)

    bot_voice.pause() if pause else bot_voice.stop()


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


async def send_view(inter, message, view=None, ephemeral=False, delete_after=None):
    if delete_after is not None and delete_after <= 0.0:
        delete_after = None

    if inter.response.is_done():
        await inter.edit_original_response(
            f"{message}", delete_after=delete_after, view=view
        )
    else:
        await inter.response.send_message(
            f"{message}", ephemeral=ephemeral, delete_after=delete_after, view=view
        )


async def handle_action(inter, selected_users, action):
    result = {
        "applied": [],
        "except": [],
        "already": [],
    }

    for user in selected_users:
        member = await inter.guild.fetch_member(user.id)
        member_vc = member.voice

        if not member_vc:
            result["except"].append(member.mention)
            continue

        if action == "silence":
            already_applied = member_vc.mute and member_vc.deaf
            edit_options = {"mute": True, "deafen": True}

        elif action == "mute":
            already_applied = member_vc.mute
            edit_options = {"mute": True}

        elif action == "deafen":
            already_applied = member_vc.deaf
            edit_options = {"deafen": True}

        else:
            raise ValueError(f"Unsupported action: {action}")

        if already_applied:
            result["already"].append(member.mention)
            continue

        await member.edit(**edit_options)
        result["applied"].append(member.mention)

    return result


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}")


@bot.slash_command(name="play", description="Plays a sound")
async def play(inter, sound: str):
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

    await inter.response.defer()

    settings = get_guild_settings(inter.guild.id)
    settings["current_sound"] = sound

    if bot_voice.is_playing():
        await fade_out(bot_voice, False)

    player_output = play_sound(bot_voice, settings, sound)
    await send_msg(inter, player_output)


@bot.slash_command(name="stop", description="Stops the currently playing sound")
async def stop(inter):
    bot_voice = inter.guild.voice_client

    if not bot_voice:
        await send_ephemeral(
            inter, "*The bot must be in a voice channel to stop a sound ¯\\\\(ツ)/¯*"
        )
        return

    if not bot_voice.is_playing():
        await send_ephemeral(inter, "*The bot is playing nothing right now 0-0*")
        return

    await inter.response.defer()
    get_guild_settings(inter.guild.id)["current_sound"] = None
    await fade_out(bot_voice, False)
    await send_msg(inter, "*The sound has been stopped (-v-)*")


@bot.slash_command(name="pause", description="Pauses the currently playing sound")
async def pause(inter):
    bot_voice = inter.guild.voice_client

    if not bot_voice:
        await send_ephemeral(
            inter, "*The bot must be in a voice channel to pause a sound ¯\\\\(ツ)/¯*"
        )
        return

    if not bot_voice.is_playing():
        await send_ephemeral(inter, "*The bot is playing nothing right now 0-0*")
        return

    if bot_voice.is_paused():
        await send_ephemeral(inter, "*The bot is already paused right now 0-0*")

    await inter.response.defer()
    await fade_out(bot_voice, True)
    await send_msg(inter, "*The sound has been paused (-v-)*")


@bot.slash_command(name="resume", description="Resumes the currently paused sound")
async def resume(inter):
    bot_voice = inter.guild.voice_client

    if not bot_voice:
        await send_ephemeral(
            inter, "*The bot must be in a voice channel to resume a sound ¯\\\\(ツ)/¯*"
        )
        return

    if bot_voice.is_playing():
        await send_ephemeral(inter, "*The bot is already playing right now 0-0*")
        return

    if not bot_voice.is_paused():
        await send_ephemeral(inter, "*The bot has nothing to play right now 0-0*")
        return

    await inter.response.defer()
    bot_voice.source.volume = 1.0
    bot_voice.resume()
    await send_msg(inter, "*The sound has been resumed (-v-)*")


@bot.slash_command(name="loop", description="Loop the current sound")
async def loop(inter):
    bot_voice = inter.guild.voice_client

    if not bot_voice:
        await send_ephemeral(
            inter, "*The bot must be in a voice channel to loop a sound ¯\\\\(ツ)/¯*"
        )
        return

    settings = get_guild_settings(inter.guild.id)
    settings["loop"] = not settings["loop"]

    status = "enabled" if settings["loop"] else "disabled"
    await send_msg(inter, f"*Sound looping has been {status} (-v-)*")


@bot.slash_command(name="clear", description="Clears the 100 most recent messages")
async def clear(inter):
    if not inter.permissions.manage_messages:
        await send_ephemeral(
            inter, "*You don't have the permission to clear messages ¯\\\\(ツ)/¯*"
        )
        return

    deleted = await inter.channel.purge(limit=100)
    await send_ephemeral(inter, f"*Cleared {len(deleted)} messages (-v-)*")


@bot.slash_command(name="soundls", description="Lists the available sounds in a pack")
async def soundls(inter, pack: str):
    pack = pack.lower()

    if not os.path.isdir(f"sounds/{pack}"):
        await send_ephemeral(inter, "*You must specify an available pack -_-*")
        return

    sound_list = [f"*The available sounds in **{pack}** are:*"]

    for filename in os.listdir(f"sounds/{pack}"):
        filepath = os.path.join("sounds", pack, filename)
        if os.path.isfile(filepath) and filename.lower().endswith(".mp3"):
            sound_list.append(f"\n**{filename.removesuffix('.mp3')}**")

    await send_msg(inter, f"{''.join(sound_list)}")


@bot.slash_command(name="packls", description="Lists the available sound packs")
async def packls(inter):
    pack_list = ["*The available sound packs are:*"]

    for dirname in os.listdir("sounds"):
        dirpath = os.path.join("sounds", dirname)
        if os.path.isdir(dirpath):
            pack_list.append(f"\n**{dirname}**")

    await send_msg(inter, f"{''.join(pack_list)}")


@bot.slash_command(name="mute", description="Mutes the selected users")
async def mute(inter):
    if not inter.permissions.mute_members:
        await send_ephemeral(
            inter, "*You don't have the permission to mute members ¯\\\\(ツ)/¯*"
        )
        return

    view = UserPicker()
    await send_view(
        inter, "Select the users to be muted:", view, ephemeral=True, delete_after=30.0
    )
    await view.wait()

    if len(view.selected_users) <= 0:
        await send_view(
            inter, "*Nobody was muted, you must specify a user -_-*", delete_after=5.0
        )
        return

    result = await handle_action(inter, view.selected_users, "mute")

    message = ""

    if result["applied"]:
        message += "*Users that have been muted:*\n" + "\n".join(result["applied"])

    if result["except"]:
        message += (
            "\n\n*Users that need to be in a voice channel to be muted:*\n"
            + "\n".join(result["except"])
        )

    if result["already"]:
        message += "\n\n*Users that were already muted:*\n" + "\n".join(
            result["already"]
        )

    await send_view(inter, message, delete_after=15.0)


@bot.event
async def on_message(message):

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
