# scheduler_utils.py
import asyncio

import aiosqlite
import discord
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone
import logging

# Optional: Configure logging for APScheduler for better debugging
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# Initialize the scheduler ONCE
scheduler = AsyncIOScheduler(timezone=pytz.utc)  # Or timezone.utc if not using pytz
scheduled_jobs = {}

# --- Your other bot setup code follows ---

# This MUST be called from within an async function where the event loop is running
async def start_global_scheduler():
    """Starts the global scheduler if it's not already running."""
    if not scheduler.running:
        try:
            scheduler.start()
            print(f"Scheduler started successfully. Running: {scheduler.running}")
            logging.info(f"Scheduler started successfully. Running: {scheduler.running}")
        except RuntimeError as e:
             print(f"Scheduler might already be running or loop issue: {e}")
             logging.warning(f"Scheduler start attempt caused RuntimeError (might be ok if already running): {e}")
        except Exception as e:
            print(f"Error starting scheduler: {e}")
            logging.exception("Error starting scheduler:")
    else:
        print(f"Scheduler is already running. Running: {scheduler.running}")
        logging.info(f"Scheduler is already running. Running: {scheduler.running}")


# --- Function to SHUT DOWN the scheduler ---
def shutdown_global_scheduler():
    """Shuts down the global scheduler."""
    if scheduler.running:
        try:
            # wait=False allows shutdown even if called from within event loop task sometimes?
            # Adjust based on testing if needed. True might be safer if called outside loop context.
            scheduler.shutdown(wait=False)
            print("Scheduler shutdown initiated.")
            logging.info("Scheduler shutdown initiated.")
        except Exception as e:
            print(f"Error shutting down scheduler: {e}")
            logging.exception("Error shutting down scheduler:")
    else:
        print("Scheduler is not running.")
        logging.info("Scheduler is not running.")


async def remind_users(session_id: int, guild_id: int, thread_id: int, time: int, bot: discord.Client) -> None:
    print(f"[Scheduler] Attempting to run remind_users for session {session_id} ({time} min)")  # DEBUG PRINT
    logging.info(f"Running reminder job for session {session_id}, guild {guild_id}, thread {thread_id}, time {time}")
    try:
        content = f"Reminder: The event is starting in {time} minutes."
        mentions = []
        async with aiosqlite.connect(f"pathparser_{guild_id}.sqlite") as db:  # Ensure DB path is correct
            # Make sure the table/column names are exact matches
            async with db.execute(
                    "SELECT Player_ID FROM Sessions_Participants WHERE Session_ID = ? AND Notification_Warning = ?",
                    # Case-sensitive?
                    (session_id, time)
            ) as cursor:
                players = await cursor.fetchall()

        mention_str = ""
        if players:
            for player in players:
                try:
                    # Consider using fetch_user for potentially uncached users, though get_user is faster if cached.
                    user = bot.get_user(player[0])
                    if user:
                        mentions.append(user)  # Collect users for AllowedMentions
                        mention_str += f"{user.mention} "
                    else:
                        logging.warning(
                            f"Could not find user with ID {player[0]} in cache for session {session_id} reminder.")
                except Exception as e:
                    logging.error(f"Error processing player ID {player[0]} for mention: {e}")

        content = mention_str + content if mention_str else content  # Prepend mentions if any

        guild = bot.get_guild(guild_id)
        if not guild:
            logging.error(f"Could not find guild with ID {guild_id} for session {session_id} reminder.")
            return  # Cannot proceed without guild

        thread = guild.get_thread(thread_id)
        if thread is None:
            logging.warning(f"Thread {thread_id} not in cache for guild {guild_id}. Fetching...")
            try:
                thread = await guild.fetch_channel(thread_id)  # fetch_channel can fetch threads too
            except discord.NotFound:
                logging.error(f"Thread {thread_id} not found in guild {guild_id} after fetching.")
                thread = None  # Explicitly set to None
            except discord.Forbidden:
                logging.error(f"Bot lacks permission to fetch channel/thread {thread_id} in guild {guild_id}.")
                thread = None
            except Exception as e:
                logging.exception(f"Unexpected error fetching thread {thread_id}: {e}")
                thread = None

        if thread:
            try:
                await thread.send(content=content.strip(), allowed_mentions=discord.AllowedMentions(users=mentions))
                logging.info(f"Reminder sent to thread {thread_id} for session {session_id} ({time} min).")
                print(f"[Scheduler] Reminder sent successfully for session {session_id} ({time} min)")  # DEBUG PRINT
            except discord.Forbidden:
                logging.error(f"Bot lacks permission to send messages in thread {thread_id} (guild {guild_id}).")
            except discord.HTTPException as e:
                logging.exception(f"Failed to send reminder message to thread {thread_id}: {e}")
            except Exception as e:
                logging.exception(f"Unexpected error sending message to thread {thread_id}: {e}")
        else:
            # Log error if thread wasn't found even after fetching
            logging.error(
                f"Cannot send reminder for session {session_id} because thread {thread_id} could not be found or accessed.")

    except aiosqlite.Error as e:
        logging.exception(f"Database error during reminder job for session {session_id}: {e}")
    except Exception as e:  # Catch broader errors during setup/retrieval phase
        logging.exception(
            f"Unexpected error in remind_users for session {session_id}, guild {guild_id}, thread {thread_id}, time {time}: {e}")


def schedule_session_reminders(
        session_id: int,
        thread_id: int,
        hammer_time: str,
        guild_id: int,
        bot: discord.Client
) -> None:
    """Schedules 0, 30, and 60-minute reminders for a session."""
    print(f"Attempting to schedule reminders for session {session_id}...")
    logging.info(
        f"Scheduling reminders for session_id={session_id}, thread_id={thread_id}, guild_id={guild_id}, hammer_time='{hammer_time}'")

    # Use the globally defined scheduler and jobs dictionary
    global scheduler, scheduled_jobs

    if not scheduler.running:
        logging.error("Cannot schedule reminders: Scheduler is not running!")
        print("Cannot schedule reminders: Scheduler is not running!")
        return

    try:
        session_start_time = parse_hammer_time(hammer_time)
        # Add check: Is session_start_time in the past?
        now = datetime.now(timezone.utc)
        if session_start_time <= now:
            logging.warning(
                f"Session {session_id} start time {session_start_time} is in the past. No reminders scheduled.")
            print(f"Session {session_id} start time {session_start_time} is in the past. No reminders scheduled.")
            return

        time_difference = session_start_time - now
        remaining_minutes = time_difference.total_seconds() / 60
        reminder_time_periods = [0, 30, 60]  # Minutes before start time

        print(f"  Session start: {session_start_time}, Time remaining: {remaining_minutes:.2f} minutes")

        for time in reminder_time_periods:
            # Only schedule if the reminder time is in the future
            if remaining_minutes >= time:
                reminder_time = session_start_time - timedelta(minutes=time)
                # Double-check reminder_time is still in the future (handles edge case near start time)
                if reminder_time > now:
                    job_id = f"session_{session_id}_reminder_{time}min"  # Unique ID for the job
                    print(f"  Scheduling job {job_id} for {reminder_time}")
                    try:
                        job = scheduler.add_job(
                            remind_users,  # The async function to run
                            'date',  # Trigger type: run once at specific date/time
                            run_date=reminder_time,  # The calculated UTC time for the reminder
                            args=[session_id, guild_id, thread_id, time, bot],  # Args for remind_users
                            id=job_id,  # Assign the unique ID
                            misfire_grace_time=90,  # Allow 90 secs delay if scheduler misses exact time
                            replace_existing=True  # Overwrite if a job with same ID exists
                        )
                        scheduled_jobs[(session_id, time)] = job  # Store reference if needed
                        logging.info(f"Scheduled job {job_id} for {reminder_time}. Job details: {job}")
                        print(f"  Job added: {job}")
                    except Exception as e:
                        logging.exception(f"Failed to add job {job_id} to scheduler: {e}")
                        print(f"  ERROR adding job {job_id}: {e}")
                else:
                    logging.warning(
                        f"Skipping {time} min reminder for session {session_id} as calculated reminder time {reminder_time} is in the past.")
                    print(f"  Skipping {time} min reminder as calculated time {reminder_time} is in the past.")
            else:
                logging.info(
                    f"Skipping {time} min reminder for session {session_id} as event starts too soon ({remaining_minutes:.2f} mins remaining).")
                print(
                    f"  Skipping {time} min reminder as event starts too soon ({remaining_minutes:.2f} mins remaining).")

    except ValueError as e:  # Catch parsing errors from parse_hammer_time
        logging.error(f"Failed to schedule reminders for session {session_id} due to invalid hammer_time: {e}")
        print(f"Failed to schedule reminders for session {session_id} due to invalid hammer_time: {e}")
    except Exception as e:
        logging.exception(f"An unexpected error occurred during scheduling for session {session_id}: {e}")
        print(f"An unexpected error occurred during scheduling for session {session_id}: {e}")


def parse_hammer_time(hammer_time_str: str) -> datetime:
    try:
        # Check if it's a pure integer string representing a Unix timestamp
        if hammer_time_str.isdigit():
            # Assume it's a Unix timestamp (seconds since epoch)
            ts = int(hammer_time_str)
            # Create timezone-aware datetime object in UTC
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            logging.debug(f"Parsed timestamp '{hammer_time_str}' to {dt}")
            return dt
        else:
            # Assume format 'YYYY-MM-DD HH:MM:SS' and assign UTC
            dt_naive = datetime.strptime(hammer_time_str, '%Y-%m-%d %H:%M:%S')
            # Make it timezone-aware, assuming UTC
            dt_aware = dt_naive.replace(tzinfo=timezone.utc)
            logging.debug(f"Parsed datetime string '{hammer_time_str}' to {dt_aware}")
            return dt_aware
    except (ValueError, TypeError) as e:
        logging.error(f"Error parsing hammer_time '{hammer_time_str}': {e}")
        # Decide error handling: raise, return None, return default?
        raise ValueError(f"Invalid hammer_time format: {hammer_time_str}") from e