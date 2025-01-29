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

import shared_functions
from commands import gamemaster_commands
from commands.RP_Commands import RPCommands, handle_rp_message, reinstate_rp_cache
from commands.admin_commands import AdminCommands
from commands.character_commands import CharacterCommands
from commands.gamemaster_commands import GamemasterCommands
from commands.player_commands import PlayerCommands
from commands.reviewer_commands import ReviewerCommands
from scheduler_utils import scheduler, scheduled_jobs, remind_users
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

                await cursor.execute(
                    "SELECT Session_ID, Session_Thread, Hammer_Time FROM Sessions WHERE IsActive = 1 AND Hammer_Time > ?",
                    (now.timestamp(),)
                )
                reminders = await cursor.fetchall()

                for reminder in reminders:
                    (session_id, thread_id, hammer_time) = reminder
                    gamemaster_commands.session_reminders(
                        session_id=session_id,
                        thread_id=thread_id,
                        hammer_time=hammer_time,
                        guild_id=guild.id,
                        remind_users=remind_users,
                        scheduler=scheduler,
                        scheduled_jobs=scheduled_jobs,
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
                await cursor.execute("SELECT Search From Admin Where Identifier = 'Sessions_Channel'")
                channel_id = await cursor.fetchone()
                print(channel_id)
                channel = server_bot.get_channel(channel_id[0])
                if not channel:
                    channel = await guild.fetch_channel(channel_id[0])

                for session in sessions:
                    session_id, session_name, message_id, channel_id, hammer_time_str = session
                    session_start_time = datetime.datetime.fromtimestamp(int(hammer_time_str), datetime.timezone.utc)
                    timeout_seconds = (
                            session_start_time - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
                    timeout_seconds = min(timeout_seconds, 12 * 3600)

                    # Fetch the channel and message
                    message = await channel.fetch_message(message_id)

                    # Create a new view with the updated timeout
                    view = gamemaster_commands.JoinOrLeaveSessionView(timeout_seconds=int(timeout_seconds),
                                                                      session_id=session_id, guild=guild,
                                                                      session_name=session_name, content="")
                    await message.edit(view=view)

        except aiosqlite.Error as e:
            logging.exception(f"Failed to reinstate session buttons for guild {guild.id} with error: {e}")


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f"Logged in as {bot.user.name}")
    await bot.add_cog(TestCommands(bot))
    await bot.add_cog(CharacterCommands(bot))
    await bot.add_cog(AdminCommands(bot))
    await bot.add_cog(GamemasterCommands(bot))
    await bot.add_cog(PlayerCommands(bot))
    await bot.add_cog(ReviewerCommands(bot))
    await bot.add_cog(RPCommands(bot))
    print("cogs added")
    await bot.tree.sync()
    print("tree synced.")

    await reinstate_cache(bot)
    await reinstate_rp_cache(bot)
    await reinstate_reminders(bot)
    await shared_functions.config_cache.initialize_configuration(discord_bot=bot)
    await reinstate_session_buttons(bot)
    await bot.loop.create_task(shared_functions.config_cache.refresh_cache_periodically(600, bot))


@bot.event
async def on_disconnect():
    print("Bot is disconnecting.")
last_trigger_time = {}


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
    try:
        async with shared_functions.config_cache.lock:
            configs = shared_functions.config_cache.cache[message.guild.id]
            no_ping_role = configs.get('Do_Not_Ping')
            no_ping_emoji = configs.get('Do_Not_Ping_React')
    except:
        logging.error("Error getting server configs")
        pass
    # Check if the guild is in the cache
    async with shared_functions.approved_channel_cache.lock:
        if guild_id in shared_functions.approved_channel_cache.cache:

            if channel_id in shared_functions.approved_channel_cache.cache[guild_id]:
                logging.debug(f"Channel {channel_id} is approved for RP messages.")
                await handle_rp_message(message)
                if message.mentions:
                    try:
                        if no_ping_role:
                            no_ping_role_flake = message.guild.get_role(no_ping_role)
                            for member in message.mentions:
                                if no_ping_role_flake in member.roles:
                                    await message.add_reaction(no_ping_emoji)
                                    break
                    except:
                        pass

            else:
                logging.debug(f"Channel {channel_id} is not approved. Processing commands.")
                random_number = random.randint(1, 50)
                if message.mentions:
                    try:
                        if no_ping_role:
                            no_ping_role_flake = message.guild.get_role(no_ping_role)
                            for member in message.mentions:

                                if no_ping_role_flake in member.roles:
                                    await message.add_reaction(no_ping_emoji)
                                    break
                    except:
                        pass
                if 'einstein' in message.content.lower():
                    await message.channel.send(
                        "https://i.insider.com/641ca0f5d67fe70018a376ca?width=800&format=jpeg&auto=webp")
                elif 'monkey' in message.content.lower():

                    current_time = datetime.datetime.utcnow()
                    last_time = last_trigger_time.get(channel_id, datetime.datetime.min)
                    if (current_time - last_time).total_seconds() > 300:  # 300 seconds = 5 minutes
                        last_trigger_time[channel_id] = current_time
                        if random_number != 1:
                            await message.channel.send("https://i.ytimg.com/vi/tLHqnn1ZkAM/maxresdefault.jpg")
                        else:
                            await message.channel.send(
                                "https://tenor.com/view/mmmm-monkey-monkey-ug-master-oogway-oogway-gif-19727561")
                    else:
                        logging.debug("Cooldown active. Skipping message.")

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

                if message.author.id == 318796580662542347 and 'stabbed' in message.content.lower():
                    await message.channel.send("https://media.tenor.com/-BpjJcwntaYAAAAM/you-fucking-what-epic-npc-dnd.gif")
                elif message.author.id == 318796580662542347 and 'hit by a car' in message.content.lower():
                    await message.channel.send("https://media.makeameme.org/created/yoooooooooooooooo-how-did.jpg")
                elif message.author.id == 318796580662542347 and 'car wreck' in message.content.lower():
                    await message.channel.send("https://media.makeameme.org/created/yoooooooooooooooo-how-did.jpg")
                elif message.author.id == 318796580662542347 and 'car crash' in message.content.lower():
                    await message.channel.send("https://media.makeameme.org/created/yoooooooooooooooo-how-did.jpg")
                elif message.author.id == 318796580662542347 and 'hit by a truck' in message.content.lower():
                    await message.channel.send("https://media.makeameme.org/created/yoooooooooooooooo-how-did.jpg")
                elif message.author.id == 318796580662542347 and 'got shot' in message.content.lower():
                    await message.channel.send("https://cdn.discordapp.com/attachments/479089930816192513/1330383824315613275/hq720.png?ex=678dc7fd&is=678c767d&hm=a4ae84c616d84827555e18cee3a61337d2f65f36eae0caf89dc9d06bd42377bd&")
                elif message.author.id == 318796580662542347 and 'tried to set me on fire' in message.content.lower():
                    await message.channel.send("https://i.imgflip.com/pwruu.jpg")
                if "%soulisawesome" in message.content.lower():
                    await message.channel.send("https://y.yarn.co/6447b331-7aa2-4785-a5a0-9d20fa4dae35_text.gif")
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
                        await message.channel.send(content=f"You have [meant](https://us-tuna-sounds-images.voicemod.net/c75f5860-13bd-4808-a2ed-3a097f0a24b1.jpg) something {number} times.")
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
                elif 'monkey' in message.content.lower():
                    current_time = datetime.datetime.utcnow()
                    last_time = last_trigger_time.get(channel_id, datetime.datetime.min)
                    if (current_time - last_time).total_seconds() > 300:  # 300 seconds = 5 minutes
                        last_trigger_time[channel_id] = current_time
                        if random_number != 1:
                            await message.channel.send("https://i.ytimg.com/vi/tLHqnn1ZkAM/maxresdefault.jpg")
                        else:
                            await message.channel.send("https://tenor.com/view/mmmm-monkey-monkey-ug-master-oogway-oogway-gif-19727561")
                    else:
                        logging.debug("Cooldown active. Skipping message.")
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

                if message.author.id == 318796580662542347 and 'stabbed' in message.content.lower():
                    await message.channel.send("https://media.tenor.com/-BpjJcwntaYAAAAM/you-fucking-what-epic-npc-dnd.gif")
                elif message.author.id == 318796580662542347 and 'hit by a car' in message.content.lower():
                    await message.channel.send("https://media.makeameme.org/created/yoooooooooooooooo-how-did.jpg")
                elif message.author.id == 318796580662542347 and 'hit by a truck' in message.content.lower():
                    await message.channel.send("https://media.makeameme.org/created/yoooooooooooooooo-how-did.jpg")
                elif message.author.id == 318796580662542347 and 'shot' in message.content.lower():
                    await message.channel.send("https://cdn.discordapp.com/attachments/479089930816192513/1330383824315613275/hq720.png?ex=678dc7fd&is=678c767d&hm=a4ae84c616d84827555e18cee3a61337d2f65f36eae0caf89dc9d06bd42377bd&")
                elif message.author.id == 318796580662542347 and 'tried to set me on fire' in message.content.lower():
                    await message.channel.send("https://i.imgflip.com/pwruu.jpg")
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
                        await message.channel.send(content=f"You have [meant](https://us-tuna-sounds-images.voicemod.net/c75f5860-13bd-4808-a2ed-3a097f0a24b1.jpg) something {number} times. ")
                await bot.process_commands(message)

    # Make sure commands are processed for messages not handled
    await bot.process_commands(message)


@bot.event
async def on_join(guild):
    shutil.copyfile(f"C:/pathparser/pathparser.sqlite",
                    f"C:/pathparser/pathparser_{guild.id}.sqlite")


bot.run(os.getenv("DISCORD_TOKEN"))
bot.loop.create_task(shared_functions.clear_autocomplete_cache())

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='pathparser.log',  # Specify the log file name
    filemode='a'  # Append mode
)
