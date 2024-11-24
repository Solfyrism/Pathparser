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
    reward_name: str = "coins"
    reward_emoji: str = "<:RPCash:884166313260503060>"


@dataclass
class RoleplayInfoCache:
    cache: Dict[int, RoleplaySettings] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


roleplay_info_cache = RoleplayInfoCache()


async def use_item(interaction: discord.Interaction, item_name: str):
    guild_id = interaction.guild.id
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            cursor = await db.execute(
                "SELECT actions_1_type, actions_1_subtype, actions_1_behavior, actions_2_type, actions_2_subtype, actions_2_behavior, actions_3_type, actions_3_subtype, actions_3_behavior FROM RP_Store_Items WHERE name = ?",
                (item_name,))
            item_info = await cursor.fetchone()
            if item_info:
                actions_1_type, actions_1_subtype, actions_1_behavior, actions_2_type, actions_2_subtype, actions_2_behavior, actions_3_type, actions_3_subtype, actions_3_behavior = item_info
                if actions_1_type and actions_1_subtype and actions_1_behavior:
                    actions_1 = await handle_action(interaction, actions_1_type, actions_1_subtype, actions_1_behavior)
                else:
                    actions_1 = 0
                if actions_2_type and actions_2_subtype and actions_2_behavior:
                    actions_2 = await handle_action(interaction, actions_2_type, actions_2_subtype, actions_2_behavior)
                else:
                    actions_2 = 0
                if actions_3_type and actions_3_subtype and actions_3_behavior:
                    actions_3 = await handle_action(interaction, actions_3_type, actions_3_subtype, actions_3_behavior)
                else:
                    actions_3 = 0
                return actions_1, actions_2, actions_3
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"An error occurred while using item: {e}")
        return -1, -1, -1



async def handle_action(interaction: discord.Interaction, actions_type: str, actions_subtype: str, actions_behavior: str):
    try:
        if int(actions_type) == 1:
            role = interaction.guild.get_role(int(actions_behavior))
            if int(actions_subtype) == 1 and role not in interaction.user.roles:
                await interaction.user.add_roles(role)
            elif int(actions_subtype) == 2 and role in interaction.user.roles:
                await interaction.user.remove_roles(role)
            else:
                if int(actions_subtype) == 1:
                    raise "User already has role and does not need another..."
                else:
                    raise "User does not have role and does not need it removed."
        else:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild.id}_test.sqlite") as db:
                cursor = await db.cursor()
                if int(actions_type) == 2:
                    if int(actions_subtype) == 1:
                        await cursor.execute("UPDATE RP_Players SET balance = balance + ? WHERE user_id = ?",
                                             (actions_behavior, interaction.user.id))
                    else:
                        await cursor.execute("UPDATE RP_Players SET balance = balance - ? WHERE user_id = ?",
                                             (actions_behavior, interaction.user.id))
                    await db.commit()
                else:
                    await cursor.execute(
                        "Select Item_Quantity from RP_PLayers_Items WHERE player_id = ? and item_name = ?",
                        (interaction.user.id, actions_behavior))
                    item_quantity_info = await cursor.fetchone()
                    item_quantity = int(item_quantity_info[0]) if item_quantity_info else None
                    if int(actions_subtype) == 1:
                        if item_quantity is None:
                            await cursor.execute(
                                "INSERT INTO RP_Players_Items (player_id, item_name, item_quantity) VALUES (?, ?, 1)",
                                (interaction.user.id, actions_behavior))
                        else:
                            await cursor.execute(
                                "UPDATE RP_Players_Items SET Item_Quantity = Item_Quantity + 1 WHERE user_id = ? and Item_Name = ?",
                                (interaction.user.id, actions_behavior))
                        await db.commit()
                    elif int(actions_subtype) == 2 and item_quantity:
                        if item_quantity == 1:
                            await cursor.execute("DELETE FROM RP_Players_Items WHERE user_id = ? and item_name = ?",
                                                 (interaction.user.id, actions_behavior))
                        else:
                            await cursor.execute(
                                "UPDATE RP_Players_Items SET item_quantity = item_quantity - ? WHERE user_id = ? AND Item_Name = ?",
                                (interaction.user.id, actions_behavior))
                        await db.commit()
        return 1
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"An error occurred while handling action: {e}")
        return -1


async def handle_requirements(requirements_type, requirements_pair, interaction, user_id, balance):
    try:
        async with aiosqlite.connect(f"Pathparser_{interaction.guild.id}_test.sqlite") as db:
            cursor = await db.cursor()

            if requirements_type == 1:
                role = interaction.guild.get_role(int(requirements_pair))
                user_roles = interaction.user.roles

                if not role in user_roles:
                    validation = False
                else:
                    validation = True
            elif requirements_type == 2:
                if balance > requirements_pair:
                    validation = True
                else:
                    validation = False
            else:
                await cursor.execute("SELECT Item_Quantity FROM RP_Players_Items WHERE player_id = ? and item_name = ?",
                                     (user_id, requirements_pair))
                item_quantity = await cursor.fetchone()
                if item_quantity is None:
                    validation = False
                else:
                    validation = True
        return validation
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"An error occurred while handling requirements: {e}")
        return False


async def add_guild_to_rp_cache(guild_id: int) -> None:
    try:
        async with roleplay_info_cache.lock:
            async with aiosqlite.connect(f"pathparser_{guild_id}_test.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("""
                    SELECT Minimum_Post_Length_In_Characters, Similarity_Threshold,
                           Minimum_Reward, Maximum_Reward, Reward_Multiplier,
                           reward_name, reward_emoji
                    FROM rp_guild_info
                """)
                settings_row = await cursor.fetchone()
                if settings_row:
                    settings = RoleplaySettings(
                        min_post_length=settings_row[0],
                        similarity_threshold=settings_row[1],
                        min_rewards=settings_row[2],
                        max_rewards=settings_row[3],
                        reward_multiplier=settings_row[4],
                        reward_name=settings_row[5],
                        reward_emoji=settings_row[6]
                    )
                    roleplay_info_cache.cache[guild_id] = settings
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Failed to add guild {guild_id} to cache with error: {e}")

async def reinstate_rp_cache(bot: commands.Bot) -> None:
    guilds = bot.guilds
    for guild in guilds:
        await add_guild_to_rp_cache(guild.id)



MAX_SIMILARITY_LENGTH = 1000  # Maximum characters to consider in similarity checks
MAX_COMPARISONS = 2  # Number of recent posts to compare against
SIMILARITY_TIMEOUT = 0.05  # Maximum time in seconds for similarity checks


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
    async with aiosqlite.connect(f"Pathparser_{message.guild.id}_test.sqlite") as db:
        # Fetch user data
        cursor = await db.execute("SELECT balance, last_post_time, recent_posts FROM RP_Players WHERE user_id = ?",
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
            await db.execute("INSERT INTO RP_Players (user_id, balance, last_post_time, recent_posts) VALUES (?, ?, ?, ?)",
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
            "UPDATE RP_Players SET balance = ?, last_post_time = ?, recent_posts = ? WHERE user_id = ?",
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
        async with aiosqlite.connect(f"Pathparser_{interaction.guild.id}_test.sqlite") as db:
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
        if amount < 1:
            await interaction.response.send_message("You can't buy less than 1 item.")
            return
        async with aiosqlite.connect(f"Pathparser_{interaction.guild.id}_test.sqlite") as db:
            cursor = await db.execute("SELECT balance FROM RP_Players WHERE user_id = ?", (user_id,))
            user_data = await cursor.fetchone()
            if user_data:
                old_balance = user_data[0]
                await cursor.execute(""" SELECT
                price, description, stock_remaining, inventory, usable, sellable, custom_message,
                matching_requirements, requirements_1_type, requirements_1_pair, requirements_2_type, requirements_2_pair, requirements_3_type, requirements_3_pair,
                actions_1_type, actions_1_subtype, actions_1_behavior, actions_2_type, actions_2_subtype, actions_2_behavior, actions_3_type, actions_3_subtype, actions_3_behavior
                From RP_Store_Items WHERE name = ?""", (item_name,))
                item_data = await cursor.fetchone()
                if item_data:
                    item_cost, item_description, stock_remaining, inventory, usable, sellable, custom_message, matching_requirements, requirements_1_type, requirements_1_pair, requirements_2_type, requirements_2_pair, requirements_3_type, requirements_3_pair, actions_1_type, actions_1_subtype, actions_1_behavior, actions_2_type, actions_2_subtype, actions_2_behavior, actions_3_type, actions_3_subtype, actions_3_behavior = item_data
                    purchase_response = f"You have bought {amount} {item_name}."
                    if stock_remaining is not None:
                        if not stock_remaining:
                            await interaction.followup.send("This item is out of stock.")
                            return
                        elif 0 <= stock_remaining < amount:
                            amount = stock_remaining
                    total_cost = item_cost * amount
                    if total_cost > old_balance:
                        await interaction.followup.send(f"You don't have enough coins to buy this item. You have {balance} coins and buying {amount} would take {total_cost}.")
                        return
                    if total_cost <= old_balance:
                        balance = old_balance - int(item_cost) * amount
                        if requirements_1_pair and requirements_1_type:
                            requirements_1_type = int(requirements_1_type)
                            requirements_1_pair = int(requirements_1_pair)

                            requirements_1_valid = await handle_requirements(requirements_1_type, requirements_1_pair,
                                                                             interaction, user_id, old_balance)
                        else:
                            requirements_1_valid = True
                        if requirements_2_pair and requirements_2_type:
                            requirements_2_type = int(requirements_2_type)
                            requirements_2_pair = int(requirements_2_pair)
                            requirements_2_valid = await handle_requirements(requirements_2_type, requirements_2_pair,
                                                                             interaction, user_id, old_balance)
                        else:
                            requirements_2_valid = True
                        if requirements_3_pair and requirements_3_type:
                            requirements_3_type = int(requirements_3_type)
                            requirements_3_pair = int(requirements_3_pair)
                            requirements_3_valid = await handle_requirements(requirements_3_type, requirements_3_pair,
                                                                             interaction, user_id, old_balance)
                        else:
                            requirements_3_valid = True

                        if matching_requirements:
                            matching_requirements = int(matching_requirements)
                            if matching_requirements == 1 and not any((requirements_1_valid, requirements_2_valid, requirements_3_valid)):
                                type_dict = {1: "Role", 2: "Balance", 3: "Item"}
                                content = f"Requirements not met: "
                                content += f"{type_dict[requirements_1_type]}: {requirements_1_pair}, " if requirements_1_valid is False else ""
                                content += f"{type_dict[requirements_2_type]}: {requirements_2_pair}, " if requirements_2_valid is False else ""
                                content += f"{type_dict[requirements_3_type]}: {requirements_3_pair}" if requirements_3_valid is False else ""
                                await interaction.followup.send(content)
                                return
                            elif matching_requirements == 2 and not all((requirements_1_valid, requirements_2_valid, requirements_3_valid)):
                                type_dict = {1: "Role", 2: "Balance", 3: "Item"}
                                content = f"Requirements not met: "
                                content += f"{type_dict[requirements_1_type]}: {requirements_1_pair}, " if not requirements_1_valid else ""
                                content += f"{type_dict[requirements_2_type]}: {requirements_2_pair}, " if not requirements_2_valid else ""
                                content += f"{type_dict[requirements_3_type]}: {requirements_3_pair}" if not requirements_3_valid else ""
                                await interaction.followup.send(content)
                                return
                            elif matching_requirements == 3 and any((requirements_1_valid, requirements_2_valid, requirements_3_valid)):
                                type_dict = {1: "Role", 2: "Balance", 3: "Item"}
                                content = f"the following requirements should NOT be met: "
                                content += f"{type_dict[requirements_1_type]}: {requirements_1_pair}, " if not requirements_1_valid else ""
                                content += f"{type_dict[requirements_2_type]}: {requirements_2_pair}, " if not requirements_2_valid else ""
                                content += f"{type_dict[requirements_3_type]}: {requirements_3_pair}" if not requirements_3_valid else ""
                                await interaction.followup.send(content)
                                return
                            else:
                                validation = True
                        else:
                            validation = True
                        if validation:
                            new_balance = balance - total_cost
                            await cursor.execute("UPDATE RP_Players SET balance = ? WHERE user_id = ?",
                                                 (new_balance, user_id))
                            await db.commit()
                            if stock_remaining is not None:
                                stock_remaining = stock_remaining - amount if stock_remaining > 0 else -1

                                await cursor.execute(
                                    "UPDATE RP_Store_Items SET stock_remaining = ? WHERE name = ?",
                                    (stock_remaining, item_name))
                                await db.commit()
                            if inventory == '0':
                                for _ in range(amount):
                                    try:
                                        actions_1, actions_2, actions_3 = await use_item(interaction=interaction, item_name=item_name,)
                                    except discord.errors.Forbidden:
                                        await interaction.followup.send("An error occurred while using the item! Bot does not have permissions to adjust that role!")
                                        return
                                    except Exception as e:
                                        await interaction.followup.send(
                                            "An error occurred while using the item.")
                                        logging.exception(f"An error occurred while using the item: {e}")
                                        return
                                    else:
                                        purchase_response += "\r\n" + custom_message
                            else:
                                await cursor.execute(
                                    "SELECT Item_Quantity FROM RP_Players_Items WHERE player_id = ? and item_name = ?",
                                    (user_id, item_name))
                                item_quantity = await cursor.fetchone()
                                if item_quantity is None:
                                    await cursor.execute(
                                        "INSERT INTO RP_Players_Items (player_id, item_name, item_quantity) VALUES (?, ?, ?)",
                                        (user_id, item_name, amount))
                                else:
                                    await cursor.execute(
                                        "UPDATE RP_Players_Items SET Item_Quantity = Item_Quantity + ? WHERE Player_ID = ? and item_name = ?",
                                        (amount, user_id, item_name))
                            await db.commit()
                            await interaction.followup.send(purchase_response)
                    else:
                        await interaction.followup.send("You don't have enough coins to buy this item.")
            else:
                await interaction.followup.send("You don't have a balance yet.")

    @roleplay_group.command(name="sell", description="sell an item from your inventory")
    @app_commands.autocomplete(item_name=shared_functions.rp_inventory_autocomplete)
    async def roleplay_sell(self, interaction: discord.Interaction, item_name: str, amount: int = 1):
        await interaction.response.defer(thinking=True)
        try:
            if amount < 1:
                await interaction.followup.send("You can't sell less than 1 item, did you mean to buy something instead?")
                return
            user_id = interaction.user.id
            async with aiosqlite.connect(f"Pathparser_{interaction.guild.id}_test.sqlite") as db:
                cursor = await db.execute("SELECT Item_Quantity FROM RP_Players_Items WHERE Player_ID = ?", (user_id,))
                user_item_data = await cursor.fetchone()
                cursor = await db.execute("SELECT balance FROM RP_Players WHERE user_id = ?", (user_id,))
                user_data = await cursor.fetchone()
                if user_data and user_item_data:
                    item_quantity = user_item_data[0]
                    balance = user_data[0]
                    await cursor.execute("SELECT Price, Sellable FROM RP_Store_Items WHERE item_name = ?", (item_name,))
                    sellable_data = await cursor.fetchone()
                    if sellable_data:
                        (item_value, sellable) = sellable_data
                        sold_value = min(item_quantity, amount) * item_value
                        balance += sold_value
                        await db.execute("UPDATE RP_Players SET balance = ? WHERE user_id = ?", (balance, user_id))
                        await db.commit()
                        if item_quantity - amount > 0:
                            await db.execute(
                                "UPDATE RP_Players_Items SET Item_Quantity = Item_Quantity - ? WHERE player_id = ? and item_name = ?",
                                (amount, user_id, item_name))
                            await db.commit()
                        else:
                            await db.execute("DELETE FROM RP_Players_Items WHERE player_id = ? and item_name = ?",
                                             (user_id, item_name))
                            await db.commit()
                        await interaction.followup.send(f"You have sold {item_name} for {item_value} coins and have a new balance of {balance}.")
                    else:
                        await interaction.followup.send(f"{item_name} could not be found!")
                else:
                    await interaction.followup.send("You don't have a balance yet or item could not be found!")
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"An error occurred while selling an item: {e}")
            await interaction.followup.send("An error occurred while selling an item.")

    @roleplay_group.command(name="use", description="use an item from your inventory")
    @app_commands.autocomplete(item_name=rp_inventory_autocomplete)
    async def roleplay_use(self, interaction: discord.Interaction, item_name: str, amount: int = 1):
        await interaction.response.defer(thinking=True)
        user_id = interaction.user.id
        async with aiosqlite.connect(f"Pathparser_{interaction.guild.id}_test.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Item_Quantity, Custom_Message FROM RP_Players_Items WHERE Player_ID = ? and Item_Name = ?", (user_id,item_name))
            item_quantity = await cursor.fetchone()
            if not item_quantity:
                await interaction.response.send_message(f"You don't have any {item_name} in your inventory.")
            else:
                response = f"You have used {amount}: {item_name}."
                for _ in range(amount):
                    actions_1, actions_2, actions_3 = await use_item(interaction=interaction, item_name=item_name)
                    response += "\r\n" + item_quantity[1] if item_quantity[1] else ""
                    if actions_1 == -1 or actions_2 == -1 or actions_3 == -1:
                        await interaction.followup.send("An error occurred while using the item.")
                        return
                await interaction.followup.send(response)

    @roleplay_group.command(name="send", description="send RP to another user")
    async def roleplay_send(self, interaction: discord.Interaction, amount: int, recipient: discord.User):
        await interaction.response.defer(thinking=True)
        try:
            sender_id = interaction.user.id
            recipient_id = recipient.id
            async with aiosqlite.connect(f"Pathparser_{interaction.guild.id}_test.sqlite") as db:
                cursor = await db.execute("SELECT balance FROM RP_Players WHERE user_id = ?", (sender_id,))
                sender_data = await cursor.fetchone()
                if sender_data:
                    sender_balance = sender_data[0]
                    if sender_balance >= amount:
                        cursor = await db.execute("SELECT balance FROM RP_Players WHERE user_id = ?", (recipient_id,))
                        recipient_data = await cursor.fetchone()
                        if recipient_data:
                            recipient_balance = recipient_data[0]
                            sender_balance -= amount
                            recipient_balance += amount
                            await db.execute("UPDATE RP_Players SET balance = ? WHERE user_id = ?", (sender_balance, sender_id))
                            await db.execute("UPDATE RP_Players SET balance = ? WHERE user_id = ?",
                                             (recipient_balance, recipient_id))
                            await db.commit()
                            await interaction.followup.send(f"You have sent {amount} coins to {recipient.mention}.")
                        else:
                            await db.execute("INSERT INTO RP_Players (user_id, balance) VALUES (?, ?)", (recipient_id, amount))
                            await db.commit()
                            await db.execute("UPDATE RP_Players SET balance = ? WHERE user_id = ?", (sender_balance - amount, sender_id))
                            await db.commit()
                            await interaction.followup.send(f"You have sent {amount} coins to {recipient.mention}.")
                    else:
                        await interaction.followup.send("You don't have enough coins to send.")
                else:
                    await interaction.followup.send("You don't have a balance yet.")
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"An error occurred while sending coins: {e}")
            await interaction.followup.send("An error occurred while sending coins.")


logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='application.log',  # Log to a file
    filemode='a'  # Append to the file
)
