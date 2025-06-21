import asyncio
import datetime
import logging
import os
import random
import re
import shutil
import aiosqlite
import discord
from discord.ext import commands
from dotenv import load_dotenv
import scheduler_utils
import shared_functions
from commands import gamemaster_commands
from commands.RP_Commands import RPCommands, handle_rp_message, reinstate_rp_cache
from commands.admin_commands import AdminCommands
from commands.character_commands import CharacterCommands
from commands.gamemaster_commands import GamemasterCommands
from commands.kingdom_commands import KingdomCommands
from commands.overseer_commands import OverseerCommands
from commands.player_commands import PlayerCommands
from commands.reviewer_commands import ReviewerCommands
from scheduler_utils import scheduler, scheduled_jobs, remind_users, start_global_scheduler, shutdown_global_scheduler
from test_functions import TestCommands

load_dotenv()

intents = discord.Intents.default()
intents.typing = True
intents.message_content = True
intents.members = True
os.chdir("C:\\pathparser")
bot = commands.Bot(command_prefix="!", intents=intents)


async def reinstate_cache(discord_bot: commands.Bot) -> None:
    for guild in discord_bot.guilds:
        await shared_functions.add_guild_to_cache(guild.id)


async def reinstate_reminders(server_bot) -> None:
    guilds = server_bot.guilds
    now = datetime.datetime.now(datetime.timezone.utc)
    for guild in guilds:
        try:
            async with aiosqlite.connect(f"pathparser_{guild.id}.sqlite") as db:
                cursor = await db.cursor()
                print(f"Reinstating reminders for guild {guild.id}")
                print(now.timestamp())
                await cursor.execute(
                    "SELECT Session_ID, Session_Thread, Hammer_Time FROM Sessions WHERE IsActive = 1 AND Hammer_Time > ?",
                    (now.timestamp(),)
                )
                reminders = await cursor.fetchall()
                print(reminders)
                for reminder in reminders:
                    (session_id, thread_id, hammer_time) = reminder
                    scheduler_utils.schedule_session_reminders(
                        session_id=session_id,
                        thread_id=thread_id,
                        hammer_time=hammer_time,
                        guild_id=guild.id,
                        bot=server_bot
                    )
        except aiosqlite.Error as e:
            logging.exception(f"Failed to reinstate reminders for guild {guild.id} with error: {e}")


async def reinstate_session_buttons(server_bot) -> None:
    guilds = server_bot.guilds
    now = datetime.datetime.now(datetime.timezone.utc)

    for guild in guilds:
        try:
            async with aiosqlite.connect(f"pathparser_{guild.id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute(
                    "SELECT Session_ID, Session_Name, Message, Session_Thread, Hammer_Time FROM Sessions WHERE IsActive = 1 AND hammer_time > ?",
                    (now.timestamp(),)
                )
                sessions = await cursor.fetchall()

                await cursor.execute("SELECT Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
                channel_id = await cursor.fetchone()
                logging.info(f"Found sessions channel: {channel_id}")

                # Try to get the channel from cache, or fetch it.
                channel = server_bot.get_channel(channel_id[0])
                if not channel:
                    channel = await guild.fetch_channel(channel_id[0])

                for session in sessions:
                    session_id, session_name, message_id, channel_id, hammer_time_str = session
                    session_start_time = datetime.datetime.fromtimestamp(int(hammer_time_str), datetime.timezone.utc)
                    timeout_seconds = (
                            session_start_time - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
                    # Cap the timeout at 12 hours.
                    timeout_seconds = min(timeout_seconds, 12 * 3600)

                    # Fetch the message to be edited.
                    try:
                        message = await channel.fetch_message(message_id)
                    except discord.HTTPException as http_err:
                        logging.exception(f"Failed to fetch message {message_id} in guild {guild.id}: {http_err}")
                        continue  # Skip to the next session

                    # Create a new view with the updated timeout.
                    view = gamemaster_commands.JoinOrLeaveSessionView(
                        timeout_seconds=int(timeout_seconds),
                        session_id=session_id,
                        guild=guild,
                        session_name=session_name,
                        content=""
                    )

                    # Try to edit the message. If a rate limit occurs, wait and try again.
                    try:
                        await message.edit(view=view)
                    except discord.HTTPException as http_err:
                        logging.warning(f"Rate limit editing message {message_id} in guild {guild.id}: {http_err}")
                        # Optionally sleep for a couple seconds and then try again:
                        await asyncio.sleep(2)
                        try:
                            await message.edit(view=view)
                        except discord.HTTPException as http_err_retry:
                            logging.exception(
                                f"Retry failed for message {message_id} in guild {guild.id}: {http_err_retry}")
                            continue  # Skip this session if it still fails

                    # Add a small delay to prevent hammering the API.
                    await asyncio.sleep(0.5)

        except aiosqlite.Error as e:
            logging.exception(f"Failed to reinstate session buttons for guild {guild.id} with error: {e}")
        except Exception as general_e:
            logging.exception(f"An unexpected error occurred for guild {guild.id}: {general_e}")


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    await bot.add_cog(TestCommands(bot))
    await bot.add_cog(CharacterCommands(bot))
    await bot.add_cog(AdminCommands(bot))
    await bot.add_cog(GamemasterCommands(bot))
    await bot.add_cog(PlayerCommands(bot))
    await bot.add_cog(ReviewerCommands(bot))
    await bot.add_cog(RPCommands(bot))
    await bot.add_cog(KingdomCommands(bot))
    await bot.add_cog(OverseerCommands(bot))
    await bot.tree.sync()
    await start_global_scheduler()
    await reinstate_reminders(bot)
    await reinstate_session_buttons(bot)
    await reinstate_cache(bot)
    await reinstate_rp_cache(bot)
    await shared_functions.config_cache.initialize_configuration(discord_bot=bot)
    await bot.loop.create_task(shared_functions.config_cache.refresh_cache_periodically(600, bot))


@bot.event
async def on_disconnect():
    print("Bot is disconnecting.")
    scheduler_utils.shutdown_global_scheduler()


@bot.event
async def on_connect():
    await start_global_scheduler()


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    guild_id = message.guild.id
    logging.debug(f"Processing message in guild {guild_id} from {message.author}")
    if isinstance(message.channel, discord.channel.TextChannel):
        channel_id = message.channel.id
    elif isinstance(message.channel, discord.channel.Thread):
        channel_id = message.channel.parent_id
    else:
        channel_id = None
    # Check if the guild is in the cache
    async with shared_functions.approved_channel_cache.lock:
        if guild_id in shared_functions.approved_channel_cache.cache:

            if channel_id in shared_functions.approved_channel_cache.cache[guild_id]:
                logging.debug(f"Channel {channel_id} is approved for RP messages.")
                await handle_rp_message(message)
            else:
                logging.debug(f"Channel {channel_id} is not approved. Processing commands.")
                random_number = random.randint(1, 50)
                if 'einstein' in message.content.lower():
                    await message.channel.send(
                        "https://i.insider.com/641ca0f5d67fe70018a376ca?width=800&format=jpeg&auto=webp")
                elif 'monkey' in message.content.lower() and random_number != 1:
                    await message.channel.send("https://i.ytimg.com/vi/tLHqnn1ZkAM/maxresdefault.jpg")
                elif 'monkey' in message.content.lower() and random_number == 1:
                    await message.channel.send(
                        "https://tenor.com/view/mmmm-monkey-monkey-ug-master-oogway-oogway-gif-19727561")
                if random_number == 1 and message.author.id == 217873501313433600:
                    await message.channel.send(
                        "https://cdn.discordapp.com/attachments/479089930816192513/1309682327860805733/7YjmdoZxhSgAAAAASUVORK5CYII.png?ex=67768b77&is=677539f7&hm=9ebebdcbf4c8f1266649c1d1d66dbcdad58b18f1a219da101094a96f910d396c&")
                elif random_number == 2 and message.author.id == 217873501313433600:
                    await message.channel.send(
                        "https://cdn.discordapp.com/attachments/479089930816192513/1309681542653546560/764rjEg82XSZ0fJzf8fVPtjhVRebgAAAAASUVORK5CYII.png?ex=67768abc&is=6775393c&hm=1728ae88544b6323a3d280dc552bb48eff922f3c0cf3983e341654cb4eb61022&")
                elif random_number == 3 and message.author.id == 217873501313433600:
                    await message.channel.send(
                        "https://cdn.discordapp.com/attachments/479089930816192513/1309681106013917284/wdUWYUf3MwhkwAAAABJRU5ErkJggg.png?ex=67768a54&is=677538d4&hm=bd846ce7d3f0ab3361170189bfc57520357ada3740ec61af1cfe7e9a5be3cf2d&")
                elif random_number == 4 and message.author.id == 217873501313433600:
                    await message.channel.send(
                        "https://cdn.discordapp.com/attachments/479089930816192513/1322782239452430467/4OGDuJJjqwVJFdQkOvEm71fkWBFQVWFFhRYEWBFQWWBRYAfoXa71Wo11RYEWBFQVWFFhRYCkFPgUCd2wuGYpcgwAAAABJRU5ErkJggg.png?ex=6776bdb5&is=67756c35&hm=35c2b303e206d87b60edc261f3134c6a072af9255a5a721e1a0cfa377fcb20a6&")
                guild_id = message.guild.id
                swears = {
                    "fuck": 0,
                    "shit": 0,
                    "damn": 0,
                    "bitch": 0,
                    "ass": 0,
                }

                # Normalize the string (optional)
                normalized_string = message.content.lower()

                # Count occurrences of each fruit in the string
                for swear in swears.keys():
                    # Use regex to match whole words
                    swears[swear] = len(re.findall(rf"\b{swear}\b", normalized_string))

                # Calculate total occurrences
                total_count = sum(swears.values())
                if total_count > 1 and message.author.id == 243120409703088128:
                    hostility = min(100, int((total_count / 5) * 100))
                    if 0 <= random_number <= 17:
                        await message.channel.send(f"Hostility Detected: {hostility}% Someone's a salty boy! :)")
                    elif 18 <= random_number <= 34:
                        await message.channel.send(f"Wow. Someone's feeling mean today! He's {hostility}% hostile!")
                    elif 35 <= random_number <= 50:
                        await message.channel.send(
                            f"Angry dog off the leash! he's feeling {hostility}% hostile! Someone better get his waifu before he wreck his laifu.")
                if message.author.id == 243120409703088128 and 'I mean' in message.content:
                    async with aiosqlite.connect(f"origin.sqlite") as db:
                        cursor = await db.cursor()
                        await cursor.execute("SELECT instances from Memes where name = 'IMean'")
                        instances = await cursor.fetchone()
                        number = instances[0] + 1
                        await cursor.execute("UPDATE Memes SET instances = ? WHERE name = 'IMean'", (number,))
                        await db.commit()
                        await message.channel.send(
                            content=f"You have [meant](https://us-tuna-sounds-images.voicemod.net/c75f5860-13bd-4808-a2ed-3a097f0a24b1.jpg) something {number} times.")
                await bot.process_commands(message)
        else:
            # Guild not in cache, add it

            logging.debug(f"Guild {guild_id} not in cache. Adding.")
            await shared_functions.add_guild_to_cache(guild_id)
            if channel_id in shared_functions.approved_channel_cache.cache[guild_id]:
                logging.debug(f"Channel {channel_id} is approved after cache update.")
                await handle_rp_message(message)
            else:
                logging.debug(f"Channel {channel_id} is still not approved. Processing commands.")
                random_number = random.randint(1, 50)
                if 'einstein' in message.content.lower():
                    await message.channel.send(
                        "https://i.insider.com/641ca0f5d67fe70018a376ca?width=800&format=jpeg&auto=webp")
                elif 'monkey' in message.content.lower() and random_number != 1:
                    await message.channel.send("https://i.ytimg.com/vi/tLHqnn1ZkAM/maxresdefault.jpg")
                elif 'monkey' in message.content.lower() and random_number == 1:
                    await message.channel.send(
                        "https://tenor.com/view/mmmm-monkey-monkey-ug-master-oogway-oogway-gif-19727561")
                if random_number == 1 and message.author.id == 217873501313433600:
                    await message.channel.send(
                        "https://cdn.discordapp.com/attachments/479089930816192513/1309682327860805733/7YjmdoZxhSgAAAAASUVORK5CYII.png?ex=67768b77&is=677539f7&hm=9ebebdcbf4c8f1266649c1d1d66dbcdad58b18f1a219da101094a96f910d396c&")
                elif random_number == 2 and message.author.id == 217873501313433600:
                    await message.channel.send(
                        "https://cdn.discordapp.com/attachments/479089930816192513/1309681542653546560/764rjEg82XSZ0fJzf8fVPtjhVRebgAAAAASUVORK5CYII.png?ex=67768abc&is=6775393c&hm=1728ae88544b6323a3d280dc552bb48eff922f3c0cf3983e341654cb4eb61022&")
                elif random_number == 3 and message.author.id == 217873501313433600:
                    await message.channel.send(
                        "https://cdn.discordapp.com/attachments/479089930816192513/1309681106013917284/wdUWYUf3MwhkwAAAABJRU5ErkJggg.png?ex=67768a54&is=677538d4&hm=bd846ce7d3f0ab3361170189bfc57520357ada3740ec61af1cfe7e9a5be3cf2d&")
                elif random_number == 4 and message.author.id == 217873501313433600:
                    await message.channel.send(
                        "https://cdn.discordapp.com/attachments/479089930816192513/1322782239452430467/4OGDuJJjqwVJFdQkOvEm71fkWBFQVWFFhRYEWBFQWWBRYAfoXa71Wo11RYEWBFQVWFFhRYCkFPgUCd2wuGYpcgwAAAABJRU5ErkJggg.png?ex=6776bdb5&is=67756c35&hm=35c2b303e206d87b60edc261f3134c6a072af9255a5a721e1a0cfa377fcb20a6&")
                guild_id = message.guild.id
                swears = {
                    "fuck": 0,
                    "shit": 0,
                    "damn": 0,
                    "bitch": 0,
                    "ass": 0,
                }

                # Normalize the string (optional)
                normalized_string = message.content.lower()

                # Count occurrences of each fruit in the string
                for swear in swears.keys():
                    # Use regex to match whole words
                    swears[swear] = len(re.findall(rf"\b{swear}\b", normalized_string))

                # Calculate total occurrences
                total_count = sum(swears.values())
                if total_count > 1 and message.author.id == 243120409703088128:
                    hostility = min(100, int((total_count / 5) * 100))
                    if 0 <= random_number <= 17:
                        await message.channel.send(f"Hostility Detected: {hostility}% Someone's a salty boy! :)")
                    elif 18 <= random_number <= 34:
                        await message.channel.send(f"Wow. Someone's feeling mean today! He's {hostility}% hostile!")
                    elif 35 <= random_number <= 50:
                        await message.channel.send(
                            f"Angry dog off the leash! he's feeling {hostility}% hostile! Someone better get his waifu before he wreck his laifu.")
                if message.author.id == 243120409703088128 and 'I mean' in message.content:
                    async with aiosqlite.connect(f"origin.sqlite") as db:
                        cursor = await db.cursor()
                        await cursor.execute("SELECT instances from Memes where name = 'IMean'")
                        instances = await cursor.fetchone()
                        number = instances[0] + 1
                        await cursor.execute("UPDATE Memes SET instances = ? WHERE name = 'IMean'", (number,))
                        await db.commit()
                        await message.channel.send(
                            content=f"You have [meant](https://us-tuna-sounds-images.voicemod.net/c75f5860-13bd-4808-a2ed-3a097f0a24b1.jpg) something {number} times. ")
                await bot.process_commands(message)

    # Make sure commands are processed for messages not handled
    await bot.process_commands(message)


@bot.event
async def on_join(guild):
    shutil.copyfile(f"C:/pathparser/pathparser.sqlite",
                    f"C:/pathparser/pathparser_{guild.id}.sqlite")


bot.run(os.getenv("DISCORD_TOKEN_V2"))


bot.loop.create_task(shared_functions.clear_autocomplete_cache())

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='pathparser.log',  # Specify the log file name
    filemode='a'  # Append mode
)
