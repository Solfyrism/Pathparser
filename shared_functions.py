import asyncio
import logging
import os
import re
import sqlite3
import typing
import urllib.error
from dataclasses import dataclass, field

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple, Union, Dict
from urllib.parse import urlparse, parse_qs
from zoneinfo import available_timezones, ZoneInfo
import aiosqlite
import discord
import matplotlib.pyplot as plt
import numpy as np
import pytz
from dateutil import parser
from discord import app_commands
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pywaclient.api import BoromirApiClient as WaClient
from unidecode import unidecode

load_dotenv()
# CALL ME MR MONEYBAGS BECAUSE HERE IS MY CASH
timezone_cache = sorted(available_timezones())


# *** AUTOCOMPLETION COMMANDS *** #


async def stg_character_select_autocompletion(
        interaction: discord.Interaction,
        current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}_test.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(
        "SELECT True_Character_Name, Character_Name from A_STG_Player_Characters where Character_Name LIKE ? OR Nickname LIKE ? LIMIT 5",
        (f"%{current}%", f"%{current}%"))
    character_list = cursor.fetchall()
    for characters in character_list:
        if current in characters[1]:
            data.append(app_commands.Choice(name=characters[0], value=characters[0]))
    cursor.close()
    db.close()
    return data


async def clear_autocomplete_cache():
    while True:
        await asyncio.sleep(300)  # Wait for 5 minutes
        async with autocomplete_cache.lock:
            autocomplete_cache.cache.clear()


async def invalidate_user_cache(user_id: int):
    async with autocomplete_cache.lock:
        keys_to_delete = [key for key in autocomplete_cache.cache if key[0] == user_id]
        for key in keys_to_delete:
            del autocomplete_cache.cache[key]


@dataclass
class AutocompleteCache:
    cache: Dict[Tuple[int, str], List[Tuple[str, str]]] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


autocomplete_cache = AutocompleteCache()

MAX_CACHE_SIZE = 100


async def own_character_select_autocompletion(
        interaction: discord.Interaction, current: str
) -> List[app_commands.Choice[str]]:
    data = []
    user_id = interaction.user.id
    guild_id = interaction.guild_id
    _, current_fixed = name_fix(current)
    current_prefix = current_fixed.lower()
    cache_key = (user_id, current_prefix)

    async with autocomplete_cache.lock:
        cached_result = autocomplete_cache.cache.get(cache_key)

    async with autocomplete_cache.lock:
        if len(autocomplete_cache.cache) >= MAX_CACHE_SIZE:
            # Remove the oldest entry
            autocomplete_cache.cache.pop(next(iter(autocomplete_cache.cache)))
    if cached_result is not None:
        character_list = cached_result
    else:
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT True_Character_Name, Character_Name
                FROM Player_Characters
                WHERE Player_Name = ?
                AND (LOWER(Character_Name) LIKE ? OR LOWER(Nickname) LIKE ?)
                LIMIT 5
                """,
                (interaction.user.name, f"{current_prefix}%", f"{current_prefix}%")
            )
            character_list = await cursor.fetchall()
            # Cache the result
            async with autocomplete_cache.lock:
                autocomplete_cache.cache[cache_key] = character_list

    for character in character_list:
        if current_prefix in character[1].lower():
            data.append(app_commands.Choice(name=character[1], value=character[1]))
    return data


async def character_select_autocompletion(interaction: discord.Interaction, current: str
                                          ) -> List[app_commands.Choice[str]]:
    data = []
    user_id = interaction.user.id
    guild_id = interaction.guild_id
    _, current_fixed = name_fix(current)
    current_prefix = current_fixed.lower()
    cache_key = (user_id, current_prefix)

    async with autocomplete_cache.lock:
        cached_result = autocomplete_cache.cache.get(cache_key)

    if cached_result is not None:
        character_list = cached_result
    else:
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT True_Character_Name, Character_Name
                FROM Player_Characters
                WHERE LOWER(Character_Name) LIKE ? OR LOWER(Nickname) LIKE ?
                LIMIT 5
                """,
                (f"{current_prefix}%", f"{current_prefix}%")
            )
            character_list = await cursor.fetchall()
            # Cache the result
            async with autocomplete_cache.lock:
                autocomplete_cache.cache[cache_key] = character_list

    for character in character_list:
        if current_prefix in character[1].lower():
            data.append(app_commands.Choice(name=character[1], value=character[1]))
    return data


async def get_plots_autocompletion(
        interaction: discord.Interaction,
        current: str) -> typing.List[app_commands.Choice[str]]:
    """This is a test command for the wa command."""
    data = []
    client = WaClient(
        'Pathparser',
        'https://github.com/Solfyrism/Pathparser',
        'V1.1',
        os.getenv('WORLD_ANVIL_API'),
        os.getenv('WORLD_ANVIL_USER')
    )
    articles_list = [article for article in client.world.articles('f7a60480-ea15-4867-ae03-e9e0c676060a',
                                                                  '9ad3d530-1a42-4e99-9a09-9c4dccddc70a')]
    for articles in articles_list:
        if current in articles['title']:
            print(articles['title'])
            data.append(app_commands.Choice(name=articles['title'], value=f"1-{articles['id']}"))
    data.append(app_commands.Choice(name=f"NEW: {str.title(current)}", value=f"2-{str.title(current)}"))
    return data


async def get_precreated_plots_autocompletion(
        interaction: discord.Interaction,
        current: str) -> typing.List[app_commands.Choice[str]]:
    """This is a test command for the wa command."""
    data = []
    client = WaClient(
        'Pathparser',
        'https://github.com/Solfyrism/Pathparser',
        'V1.1',
        os.getenv('WORLD_ANVIL_API'),
        os.getenv('WORLD_ANVIL_USER')
    )
    articles_list = [article for article in client.world.articles('f7a60480-ea15-4867-ae03-e9e0c676060a',
                                                                  '9ad3d530-1a42-4e99-9a09-9c4dccddc70a')]
    for articles in articles_list:
        if str.lower(current) in str.lower(articles['title']):
            data.append(app_commands.Choice(name=articles['title'], value=f"{articles['id']}"))
    return data


async def session_autocompletion(
        interaction: discord.Interaction,
        current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}_test.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(
        "SELECT Session_ID, Session_Name FROM Sessions WHERE GM_Name = ? and Completed_Time is not Null AND (Session_ID LIKE ? OR Session_Name like ?) Limit 15",
        (interaction.user.name, f"%{current}%", f"%{current}%"))
    session_list = cursor.fetchall()
    for test_text in session_list:
        if current in str(test_text[0]) or str.lower(current) in str.lower(test_text[1]):
            name_result = f"{test_text[0]}: {test_text[1]}"
            data.append(app_commands.Choice(name=name_result, value=test_text[0]))
    cursor.close()
    db.close()
    return data


async def group_id_autocompletion(
        interaction: discord.Interaction,
        current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}_test.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute("SELECT Group_ID, Group_Name  FROM Sessions_Group WHERE Group_Name LIKE ? Limit 15",
                   (f"%{current}%",))
    session_list = cursor.fetchall()
    for test_text in session_list:
        if current in str(test_text[0]) or str.lower(current) in str.lower(test_text[1]):
            name_result = f"{test_text[0]}: {test_text[1]}"
            data.append(app_commands.Choice(name=name_result, value=test_text[0]))
    cursor.close()
    db.close()
    return data


async def get_plots_autocomplete(
        interaction: discord.Interaction,
        current: str) -> typing.List[app_commands.Choice[str]]:
    """This is a test command for the wa command."""
    data = []
    client = WaClient(
        'Pathparser',
        'https://github.com/Solfyrism/Pathparser',
        'V1.1',
        os.getenv('WORLD_ANVIL_API'),
        os.getenv('WORLD_ANVIL_USER')
    )
    articles_list = [article for article in client.world.articles('f7a60480-ea15-4867-ae03-e9e0c676060a',
                                                                  '9ad3d530-1a42-4e99-9a09-9c4dccddc70a')]
    for articles in articles_list:
        if current in articles['title']:
            print(articles['title'])
            data.append(app_commands.Choice(name=articles['title'], value=f"1-{articles['id']}"))
    data.append(app_commands.Choice(name=f"NEW: {str.title(current)}", value=f"2-{str.title(current)}"))
    return data


async def player_session_autocomplete(
        interaction: discord.Interaction,
        current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}_test.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(
        "SELECT Session_ID, Session_Name Sessions_Archive WHERE Player_Name = ? AND Session_ID LIKE ? OR Player_Name = ? AND Session_Name like ? Limit 20",
        (interaction.user.name, f"%{current}%", interaction.user.name, f"%{current}%"))
    character_list = cursor.fetchall()
    for test_text in character_list:
        if current in str(test_text[0]) or str.lower(current) in str.lower(test_text[1]):
            name_result = f"{test_text[0]}: {test_text[1]}"
            data.append(app_commands.Choice(name=name_result, value=test_text[0]))
    #        if current in characters[1]:
    #            data.append(app_commands.Choice(name=f"Name: {characters[3]} Requirement: {characters[0]}, Prestige Cost: {characters[1]} **Effect**: {characters[2]}, **Limit**: {characters[4]}", value=characters[3]))
    cursor.close()
    db.close()
    return data


async def fame_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}_test.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(
        "SELECT Fame_Required, Prestige_Cost, Effect, Name, Use_Limit from Store_Fame WHERE Effect LIKE ? Limit 20",
        (f"%{current}%",))
    character_list = cursor.fetchall()
    for characters in character_list:
        if current in characters[3]:
            data.append(app_commands.Choice(name=f"{characters[3]}", value=characters[3]))
    #        if current in characters[1]:
    #            data.append(app_commands.Choice(name=f"Name: {characters[3]} Requirement: {characters[0]}, Prestige Cost: {characters[1]} **Effect**: {characters[2]}, **Limit**: {characters[4]}", value=characters[3]))
    cursor.close()
    db.close()
    return data


async def title_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT ID, Masculine_Name, Feminine_Name, Fame, Effect from Store_Title WHERE Masculine_Name LIKE ? OR Feminine_Name LIKE ? LIMIT 20",
            (f"%{current}%", f"%{current}%"))
        character_list = await cursor.fetchall()
        for characters in character_list:
            if current in characters[1]:
                data.append(app_commands.Choice(name=f"{characters[1]}", value=characters[1]))
            if current in characters[2]:
                data.append(app_commands.Choice(name=f"{characters[2]}", value=characters[2]))
    return data


import aiosqlite
from discord import app_commands
from unidecode import unidecode
import logging


async def settings_autocomplete(
        interaction: discord.Interaction,
        current: str) -> list[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild.id
    current = unidecode(current.lower())
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            # Correct parameterized query
            cursor = await db.execute("SELECT Identifier FROM Admin WHERE Identifier LIKE ? LIMIT 20",
                                      (f"%{current}%",))
            settings_list = await cursor.fetchall()

            # Populate choices
            for setting in settings_list:
                if current in setting[0].lower():
                    data.append(app_commands.Choice(name=setting[0], value=setting[0]))

    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"An error occurred while fetching settings: {e}")
    return data


# *** DISPLAY FUNCTIONS *** #

async def character_embed(
        character_name: str,
        guild: discord.Guild) -> Union[Tuple[discord.Embed, str, int], str]:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild.id}_test.sqlite") as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.cursor()

            # Fetch channel ID
            await cursor.execute("SELECT Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            channel_id_row = await cursor.fetchone()
            if not channel_id_row:
                return f"No channel found with Identifier 'Accepted_Bio_Channel' in Admin table."
            channel_id = channel_id_row['Search']

            # Fetch character info
            await cursor.execute(
                """
                SELECT player_name, player_id, True_Character_Name, Title, Titles, Description, Oath, Level,
                       Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value,
                       Essence, Fame, Prestige, Color, Mythweavers, Image_Link, Tradition_Name,
                       Tradition_Link, Template_Name, Template_Link, Article_Link, Message_ID
                FROM Player_Characters WHERE Character_Name = ?
                """, (character_name,))
            character_info = await cursor.fetchone()
            if not character_info:
                return f"No character found with Character_Name '{character_name}'."

        # Unpack character_info using column names
        player_name = character_info['player_name']
        player_id = character_info['player_id']
        true_character_name = character_info['True_Character_Name']
        title = character_info['Title']
        titles = character_info['Titles']
        description = character_info['Description']
        oath = character_info['Oath']
        level = character_info['Level']
        tier = character_info['Tier']
        milestones = character_info['Milestones']
        milestones_required = character_info['Milestones_Required']
        trials = character_info['Trials']
        trials_required = character_info['Trials_Required']
        gold = character_info['Gold']
        gold_value = character_info['Gold_Value']
        essence = character_info['Essence']
        fame = character_info['Fame']
        prestige = character_info['Prestige']
        color = character_info['Color']
        mythweavers = character_info['Mythweavers']
        image_link = character_info['Image_Link']
        tradition_name = character_info['Tradition_Name']
        tradition_link = character_info['Tradition_Link']
        template_name = character_info['Template_Name']
        template_link = character_info['Template_Link']
        article_link = character_info['Article_Link']
        message_id = character_info['Message_ID']

        # Convert color to integer
        try:
            int_color = int(color.lstrip('#'), 16)
        except ValueError:
            int_color = 0x000000  # Default color if invalid

        # Build embed description
        description_field = ""
        if titles:
            description_field += f"**Other Names**: {titles}\n"
        if article_link:
            description_field += f"[**Backstory**]({article_link})"

        titled_character_name = true_character_name if not title else f"{title} {true_character_name}"

        embed = discord.Embed(
            title=titled_character_name,
            url=mythweavers,
            description=description_field,
            color=int_color
        )
        embed.set_author(name=player_name)
        embed.set_thumbnail(url=image_link)
        embed.add_field(
            name="Information",
            value=f'**Level**: {level}, **Mythic Tier**: {tier}\n**Fame**: {fame}, **Prestige**: {prestige}',
            inline=False
        )
        embed.add_field(
            name="Experience",
            value=f'**Milestones**: {milestones}, **Remaining**: {milestones_required}'
        )
        embed.add_field(
            name="Mythic",
            value=f'**Trials**: {trials}, **Remaining**: {trials_required}'
        )
        embed.add_field(
            name="Current Wealth",
            value=f'**GP**: {Decimal(gold)}, **Effective**: {Decimal(gold_value)} GP',
            inline=False
        )
        embed.add_field(
            name="Current Essence",
            value=f'**Essence**: {essence}'
        )

        # Additional Info
        linkage = ""
        if tradition_name:
            linkage += f"**Tradition**: [{tradition_name}]({tradition_link})"
        if template_name:
            if tradition_name:
                linkage += " "
            linkage += f"**Template**: [{template_name}]({template_link})"
        if linkage:
            embed.add_field(name='Additional Info', value=linkage, inline=False)

        # Footer with Oath
        oath_icons = {
            'Offerings': 'https://i.imgur.com/dSuLyJd.png',
            'Poverty': 'https://i.imgur.com/4Fr9ZnZ.png',
            'Absolute': 'https://i.imgur.com/ibE5vSY.png'
        }
        icon_url = oath_icons.get(oath)
        embed.set_footer(text=description, icon_url=icon_url)

        message_content = f"<@{player_id}>"

        # Fetch the bio channel
        bio_channel = guild.get_channel(channel_id)
        if bio_channel is None:
            bio_channel = await guild.fetch_channel(channel_id)
        if bio_channel is None:
            return f"Channel with ID {channel_id} not found."

        # Fetch and edit the message
        try:
            bio_message = await bio_channel.fetch_message(message_id)
            await bio_message.edit(content=message_content, embed=embed)
        except discord.NotFound:
            return f"Message with ID {message_id} not found in channel {bio_channel.name}."
        except discord.Forbidden:
            return "Bot lacks permissions to edit the message."
        except discord.HTTPException as e:
            logging.exception(f"Discord error while editing message: {e}")
            return "An error occurred while editing the message."

        return embed, message_content, channel_id

    except aiosqlite.Error as e:
        logging.exception(f"Database error: {e}")
        return f"An error occurred with the database."
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        return f"An unexpected error occurred while building character embed for '{character_name}'."


def name_fix(name) -> Optional[Tuple[str, str]]:
    return_value = [None, None]
    try:
        coded_name = str.replace(
            str.replace(
                str.replace(str.replace(str.replace(str.title(name), ";", ""), "(", ""), ")", ""),
                "[", ""), "]", "")
        unidecoded_name = unidecode(coded_name)
        return_value = coded_name, unidecoded_name
    except (TypeError, ValueError) as e:
        logging.exception(f"An error occurred whilst fixing character name '{name}': {e}")
    return return_value


@dataclass
class CharacterChange:
    character_name: str
    author: str
    titles: Optional[str] = None
    image: Optional[str] = None
    mythweavers: Optional[str] = None
    level: Optional[int] = None
    oath: Optional[str] = None
    backstory: Optional[str] = None
    description: Optional[str] = None
    milestone_change: Optional[int] = None
    milestones_total: Optional[int] = None
    milestones_remaining: Optional[int] = None
    tier: Optional[int] = None
    trial_change: Optional[int] = None
    trials: Optional[int] = None
    trials_remaining: Optional[int] = None
    gold: Optional[Decimal] = None
    gold_change: Optional[Decimal] = None
    gold_value: Optional[Decimal] = None
    gold_value_max: Optional[Decimal] = None
    transaction_id: Optional[int] = None
    essence: Optional[int] = None
    essence_change: Optional[int] = None
    tradition_name: Optional[str] = None
    tradition_link: Optional[str] = None
    template_name: Optional[str] = None
    template_link: Optional[str] = None
    alternate_reward: Optional[str] = None
    total_fame: Optional[int] = None
    fame: Optional[int] = None
    total_prestige: Optional[int] = None
    prestige: Optional[int] = None
    source: Optional[str] = None


@dataclass
class UpdateCharacterData:
    character_name: str
    level_package: Optional[Tuple[int, int, int]] = None  # (Level, Milestones, Milestones_Required)
    mythic_package: Optional[Tuple[int, int, int]] = None  # (Tier, Trials, Trials_Required)
    gold_package: Optional[Tuple[Decimal, Decimal, Decimal]] = None  # (Gold, Gold_Value, Gold_Value_Max)
    essence: Optional[int] = None
    fame_package: Optional[Tuple[int, int]] = None  # (Fame, Prestige)


async def update_character(guild_id: int, change: UpdateCharacterData) -> str:
    try:
        # Lists to collect column assignments and values
        assignments = []
        values = []

        # Handle level package
        if change.level_package:
            assignments.extend(["Level = ?", "Milestones = ?", "Milestones_Required = ?"])
            values.extend(change.level_package)

        # Handle mythic package
        if change.mythic_package:
            assignments.extend(["Tier = ?", "Trials = ?", "Trials_Required = ?"])
            values.extend(change.mythic_package)

        # Handle gold package
        if change.gold_package:
            # Ensure values are Decimal and formatted to two decimal places
            gold_values = [str(Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)) for value in
                           change.gold_package]
            assignments.extend(["Gold = ?", "Gold_Value = ?", "Gold_Value_Max = ?"])
            values.extend(gold_values)

        # Handle essence
        if change.essence is not None:
            assignments.append("Essence = ?")
            values.append(change.essence)

        # Handle fame package
        if change.fame_package:
            assignments.extend(["Fame = ?", "Prestige = ?"])
            values.extend(change.fame_package)

        # Check if there are any assignments to update
        if not assignments:
            return "No changes to update."

        # Construct the SQL statement
        sql_statement = f"UPDATE Player_Characters SET {', '.join(assignments)} WHERE Character_Name = ?"
        values.append(change.character_name)

        # Execute the SQL statement
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            cursor = await db.cursor()
            print(sql_statement, values)
            await cursor.execute(sql_statement, values)
            updated_rows = cursor.rowcount
            if updated_rows == 0:
                return f"No character found with name '{change.character_name}'."
            else:
                await db.commit()
                logging.info(f"Character '{change.character_name}' updated successfully.")
                return f"Character '{change.character_name}' updated successfully."

    except aiosqlite.Error as e:
        logging.exception(f"Database error while updating '{change.character_name}': {e}")
        return f"An error occurred with the database while updating '{change.character_name}'."
    except (TypeError, ValueError) as e:
        logging.exception(f"Invalid data provided for '{change.character_name}': {e}")
        return f"Invalid data provided for '{change.character_name}'. Please check the input values."
    except Exception as e:
        logging.exception(f"An unexpected error occurred while updating '{change.character_name}': {e}")
        return f"An unexpected error occurred while updating '{change.character_name}'."


# Function to create the embed
async def log_embed(change: CharacterChange, guild: discord.Guild, thread: int, bot) -> discord.Embed:
    try:
        embed = discord.Embed(
            title=change.character_name,
            description="Character Change",
            color=discord.Color.blurple()
        )
        embed.set_author(name=change.author)
        if change.titles is not None:
            embed.add_field(
                name="titles",
                value=f"new titles: {change.titles}"
            )

        if change.image is not None:
            embed.set_thumbnail(url=change.image)
        if change.mythweavers is not None:
            embed.add_field(
                name="Mythweavers",
                value=f"[Character Sheet]({change.mythweavers})"
            )

        if change.titles is not None:
            embed.add_field(
                name="titles",
                value=f"new titles: {change.titles}"
            )

        if change.oath is not None:
            embed.add_field(
                name="Oath",
                value=change.oath
            )

        if change.backstory is not None:
            embed.add_field(
                name="Backstory",
                value=change.backstory
            )

        if change.description is not None:
            embed.add_field(
                name="Description",
                value=change.description
            )
        # Milestone Change
        if change.milestone_change is not None:
            embed.add_field(
                name="Milestone Change",
                value=(
                    f"**Level**: {change.level}\n"
                    f"**Milestone Change**: {change.milestone_change}\n"
                    f"**Total Milestones**: {change.milestones_total}\n"
                    f"**Milestones Remaining**: {change.milestones_remaining}"
                )
            )

        # Trial Change
        if change.trial_change is not None:
            embed.add_field(
                name="Trial Change",
                value=(
                    f"**Mythic Tier**: {change.tier}\n"
                    f"**Trial Change**: {change.trial_change}\n"
                    f"**Total Trials**: {change.trials}\n"
                    f"**Trials Remaining**: {change.trials_remaining}"
                )
            )

        # Wealth Changes
        if change.gold_change is not None:
            gold = round(change.gold, 2) if change.gold is not None else "N/A"
            gold_change = round(change.gold_change, 2) if change.gold_change is not None else "N/A"
            gold_value = round(change.gold_value, 2) if change.gold_value is not None else "N/A"
            print(gold, gold_change, gold_value)
            embed.add_field(
                name="Wealth Changes",
                value=(
                    f"**Gold**: {gold}\n"
                    f"**Gold Change**: {gold_change}\n"
                    f"**Effective Gold**: {gold_value} GP\n"
                    f"**Transaction ID**: {change.transaction_id}"
                )
            )

        # Essence Change
        if change.essence_change is not None:
            embed.add_field(
                name="Essence Change",
                value=(
                    f"**Essence**: {change.essence}\n"
                    f"**Essence Change**: {change.essence_change}"
                )
            )

        # Tradition Change
        if change.tradition_name and change.tradition_link:
            embed.add_field(
                name="Tradition Change",
                value=f"**Tradition**: [{change.tradition_name}]({change.tradition_link})"
            )

        # Template Change
        if change.template_name and change.template_link:
            embed.add_field(
                name="Template Change",
                value=f"**Template**: [{change.template_name}]({change.template_link})"
            )

        # Alternate Reward
        if change.alternate_reward is not None:
            embed.add_field(
                name="Other Rewards",
                value=change.alternate_reward
            )

        # Fame and Prestige
        if change.fame is not None or change.prestige is not None:
            total_fame = change.total_fame if change.total_fame is not None else "Not Changed"
            total_prestige = change.total_prestige if change.total_prestige is not None else "Not Changed"
            fame = change.fame if change.fame is not None else "Not Changed"
            prestige = change.prestige if change.prestige is not None else "Not Changed"
            embed.add_field(
                name="Fame and Prestige",
                value=(
                    f"**Total Fame**: {total_fame}\n"
                    f"**Received Fame**: {fame}\n"
                    f"**Total Prestige**: {total_prestige}\n"
                    f"**Received Prestige**: {prestige}"
                )
            )

        # Set Footer
        if change.source is not None:
            embed.set_footer(text=change.source)
        logging_thread = guild.get_thread(thread)
        if logging_thread is None:
            logging_thread = await bot.fetch_channel(thread)
            if logging_thread.archived:
                try:
                    # Remove the thread from Archive
                    await logging_thread.edit(archived=False, locked=False)
                except discord.Forbidden:
                    logging.exception(f"Bot lacks permissions to update thread from archived {logging_thread.id}")
        await logging_thread.send(embed=embed)
        return embed
    except (TypeError, ValueError) as e:
        logging.exception(f"An error occurred whilst building character embed for '{change.character_name}': {e}")


# *** TIME MANAGEMENT FUNCTIONS *** #

def get_next_weekday(weekday):
    """Return the date of the next specified weekday (0=Monday, 6=Sunday)."""
    today = datetime.now().date()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def parse_time_input(time_str):
    """Parse time input in various formats and return a time object."""
    try:
        # Use dateutil.parser to parse the time string
        dt = parser.parse(time_str, fuzzy=True)
        return dt.time()
    except (parser.ParserError, ValueError):
        return None


async def search_timezones(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    # Get all available timezones
    global timezone_cache
    # Check if timezone cache is initialized
    # Filter timezones based on current input
    filtered_timezones = [tz for tz in timezone_cache if current.lower() in tz.lower()]
    print(filtered_timezones)
    # Return list of app_commands.Choice objects (maximum 25 choices for Discord autocomplete)
    return [
        app_commands.Choice(name=tz, value=tz)
        for tz in filtered_timezones[:25]  # Limit to 25 results to comply with Discord's limit
    ]


def get_utc_offset(tz):
    try:
        # Get the current time for the timezone
        tzinfo = ZoneInfo(tz)
        now_utc = datetime.now(timezone.utc)
        now_tz = now_utc.astimezone(tzinfo)
        print(tzinfo, now_utc, now_tz)
        # Get the offset in hours and minutes
        offset_seconds = now_tz.utcoffset().total_seconds()
        offset_hours = int(offset_seconds // 3600)
        offset_minutes = int((offset_seconds % 3600) // 60)
        print(offset_hours, offset_minutes)
        # Format the offset as "+HH:MM" or "-HH:MM"
        return f"{offset_hours:+03}:{offset_minutes:02}"
    except Exception as e:
        logging.exception(f"An error occurred whilst getting UTC offset for timezone '{tz}': {e}")
        return "+00:00"  # Return UTC if the timezone is invalid or there's an error


def time_to_minutes(t):
    pattern = r'^(?P<sign>[+-]?)(?P<hours>\d{1,2}):(?P<minutes>\d{2})$'
    match = re.match(pattern, t)
    if not match:
        logging.error(f"Invalid time format: {t}")
        return 0  # Or raise an exception

    sign = -1 if match.group('sign') == '-' else 1
    hours = int(match.group('hours'))
    minutes = int(match.group('minutes'))
    total_minutes = sign * (hours * 60 + minutes)
    return total_minutes


def fetch_timecard_data_from_db(guild_id, player_name, day, utc_offset):
    time_labels = [
        "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30",
        "05:00", "05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30",
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
        "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30",
        "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", "24:00", "24:30"
    ]
    conn = sqlite3.connect(f"Pathparser_{guild_id}_test.sqlite")
    cursor = conn.cursor()
    print(f" this is {utc_offset}")
    if utc_offset > 0:
        select_columns = []
        for col in time_labels:
            col_minutes = time_to_minutes(col)
            if 1440 + -abs(utc_offset) < col_minutes <= 1470:
                select_columns.append(f'pt1."{col}"')
        for col in time_labels:
            col_minutes = time_to_minutes(col)
            if col_minutes <= 1470 + -abs(utc_offset):
                select_columns.append(f'pt2."{col}"')
        select_clause = ', '.join(select_columns)
        day_two = adjust_day(day, 2, 4)
        cursor.execute(
            "SELECT {select_clause} FROM Player_Timecard PT1 Left Join Player_Timecard PT2 on PT1.Player_Name = PT2.Player_Name where PT1.Player_Name = ? and PT1.Day = ? AND PT2.Day = ?",
            (player_name, day_two, day))
        row = cursor.fetchone()
    elif utc_offset < 0:
        select_columns = []
        for col in time_labels:
            col_minutes = time_to_minutes(col)
            if abs(utc_offset) <= col_minutes <= 1470:
                select_columns.append(f'pt1."{col}"')
        for col in time_labels:
            col_minutes = time_to_minutes(col)
            if col_minutes < abs(utc_offset):
                select_columns.append(f'pt2."{col}"')
        select_clause = ', '.join(select_columns)
        day_two = adjust_day(day, 23, -4)
        print(f" DAY ONE IS {day} DAY TWO IS {day_two}")
        print(f"The select clause is {select_clause}", f"the day is day {day_two}")
        cursor.execute(
            "SELECT {select_clause} FROM Player_Timecard PT1 Left Join Player_Timecard PT2 on PT1.Player_Name = PT2.Player_Name where PT1.Player_Name = ? and PT1.Day = ? AND PT2.Day = ?",
            (player_name, day, day_two))
        row = cursor.fetchone()
    # Fetch time slots for the specific player and day
    else:
        cursor.execute("SELECT * FROM Player_Timecard WHERE Player_Name = ? AND Day = ?", (player_name, day))
        row = cursor.fetchone()
        row = row[3:] if row else None  # Skip the first 3 columns (Player_Name, UTC_Offset, Day)
    conn.close()
    return row


# Function to plot and save the graph as an image
async def create_timecard_plot(guild_id, player_name, day, utc_offset):
    # Time intervals (x-axis)
    time_labels = [
        "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30",
        "05:00", "05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30",
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
        "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30",
        "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", "24:00", "24:30"
    ]
    days_dict = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
    # Get timecard data for the player and day
    utc_offset_time = get_utc_offset(utc_offset)
    utc_offset_minutes = time_to_minutes(utc_offset_time)
    if isinstance(player_name, str):
        row = fetch_timecard_data_from_db(guild_id, player_name, day, utc_offset_minutes)

        if row:
            player_availability = row  # Skip the first 3 columns (Player_Name, UTC_Offset, Day)
        else:
            player_availability = [0] * len(time_labels)  # Default to 0 if no data found
        player_availability = [int(x) if str(x).isdigit() else 0 for x in player_availability]
        # Reshape the 1D array to a 2D array with 1 row and 48 columns
        player_availability = np.array(player_availability).reshape(1, -1)

        # Use the updated colormap call to avoid deprecation warning
        cmap = plt.colormaps.get_cmap('RdYlGn')

        # Create a plot with larger size to fit everything
        plt.figure(figsize=(14, 3))  # Widen the figure

        # Plot the data
        plt.imshow(player_availability, cmap=cmap, aspect='auto')

        midpoints = np.arange(len(time_labels)) - 0.5  # Shift ticks by -0.5 to place grid between labels
        # Rotate the x-axis labels and align them properly
        plt.xticks(np.arange(len(time_labels)), time_labels, rotation=90, ha="center",
                   fontsize=8)  # Adjust rotation and font size

        plt.yticks(np.arange(1), [player_name])

        plt.gca().set_xticks(midpoints, minor=True)  # Set the grid to the midpoints between ticks
        plt.gca().grid(which='minor', color='white', linestyle='-', linewidth=2)  # Minor grid between ticks

        plt.tick_params(axis='x', which='both', length=4, pad=5)
        # Labeling the graph
        cbar = plt.colorbar()
        cbar.set_label('Red = Unavailable, Green = Available', fontsize=10)

        # Add a title with an increased font size
        plt.title(f"{player_name} availability on {days_dict[day]}", fontsize=14)

        # Adjust the layout to fit the x-axis labels and title
        plt.subplots_adjust(bottom=0.3,
                            top=0.85)  # Adjust bottom and top margins to give room for the x-labels and title

        plt.tight_layout()
    elif isinstance(player_name, list):  # Correct
        player_list = []  # Initialize an empty list to store player names
        player_availability = []  # Initialize an empty list to store all players' availability data
        group_name = None
        for player in player_name:
            row = fetch_timecard_data_from_db(guild_id, player[2], day, utc_offset_minutes)
            group_name = player[0]
            if row:
                player_list.append(player[2])  # Append the player name to the list
                availability = [int(x) if str(x).isdigit() else 0 for x in row]  # Process row data
                player_availability.append(availability)  # Add the player's availability to the list
        # Convert the list of lists into a 2D numpy array for plotting
        player_availability = np.array(player_availability)
        group_availability = np.sum(player_availability, axis=0)  # Summing along the player axis

        # Use the updated colormap call to avoid deprecation warning
        cmap = plt.colormaps.get_cmap('RdYlGn')

        # Create a plot with larger size to fit everything
        min_height = max(3, int(len(player_name) * 0.5))  # Minimum height of 3 inches
        fig, ax1 = plt.subplots(figsize=(14, min_height))  # ax1 will be used for the player availability heatmap

        # Plot the player availability heatmap
        heatmap1 = ax1.imshow(player_availability, cmap=cmap, aspect='auto')

        # Rotate the x-axis labels and align them properly
        midpoints = np.arange(len(time_labels)) - 0.5  # Shift ticks by -0.5 to place grid between labels
        ax1.set_xticks(np.arange(len(time_labels)))
        ax1.set_xticklabels(time_labels, rotation=90, ha="center", fontsize=8)

        # Set y-axis ticks to show player names
        player_list = [p[2] for p in player_name]  # Extract player names from player_name tuple
        ax1.set_yticks(np.arange(len(player_list)))
        ax1.set_yticklabels(player_list)

        # Add a grid between x-axis labels
        ax1.set_xticks(midpoints, minor=True)
        ax1.grid(which='minor', color='white', linestyle='-', linewidth=2)

        # Add color bar for player availability heatmap
        cbar1 = plt.colorbar(heatmap1, ax=ax1, pad=0.02)
        cbar1.set_label('Red = Unavailable, Green = Available', fontsize=10)

        # Create a second axis (ax2) to plot the group availability heatmap
        ax2 = ax1.twinx()  # Create a twin axis sharing the same x-axis
        ax2.set_yticks([])  # Hide y-axis ticks for ax2, since it's just an overlay

        # Plot the group availability as a secondary plot on ax2
        # You can use a different colormap to distinguish between individual and group heatmaps
        ax2.plot(group_availability, color='blue', linewidth=2, label='Group Availability')

        # Add a legend for group availability
        ax2.legend(loc='upper right')

        # Add a title with an increased font size
        ax1.set_title(f"{group_name} Availability for {days_dict[day]}", fontsize=14)

        # Adjust the layout to fit the x-axis labels and title
        plt.subplots_adjust(bottom=0.3, top=0.85)

        plt.tight_layout(rect=[0, 0, 0.95, 1])  # Adjust the right margin to fit the color bar

    # Save the plot as an image file
    plt.savefig('C:\\Pathparser\\plots\\timecard_plot.png')  # Ensure the path is correct for your system
    plt.close()


def convert_to_unix(military_time: str, timezone_str: str) -> str:
    # Ensure military_time is in HH:MM format
    if len(military_time) != 5 or ':' not in military_time:
        return "Invalid military time format. Please provide time as HH:MM."

    # Parse the military time into hours and minutes
    hours, minutes = map(int, military_time.split(':'))

    # Get the current date and combine it with the provided time
    current_date = datetime.now().date()
    time_combined = datetime(current_date.year, current_date.month, current_date.day, hours, minutes)

    # Convert to the given timezone
    try:
        timezone_info = pytz.timezone(timezone_str)
        localized_time = timezone_info.localize(time_combined)
        unix_timestamp = int(localized_time.timestamp())
        return f"<t:{unix_timestamp}:t>"
    except Exception as e:
        return f"Error: {e}"

    # Get the Unix timestamp

    # Return the formatted string for Discord


def adjust_day(day, hours, utc_offset):
    logging.debug(f"Adjusting day {day} with hours {hours} and UTC offset {utc_offset}")
    adjusted_day = day + (1 if int(hours) - int(utc_offset) >= 24 else -1 if int(hours) - int(utc_offset) <= 0 else 0)
    return ((adjusted_day - 1) % 7) + 1


# *** MISC FUNCTIONS *** #
def extract_document_id(url: str) -> Optional[str]:
    try:
        pattern = r'/document/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        else:
            return None
    except Exception as e:
        logging.error(f"Failed to extract document ID from URL '{url}': {e}")
        return None


def validate_mythweavers(url: str) -> Tuple[bool, str, int]:
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme != 'https':
            return False, "URL must start with 'https://'", 0
        if parsed_url.netloc != 'www.myth-weavers.com':
            return False, "URL must be from 'www.myth-weavers.com'", 1
        if parsed_url.path != '/sheets/':
            return False, "URL path must be '/sheet.html'", 2
        query_params = parse_qs(parsed_url.query)
        fragment_params = parse_qs(parsed_url.fragment)
        id_param = query_params.get('id') or fragment_params.get('id')
        if not id_param or not id_param[0].isdigit():
            return False, "URL must contain a valid 'id' parameter", 3
        return True, "", -1
    except Exception as e:
        logging.error(f"Error validating Myth-Weavers link '{url}': {e}")
        return False, "An error occurred during validation", -1


def validate_worldanvil(url: str) -> Tuple[bool, str, int]:
    """
    Validates a World Anvil character sheet URL.

    Args:
        url (str): The URL to validate.

    Returns:
        Tuple[bool, str, int]: A tuple containing a boolean indicating validity, an error message if invalid, and a step indicator.
    """
    try:
        parsed_url = urlparse(url)

        # Check the URL scheme
        if parsed_url.scheme != 'https':
            return False, "URL must start with 'https://'.", 0

        # Check the netloc (domain)
        if parsed_url.netloc not in ('www.worldanvil.com', 'worldanvil.com'):
            return False, "URL must be from 'www.worldanvil.com' or 'worldanvil.com'.", 1

        # Check that the path starts with '/hero/'
        if not parsed_url.path.startswith('/hero/'):
            return False, "URL path must start with '/hero/'.", 2

        # Extract the character ID from the path
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2 or path_parts[0] != 'hero' or not path_parts[1].isdigit():
            return False, "URL must contain a valid character ID after '/hero/'.", 3

        return True, "", -1  # Success case includes step indicator -1
    except Exception as e:
        logging.error(f"Error validating World Anvil link '{url}': {e}")
        return False, "An error occurred during validation.", -1  # Exception case uses step indicator -1


def validate_vtt(url: str) -> Tuple[bool, str, int]:
    """
    Validates a Virtual Tabletop (VTT) game link URL for platforms like Roll20 and Forge.

    Args:
        url (str): The URL to validate.

    Returns:
        Tuple[bool, str, int]: A tuple containing:
            - A boolean indicating validity.
            - An error message if invalid.
            - A step indicator for the validation process.
    """
    try:
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme.lower()
        domain = parsed_url.hostname.lower() if parsed_url.hostname else ''
        path = parsed_url.path.lower()

        # Step indicator starts at 0
        step = 0

        # Check the URL scheme
        if scheme != 'https':
            return False, "URL must start with 'https://'.", step

        step += 1  # Step 1

        # Define valid domains
        valid_domains = ('roll20.net', 'forge-vtt.com')

        # Check the domain
        if not any(domain.endswith(valid_domain) for valid_domain in valid_domains):
            return False, "URL must be from Roll20 or Forge.", step

        step += 1  # Step 2

        # Additional path validation for Roll20
        if domain.endswith('roll20.net'):
            if not path.startswith('/join/'):
                return False, "Roll20 game links should start with '/join/'.", step

        # Additional path validation for Forge
        if domain.endswith('forge-vtt.com'):
            print(path)
            if not path.startswith('/invite/') and not path.startswith('/game/'):
                return False, "Forge game links should start with '/invite/' or  '/game/'.", step

        # All checks passed
        return True, "", -1  # Success case includes step indicator -1

    except ValueError as e:
        logging.error(f"Error parsing game link '{url}': {e}")
        return False, "Invalid URL format.", -1  # Exception case uses step indicator -1


def parse_hammer_time_to_iso(hammer_time_str: str) -> datetime:
    return datetime.fromtimestamp(int(hammer_time_str), tz=timezone.utc)


def parse_hammer_time_to_timestamp(hammer_time_str: str) -> datetime:
    return datetime.fromisoformat(hammer_time_str)


def validate_hammertime(
        hammertime: Union[str, datetime]) -> Union[Tuple[bool, bool, Tuple[str, str, str, str]], Tuple[bool, str]]:
    try:
        # Check if hammertime is already a 10-digit Unix timestamp
        if len(hammertime) == 10 or len(hammertime) == 16:
            if len(hammertime) == 10:
                # Use only the first 10 digits if length is 16 (e.g., with milliseconds)
                hammertime = hammertime
                dt_hammertime = datetime.fromtimestamp(int(hammertime))
            elif len(hammertime) == 16:
                hammertime = hammertime[3:13]
                # Convert hammertime to datetime object
                dt_hammertime = datetime.fromtimestamp(int(hammertime))
            else:
                raise ValueError("Invalid timestamp format. Please provide a valid timestamp.")
            # Generate time formats for the Discord message
            date = f"<t:{hammertime}:D>"
            hour = f"<t:{hammertime}:t>"
            arrival = f"<t:{hammertime}:R>"
            success = True

            # Check if the datetime is more than 5 years in the past or in the future
            if dt_hammertime > datetime.now() or dt_hammertime < (datetime.now() - timedelta(days=365 * 5)):
                valid_time = True  # valid if it's in the future or more than 5 years ago
            else:
                valid_time = False  # invalid if it's in the past 5 years

            return success, valid_time, (date, hour, arrival, hammertime)
        else:
            return True, f"{hammertime}"
    except (ValueError, IndexError) as e:
        logging.exception(f"Error validating hammertime '{hammertime}': {e}")
        return False, "Invalid timestamp format. Please provide a valid timestamp."


def convert_datetime_to_unix(time_str, timezone_str):
    # Define possible date formats
    formats = ["%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M"]
    for fmt in formats:
        try:
            # Parse the date with the given format
            dt = datetime.strptime(time_str, fmt)
            break
        except ValueError:
            continue
    else:
        raise ValueError("Time format not recognized.")

    # Localize the datetime to the specified timezone
    tz = pytz.timezone(timezone_str)
    dt = tz.localize(dt)

    # Convert to Unix timestamp
    unix_time = int(dt.timestamp())
    return unix_time


# Function to validate "hammertime" based on different input formats.
async def complex_validate_hammertime(
        guild_id,
        author_name,
        hammertime: Union[str, datetime]) -> Union[Tuple[bool, bool, Tuple[str, str, str, str]], Tuple[bool, str]]:
    try:
        # If hammertime is either 10 or 16 characters long, assume it's a date or timestamp format that can be validated directly.
        if len(hammertime) == 10 or len(hammertime) == 16:
            hammertime_result = validate_hammertime(hammertime)
            return hammertime_result

        # Otherwise, connect to the database to retrieve the user's UTC offset.
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "SELECT UTC_Offset FROM Player_Timecard WHERE Player_Name = ?", (author_name,)
            )
            utc_result = await cursor.fetchone()

            # Proceed only if UTC offset was successfully retrieved.
            if utc_result:
                # Check if hammertime includes "AM" or "PM" and is likely in a 12-hour format (3 to 8 characters).
                if (hammertime[-2:] == 'PM' or hammertime[-2:] == 'AM') and 3 < len(hammertime) < 8:
                    midday = hammertime[-2:]  # Extract 'AM' or 'PM'
                    midday_hours = 0 if midday == 'AM' else 12
                    hammertime = hammertime[:-2].strip()  # Remove 'AM'/'PM' and strip whitespace

                    # Get current time in user's timezone.
                    now = datetime.now(tz=pytz.timezone(utc_result[0]))

                    # Depending on length, set the hour and minute, handling single and double-digit hours.
                    if len(hammertime) == 4:
                        updated_time = now.replace(hour=int(hammertime[:1]) + midday_hours, minute=int(hammertime[2:]))
                    elif len(hammertime) == 5:
                        updated_time = now.replace(hour=int(hammertime[:2]) + midday_hours, minute=int(hammertime[3:]))

                    # If the computed time has already passed today, set it to the same time tomorrow.
                    if now > updated_time:
                        updated_time += timedelta(days=1)

                    # Convert to Unix timestamp and validate.
                    create_timestamp = int(updated_time.timestamp())
                    hammertime_result = validate_hammertime(str(create_timestamp))

                # If hammertime is in 24-hour format without AM/PM, handle it here.
                elif len(hammertime) == 5:
                    now = datetime.now(tz=pytz.timezone(utc_result[0]))
                    updated_time = now.replace(hour=int(hammertime[:2]), minute=int(hammertime[3:]))

                    if now > updated_time:
                        updated_time += timedelta(days=1)

                    create_timestamp = int(updated_time.timestamp())
                    hammertime_result = validate_hammertime(str(create_timestamp))

                # If hammertime format is non-standard, use a conversion function with UTC offset.
                else:
                    (utc_offset,) = utc_result
                    create_timestamp = convert_datetime_to_unix(hammertime, utc_offset)
                    hammertime_result = validate_hammertime(str(create_timestamp))

                return hammertime_result

            # If no UTC offset was found, return an error message.
            else:
                return False, "Player not found in the database."

    # Exception handling for common errors like ValueError, IndexError, or database errors.
    except (ValueError, IndexError, aiosqlite.Error) as e:
        logging.exception(f"Error validating hammertime '{hammertime}': {e}")
        return False, "Invalid timestamp format. Please provide a valid timestamp."


def validate_worldanvil_link(guild_id: int, article_id: str) -> (
        Optional)[dict]:
    allowed_guilds = [883009758179762208, 280061170231017472]
    if guild_id not in allowed_guilds:
        logging.warning(f"Guild ID {guild_id} is not authorized to create articles.")
        return None
    try:
        api_key = os.getenv('WORLD_ANVIL_API')
        user_id = os.getenv('WORLD_ANVIL_USER')
        if not api_key or not user_id:
            logging.error("World Anvil API credentials are not set.")
            return None

        client = WaClient(
            'pathparser',
            'https://github.com/Solfyrism/Pathparser',
            'V1.1',
            api_key,
            user_id
        )

        returned_page = client.article.get(identifier=article_id, granularity=1)

        return returned_page
    except Exception as e:
        # I haven't ever gotten a proper exception from the World Anvil API, so this is a catch-all until I can specify it down. https://pypi.org/project/pywaclient/#exceptions has them, but I'm not sure how to catch them yet.
        logging.exception(f"Error in retrieving article with ID '{article_id}': {e}")
        return None


def ordinal(n):
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


async def put_wa_article(guild_id: int, template: str, category: str, title: str, overview: str, author: str) -> (
        Optional)[dict]:
    allowed_guilds = [883009758179762208, 280061170231017472]
    if guild_id not in allowed_guilds:
        logging.warning(f"Guild ID {guild_id} is not authorized to create articles.")
        return None
    try:
        api_key = os.getenv('WORLD_ANVIL_API')
        user_id = os.getenv('WORLD_ANVIL_USER')
        if not api_key or not user_id:
            logging.error("World Anvil API credentials are not set.")
            return None

        client = WaClient(
            'pathparser',
            'https://github.com/Solfyrism/Pathparser',
            'V1.1',
            api_key,
            user_id
        )
        world_id = 'f7a60480-ea15-4867-ae03-e9e0c676060a'

        evaluated_overview = drive_word_document(overview)

        # Map templates to entity classes
        template_to_entity_class = {
            'generic': 'Generic',
            'person': 'Person',
            'location': 'Location',
            # Add other mappings as needed
        }
        entity_class = template_to_entity_class.get(template.lower(), template)

        new_page = client.article.put({
            'title': title,
            'content': evaluated_overview,
            'category': {'id': category},
            'templateType': template.lower(),
            'state': 'public',
            'isDraft': False,
            'entityClass': entity_class.title(),
            'tags': author,
            'world': {'id': world_id}
        })
        return new_page
    except Exception as e:
        # I haven't ever gotten a proper exception from the World Anvil API, so this is a catch-all until I can specify it down. https://pypi.org/project/pywaclient/#exceptions has them, but I'm not sure how to catch them yet.
        logging.exception(f"Error in article creation for title '{title}': {e}")
        return None


async def patch_wa_article(guild_id: int, article_id: str, overview: str) -> Optional[dict]:
    allowed_guilds = [883009758179762208, 280061170231017472]
    if guild_id not in allowed_guilds:
        logging.warning(f"Guild ID {guild_id} is not authorized to create articles.")
        return None
    try:
        api_key = os.getenv('WORLD_ANVIL_API')
        user_id = os.getenv('WORLD_ANVIL_USER')
        if not api_key or not user_id:
            logging.error("World Anvil API credentials are not set.")
            return None

        client = WaClient(
            'pathparser',
            'https://github.com/Solfyrism/Pathparser',
            'V1.1',
            api_key,
            user_id
        )
        world_id = 'f7a60480-ea15-4867-ae03-e9e0c676060a'

        evaluated_overview = drive_word_document(overview)

        updated_page = client.article.patch(article_id, {
            'content': f'{evaluated_overview}',
            'world': {'id': world_id}
        })
        return updated_page
    except Exception as e:
        # I haven't ever gotten a proper exception from the World Anvil API, so this is a catch-all until I can specify it down. https://pypi.org/project/pywaclient/#exceptions has them, but I'm not sure how to catch them yet.
        logging.exception(f"Error in article creation for article '{article_id}': {e}")
        return None


async def put_wa_report(guild_id: int, session_id: int, overview: str, author: str, plot: str,
                        significance: int) -> Optional[tuple]:
    if guild_id in [883009758179762208, 280061170231017472]:
        evaluated_overview = drive_word_document(overview)
        try:
            client = WaClient(
                'pathparser',
                'https://github.com/Solfyrism/Pathparser',
                'V1.1',
                os.getenv('WORLD_ANVIL_API'),
                os.getenv('WORLD_ANVIL_USER')
            )
            world_id = 'f7a60480-ea15-4867-ae03-e9e0c676060a'
            async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("Select Search from Admin where Identifier = 'WA_Session_Folder'")
                session_folder = await cursor.fetchone()
                if not session_folder:
                    raise ValueError("No World Anvil session folder set.")
                session_folder = session_folder[0]
                await cursor.execute("Select Search from Admin where Identifier = 'WA_Timeline_Default'")
                timeline = await cursor.fetchone()
                if not timeline:
                    raise ValueError("No World Anvil timeline set.")
                timeline = timeline[0]
                await cursor.execute(
                    "SELECT Session_Name, Completed_Time, Alt_Reward_Party, Alt_Reward_All, Overview from Sessions where Session_ID = ?",
                    (session_id,))
                session_info = await cursor.fetchone()
                await cursor.execute(
                    "SELECT SA.Character_Name, PC.Article_Link, Article_ID FROM Sessions_Archive as SA left join Player_Characters AS PC on PC.Character_Name = SA.Character_Name WHERE SA.Session_ID = ? and SA.Player_Name != ? ",
                    (session_id, author))
                characters = await cursor.fetchall()
                if len(characters) == 0:
                    await cursor.execute(
                        "SELECT SA.Character_Name, PC.Article_Link, Article_ID FROM Sessions_Participants as SA left join Player_Characters AS PC on PC.Character_Name = SA.Character_Name WHERE SA.Session_ID = ? and SA.Player_Name != ? ",
                        (session_id, author))
                    characters = cursor.fetchall()
                else:
                    characters = characters
                related_persons_block = []
                counter = 0
                completed_str = session_info[1] if session_info[1] is not None else datetime.now().strftime(
                    "%Y-%m-%d %H:%M")
                completed_time = datetime.strptime(completed_str, '%Y-%m-%d %H:%M')
                day_test = datetime.strftime(completed_time, '%d')
                month_test = datetime.strftime(completed_time, '%m')
                new_report_page = client.article.put({
                    'title': f'{str(session_id).rjust(3, "0")}: {session_info[0]}',
                    'content': f'{evaluated_overview}',
                    'category': {'id': f'{session_folder}'},
                    'templateType': 'report',  # generic article template
                    'state': 'public',
                    'isDraft': False,
                    'entityClass': 'Report',
                    'tags': f'{author}',
                    'world': {'id': world_id},
                    #                  'reportDate': report_date,  # Convert the date to a string
                    'plots': [{'id': plot}]
                })
                for character in characters:
                    print(f" This is a character {character[0]} Do they have an article: {character[2]}?")
                    if character[2] is not None:
                        person = {'id': character[2]}
                        related_persons_block.append(person)
                        counter += 1
                if counter == 0:
                    new_timeline_page = client.history.put({
                        'title': f'{session_info[0]}',
                        'content': f'{session_info[4]}',
                        'fullcontent': f'{evaluated_overview}',
                        'timelines': [{'id': f'{timeline}'}],
                        'significance': significance,
                        'parsedContent': session_info[4],
                        'report': {'id': new_report_page['id']},
                        'year': 22083,
                        'month': int(month_test),
                        'day': int(day_test),
                        'endingYear': int(22083),
                        'endingMonth': int(month_test),
                        'endingDay': int(day_test),
                        'world': {'id': world_id}
                    })
                else:
                    related_persons_block = related_persons_block
                    new_timeline_page = client.history.put({
                        'title': f'{session_info[0]}',
                        'content': f'{session_info[4]}',
                        'fullcontent': f'{evaluated_overview}',
                        'timelines': [{'id': f'{timeline}'}],
                        'significance': significance,
                        'characters': related_persons_block,
                        'parsedContent': session_info[4],
                        'report': {'id': new_report_page['id']},
                        'year': 22083,
                        'month': int(month_test),
                        'day': int(day_test),
                        'endingYear': int(22083),
                        'endingMonth': int(month_test),
                        'endingDay': int(day_test),
                        'world': {'id': world_id}
                    })
                await cursor.execute(
                    'update Sessions set Article_link = ?, Article_ID = ?, History_ID = ? where Session_ID = ?',
                    (new_report_page['url'], new_report_page['id'], new_timeline_page['id'], session_id))
                await db.commit()
                return new_report_page, new_timeline_page
        except Exception as e:
            # I haven't ever gotten a proper exception from the World Anvil API, so this is a catch-all until I can specify it down. https://pypi.org/project/pywaclient/#exceptions has them, but I'm not sure how to catch them yet.
            logging.exception(f"Error in article creation for session '{session_id}': {e}")
            return None


async def patch_wa_report(guild_id: int, session_id: int, overview: str) -> Optional[dict]:
    if guild_id not in [883009758179762208, 280061170231017472]:
        logging.warning(f"Guild ID {guild_id} is not authorized to create articles.")
        return None

    evaluated_overview = drive_word_document(overview)
    try:
        client = WaClient(
            'pathparser',
            'https://github.com/Solfyrism/Pathparser',
            'V1.1',
            os.getenv('WORLD_ANVIL_API'),
            os.getenv('WORLD_ANVIL_USER')
        )
        world_id = 'f7a60480-ea15-4867-ae03-e9e0c676060a'

        # Establish a new database connection
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()

            # Fetch session information
            await cursor.execute("SELECT Article_ID, History_ID FROM Sessions WHERE Session_ID = ?", (session_id,))
            session_info = await cursor.fetchone()
            if not session_info:
                logging.error(f"No session found with Session_ID {session_id}")
                return None

            article_id = session_info[0]
            history_id = session_info[1]

            # Update the article and history on World Anvil
            new_page = client.article.patch(article_id, {
                'content': evaluated_overview,
                'world': {'id': world_id}
            })
            new_history = client.history.patch(history_id, {
                'content': evaluated_overview,
                'world': {'id': world_id}
            })

            return {'article': new_page, 'history': new_history}

    except Exception as e:
        logging.exception(f"Error in article update for session '{session_id}': {e}")
        return None


def drive_word_document(overview: str) -> Optional[str]:
    try:
        if overview.startswith("http"):
            document_id = extract_document_id(overview)
            if document_id is None:
                logging.error(f"Could not extract document ID from URL '{overview}'.")
                return None
        else:
            # If overview is not a URL, return it as is
            return overview

        # Authenticate with Google Docs API
        service_account_file = os.getenv('SERVICE_ACCOUNT_FILE')
        if not service_account_file:
            logging.error("Service account file is not set.")
            return None

        scopes = ['https://www.googleapis.com/auth/documents.readonly']
        credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
        service = build('docs', 'v1', credentials=credentials)

        # Fetch the document content
        document = service.documents().get(documentId=document_id).execute()

        word_blob = ""
        for element in document.get('body', {}).get('content', []):
            paragraph = element.get('paragraph')
            if paragraph:
                for text_run in paragraph.get('elements', []):
                    text_content = text_run.get('textRun', {}).get('content')
                    if text_content:
                        word_blob += text_content

        return word_blob.strip()
    except urllib.error.HTTPError as e:
        logging.exception(f"HTTP error while retrieving document: {e}")
        return None
    except Exception as e:
        logging.exception(f"Error in retrieving overview: {e}")
        return None


class ShopView(discord.ui.View):
    """Base class for shop views with pagination."""

    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int, interaction: discord.Interaction,
                 content: typing.Optional[str]):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.content = content
        self.message = None
        self.interaction = interaction
        self.guild_id = guild_id
        self.offset = offset
        self.limit = limit
        self.results = []
        self.embed = None

        self.message = None
        # Initialize buttons
        self.first_page_button = discord.ui.Button(label='First Page', style=discord.ButtonStyle.primary)
        self.previous_page_button = discord.ui.Button(label='Previous Page', style=discord.ButtonStyle.primary)
        self.next_page_button = discord.ui.Button(label='Next Page', style=discord.ButtonStyle.primary)
        self.last_page_button = discord.ui.Button(label='Last Page', style=discord.ButtonStyle.primary)

        self.first_page_button.callback = self.first_page
        self.previous_page_button.callback = self.previous_page
        self.next_page_button.callback = self.next_page
        self.last_page_button.callback = self.last_page

        self.add_item(self.first_page_button)
        self.add_item(self.previous_page_button)
        self.add_item(self.next_page_button)
        self.add_item(self.last_page_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure that only the user who initiated the view can interact with the buttons."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You cannot interact with this button.",
                ephemeral=True
            )
            return False
        return True

    async def first_page(self, interaction: discord.Interaction):
        """Handle moving to the first page."""
        await interaction.response.defer()
        if self.offset == 1:
            await interaction.response.send_message("You are already on the first page.", ephemeral=True)
            return
        self.offset = 1
        await self.update_results()
        await self.create_embed()
        await self.update_buttons()
        await interaction.message.edit(
            embed=self.embed,
            view=self
        )

    async def previous_page(self, interaction: discord.Interaction):
        """Handle moving to the previous page."""
        await interaction.response.defer()
        if self.offset > 1:
            self.offset -= self.limit
            if self.offset < 1:
                self.offset = 1
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await interaction.message.edit(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.response.send_message("You are on the first page.", ephemeral=True)

    async def next_page(self, interaction: discord.Interaction):
        """Handle moving to the next page."""
        await interaction.response.defer()
        max_items = await self.get_max_items()
        if self.offset + self.limit - 1 < max_items:
            self.offset += self.limit
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await interaction.message.edit(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.response.send_message("You are on the last page.", ephemeral=True)

    async def last_page(self, interaction: discord.Interaction):
        """Handle moving to the last page."""
        await interaction.response.defer()
        max_items = await self.get_max_items()
        last_page_offset = ((max_items - 1) // self.limit) * self.limit + 1
        if self.offset != last_page_offset:
            self.offset = last_page_offset
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await interaction.message.edit(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.response.send_message("You are on the last page.", ephemeral=True)

    async def update_buttons(self):
        """Update the enabled/disabled state of buttons based on the current page."""
        max_items = await self.get_max_items()
        first_page = self.offset == 1
        last_page = self.offset + self.limit - 1 >= max_items

        self.first_page_button.disabled = first_page
        self.previous_page_button.disabled = first_page
        self.next_page_button.disabled = last_page
        self.last_page_button.disabled = last_page

    async def send_initial_message(self):
        """Send the initial message with the view."""
        try:
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await self.interaction.followup.send(
                content=self.content,
                embed=self.embed,
                view=self
            )
            self.message = self.interaction.original_response()
        except (discord.HTTPException, AttributeError) as e:
            logging.error(f"Failed to send message: {e} in guild {self.interaction.guild.id} for {self.user_id}")

    async def on_timeout(self):
        """Disable buttons when the view times out."""
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(content=self.content, embed=self.embed, view=self)
            except discord.HTTPException as e:
                logging.error(f"Failed to edit message on timeout: {e}")

    async def update_results(self):
        """Fetch the results for the current page. To be implemented in subclasses."""
        raise NotImplementedError

    async def create_embed(self):
        """Create the embed for the current page. To be implemented in subclasses."""
        raise NotImplementedError

    async def get_max_items(self):
        """Get the total number of items. To be implemented in subclasses."""
        raise NotImplementedError


class RecipientAcknowledgementView(discord.ui.View):
    """Base class for views requiring acknowledgment."""

    def __init__(self, allowed_user_id: int, content: typing.Optional, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.allowed_user_id = allowed_user_id
        self.embed = None
        self.content = content
        self.message = None
        self.interaction = interaction
        # Initialize buttons
        self.accept_button = discord.ui.Button(label='Accept', style=discord.ButtonStyle.primary)
        self.reject_button = discord.ui.Button(label='Reject', style=discord.ButtonStyle.danger)

        self.accept_button.callback = self.accept
        self.reject_button.callback = self.reject

        self.add_item(self.accept_button)
        self.add_item(self.reject_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure that only the allowed user can interact with the buttons."""
        if interaction.user.id != self.allowed_user_id:
            await interaction.response.send_message(
                "You cannot interact with this button.",
                ephemeral=True
            )
            return False
        return True

    async def accept(self, interaction: discord.Interaction):
        """Handle the accept action."""
        await self.accepted(interaction)
        await interaction.message.edit(
            embed=self.embed,
            view=None
        )

    async def reject(self, interaction: discord.Interaction):
        """Handle the reject action."""
        await self.rejected(interaction)
        await interaction.message.edit(
            embed=self.embed,
            view=None
        )

    async def send_initial_message(self):
        """Send the initial message with the view."""
        await self.create_embed()
        try:
            async with aiosqlite.connect(f"Pathparser_{self.interaction.guild_id}_test.sqlite") as conn:
                cursor = await conn.cursor()
                await cursor.execute("SELECT Search FROM Admin WHERE identifier = 'Character_Transaction_Channel'")
                channel_id = await cursor.fetchone()
                if channel_id is None:
                    await self.interaction.followup.send(
                        "Character Transaction Channel not found in the database.",
                        ephemeral=True
                    )
                    return
                channel = self.interaction.guild.get_channel(int(channel_id[0]))
                if not channel:
                    channel = await self.interaction.guild.fetch_channel(int(channel_id[0]))
                if channel:
                    send_message = await channel.send(
                        content=self.content,
                        embed=self.embed,
                        view=self
                    )
                    await self.interaction.followup.send(
                        f"Message sent to the Character Transaction Channel. {send_message.jump_url}",
                        ephemeral=True
                    )
                else:
                    await self.interaction.followup.send(
                        content=self.content,
                        embed=self.embed,
                        view=self
                    )
        except (discord.HTTPException, AttributeError, aiosqlite.Error) as e:
            logging.error(f"Failed to send message: {e} in guild {self.interaction.guild.id}")
            await self.interaction.followup.send(
                "An error occurred while trying to send the message. Please try again later.",
                ephemeral=True
            )

    async def on_timeout(self):
        """Disable buttons when the view times out."""
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(content=self.content, embed=self.embed, view=self)
            except discord.HTTPException as e:
                logging.error(f"Failed to edit message on timeout: {e}")

    async def accepted(self, interaction: discord.Interaction):
        """To be implemented in subclasses."""
        raise NotImplementedError

    async def rejected(self, interaction: discord.Interaction):
        """To be implemented in subclasses."""
        raise NotImplementedError

    async def create_embed(self):
        """To be implemented in subclasses."""
        raise NotImplementedError


class SelfAcknowledgementView(discord.ui.View):
    """Base class for views requiring acknowledgment."""

    def __init__(self, content: typing.Optional, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.embed = None
        self.message = None
        self.content = content
        self.message = None
        self.interaction = interaction
        self.user_id = interaction.user.id

        # Initialize buttons
        self.accept_button = discord.ui.Button(label='Accept', style=discord.ButtonStyle.primary)
        self.reject_button = discord.ui.Button(label='Reject', style=discord.ButtonStyle.danger)

        self.accept_button.callback = self.accept
        self.reject_button.callback = self.reject

        self.add_item(self.accept_button)
        self.add_item(self.reject_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure that only the user who initiated the view can interact with the buttons."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You cannot interact with this button.",
                ephemeral=True
            )
            return False
        return True

    async def send_initial_message(self):
        """Send the initial message with the view."""
        await self.create_embed()
        try:
            self.message = await self.interaction.followup.send(
                content=self.content,
                embed=self.embed,
                view=self
            )
        except (discord.HTTPException, AttributeError) as e:
            logging.error(f"Failed to send message: {e} in guild {self.interaction.guild.id} for {self.user_id}")

    async def on_timeout(self):
        """Disable buttons when the view times out."""
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(content=self.content, embed=self.embed, view=self)
            except (discord.HTTPException, AttributeError) as e:
                logging.error(
                    f"Failed to edit message on timeout for user {self.user_id} in guild {self.interaction.guild.id}: {e}")

    async def accept(self, interaction: discord.Interaction):
        """Handle the accept action."""
        await interaction.response.defer()
        await self.accepted(interaction)
        await interaction.message.edit(
            embed=self.embed,
            view=None
        )

    async def reject(self, interaction: discord.Interaction):
        """Handle the reject action."""
        await interaction.response.defer()
        await self.rejected(interaction)
        await interaction.message.edit(
            embed=self.embed,
            view=None
        )

    async def accepted(self, interaction: discord.Interaction):
        """To be implemented in subclasses."""
        raise NotImplementedError

    async def rejected(self, interaction: discord.Interaction):
        """To be implemented in subclasses."""
        raise NotImplementedError

    async def create_embed(self):
        """To be implemented in subclasses."""
        raise NotImplementedError


class DualView(discord.ui.View):
    """Base class for shop views with pagination."""

    def __init__(self, user_id, guild_id, offset, limit, view_type, content: typing.Optional,
                 interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.guild_id = guild_id
        self.offset = offset
        self.limit = limit
        self.content = content
        self.message = None
        self.interaction = interaction
        self.results = []
        self.embed = None
        self.view_type = view_type

        # Initialize buttons
        self.first_page_button = discord.ui.Button(label='First Page', style=discord.ButtonStyle.primary)
        self.previous_page_button = discord.ui.Button(label='Previous Page', style=discord.ButtonStyle.primary)
        self.change_view_button = discord.ui.Button(label='Change View', style=discord.ButtonStyle.primary)
        self.next_page_button = discord.ui.Button(label='Next Page', style=discord.ButtonStyle.primary)
        self.last_page_button = discord.ui.Button(label='Last Page', style=discord.ButtonStyle.primary)

        self.first_page_button.callback = self.first_page
        self.previous_page_button.callback = self.previous_page
        self.change_view_button.callback = self.change_view
        self.next_page_button.callback = self.next_page
        self.last_page_button.callback = self.last_page

        self.add_item(self.first_page_button)
        self.add_item(self.previous_page_button)
        self.add_item(self.change_view_button)
        self.add_item(self.next_page_button)
        self.add_item(self.last_page_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure that only the user who initiated the view can interact with the buttons."""
        try:
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    "You cannot interact with this button.",
                    ephemeral=True
                )
                return False
            return True
        except Exception as e:
            logging.error(f"Failed to check interaction: {e}")
            raise

    async def first_page(self, interaction: discord.Interaction):
        """Handle moving to the first page."""
        try:
            await interaction.response.defer()
            if self.offset == 1:
                await interaction.response.send_message("You are already on the first page.", ephemeral=True)
                return
            self.offset = 1
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await interaction.message.edit(
                embed=self.embed,
                view=self
            )
        except Exception as e:
            logging.error(f"Failed to move to the first page: {e}")
            raise

    async def previous_page(self, interaction: discord.Interaction):
        """Handle moving to the previous page."""
        try:
            await interaction.response.defer()
            if self.offset > 1:
                self.offset -= self.limit
                if self.offset < 1:
                    self.offset = 1
                await self.update_results()
                await self.create_embed()
                await self.update_buttons()
                await interaction.message.edit(
                    embed=self.embed,
                    view=self
                )
            else:
                await interaction.followup.send("You are on the first page.", ephemeral=True)
        except Exception as e:
            logging.error(f"Failed to move to the previous page: {e}")
            raise

    async def send_initial_message(self):
        """Send the initial message with the view."""
        try:
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            self.message = await self.interaction.followup.send(
                content=self.content,
                embed=self.embed,
                view=self
            )
        except discord.HTTPException as e:
            logging.error(
                f"Failed to send message due to HTTPException: {e} in guild {self.interaction.guild.id} for {self.user_id}")
        except Exception as e:
            logging.error(f"Failed to send message: {e} in guild {self.interaction.guild.id} for {self.user_id}")

    async def on_timeout(self):
        """Disable buttons when the view times out."""
        try:
            for child in self.children:
                child.disabled = True
            if self.message:
                try:
                    await self.message.edit(content=self.content, embed=self.embed, view=self)
                except discord.HTTPException as e:
                    logging.error(f"Failed to edit message on timeout: {e}")

        except Exception as e:
            logging.error(f"Failed to disable buttons: {e}")
            raise

    async def change_view(self, interaction: discord.Interaction):
        """Change the view type."""
        await interaction.response.defer()
        try:
            await self.on_view_change()
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await interaction.message.edit(
                embed=self.embed,
                view=self
            )
        except Exception as e:
            logging.error(f"Failed to change view: {e}")
            raise

    async def next_page(self, interaction: discord.Interaction):
        """Handle moving to the next page."""
        try:
            await interaction.response.defer()
            max_items = await self.get_max_items()
            if self.offset + self.limit - 1 < max_items:
                self.offset += self.limit
                await self.update_results()
                await self.create_embed()
                await self.update_buttons()
                await interaction.message.edit(
                    embed=self.embed,
                    view=self
                )
            else:
                await interaction.response.send_message("You are on the last page.", ephemeral=True)
        except Exception as e:
            logging.error(f"Failed to move to the next page: {e}")
            raise

    async def last_page(self, interaction: discord.Interaction):
        """Handle moving to the last page."""
        try:
            await interaction.response.defer()
            max_items = await self.get_max_items()
            last_page_offset = ((max_items - 1) // self.limit) * self.limit + 1
            if self.offset != last_page_offset:
                self.offset = last_page_offset
                await self.update_results()
                await self.create_embed()
                await self.update_buttons()
                await interaction.message.edit(
                    embed=self.embed,
                    view=self
                )
            else:
                await interaction.response.send_message("You are on the last page.", ephemeral=True)
        except Exception as e:
            logging.error(f"Failed to move to the last page: {e}")
            raise

    async def update_buttons(self):
        """Update the enabled/disabled state of buttons based on the current page."""
        try:

            max_items = await self.get_max_items()
            print("Updating buttons", self.offset, self.limit, max_items)
            first_page = self.offset == 1
            last_page = self.offset + self.limit - 1 >= max_items

            self.first_page_button.disabled = first_page
            self.previous_page_button.disabled = first_page
            self.next_page_button.disabled = last_page
            self.last_page_button.disabled = last_page
        except Exception as e:
            logging.error(f"Failed to update buttons: {e}")
            raise

    async def on_view_change(self):
        """Change the view type."""
        raise NotImplementedError

    async def update_results(self):
        """Fetch the results for the current page. To be implemented in subclasses."""
        raise NotImplementedError

    async def create_embed(self):
        """Create the embed for the current page. To be implemented in subclasses."""
        raise NotImplementedError

    async def get_max_items(self):
        """Get the total number of items. To be implemented in subclasses."""
        raise NotImplementedError


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='pathparser.log',  # Specify the log file name
    filemode='a'  # Append mode
)
