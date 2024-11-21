import logging
from dataclasses import dataclass, field
from typing import Dict

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
import aiosqlite
import asyncio
import json
import difflib
from datetime import datetime

from unidecode import unidecode

import shared_functions


@dataclass
class RoleplaySettings:
    min_post_length: int
    similarity_threshold: float
    min_rewards: int
    max_rewards: int
    reward_multiplier: float


@dataclass
class RoleplayInfoCache:
    cache: Dict[int, RoleplaySettings] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


roleplay_info_cache = RoleplayInfoCache()



async def use_item(interaction: discord.Interaction, character_name: str, item_name: str):
    guild_id = interaction.guild.id
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            cursor = await db.execute("SELECT Action_1_type, Action_1_subtype, action_1_behavior, action_2_type, action_2_subtype, action_2_behavior, action_3_type, action_3_subtype, action_3_behavior FROM RP_Store_Items WHERE item_name = ?",
                                      (item_name,))
            item_info = await cursor.fetchone()
            if item_info:
                action_1_type, action_1_subtype, action_1_behavior, action_2_type, action_2_subtype, action_2_behavior, action_3_type, action_3_subtype, action_3_behavior = item_info
                if action_1_type and action_1_subtype and action_1_behavior:
                    action_1 = await handle_action(interaction, action_1_type, action_1_subtype, action_1_behavior, character_name)
                else:
                    action_1 = 0
                if action_2_type and action_2_subtype and action_2_behavior:
                    action_2 = await handle_action(interaction, action_2_type, action_2_subtype, action_2_behavior, character_name)
                else:
                    action_2 = 0
                if action_3_type and action_3_subtype and action_3_behavior:
                    action_3 = await handle_action(interaction, action_3_type, action_3_subtype, action_3_behavior, character_name)
                else:
                    action_3 = 0
                return action_1, action_2, action_3
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"An error occurred while using item: {e}")
        return -1, -1, -1




async def handle_action(interaction: discord.Interaction, action_type: str, action_subtype: str, action_behavior: str):
    try:
        if action_type == 1:
            role = interaction.guild.get_role(int(action_behavior))
            if action_subtype == 1:
                await interaction.user.add_roles(role)
            elif action_subtype == 2:
                await interaction.user.remove_roles(role)
        else:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild.id}_test.sqlite") as db:
                cursor = await db.cursor()
                if action_type == 2:
                    if action_subtype == 1:
                        await cursor.execute("UPDATE RP_Players SET balance = balance + ? WHERE user_id = ?", (action_behavior, interaction.user.id))
                    else:
                        await cursor.execute("UPDATE RP_Players SET balance = balance - ? WHERE user_id = ?", (action_behavior, interaction.user.id))
                    await db.commit()
                else:
                    await cursor.execute("Select Item_Quantity from RP_PLayers_Items WHERE player_id = ? and item_name = ?", (interaction.user.id, action_behavior))
                    item_quantity = await cursor.fetchone()
                    if action_subtype == 1:
                        if item_quantity is None:
                            await cursor.execute("INSERT INTO RP_Players_Items (player_id, item_name, item_quantity) VALUES (?, ?, 1)", (interaction.user.id, action_behavior))
                        else:
                            await cursor.execute("UPDATE RP_Players_Items SET Item_Quantity = Item_Quantity + 1 WHERE user_id = ? and Item_Name = ?", (interaction.user.id, action_behavior))
                        await db.commit()
                    elif action_subtype == 2 and item_quantity:
                        if item_quantity == 1:
                            await cursor.execute("DELETE FROM RP_Players_Items WHERE user_id = ? and item_name = ?", (interaction.user.id, action_behavior))
                        else:
                            await cursor.execute("UPDATE RP_Players_Items SET item_quantity = item_quantity - ? WHERE user_id = ? AND Item_Name = ?", (interaction.user.id, action_behavior))
                        await db.commit()
        return 1
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"An error occurred while handling action: {e}")
        return -1




async def add_guild_to_rp_cache(guild_id: int) -> None:
    async with roleplay_info_cache.lock:
        async with aiosqlite.connect(f"pathparser_{guild_id}_test.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("""
                SELECT Minimum_Post_Length_In_Characters, Similarity_Threshold,
                       Minimum_Rewards, Maximum_Rewards, Reward_Multiplier
                FROM rp_guild_info
            """)
            settings_row = await cursor.fetchone()
            if settings_row:
                settings = RoleplaySettings(
                    min_post_length=settings_row[0],
                    similarity_threshold=settings_row[1],
                    min_rewards=settings_row[2],
                    max_rewards=settings_row[3],
                    reward_multiplier=settings_row[4]
                )
                roleplay_info_cache.cache[guild_id] = settings


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
    guild_id = message.guild.id
    content = message.content.strip()
    if content.startswith('(') and content.endswith(')'):
        return

    # Ensure the guild's settings are in the cache
    async with roleplay_info_cache.lock:
        if guild_id not in roleplay_info_cache.cache:
            await add_guild_to_rp_cache(guild_id)
        settings = roleplay_info_cache.cache[guild_id]
        min_content_length = settings.min_post_length if settings.min_post_length else 50
        similarity_threshold = settings.similarity_threshold if settings.similarity_threshold else 0.8
        minimum_reward = settings.min_rewards if settings.min_rewards else 1
        maximum_reward = settings.max_rewards if settings.max_rewards else 100
        reward_multiplier = settings.reward_multiplier if settings.reward_multiplier else 1

    user_id = message.author.id
    now = datetime.utcnow()

    async with aiosqlite.connect(DATABASE) as db:
        # Fetch user data
        cursor = await db.execute("SELECT balance, last_post_time, recent_posts FROM users WHERE user_id = ?",
                                  (user_id,))
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
        reward = calculate_reward(content_length, time_since_last_post, reward_multiplier, minimum_reward,
                                  maximum_reward)

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


async def rp_inventory_autocomplete(
        interaction: discord.Interaction,
        current: str) -> list[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild.id
    current = unidecode(current.lower())
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            # Correct parameterized query
            cursor = await db.execute(
                "SELECT Item_Name FROM rp_players_items WHERE player_id = ? and item_name LIKE ? LIMIT 20",
                (interaction.user.id, f"%{current}%",))
            items_list = await cursor.fetchall()

            # Populate choices
            for item in items_list:
                if current in item[0].lower():
                    data.append(app_commands.Choice(name=item[0], value=item[0]))

    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"An error occurred while fetching settings: {e}")
    return data


class RPCommands(commands.Cog, name='RP'):
    def __init__(self, bot):
        self.bot = bot

    roleplay_group = discord.app_commands.Group(
        name='roleplay',
        description='roleplay Roots commands.'
    )

    @roleplay_group.command(name="help", description="Get help with roleplay commands.")
    async def roleplay_help(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        embed = discord.Embed(
            title="Roleplay Commands",
            description="Here are the available roleplay commands:",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

    @roleplay_group.command(name="shop", description="View the roleplay shop")
    async def roleplay_shop(self, interaction: discord.Interaction, page_number: int = 1):
        await interaction.response.defer(thinking=True)

        embed = discord.Embed(
            title="Roleplay Shop",
            description="Here are the items available in the roleplay shop:",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

    @roleplay_group.command(name="balance", description="Check your roleplay balance")
    async def roleplay_balance(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        user_id = interaction.user.id
        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.execute("SELECT balance FROM RP_Players WHERE user_id = ?", (user_id,))
            user_data = await cursor.fetchone()
            if user_data:
                balance = user_data[0]
                await interaction.response.send_message(f"Your balance is {balance} :<:RPCash:884166313260503060>.")
            else:
                await interaction.response.send_message("You don't have a balance yet.")

    @roleplay_group.command(name="buy", description="buy an item from the store")
    @app_commands.autocomplete(item_name=shared_functions.rp_store_autocomplete)
    async def roleplay_buy(self, interaction: discord.Interaction, item_name: str, amount: int = 1):
        await interaction.response.defer(thinking=True)

        user_id = interaction.user.id
        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            user_data = await cursor.fetchone()
            if user_data:
                balance = user_data[0]

                if balance >= item_cost:
                    balance -= item_cost
                    await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (balance, user_id))
                    await db.commit()
                    await interaction.response.send_message(f"You have purchased {item_name} for {item_cost} coins.")
                else:
                    await interaction.response.send_message("You don't have enough coins to purchase this item.")
            else:
                await interaction.response.send_message("You don't have a balance yet.")

    @roleplay_group.command(name="sell", description="sell an item from your inventory")
    @app_commands.autocomplete(item_name=shared_functions.rp_inventory_autocomplete)
    async def roleplay_sell(self, interaction: discord.Interaction, item_name: str, amount: int = 1):
        await interaction.response.defer(thinking=True)

        user_id = interaction.user.id
        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            user_data = await cursor.fetchone()
            if user_data:
                balance = user_data[0]
                item_value = shared_functions.get_item_value(item_name)
                balance += item_value
                await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (balance, user_id))
                await db.commit()
                await interaction.response.send_message(f"You have sold {item_name} for {item_value} coins.")
            else:
                await interaction.response.send_message("You don't have a balance yet.")

    @roleplay_group.command(name="use", description="use an item from your inventory")
    @app_commands.autocomplete(item_name=rp_inventory_autocomplete)
    async def roleplay_use(self, interaction: discord.Interaction, item_name: str):
        await interaction.response.defer(thinking=True)

        user_id = interaction.user.id
        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            user_data = await cursor.fetchone()
            if user_data:
                balance = user_data[0]
                item_effect = shared_functions.get_item_effect(item_name)
                if item_effect:
                    # Apply the item effect
                    await interaction.response.send_message(f"You have used {item_name}. {item_effect}")
                else:
                    await interaction.response.send_message(f"{item_name} does not have a use effect.")
            else:
                await interaction.response.send_message("You don't have a balance yet.")

    @roleplay_group.command(name="send", description="send RP to another user")
    async def roleplay_send(self, interaction: discord.Interaction, amount: int, recipient: discord.User):
        await interaction.response.defer(thinking=True)

        sender_id = interaction.user.id
        recipient_id = recipient.id

        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (sender_id,))
            sender_data = await cursor.fetchone()
            if sender_data:
                sender_balance = sender_data[0]
                if sender_balance >= amount:
                    cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (recipient_id,))
                    recipient_data = await cursor.fetchone()
                    if recipient_data:
                        recipient_balance = recipient_data[0]
                        sender_balance -= amount
                        recipient_balance += amount
                        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (sender_balance, sender_id))
                        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?",
                                         (recipient_balance, recipient_id))
                        await db.commit()
                        await interaction.response.send_message(f"You have sent {amount} coins to {recipient.mention}.")
                    else:
                        await interaction.response.send_message("The recipient does not have a balance yet.")
                else:
                    await interaction.response.send_message("You don't have enough coins to send.")
            else:
                await interaction.response.send_message("You don't have a balance yet.")
