# scheduler_utils.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import logging

# Initialize the scheduler
scheduler = AsyncIOScheduler()
scheduler.start()
scheduled_jobs = {}


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


def parse_hammer_time(hammer_time_str: str) -> datetime:
    # Implement your hammer time parsing logic
    return datetime.strptime(hammer_time_str, '%Y-%m-%d %H:%M:%S')
