# scheduler_utils.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import logging

# Initialize the scheduler
scheduler = AsyncIOScheduler()
scheduler.start()
scheduled_jobs = {}

def session_reminders(scheduler, remind_users, scheduled_jobs, session_id: int, thread_id: int, hammer_time: str, guild_id: int) -> None:
    now = datetime.utcnow()
    session_start_time = parse_hammer_time(hammer_time)
    time_difference = session_start_time - now
    remaining_minutes = time_difference.total_seconds() / 60
    reminder_time_periods = [0, 30, 60]

    for time in reminder_time_periods:
        if remaining_minutes >= time:
            reminder_time = session_start_time - timedelta(minutes=time)
            job = scheduler.add_job(
                remind_users,
                trigger='date',
                run_date=reminder_time,
                args=[session_id, guild_id, thread_id, time],
            )
            scheduled_jobs[(session_id, time)] = job

def parse_hammer_time(hammer_time_str: str) -> datetime:
    # Implement your hammer time parsing logic
    return datetime.strptime(hammer_time_str, '%Y-%m-%d %H:%M:%S')