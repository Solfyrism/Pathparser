# scheduler_utils.py
import asyncio

import aiosqlite
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone
import logging

# Initialize the scheduler
scheduler = AsyncIOScheduler()
scheduler.start()
scheduled_jobs = {}


# Initialize the scheduler
scheduler = AsyncIOScheduler()
scheduler.start()
scheduled_jobs = {}


async def remind_users(session_id: int, guild_id: int, thread_id: int, time: int, bot: discord.Client) -> None:
    try:
        content = f"Reminder: The event is starting in {time} minutes."
        async with aiosqlite.connect("pathparser.db") as db:
            cursor = await db.execute(
                "SELECT Player_ID FROM Sessions_Participants WHERE session_id = ? AND Notification_Warning = ?",
                (session_id, time))
            players = await cursor.fetchall()
            for player in players:
                user = bot.get_user(player[0])
                if user is not None:
                    content = f"{user.mention} " + content
            guild = bot.get_guild(guild_id)
            thread = guild.get_thread(thread_id)
            if thread is None:
                thread = await guild.fetch_channel(thread_id)
            if thread is None:
                raise ValueError(f"Thread {thread_id} not found in guild {guild_id}")
            else:
                await thread.send(content=content, allowed_mentions=discord.AllowedMentions(users=True))
    except (aiosqlite.Error, TypeError) as e:
        logging.exception(
            f"Failed to run scheduled task for guild_id {guild_id}, session_id {session_id}, thread_id {thread_id}, with error: {e}")


def session_reminders(
        scheduler, remind_users, scheduled_jobs, session_id: int, thread_id: int, hammer_time: str, guild_id: int,
        bot: discord.Client
) -> None:
    now = datetime.now(timezone.utc)  # Make 'now' timezone-aware
    session_start_time = parse_hammer_time(hammer_time)  # Ensure this is timezone-aware
    time_difference = session_start_time - now
    remaining_minutes = time_difference.total_seconds() / 60
    reminder_time_periods = [0, 30, 60]

    for time in reminder_time_periods:
        if remaining_minutes >= time:
            reminder_time = session_start_time - timedelta(minutes=time)
            job = scheduler.add_job(
                remind_users,
                'date',
                run_date=reminder_time,
                args=[session_id, guild_id, thread_id, time, bot]
            )
            scheduled_jobs[(session_id, time)] = job


def parse_hammer_time(hammer_time_str: str) -> datetime:
    if len(hammer_time_str) == 10:
        # Unix timestamp, return aware datetime
        return datetime.fromtimestamp(int(hammer_time_str), tz=timezone.utc)
    else:
        # Parse string and set timezone to UTC
        dt_naive = datetime.strptime(hammer_time_str, '%Y-%m-%d %H:%M:%S')
        dt_aware = dt_naive.replace(tzinfo=timezone.utc)
        return dt_aware