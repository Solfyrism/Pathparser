from dataclasses import dataclass, field
from typing import Dict

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import aiosqlite
import asyncio
import json
import difflib
from datetime import datetime


@dataclass
class RoleplayInfoCache:
    cache: Dict[int, tuple] = field(default_factory=dict)  # Replace 'tuple' with the actual value type if known
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


async def add_guild_to_rp_cache(guild_id: int) -> RoleplayInfoCache:
    cache = RoleplayInfoCache()
    async with aiosqlite.connect(f"pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT Minimum_Post_Length_In_Characters, Similarity_Threshold, Minimum_Rewards, Maximum_Rewards, Reward_Multiplier FROM rp_guild_info")
        approved_channels = await cursor.fetchone()
        cache.cache[guild_id] = approved_channels
    return cache


async def reinstate_rp_cache(bot: commands.Bot) -> None:
    guilds = bot.guilds
    for guild in guilds:
        await add_guild_to_rp_cache(guild.id)


MAX_SIMILARITY_LENGTH = 1000  # Maximum characters to consider in similarity checks
MAX_COMPARISONS = 2  # Number of recent posts to compare against
SIMILARITY_TIMEOUT = 0.05  # Maximum time in seconds for similarity checks
DATABASE = 'your_database.db'  # Path to your SQLite database file




# Handler for RP messages
async def handle_rp_message(message):
    # Ignore messages wrapped in parentheses (OOC)
    content = message.content.strip()
    if content.startswith('(') and content.endswith(')'):
        return
    if message.guild.id in RoleplayInfoCache.cache:
        min_content_length, similarity_threshold, minimum_reward, maximum_reward, reward_multiplier = RoleplayInfoCache.cache[message.guild.id]
        min_content_length = min_content_length if min_content_length else 50
        similarity_threshold = similarity_threshold if similarity_threshold else 0.8
        minimum_reward = minimum_reward if minimum_reward else 1
        maximum_reward = maximum_reward if maximum_reward else 100
        reward_multiplier = reward_multiplier if reward_multiplier else 1
    else:
        min_content_length = 50
        similarity_threshold = 0.8
        minimum_reward = 1
        maximum_reward = 100
        reward_multiplier = 1

    user_id = message.author.id
    now = datetime.utcnow()

    async with aiosqlite.connect(DATABASE) as db:
        # Fetch user data
        cursor = await db.execute("SELECT balance, last_post_time, recent_posts FROM users WHERE user_id = ?", (user_id,))
        user_data = await cursor.fetchone()

        if user_data:
            balance, last_post_time_str, recent_posts_str = user_data
            if last_post_time_str:
                last_post_time = datetime.fromisoformat(last_post_time_str)
            else:
                last_post_time = None
            recent_posts = json.loads(recent_posts_str)
        else:
            # Create a new user record
            balance = 0
            last_post_time = None
            recent_posts = []
            await db.execute("INSERT INTO users (user_id, balance, last_post_time, recent_posts) VALUES (?, ?, ?, ?)",
                             (user_id, balance, None, json.dumps(recent_posts)))
            await db.commit()

        # Content Quality Check
        if len(content) < min_content_length:
            await message.channel.send(
                f"{message.author.mention}, your post is too short to earn rewards."
            )
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

            if similarity_ratio > similarity_threshold:
                is_similar = True
                break

        if is_similar:
            await message.channel.send(
                f"{message.author.mention}, your post is too similar to your recent posts and won't earn rewards."
            )
            return

        # Time since last post
        if last_post_time:
            time_since_last_post = (now - last_post_time).total_seconds()
        else:
            time_since_last_post = None  # First recorded post

        # Update user's last post time
        last_post_time_str = now.isoformat()

        # Append current post to recent posts
        recent_posts.append(content)
        # Keep only the last 5 posts
        recent_posts = recent_posts[-5:]
        recent_posts_str = json.dumps(recent_posts)

        # Calculate Reward
        content_length = len(content)
        reward = calculate_reward(content_length, time_since_last_post, reward_multiplier, minimum_reward, maximum_reward)

        # Update user's balance and other data in the database
        balance += reward
        await db.execute(
            "UPDATE users SET balance = ?, last_post_time = ?, recent_posts = ? WHERE user_id = ?",
            (balance, last_post_time_str, recent_posts_str, user_id)
        )
        await db.commit()

    # Provide feedback to the user
    await message.channel.send(
        f"{message.author.mention}, you have earned {reward} coins! Your new balance is {balance} coins."
    )

def truncate_text(text):
    """Truncate text to the maximum similarity length."""
    return text[:MAX_SIMILARITY_LENGTH]

def calculate_reward(content_length, time_since_last_post, multiplier, minumum_reward, maximum_reward):
    """
    Calculate the reward based on content length and time since last post.
    Rewards increase with longer intervals between posts, up to a maximum cap.
    """
    # Base reward: 1 coin per 10 characters
    base_reward = content_length // 10 * multiplier

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
    total_reward = max(minumum_reward, min(total_reward, maximum_reward))

    return total_reward










class RPCommands(commands.Cog, name='RP'):
    def __init__(self, bot):
        self.bot = bot
