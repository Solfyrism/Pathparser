import typing
import urllib.error
import discord
import math
import sqlite3
from dateutil import parser
from discord import app_commands
import pytz
from math import floor
from dotenv import load_dotenv
from unidecode import unidecode
from pywaclient.api import BoromirApiClient as WaClient
import numpy as np
from typing import List, Optional, Tuple, Union
import matplotlib.pyplot as plt
from zoneinfo import available_timezones, ZoneInfo
import os
from datetime import datetime
from decimal import Decimal
import aiosqlite
import logging
from dataclasses import dataclass
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs

load_dotenv()
# CALL ME MR MONEYBAGS BECAUSE HERE IS MY CASH
timezone_cache = sorted(available_timezones())


# *** AUTOCOMPLETION COMMANDS *** #
async def character_select_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(
        "SELECT True_Character_Name, Character_Name from Player_Characters where Character_Name LIKE ? OR Nickname LIKE ? LIMIT 5",
        (f"%{current}%", f"%{current}%"))
    character_list = cursor.fetchall()
    for characters in character_list:
        if current in characters[1]:
            data.append(app_commands.Choice(name=characters[1], value=characters[1]))
    cursor.close()
    db.close()
    return data


async def stg_character_select_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
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


async def own_character_select_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(
        "SELECT True_Character_Name, Character_Name from Player_Characters where Player_Name = ? AND Character_Name LIKE ? OR Player_Name = ? AND Nickname LIKE ?",
        (interaction.user.name, f"%{current}%", interaction.user.name, f"%{current}%"))
    character_list = cursor.fetchall()
    for characters in character_list:
        if current in characters[1]:
            data.append(app_commands.Choice(name=characters[1], value=characters[1]))
    cursor.close()
    db.close()
    return data


async def get_plots(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    """This is a test command for the wa command."""
    data = []
    guild_id = interaction.guild_id
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


async def get_precreated_plots(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
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


async def session_lookup(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(
        "SELECT Session_ID, Session_Name FROM Sessions WHERE GM_Name = ? AND Session_ID LIKE ?  and Completed_Time is not Null OR GM_Name = ? AND Session_Name like ? and Completed_Time is not Null Limit 15",
        (interaction.user.name, f"%{current}%", interaction.user.name, f"%{current}%"))
    session_list = cursor.fetchall()
    for test_text in session_list:
        if current in str(test_text[0]) or str.lower(current) in str.lower(test_text[1]):
            name_result = f"{test_text[0]}: {test_text[1]}"
            data.append(app_commands.Choice(name=name_result, value=test_text[0]))
    cursor.close()
    db.close()
    return data


async def group_id_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
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


async def player_session_lookup(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
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


async def fame_lookup(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
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


async def title_lookup(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(
        "SELECT ID, Masculine_Name, Feminine_Name, Fame, Effect from Store_Title WHERE Masculine_Name LIKE ? OR Feminine_Name LIKE ? LEFT JOIN  Limit 20",
        (f"%{current}%", f"%{current}%"))
    character_list = cursor.fetchall()
    for characters in character_list:
        if current in characters[1]:
            data.append(app_commands.Choice(name=f"{characters[1]}", value=characters[1]))
    cursor.close()
    db.close()
    return data


# *** DISPLAY FUNCTIONS *** #

async def character_embed(cursor, character_name: str, guild) -> (Union[Tuple[discord.Embed, str, int], str]):
    try:
        await cursor.execute("SELECT Search from Admin where Identifier = 'Accepted_Bio_Channel'")
        channel_id = await cursor.fetchone()
        # 8 7 7 6
        await cursor.execute(
            "SELECT player_name, player_id, True_Character_Name, Title, Titles, Description, Oath, Level, "
            "Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, "
            "Essence, Fame, Prestige, Color, Mythweavers, Image_Link, Tradition_Name, "
            "Tradition_Link, Template_Name, Template_Link, Article_Link, Message_ID"
            " FROM Player_Characters WHERE Character_Name = ?", (character_name,))
        character_info = await cursor.fetchone()
        color = character_info[17]
        int_color = int(color[1:], 16)
        description_field = f" "
        if character_info[4] is not None:
            description_field += f"**Other Names**: {character_info[4]} \r\n"  # Titles
        if character_info[25] is not None:  # Backstory
            description_field += f"[**Backstory**](<{character_info[25]}>)"
        titled_character_name = character_info[2] if character_info[3] is None else \
            f"{character_info[3]} {character_info[2]}"  # Store bought Title, Character Name, Store bought Title, Character Name
        embed = discord.Embed(title=f"{titled_character_name}", url=f'{character_info[18]}',
                              description=f"{description_field}",  # Character Name, Mythweavers, Description
                              color=int_color)
        embed.set_author(name=f'{character_info[0]}')  # Player Name
        embed.set_thumbnail(url=f'{character_info[20]}')  # Image Link
        embed.add_field(name="Information",
                        value=f'**Level**: {character_info[7]}, '
                              f'**Mythic Tier**: {character_info[8]}, '
                              f'**Fame**: {character_info[16]}, '
                              f'**Prestige**: {character_info[17]}',
                        # Level, Tier, Fame, Prestige
                        inline=False)
        embed.add_field(name="Experience",
                        value=f'**Milestones**: {character_info[9]}, '
                              f'**Remaining**: {character_info[10]}')  # Milestones, Remaining Milestones
        embed.add_field(name="Mythic",
                        value=f'**Trials**: {character_info[11]}, '
                              f'**Remaining**: {character_info[12]}')  # Trials, Remaining Trials
        embed.add_field(name="Current Wealth",
                        value=f'**GP**: {Decimal(character_info[13])}, '
                              f'**Effective** {Decimal(character_info[14])} GP',
                        inline=False)  # Gold, Effective Gold
        embed.add_field(name="Current Essence", value=f'**Essence**: {character_info[15]}')
        linkage = f""
        if character_info[21] is not None:  # Tradition Name
            linkage += f"**Tradition**: [{character_info[21]}]({character_info[22]})"
        if character_info[23] is not None:  # Template Name
            if character_info[21] is not None:  # check if there's a tradition to link to.
                linkage += " "
            linkage += f"**Template**: [{character_info[23]}]({character_info[24]})"
        if character_info[21] is not None or character_info[23] is not None:
            # check if there's a tradition or template worth adding to the embed.
            embed.add_field(name=f'Additional Info', value=linkage, inline=False)
        # Handling Oaths below.
        description = character_info[5]
        if character_info[6] == 'Offerings':
            embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
        elif character_info[6] == 'Poverty':
            embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
        elif character_info[6] == 'Absolute':
            embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
        else:
            embed.set_footer(text=f'{description}')
        message = f"<@{character_info[1]}>"
        bio_channel = guild.get_channel(channel_id[0])
        bio_message = await bio_channel.fetch_message(character_info[26])
        await bio_message.edit(content=message, embed=embed)
        return_value = embed, message, channel_id[0]
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"An error occurred whilst building character embed for '{character_name}': {e}")
        return_value = f"An error occurred whilst building character embed for '{character_name}'."
    return return_value


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
    effective_gold: Optional[Decimal] = None
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
class UpdateCharacter:
    character_name: str
    level_package: Optional[Tuple[int, int, int]] = None  # (Level, Milestones, Milestones_Required)
    mythic_package: Optional[Tuple[int, int, int]] = None  # (Tier, Trials, Trials_Required)
    gold_package: Optional[Tuple[int, int, int]] = None  # (Gold, Gold_Value, Gold_Value_Max)
    essence: Optional[int] = None
    fame_package: Optional[Tuple[int, int]] = None  # (Fame, Prestige)


async def update_character(cursor, change: UpdateCharacter) -> Union[str, Tuple[discord.Embed, str, int]]:
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
            assignments.extend(["Gold = ?", "Gold_Value = ?", "Gold_Value_Max = ?"])
            values.extend(change.gold_package)

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
        await cursor.execute(sql_statement, values)
        return "Character updated successfully."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"An error occurred whilst updating '{change.character_name}': {e}")
        return f"An error occurred whilst updating '{change.character_name}'."

# Function to create the embed
async def log_embed(change: CharacterChange, guild, thread, bot) -> discord.Embed:
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
            gold_change = round(change.gold_change, 2)
            effective_gold = round(change.effective_gold, 2) if change.effective_gold is not None else "N/A"
            embed.add_field(
                name="Wealth Changes",
                value=(
                    f"**Gold**: {gold}\n"
                    f"**Gold Change**: {gold_change}\n"
                    f"**Effective Gold**: {effective_gold} GP\n"
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
                    # Unarchive the thread
                    await logging_thread.edit(archived=False, locked=False)
                except discord.Forbidden:
                    logging.exception(f"Bot lacks permissions to unarchive thread {logging_thread.id}")
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
    return today + datetime.timedelta(days=days_ahead)


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
        now_utc = datetime.now(datetime.timezone.utc)
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
    if t[:1] == '-':
        hours, minutes = map(int, t[1:].split(':'))
        hours = -abs(hours)
        minutes = -abs(minutes)
    elif t[:1] == '+':
        hours, minutes = map(int, t[1:].split(':'))
    elif len(t) == 5:
        hours, minutes = map(int, t.split(':'))
    else:
        hours = 0
        minutes = 0
    return hours * 60 + minutes


def fetch_timecard_data_from_db(guild_id, player_name, day, utc_offset):
    time_labels = [
        "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30",
        "05:00", "05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30",
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
        "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30",
        "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", "24:00", "24:30"
    ]
    conn = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
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
    daysdict = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
    # Get timecard data for the player and day
    print(f"trying to adjust UTC Offset of {utc_offset}")
    utc_offset_time = get_utc_offset(utc_offset)
    print(f"transforming of {utc_offset_time}")
    utc_offset_minutes = time_to_minutes(utc_offset_time)
    test = ['nuts', 'berries', 'bananas']
    if type(player_name) is str:
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
        plt.title(f"{player_name} availability on {daysdict[day]}", fontsize=14)

        # Adjust the layout to fit the x-axis labels and title
        plt.subplots_adjust(bottom=0.3,
                            top=0.85)  # Adjust bottom and top margins to give room for the x-labels and title

        plt.tight_layout()
    elif type(player_name) is type(test):  # Correct
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
        ax1.set_title(f"{group_name} Availability for {daysdict[day]}", fontsize=14)

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
        timezone = pytz.timezone(timezone_str)
        localized_time = timezone.localize(time_combined)
        unix_timestamp = int(localized_time.timestamp())
        return f"<t:{unix_timestamp}:t>"
    except Exception as e:
        return f"Error: {e}"

    # Get the Unix timestamp

    # Return the formatted string for Discord


def adjust_day(day, hours, utc_offset):
    print(type(day), hours, type(utc_offset))
    adjusted_day = day + (1 if int(hours) - int(utc_offset) >= 24 else -1 if int(hours) - utc_offset <= 0 else 0)
    # Ensure the day wraps around in the range 1 to 7 (days of the week)
    return (adjusted_day - 1) % 7 + 1


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


def validate_mythweavers(url: str) -> Tuple[bool, str]:
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme != 'https':
            return False, "URL must start with 'https://'"
        if parsed_url.netloc != 'www.myth-weavers.com':
            return False, "URL must be from 'www.myth-weavers.com'"
        if parsed_url.path != '/sheet.html':
            return False, "URL path must be '/sheet.html'"
        query_params = parse_qs(parsed_url.query)
        fragment_params = parse_qs(parsed_url.fragment)
        id_param = query_params.get('id') or fragment_params.get('id')
        if not id_param or not id_param[0].isdigit():
            return False, "URL must contain a valid 'id' parameter"
        return True, ""
    except Exception as e:
        logging.error(f"Error validating Myth-Weavers link '{url}': {e}")
        return False, "An error occurred during validation"


def ordinal(n):
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd"][n % 10] if n % 10 < 4 else "th"
    return str(n) + suffix


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
            'templateType': template,
            'state': 'public',
            'isDraft': False,
            'entityClass': entity_class,
            'tags': author,
            'world': {'id': world_id}
        })
        return new_page
    except Exception as e:
        # I haven't ever gotten a proper exception from the World Anvil API, so this is a catch-all until I can specify it down. https://pypi.org/project/pywaclient/#exceptions has them, but I'm not sure how to catch them yet.
        logging.exception(f"Error in article creation for title '{title}': {e}")
        return None


async def patch_wa_article(cursor, guild_id: int, article_id: str, title: str, overview: str) -> Optional[dict]:
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
            'title': title,
            'content': f'{evaluated_overview}',
            'world': {'id': world_id}
        })
        return updated_page
    except Exception as e:
        # I haven't ever gotten a proper exception from the World Anvil API, so this is a catch-all until I can specify it down. https://pypi.org/project/pywaclient/#exceptions has them, but I'm not sure how to catch them yet.
        logging.exception(f"Error in article creation for title '{title}': {e}")
        return None


async def put_wa_report(cursor, guild_id: int, session_id: int, overview: str, author: str, plot: str,
                        significance: int) -> Optional[dict]:
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
            await cursor.execute(
                "SELECT Session_Name, Completed_Time, Alt_Reward_Party, Alt_Reward_All, Overview from Sessions where Session_ID = ?",
                (session_id,))
            session_info = await cursor.fetchone()
            await cursor.execute(
                "SELECT SA.Character_Name, PC.Article_Link, Article_ID FROM Sessions_Archive as SA left join Player_Characters AS PC on PC.Character_Name = SA.Character_Name WHERE SA.Session_ID = ? and SA.Player_Name != ? ",
                (session_id, author))
            characters = await cursor.fetchall()
            if len(characters) == 0:
                cursor.execute(
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
                'category': {'id': 'b71f939a-f72d-413b-b4d7-4ebff1e162ca'},
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
                    'timelines': [{'id': '906c8c14-2283-47e0-96e2-0fcd9f71d0d0'}],
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
                    'timelines': [{'id': '906c8c14-2283-47e0-96e2-0fcd9f71d0d0'}],
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
            await cursor.connection.commit()
        except Exception as e:
            # I haven't ever gotten a proper exception from the World Anvil API, so this is a catch-all until I can specify it down. https://pypi.org/project/pywaclient/#exceptions has them, but I'm not sure how to catch them yet.
            logging.exception(f"Error in article creation for session '{session_id}': {e}")
            return None


async def patch_wa_report(cursor, guild_id: int, session_id: int, overview: str, author: str, plot: str,
                          significance: int) -> Optional[dict]:
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
            session_info = cursor.fetchone()
            new_page = client.article.patch(session_info[0], {
                'content': f'{overview}',
                'world': {'id': world_id}
            })
            new_history = client.history.patch(session_info[0], {
                'content': f'{overview}',
                'world': {'id': world_id}
            })
        except Exception as e:
            # I haven't ever gotten a proper exception from the World Anvil API, so this is a catch-all until I can specify it down. https://pypi.org/project/pywaclient/#exceptions has them, but I'm not sure how to catch them yet.
            logging.exception(f"Error in article creation for session '{session_id}': {e}")
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

    def __init__(self, user_id, guild_id, offset, limit):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.guild_id = guild_id
        self.offset = offset
        self.limit = limit
        self.results = []
        self.embed = None

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
        if self.offset == 1:
            await interaction.response.send_message("You are already on the first page.", ephemeral=True)
            return
        self.offset = 1
        await self.update_results()
        await self.create_embed()
        await self.update_buttons()
        await interaction.response.edit_message(
            embed=self.embed,
            view=self
        )

    async def previous_page(self, interaction: discord.Interaction):
        """Handle moving to the previous page."""
        if self.offset > 1:
            self.offset -= self.limit
            if self.offset < 1:
                self.offset = 1
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await interaction.response.edit_message(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.response.send_message("You are on the first page.", ephemeral=True)

    async def next_page(self, interaction: discord.Interaction):
        """Handle moving to the next page."""
        max_items = await self.get_max_items()
        if self.offset + self.limit - 1 < max_items:
            self.offset += self.limit
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await interaction.response.edit_message(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.response.send_message("You are on the last page.", ephemeral=True)

    async def last_page(self, interaction: discord.Interaction):
        """Handle moving to the last page."""
        max_items = await self.get_max_items()
        last_page_offset = ((max_items - 1) // self.limit) * self.limit + 1
        if self.offset != last_page_offset:
            self.offset = last_page_offset
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await interaction.response.edit_message(
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

    async def update_results(self):
        """Fetch the results for the current page. To be implemented in subclasses."""
        raise NotImplementedError

    async def create_embed(self):
        """Create the embed for the current page. To be implemented in subclasses."""
        raise NotImplementedError

    async def get_max_items(self):
        """Get the total number of items. To be implemented in subclasses."""
        raise NotImplementedError


class AcknowledgementView(discord.ui.View):
    """Base class for views requiring acknowledgment."""

    def __init__(self, allowed_user_id: int):
        super().__init__(timeout=180)
        self.allowed_user_id = allowed_user_id
        self.embed = None

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
        await interaction.response.edit_message(
            embed=self.embed,
            view=None
        )

    async def reject(self, interaction: discord.Interaction):
        """Handle the reject action."""
        await self.rejected(interaction)
        await interaction.response.edit_message(
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

    def __init__(self, user_id, guild_id, offset, limit, view_type):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.guild_id = guild_id
        self.offset = offset
        self.limit = limit
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
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You cannot interact with this button.",
                ephemeral=True
            )
            return False
        return True

    async def first_page(self, interaction: discord.Interaction):
        """Handle moving to the first page."""
        if self.offset == 1:
            await interaction.response.send_message("You are already on the first page.", ephemeral=True)
            return
        self.offset = 1
        await self.update_results()
        await self.create_embed()
        await self.update_buttons()
        await interaction.response.edit_message(
            embed=self.embed,
            view=self
        )

    async def previous_page(self, interaction: discord.Interaction):
        """Handle moving to the previous page."""
        if self.offset > 1:
            self.offset -= self.limit
            if self.offset < 1:
                self.offset = 1
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await interaction.response.edit_message(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.response.send_message("You are on the first page.", ephemeral=True)

    async def change_view(self, interaction: discord.Interaction):
        """Change the viewtype."""
        await self.on_view_change()
        await self.update_results()
        await self.create_embed()
        await self.update_buttons()
        await interaction.response.edit_message(
            embed=self.embed,
            view=self
        )

    async def next_page(self, interaction: discord.Interaction):
        """Handle moving to the next page."""
        max_items = await self.get_max_items()
        if self.offset + self.limit - 1 < max_items:
            self.offset += self.limit
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await interaction.response.edit_message(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.response.send_message("You are on the last page.", ephemeral=True)

    async def last_page(self, interaction: discord.Interaction):
        """Handle moving to the last page."""
        max_items = await self.get_max_items()
        last_page_offset = ((max_items - 1) // self.limit) * self.limit + 1
        if self.offset != last_page_offset:
            self.offset = last_page_offset
            await self.update_results()
            await self.create_embed()
            await self.update_buttons()
            await interaction.response.edit_message(
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
