import datetime
import logging
import math
import os
import random
import typing
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Union
import aiosqlite
import discord
from discord import app_commands, Embed, TextChannel
from discord.ext import commands
from matplotlib import pyplot as plt

import commands.character_commands as character_commands
import commands.player_commands as player_commands
import shared_functions
from scheduler_utils import scheduled_jobs, remind_users, scheduler, session_reminders
from shared_functions import name_fix

# Handler for RP messages
async def handle_rp_message(message):
    # Ignore messages wrapped in parentheses (OOC)
    content = message.content.strip()
    if content.startswith('(') and content.endswith(')'):
        return

    user_id = message.author.id
    now = datetime.utcnow()

    # Start a database session
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()

    # If user doesn't exist, create a new record
    if not user:
        user = User(
            user_id=user_id,
            balance=0,
            last_post_time=None,
            recent_posts='[]'
        )
        session.add(user)
        session.commit()

    # Load recent posts from the database
    recent_posts = json.loads(user.recent_posts)

    # Content Quality Check
    if len(content) < MIN_CONTENT_LENGTH:
        await message.channel.send(
            f"{message.author.mention}, your post is too short to earn rewards."
        )
        session.close()
        return

    # Content Similarity Check
    is_similar = False
    truncated_content = truncate_text(content)

    for past_content in recent_posts[-MAX_COMPARISONS:]:
        truncated_past_content = truncate_text(past_content)

        # Time the similarity calculation
        start_time = asyncio.get_event_loop().time()

        similarity_ratio = difflib.SequenceMatcher(None, truncated_content, truncated_past_content).ratio()

        elapsed_time = asyncio.get_event_loop().time() - start_time

        if elapsed_time > SIMILARITY_TIMEOUT:
            # Skip this check if it takes too long
            continue

        if similarity_ratio > SIMILARITY_THRESHOLD:
            is_similar = True
            break

    if is_similar:
        await message.channel.send(
            f"{message.author.mention}, your post is too similar to your recent posts and won't earn rewards."
        )
        session.close()
        return

    # Time since last post
    if user.last_post_time:
        time_since_last_post = (now - user.last_post_time).total_seconds()
    else:
        time_since_last_post = None  # First recorded post

    # Update user's last post time
    user.last_post_time = now

    # Append current post to recent posts
    recent_posts.append(content)
    # Keep only the last 5 posts
    recent_posts = recent_posts[-5:]
    user.recent_posts = json.dumps(recent_posts)

    # Calculate Reward
    content_length = len(content)
    reward = calculate_reward(content_length, time_since_last_post)

    # Update user's balance
    user.balance += reward
    session.commit()
    session.close()

    # Provide feedback to the user
    await message.channel.send(
        f"{message.author.mention}, you have earned {reward} coins! Your new balance is {user.balance} coins."
    )
def truncate_text(text):
    """Truncate text to the maximum similarity length."""
    return text[:MAX_SIMILARITY_LENGTH]

def calculate_reward(content_length, time_since_last_post):
    """
    Calculate the reward based on content length and time since last post.
    Rewards increase with longer intervals between posts, up to a maximum cap.
    """
    # Base reward: 1 coin per 10 characters
    base_reward = content_length // 10

    # Time bonus: Additional coins based on time since last post
    if time_since_last_post is not None:
        MAX_TIME = 6 * 60 * 60  # 6 hours in seconds
        time_bonus_seconds = min(time_since_last_post, MAX_TIME)
        time_bonus = int(time_bonus_seconds // (30 * 60))  # 1 coin per 30 minutes
    else:
        time_bonus = 0  # No time bonus for first post

    # Total reward calculation
    total_reward = base_reward + time_bonus

    # Enforce minimum and maximum rewards
    MIN_REWARD = 1
    MAX_REWARD = 100
    total_reward = max(MIN_REWARD, min(total_reward, MAX_REWARD))

    return total_reward











class RPCommands(commands.Cog, name='RP'):
    def __init__(self, bot):
        self.bot = bot
