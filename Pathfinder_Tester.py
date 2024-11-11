import datetime
import aiosqlite
import discord
from discord.ext import commands
import os
from test_functions import TestCommands
from commands.character_commands import CharacterCommands
from commands.admin_commands import AdminCommands
from commands.gamemaster_commands import GamemasterCommands
from commands.player_commands import PlayerCommands
import logging
import shared_functions
from commands import gamemaster_commands
from scheduler_utils import session_reminders, scheduler, scheduled_jobs
from dotenv import load_dotenv;
load_dotenv()

intents = discord.Intents.default()
intents.typing = True
intents.message_content = True
intents.members = True
os.chdir("C:\\pathparser")
bot = commands.Bot(command_prefix="!", intents=intents)


async def reinstate_reminders(server_bot) -> None:
    guilds = server_bot.guilds
    now = datetime.datetime.now(datetime.timezone.utc)
    for guild in guilds:
        async with aiosqlite.connect(f"pathparser_{guild.id}_test..sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "SELECT Session_ID, Thread_ID, Hammer_Time FROM Sessions WHERE IsActive = 1 AND Hammer_Time > ?",
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
                    scheduled_jobs=scheduled_jobs
                )


@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f"Logged in as {bot.user.name}")
    await bot.add_cog(TestCommands(bot))
    await bot.add_cog(CharacterCommands(bot))
    await bot.add_cog(AdminCommands(bot))
    await bot.add_cog(GamemasterCommands(bot))
    await bot.add_cog(PlayerCommands(bot))

    await bot.tree.sync()
    await reinstate_reminders(bot)
    await reinstate_session_buttons(bot)


@bot.event
async def on_disconnect():
    print("Bot is disconnecting.")


bot.run(os.getenv("DISCORD_TOKEN_V2"))
bot.loop.create_task(shared_functions.clear_autocomplete_cache())

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='pathparser.log',  # Specify the log file name
    filemode='a'  # Append mode
)





async def reinstate_reminders(server_bot) -> None:
    guilds = server_bot.guilds
    now = datetime.datetime.utcnow()
    for guild in guilds:
        async with aiosqlite.connect(f"pathparser_{guild.id}_test..sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "SELECT Session_ID, Thread_ID, Hammer_Time FROM Sessions WHERE IsActive = 1 AND Hammer_Time > ?",
                (now.timestamp(),)
            )
            reminders = await cursor.fetchall()
            for reminder in reminders:
                (session_id, thread_id, hammer_time) = reminder
                session_reminders(
                    scheduler=scheduler,
                    remind_users=remind_users,
                    scheduled_jobs=scheduled_jobs,
                    session_id=session_id,
                    thread_id=thread_id,
                    hammer_time=hammer_time,
                    guild_id=guild.id
                )