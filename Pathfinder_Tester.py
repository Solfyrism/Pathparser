import datetime
import aiosqlite
import discord
from discord.ext import commands
from dotenv import load_dotenv;

load_dotenv()
import os
from test_functions import TestCommands
from commands.character_commands import CharacterCommands
from commands.admin_commands import AdminCommands
from commands.gamemaster_commands import GamemasterCommands
from commands.player_commands import PlayerCommands

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import shared_functions
from commands import gamemaster_commands
from scheduler
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
        async with aiosqlite.connect(f"pathparser_{guild.id}.sqlite") as db:
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


async def remind_users(session_id: int, guild_id: int, thread_id: int, time: int):
    try:
        content = f"Reminder: The event is starting in {time} minutes."
        async with aiosqlite.connect("pathparser.db") as db:
            cursor = await db.cursor
            await cursor.execute(
                "SELECT Player_ID FROM Sessions_Participants WHERE session_id = ? AND Notification_Warning = ?",
                (session_id, time))
            players = await cursor.fetchall()
            for player in players:
                user = bot.get_user(player[0])
                if user is not None:
                    content = f"{user.mention}" + content
            guild = bot.get_guild(guild_id)
            thread = guild.get_thread(thread_id)
            if thread is None:
                thread = await guild.fetch_channel(thread_id)
            if thread is None:
                raise ValueError(f"Thread {thread_id} not found in guild {guild_id}")
            else:
                await thread.send(content=content, allowed_mentions=discord.AllowedMentions.users())
    except (aiosqlite.Error, TypeError) as e:
        logging.exception(
            f"failed to run scheduled task for {guild_id}, session_id {session_id} {thread_id}, with error: {e}")

async def reinstate_session_buttons(server_bot) -> None:
    guilds = server_bot.guilds
    now = datetime.datetime.now(datetime.timezone.utc)
    for guild in guilds:
        async with aiosqlite.connect(f"pathparser_{guild.id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "SELECT Session_ID, Session_Name, Message, Channel_ID, hammer_time FROM Sessions WHERE IsActive = 1 AND hammer_time > ?",
                (now.timestamp(),)
            )
            sessions = await cursor.fetchall()
            for session in sessions:
                session_id, session_name, message_id, channel_id, hammer_time_str = session
                session_start_time = datetime.datetime.strptime(hammer_time_str, '%Y-%m-%d %H:%M:%S')
                timeout_seconds = (session_start_time - datetime.datetime.utcnow()).total_seconds()
                timeout_seconds = min(timeout_seconds, 12 * 3600)

                # Fetch the channel and message
                channel = server_bot.get_channel(channel_id)
                message = await channel.fetch_message(message_id)

                # Create a new view with the updated timeout
                view = gamemaster_commands.JoinOrLeaveSessionView(timeout_seconds=int(timeout_seconds),
                                                                  session_id=session_id, guild=guild,
                                                                  session_name=session_name)
                await message.edit(view=view)
