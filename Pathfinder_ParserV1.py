import datetime
import time
import re
import shutil
import typing
import discord
import sqlite3
import os
from discord import app_commands
from discord.ext import commands
from Event_List import Managed_events as EventCommand
from unbelievaboat import Client
import unbelievaboat
import asyncio
import math
import random
from math import floor
from dotenv import load_dotenv; load_dotenv()
from unidecode import unidecode
from pywaclient.api import BoromirApiClient as WaClient
import numpy as np
import matplotlib.pyplot as plt
intents = discord.Intents.default()
intents.typing = True
intents.message_content = True
intents.members = True
os.chdir("C:\\pathparser")


"""class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False
    async def on_ready(self):

"""

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())


class Kingdom(app_commands.Group):
    ...


class Admin(app_commands.Group):
    ...


class Buildings(app_commands.Group):
    ...


class Settlement(app_commands.Group):
    ...


class Leadership(app_commands.Group):
    ...


class Hex(app_commands.Group):
    ...


class Character(app_commands.Group):
    ...


class Gold(app_commands.Group):
    ...


class Gamemaster(app_commands.Group):
    ...


class Overseer(app_commands.Group):
    ...

class Content(app_commands.Group):
    ...

class Player(app_commands.Group):
    ...

admin = Admin(name="admin", description="Administration Commands")
kingdom = Kingdom(name="kingdom", description="Kingdom Management Commands")
buildings = Buildings(name="buildings", description="Building Management Commands")
settlement = Settlement(name="settlement", description="Settlement Management Commands")
leadership = Leadership(name="leadership", description="Leadership Management Commands")
hex = Hex(name="hex", description="Hex Management Commands")
character = Character(name="character", description="Character Management Commands")
gold = Gold(name="gold", description="gold management commands")
gamemaster = Gamemaster(name="gamemaster", description="GameMaster session management commands")
player = Player(name="player", description="Player session management commands")
overseer = Overseer(name="overseer", description="Overseer commands")
content = Content(name="content", description="Content Reviewer commands")

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f"We have logged in as {bot.user}.")
    bot.tree.add_command(kingdom)
    bot.tree.add_command(admin)
    bot.tree.add_command(buildings)
    bot.tree.add_command(settlement)
    bot.tree.add_command(leadership)
    bot.tree.add_command(hex)
    bot.tree.add_command(character)
    bot.tree.add_command(gold)
    bot.tree.add_command(gamemaster)
    bot.tree.add_command(player)
    bot.tree.add_command(overseer)
    bot.tree.add_command(content)

def require_me(ctx, action):
    if action == 'Item_Store':
        truthiness = True
    else:
        truthiness = False
    return truthiness

def hide_me(ctx, modify):
    if modify == 4 or modify.value == 4:
        truthiness = True
    else:
        truthiness = False
    return truthiness


def adjust_day(day, hours, utc_offset):
    print(type(day), hours, type(utc_offset))
    adjusted_day = day + (1 if int(hours) - int(utc_offset) >= 24 else -1 if int(hours) - utc_offset <= 0 else 0)
    # Ensure the day wraps around in the range 1 to 7 (days of the week)
    return (adjusted_day - 1) % 7 + 1


def character_embed(player_name, player_id, character_name, titles, description, oath, level, tier, milestones, milestones_required, trials, trials_required, gold, effective_gold, flux, color, mythweavers, image_link, tradition_name, tradition_link, template_name, template_link, fame, title, prestige, backstory):
    int_color = int(color[1:], 16)
    print(titles)
    description_field = f" "
    if titles is not None:
        description_field += f"**Other Names**: {titles} \r\n"
    if backstory is not None:
        description_field += f"[**Backstory**](<{backstory}>)"
    character_name = character_name if title is None else f"{title} {character_name}"
    embed = discord.Embed(title=f"{character_name}", url=f'{mythweavers}', description=f"{description_field}", color=int_color)
    embed.set_author(name=f'{player_name}')
    embed.set_thumbnail(url=f'{image_link}')
    embed.add_field(name="Information", value=f'**Level**: {level}, **Mythic Tier**: {tier}, **Fame**: {fame}, **Prestige**: {prestige}', inline=False)
    embed.add_field(name="Experience", value=f'**Milestones**: {milestones}, **Remaining**: {milestones_required}')
    embed.add_field(name="Mythic", value=f'**Trials**: {trials}, **Remaining**: {trials_required}', inline=True)
    embed.add_field(name="Current Wealth", value=f'**GP**: {round(gold,2)}, **Effective** {round(effective_gold,2)} GP', inline=False)
    embed.add_field(name="Current Flux", value=f'**Flux**: {flux}')
    linkage = f""
    if tradition_name is not None:
        linkage += f"**Tradition**: [{tradition_name}]({tradition_link})"
    if template_name is not None:
        if tradition_name is not None:
            linkage += " "
        linkage += f"**Template**: [{template_name}]({template_link})"
    if tradition_name is not None or template_name is not None:
        embed.add_field(name=f'Additional Info', value=linkage, inline=False)
    print(oath)
    if oath == 'Offerings':
        embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
    elif oath == 'Poverty':
        embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
    elif oath == 'Absolute':
        embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
    else:
        embed.set_footer(text=f'{description}')
    message = f"<@{player_id}>"
    return embed, message


def log_embed(character_name, author, level, milestone_change, milestones_total, milestones_remaining, tier, trial_change, trials, trials_remaining, gold, gold_change, effective_gold, transaction_id, flux, flux_change, tradition_name, tradition_link, template_name, template_link, alternate_reward, total_fame, fame, total_prestige, prestige, source):
    embed = discord.Embed(title=f"{character_name}", description=f"Character Change", color=discord.Colour.blurple())
    embed.set_author(name=f'{author}')
    if milestone_change is not None:
        embed.add_field(name="Milestone Change", value=f'**Level**: {level}, **Milestone Change**: {milestone_change}, **Total Milestones**: {milestones_total}, **Milestones Remaining**: {milestones_remaining}', inline=False)
    if trial_change is not None:
        embed.add_field(name="Trial Change", value=f'**Mythic Tier**: {tier}, **Trial Change**: {trial_change}, **Total Trials**: {trials}, **Trials Remaining**: {trials_remaining}', inline=False)
    if gold_change is not None:
        round(gold, 2)
        round(gold_change, 2)
        round(effective_gold, 2)
        embed.add_field(name="Wealth Changes", value=f'**Gold**: {gold}, **Gold Change**: {gold_change}, **Effective Gold**: {effective_gold} GP **Transaction_ID**: {transaction_id}', inline=False)
    if flux_change is not None:
        embed.add_field(name="Flux Change", value=f'**Flux**: {flux}, **Flux Change**: {flux_change}', inline=False)
    if tradition_name is not None:
        embed.add_field(name="Tradition Change", value=f'**Tradition**: [{tradition_name}]({tradition_link})', inline=False)
    if template_name is not None:
        embed.add_field(name="Template Change", value=f'**Template**: [{template_name}]({template_link})', inline=False)
    if alternate_reward is not None:
        embed.add_field(name="other rewards", value=f'{alternate_reward}', inline=False)
    if fame or prestige is not None:
        total_fame = total_fame if total_fame is not None else "Not Changed"
        total_prestige = total_prestige if total_prestige is not None else "Not Changed"
        fame = fame if fame is not None else "Not Changed"
        prestige = prestige if prestige is not None else "Not Changed"
        embed.add_field(name="Fame and Prestige", value=f' **Total Fame**: {total_fame}, **Received Fame**: {fame} **Total Prestige**: {total_prestige}, **Received Prestige**: {prestige}', inline=False)
    embed.set_footer(text=f"{source}")
    return embed


def level_calculation(guild_id, milestone_total, rewarded, personal_cap):
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    print(milestone_total, rewarded, personal_cap)
    new_milestone_total = milestone_total + rewarded
    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
    max_level = cursor.fetchone()
    cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{new_milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
    current_level = cursor.fetchone()
    int_max_level = int(max_level[0])
    if personal_cap is not None:
        int_max_level = personal_cap if personal_cap < int_max_level else int_max_level
    else:
        int_max_level = int_max_level
    if int_max_level < current_level[0]:
        cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Level = {int_max_level} ORDER BY Minimum_Milestones DESC  LIMIT 1")
        current_level = cursor.fetchone()
        true_level = int_max_level
    else:
        cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{new_milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
        current_level = cursor.fetchone()
        true_level = current_level[0]
    remaining = current_level[1] + current_level[2] - new_milestone_total
    cursor.close()
    db.close()
    return true_level, remaining


def mythic_calculation(guild_id, true_level, trial_total, rewarded):
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    new_trials_total = trial_total + rewarded
    cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Trials <= {new_trials_total} ORDER BY Trials DESC  LIMIT 1")
    current_mythic_information = cursor.fetchone()
    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Cap'")
    max_tier = cursor.fetchone()
    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
    break_point = cursor.fetchone()
    if true_level <= int(break_point[0]):
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
        tier_rate_limit = cursor.fetchone()
    else:
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
        tier_rate_limit = cursor.fetchone()
    rate_limited_tier = floor(true_level / int(tier_rate_limit[0]))
    true_tier = int(max_tier[0]) if current_mythic_information[0] > int(max_tier[0]) else current_mythic_information[0]
    true_tier = true_tier if true_tier <= rate_limited_tier else rate_limited_tier
    cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Tier = {true_tier} ORDER BY Trials DESC  LIMIT 1")
    new_tier_information = cursor.fetchone()
    trials_required = new_tier_information[1] + new_tier_information[2] - trial_total
    cursor.close()
    db.close()
    return true_tier, trials_required


def gold_calculation(true_level, oath, gold, gold_value, gold_value_max, gold_change):
    gold_value_max_total = gold_value_max + gold_change
    print(true_level, oath, gold, gold_value, gold_value_max, gold_change)
    if gold_change > 0:
        if oath == 'Offerings':
            difference = gold_change * .5
            gold_total = gold + difference
            gold_value_total = gold_value + difference
        elif oath == 'Poverty':
            max_gold = 80 * true_level * true_level
            if gold_value > max_gold and gold_change > 0:
                difference = 0
                gold_total = gold
                gold_value_total = gold_value
            elif gold_value > max_gold and gold_change < 0:
                difference = gold_change
                gold_total = gold + difference
                gold_value_total = gold_value + difference
            elif gold_value + gold_change > max_gold:
                difference = max_gold - gold_value
                gold_total = gold + difference
                gold_value_total = gold_value + difference
            else:
                difference = gold_change
                gold_total = gold + difference
                gold_value_total = gold_value + difference
        elif oath == 'Absolute':
            max_gold = true_level * 5
            if gold_value > max_gold and gold_change > 0:
                difference = 0
                gold_total = gold + difference
                gold_value_total = gold_value + difference
            elif gold_value > max_gold and gold_change < 0:
                difference = gold_change
                gold_total = gold + difference
                gold_value_total = gold_value + difference
            elif gold_value + gold_change > max_gold:
                difference = max_gold - gold_value
                gold_total = gold + difference
                gold_value_total = gold_value + difference
            else:
                difference = gold_change
                gold_total = gold + difference
                gold_value_total = gold_value + difference
        else:
            gold_total = gold + gold_change
            gold_value_total = gold_value + gold_change
            difference = gold_change
    else:
        gold_total = gold + gold_change
        gold_value_total = gold_value + gold_change
        difference = gold_change
    gold_total = round(gold_total, 2)
    gold_value_total = round(gold_value_total, 2)
    gold_value_max_total = round(gold_value_max_total, 2)
    difference = round(difference, 2)
    return gold_total, gold_value_total, gold_value_max_total, difference

def ordinal(n):
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd"][n % 10] if n % 10 < 4 else "th"
    return str(n) + suffix



def time_to_minutes(t):
    hours, minutes = map(int, t.split(':'))
    return hours * 60 + minutes



def fetch_timecard_data_from_db(guild_id, player_name, day):
    conn = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = conn.cursor()

    # Fetch time slots for the specific player and day
    cursor.execute(f"SELECT * FROM Player_Timecard WHERE Player_Name = ? AND Day = ?", (player_name, day))
    row = cursor.fetchone()

    conn.close()

    return row


# Function to plot and save the graph as an image
async def create_timecard_plot(guild_id, player_name, day):
    # Time intervals (x-axis)
    time_labels = [
        "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30",
        "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30",
        "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
        "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30",
        "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30"
    ]
    # Get timecard data for the player and day
    row = fetch_timecard_data_from_db(guild_id, player_name, day)
    player_availability = [] # Initialize an empty list to store player availability
    if row:
        player_availability = row[3:]  # Skip the first 3 columns (Player_Name, UTC_Offset, Day)
    else:
        player_availability = [0] * len(time_labels)  # Default to 0 if no data found
    player_availability = [int(x) if str(x).isdigit() else 0 for x in player_availability]

    # Create a plot
    plt.figure(figsize=(10, 6))
    plt.plot(time_labels, player_availability, marker='o', linestyle='-', color='b', label=f'{player_name} Availability')
    plt.fill_between(time_labels, player_availability, color='lightblue', alpha=0.5)

    # Labeling the graph
    plt.title(f"Availability for {player_name} on {day}")
    plt.xlabel("Time of Day")
    plt.ylabel("Availability (1=Available, 0=Not Available)")
    plt.xticks(rotation=90)
    plt.grid(True)

    # Save the plot as an image file
    plt.savefig('C:\\Pathparser\\plots\\timecard_plot.png')  # Ensure the path is correct for your system
    plt.close()

async def character_select_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(f"Select True_Character_Name, Character_Name from Player_Characters where Character_Name LIKE ? OR Nickname LIKE ? LIMIT 5", (f"%{current}%", f"%{current}%"))
    character_list = cursor.fetchall()
    for characters in character_list:
        if current in characters[1]:
            data.append(app_commands.Choice(name=characters[1], value=characters[1]))
    cursor.close()
    db.close()
    return data

async def stg_character_select_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(f"Select True_Character_Name, Character_Name from A_STG_Player_Characters where Character_Name LIKE ? OR Nickname LIKE ? LIMIT 5", (f"%{current}%", f"%{current}%"))
    character_list = cursor.fetchall()
    for characters in character_list:
        if current in characters[1]:
             data.append(app_commands.Choice(name=characters[0], value=characters[0]))
    cursor.close()
    db.close()
    return data

async def own_character_select_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(f"Select True_Character_Name, Character_Name from Player_Characters where Player_Name = ? AND Character_Name LIKE ? OR Player_Name = ? AND Nickname LIKE ?", (interaction.user.name, f"%{current}%", interaction.user.name, f"%{current}%"))
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
    articles_list = [article for article in client.world.articles('f7a60480-ea15-4867-ae03-e9e0c676060a', '9ad3d530-1a42-4e99-9a09-9c4dccddc70a')]
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
    articles_list = [article for article in client.world.articles('f7a60480-ea15-4867-ae03-e9e0c676060a', '9ad3d530-1a42-4e99-9a09-9c4dccddc70a')]
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
    cursor.execute(f"Select Session_ID, Session_Name FROM Sessions WHERE GM_Name = ? AND Session_ID LIKE ?  and Completed_Time is not Null OR GM_Name = ? AND Session_Name like ? and Completed_Time is not Null Limit 15", (interaction.user.name, f"%{current}%", interaction.user.name, f"%{current}%"))
    session_list = cursor.fetchall()
    for test_text in session_list:
        print(current, test_text[1])
        evaluation = True if current in test_text[1] else False
        print(evaluation)
        print(current == str(test_text[0]))
        print(current == test_text[1])
        if current in str(test_text[0]) or str.lower(current) in str.lower(test_text[1]):
            name_result = f"{test_text[0]}: {test_text[1]}"
            data.append(app_commands.Choice(name=name_result, value=test_text[0]))
    cursor.close()
    db.close()
    return data

async def player_session_lookup(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    current = unidecode(str.title(current))
    cursor.execute(f"Select Session_ID, Session_Name Sessions_Archive WHERE Player_Name = ? AND Session_ID LIKE ? OR Player_Name = ? AND Session_Name like ? Limit 20", (interaction.user.name, f"%{current}%", interaction.user.name, f"%{current}%"))
    character_list = cursor.fetchall()
    print(character_list)
    print("WHAT THE FUCK")
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
    cursor.execute(f"Select Fame_Required, Prestige_Cost, Effect, Name, Use_Limit from Store_Fame WHERE Effect LIKE ? Limit 20", (f"%{current}%", ))
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
    cursor.execute(f"Select ID, Masculine_Name, Feminine_Name, Fame, Effect from Store_Title WHERE Masculine_Name LIKE ? OR Feminine_Name LIKE ? Limit 20", (f"%{current}%",f"%{current}%"))
    character_list = cursor.fetchall()
    for characters in character_list:
        if current in characters[1]:
            data.append(app_commands.Choice(name=f"{characters[1]}", value=characters[1]))
    cursor.close()
    db.close()
    return data


# noinspection PyUnresolvedReferences
@bot.tree.command(name="sync_tree", description="Sync commands to server", guild=discord.Object(id=280061170231017472))
async def self(interaction: discord.Interaction):
    fmt = await bot.tree.sync()
    amt = len(fmt)
    await interaction.response.send_message(f"You have synced {amt} your commands")


# noinspection PyUnresolvedReferences
@bot.tree.command(name="database", description="confirms if server database is present")
async def self(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    try:
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
        cursor.fetchone()
        cursor.close()
        db.close()
        await interaction.response.send_message(f"Connection attempt successful!.")
    except sqlite3.OperationalError:
        shutil.copyfile(f"C:/pathparser/pathparser.sqlite", f"C:/pathparser/pathparser_{guild_id}.sqlite")
        await interaction.response.send_message(f"The requested database has been created.")


@kingdom.command()
async def help(ctx: commands.Context):
    """an extremely simple help request for Kingdoms"""
    embed = discord.Embed(title=f"Kingdoms Help", description=f'This is a list of kingdom help commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Create Kingdom**', value=f'This command allows a player to take the first step of kingdom management, creating their kingdom and allowing them to interact with it. NOTE: There is NO encryption. When creating a password do NOT use a personalized password.', inline=False)
    embed.add_field(name=f'**Destroy Kingdom**', value=f'This command will delete all properties of kingdom management, deleting it from the database.', inline=False)
    embed.add_field(name=f'**Modify Kingdom**', value=f'This command allows the kingdom leaders to modify the name of the kingdom.', inline=False)
    embed.add_field(name=f'**Display Kingdom**', value=f'This command displays all kingdoms along with some basic information about them.', inline=False)
    embed.add_field(name=f'**Detail Kingdoms**', value=f'This displays the detailed view of a singular kingdom.', inline=False)
    embed.add_field(name=f'**BP**', value=f'Modifies the build points allocated to a kingdom by a negative or positive value', inline=False)
    embed.add_field(name=f'**SP**', value=f'Modifies the [stabilization points](https://docs.google.com/document/d/1c_W0d-fDgQukteeX8fwNXv3egKD41b6FXtuSPurUoLg/edit?usp=sharing) allocated to a kingdom by a negative or positive value', inline=False)
    embed.add_field(name=f'**Reference Links**', value=f'[Government](https://www.aonprd.com/Rules.aspx?Name=Forms%20of%20Government&Category=Optional%20Kingdom%20Rules),[Build Points](https://www.d20pfsrd.com/gamemastering/other-rules/kingdom-building#TOC-Build-Points), [Decay](https://docs.google.com/document/d/1c_W0d-fDgQukteeX8fwNXv3egKD41b6FXtuSPurUoLg/edit?usp=sharing)')
    await ctx.response.send_message(embed=embed)


@kingdom.command()
async def create(ctx: commands.Context, kingdom: str, password: str, government: str, alignment: str):
    """This creates allows a player to create a new kingdom"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    government = str.replace(str.title(government), ";", "")
    password = str.replace(password, ";", "")
    alignment = str.replace(str.upper(alignment), ";", "")
    guild_id = ctx.guild.id
    author = ctx.user.name
    db = sqlite3.connect(f"pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_validity = cursor.fetchone()
    cursor.execute(f"""SELECT Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = '{alignment}'""", {'Alignment': alignment})
    alignment_validity = cursor.fetchone()
    cursor.execute(f"""SELECT Government FROM AA_Government WHERE Government = '{government}'""", {'Government': government})
    government_validity = cursor.fetchone()
    if alignment_validity is None:
        await ctx.response.send_message(content=f"You have offered an invalid alignment of {alignment}.")
        cursor.close()
        db.close()
        return
    if kingdom_validity is not None:
        status = f"the kingdom of **{kingdom}** Already Exists."
        await ctx.response.send_message(content=status)
        cursor.close()
        db.close()
        return
    if government_validity is None:
        await ctx.response.send_message(content=f"{government} government type does not exist.")
        cursor.close()
        db.close()
        return
    if alignment_validity is not None and kingdom_validity is None and government_validity is not None:
        economy = alignment_validity[1]
        loyalty = alignment_validity[2]
        stability = alignment_validity[3]
        status = f"Congratulations you have made the kingdom of **{kingdom}** a reality"
        await EventCommand.create_kingdom(self, kingdom, password, government, alignment, economy, loyalty, stability, guild_id, author)
        await ctx.response.send_message(content=status)
    cursor.close()
    db.close()


@kingdom.command()
async def destroy(ctx: commands.Context, kingdom: str, password: str):
    """This is a player command to remove a kingdom THEY OWN from play"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"the kingdom which you have elected to make a war crime out of couldn't be found."
        await ctx.response.send_message(content=status)
    if result is not None and result[1] == password:
        status = f"The Kingdom of {kingdom} can no longer be found, whether it be settlements, political figures, or Buildings"
        await EventCommand.destroy_kingdom(self, kingdom, guild_id, author)
        await ctx.response.send_message(content=status)
    else:
        status = f"You have entered an invalid password for this kingdom."
        await ctx.response.send_message(content=status)


@kingdom.command()
async def modify(ctx: commands.Context, old_kingdom: str, new_kingdom: str, old_password: str, new_password: str, new_government: str, new_alignment: str):
    """This is a player command to modify a kingdom THEY OWN."""
    new_kingdom = str.replace(str.title(new_kingdom), ";", "")
    old_kingdom = str.replace(str.title(old_kingdom), ";", "")
    new_government = str.replace(str.title(new_government), ";", "")
    new_alignment = str.replace(str.upper(new_alignment), ";", "")
    new_password = str.replace(new_password, ";", "")
    old_password = str.replace(old_password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{old_kingdom}'""", {'Kingdom': old_kingdom})
    result = cursor.fetchone()
    cursor.execute(f"""SELECT Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = '{new_alignment}'""", {'Alignment': new_alignment})
    alignment_validity = cursor.fetchone()
    cursor.execute(f"""SELECT Government FROM AA_Government WHERE Government = '{new_government}'""", {'Government': new_government})
    government_validity = cursor.fetchone()
    cursor.close()
    db.close()
    if alignment_validity is None:
        await ctx.response.send_message(content=f"{new_alignment} is not a invalid alignment.")
        return
    if government_validity is None:
        await ctx.response.send_message(content=f"Government type of {new_government} does not exist.")
        return
    if result is None:
        status = f"The kingdom of {old_kingdom} which you have attempted to modify was doesn't exist."
        await ctx.response.send_message(status)
    elif old_password != result[1]:
        status = f"H-Have you lied to me slash commander-kun? That password wasn't correct for the kingdom of {kingdom}!"
        await ctx.response.send_message(status)
    elif result is not None and result[1] == old_password:
        await EventCommand.modify_kingdom(self, old_kingdom, new_kingdom, new_password, new_government, new_alignment, guild_id, author)
        status = f"the specified kingdom of {old_kingdom} has been modified with the relevant changes to make it into {new_kingdom}"
        await ctx.response.send_message(status)


@kingdom.command()
async def display(ctx: commands.Context, current_page: int = 1):
    """This displays all kingdoms stored in the database"""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    cursor.execute(f"SELECT COUNT(Kingdom) FROM Kingdoms")
    kingdom_count = cursor.fetchone()
    max_page = math.ceil(kingdom_count[0] / 5)
    if current_page >= max_page:
        current_page = max_page
    low = 1 + ((current_page-1) * 5)
    high = 5 + ((current_page-1) * 5)
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    decay = cursor.fetchone()
    if decay[0]:  # IF THE SERVER HAS DECAY ON
        cursor.execute(f"""SELECT Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"Kingdoms page {current_page}", description=f'This is list of kingdoms', colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f'Kingdom info', value=f'**Kingdom**: {result[0]}, **Govt**: {result[1]} **Alignment**: {result[2]}', inline=False)
            embed.add_field(name=f'Kingdom Control', value=f'**Control DC**: {result[3]}, **BP**: {result[4]}')
            embed.add_field(name=f'Kingdom Stats', value=f'**Hex**: {result[6]} **Pop**: {result[7]} **Cons**: {result[13]}')
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()

                cursor.close()
                db.close()
                return print("timed out")
            else:
                previous_page = current_page
                if reaction.emoji == u"\u23EA":
                    current_page = 1
                    low = 1
                    high = 5
                elif reaction.emoji == u"\u2B05" and current_page > 1:
                    low -= 5
                    high -= 5
                    current_page -= 1
                elif reaction.emoji == u"\u27A1" and current_page < max_page:
                    low += 5
                    high += 5
                    current_page += 1
                elif reaction.emoji == u"\u23E9":
                    current_page = max_page
                    low = ((5 * max_page) - 4)
                    high = (5 * max_page)
                for button in buttons:
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(f"SELECT Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}")
                    edit_pull = cursor.fetchall()
                    embed = discord.Embed(title=f"Kingdoms page {current_page}", description=f'This is list of kingdoms', colour=discord.Colour.blurple())
                    for result in edit_pull:
                        embed.add_field(name=f'Kingdom info',
                                        value=f'**Kingdom**: {result[0]}, **Govt**: {result[1]} **Alignment**: {result[2]}',
                                        inline=False)
                        embed.add_field(name=f'Kingdom Control',
                                        value=f'**Control DC**: {result[3]}, **BP**: {result[4]}',
                                        inline=True)
                        embed.add_field(name=f'Kingdom Stats',
                                        value=f'**Hex**: {result[6]} **Pop**: {result[7]} **Cons**: {result[13]}',
                                        inline=True)
                    await msg.edit(embed=embed)
    if not decay[0]:  # IF THE SERVER HAS DECAY OFF
        cursor.execute(f"""SELECT Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"Kingdoms page {current_page}", description=f'This is list of kingdoms', colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f'Kingdom info', value=f'**Kingdom**: {result[0]}, **Govt**: {result[1]} **Alignment**: {result[2]}', inline=False)
            embed.add_field(name=f'Kingdom Control', value=f'**Control DC**: {result[3]}, **BP**: {result[4]}, **SP**: {result[5]}')
            embed.add_field(name=f'Kingdom Stats', value=f'**Hex**: {result[6]} **Pop**: {result[7]} **Cons**: {result[13]}')
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()

                cursor.close()
                db.close()
                return print("timed out")
            else:
                previous_page = current_page
                if reaction.emoji == u"\u23EA":
                    current_page = 1
                    low = 1
                    high = 5
                elif reaction.emoji == u"\u2B05" and current_page > 1:
                    low -= 5
                    high -= 5
                    current_page -= 1
                elif reaction.emoji == u"\u27A1" and current_page < max_page:
                    low += 5
                    high += 5
                    current_page += 1
                elif reaction.emoji == u"\u23E9":
                    current_page = max_page
                    low = ((5 * max_page) - 4)
                    high = (5 * max_page)
                for button in buttons:
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(f"SELECT Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}")
                    edit_pull = cursor.fetchall()
                    embed = discord.Embed(title=f"Kingdoms page {current_page}", description=f'This is list of kingdoms', colour=discord.Colour.blurple())
                    for result in edit_pull:
                        embed.add_field(name=f'Kingdom info',
                                        value=f'**Kingdom**: {result[0]}, **Govt**: {result[1]} **Alignment**: {result[2]}',
                                        inline=False)
                        embed.add_field(name=f'Kingdom Control',
                                        value=f'**Control DC**: {result[3]}, **BP**: {result[4]}, **SP**: {result[5]}',
                                        inline=True)
                        embed.add_field(name=f'Kingdom Stats',
                                        value=f'**Hex**: {result[6]} **Pop**: {result[7]} **Cons**: {result[13]}',
                                        inline=True)
                    await msg.edit(embed=embed)
"""This is a shop"""


@kingdom.command()
async def detail(ctx: commands.Context, kingdom: str, custom_stats: bool = False):
    """This displays the detailed information of a specific kingdom"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if custom_stats:
        cursor.execute(
            f"SELECT Control_DC, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms_Custom where Kingdom = '{kingdom}'")
        kingdom_info = cursor.fetchone()
        if kingdom_info is None:
            await ctx.response.send_message(f'The kingdom of {kingdom_info} could not be found.')
        if kingdom_info is not None:
            embed = discord.Embed(title=f"Kingdom of {kingdom}", description=f'Here is the full view of this Custom Information for this kingdom', colour=discord.Colour.blurple())
            embed.add_field(name=f'Control_DC', value=f'{kingdom_info[0]}')
            embed.add_field(name=f'Economy', value=f'{kingdom_info[1]}')
            embed.add_field(name=f'Loyalty', value=f'{kingdom_info[2]}')
            embed.add_field(name=f'Stability', value=f'{kingdom_info[3]}')
            embed.add_field(name=f'Fame', value=f'{kingdom_info[4]}')
            embed.add_field(name=f'Unrest', value=f'{kingdom_info[5]}')
            embed.add_field(name=f'Consumption', value=f'{kingdom_info[6]}')
            await ctx.response.send_message(embed=embed)
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    decay = cursor.fetchone()
    if decay[0]:
        if not custom_stats:
            cursor.execute(f"""SELECT Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
            kingdom_info = cursor.fetchone()
            if kingdom_info is None:
                await ctx.response.send_message(f'The kingdom of {kingdom} could not be found.')
            if kingdom_info is not None:
                embed = discord.Embed(title=f"Kingdom of {kingdom}", description=f'Here is the full view of this kingdom', colour=discord.Colour.blurple())
                embed.add_field(name=f'Government', value=f'{kingdom_info[0]}')
                embed.add_field(name=f'Alignment', value=f'{kingdom_info[1]}')
                embed.add_field(name=f'Control_DC', value=f'{kingdom_info[2]}')
                embed.add_field(name=f'Build_Points', value=f'{kingdom_info[3]}')
                embed.add_field(name=f'Stabilization_Points', value=f'{kingdom_info[4]}')
                embed.add_field(name=f'Size', value=f'{kingdom_info[5]}', inline=False)
                embed.add_field(name=f'Population', value=f'{kingdom_info[6]}')
                embed.add_field(name=f'Economy', value=f'{kingdom_info[7]}')
                embed.add_field(name=f'Loyalty', value=f'{kingdom_info[8]}')
                embed.add_field(name=f'Stability', value=f'{kingdom_info[9]}')
                embed.add_field(name=f'Fame', value=f'{kingdom_info[10]}')
                embed.add_field(name=f'Unrest', value=f'{kingdom_info[11]}')
                embed.add_field(name=f'Consumption', value=f'{kingdom_info[12]}')
                await ctx.response.send_message(embed=embed)
    if not decay[0]:
        if not custom_stats:
            cursor.execute(f"""SELECT Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
            kingdom_info = cursor.fetchone()
            if kingdom_info is None:
                await ctx.response.send_message(f'The kingdom of {kingdom} could not be found.')
            if kingdom_info is not None:
                embed = discord.Embed(title=f"Kingdom of {kingdom}", description=f'Here is the full view of this kingdom', colour=discord.Colour.blurple())
                embed.add_field(name=f'Government', value=f'{kingdom_info[0]}')
                embed.add_field(name=f'Alignment', value=f'{kingdom_info[1]}')
                embed.add_field(name=f'Control_DC', value=f'{kingdom_info[2]}')
                embed.add_field(name=f'Build_Points', value=f'{kingdom_info[3]}')
                embed.add_field(name=f'Size', value=f'{kingdom_info[5]}', inline=False)
                embed.add_field(name=f'Population', value=f'{kingdom_info[6]}')
                embed.add_field(name=f'Economy', value=f'{kingdom_info[7]}')
                embed.add_field(name=f'Loyalty', value=f'{kingdom_info[8]}')
                embed.add_field(name=f'Stability', value=f'{kingdom_info[9]}')
                embed.add_field(name=f'Fame', value=f'{kingdom_info[10]}')
                embed.add_field(name=f'Unrest', value=f'{kingdom_info[11]}')
                embed.add_field(name=f'Consumption', value=f'{kingdom_info[12]}')
                await ctx.response.send_message(embed=embed)

    cursor.close()
    db.close()
"""THIS CALLS FOR A SINGULAR KINGDOM OR IT'S CUSTOM INFORMATION"""


# noinspection PyUnresolvedReferences
@kingdom.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def bp(interaction: discord.Interaction, kingdom: str, password: str, character_name: str, amount: int):
    """This modifies the number of build points in a kingdom"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    password = str.replace(password, ";", "")
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom, Password, Build_Points FROM Kingdoms where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
    result = cursor.fetchone()
    sql = f"""Select True_Character_Name, Gold from Player_Characters where Player_Name = ? and Character_Name = ? OR  Player_Name = ? and Nickname = ?"""
    val = (author, character_name, author, character_name)
    cursor.execute(sql, val)
    character_info = cursor.fetchone()
    if character_info is None:
        await interaction.response.send_message(f"Falsehoods! the Character of {character_name} either doesn't exist or belong to {author}!")
    elif character_info is not None:
        cost = amount * 4000
        gold_value = character_info[1] - cost
        if gold_value < 0:
            await interaction.response.send_message(f"Sell yourself into slavery if you want to buy these points! We don't accept debt at this shop!")
        if gold_value >= 0:
            if result is None:
                await interaction.response.send_message(f"Bollocks! The kingdom of {kingdom} was not a valid kingdom to give building points to!")
                return
            if result[1] != password:
                await interaction.response.send_message(f"The password provided for the kingdom of {kingdom} was inaccurate!!")
            if result is not None and result[1] == password:
                build_points = result[2] + amount
                if build_points < 0:
                    await interaction.response.send_message(f"Impossible! the kingdom of {kingdom} would have {build_points} remaining build points and go into anarchy!!")
                if build_points >= 0:
                    await EventCommand.adjust_build_points(self, kingdom, amount, guild_id, character_info[0], author)
                    await interaction.response.send_message(f"the kingdom of {kingdom} has been adjusted by {amount} build points and has a new value of {build_points}! {character_info[0]} has been charged {cost} GP leaving {gold_value} remaining!")
"""We can make this ALL settlements for that kingdom, or a specific settlement"""


# noinspection PyUnresolvedReferences
@kingdom.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def sp(interaction: discord.Interaction, kingdom: str, password: str, character_name: str, amount: int):
    """This modifies the Stability Points for a kingdom"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    password = str.replace(password, ";", "")
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    decay = cursor.fetchone()
    if decay[0]:  # IF THE SERVER HAS DECAY ON
        cursor.execute(f"""SELECT Kingdom, Password, Stabilization_Points FROM Kingdoms where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
        result = cursor.fetchone()
        sql = f"""Select True_Character_Name, Gold from Player_Characters where Player_Name = ? and  Character_Name = ? or  Player_Name = ? and Nickname = ?"""
        val = (author, character_name, author, character_name)
        cursor.execute(sql, val)
        character_info = cursor.fetchone()
        cost = amount * 4000
        gold_value = character_info[1] - cost
        if character_info is None:
            await interaction.response.send_message(f"Falsehoods! the Character of {character_name} either doesn't exist or belong to {author}!")
        elif character_info is not None:
            if gold_value < 0:
                await interaction.response.send_message(f"Sell yourself into slavery if you want to buy these points! We don't accept debt at this shop!")
            elif gold_value >= 0:
                if result is None:
                    await interaction.response.send_message(f"You fool! The kingdom of {kingdom} a valid kingdom to give building points to!")
                    return
                if result[1] != password:
                    await interaction.response.send_message(f"The password provided for the kingdom of {kingdom} was inaccurate!!")
                if result is not None and result[1] == password:
                    stabilization_points = result[2] + amount
                    if stabilization_points < 0:
                        await interaction.response.send_message(f"Impossible! the kingdom of {kingdom} would have {stabilization_points} remaining stabilization_points and go into anarchy!!")
                    if stabilization_points >= 0:
                        await EventCommand.adjust_stabilization_points(self, kingdom, amount, guild_id, author, character_info[0])
                        await interaction.response.send_message(f"The kingdom of {kingdom} has been adjusted by {amount} Stabilization Points and has a new value of {stabilization_points}! {character_info[0]} has been charged {cost} GP leaving {gold_value} remaining!")
        if not decay[0]:
            await interaction.response.send_message(f"this server does not have decay enabled!")
"""We can make this ALL settlements for that kingdom, or a specific settlement"""


@overseer.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Overseer Help", description=f'This is a list of Overseer help commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**blueprint_add**', value=f'The command for an overseer to create a new blueprint for players to use..', inline=False)
    embed.add_field(name=f'**blueprint_remove**', value=f'This command removes blueprints from player usage.', inline=False)
    embed.add_field(name=f'**blueprint_modify**', value=f'This command modifies a blueprint that is already in use.', inline=False)
    embed.add_field(name=f'**kingdom_modifiers**', value=f'This command adjusts the custom modifiers associated with a kingdom.', inline=False)
    embed.add_field(name=f'**settlement_modifiers**', value=f'This command adjusts the custom modifiers associated with a settlement.', inline=False)
    embed.add_field(name=f'**settlement_decay**', value=f'This command modifies the multiplier for stabilization points a settlement requires in order to build.', inline=False)
    embed.add_field(name=f'**improvement_add**', value=f'This command adds a new hex improvement for players to build', inline=False)
    embed.add_field(name=f'**improvement_remove**', value=f'This command removes hex improvements from options players can build.', inline=False)
    embed.add_field(name=f'**improvement_modify**', value=f'This command modifies hex improvements that are available to build, or have been built', inline=False)
    embed.add_field(name=f'**kingdom_tables_rebalance**', value=f'Forced the kingdom and settlement tables to rebalance.', inline=False)
    await ctx.response.send_message(embed=embed)


@overseer.command()
async def blueprint_add(ctx: commands.Context, building: str, build_points: int, lots: int, economy: int, loyalty: int, stability: int, fame: int, unrest: int, corruption: int, crime: int, productivity: int, law: int, lore: int, society: int, danger: int, defence: int, base_value: int, spell_casting: int, supply: int, settlement_limit: int, district_limit: int, description: str):
    """This adds a new blueprint for players to build with"""
    building = str.replace(str.title(building), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT building FROM Buildings_Blueprints where building = '{building}' LIMIT 1;""", {'building': building})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"Congratulations you have allowed the construction of **{building}**"
        await EventCommand.create_blueprint(self, building, build_points, lots, economy, loyalty, stability, fame, unrest, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spell_casting, supply, settlement_limit, district_limit, description, guild_id, author)
        await ctx.response.send_message(status)
    if result is not None:
        status = f"you have already allowed the construction of **{building}**"
        await ctx.response.send_message(status)


@overseer.command()
async def blueprint_remove(ctx: commands.Context, building: str):
    """This removes a blueprint from play and refunds some build points used."""
    building = str.replace(str.title(building), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Building FROM Buildings_Blueprints WHERE Building = '{building}'""", {'building': building})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"You have removed the possibility of constructing {building} for all future kingdoms."
        await ctx.response.send_message(status)
    if result is not None:
        status = f"You have done the YEETETH of this particular building which is {building}."
        await EventCommand.remove_blueprint(self, building, guild_id, author)
        await ctx.response.send_message(status)


@overseer.command()
async def blueprint_modify(ctx: commands.Context, building: str, build_points: int, lots: int, economy: int, loyalty: int, stability: int, fame: int, unrest: int, corruption: int, crime: int, productivity: int, law: int, lore: int, society: int, danger: int, defence: int, base_value: int, spellcasting: int, supply: int, settlement_limit: int, district_limit: int, description: str):
    """this modifies a blueprint that is currently in play"""
    building = str.replace(str.title(building), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Building FROM Buildings_Blueprints WHERE Building = '{building}'""", {'Building': building})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"You, like a false god have falsely instructed me to modify this nonexistent {building}."
        await ctx.response.send_message(status)
    if result is not None:
        status = f"The blueprint of {building} has been modified for all times built, and in the records!"
        await EventCommand.modify_blueprint(self, building, build_points, lots, economy, loyalty, stability, fame, unrest, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting, supply, settlement_limit, district_limit, description, guild_id, author)
        await ctx.response.send_message(status)


@overseer.command()
async def kingdom_modifiers(ctx: commands.Context, kingdom: str, control_dc: int, economy: int, loyalty: int, stability: int, fame: int, unrest: int, consumption: int):
    """This will set the custom kingdom values as a new value. it does NOT handle addition or subtraction."""
    kingdom = str.title(kingdom)
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"the kingdom of {kingdom} which you have attempted to set new modifiers for couldn't be found."
        await ctx.response.send_message(status)
    if result is not None:
        status = f"The kingdom of {kingdom} which you have set new modifiers for has been adjusted"
        await EventCommand.customize_kingdom_modifiers(self, kingdom, control_dc, economy, loyalty, stability, fame, unrest, consumption, guild_id, author)
        await ctx.response.send_message(status)


@overseer.command()
async def settlement_modifiers(ctx: commands.Context, kingdom: str, settlement: str, corruption: int, crime: int, productivity: int, law: int, lore: int, society: int, danger: int, defence: int, base_value: int, spellcasting: int, supply: int):
    """Sets new values for a settlement."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Settlement FROM Settlements WHERE Settlement = '{settlement}' AND Kingdom = '{kingdom}'""")
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"you cannot apply custom modifiers if the settlement of {settlement} doesn't exist for the kingdom of {kingdom}!"
        await ctx.response.send_message(status)
    if result is not None:
        status = f"You have modified the settlement of {settlement} congratulations!"
        await ctx.response.send_message(status)
        await EventCommand.custom_settlement_modifiers(self, kingdom, settlement, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting, supply, guild_id, author)


@overseer.command()
async def settlement_decay(ctx: commands.Context, kingdom: str, settlement: str, decay: int):
    """This will set the custom decay of a settlement."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    server_decay = cursor.fetchone()
    if server_decay[0]:  # IF THE SERVER HAS DECAY ON
        cursor = db.cursor()
        cursor.execute(f"""SELECT Kingdom FROM Settlements where Kingdom = '{kingdom}' AND Settlement = '{settlement}'""", {'Kingdom': kingdom, 'Settlement': settlement})
        result = cursor.fetchone()
        if result is None:
            await ctx.response.send_message(f"You have failed to specify a valid settlement to adjust the decay!!")
            return
        if result is not None:
            await EventCommand.settlement_decay_set(self, kingdom, settlement, decay, guild_id, author)
            await ctx.response.send_message(f"The settlement of {settlement} within the kingdom of {kingdom} has had it's decay set to {decay}!")
    if not server_decay[0]:
        await ctx.response.send_message(f"Decay is not enabled in this server!")


@overseer.command()
async def improvement_add(ctx: commands.Context, improvement: str, build_points: int, road_multiplier: int, economy: int, loyalty: int, stability: int, unrest: int, consumption: int, defence: int, taxation: int, cavernous: bool, coastline: bool, desert: bool, forest: bool, hills: bool, jungle: bool, marsh: bool, mountain: bool, plains: bool, water: bool):
    """This will add a new custom improvement for the players to build for hexes"""
    improvement = str.replace(str.title(improvement), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Improvement from Hexes_Improvements where Improvement = '{improvement}'""", {'Improvement': improvement})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        await EventCommand.add_hex_improvements(self, improvement, build_points, road_multiplier, economy, loyalty, stability, unrest, consumption, defence, taxation, cavernous, coastline, desert, forest, hills, jungle, marsh, mountain, plains, water, guild_id, author)
        status = f"You have allowed the creation the new hex improvement: {improvement}!"
        await ctx.response.send_message(status)
    if result is not None:
        status = f"You cannot add a improvement with the same name of {improvement}!"
        await ctx.response.send_message(status)


@overseer.command()
async def improvement_remove(ctx: commands.Context, improvement: str):
    """This will remove a custom improvement from play for players and delete historical instances of it."""
    improvement = str.replace(str.title(improvement), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Improvement from Hexes_Improvements where Improvement = '{improvement}'""", {'Improvement': improvement})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is not None:
        await EventCommand.remove_hex_improvement(self, improvement, guild_id, author)
        status = f"You have removed {improvement} from the list of available improvements."
        await ctx.response.send_message(status)
    if result is None:
        status = f"You cannot remove a thing which doesn't exist!!! or can you? {improvement} was not found."
        await ctx.response.send_message(status)


@overseer.command()
async def improvement_modify(ctx: commands.Context, old_improvement: str, new_improvement: str, new_build_points: int, new_road_multiplier: int, new_economy: int, new_loyalty: int, new_stability: int, new_unrest: int, new_consumption: bool, new_defence: int, new_taxation: int, new_cavernous: bool, new_coastline: bool, new_desert: bool, new_forest: bool, new_hills: bool, new_jungle: bool, new_marsh: bool, new_mountains: bool, new_plains: bool, new_water: bool):
    """This is an overseer command that modifies an existing improvement."""
    new_improvement = str.replace(str.title(new_improvement), ";", "")
    old_improvement = str.replace(str.title(old_improvement), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Improvement from Hexes_Improvements where Improvement = '{new_improvement}'""", {'Improvement': new_improvement})
    result1 = cursor.fetchone()
    cursor.execute(f"""SELECT Improvement from Hexes_Improvements where Improvement = '{old_improvement}'""", {'Improvement': old_improvement})
    result2 = cursor.fetchone()
    cursor.close()
    db.close()
    if result1 is None:
        status = f"My master, You cannot alter that which doesn't exist. {old_improvement} doesn't exist."
        await ctx.response.send_message(status)
    if result1 is not None:
        if result2 is None:
            status = f"You have made this improvement into something new... something different. {new_improvement} has been altered for all settlements."
            await ctx.response.send_message(status)
            await EventCommand.modify_hex_improvement(self, old_improvement, new_improvement, new_build_points, new_road_multiplier, new_economy, new_loyalty, new_stability, new_unrest, new_consumption, new_defence, new_taxation, new_cavernous, new_coastline, new_desert, new_forest, new_hills, new_jungle, new_marsh, new_mountains, new_plains, new_water, guild_id, author)
        elif result1[0] == result2[0]:
            await EventCommand.modify_hex_improvement(self, old_improvement, new_improvement, new_build_points, new_road_multiplier, new_economy, new_loyalty, new_stability, new_unrest, new_consumption, new_defence, new_taxation, new_cavernous, new_coastline, new_desert, new_forest, new_hills, new_jungle, new_marsh, new_mountains, new_plains, new_water, guild_id, author)
            status = f"You have kept the name the same for this building. The stats of {new_improvement} have been altered.."
            await ctx.response.send_message(status)
        elif result2 is not None:
            status = f"for shame! {new_improvement} already exists! You cannot change something to be the same as another! (no seriously, it breaks shit)"
            await ctx.response.send_message(status)


@overseer.command()
async def kingdom_tables_rebalance(ctx: commands.Context):
    """This will rebalance the existing tables"""
    guild_id = ctx.guild_id
    author = ctx.user.name
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    shutil.copyfile(f"C:/pathparser/pathparser_{guild_id}.sqlite", f"C:/pathparser/pathparser_{guild_id}_{time}.sqlite")
    await EventCommand.balance_tables(self, guild_id, author)
    status = f"TABLE UPDATE HAS BEEN COMPLETED"
    await ctx.response.send_message(status)


@admin.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Admin Help", description=f'This is a list of Admin help commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Character Commands**', value=f'**/Character_Milestones**: Modifies the milestones associated with a character. \r\n' +
                    f'**/admin character_trials**: Modifies the trials associated with a character. \r\n' +
                    f'**/admin gold_adjust**: Modifies the gold that a character has. \r\n ' +
                    f'**/admin Flux_Adjust**: Modifies the flux that a character has. \r\n ' +
                    f'**/admin customize**: Apply a Tradition or Template for a character \r\n' +
                    f'**/admin manage**: Accept or reject a player registration attempt, or clean out historical ones. \r\n ' +
                    f'**/admin undo_transaction**: undo a player transaction',inline=False)
    embed.add_field(name=f'**Database Commands**', value=f'**/settings_display**: Display the various Administrative Defined Settings\r\n' +
                    f'**/admin settings_define**: Define an Administrative Setting.\r\n' +
                    f'**/admin level_cap**: Set a new level cap and set all player characters levels as appropriate.\r\n' +
                    f'**/admin Tier_cap**: Set a new tier cap and set all player characters levels as appropriate.\r\n' +
                    f'**/admin level_range**: Define a role and range for a level range.\r\n' +
                    f'**/admin reset_database**: Reset the Server Database to Defaults.\r\n' +
                    f'**/admin clean_playerbase**: Clean out a or all inactive player characters from player characters and gold history and session history.', inline=False)
    embed.add_field(name=f"**Utility Commands**", value=f'**/admin session_adjust**: alter the reward from a session.\r\n' +
                    f'**/admin ubb_inventory**: Display the inventory of a user in order to find information.', inline=False)
    embed.add_field(name=f"**Fame Commands**", value=f'**/admin fame_store**: Add, edit, or remove items from the fame store.\r\n' +
                    f'**/admin title_store**: Add, edit, or remove items from the title store.\r\n', inline=False)
    await ctx.response.send_message(embed=embed)



@admin.command(name="character_milestones", description="commands for adding or removing milestones")
@app_commands.autocomplete(character_name=character_select_autocompletion)
@app_commands.describe(job='What kind of job you are adding')
@app_commands.choices(job=[discord.app_commands.Choice(name='Easy', value=1), discord.app_commands.Choice(name='Medium', value=2), discord.app_commands.Choice(name='Hard', value=3), discord.app_commands.Choice(name='Deadly', value=4), discord.app_commands.Choice(name='None', value=5)])
@app_commands.describe(level="The character level for the adjustment: Default at 0 to use current level.")
async def character_milestones(ctx: commands.Context, character_name: str, amount: int, job: discord.app_commands.Choice[int], level: typing.Optional[int], misc_milestones: int = 0):
    """Adjusts the milestone number a PC has."""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    if job == 1:
        job = 1
    else:
        job = job.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if job == 1:
        job_name = 'Easy'
    elif job == 2:
        job_name = 'Medium'
    elif job == 3:
        job_name = 'Hard'
    elif job == 4:
        job_name = 'Deadly'
    else:
        job_name = 'None'
    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name, character_name))
    player_info = cursor.fetchone()
    if player_info is None:
        await ctx.response.send_message(f"{author} does not have {character_name} registered to their account.")
    if player_info is not None:
        if amount == 0 and misc_milestones == 0:
            await ctx.response.send_message("No Change in Milestones!", ephemeral=True)
        if job_name == 'None' and misc_milestones == 0:
            await ctx.response.send_message("No Change in Milestones!", ephemeral=True)

        else:
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
            max_level = cursor.fetchone()
            int_max_level = int(max_level[0])
            if player_info[29] is not None:
                int_max_level = player_info[29] if player_info[29] < int_max_level else int_max_level
            if job_name != 'None':
                character_level = player_info[7] if level is None else level
                cursor.execute(f"SELECT {job_name} from AA_Milestones where level = {character_level}")
                milestone_info = cursor.fetchone()
                milestone_total = (milestone_info[0] * amount) + misc_milestones + player_info[9]
                adjust_milestones = (milestone_info[0] * amount) + misc_milestones
            else:
                milestone_total = player_info[9] + misc_milestones
                adjust_milestones = misc_milestones
            cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
            current_level = cursor.fetchone()

            if current_level[0] < int_max_level:
                character_level = current_level[0]
                remaining = current_level[1] + current_level[2] - milestone_total
            else:
                character_level = int_max_level
                cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE level = '{character_level}'")
                current_level = cursor.fetchone()
                remaining = current_level[1] + current_level[2] - milestone_total
            if current_level is None:
                await ctx.response.send_message(f"Comrade, one cannot degrade this character: {character_name} past level 3, please train them to  best level up in the future!")
            else:
                await EventCommand.adjust_milestones(self, character_name, milestone_total, remaining, character_level, guild_id, author)
                if character_level != player_info[1]:
                    cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = '{player_info[7]}'")
                    level_range = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Desc")
                    level_range_max = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Asc")
                    level_range_min = cursor.fetchone()
                    cursor.execute(f"Select True_Character_Name from Player_Characters WHERE Player_Name = '{player_info[0]}' AND level >= {level_range_min[0]} AND level <= {level_range_max[0]}")
                    level_range_characters = cursor.fetchone()
                    member = await guild.fetch_member(player_info[1])
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    accepted_bio_channel = cursor.fetchone()
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                    character_log_channel_id = cursor.fetchone()
                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], character_level, player_info[8], milestone_total, remaining, player_info[11], player_info[12], player_info[13], player_info[14], player_info[16] , player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                    bio_message = await bio_channel.fetch_message(player_info[24])
                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                    source = f"admin adjusted milestones by {adjust_milestones} for {character_name}"
                    logging_embed = log_embed(player_info[2], author, character_level, adjust_milestones, milestone_total, remaining, None, None, None, None, None, None, None, None, None, None, None, None,None, None, None, None, None, None, None, source)
                    logging_thread = guild.get_thread(player_info[25])
                    await logging_thread.send(embed=logging_embed)
                    if level_range_characters is None:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {character_level}")
                        new_level_range = cursor.fetchone()
                        role1 = guild.get_role(level_range[2])
                        role2 = guild.get_role(new_level_range[2])
                        await member.remove_roles(role1)
                        await member.add_roles(role2)
                    else:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {character_level}")
                        new_level_range = cursor.fetchone()
                        role2 = guild.get_role(new_level_range[2])
                        await member.add_roles(role2)
                    await ctx.response.send_message(f"{ctx.user.name} has adjusted {character_name}'s milestones by {adjust_milestones}, they are now level {current_level[0]} and require {remaining} milestones to reach their next level up!")
                if player_info[1] == current_level[0]:
                    await ctx.response.send_message(f"{ctx.user.name} has adjusted {character_name}'s milestones by {adjust_milestones}, they require {remaining} milestones to level up!")
    cursor.close()
    db.close()


@admin.command(name="character_trials", description="commands for adding or removing trials")
@app_commands.autocomplete(character_name=character_select_autocompletion)
async def character_trials(ctx: commands.Context, character_name: str, amount: int):
    """Adjust the number of Mythic Trials a character possesses"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    guild = ctx.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name,character_name))
    player_info = cursor.fetchone()
    if amount == 0:
        await ctx.response.send_message(f"No changes to trial total required.")
    else:
        if player_info is None:
            await ctx.response.send_message(f"{ctx.user.name} does not have {character_name} registered to their account.")
        else:
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Cap'")
            max_tier = cursor.fetchone()
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
            break_point = cursor.fetchone()
            if player_info[7] <= int(break_point[0]):
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
                tier_rate_limit = cursor.fetchone()
            else:
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
                tier_rate_limit = cursor.fetchone()
            rate_limited_tier = floor(player_info[7] / int(tier_rate_limit[0]))
            tier_max = rate_limited_tier if rate_limited_tier <= max_tier[0] else max_tier[0]
            total_trials = player_info[11] + amount
            cursor.execute(f"SELECT Tier, Trials, Trials_Required FROM AA_Trials where Trials <= {total_trials} ORDER BY Trials Desc LIMIT 1")
            trial_info = cursor.fetchone()
            if trial_info is None:
                await ctx.response.send_message(f"{character_name} cannot be made any more menial! Please comrade, encourage them to elevate themselves in the future!")
            elif trial_info[0] <= tier_max or amount < 0:
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16] , player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"admin adjusted trials by {amount} for {character_name}"
                logging_embed = log_embed(player_info[2], author, None, None, None, None, trial_info[0], amount, total_trials, trial_info[1] + trial_info[2] - total_trials, None, None, None, None, None, None, None, None,None, None, None, None, None, None, None, source)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await EventCommand.adjust_trials(self, character_name, total_trials, guild_id, author)
                if player_info[8] != trial_info[0]:
                    remaining = trial_info[1] + trial_info[2] - total_trials
                    await ctx.response.send_message(f"{ctx.user.name} has adjusted {character_name}'s trials by {amount}, reaching a tier of {trial_info[0]} with {remaining} trials to increase their tier.")
                if player_info[8] == trial_info[0]:
                    remaining = trial_info[1] + trial_info[2] - total_trials
                    await ctx.response.send_message(f"{ctx.user.name} has adjusted {character_name}'s trials by {amount} with {remaining} trials to increase their tier")
            else:
                await ctx.response.send_message(f"{character_name} is at the max tier cap for the server or his level!")
        cursor.close()
        db.close()


@admin.command()
@app_commands.autocomplete(character_name=character_select_autocompletion)
async def gold_adjust(ctx: commands.Context, character_name: str, amount: typing.Optional[float], effective_gold: typing.Optional[float], lifetime_gold: typing.Optional[float], reason: str):
    """Adjust the gold a PC has"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    reason = str.replace(reason, ";", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount is None and effective_gold is None and lifetime_gold is None:
        await ctx.response.send_message(f"BRUH, if you don't intend to change anything why change at all?", ephemeral=True)
    else:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR Nickname = ?",(character_name, character_name))
        player_info = cursor.fetchone()
        print(player_info[4])
        if player_info is None:
            await ctx.response.send_message(f"There is no character with the name or nickname of {character_name}.")
        else:
            amount = 0 if amount is None else amount
            gold_info = gold_calculation(player_info[7], player_info[6], player_info[13], player_info[14], player_info[15], amount)
            lifetime_gold_change = lifetime_gold if lifetime_gold is not None else amount
            effective_gold_change = effective_gold if effective_gold is not None else gold_info[3]
            await EventCommand.gold_change(self, guild_id, author, author_id, player_info[3], gold_info[3], effective_gold_change, lifetime_gold_change, reason, 'Admin Gold Adjust')
            cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
            transaction_id = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + gold_info[3], player_info[14] + effective_gold_change, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"admin adjusted gold by {amount} for {character_name}"
            logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, player_info[13] + gold_info[3], gold_info[3], player_info[14] + effective_gold_change, transaction_id[0], None, None, None, None, None, None, None, None, None, None, None, source)
            logging_thread = guild.get_thread(player_info[25])
            await logging_thread.send(embed=logging_embed)
            embed = discord.Embed(title=f"Admin Gold Change", description=f'Gold Adjustment Transaction', colour=discord.Colour.blurple())
            embed.add_field(name=f'**Adjustments**', value=f'Gold change: {gold_info[3]}, Effective Gold Change: {effective_gold_change}, Lifetime Wealth Change: {lifetime_gold_change}', inline=False)
            embed.add_field(name=f"**Totals**", value=f"Gold Total: {player_info[13] + gold_info[3]}, Effective Gold Total: {player_info[14] + effective_gold_change}, Lifetime Wealth Total: {player_info[15] + lifetime_gold_change}", inline=False)
            embed.set_footer(text=f"Transaction ID: {transaction_id[0]}")
            await ctx.response.send_message(embed=embed, ephemeral=True)
    cursor.close()
    db.close()


@admin.command()
async def undo_transaction(ctx: commands.Context, transaction_id: int):
    """Undo a transaction performed by a PC"""
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    guild = ctx.guild
    author = ctx.user.name
    cursor.execute(f"Select Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_value_max FROM A_Audit_Gold WHERE Transaction_ID = {transaction_id}")
    transaction_info = cursor.fetchone()
    if transaction_info is not None:
        embed = discord.Embed(title=f"Undoing Transaction: {transaction_id}", description=f'Undoing a transaction', colour=discord.Colour.red())
        """Help commands for the associated tree"""
        mentions = f"The Below Transaction has been cancelled for {transaction_info[2]}, <@{transaction_info[1]}>"
        gold = transaction_info[3] * -1
        effective_gold = transaction_info[4] * -1
        max_effective_gold = transaction_info[5] * -1
        embed.add_field(name=f"**{transaction_info[2]}'s Transaction Info:**", value=f'**Gold:** {transaction_info[3]} GP, **Effective Gold**: {transaction_info[4]} GP, **Lifetime Gold**: {transaction_info[5]}.', inline=False)
        cursor.execute(f"Select Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_value_max, Transaction_ID FROM A_Audit_Gold WHERE Related_Transaction_ID = {transaction_id}")
        related_transaction_info = cursor.fetchone()
        await EventCommand.undo_transaction(self, guild_id, transaction_id, gold, effective_gold, max_effective_gold, transaction_info[2], transaction_info[0])
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
        accepted_bio_channel = cursor.fetchone()
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
        character_log_channel_id = cursor.fetchone()
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?",(transaction_info[2],))
        player_info = cursor.fetchone()
        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
        bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + gold, player_info[14] + effective_gold, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
        bio_message = await bio_channel.fetch_message(player_info[24])
        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
        source = f"admin undid transaction {transaction_id}"
        logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, player_info[13] + gold, gold, player_info[14] + effective_gold, transaction_id, None, None, None, None, None, None, None, None, None, None, None, source)
        logging_thread = guild.get_thread(player_info[25])
        await logging_thread.send(embed=logging_embed)
        if related_transaction_info is not None:
            mentions = f"and for {transaction_info[2]}, <@{transaction_info[1]}>!"
            """Help commands for the associated tree"""
            gold = related_transaction_info[3] * -1
            effective_gold = related_transaction_info[4] * -1
            max_effective_gold = related_transaction_info[5] * -1
            cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?",(related_transaction_info[2],))
            player_info = cursor.fetchone()
            embed.add_field(name=f"**{related_transaction_info[2]}'s Transaction Info:**", value=f'**Gold:** {related_transaction_info[3]} GP, **Effective Gold**: {related_transaction_info[4]} GP, **Lifetime Gold**: {related_transaction_info[5]}.', inline=False)
            await EventCommand.undo_transaction(self, guild_id, related_transaction_info[6], gold, effective_gold, max_effective_gold, related_transaction_info[0], related_transaction_info[2])
            bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11],player_info[12], player_info[13] + gold, player_info[14] + effective_gold,player_info[16], player_info[17], player_info[18], player_info[19],player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"admin undid transaction {transaction_id}"
            logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None,player_info[13] + gold, gold, player_info[14] + effective_gold, transaction_id,None, None, None, None, None, None, None, None, None, None, None, source)
            logging_thread = guild.get_thread(player_info[25])
            await logging_thread.send(embed=logging_embed)
    else:
        mentions = f"This Transaction was not a valid transaction to undo!!"
        embed = discord.Embed(title=f"Command Failed! Undo Transaction: {transaction_id}", description=f'This Command Failed', colour=discord.Colour.red())
    await ctx.response.send_message(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
    cursor.close()
    db.close()


@admin.command()
async def session_management(interaction: discord.Interaction, session_id: int, gold: typing.Optional[int], easy: typing.Optional[int], medium: typing.Optional[int], hard: typing.Optional[int], deadly: typing.Optional[int], flux: typing.Optional[int], trials: typing.Optional[int], reward_all: typing.Optional[str], party_reward: typing.Optional[str], fame: typing.Optional[int], prestige: typing.Optional[int]):
    """Update Session Information and alter the rewards received by the players"""
    guild_id = interaction.guild_id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT GM_Name, Session_Name, Play_Time, Session_Range, Gold, Flux, Easy, Medium, Hard, Deadly, Trials, Alt_Reward_All, Alt_Reward_Party, Session_Thread, Message, Rewards_Message, Rewards_Thread, Fame, Prestige FROM Sessions WHERE Session_ID = {session_id} and IsActive = 0 LIMIT 1""")
    session_simple = cursor.fetchone()
    cursor.execute(f"""SELECT Player_Name, Character_Name, Level, Received_Milestones, Effective_Gold, Received_Gold, Player_ID, Received_Fame, Forego, Received_Prestige FROM Sessions_Archive WHERE Session_ID = {session_id}""")
    session_complex = cursor.fetchall()
    if session_simple is None:
        await interaction.response.send_message(f'invalid session ID of {session_id}')
    else:
        if gold is not None and gold < 0 or easy is not None and easy < 0 or medium is not None and medium < 0 or hard is not None and hard < 0 or deadly is not None and deadly < 0 or flux is not None and flux < 0 or trials is not None and trials < 0:
            await interaction.response.send_message(f"Minimum Session Rewards may only be 0, if a player receives a lesser reward, have them claim the transaction.")
        elif gold is None and easy is None and medium is None and hard is None and deadly is None and flux is None and trials is None and fame is None and reward_all is None and party_reward is None:
            embed = discord.Embed(title="Session Report", description=f"a report of the session: {session_simple[1]}", color=discord.Color.blue())
            embed.set_author(name=f'{session_simple[0]}')
            embed.add_field(name="Session Info", value=f'**GM:** {session_simple[0]} \n **Level Range**: {session_simple[3]}, **Gold**: {session_simple[4]}, **Trials**: {session_simple[10]}, **Fame**: {session_simple[17]} **Flux**:{session_simple[5]}', inline=False)
            embed.add_field(name="Job Info", value=f'**Easy**: {session_simple[6]}, **Medium**:{session_simple[7]}, **Hard**: {session_simple[8]}, **Deadly**: {session_simple[9]}', inline=False)
            for player in session_complex:
                embed.add_field(name="Character Info", value=f'Player: {player[0]} Character:{player[1]} \r\n **Level**: {player[2]} \r\n **Milestones Received**: {player[3]} **Gold Received**: {player[5]} \r\n ***Fame Received***: {player[[7]]}', inline=False)
            embed.set_footer(text=f'Session occurred on: {session_simple[2]}.')
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.defer(thinking=True)
            gold = session_simple[4] if gold is None else gold
            flux = session_simple[5] if flux is None else flux
            easy = session_simple[6] if easy is None else easy
            medium = session_simple[7] if medium is None else medium
            hard = session_simple[8] if hard is None else hard
            deadly = session_simple[9] if deadly is None else deadly
            trials = session_simple[10] if trials is None else trials
            reward_all = session_simple[11] if reward_all is None else reward_all
            fame = session_simple[17] if fame is None else fame
            prestige = session_simple[18] if prestige is None else prestige
            embed = discord.Embed(title="Session Report", description=f"a report of the session: {session_simple[1]}", color=discord.Color.blue())
            embed.set_author(name=f'{session_simple[0]}')
            embed.add_field(name="Session Info", value=f'**GM:** {session_simple[0]} \n **Level Range**: {session_simple[3]}, **Gold**: {gold}, **Trials**: {trials}, **Fame**: {fame}, **Flux**:{flux}', inline=False)
            embed.add_field(name="Job Info", value=f'**Easy**: {easy}, **Medium**:{medium}, **Hard**: {hard}, **Deadly**: {deadly}', inline=False)
            x = 0
            if party_reward is not None:
                party_reward_embed = discord.Embed(title="Party Reward", description=f"Party Reward for {session_simple[1]}", color=discord.Color.blue())
                party_reward_embed.set_author(name=f'{session_simple[0]}')
                party_reward_embed.add_field(name="Reward Info", value=f'{party_reward}', inline=False)
                if session_simple[16] is None:
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
                    rewards_channel = cursor.fetchone()
                    reward_channel = await bot.fetch_channel(rewards_channel[0])
                    reward_msg = await reward_channel.fetch_message(session_simple[16])
                    reward_thread = await reward_msg.create_thread(name=f"Session name: {session_simple[1]} Party Rewards, Session ID: {session_simple[0]}", auto_archive_duration=60, reason=f"{party_reward}")
                    reward_thread_id = reward_thread.id
                    reward_message_id = reward_msg.id
                    await reward_thread.send(embed=party_reward_embed)
                else:
                    thread = guild.get_thread(session_simple[16])
                    await thread.send(embed=party_reward_embed)
                    reward_message_id = session_simple[15]
                    reward_thread_id = session_simple[16]
            else:
                reward_message_id = session_simple[15]
                reward_thread_id = session_simple[16]
            for player in session_complex:
                x += 1
                cursor.execute(f"""SELECT Easy, Medium, Hard, Deadly from AA_Milestones WHERE level = {player[2]}""")
                job_info = cursor.fetchone()
                easy_jobs = (easy - session_simple[6]) * job_info[0]
                medium_jobs = (medium - session_simple[7]) * job_info[1]
                hard_jobs = (hard - session_simple[8]) * job_info[2]
                deadly_jobs = (deadly - session_simple[9]) * job_info[3]
                if player[8] == 2:
                    rewarded = 0
                else:
                    rewarded = easy_jobs + medium_jobs + hard_jobs + deadly_jobs
                new_milestones = player[3] + rewarded
                # SETTING WHAT THE LEVEL WILL BE.
                cursor.execute(f"SELECT Milestones, Tier, Trials, Gold, Gold_Value, Gold_Value_Max, Flux, Oath FROM Player_Characters WHERE Character_Name = ?", (player[1],))
                current_info = cursor.fetchone()
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?",(player[1],))
                player_info = cursor.fetchone()
                new_milestone_total = player_info[9] + rewarded
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
                max_level = cursor.fetchone()
                int_max_level = int(max_level[0])
                cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{new_milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
                current_level = cursor.fetchone()
                if int_max_level < current_level[0]:
                    int_max_level = player_info[29] if player_info[29] is not None and  int_max_level > player_info[29] else int_max_level
                    cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Level = {int_max_level} ORDER BY Minimum_Milestones DESC  LIMIT 1")
                    current_level = cursor.fetchone()
                    true_level = int(max_level[0])
                else:
                    cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{new_milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
                    current_level = cursor.fetchone()
                    true_level = current_level[0]
                remaining = current_level[1] + current_level[2] - new_milestone_total
                if true_level != player[2]:
                    cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {player[2]}")
                    level_range = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Desc")
                    level_range_max = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Asc")
                    level_range_min = cursor.fetchone()
                    cursor.execute(f"Select True_Character_Name from Player_Characters WHERE Player_Name = '{player[0]}' AND level >= {level_range_min[0]} AND level <= {level_range_max[0]}")
                    level_range_characters = cursor.fetchone()
                    member = await guild.fetch_member(player_info[1])
                    if level_range_characters is None:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {true_level}")
                        new_level_range = cursor.fetchone()
                        role1 = guild.get_role(level_range[2])
                        role2 = guild.get_role(new_level_range[2])
                        await member.remove_roles(role1)
                        await member.add_roles(role2)
                    else:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {true_level}")
                        new_level_range = cursor.fetchone()
                        role2 = guild.get_role(new_level_range[2])
                        await member.add_roles(role2)
#                    DONE SETTING THE LEVEL
#                    SETTING THE MYTHIC TIER, REQUIRES LEVEL TO BE SET BEFOREHAND.
                trials_total = player_info[11] + trials - session_simple[10]
                cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Trials <= {trials_total} ORDER BY Trials DESC  LIMIT 1")
                current_mythic_information = cursor.fetchone()
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Cap'")
                max_tier = cursor.fetchone()
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
                break_point = cursor.fetchone()
                if true_level <= int(break_point[0]):
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
                    tier_rate_limit = cursor.fetchone()
                else:
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
                    tier_rate_limit = cursor.fetchone()
                rate_limited_tier = floor(true_level / int(tier_rate_limit[0]))
                true_tier = int(max_tier[0]) if current_mythic_information[0] > int(max_tier[0]) else current_mythic_information[0]
                true_tier = true_tier if true_tier <= rate_limited_tier else rate_limited_tier
                if true_tier == rate_limited_tier or true_tier == max_tier:
                    cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Tier = {true_tier} LIMIT 1")
                    current_mythic_information = cursor.fetchone()
                    trials_required = current_mythic_information[1] + current_mythic_information[2] - trials_total
                else:
                    trials_required = current_mythic_information[1] + current_mythic_information[2] - trials_total
#                   Done Creating the Tier Variables
                flux_total = player_info[16] + (flux - session_simple[5])
                fame_total = player_info[27] + fame - player[7]
                prestige_total = player_info[30] + prestige - player[9]
#                CREATING THE GOLD VARIABLES (REQUIRES LEVEL TO BE ALREADY SET)
                if player[8] == 3:
                    difference = 0
                    gold_difference = 0
                    effective_gold_total = player_info[14]
                    gold = 0
                else:
                    gold_difference = gold - session_simple[4]
                    effective_gold_total = player_info[14] + gold_difference
                    if current_info[6] == 'Offerings':
                        difference = gold_difference * .5
                    elif current_info[6] == 'Poverty':
                        max_gold = 80 * true_level * true_level
                        if current_info[4] > max_gold:
                            difference = 0
                        elif effective_gold_total > max_gold:
                            difference = effective_gold_total - max_gold
                            effective_gold_total -= difference
                        else:
                            difference = gold_difference
                    elif current_info[7] == 'Absolute':
                        max_gold = true_level * 5
                        if current_info[4] > max_gold:
                            difference = 0
                        elif effective_gold_total > max_gold:
                            difference = effective_gold_total - max_gold
                            effective_gold_total -= difference
                        else:
                            difference = gold_difference
                    else:
                        difference = gold_difference
#                    DONE WITH GOLD
                difference = round(difference, 2)
                await EventCommand.session_rewards(self, player[0], guild_id, player[1], true_level, new_milestone_total, remaining, flux_total, true_tier, trials_total, trials_required, fame_total, prestige_total, f"Adjusting Session {session_id} reward")
                await EventCommand.gold_change(self, guild_id, player[0], player[6], player[1], difference, difference, gold, 'Session Reward', 'Session Reward')
                await EventCommand.update_session_log_player(self, guild_id, session_id, player[1], rewarded, trials, difference, fame, prestige)
                embed.add_field(name="Character Info", value=f'Player: {player[0]} Character:{player[1]} \n **Level**: {true_level} \n **Milestone change**: {rewarded} **Gold change**: {difference}', inline=False)
                cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                transaction_id = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], true_level, true_tier, new_milestone_total, remaining, trials_total, trials_required, player_info[13] + difference, player_info[14] + difference, flux_total, player_info[17], player_info[18], player_info[19], player_info[20], player_info[21],player_info[22], player_info[23], player_info[27], fame_total, prestige_total, player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"admin adjusted session {session_id}"
                logging_embed = log_embed(player_info[2], player_info[2], true_level, rewarded, new_milestone_total, remaining, true_tier, trials - session_simple[10], trials_total, trials_required, player_info[13] + difference, difference, player_info[14] + difference, transaction_id[0], flux_total, flux - session_simple[5], None, None, None, None, reward_all, fame_total, fame, prestige_total, prestige, source)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
            await EventCommand.update_session_log(self, guild_id, session_id, gold, flux, easy, medium, hard, deadly, trials, reward_all, party_reward, reward_message_id, reward_thread_id, fame, prestige)
            await interaction.followup.send(embed=embed)
            cursor.close()
            db.close()


@admin.command()
async def ubb_inventory(interaction: discord.Interaction, player: discord.Member):
    """Display a player's inventory to identify their owned items and set the serverside items for pouches, milestones, and other"""
    guild_id = interaction.guild_id
    client = Client(os.getenv('UBB_TOKEN'))
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    shop = await client.get_inventory_items_all(guild_id, player.id)  # get the inventory
    if shop is not None:
        embed = discord.Embed(title=f"UBB Inventory", description=f'UBB inventory', colour=discord.Colour.blurple())
        embed.add_field(name=f'**new item**', value=f'{shop}', inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"This player does not have any items in their inventory.")
    cursor.close()
    db.close()
    await client.close()


@admin.command()
async def settings_display(ctx: commands.Context, current_page: int = 1):
    """Serverside Settings detailed view"""
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    cursor.execute(f"""SELECT COUNT(Identifier) FROM Admin""")
    admin_count = cursor.fetchone()
    max_page = math.ceil(admin_count[0] / 20)
    if current_page >= max_page:
        current_page = max_page
    low = 1 + ((current_page-1) * 20)
    high = 20 + ((current_page-1) * 20)
    cursor.execute(f"""SELECT Search, Type, Identifier, Description from Admin WHERE ROWID BETWEEN {low} and {high}""")
    pull = cursor.fetchall()
    embed = discord.Embed(title=f"Admin Settings Page {current_page}", description=f'This is a list of the administrative defined settings', colour=discord.Colour.blurple())
    for result in pull:
        embed.add_field(name=f'Identifier: {result[2]}', value=f'**Search Key**: {result[0]}, **Data Type**: {result[1]}, \n **Description**:{result[3]}', inline=False)
    await ctx.response.send_message(embed=embed)
    msg = await ctx.original_response()
    for button in buttons:
        await msg.add_reaction(button)
    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
        except asyncio.TimeoutError:
            embed.set_footer(text="Request has timed out.")
            await msg.edit(embed=embed)
            await msg.clear_reactions()
            cursor.close()
            db.close()
            return print("timed out")
        else:
            previous_page = current_page
            if reaction.emoji == u"\u23EA":
                current_page = 1
                low = 1
                high = 20
            elif reaction.emoji == u"\u2B05" and current_page > 1:
                low -= 20
                high -= 20
                current_page -= 1
            elif reaction.emoji == u"\u27A1" and current_page < max_page:
                low += 20
                high += 20
                current_page += 1
            elif reaction.emoji == u"\u23E9":
                current_page = max_page
                low = ((20 * max_page) - 19)
                high = (20 * max_page)
            for button in buttons:
                await msg.remove_reaction(button, ctx.user)
            if current_page != previous_page:
                cursor.execute(f"""SELECT Search, Type, Identifier, Description from Admin WHERE ROWID BETWEEN {low} and {high}""")
                pull = cursor.fetchall()
                embed = discord.Embed(title=f"Admin Settings Page {current_page}", description=f'This is a list of the administrative defined settings', colour=discord.Colour.blurple())
                for result in pull:
                    embed.add_field(name=f'Search key: {result[2]}', value=f'**Identifier**: {result[0]}, **Type**: {result[1]}, \n **Description**:{result[3]}', inline=False)
                await msg.edit(embed=embed)


@admin.command()
@app_commands.describe(new_search='Enter the corresponding search-key for the Identifier')
@app_commands.describe(identifier='Key phrase to be updated')
async def settings_define(interaction: discord.Interaction, identifier: str, new_search: str):
    """This allows the admin to adjust a serverside setting"""
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = interaction.user.name
    if new_search is None:
        await interaction.response.send_message(f"cannot replace a search key with None")
    elif identifier is None:
        await interaction.response.send_message(f"Yeah... that would break shit, no.")
    else:
        cursor.execute(f"""SELECT Search, Type, Identifier, Description FROM Admin where Identifier = '{identifier}'""")
        information = cursor.fetchone()
        if information is None:
            await interaction.response.send_message('The identifier you have supplied is incorrect.')
        if information is not None:
            await EventCommand.update_settings(self, guild_id, author, new_search, identifier)
            await interaction.response.send_message(f'The identifier of {identifier} is now looking for {new_search}.')
    cursor.close()
    db.close()


@admin.command()
async def level_cap(interaction: discord.Interaction, new_level: int):
    """This allows the admin to adjust the server wide level cap"""
    guild_id = interaction.guild_id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = interaction.user.name
    if new_level < 3:
        await interaction.response.send_message(f"Your server does not have a milestone system for below level 3")
    if new_level > 20:
        await interaction.response.send_message(f"Your server does not have a milestone system for above level 20")
    else:
        await interaction.response.defer(thinking=True)
        await EventCommand.update_level_cap(self, guild_id, author, new_level)
        cursor.execute(f"SELECT Minimum_Milestones FROM AA_Milestones where Level = {new_level}")
        level_info = cursor.fetchone()
        minimum_milestones = level_info[0]
        cursor.execute(f"SELECT COUNT(Character_Name) FROM Player_Characters WHERE Milestones >= {minimum_milestones}")
        count_of_characters = cursor.fetchone()
        cursor.execute(f"SELECT Player_Name, Player_ID, Character_Name, Level, Personal_Cap FROM Player_Characters WHERE Milestones >= {minimum_milestones} LIMIT 20")
        characters_info = cursor.fetchall()
        embed = discord.Embed(title=f"New Level Cap", description=f'The Server level cap has been adjusted', colour=discord.Colour.blurple())
        if count_of_characters is not None:
            x = 0
            character_count = count_of_characters[0]
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            for characters in characters_info:
                personal_cap = 20 if characters[4] is None else characters[4]
                if personal_cap >= new_level:
                    x += 1
                    cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {characters[3]}")
                    level_range = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Desc")
                    level_range_max = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Asc")
                    level_range_min = cursor.fetchone()
                    cursor.execute(f"Select True_Character_Name from Player_Characters WHERE Player_Name = '{characters[2]}' AND level >= {level_range_min[0]} AND level <= {level_range_max[0]}")
                    level_range_characters = cursor.fetchone()
                    member = await guild.fetch_member(characters[1])
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                    character_log_channel_id = cursor.fetchone()
                    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?", (characters[2],))
                    player_info = cursor.fetchone()
                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], new_level, player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21],player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                    bio_message = await bio_channel.fetch_message(player_info[24])
                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                    source = f"admin adjusted level cap to {new_level}"
                    logging_embed = log_embed(player_info[2], author, new_level, 0, player_info[9], player_info[10], player_info[8], 0, player_info[11], player_info[12], None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, source)
                    logging_thread = guild.get_thread(player_info[25])
                    logging_thread_mention = f"<@{player_info[1]}>"
                    await logging_thread.send(embed=logging_embed, content=logging_thread_mention, allowed_mentions=discord.AllowedMentions(users=True))
                    if level_range_characters is None:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {new_level}")
                        new_level_range = cursor.fetchone()
                        role1 = guild.get_role(level_range[2])
                        role2 = guild.get_role(new_level_range[2])
                        await member.remove_roles(role1)
                        await member.add_roles(role2)
                    else:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {new_level}")
                        new_level_range = cursor.fetchone()
                        role2 = guild.get_role(new_level_range[2])
                        await member.add_roles(role2)
                    if x <= 20:
                        embed.add_field(name=f"**{characters[2]}**", value=f"<@{characters[1]}>'s character {characters[2]} has been leveled up to {new_level}.", inline=False)
                if character_count <= 20:
                    if character_count == 0:
                        embed.set_footer(text="There were no characters to be adjusted.")
                    else:
                        embed.set_footer(text="Are all the characters who have been adjusted to a new level.")
            else:
                character_count -= 20
                embed.set_footer(text=f"And {character_count[0]} more have obtained a new level")
        if count_of_characters is None:
            embed.add_field(name=f"**No Characters Changed:**", value=f"The server cap is now {new_level} but no characters meet the minimum milestones.", inline=False)
        await interaction.followup.send(embed=embed)
    cursor.close()
    db.close()


@admin.command()
async def tier_cap(interaction: discord.Interaction, new_tier: int):
    """This allows the admin to adjust the max serverside tier"""
    guild_id = interaction.guild_id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = interaction.user.name
    await interaction.response.defer(thinking=True, ephemeral=True)
    if new_tier < 1:
        await interaction.followup.send(f"Negative Mythic Tiers? More like... Negative Brain Cells AMIRITE? {new_tier} is not valid")
    elif new_tier > 10:
        await interaction.followup.send(f"Just make them gods already damnit?! {new_tier} is too high!")
    else:
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
        break_point = cursor.fetchone()
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
        tier_rate_limit = cursor.fetchone()
        minimum_level = new_tier * int(tier_rate_limit[0])
        if int(minimum_level) <= int(break_point[0]):
            minimum_level = minimum_level
        else:
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
            tier_rate_limit = cursor.fetchone()
            minimum_level = new_tier * int(tier_rate_limit[0])
        cursor.execute(f"SELECT Trials FROM AA_Trials where Tier = {new_tier}")
        level_info = cursor.fetchone()
        minimum_milestones = level_info[0]
        cursor.execute(f"SELECT COUNT(Character_Name) FROM Player_Characters Trials WHERE level >= {minimum_milestones} and level >= {minimum_level}")
        count_of_characters = cursor.fetchone()
        cursor.execute(f"SELECT Player_Name, Player_ID, Character_Name FROM Player_Characters WHERE Trials >= {minimum_milestones} LIMIT 20")
        characters_info = cursor.fetchall()
        await EventCommand.update_tier_cap(self, guild_id, author, new_tier, minimum_level)
        embed = discord.Embed(title=f"New Trial Cap", description=f'The Server Trial cap has been adjusted', colour=discord.Colour.blurple())
        if count_of_characters is not None:
            x = 0
            character_count = count_of_characters[0]
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            for characters in characters_info:
                x += 1
                embed.add_field(name=f"**{characters[2]}**", value=f"<@{characters[1]}>'s character {characters[2]} has attained a new tier of {new_tier}.", inline=False)
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?",(characters[2],))
                player_info = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"admin adjusted tier cap to {new_tier}"
                logging_embed = log_embed(player_info[2], author, None, None, None,None, new_tier, 0, player_info[11], player_info[12], None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, source)
                logging_thread = guild.get_thread(player_info[25])
                try:
                    await logging_thread.send(embed=logging_embed)
                except:
                    pass
            if character_count <= 20:
                embed.set_footer(text=f"Are all the characters who have been adjusted to a new new_tier.")
            else:
                character_count -= 20
                embed.set_footer(text="And {character_count[0]} more have obtained a new tier")
        if count_of_characters is None:
            embed.add_field(name=f"**No Characters Changed:**", value=f"The server cap is now {new_tier} but no characters meet the minimum milestones.", inline=False)
        await interaction.followup.send(embed=embed)
    cursor.close()
    db.close()


@admin.command()
@app_commands.autocomplete(character_name=character_select_autocompletion)
async def flux_adjust(ctx: commands.Context, character_name: str, amount: int):
    """Adjust the flux a PC has"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount == 0:
        ctx.response.send_message(f"BRUH, 0 flux change? SRSLY?")
    elif amount != 0:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name, character_name))
        player_info = cursor.fetchone()
        if player_info is None:
            await ctx.response.send_message(f"There is no character named {character_name} that can be found by their name or nickname")
        elif player_info is not None:
            true_name = player_info[2]
            new_flux = player_info[16] + amount
            await EventCommand.flux(self, guild_id, true_name, amount, new_flux, author)
            response = f"{character_name}'s Flux has changed by {amount} to become {new_flux}."
            await ctx.response.send_message(response, ephemeral=True)
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16] + amount, player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"admin adjusted gold by {amount} for {character_name}"
            logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, None, None, None, None, new_flux, amount, None, None, None, None, None, None, None, None, None, source)
            logging_thread = guild.get_thread(player_info[25])
            await logging_thread.send(embed=logging_embed)
    cursor.close()
    db.close()


@admin.command()
async def level_range(ctx: commands.Context, range: discord.Role, minimum_level: int, maximum_level: int):
    """Adjust the role associated with a level range in the server"""
    if maximum_level < minimum_level:
        await ctx.response.send_message("Your Minimum Level Exceeded your maximum level!", ephemeral=True)
    elif maximum_level < 3 or maximum_level > 20:
        await ctx.response.send_message(f"Your maximum level of {maximum_level} is either below 3 or above 20!", ephemeral=True)
    elif minimum_level < 3 or minimum_level > 20:
        await ctx.response.send_message(f"Your minimum level of {minimum_level} is either below 3 or above 20!", ephemeral=True)
    else:
        guild_id = ctx.guild_id
        author = ctx.user.name
        role_name = range.name
        role_id = range.id
        await EventCommand.set_range(self, guild_id, author, role_name, role_id, minimum_level, maximum_level)
        embed = discord.Embed(title=f"Range Update", description=f'a new role name and role ID has been applied', colour=discord.Colour.green())
        embed.add_field(name=f'**Role**', value=f'{role_name} with ID: {role_id}.', inline=False)
        embed.add_field(name=f'**Range**', value=f'{minimum_level} level to {maximum_level} level have been updated', inline=False)
        await ctx.response.send_message(embed=embed)


@admin.command()
@app_commands.describe(certainty="is life short?")
@app_commands.choices(certainty=[discord.app_commands.Choice(name='YOLO', value=1), discord.app_commands.Choice(name='No', value=2)])
async def reset_database(ctx: commands.Context, certainty: discord.app_commands.Choice[int]):
    """Perform a database reset, remember to reassign role ranges and server settings!"""
    if certainty == 1:
        certainty = 1
    else:
        certainty = certainty.value
    if certainty.value == 1:
        guild_id = ctx.guild_id
        buttons = ["✅", "❌"]  # checkmark X symbol
        embed = discord.Embed(title=f"Are you sure you want to reset the server database??", description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                return print("timed out")
            else:
                if reaction.emoji == u"\u264C":
                    embed = discord.Embed(title=f"You have thought better of freely giving your money", description=f"Savings!", colour=discord.Colour.blurple())
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                if reaction.emoji == u"\u2705":
                    embed = discord.Embed(title=f"Database Reset has occurred!", description=f"Say Farewell to a world you used to know.", colour=discord.Colour.red())
                    await msg.clear_reactions()
                    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    shutil.copyfile(f"C:/pathparser/pathparser_{guild_id}.sqlite", f"C:/pathparser/pathparser_{guild_id}_{time}.sqlite")
                    shutil.copyfile(f"C:/pathparser/pathparser.sqlite", f"C:/pathparser/pathparser_{guild_id}.sqlite")
                    await msg.edit(embed=embed)
    else:
        await ctx.response.send_message(f"I'M FIRING MY LAS--- What?")


@admin.command()
@app_commands.describe(player_wipe="if yes, remove all inactive players!")
@app_commands.choices(player_wipe=[discord.app_commands.Choice(name='No!', value=1), discord.app_commands.Choice(name='Yes!', value=2)])
async def clean_playerbase(ctx: commands.Context, player: typing.Optional[discord.Member], player_id: typing.Optional[int], player_wipe: discord.app_commands.Choice[int] = 1):
    """Clean out the entire playerbase or clean out a specific player's character by mentioning them or using their role!"""
    if player_wipe == 1:
        player_wipe = 1
    else:
        player_wipe = player_wipe.value
    if player_wipe == 1 and player_id is None and player is None:
        await ctx.response.send_message(f"Pick Something that lets me end someone! Please?", ephemeral=True)
    else:
        guild_id = ctx.guild_id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = ctx.user.name
        overall_wipe_list = []
        embed = discord.Embed(title=f"The Following Players will have their characters removed:",
                              description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
        if player_id is not None:
            cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from Player_Characters where Player_ID = {player_id}")
            player_id_info = cursor.fetchone()
            if player_id_info is not None:
                overall_wipe_list.append(player_id)
                embed.add_field(name=f"{player_id_info[0]}'s characters will be removed", value=f"this player had {player_id_info[1]} characters!")
            else:
                embed.add_field(name=f"{player_id} could not be found in the database.", value=f"This ID had no characters associated with it..")
        if player is not None:
            cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from Player_Characters where Player_ID = {player.id}")
            player_id_info = cursor.fetchone()
            if player_id_info is not None:
                embed.add_field(name=f"{player_id_info}'s characters will be removed", value=f"This player had {player_id_info[2]} characters who will be removed.")
                overall_wipe_list.append(player.id)
            else:
                embed.add_field(name=f"{player.name} could not be found in the database.", value=f"This user had no characters associated with it..")
        if player_wipe == 2:
            guild = ctx.guild
            cursor.execute(f"Select distinct(Player_ID), count(Character_Name) from Player_Characters")
            player_id_info = cursor.fetchall()
            wipe_tuple = None
            x = 0
            for inactive_player in player_id_info:
                member = guild.get_member(inactive_player[0])
                if member is None:
                    x += 1
                    overall_wipe_list.append(inactive_player[0])
                    if x <= 20:
                        embed.add_field(name=f"{player_id_info[0]}'s characters will be removed", value=f"this player had {player_id_info[1]} characters!")
                else:
                    x = x
                    wipe_tuple = wipe_tuple
            embed.set_footer(text=f"{x} Total Players were inactive and are being removed!")
        else:
            embed.add_field(name=f"No Player Characters could be found in the database.", value=f"This ID had no characters associated with it..")
        guild_id = ctx.guild_id
        buttons = ["✅", "❌"]  # checkmark X symbol
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                cursor.close()
                db.close()
                return print("timed out")
            else:
                if reaction.emoji == u"\u264C":
                    embed = discord.Embed(title=f"You have thought better of freely giving your money", description=f"Savings!", colour=discord.Colour.blurple())
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                if reaction.emoji == u"\u2705":
                    embed = discord.Embed(title=f"Database Reset has occurred!", description=f"Say Farewell to a world you used to know.", colour=discord.Colour.red())
                    await msg.clear_reactions()
                    await msg.edit(embed=embed)
                    for wiped in overall_wipe_list:
                        await EventCommand.wipe_unapproved(self, wiped[0], guild_id, author)



@admin.command()
@app_commands.autocomplete(character_name=stg_character_select_autocompletion)
@app_commands.describe(cleanse="Optional: supply a number ending with D or W to remove users who have not been accepted within that period!")
@app_commands.describe(status="Accepted players are moved into active and posted underneath!")
@app_commands.choices(status=[discord.app_commands.Choice(name='Accepted!', value=1), discord.app_commands.Choice(name='Rejected!', value=2)])
async def manage(ctx: commands.Context, character_name: str, player_id: typing.Optional[int], status: discord.app_commands.Choice[int] = 1, cleanse: str = None):
    """accept a player into your accepted bios, or clean out the stage tables!"""
    guild = ctx.guild
    guild_id = ctx.guild_id
    if status == 1:
        status = 1
    else:
        status = status.value
    if character_name is None and cleanse is None:
        await ctx.response.send_message(f"NOTHING COMPLETED, RUN DURATION: 1 BAJILLION Eternities?", ephemeral=True)
    elif cleanse is not None or character_name is not None and status == 2 or player_id is not None and status == 2:
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = ctx.user.name
        if status == 2:
            overall_wipe_list = []
            character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
            embed = discord.Embed(title=f"The Following Players will have their staged characters removed:",
                                  description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
            if character_name is not None:
                cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where character_name = ?", (character_name,))
                player_id_info = cursor.fetchone()
                if player_id_info is not None:
                    overall_wipe_list.append(character_name)
                    embed.add_field(name=f"{player_id_info[0]}'s character will be removed from stage", value=f"The character of {character_name} will be removed!")
                else:
                    embed.add_field(name=f"{character_name} could not be found in the database.", value=f"This character name had no characters associated with it.")
            if cleanse is not None:
                if cleanse.endswith('D'):
                    cleanse = cleanse.replace('D', '')
                    cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where Created_Date <= date('now', '-{cleanse} days')")
                    player_id_info = cursor.fetchall()
                    x = 0
                    for inactive_player in player_id_info:
                        x += 1
                        overall_wipe_list.append(inactive_player[0])
                        if x <= 20:
                            embed.add_field(name=f"{player_id_info[0]}'s characters will be removed", value=f"this player had {player_id_info[1]} characters!")
                    embed.set_footer(text=f"{x} Total Players were inactive and are being removed!")
                elif cleanse.endswith('W'):
                    cleanse = cleanse.replace('W', '')
                    cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where Created_Date <= date('now', '-{cleanse} weeks')")
                    player_id_info = cursor.fetchall()
                    x = 0
                    for inactive_player in player_id_info:
                        x += 1
                        overall_wipe_list.append(inactive_player[0])
                        if x <= 20:
                            embed.add_field(name=f"{player_id_info[0]}'s characters will be removed", value=f"this player had {player_id_info[1]} characters!")
                    embed.set_footer(text=f"{x} Total Players were inactive and are being removed!")
                else:
                    embed.add_field(name=f"Invalid Duration", value=f"Please use a number ending in D for days or W for weeks.")
            buttons = ["✅", "❌"]  # checkmark X symbol
            await ctx.response.send_message(embed=embed)
            msg = await ctx.original_response()
            for button in buttons:
                await msg.add_reaction(button)
            while True:
                try:
                    reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
                except asyncio.TimeoutError:
                    embed.set_footer(text="Request has timed out.")
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                    cursor.close()
                    db.close()
                    return print("timed out")
                else:
                    if reaction.emoji == "❌":
                        embed = discord.Embed(title=f"you have reconsidered wiping a character", description=f"life is a kindness, do not waste it!", colour=discord.Colour.blurple())
                        await msg.edit(embed=embed)
                        await msg.clear_reactions()
                    if reaction.emoji == u"\u2705":
                        embed = discord.Embed(title=f"Character wipe has been approved!", description=f"Getting rid of outdated characters.", colour=discord.Colour.red())
                        await msg.clear_reactions()
                        await msg.edit(embed=embed)
                        print(overall_wipe_list)
                        print(type(overall_wipe_list))
                        for wiped in overall_wipe_list:
                            await EventCommand.wipe_unapproved(self, wiped, guild_id, author)
    else:
        e = None
        try:
            await ctx.response.defer(thinking=True, ephemeral=True)
        except Exception as e:
            print(e)
            pass
        guild_id = ctx.guild_id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = ctx.user.name
        character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
        cursor.execute(f"Select True_Character_Name, tmp_bio, mythweavers from A_STG_Player_Characters where character_name = ?", (character_name,))
        player_id_info = cursor.fetchone()
        if player_id_info is not None:
            if player_id_info[1] is not None or 'worldanvil' in player_id_info[2]:
                try:
                    e = None
                    await EventCommand.create_bio(self, guild_id, player_id_info[0], player_id_info[1], player_id_info[2])
                except Exception as e:
                    print(e)
                    pass
            else:
                e = None
            await EventCommand.create_character(self, guild_id, author, player_id_info[0])
            cursor.execute(f"SELECT Search FROM Admin WHERE Identifier = 'Approved_Character'")
            approved_character = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            cursor.execute(f"SELECT Player_Name, True_Character_Name, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_Value_Max, Mythweavers, Image_Link, Color, Flux, Player_ID, Oath, Article_Link FROM Player_Characters WHERE Character_Name = ?", (character_name,))
            character_info = cursor.fetchone()
            member = await guild.fetch_member(character_info[17])
            role1 = guild.get_role(int(approved_character[0]))
            await member.add_roles(role1)
            color = character_info[15]
            int_color = int(color[1:], 16)
            mentions = f'<@{character_info[17]}>'
            description_field = f" "
            print(character_info[19])
            if character_info[2] is not None:
                description_field += f"**Other Names**: {character_info[2]}\r\n"
            if character_info[19] is not None:
                description_field += f"[Backstory](<{character_info[19]}>)"
            embed = discord.Embed(title=f"{character_info[1]}", url=f'{character_info[13]}', description=f"{description_field}", color=int_color)
            embed.set_author(name=f'{character_info[0]}')
            embed.set_thumbnail(url=f'{character_info[14]}')
            embed.add_field(name="Information", value=f'**Level**: 3, **Mythic Tier**: 0, **Fame**: 0', inline=False)
            embed.add_field(name="Experience", value=f'**Milestones**: 0, **Remaining**: 3')
            embed.add_field(name="Mythic", value=f'**Trials**: 0, **Remaining**: 0')
            embed.add_field(name="Current Wealth", value=f'**GP**: {character_info[10]}', inline=False)
            embed.add_field(name="Current Flux", value=f'**Flux**: 0')
            print(character_info[18])
            if character_info[18] == 'Offerings':
                embed.set_footer(text=f'{character_info[3]}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
            elif character_info[18] == 'Poverty':
                embed.set_footer(text=f'{character_info[3]}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
            elif character_info[18] == 'Absolute':
                embed.set_footer(text=f'{character_info[3]}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
            else:
                embed.set_footer(text=f'{character_info[3]}')
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.send(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            embed = discord.Embed(title=f"{character_info[1]}", url=f'{character_info[13]}', description=f"Other Names: {character_info[2]}", color=int_color)
            embed.set_author(name=f'{character_info[0]}')
            embed.set_thumbnail(url=f'{character_info[14]}')
            character_log_channel = await bot.fetch_channel(character_log_channel_id[0])
            character_log_message = await character_log_channel.send(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            thread = await character_log_message.create_thread(name=f'{character_info[1]}')
            await EventCommand.log_character(self, guild_id, character_name, bio_message.id, character_log_message.id, thread.id)
            if e is None:
                await ctx.followup.send(content=f"{character_name} has been accepted into the server!")
            else:
                await ctx.send(f"{character_name} has been accepted into the server!")
        else:
            if e is None:
                await ctx.followup.send(f"{character_name} could not be found in the database.", ephemeral=True)
            else:
                await ctx.send(f"{character_name} has been accepted into the server!")

@content.command()
@app_commands.autocomplete(character_name=stg_character_select_autocompletion)
@app_commands.describe(cleanse="Optional: supply a number ending with D or W to remove users who have not been accepted within that period!")
@app_commands.describe(status="Accepted players are moved into active and posted underneath!")
@app_commands.choices(status=[discord.app_commands.Choice(name='Accepted!', value=1), discord.app_commands.Choice(name='Rejected!', value=2)])
async def manage(ctx: commands.Context, character_name: str, player_id: typing.Optional[int], status: discord.app_commands.Choice[int] = 1, cleanse: str = None):
    """accept a player into your accepted bios, or clean out the stage tables!"""
    guild = ctx.guild
    guild_id = ctx.guild_id
    if status == 1:
        status = 1
    else:
        status = status.value
    if character_name is None and cleanse is None:
        await ctx.response.send_message(f"NOTHING COMPLETED, RUN DURATION: 1 BAJILLION Eternities?", ephemeral=True)
    elif cleanse is not None or character_name is not None and status == 2 or player_id is not None and status == 2:
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = ctx.user.name
        if status == 2:
            overall_wipe_list = []
            character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
            embed = discord.Embed(title=f"The Following Players will have their staged characters removed:",
                                  description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
            if character_name is not None:
                cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where character_name = ?", (character_name,))
                player_id_info = cursor.fetchone()
                if player_id_info is not None:
                    overall_wipe_list.append(character_name)
                    embed.add_field(name=f"{player_id_info[0]}'s character will be removed from stage", value=f"The character of {character_name} will be removed!")
                else:
                    embed.add_field(name=f"{character_name} could not be found in the database.", value=f"This character name had no characters associated with it.")
            if cleanse is not None:
                if cleanse.endswith('D'):
                    cleanse = cleanse.replace('D', '')
                    cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where Created_Date <= date('now', '-{cleanse} days')")
                    player_id_info = cursor.fetchall()
                    x = 0
                    for inactive_player in player_id_info:
                        x += 1
                        overall_wipe_list.append(inactive_player[0])
                        if x <= 20:
                            embed.add_field(name=f"{player_id_info[0]}'s characters will be removed", value=f"this player had {player_id_info[1]} characters!")
                    embed.set_footer(text=f"{x} Total Players were inactive and are being removed!")
                elif cleanse.endswith('W'):
                    cleanse = cleanse.replace('W', '')
                    cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where Created_Date <= date('now', '-{cleanse} weeks')")
                    player_id_info = cursor.fetchall()
                    x = 0
                    for inactive_player in player_id_info:
                        x += 1
                        overall_wipe_list.append(inactive_player[0])
                        if x <= 20:
                            embed.add_field(name=f"{player_id_info[0]}'s characters will be removed", value=f"this player had {player_id_info[1]} characters!")
                    embed.set_footer(text=f"{x} Total Players were inactive and are being removed!")
                else:
                    embed.add_field(name=f"Invalid Duration", value=f"Please use a number ending in D for days or W for weeks.")
            buttons = ["✅", "❌"]  # checkmark X symbol
            await ctx.response.send_message(embed=embed)
            msg = await ctx.original_response()
            for button in buttons:
                await msg.add_reaction(button)
            while True:
                try:
                    reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
                except asyncio.TimeoutError:
                    embed.set_footer(text="Request has timed out.")
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                    cursor.close()
                    db.close()
                    return print("timed out")
                else:
                    if reaction.emoji == "❌":
                        embed = discord.Embed(title=f"you have reconsidered wiping a character", description=f"life is a kindness, do not waste it!", colour=discord.Colour.blurple())
                        await msg.edit(embed=embed)
                        await msg.clear_reactions()
                    if reaction.emoji == u"\u2705":
                        embed = discord.Embed(title=f"Character wipe has been approved!", description=f"Getting rid of outdated characters.", colour=discord.Colour.red())
                        await msg.clear_reactions()
                        await msg.edit(embed=embed)
                        print(overall_wipe_list)
                        print(type(overall_wipe_list))
                        for wiped in overall_wipe_list:
                            await EventCommand.wipe_unapproved(self, wiped, guild_id, author)
    else:
        e = None
        try:
            await ctx.response.defer(thinking=True, ephemeral=True)
        except Exception as e:
            print(e)
            pass
        guild_id = ctx.guild_id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = ctx.user.name
        character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
        cursor.execute(f"Select True_Character_Name, tmp_bio, mythweavers from A_STG_Player_Characters where character_name = ?", (character_name,))
        player_id_info = cursor.fetchone()
        if player_id_info is not None:
            e = None
            if player_id_info[1] is not None or 'worldanvil' in player_id_info[2]:
                try:
                    e = None
                    await EventCommand.create_bio(self, guild_id, player_id_info[0], player_id_info[1], player_id_info[2])
                except Exception as e:
                    print(e)
                    pass
            else:
                e = None
            await EventCommand.create_character(self, guild_id, author, player_id_info[0])
            cursor.execute(f"SELECT Search FROM Admin WHERE Identifier = 'Approved_Character'")
            approved_character = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            cursor.execute(f"SELECT Player_Name, True_Character_Name, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_Value_Max, Mythweavers, Image_Link, Color, Flux, Player_ID, Oath, Article_Link FROM Player_Characters WHERE Character_Name = ?", (character_name,))
            character_info = cursor.fetchone()
            member = await guild.fetch_member(character_info[17])
            role1 = guild.get_role(int(approved_character[0]))
            await member.add_roles(role1)
            color = character_info[15]
            int_color = int(color[1:], 16)
            mentions = f'<@{character_info[17]}>'
            description_field = f" "
            print(character_info[19])
            if character_info[2] is not None:
                description_field += f"**Other Names**: {character_info[2]}\r\n"
            if character_info[19] is not None:
                description_field += f"[Backstory](<{character_info[19]}>)"
            embed = discord.Embed(title=f"{character_info[1]}", url=f'{character_info[13]}', description=f"{description_field}", color=int_color)
            embed.set_author(name=f'{character_info[0]}')
            embed.set_thumbnail(url=f'{character_info[14]}')
            embed.add_field(name="Information", value=f'**Level**: 3, **Mythic Tier**: 0, **Fame**: 0', inline=False)
            embed.add_field(name="Experience", value=f'**Milestones**: 0, **Remaining**: 3')
            embed.add_field(name="Mythic", value=f'**Trials**: 0, **Remaining**: 0')
            embed.add_field(name="Current Wealth", value=f'**GP**: {character_info[10]}', inline=False)
            embed.add_field(name="Current Flux", value=f'**Flux**: 0')
            print(character_info[18])
            if character_info[18] == 'Offerings':
                embed.set_footer(text=f'{character_info[3]}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
            elif character_info[18] == 'Poverty':
                embed.set_footer(text=f'{character_info[3]}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
            elif character_info[18] == 'Absolute':
                embed.set_footer(text=f'{character_info[3]}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
            else:
                embed.set_footer(text=f'{character_info[3]}')
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.send(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            embed = discord.Embed(title=f"{character_info[1]}", url=f'{character_info[13]}', description=f"Other Names: {character_info[2]}", color=int_color)
            embed.set_author(name=f'{character_info[0]}')
            embed.set_thumbnail(url=f'{character_info[14]}')
            character_log_channel = await bot.fetch_channel(character_log_channel_id[0])
            character_log_message = await character_log_channel.send(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            thread = await character_log_message.create_thread(name=f'{character_info[1]}')
            await EventCommand.log_character(self, guild_id, character_name, bio_message.id, character_log_message.id, thread.id)
            if e is None:
                await ctx.followup.send(content=f"{character_name} has been accepted into the server!")
            else:
                await ctx.send(f"{character_name} has been accepted into the server!")
        else:
            if e is None:
                await ctx.followup.send(f"{character_name} could not be found in the database.", ephemeral=True)
            else:
                await ctx.send(f"{character_name} has been accepted into the server!")




@admin.command()
@app_commands.autocomplete(character_name=character_select_autocompletion)
@app_commands.describe(destination="Shorthand for determining whether you are looking for a character name or nickname")
@app_commands.choices(destination=[discord.app_commands.Choice(name='Tradition', value=1), discord.app_commands.Choice(name='Template', value=2)])
@app_commands.describe(customized_name="For the name of the template or tradition")
async def customize(ctx: commands.Context, character_name: str, destination: discord.app_commands.Choice[int], customized_name: str, link: str, flux_cost: int = 0):
    """Administrative: set a character's template or tradition!"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    if destination == 1:
        destination = 1
    else:
        destination = destination.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = ctx.user.name
    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?", (character_name, ))
    player_info = cursor.fetchone()

    if player_info is None:
        await ctx.response.send_message(f"no character with the Name or Nickname of {character_name} could be found!", ephemeral=True)
    else:
        destination_name = 'Tradition_Name' if destination == 1 else 'Template_Name'
        destination_link = 'Tradition_Link' if destination == 1 else 'Template_Link'
        destination_name_pretty = 'Tradition Name' if destination == 1 else 'Template Name'
        tradition_name = customized_name if destination == 1 else None
        tradition_link = link if destination == 1 else None
        template_name = customized_name if destination == 2 else None
        template_link = link if destination == 2 else None
        flux_remaining = player_info[16] - flux_cost
        await EventCommand.customize_characters(self, guild_id, author, player_info[3], destination_name, destination_link, customized_name, link, flux_remaining, flux_cost)
        embed = discord.Embed(title=f"{destination_name_pretty} change for {player_info[3]}", description=f"<@{player_info[1]}>'s {player_info[3]} has spent {flux_cost} flux leaving them with {player_info[16] - flux_cost} flux!", colour=discord.Colour.blurple())
        embed.add_field(name=f'**{destination_name_pretty} Information:**', value=f'[{customized_name}](<{link}>)', inline=False)
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
        accepted_bio_channel = cursor.fetchone()
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
        character_log_channel_id = cursor.fetchone()
        cursor.close()
        db.close()
        bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16] + flux_cost, player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
        bio_message = await bio_channel.fetch_message(player_info[24])
        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
        source = f"changed a template or tradition for {character_name}"
        logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, None, None, None, None, player_info[16] - flux_cost, flux_cost, tradition_name, tradition_link, template_name, template_link, None, None, None, None, None, source)
        logging_thread = guild.get_thread(player_info[25])
        await logging_thread.send(embed=logging_embed)
        await ctx.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))

@content.command()
@app_commands.autocomplete(character_name=character_select_autocompletion)
@app_commands.describe(destination="Shorthand for determining whether you are looking for a character name or nickname")
@app_commands.choices(destination=[discord.app_commands.Choice(name='Tradition', value=1), discord.app_commands.Choice(name='Template', value=2)])
@app_commands.describe(customized_name="For the name of the template or tradition")
async def customize(ctx: commands.Context, character_name: str, destination: discord.app_commands.Choice[int], customized_name: str, link: str, flux_cost: int = 0):
    """Administrative: set a character's template or tradition!"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    if destination == 1:
        destination = 1
    else:
        destination = destination.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = ctx.user.name
    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?", (character_name, ))
    player_info = cursor.fetchone()

    if player_info is None:
        await ctx.response.send_message(f"no character with the Name or Nickname of {character_name} could be found!", ephemeral=True)
    else:
        destination_name = 'Tradition_Name' if destination == 1 else 'Template_Name'
        destination_link = 'Tradition_Link' if destination == 1 else 'Template_Link'
        destination_name_pretty = 'Tradition Name' if destination == 1 else 'Template Name'
        tradition_name = customized_name if destination == 1 else None
        tradition_link = link if destination == 1 else None
        template_name = customized_name if destination == 2 else None
        template_link = link if destination == 2 else None
        flux_remaining = player_info[16] - flux_cost
        await EventCommand.customize_characters(self, guild_id, author, player_info[3], destination_name, destination_link, customized_name, link, flux_remaining, flux_cost)
        embed = discord.Embed(title=f"{destination_name_pretty} change for {player_info[3]}", description=f"<@{player_info[1]}>'s {player_info[3]} has spent {flux_cost} flux leaving them with {player_info[16] - flux_cost} flux!", colour=discord.Colour.blurple())
        embed.add_field(name=f'**{destination_name_pretty} Information:**', value=f'[{customized_name}](<{link}>)', inline=False)
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
        accepted_bio_channel = cursor.fetchone()
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
        character_log_channel_id = cursor.fetchone()
        cursor.close()
        db.close()
        bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16] + flux_cost, player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
        bio_message = await bio_channel.fetch_message(player_info[24])
        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
        source = f"changed a template or tradition for {character_name}"
        logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, None, None, None, None, player_info[16] - flux_cost, flux_cost, tradition_name, tradition_link, template_name, template_link, None, None, None, None, None, source)
        logging_thread = guild.get_thread(player_info[25])
        await logging_thread.send(embed=logging_embed)
        await ctx.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))


@admin.command()
@app_commands.describe(modify="add, remove edit, or display something in the store.")
@app_commands.choices(modify=[discord.app_commands.Choice(name='Display', value=1), discord.app_commands.Choice(name='Add', value=2), discord.app_commands.Choice(name='Edit', value=3), discord.app_commands.Choice(name='Remove', value=4)])
async def fame_store(ctx: commands.Context, name: str, fame_required: typing.Optional[int], prestige_cost: typing.Optional[int], effect: typing.Optional[str], limit: typing.Optional[int], modify: discord.app_commands.Choice[int] = 1):
    """add, edit, remove, or display something from one of the stores"""
    guild_id = ctx.guild_id
    if modify == 1:
        modify = 1
    else:
        modify = modify.value
    name = f"N/A" if name is None else name
    fame_required = 0 if fame_required is None else fame_required
    prestige_cost = 0 if prestige_cost is None else prestige_cost
    effect = f"N/A" if effect is None else effect
    limit = 99 if limit is None else limit
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = ctx.user.name
    cursor.execute(f"SELECT Fame_Required, Prestige_Cost, Effect, Use_Limit FROM Store_Fame where Name = ?", (name,))
    item_info = cursor.fetchone()
    cursor.close()
    db.close()
    if item_info is None and modify == 2:
        await EventCommand.add_fame_store(self, guild_id, author, fame_required, prestige_cost, name, effect, limit)
        embed = discord.Embed(title=f"New Fame Store Item", description=f'{name} has been added to the fame store!', colour=discord.Colour.blurple())
        embed.add_field(name=f'**Cost:**', value=f'Requires {fame_required} fame, Costs: {prestige_cost} prestige, Limited to {limit}', inline=False)
        embed.add_field(name=f'**Effect:**', value=f'{effect}', inline=False)
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 3:
        await EventCommand.remove_fame_store(self, guild_id, author, name)
        embed = discord.Embed(title=f"Removed Fame Store Item", description=f'{name} has been removed from the fame store!', colour=discord.Colour.blurple())
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 4:
        await EventCommand.edit_fame_store(self, guild_id, author, fame_required, prestige_cost, name, effect, limit)
        embed = discord.Embed(title=f"Edited Fame Store Item", description=f'{name} has been edited in the fame store!', colour=discord.Colour.blurple())
        embed.add_field(name=f'**Cost:**', value=f'Requires {fame_required} fame, Costs: {prestige_cost} prestige, Limited to {limit}', inline=False)
        embed.add_field(name=f'**Effect:**', value=f'{effect}', inline=False)
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif modify == 1:
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit FROM Store_Fame where Name = ?""", (name,))
        item_info = cursor.fetchone()
        if item_info is not None:
            embed = discord.Embed(title=f'**Fame Required**: {item_info[0]} **Prestige Cost**: {item_info[1]}, **Limit**: {item_info[4]} \r\n **Effect**: {item_info[3]}', colour=discord.Colour.blurple())
            await ctx.response.send_message(embed=embed)
        else:
            buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
            cursor.execute(f"""SELECT COUNT(Name) FROM Store_Fame""")
            admin_count = cursor.fetchone()
            max_page = math.ceil(admin_count[0] / 20)
            current_page = 1
            low = 1 + ((current_page - 1) * 20)
            high = 20 + ((current_page - 1) * 20)
            cursor.execute(f"""SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}""")
            pull = cursor.fetchall()
            embed = discord.Embed(title=f"Fame Store Settings Page {current_page}", description=f'This is a list of the administratively defined items', colour=discord.Colour.blurple())
            for result in pull:
                embed.add_field(name=f'**Name**: {result[2]}', value=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}', inline=False)
            await ctx.response.send_message(embed=embed)
            msg = await ctx.original_response()
            for button in buttons:
                await msg.add_reaction(button)
            while True:
                try:
                    reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
                except asyncio.TimeoutError:
                    embed.set_footer(text="Request has timed out.")
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                    cursor.close()
                    db.close()
                    return print("timed out")
                else:
                    previous_page = current_page
                    if reaction.emoji == u"\u23EA":
                        current_page = 1
                        low = 1
                        high = 20
                    elif reaction.emoji == u"\u2B05" and current_page > 1:
                        low -= 20
                        high -= 20
                        current_page -= 1
                    elif reaction.emoji == u"\u27A1" and current_page < max_page:
                        low += 20
                        high += 20
                        current_page += 1
                    elif reaction.emoji == u"\u23E9":
                        current_page = max_page
                        low = ((20 * max_page) - 19)
                        high = (20 * max_page)
                    for button in buttons:
                        await msg.remove_reaction(button, ctx.user)
                    if current_page != previous_page:
                        cursor.execute(f"""SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}""")
                        pull = cursor.fetchall()
                        embed = discord.Embed(title=f"Fame Store Settings Page {current_page}", description=f'This is a list of the administratively defined items', colour=discord.Colour.blurple())
                        for result in pull:
                            embed.add_field(name=f'**Name**: {result[2]}', value=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}', inline=False)
                        await msg.edit(embed=embed)
    else:
        await ctx.response.send_message(f"you were trying to do the following {modify} modification in the Fame Store, but {name} was incorrect!", ephemeral=True)

@admin.command()
@app_commands.describe(modify="add, remove edit, or display something in the store.")
@app_commands.choices(modify=[discord.app_commands.Choice(name='Add', value=1), discord.app_commands.Choice(name='Remove', value=2), discord.app_commands.Choice(name='edit', value=3), discord.app_commands.Choice(name='Display', value=4)])
async def title_store(ctx: commands.Context, masculine_name: typing.Optional[str], feminine_name: typing.Optional[str], fame: typing.Optional[int], effect: typing.Optional[str], ubb_id: typing.Optional[str], modify: discord.app_commands.Choice[int] = 4):
    """add, edit, remove, or display something from one of the stores"""
    guild_id = ctx.guild_id
    ubb_id = ubb_id.strip() if ubb_id is not None else None
    fame = 0 if fame is None else fame
    modify = 4 if modify == 4 else modify.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = ctx.user.name
    cursor.execute(f"SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title where Masculine_Name = ? OR Feminine_Name = ?", (masculine_name, feminine_name))
    item_info = cursor.fetchone()
    cursor.close()
    db.close()
    if item_info is None and modify == 1:
        await EventCommand.add_title_store(self, guild_id, author, ubb_id, effect, fame, masculine_name, feminine_name)
        embed = discord.Embed(title=f"New Title Store Item", description=f'{masculine_name}/{feminine_name} has been added to the title store!', colour=discord.Colour.blurple())
        embed.add_field(name=f'**description:**', value=f'{effect}', inline=False)
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 2:
        await EventCommand.remove_title_store(self, guild_id, author, item_info[2], item_info[3], item_info[4])
        embed = discord.Embed(title=f"Removed Title Store Item", description=f'{masculine_name}/{feminine_name} has been removed from the title store!', colour=discord.Colour.blurple())
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 3:
        await EventCommand.edit_title_store(self, guild_id, author, ubb_id, effect, fame, masculine_name, feminine_name)
        embed = discord.Embed(title=f"Edited Title Store Item", description=f'{masculine_name}/{feminine_name} has been edited in the title store!', colour=discord.Colour.blurple())
        embed.add_field(name=f'**description:**', value=f'{effect}', inline=False)
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif modify == 4:
        if item_info is not None:
            embed = discord.Embed(title=f"Title Store Item: {item_info[3]}/{item_info[4]}", description=f'**ID**: {item_info[0]}, **Effect**: {item_info[1]}, **Rewarded Fame**: {item_info[2]}', colour=discord.Colour.blurple())
            await ctx.response.send_message(embed=embed)
        else:
            db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
            cursor = db.cursor()
            buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
            cursor.execute(f"""SELECT COUNT(masculine_name) FROM Store_Title""")
            admin_count = cursor.fetchone()
            max_page = math.ceil(admin_count[0] / 20)
            current_page = 1
            low = 1 + ((current_page - 1) * 20)
            high = 20 + ((current_page - 1) * 20)
            cursor.execute(f"""SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}""")
            pull = cursor.fetchall()
            embed = discord.Embed(title=f"Title Store Settings Page {current_page}", description=f'This is a list of the administratively defined items', colour=discord.Colour.blurple())
            for result in pull:
                embed.add_field(name=f"Title Store Item: {result[3]}/{result[4]}", value=f'**ID**: {result[0]}, **Effect**: {result[1]}, **Rewarded Fame**: {result[2]}', inline=False)
            await ctx.response.send_message(embed=embed)
            msg = await ctx.original_response()
            for button in buttons:
                await msg.add_reaction(button)
            while True:
                try:
                    reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
                except asyncio.TimeoutError:
                    embed.set_footer(text="Request has timed out.")
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                    cursor.close()
                    db.close()
                    return print("timed out")
                else:
                    previous_page = current_page
                    if reaction.emoji == u"\u23EA":
                        current_page = 1
                        low = 1
                        high = 20
                    elif reaction.emoji == u"\u2B05" and current_page > 1:
                        low -= 20
                        high -= 20
                        current_page -= 1
                    elif reaction.emoji == u"\u27A1" and current_page < max_page:
                        low += 20
                        high += 20
                        current_page += 1
                    elif reaction.emoji == u"\u23E9":
                        current_page = max_page
                        low = ((20 * max_page) - 19)
                        high = (20 * max_page)
                    for button in buttons:
                        await msg.remove_reaction(button, ctx.user)
                    if current_page != previous_page:
                        cursor.execute(f"""SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}""")
                        pull = cursor.fetchall()
                        embed = discord.Embed(title=f"Title Store Settings Page {current_page}", description=f'This is a list of the administratively defined items', colour=discord.Colour.blurple())
                        for result in pull:
                            embed.add_field(name=f"Title Store Item: {result[3]}/{result[4]}", value=f'**ID**: {result[0]}, **Effect**: {result[1]}, **Rewarded Fame**: {result[2]}', inline=False)
                        await msg.edit(embed=embed)
    else:
        await ctx.response.send_message(f"you were trying to do the following {modify} modification in the title store, but {masculine_name} was incorrect!", ephemeral=True)


@admin.command()
async def watest(ctx: commands.Context):
    """This is a test command for the wa command."""
    await ctx.response.send_message("This is a test command for the wa command.")
    client = WaClient(
        'Pathparser',
        'https://github.com/Solfyrism/Pathparser',
        'V1.1',
        os.getenv('WORLD_ANVIL_API'),
        os.getenv('WORLD_ANVIL_USER')
    )
#    timeline = client.timeline.get('906c8c14-2283-47e0-96e2-0fcd9f71d0d0', granularity=str(1))
#    print(timeline)
    history = client.history.get('76c474c1-c1db-4587-ab62-471e3a29f55f', granularity=str(2))
    print(history)
#    category = client.category.get('a9eee0b7-6121-4680-aa43-f128b8c19506', granularity=str(1))
#    print(category)
#    authenticated_user = client.user.identity()
#    print(f"I am the authenticated user of {authenticated_user}")
#    worlds = [world for world in client.user.worlds(authenticated_user['id'])]
#    print(f"This is my World: {worlds}")
#    categories = [category for category in client.world.categories('f7a60480-ea15-4867-ae03-e9e0c676060a')]
#    print(f"this category contains the following categories {categories}")
#    articles = [article for article in client.world.articles('f7a60480-ea15-4867-ae03-e9e0c676060a', 'b71f939a-f72d-413b-b4d7-4ebff1e162ca')]
#    print(articles)
    specific_article = client.article.get('3e958a12-25f5-40cc-a421-b1121a357ba7', granularity=str(1))
    print(f"THIS IS {specific_article}")
#    print(f"Content for  {specific_article['content']}")
#    world_id = 'f7a60480-ea15-4867-ae03-e9e0c676060a'


@settlement.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Settlement Help", description=f'This is a list of Settlement help commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Claim**', value=f'The command for a player to claim a new settlement.', inline=False)
    embed.add_field(name=f'**Destroy**', value=f'The command for a player to release their settlement.', inline=False)
    embed.add_field(name=f'**Modify**', value=f'The command for a player to modify the properties of a settlement.', inline=False)
    embed.add_field(name=f'**Detail**', value=f'The detailed display of the buildings in a settlement.', inline=False)
    embed.add_field(name=f'**DisplayOne**', value=f'The kingdom display of a settlement.', inline=False)
    embed.add_field(name=f'**DisplayAll**', value=f'Displays all settlements owned by the kingdom.', inline=False)
    await ctx.response.send_message(embed=embed)


@settlement.command()
async def claim(ctx: commands.Context, kingdom: str, password: str, settlement: str):
    """This allows the kingdom to claim a new settlement."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Settlement FROM Settlements WHERE Settlement = '{settlement}' AND Kingdom = '{kingdom}'""", {'settlement': settlement, 'kingdom': kingdom})
    settlement_result = cursor.fetchone()
    cursor.execute(f"""SELECT kingdom, password FROM kingdoms WHERE Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_result = cursor.fetchone()
    cursor.close()
    db.close()
    if kingdom_result is None:
        await ctx.response.send_message(f'{kingdom} does not exist!')
    if kingdom_result[1] != password:
        await ctx.response.send_message(f'The password you used was incorrect for the kingdom of {kingdom}!')
    if settlement_result is not None:
        status = f"You cannot claim the same settlement of {settlement} a second time for your kingdom of {kingdom}"
        await ctx.response.send_message(status)
    if settlement_result is None and kingdom_result[1] == password:
        status = f"You have claimed {settlement} for your kingdom of {kingdom}"
        await ctx.response.send_message(status)
        await EventCommand.claim_settlement(self, kingdom, settlement, guild_id, author)


@settlement.command()
async def destroy(ctx: commands.Context, kingdom: str, password: str, settlement: str):
    """This allows a kingdom to remove its claim to a settlement and void its holdings."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Settlement FROM Settlements WHERE Settlement = '{settlement}' AND Kingdom = '{kingdom}'""", {'Kingdom': kingdom, 'Settlement': settlement})
    settlement_result = cursor.fetchone()
    cursor.execute(f"""SELECT Kingdom, Password FROM kingdoms WHERE Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_result = cursor.fetchone()
    cursor.close()
    db.close()
    if kingdom_result is None:
        await ctx.response.send_message(f'{kingdom} is not a valid kingdom.')
    elif kingdom_result[1] != password:
        await ctx.response.send_message(f'you have submitted an invalid password for {kingdom}')
    elif settlement_result is not None and kingdom_result[1] == password:
        status = f"Your kingdom of {kingdom} has let their control over the settlement of {settlement} lapse."
        await EventCommand.destroy_settlement(self, kingdom, settlement, guild_id, author)
        await ctx.response.send_message(status)
    elif settlement_result is None:
        status = f"You cannot have {kingdom} make a war crime out of {settlement} if it doesn't exist!"
        await ctx.response.send_message(status)


# noinspection PyTypeChecker
@settlement.command()
async def modify(ctx: commands.Context, kingdom: str, password: str, old_settlement: str, new_settlement: str):
    """This will modify the name of a settlement by the kingdom owner."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    old_settlement = str.replace(str.title(old_settlement), ";", "")
    new_settlement = str.replace(str.title(new_settlement), ";", "")
    password = str.replace(str.title(password), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Settlement FROM Settlements WHERE Settlement = '{old_settlement}' AND Kingdom = '{kingdom}'""", {'Settlement': old_settlement, 'Kingdom': kingdom})
    result = cursor.fetchone()
    cursor.execute(f"""SELECT Kingdom, Password FROM kingdoms WHERE Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_result = cursor.fetchone()
    cursor.close()
    db.close()
    if kingdom_result is None:
        await ctx.response.send_message(f'{kingdom} is not a valid kingdom.')
    elif kingdom_result[1] != password:
        await ctx.response.send_message(f'you have submitted an invalid password for {kingdom}')
    if result is None:
        status = f"You cannot modify a settlement which doesn't exist!"
        await ctx.response.send_message(status)
    if result is not None and password == kingdom_result[1]:
        status = f"Congratulations you have changed the settlement from {old_settlement} to {new_settlement}"
        await ctx.response.send_message(status)
        await EventCommand.modify_settlement(self, kingdom, old_settlement, new_settlement, guild_id, author)


@settlement.command()
async def detail(ctx: commands.Context, kingdom: str, settlement: str, current_page: int = 1):
    """This will offer the detailed view of a settlement and it's buildings"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    cursor.execute(f"""SELECT COUNT(building) FROM Buildings WHERE Kingdom = '{kingdom}' AND Settlement = '{settlement}'""", {'Kingdom': kingdom, 'Settlement': settlement})
    blueprint_count = cursor.fetchone()
    max_page = math.ceil(blueprint_count[0] / 5)
    if current_page >= max_page:
        current_page = max_page
    low = 1 + ((current_page-1) * 5)
    high = 5 + ((current_page-1) * 5)
    cursor.execute(f"""SELECT Building, Constructed, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_value, Spellcasting, Supply from Buildings WHERE Kingdom = '{kingdom}' AND Settlement = '{settlement}' AND ROWID BETWEEN {low} and {high}""", {'Kingdom': kingdom, 'Settlement': settlement})
    pull = cursor.fetchall()
    embed = discord.Embed(title=f"Buildings page {current_page}", description=f'This is list of constructed buildings in the settlement of {settlement} in kingdom of {kingdom}', colour=discord.Colour.blurple())
    for result in pull:
        embed.add_field(name=f'Buildings Info', value=f'***__Building__***: {result[0]}, **Constructed**: {result[1]}, **Lots occupied**: {result[2]}, **Supply**: {result[18]}', inline=False)
        embed.add_field(name=f'Kingdom Benefits', value=f'**Economy**: {result [3]}, **Loyalty**: {result[4]}, **Stability**: {result[5]}, **Fame:**: {result[6]}, **Unrest**: {result[7]}', inline=False)
        embed.add_field(name=f'Settlement Benefits', value=f'**Corruption:**: {result[8]}, **Crime**: {result[9]}, **Productivity**: {result[10]}, **Law**: {result[11]}, **Lore**: {result[12]}, **Society**: {result[13]}', inline=False)
        embed.add_field(name=f'Settlement Risks', value=f'**Danger**: {result[14]} **Defence**: {result[15]}')
        embed.add_field(name=f'Settlement Economy', value=f'**Base Value**: {result[16]}, **Spellcasting**: {result[17]}')
        embed.add_field(name=f'Settlement Limitation', value=f'**Settlement Limit**: {result[19]}, **District Limit**: {result[20]}')
        embed.add_field(name=f'Blueprint Description', value=f'{result[21]}', inline=False)
    await ctx.response.send_message(embed=embed)
    msg = await ctx.original_response()
    for button in buttons:
        await msg.add_reaction(button)
    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
        except asyncio.TimeoutError:
            embed.set_footer(text="Request has timed out.")
            await msg.edit(embed=embed)
            await msg.clear_reactions()
            cursor.close()
            db.close()
            return print("timed out")
        else:
            previous_page = current_page
            if reaction.emoji == u"\u23EA":
                current_page = 1
                low = 1
                high = 5
            elif reaction.emoji == u"\u2B05" and current_page > 1:
                low -= 5
                high -= 5
                current_page -= 1
            elif reaction.emoji == u"\u27A1" and current_page < max_page:
                low += 5
                high += 5
                current_page += 1
            elif reaction.emoji == u"\u23E9":
                current_page = max_page
                low = ((5 * max_page) - 4)
                high = (5 * max_page)
            for button in buttons:
                await msg.remove_reaction(button, ctx.user)
            if current_page != previous_page:
                cursor.execute(f"""SELECT Building, Build_Points, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence Base_value, Spellcasting, Supply, Settlement_limit, District_Limit, Description from Buildings WHERE Kingdom = '{kingdom}' AND Settlement = '{settlement}' AND ROWID BETWEEN {low} and {high}""", {'Kingdom': kingdom, 'Settlement': settlement})
                edit_pull = cursor.fetchall()
                embed = discord.Embed(title=f"Buildings page {current_page}", description=f'This is list of constructed buildings in the settlement of {settlement} in kingdom of {kingdom}', colour=discord.Colour.blurple())
                for result in edit_pull:
                    embed.add_field(name=f'Buildings Info', value=f'***__Building__***: {result[0]}, **Constructed**: {result[1]}, **Lots occupied**: {result[2]}, **Supply**: {result[18]}', inline=False)
                    embed.add_field(name=f'Kingdom Benefits', value=f'**Economy**: {result[3]}, **Loyalty**: {result[4]}, **Stability**: {result[5]}, **Fame:**: {result[6]}, **Unrest**: {result[7]}', inline=False)
                    embed.add_field(name=f'Settlement Benefits', value=f'**Corruption:**: {result[8]}, **Crime**: {result[9]}, **Productivity**: {result[10]}, **Law**: {result[11]}, **Lore**: {result[12]}, **Society**: {result[13]}', inline=False)
                    embed.add_field(name=f'Settlement Risks', value=f'**Danger**: {result[14]} **Defence**: {result[15]}')
                    embed.add_field(name=f'Settlement Economy', value=f'**Base Value**: {result[16]}, **Spellcasting**: {result[17]}')
                    embed.add_field(name=f'Settlement Limitation', value=f'**Settlement Limit**: {result[19]}, **District Limit**: {result[20]}')
                    embed.add_field(name=f'Blueprint Description', value=f'{result[21]}', inline=False)
                await msg.edit(embed=embed)

"""This calls all buildings in a settlement"""


@settlement.command()
async def displayall(ctx: commands.Context, kingdom: str, settlement: str, current_page: int = 1):
    """This will display all settlements associated to a kingdom."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT COUNT(Settlement) FROM Settlements WHERE Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
    settlement_count = cursor.fetchone()
    max_page = math.ceil(settlement_count[0] / 5)
    if current_page >= max_page:
        current_page = max_page
    low = 1 + ((current_page-1) * 5)
    high = 5 + ((current_page-1) * 5)
    cursor.execute(f"""SELECT Settlement, size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay FROM Settlements WHERE Kingdom = '{kingdom}' AND ROWID BETWEEN {low} and {high}""", {'Kingdom': kingdom})
    pull = cursor.fetchall()
    embed = discord.Embed(title=f"Settlements page {current_page}", description=f'This is list of settlements in {kingdom}', colour=discord.Colour.blurple())
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    decay = cursor.fetchone()
    if decay[0]:  # IF THE SERVER HAS DECAY ON
        for result in pull:
            embed.add_field(name=f'Settlement info', value=f'**Settlement**: {result[0]}, **Districts**: {result[1]} **Population**: {result[2]}, **Supply**: {result[13]}, **Decay**: {result[14]}', inline=False)
            embed.add_field(name=f'Settlement Benefits', value=f'**Corruption**: {result[3]}, **Crime**: {result[4]}, **Productivity**: {result[5]}, **Law**: {result[6]}, **Lore**: {result[7]}, **Society**: {result[8]}', inline=False)
            embed.add_field(name=f'Settlement Misc', value=f'**Danger**: {result[9]}, **Defence**: {result[10]} **Base_Value**: {result[11]} **Spellcasting**: {result[12]}, ', inline=False)
    else:
        for result in pull:
            embed.add_field(name=f'Settlement info', value=f'**Settlement**: {result[0]}, **Districts**: {result[1]} **Population**: {result[2]}, **Supply**: {result[13]}', inline=False)
            embed.add_field(name=f'Settlement Benefits', value=f'**Corruption**: {result[3]}, **Crime**: {result[4]}, **Productivity**: {result[5]}, **Law**: {result[6]}, **Lore**: {result[7]}, **Society**: {result[8]}', inline=False)
            embed.add_field(name=f'Settlement Misc', value=f'**Danger**: {result[9]}, **Defence**: {result[10]} **Base_Value**: {result[11]} **Spellcasting**: {result[12]}, ', inline=False)
    await ctx.response.send_message(embed=embed)
    msg = await ctx.original_response()
    for button in buttons:
        await msg.add_reaction(button)
    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
        except asyncio.TimeoutError:
            embed.set_footer(text="Request has timed out.")
            await msg.edit(embed=embed)
            await msg.clear_reactions()

            cursor.close()
            db.close()
            return print("timed out")
        else:
            previous_page = current_page
            if reaction.emoji == u"\u23EA":
                current_page = 1
                low = 1
                high = 5
            elif reaction.emoji == u"\u2B05" and current_page > 1:
                low -= 5
                high -= 5
                current_page -= 1
            elif reaction.emoji == u"\u27A1" and current_page < max_page:
                low += 5
                high += 5
                current_page += 1
            elif reaction.emoji == u"\u23E9":
                current_page = max_page
                low = ((5 * max_page) - 4)
                high = (5 * max_page)
            for button in buttons:
                await msg.remove_reaction(button, ctx.user)
            if current_page != previous_page:
                cursor.execute(f"""SELECT Settlement, size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay FROM Settlements WHERE Kingdom = '{kingdom}' AND ROWID BETWEEN {low} and {high}""", {'Kingdom': kingdom})
                edit_pull = cursor.fetchall()
                embed = discord.Embed(title=f"Settlements page {current_page}", description=f'This is list of settlements in {kingdom}', colour=discord.Colour.blurple())
                if decay[0]:  # IF THE SERVER HAS DECAY ON
                    for result in pull:
                        embed.add_field(name=f'Settlement info', value=f'**Settlement**: {result[0]}, **Districts**: {result[1]} **Population**: {result[2]}, **Supply**: {result[13]}, **Decay**: {result[14]}', inline=False)
                        embed.add_field(name=f'Settlement Benefits', value=f'**Corruption**: {result[3]}, **Crime**: {result[4]}, **Productivity**: {result[5]}, **Law**: {result[6]}, **Lore**: {result[7]}, **Society**: {result[8]}', inline=False)
                        embed.add_field(name=f'Settlement Misc', value=f'**Danger**: {result[9]}, **Defence**: {result[10]} **Base_Value**: {result[11]} **Spellcasting**: {result[12]}, ', inline=False)
                else:
                    for result in pull:
                        embed.add_field(name=f'Settlement info', value=f'**Settlement**: {result[0]}, **Districts**: {result[1]} **Population**: {result[2]}, **Supply**: {result[13]}', inline=False)
                        embed.add_field(name=f'Settlement Benefits', value=f'**Corruption**: {result[3]}, **Crime**: {result[4]}, **Productivity**: {result[5]}, **Law**: {result[6]}, **Lore**: {result[7]}, **Society**: {result[8]}', inline=False)
                        embed.add_field(name=f'Settlement Misc', value=f'**Danger**: {result[9]}, **Defence**: {result[10]} **Base_Value**: {result[11]} **Spellcasting**: {result[12]}, ', inline=False)
                await msg.edit(embed=embed)
"""This is a Settlement shop"""


@settlement.command()
async def displayone(ctx: commands.Context, kingdom: str, settlement: str, custom_stats: bool = False):
    """This will display a singular settlement, and it's basic information"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    decay = cursor.fetchone()
    if custom_stats is False:
        cursor.execute(f"""SELECT Size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay from Settlements where Kingdom = '{kingdom}' and Settlement = '{settlement}'""", {'Kingdom': kingdom, 'Settlement': settlement})
        settlement_info = cursor.fetchone()
        cursor.execute(f"""SELECT Government, Alignment from Kingdoms where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
        kingdom_info = cursor.fetchone()
        if kingdom_info is None:
            await ctx.response.send_message(f'The kingdom of {kingdom} could not be found.')
        if settlement_info is None:
            await ctx.response.send_message(f'The settlement of {settlement} could not be found underneath the kingdom of {kingdom}.')
        if kingdom_info is not None and settlement_info is not None:
            embed = discord.Embed(title=f"Settlement {Settlement} of kingdom {kingdom}", description=f'Here is the full view of this Settlement', colour=discord.Colour.blurple())
            embed.add_field(name=f'Government', value=f'{kingdom_info[0]}')
            embed.add_field(name=f'Alignment', value=f'{kingdom_info[1]}')
            embed.add_field(name=f'Size', value=f'{settlement_info[0]}', inline=False)
            embed.add_field(name=f'Population', value=f'{settlement_info[1]}')
            embed.add_field(name=f'Corruption', value=f'{settlement_info[2]}')
            embed.add_field(name=f'Crime', value=f'{settlement_info[3]}')
            embed.add_field(name=f'Productivity', value=f'{settlement_info[4]}')
            embed.add_field(name=f'Law', value=f'{settlement_info[5]}')
            embed.add_field(name=f'Lore', value=f'{settlement_info[6]}')
            embed.add_field(name=f'Society', value=f'{settlement_info[7]}')
            embed.add_field(name=f'Danger', value=f'{settlement_info[8]}')
            embed.add_field(name=f'Defence', value=f'{settlement_info[9]}')
            embed.add_field(name=f'Base_Value', value=f'{settlement_info[10]}')
            embed.add_field(name=f'Spellcasting', value=f'{settlement_info[11]}')
            embed.add_field(name=f'Supply', value=f'{settlement_info[12]}')
            if decay[0]:  # IF THE SERVER HAS DECAY ON
                embed.add_field(name=f'Decay', value=f'{settlement_info[15]}')
            await ctx.response.send_message(embed=embed)
    if custom_stats is True:
        cursor.execute(f"""SELECT Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply from Settlements_Custom where Kingdom = '{kingdom}' and Settlement = '{settlement}'""", {'Kingdom': kingdom, 'Settlement': settlement})
        kingdom_info = cursor.fetchone()
        if kingdom_info is None:
            await ctx.response.send_message(f'The settlement of {settlement} underneath kingdom of {kingdom_info} could not be found.')
        if kingdom_info is not None:
            embed = discord.Embed(title=f"Settlement of {settlement} underneath kingdom of {kingdom}", description=f'Here is the full view of this Custom Information for this Settlement', colour=discord.Colour.blurple())
            embed.add_field(name=f'Corruption', value=f'{kingdom_info[0]}')
            embed.add_field(name=f'Crime', value=f'{kingdom_info[1]}')
            embed.add_field(name=f'Productivity', value=f'{kingdom_info[2]}')
            embed.add_field(name=f'Law', value=f'{kingdom_info[3]}')
            embed.add_field(name=f'Lore', value=f'{kingdom_info[4]}')
            embed.add_field(name=f'Society', value=f'{kingdom_info[5]}')
            embed.add_field(name=f'Danger', value=f'{kingdom_info[6]}')
            embed.add_field(name=f'Defence', value=f'{kingdom_info[7]}')
            embed.add_field(name=f'Base_Value', value=f'{kingdom_info[8]}')
            embed.add_field(name=f'Spellcasting', value=f'{kingdom_info[9]}')
            await ctx.response.send_message(embed=embed)
    cursor.close()
    db.close()
"""This calls a specific settlement or custom info"""


@buildings.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Building Help", description=f'This is a list of Settlement help commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Shop**', value=f'Display all known blueprints that can be built.', inline=False)
    embed.add_field(name=f'**Build**', value=f'Build a building based off of a known blueprint.', inline=False)
    embed.add_field(name=f'**Destroy**', value=f'Destroy a building based off of one in your settlement.', inline=False)
    await ctx.response.send_message(embed=embed)


@buildings.command()
async def shop(ctx: commands.Context, current_page: int = 1, building: str = 'All'):
    """displays the buildings in store, or a specific building."""
    building = str.replace(str.title(building), ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if building == 'All':
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        cursor.execute(f"""SELECT COUNT(building) FROM Buildings_Blueprints""")
        blueprint_count = cursor.fetchone()
        max_page = math.ceil(blueprint_count[0] / 4)
        if current_page >= max_page:
            current_page = max_page
        low = 1 + ((current_page-1) * 4)
        high = 4 + ((current_page-1) * 4)
        cursor.execute(f"""SELECT Building, Build_Points, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_value, Spellcasting, Supply, Settlement_limit, District_Limit, Description from Buildings_Blueprints WHERE ROWID BETWEEN {low} and {high}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"Blueprints page {current_page}", description=f'This is list of blueprints', colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f'Blueprint info', value=f'***__Blueprint__***: {result[0]}, **build_points**: {result[1]}, **Lots**: {result[2]}, **Supply**: {result[18]}', inline=False)
            embed.add_field(name=f'Kingdom Benefits', value=f'**Economy**: {result [3]}, **Loyalty**: {result[4]}, **Stability**: {result[5]}, **Fame:**: {result[6]}, **Unrest**: {result[7]}', inline=False)
            embed.add_field(name=f'Settlement Benefits', value=f'**Corruption:**: {result[8]}, **Crime**: {result[9]}, **Productivity**: {result[10]}, **Law**: {result[11]}, **Lore**: {result[12]}, **Society**: {result[13]}', inline=False)
            embed.add_field(name=f'Settlement Misc', value=f'**Danger**: {result[14]}, **Defence**: {result[15]}, **Base Value**: {result[16]}, **Spellcasting**: {result[17]}')
            embed.add_field(name=f'Settlement Limitation', value=f'**Settlement Limit**: {result[19]}, **District Limit**: {result[20]}')
            embed.add_field(name=f'Blueprint Description', value=f'{result[21]}', inline=False)
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                return print("timed out")
            else:
                previous_page = current_page
                if reaction.emoji == u"\u23EA":
                    current_page = 1
                    low = 1
                    high = 4
                elif reaction.emoji == u"\u2B05" and current_page > 1:
                    low -= 4
                    high -= 4
                    current_page -= 1
                elif reaction.emoji == u"\u27A1" and current_page < max_page:
                    low += 4
                    high += 4
                    current_page += 1
                elif reaction.emoji == u"\u23E9":
                    current_page = max_page
                    low = ((4 * max_page) - 3)
                    high = (4 * max_page)
                for button in buttons:
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(f"""SELECT Building, Build_Points, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_value, Spellcasting, Supply, Settlement_limit, District_Limit, Description from Buildings_Blueprints WHERE ROWID BETWEEN {low} and {high}""")
                    edit_pull = cursor.fetchall()
                    embed = discord.Embed(title=f"Blueprints page {current_page}", description=f'This is list of blueprints', colour=discord.Colour.blurple())
                    for result in edit_pull:
                        embed.add_field(name=f'Blueprint info', value=f'***__Blueprint__***: {result[0]}, **build_points**: {result[1]}, **Lots**: {result[2]}, **Supply**: {result[18]}', inline=False)
                        embed.add_field(name=f'Kingdom Benefits', value=f'**Economy**: {result[3]}, **Loyalty**: {result[4]}, **Stability**: {result[5]}, **Fame:**: {result[6]}, **Unrest**: {result[7]}', inline=False)
                        embed.add_field(name=f'Settlement Benefits', value=f'**Corruption:**: {result[8]}, **Crime**: {result[9]}, **Productivity**: {result[10]}, **Law**: {result[11]}, **Lore**: {result[12]}, **Society**: {result[13]}', inline=False)
                        embed.add_field(name=f'Settlement Misc', value=f'**Danger**: {result[14]}, **Defence**: {result[15]}, **Base Value**: {result[16]}, **Spellcasting**: {result[17]}')
                        embed.add_field(name=f'Settlement Limitation', value=f'**Settlement Limit**: {result[19]}, **District Limit**: {result[20]}')
                        embed.add_field(name=f'Blueprint Description', value=f'{result[21]}', inline=False)
                    await msg.edit(embed=embed)
    if building != 'All':
        cursor.execute(f"""SELECT Build_Points, Lots, Economy, Loyalty, Stability, Fame, unrest, Corruption, Crime, Productivity, law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Settlement_Limit, District_Limit, Description FROM Buildings_Blueprints WHERE Building = '{building}'""", {'Building': building})
        result = cursor.fetchone()
        if result is None:
            await ctx.response.send_message(f"{building} is not a valid blueprints.")
        else:
            embed = discord.Embed(title=f"Blueprints page {current_page}", description=f'This is list of blueprints', colour=discord.Colour.blurple())
            embed.add_field(name=f'Blueprint info', value=f'***__Blueprint__***: {result[0]}, **build_points**: {result[1]} **Lots**: {result[2]} **Supply**: {result[18]}', inline=False)
            embed.add_field(name=f'Kingdom Benefits', value=f'**Economy**: {result[3]}, **Loyalty**: {result[4]}, **Stability**: {result[5]}, **Fame:**: {result[6]}, **Unrest**: {result[7]}', inline=False)
            embed.add_field(name=f'Settlement Benefits', value=f'**Corruption:**: {result[8]} **Crime**: {result[9]} **Productivity**: {result[10]}, **Law**: {result[11]}, **Lore**: {result[12]}, **Society**: {result[13]}', inline=False)
            embed.add_field(name=f'Alternate Modifier', value=f'**Danger**:{result[14]}, **Defence**: {result[15]}, **Base_Value**: {result[16]}, **Spellcasting**: {result[17]}', inline=False)
            embed.add_field(name=f'Settlement Limitation', value=f'**Settlement Limit**: {result[19]}, **District Limit**: {result[20]}', inline=False)
            embed.add_field(name=f'Blueprint Description', value=f'{result[21]}', inline=False)
            await ctx.response.send_message(embed=embed)
    cursor.close()
    db.close()
"""This is a shop, but can call for a specific blueprint"""


@buildings.command()
async def build(ctx: commands.Context, kingdom: str, password: str, settlement: str, building: str, amount: int):
    """Player command to build a building in a settlement."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    building = str.replace(str.title(building), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Building FROM Buildings_Blueprints WHERE Building = '{building}'""", {'building': building})
    blueprint_result = cursor.fetchone()
    cursor.execute(f"""SELECT Password FROM Kingdoms WHERE Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_result = cursor.fetchone()
    cursor.execute(f"""SELECT Settlement FROM Settlements WHERE Kingdom = '{kingdom}' AND settlement = '{settlement}'""", {'kingdom': kingdom, 'settlement': settlement})
    settlement_result = cursor.fetchone()
    cursor.close()
    db.close()
    if blueprint_result is None:
        status = f"You cannot build a building based off a blueprint which hasn't been allowed!"
        await ctx.response.send_message(status)
    if kingdom_result is None:
        await ctx.response.send_message(f'{kingdom} was not a valid kingdom.')
    if settlement_result is None:
        await ctx.response.send_message(f'the kingdom of {kingdom} has no valid settlement named {settlement}')
    if kingdom_result[0] != password:
        await ctx.response.send_message(f'you attempted to use an invalid password for the kingdom of {kingdom}.')
    if blueprint_result is not None and settlement_result is not None and kingdom_result[0] == password:
        status = f"You have built {amount} of {building} within your settlement!"
        await ctx.response.send_message(status)
        await EventCommand.construct_building(self, kingdom, settlement, building, amount, guild_id, author)


@buildings.command()
async def destroy(ctx: commands.Context, kingdom: str, password: str, settlement: str, building: str, amount: int):
    """This is a command for a player to remove buildings from their settlement"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    building = str.replace(str.title(building), ";", "")
    password = str.replace(password, ";", "")
    amount = abs(amount)
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Building, Constructed FROM Buildings WHERE Building = '{building}'""", {'building': building})
    building_result = cursor.fetchone()
    cursor.execute(f"""SELECT Password FROM Kingdoms WHERE Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_result = cursor.fetchone()
    cursor.close()
    db.close()
    if kingdom_result[0] != password:
        await ctx.response.send_message(f"How dare you try to put in the incorrect password for {kingdom}!")
    elif building_result is None:
        status = f"You cannot remove a building that you haven't built!!!"
        await ctx.response.send_message(status)
    elif building_result[1] - amount < 0:
        await ctx.response.send_message(f"Brother! You cannot destroy this {amount} of {building}s! you only have {building_result[1]} built!")
    else:
        status = f"You have destroyed {amount} of {building} within your settlement of {settlement}!"
        await ctx.response.send_message(status)
        await EventCommand.destroy_building(self, kingdom, settlement, building, amount, guild_id, author)


@leadership.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Leadership Help", description=f'This is a list of Leadership commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Modify**', value=f'Update a leader, shift one leader for another, or fill or vacant spot.', inline=False)
    embed.add_field(name=f'**Remove**', value=f'Remove a leader and set their role as vacant.', inline=False)
    embed.add_field(name=f'**Display**', value=f'Display the leaders working for your settlement.', inline=False)
    await ctx.response.send_message(embed=embed)


@leadership.command()
async def modify(ctx: commands.Context, kingdom: str, password: str, leader: str, title: str, modifier: int):
    """This command changes a leader from a vacant or existing position."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    leader = str.replace(str.title(leader), ";", "")
    title = str.replace(str.title(title), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT password FROM Kingdoms WHERE kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_results = cursor.fetchone()
    if kingdom_results[0] != password:
        await ctx.response.send_message(f"BEHOLD, THE ULTIMATE POWER OF SUBMITTING THE WRONG PASSWORD FOR THE KINGDOM OF {kingdom}!")
        cursor.close()
        db.close()
        return
    if kingdom_results[0] is None:
        await ctx.response.send_message(f"The {kingdom} of kingdom apparently doesn't seem to exist!")
        cursor.close()
        db.close()
        return
    statistics = ([':red_circle: Strength', 'Strength', '🔴'], [':blue_circle: Dexterity', 'Dexterity', '🔵'], [':green_circle: Constitution', 'Constitution', '🟢'], [':purple_circle: Intelligence', 'Intelligence', '🟣'], [':yellow_circle: Wisdom', 'Wisdom', '🟡'], [':orange_circle: Charisma', 'Charisma', '🟠'])
    cursor.execute(f"""SELECT Title, Ability, Description, Economy, Loyalty, Stability FROM AA_Leadership_Roles WHERE Title = '{title}'""", {'title': title})
    result = cursor.fetchone()
    if result is None:
        await ctx.response.send_message(f"what's this! {title} doesn't exist?! Try again!")
        return
    buttons = ["🔴", "🔵", "🟢", "🟣", "🟡", "🟠"]
    buttons2 = ["🔴", "🔵", "🟢"]
    ability = result[1]
    embed = discord.Embed(title=f"{kingdom} Kingdom Leader: {title}", description=f"{result[2]}")
    for stat in statistics:
        if ability.find(f"{stat[1]}") >= 0:
            embed.add_field(name="Ability Score", value=f"{stat[0]}")
    await ctx.response.send_message(embed=embed)
    msg = await ctx.original_response()
    for stat in statistics:
        if ability.find(f"{stat[1]}") >= 0:
            await msg.add_reaction(stat[2])
    ability_score = None
    while ability_score is None:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
        except asyncio.TimeoutError:
            embed.set_footer(text="Request has timed out.")
            await msg.edit(embed=embed)
            await msg.clear_reactions()
            return print("timed out")
        else:
            if reaction.emoji == "🔴":
                ability_score = 'Strength'
            if reaction.emoji == "🔵":
                ability_score = 'Dexterity'
            if reaction.emoji == "🟢":
                ability_score = 'Constitution'
            if reaction.emoji == "🟣":
                ability_score = 'Intelligence'
            if reaction.emoji == "🟡":
                ability_score = 'Wisdom'
            if reaction.emoji == "🟠":
                ability_score = 'Charisma'
    await msg.clear_reactions()
    embed = discord.Embed(title=f"{kingdom} Kingdom Leader: {title}", description=f"{result[2]}")
    embed.add_field(name="Selected Ability Score", value=f"{ability_score}", inline=False)
    embed.add_field(name="Kingdom Role Multipliers", value=" ", inline=False)
    embed.add_field(name="Economy", value=f":red_circle: {result[3]}")
    embed.add_field(name="Loyalty", value=f":blue_circle: {result[4]}")
    embed.add_field(name="Stability", value=f":green_circle: {result[5]}")
    await msg.edit(embed=embed)
    for button2 in buttons2:
        await msg.add_reaction(button2)
    kingdom_modifier = None
    while kingdom_modifier is None:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons2, timeout=60.0)
        except asyncio.TimeoutError:
            embed.set_footer(text="Request has timed out.")
            await msg.edit(embed=embed)
            await msg.clear_reactions()
            return print("timed out")
        else:
            if reaction.emoji == "🔴":
                kingdom_modifier = 'Economy'
                stat_modifier = modifier * result[3]
                economy_modifier = modifier * result[3]
                loyalty_modifier = 0
                stability_modifier = 0
            elif reaction.emoji == "🔵":
                kingdom_modifier = 'Loyalty'
                stat_modifier = modifier * result[4]
                economy_modifier = 0
                loyalty_modifier = modifier * result[4]
                stability_modifier = 0
            else:
                kingdom_modifier = 'Stability'
                stat_modifier = modifier * result[5]
                economy_modifier = 0
                loyalty_modifier = 0
                stability_modifier = modifier * result[5]
        await msg.clear_reactions()
        embed = discord.Embed(title=f"{kingdom} Kingdom Leader: {title}", description=f"{result[2]}")
        embed.add_field(name=f"Leader Name:", value=f"{leader}", inline=False)
        embed.add_field(name=f"Leader Stat:", value=f"{ability_score}", inline=False)
        embed.add_field(name=f"Effective Leader Modifier:", value=f"{stat_modifier}", inline=False)
        embed.add_field(name=f"Leader Focus:", value=f"{kingdom_modifier}", inline=False)
        await msg.edit(embed=embed)
        column = kingdom_modifier
        await EventCommand.modify_leader(self, kingdom, leader, title, modifier, column, economy_modifier, loyalty_modifier, stability_modifier, guild_id, author)
    cursor.close()
    db.close()


@leadership.command()
async def remove(ctx: commands.Context, kingdom: str, password: str, title: str):
    """This command is used to remove a leader and make it a vacant position"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    title = str.replace(str.title(title), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Name, Title FROM Leadership WHERE Title = '{title}' AND Kingdom = '{kingdom}'""", {'title': title, 'kingdom': kingdom})
    leadership_results = cursor.fetchone()
    cursor.execute(f"""SELECT password FROM Kingdoms WHERE kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_results = cursor.fetchone()
    cursor.close()
    db.close()
    if kingdom_results[0] is None:
        await ctx.response.send_message(f"{kingdom} is not a kingdom that exists.")
    if leadership_results[0] is None:
        await ctx.response.send_message(f"{title} was not a valid role to remove leadership from!")
    if kingdom_results[0] != password:
        await ctx.response.send_message(f"yametikeraSTOP giving me the wrong password for the kingdom of {kingdom}!")
    if leadership_results[0] is not None and kingdom_results[0] == password:
        await EventCommand.remove_leader(self, kingdom, title, guild_id, author)
        await ctx.response.send_message(f"You have removed {leadership_results[0]} from the position of {leadership_results[1]} for {kingdom}")


@leadership.command()
async def display(ctx: commands.Context, kingdom: str, current_page: int = 1, leader: str = 'All'):
    """This command will either display all leaders for a kingdom, or a specific title."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    leader = str.replace(str.title(leader), ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if leader == 'All':
        cursor.execute(f"""SELECT COUNT(title) FROM Leadership where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
        leaders = cursor.fetchone()
        max_page = math.ceil(leaders[0] / 5)
        if current_page >= max_page:
            current_page = max_page
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        low = 0 + (5 * (current_page-1))
        offset = 10
        cursor.execute(f"""SELECT Name, Title, Stat, Modifier, Economy, Loyalty, Stability, Unrest from Leadership WHERE Kingdom = '{kingdom}' LIMIT {low}, {offset}""", {'Kingdom': kingdom})
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"{kingdom} Leadership page {current_page}", description=f"This is list of {kingdom}'s leaders", colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f'Leader info', value=f'**Name**: {result[0]}, **Title**: {result[1]}, **Stat**: {result[2]}, **Modifier**: {result[3]}', inline=False)
            embed.add_field(name=f'Kingdom Benefits', value=f'**Economy**: {result[4]}, **Loyalty**: {result[5]}, **Stability**: {result[5]}, **Unrest**: {result[7]}', inline=False)
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                return print("timed out")
            else:
                previous_page = current_page
                if reaction.emoji == u"\u23EA":
                    current_page = 1
                    low = 0 + (10 * (current_page - 1))
                    offset = 10
                elif reaction.emoji == u"\u2B05" and current_page > 1:
                    current_page -= 1
                    low = 0 + (10 * (current_page - 1))
                    offset = 10
                elif reaction.emoji == u"\u27A1" and current_page < max_page:
                    current_page += 1
                    low = 0 + (10 * (current_page - 1))
                    offset = 10
                elif reaction.emoji == u"\u23E9":
                    current_page = max_page
                    low = 0 + (10 * (current_page - 1))
                    offset = 10
                for button in buttons:
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(f"""SELECT Name, Title, Stat, Modifier, Economy, Loyalty, Stability, Unrest from Leadership WHERE Kingdom = '{kingdom}' LIMIT {low}, {offset}""")
                    edit_pull = cursor.fetchall()
                    embed = discord.Embed(title=f"{kingdom} Leadership page {current_page}", description=f"This is list of {kingdom}'s leaders", colour=discord.Colour.blurple())
                    for result in edit_pull:
                        embed.add_field(name=f'Leader info', value=f'**Name**: {result[0]}, **Title**: {result[1]}, **Stat**: {result[2]}, **Modifier**: {result[3]}', inline=False)
                        embed.add_field(name=f'Kingdom Benefits', value=f'**Economy**: {result[4]}, **Loyalty**: {result[5]}, **Stability**: {result[5]}, **Unrest**: {result[7]}', inline=False)
                    await msg.edit(embed=embed)
    elif leader != 'All':
        cursor.execute(f"""SELECT Name, Title, Stat, Modifier, Economy, Loyalty, Stability, Unrest from Leadership WHERE Kingdom = '{kingdom}' AND Title = '{leader}'""", {'Kingdom': kingdom, 'Leader': leader})
        pull = cursor.fetchone()
        if pull is None:
            cursor.execute(f"""SELECT Name, Title, Stat, Modifier, Economy, Loyalty, Stability, Unrest from Leadership WHERE Kingdom = '{kingdom}' AND Name = '{leader}'""", {'Kingdom': kingdom, 'Leader': leader})
            pull = cursor.fetchone()
            if pull is None:
                await ctx.response.send_message(f"{leader} is not a valid leader for that kingdom.")

                cursor.close()
                db.close()
                return
            else:
                embed = discord.Embed(title=f"{kingdom}'s {leader}", description=f"This is {kingdom}'s {leader}: {pull[0]}", colour=discord.Colour.blurple())
                embed.add_field(name=f'Leader info', value=f'**Name**: {pull[0]}, **Title**: {pull[1]}, **Stat**: {pull[2]}, **Modifier**: {pull[3]}', inline=False)
                embed.add_field(name=f'Kingdom Benefits', value=f'**Economy**: {pull[4]}, **Loyalty**: {pull[5]}, **Stability**: {pull[5]}, **Unrest**: {pull[6]}', inline=False)
                await ctx.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title=f"{kingdom}'s {leader}", description=f"This is {kingdom}'s {leader}: {pull[0]}", colour=discord.Colour.blurple())
            embed.add_field(name=f'Leader info', value=f'**Name**: {pull[0]}, **Title**: {pull[1]}, **Stat**: {pull[2]}, **Modifier**: {pull[3]}', inline=False)
            embed.add_field(name=f'Kingdom Benefits', value=f'**Economy**: {pull[4]}, **Loyalty**: {pull[5]}, **Stability**: {pull[5]}, **Unrest**: {pull[6]}', inline=False)
            await ctx.response.send_message(embed=embed)
    cursor.close()
    db.close()
"""we can make this do "All leaders" or "A" leader because this shouldn't require all info."""
# I could potentially make this have a VACANT check and show all vacancies in a kingdom.

# @bot.hybrid_group(fallback="help")
# async def hex(ctx):
#    await ctx.response.send_message(f"This is for hex management for the kingdom!")


@hex.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Hex Help", description=f'This is a list of Hex administration commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Claim**', value=f'Claim an unclaimed hex to be able to improvement.', inline=False)
    embed.add_field(name=f'**Remove**', value=f'Remove a claimed not improved hex from your kingdoms possession.', inline=False)
    embed.add_field(name=f'**Improve**', value=f'Add an upgrade or improvement to a hex.', inline=False)
    embed.add_field(name=f'**Diminish**', value=f'Remove an upgrade or improvement on a hex.', inline=False)
    embed.add_field(name=f'**Improvements**', value=f'Display the improved hexes that a kingdom has claimed.', inline=False)
    embed.add_field(name=f'**Store**', value=f'Display the hex improvement list available.', inline=False)
    await ctx.response.send_message(embed=embed)


@hex.command()
@app_commands.describe(hex_terrain='What kind of hex terrain are you claiming?')
@app_commands.choices(hex_terrain=[discord.app_commands.Choice(name='Cavernous', value=1), discord.app_commands.Choice(name='Coastline', value=2), discord.app_commands.Choice(name='Desert', value=3), discord.app_commands.Choice(name='Forest', value=4), discord.app_commands.Choice(name='Hills', value=5), discord.app_commands.Choice(name='jungle', value=6), discord.app_commands.Choice(name='Marsh', value=7), discord.app_commands.Choice(name='Mountains', value=8), discord.app_commands.Choice(name='Plains', value=9), discord.app_commands.Choice(name='Water', value=10)])
async def claim(ctx: commands.Context, kingdom: str, password: str, hex_terrain: discord.app_commands.Choice[int]):
    """This command is used to claim a new hex for a kingdom."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    hex_terrain = str.replace(str.title(hex_terrain), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    if hex_terrain == 1:
        hex_terrain = 1
    else:
        hex_terrain = hex_terrain.value
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_results = cursor.fetchone()
    cursor.execute(f"""SELECT Hex_Terrain FROM AA_Hex_Terrains WHERE Hex_Terrain = '{hex_terrain}'""", {'Hex_Terrain': hex_terrain})
    hex_results = cursor.fetchone()
    cursor.close()
    db.close()
    if kingdom_results is None:
        status = f"You cannot claim hexes for {kingdom} when it is a kingdom which doesn't exist!"
        await ctx.response.send_message(status)
    if password != kingdom_results[1]:
        await ctx.response.send_message(f"You have submitted the wrong password for the kingdom of {kingdom}!")
    if hex_results is None:
        await ctx.response.send_message(f"you cannot claim hexes of the {hex_terrain} hex terrain! it doesn't exist!")
    if kingdom_results is not None and password == kingdom_results[1] and hex_results is not None:
        status = f"You have claimed a hex for the kingdom of {kingdom}"
        await EventCommand.claim_hex(self, kingdom, hex_terrain, guild_id, author)
        await ctx.response.send_message(status)


@hex.command()
@app_commands.describe(hex_terrain='What kind of hex terrain are you claiming?')
@app_commands.choices(hex_terrain=[discord.app_commands.Choice(name='Cavernous', value=1), discord.app_commands.Choice(name='Coastline', value=2), discord.app_commands.Choice(name='Desert', value=3), discord.app_commands.Choice(name='Forest', value=4), discord.app_commands.Choice(name='Hills', value=5), discord.app_commands.Choice(name='jungle', value=6), discord.app_commands.Choice(name='Marsh', value=7), discord.app_commands.Choice(name='Mountains', value=8), discord.app_commands.Choice(name='Plains', value=9), discord.app_commands.Choice(name='Water', value=10)])
async def remove(ctx: commands.Context, kingdom: str, password: str, hex_terrain: discord.app_commands.Choice[int]):
    """This will remove an unimproved hex from play."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    if hex_terrain == 1:
        hex_terrain = 1
    else:
        hex_terrain = hex_terrain.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': {kingdom}})
    kingdom_results = cursor.fetchone()
    cursor.execute(f"""SELECT Kingdom, Hex_Terrain FROM Hexes WHERE Kingdom = '{kingdom}' AND Hex_Terrain = '{hex_terrain}' AND Improvement = 'None'""", {'kingdom': kingdom, 'Hex_Terrain': hex_terrain})
    hex_results = cursor.fetchone()
    cursor.close()
    db.close()
    if kingdom_results is None:
        status = f"You cannot claim hexes for {kingdom} when it is a kingdom which doesn't exist!"
        await ctx.response.send_message(status)
    if password != kingdom_results[1]:
        await ctx.response.send_message(f"You have submitted the wrong password for the kingdom of {kingdom}!")
    if hex_results is None:
        await ctx.response.send_message(f"you do not have any unimproved hexes of the {hex_terrain} hex terrain to release!")
    if kingdom_results is not None and password == kingdom_results[1] and hex_results is not None:
        status = f"You have released a hex from the kingdom of {kingdom}"
        await EventCommand.relinquish_hex(self, kingdom, hex_terrain, guild_id, author)
        await ctx.response.send_message(status)


@hex.command()
@app_commands.describe(hex_terrain='What kind of terrain are you applying this to? ')
@app_commands.choices(hex_terrain=[discord.app_commands.Choice(name='Cavernous', value=1), discord.app_commands.Choice(name='Coastline', value=2), discord.app_commands.Choice(name='Desert', value=3), discord.app_commands.Choice(name='Forest', value=4), discord.app_commands.Choice(name='Hills', value=5), discord.app_commands.Choice(name='jungle', value=6), discord.app_commands.Choice(name='Marsh', value=7), discord.app_commands.Choice(name='Mountains', value=8), discord.app_commands.Choice(name='Plains', value=9), discord.app_commands.Choice(name='Water', value=10)])
async def improve(ctx: commands.Context, kingdom: str, password: str, hex_terrain: discord.app_commands.Choice[int], improvement: str):
    """This will improve an unused hex."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    improvement = str.replace(str.title(improvement), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    if hex_terrain == 1:
        hex_terrain = 1
    else:
        hex_terrain = hex_terrain.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'")
    kingdom_results = cursor.fetchone()
    cursor.execute(f"""SELECT {hex_terrain} FROM Hexes_Improvements where Improvement = '{improvement}'""", {'Improvement': improvement})
    improvement_result = cursor.fetchone()
    cursor.execute(f"""SELECT Amount FROM Hexes where Improvement = 'None' AND Hex_Terrain = '{hex_terrain}' AND kingdom = '{kingdom}'""")
    hex_results = cursor.fetchone()
    cursor.close()
    db.close()
    if improvement_result is not None:
        if kingdom_results is None:
            status = f"You cannot update hexes from a kingdom which doesn't exist!"
            await ctx.response.send_message(status)
        if kingdom_results is not None and kingdom_results[1] == password:
            if hex_results is not None:
                status = f"You have built a improvement on a hex for the kingdom of {kingdom}"
                await EventCommand.improve_hex(self, kingdom, hex_terrain, improvement, guild_id, author)
                await ctx.response.send_message(status)
        if kingdom_results[1] != password:
            await ctx.response.send_message(f"you have specified an incorrect password for the kingdom.")
        if hex_results is None:
            status = f"You have no available unimproved hexes of the {hex_terrain} hex terrain"
            await ctx.response.send_message(status)
    else:
        await ctx.response.send_message("The improvement could not be built on the supplied hex hex terrain.")


@hex.command()
@app_commands.describe(hex_terrain='What kind of terrain are you applying this to?')
@app_commands.choices(hex_terrain=[discord.app_commands.Choice(name='Cavernous', value=1), discord.app_commands.Choice(name='Coastline', value=2), discord.app_commands.Choice(name='Desert', value=3), discord.app_commands.Choice(name='Forest', value=4), discord.app_commands.Choice(name='Hills', value=5), discord.app_commands.Choice(name='jungle', value=6), discord.app_commands.Choice(name='Marsh', value=7), discord.app_commands.Choice(name='Mountains', value=8), discord.app_commands.Choice(name='Plains', value=9), discord.app_commands.Choice(name='Water', value=10)])
async def diminish(ctx: commands.Context, kingdom: str, password: str, hex_terrain: discord.app_commands.Choice[int], improvement: str):
    """This removes an improvement from a hex"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    improvement = str.replace(str.title(improvement), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    if hex_terrain == 1:
        hex_terrain = 1
    else:
        hex_terrain = hex_terrain.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
    kingdom_results = cursor.fetchone()
    cursor.execute(f"""SELECT Kingdom FROM Hexes where Kingdom = '{kingdom}' AND Hex_Terrain = '{hex_terrain}' AND Improvement = '{improvement}'""", {'Kingdom': kingdom, 'Hex_Terrain': hex_terrain, 'Improvement': improvement})
    hexes_results = cursor.fetchone()
    cursor.close()
    db.close()
    if kingdom_results is None:
        status = f"You cannot update hexes from a kingdom which doesn't exist!"
        await ctx.response.send_message(status)
    elif hexes_results is None:
        await ctx.response.send_message(f"You are lacking a hex that matches the {hex_terrain} hex_terrain or {improvement} improvement")
    elif kingdom_results[1] != password:
        await ctx.response.send_message(f"Your password was incorrect for the kingdom of {kingdom}")
    elif kingdom_results is not None and hexes_results is not None and kingdom_results[1] == password:
        status = f"You have removed a improvement on a hex for the kingdom of {kingdom}"
        await EventCommand.diminish_hex(self, kingdom, hex_terrain, improvement, guild_id, author)
        await ctx.response.send_message(status)


@hex.command()
async def improvements(ctx: commands.Context, kingdom: str, current_page: int = 1):
    """This command displays the constructed improvements made by a kingdom."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT COUNT(Hex_terrain) FROM Hexes where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
    leaders = cursor.fetchone()
    max_page = math.ceil(leaders[0] / 5)
    if current_page >= max_page:
        current_page = max_page
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    low = 0 + (5 * (current_page-1))
    offset = 10
    cursor.execute(f"""SELECT Hex_Terrain, Amount, Improvement, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation from Hexes WHERE Kingdom = '{kingdom}' LIMIT {low}, {offset}""", {'Kingdom': kingdom})
    pull = cursor.fetchall()
    embed = discord.Embed(title=f"{kingdom} Hex page {current_page}", description=f"This is list of the hexes owned by {kingdom}", colour=discord.Colour.blurple())
    for result in pull:
        embed.add_field(name=f'Hex Information', value=f'**Terrain**: {result[0]}, **Improvement*: {result[2]}, **Amount**: {result[1]}', inline=False)
        embed.add_field(name=f'Hex Benefits', value=f'**Economy**: {result[3]}, **Loyalty**: {result[4]}, **Stability**: {result[5]}, **Unrest**: {result[6]} **Consumption**: {result[7]} **Defence**: {result[8]}, **Taxation**: {result[9]}', inline=False)
    await ctx.response.send_message(embed=embed)
    msg = await ctx.original_response()
    for button in buttons:
        await msg.add_reaction(button)
    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
        except asyncio.TimeoutError:
            embed.set_footer(text="Request has timed out.")
            await msg.edit(embed=embed)
            await msg.clear_reactions()
            cursor.close()
            db.close()
            return print("timed out")
        else:
            previous_page = current_page
            if reaction.emoji == u"\u23EA":
                current_page = 1
                low = 0 + (10 * (current_page - 1))
                offset = 10
            elif reaction.emoji == u"\u2B05" and current_page > 1:
                current_page -= 1
                low = 0 + (10 * (current_page - 1))
                offset = 10
            elif reaction.emoji == u"\u27A1" and current_page < max_page:
                current_page += 1
                low = 0 + (10 * (current_page - 1))
                offset = 10
            elif reaction.emoji == u"\u23E9":
                current_page = max_page
                low = 0 + (10 * (current_page - 1))
                offset = 10
            for button in buttons:
                await msg.remove_reaction(button, ctx.user)
            if current_page != previous_page:
                cursor.execute(f"""SELECT Hex_Terrain, Amount, Improvement, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation from Hexes WHERE Kingdom = '{kingdom}' LIMIT {low}, {offset}""", {'Kingdom': kingdom})
                pull = cursor.fetchall()
                embed = discord.Embed(title=f"{kingdom} Hex page {current_page}", description=f"This is list of the hexes owned by {kingdom}", colour=discord.Colour.blurple())
                for result in pull:
                    embed.add_field(name=f'Hex Information', value=f'**Terrain**: {result[0]}, **Improvement*: {result[2]}, **Amount**: {result[1]}', inline=False)
                    embed.add_field(name=f'Hex Benefits', value=f'**Economy**: {result[3]}, **Loyalty**: {result[4]}, **Stability**: {result[5]}, **Unrest**: {result[6]} **Consumption**: {result[7]} **Defence**: {result[8]} **Taxation**:{result[9]}', inline=False)
                await msg.edit(embed=embed)


@hex.command()
async def store(ctx: commands.Context, current_page: int = 1):
    """This command displays all available hex improvements."""
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT COUNT(Improvement) FROM Hexes_Improvements where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
    leaders = cursor.fetchone()
    max_page = math.ceil(leaders[0] / 5)
    if current_page >= max_page:
        current_page = max_page
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    low = 0 + (5 * (current_page-1))
    offset = 10
    cursor.execute(f"""SELECT Improvement, Road_Multiplier, Build_Points, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation, Cavernous, Coastline, Desert, Forest, Hills, Jungle, Marsh, Mountains, Plains, Water from Hexes_Improvements LIMIT {low}, {offset}""", {'Kingdom': kingdom})
    pull = cursor.fetchall()
    embed = discord.Embed(title=f"Available Improvements Page {current_page}", description=f"This is list of the available hex improvements.", colour=discord.Colour.blurple())
    for result in pull:
        embed.add_field(name=f'Hex Information', value=f'**Improvement*: {result[2]}, **Cost**: {result[2]} BP', inline=False)
        embed.add_field(name=f'Hex Benefits', value=f'**Economy**: {result[3]}, **Loyalty**: {result[4]}, **Stability**: {result[5]}, **Unrest**: {result[6]} **Consumption**: {result[7]} **Defence**: {result[8]}, **Taxation**: {result[9]}', inline=False)
        embed.add_field(name=f"Buildable Terrains", value=f'**Cavernous**: {result[10]}, **Coastline**: {result[11]}, **Desert**: {result[12]}, **Forest**: {result[13]}, **Hills**: {result[14]}, **Jungle**: {result[15]}, **Marsh**: {result[16]}, **Mountains**: {result[17]}, **Plains**: {result[18]}, **Water**: {result[19]}')
    await ctx.response.send_message(embed=embed)
    msg = await ctx.original_response()
    for button in buttons:
        await msg.add_reaction(button)
    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
        except asyncio.TimeoutError:
            embed.set_footer(text="Request has timed out.")
            await msg.edit(embed=embed)
            await msg.clear_reactions()
            cursor.close()
            db.close()
            return print("timed out")
        else:
            previous_page = current_page
            if reaction.emoji == u"\u23EA":
                current_page = 1
                low = 0 + (10 * (current_page - 1))
                offset = 10
            elif reaction.emoji == u"\u2B05" and current_page > 1:
                current_page -= 1
                low = 0 + (10 * (current_page - 1))
                offset = 10
            elif reaction.emoji == u"\u27A1" and current_page < max_page:
                current_page += 1
                low = 0 + (10 * (current_page - 1))
                offset = 10
            elif reaction.emoji == u"\u23E9":
                current_page = max_page
                low = 0 + (10 * (current_page - 1))
                offset = 10
            for button in buttons:
                await msg.remove_reaction(button, ctx.user)
            if current_page != previous_page:
                cursor.execute(
                    f"""SELECT Improvement, Road_Multiplier, Build_Points, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation, Cavernous, Coastline, Desert, Forest, Hills, Jungle, Marsh, Mountains, Plains, Water from Hexes_Improvements LIMIT {low}, {offset}""",
                    {'Kingdom': kingdom})
                pull = cursor.fetchall()
                embed = discord.Embed(title=f"Available Improvements Page {current_page}", description=f"This is list of the available hex improvements.", colour=discord.Colour.blurple())
                for result in pull:
                    embed.add_field(name=f'Hex Information', value=f'**Improvement*: {result[2]}, **Cost**: {result[2]} BP', inline=False)
                    embed.add_field(name=f'Hex Benefits', value=f'**Economy**: {result[3]}, **Loyalty**: {result[4]}, **Stability**: {result[5]}, **Unrest**: {result[6]} **Consumption**: {result[7]} **Defence**: {result[8]}, **Taxation**: {result[9]}', inline=False)
                    embed.add_field(name=f"Buildable Terrains", value=f'**Cavernous**: {result[10]}, **Coastline**: {result[11]}, **Desert**: {result[12]}, **Forest**: {result[13]}, **Hills**: {result[14]}, **Jungle**: {result[15]}, **Marsh**: {result[16]}, **Mountains**: {result[17]}, **Plains**: {result[18]}, **Water**: {result[19]}')
                await msg.edit(embed=embed)


@character.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Character Help", description=f'This is a list of Character commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Register**', value=f'Register your character!', inline=False)
    embed.add_field(name=f'**Retire**', value=f'Retire a registered character!', inline=False)
    embed.add_field(name=f'**levelup**', value=f'Use Medium Jobs from the unbelievaboat shop.', inline=False)
    embed.add_field(name=f'**trialup**', value=f'Use Trial Catch Ups from the unbelievaboat shop', inline=False)
    embed.add_field(name=f'**Pouch**', value=f'Use Gold Pouches from the unbelievaboat shop.', inline=False)
    embed.add_field(name=f'**Display**', value=f'View information about a character.', inline=False)
    embed.add_field(name=f'**List**', value=f'View information about characters in a level range.', inline=False)
    embed.add_field(name=f'**Edit**', value=f'Change the Character Name, Mythweavers, Image, Nickname, Titles, Description, Oath of your character, or color of your embed.', inline=False)
    embed.add_field(name=f'**Entitle**', value=f'Use an approved title item from the unbelievaboat Store. NOTE: Your most famous title is the one that will be used.', inline=False)
    embed.add_field(name=f'**Proposition**', value=f'Use your prestigious status to proposition an act.', inline=False)
    embed.add_field(name=f'**Cap**', value=f'Stop yourself from leveling! For reasons only you understand.', inline=False)
    embed.add_field(name=f'**Backstory**', value=f'Give your character a backstory if they do not already have one.', inline=False)
    await ctx.response.send_message(embed=embed)


@character.command()
@app_commands.describe(oath="Determining future gold gain from sessions and gold claims.")
@app_commands.choices(oath=[discord.app_commands.Choice(name='No Oath', value=1), discord.app_commands.Choice(name='Oath of Offerings', value=2), discord.app_commands.Choice(name='Oath of Poverty', value=3), discord.app_commands.Choice(name='Oath of Absolute Poverty', value=4)])
@app_commands.describe(nickname='a shorthand way to look for your character in displays')
async def register(ctx: commands.Context, character_name: str, mythweavers: str, image_link: str, nickname: str = None, titles: str = None, description: str = None, oath: discord.app_commands.Choice[int] = 1, color: str = '#5865F2', backstory: str = None):
    """Register your character"""
    if character_name is not None:
        true_character_name = str.replace(str.replace(str.replace(str.replace(str.replace(str.title(character_name), ";", ""), "(", ""), ")", ""), "[", ""), "]", "")
        character_name = unidecode(true_character_name)
    else:
        await ctx.response.send_message(f"Character Name is required")
        return
    if nickname is not None:
        nickname = str.replace(str.replace(str.title(nickname), ";", ""), ")", "")
    if titles is not None:
        titles = str.replace(titles, ";", "")
    if description is not None:
        description = str.replace(description, ";", "")
    if mythweavers is not None:
        mythweavers = str.replace(str.replace(str.lower(mythweavers), ";", ""), ")", "")
        mythweavers_valid = str.lower(mythweavers[0:5])
        if mythweavers_valid != 'https':

            await ctx.response.send_message(f"Mythweavers link is missing HTTPS:", ephemeral=True)
            return
    else:
        await ctx.response.send_message(f"Mythweavers link is required", ephemeral=True)
        return
    if image_link is not None:
        image_link = str.replace(str.replace(image_link, ";", ""), ")", "")
        image_link_valid = str.lower(image_link[0:5])
        if image_link_valid != 'https':
            await ctx.response.send_message(f"Image link is missing HTTPS:")
            return
    else:
        await ctx.response.send_message(f"image link is required", ephemeral=True)
        return
    if oath == 1:
        oath = 1
    else:
        oath = oath.value
    if oath == 2:
        oath_name = 'Offerings'
        starting_gold = 1500
    elif oath == 3:
        oath_name = 'Poverty'
        starting_gold = 720
    elif oath == 4:
        oath_name = 'Absolute'
        starting_gold = 15
    else:
        oath_name = 'No Oath'
        starting_gold = 3000
    regex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
    match = re.search(regex, color)
    if len(color) == 7 and match:
        guild_id = ctx.guild_id
        author = ctx.user.name
        author_id = ctx.user.id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Player_Name, Character_Name from Player_Characters where Character_Name = ?""", (character_name,))
        results = cursor.fetchone()
        cursor.execute(f"""SELECT Player_Name, Character_Name from A_STG_Player_Characters where Character_Name = ?""", (character_name,))
        results2 = cursor.fetchone()
        cursor.close()
        db.close()
        print(results, results2)
        if results is None and results2 is None:
            int_color = int(color[1:], 16)
            await EventCommand.stage_character(self, true_character_name, character_name, author, author_id, guild_id, nickname, titles, description, oath_name, mythweavers, image_link, color, backstory)
            await EventCommand.stg_gold_change(self, guild_id, author, author_id, character_name, starting_gold, starting_gold, 3000, 'Character Creation', 'Character Create')
            embed = discord.Embed(title=f"{character_name}", url=f'{mythweavers}', description=f"Other Names: {titles}", color=int_color)
            embed.set_author(name=f'{author}')
            embed.set_thumbnail(url=f'{image_link}')
            embed.add_field(name="Information", value=f'**Level**: 3, **Mythic Tier**: 0', inline=False)
            embed.add_field(name="Experience", value=f'**Milestones**: 0, **Remaining**: 3')
            embed.add_field(name="Mythic", value=f'**Trials**: 0, **Remaining**: 0')
            embed.add_field(name="Current Wealth", value=f'**GP**: {starting_gold}', inline=False)
            embed.add_field(name="Current Flux", value=f'**Flux**: 0')
            if oath_name == 'Offerings':
                embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
            elif oath_name == 'Poverty':
                embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
            elif oath_name == 'Absolute':
                embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
            else:
                embed.set_footer(text=f'{description}')
            try :
                await ctx.response.send_message(embed=embed)
            except discord.errors.HTTPException:
                embed = discord.Embed(title=f"{character_name}", url=f'https://cdn.discordapp.com/attachments/977939245463392276/1194141019088891984/super_saiyan_mr_bean_by_zakariajames6_defpqaz-fullview.jpg?ex=65af457d&is=659cd07d&hm=57bdefe2d376face6a842a7b7a5ed8021e854a64e798f901824242c4a939a37b&',
                                      description=f"Other Names: {titles}", color=int_color)
                embed.set_author(name=f'{author}')
                embed.set_thumbnail(url=f'https://cdn.discordapp.com/attachments/977939245463392276/1194140952789536808/download.jpg?ex=65af456d&is=659cd06d&hm=1613025f9f1c1263823881c91a81fc4b93831ff91df9f4a84c813e9fab6467e9&')
                embed.add_field(name="Information", value=f'**Level**: 3, **Mythic Tier**: 0', inline=False)
                embed.add_field(name="Experience", value=f'**Milestones**: 0, **Remaining**: 3')
                embed.add_field(name="Mythic", value=f'**Trials**: 0, **Remaining**: 0')
                embed.add_field(name="Current Wealth", value=f'**GP**: {starting_gold}', inline=False)
                embed.add_field(name="Current Flux", value=f'**Flux**: 0')
                embed.set_footer(text=f'Oops! You used a bad URL, please fix it.')
                await ctx.response.send_message(embed=embed)
                await EventCommand.fix_character(self, guild_id, character_name)
        else:
            await ctx.response.send_message(f"{character_name} has already been registered by {author}", ephemeral=True)
    else:
        await ctx.response.send_message(f"Invalid Hex Color Code!", ephemeral=True)


@character.command()
@app_commands.autocomplete(name=own_character_select_autocompletion)
@app_commands.describe(oath="Determining future gold gain from sessions and gold claims.")
@app_commands.choices(oath=[discord.app_commands.Choice(name='No Oath', value=1), discord.app_commands.Choice(name='Oath of Offerings', value=2), discord.app_commands.Choice(name='Oath of Poverty', value=3), discord.app_commands.Choice(name='Oath of Absolute Poverty', value=4), discord.app_commands.Choice(name='No Change', value=5)])
@app_commands.describe(new_nickname='a shorthand way to look for your character in displays')
async def edit(ctx: commands.Context, name: str, new_character_name: str = None, mythweavers: str = None, image_link: str = None, new_nickname: str = None, titles: str = None, description: str = None, oath: discord.app_commands.Choice[int] = 5, color: int = None):
    """Register your character"""
    name = str.replace(str.replace(str.replace(str.replace(str.replace(str.title(name), ";", ""), "(", ""), ")", ""), "[", ""), "]", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    if oath == 5:
        oath = 5
    else:
        oath = oath.value
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    sql = f"""Select True_Character_Name, Nickname, Titles, Description, Mythweavers, Image_Link, Oath, Color, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Gold_Value, Gold_Value_Max, Flux, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? OR Player_Name = ? AND  Nickname = ?"""
    val = (author, name, author, name)
    cursor.execute(sql, val)
    results = cursor.fetchone()
    await ctx.response.defer(thinking=True, ephemeral=True)
    if results is None:
        sql = f"""Select True_Character_Name, Nickname, Titles, Description, Mythweavers, Image_Link, Oath, Color, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Gold_Value, Gold_Value_Max, Flux, Character_Name from A_STG_Player_Characters where Player_Name = ? AND Character_Name = ? OR  Player_Name = ? AND Nickname = ?"""
        val = (author, name, author, name)
        cursor.execute(sql, val)
        results = cursor.fetchone()
        if results is None:
            await ctx.response.send_message(f"Cannot find any {name} owned by {author} with the supplied name or nickname.")
        else:
            if new_character_name is not None:
                new_character_name = str.replace(str.replace(str.replace(str.replace(str.replace(str.title(new_character_name), ";", ""), ")", ""), "("),"["), "]")
                true_character_name = unidecode(new_character_name)
            else:
                true_character_name = results[0]
                new_character_name = results[18]
            if new_nickname is not None:
                new_nickname = str.replace(str.replace(str.title(new_nickname), ";", ""), ")", "")
            else:
                new_nickname = results[1]
            if titles is not None:
                titles = str.replace(str.replace(titles, ";", ""), ")", "")
            else:
                titles = results[2]
            if description is not None:
                description = str.replace(str.replace(description, ";", ""), ")", "")
            else:
                description = results[3]
            print(f"test")
            print(mythweavers)
            if mythweavers is not None:
                print(mythweavers)
                mythweavers = str.replace(str.replace(str.lower(mythweavers), ";", ""), ")", "")
                mythweavers_valid = str.lower(mythweavers[0:5])
                print(mythweavers_valid)
                if mythweavers_valid != 'https':
                    await ctx.response.send_message(f"Mythweavers link is missing HTTPS:")
                    return
            else:
                mythweavers = results[4]
            if image_link is not None:
                image_link = str.replace(str.replace(image_link, ";", ""), ")", "")
                image_link_valid = str.lower(image_link[0:5])
                print(image_link_valid)
                if image_link_valid != 'https':
                    await ctx.response.send_message(f"Image link is missing HTTPS:")
                    return
            else:
                image_link = results[5]
            if oath == 1:
                oath_name = 'No Oath'
                gold = 3000
            elif oath == 2:
                oath_name = 'Offerings'
                gold = 1500
            elif oath == 3:
                oath_name = 'Poverty'
                gold = 720
            elif oath == 4:
                oath_name = 'Absolute'
                gold = 15
            else:
                oath_name = results[6]
            if color is not None:
                regex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
                match = re.search(regex, color)
            else:
                color = results[7]
                regex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
                match = re.search(regex, color)
            if len(color) == 7 and match:
                cursor.close()
                db.close()
                if results is not None:
                    int_color = int(color[1:], 16)
                    true_name = results[0]
                    if oath_name != results[6]:
                        await EventCommand.gold_set(self, guild_id, author, author_id, name, gold, gold, gold, 'Oath Change', 'Character Edit', 2)
                    await EventCommand.edit_stg_character(self, true_name, true_character_name, new_character_name, guild_id, new_nickname, titles, description, oath_name, mythweavers, image_link, color, author)
                    embed = discord.Embed(title=f"Edited Character: {new_character_name}", url=f'{mythweavers}', description=f"Other Names: {titles}", color=int_color)
                    embed.set_author(name=f'{author}')
                    embed.set_thumbnail(url=f'{image_link}')
                    embed.add_field(name="Information", value=f'**Level**: {results[8]}, **Mythic Tier**: {results[9]}', inline=False)
                    embed.add_field(name="Experience", value=f'**Milestones**: {results[10]}, **Remaining**: {results[11]}')
                    embed.add_field(name="Mythic", value=f'**Trials**: {results[12]}, **Remaining**: {results[13]}')
                    embed.add_field(name="Current Wealth", value=f'**Current gold**: {results[14]} GP, **Effective Gold**: {results[15]} GP, **Lifetime Wealth**: {results[16]} GP', inline=False)
                    embed.add_field(name="Current Flux", value=f'**Flux**: {results[17]}', inline=False)
                    if oath_name == 'Offerings':
                        embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
                    elif oath_name == 'Poverty':
                        embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
                    elif oath_name == 'Absolute':
                        embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
                    else:
                        embed.set_footer(text=f'{description}')
                    await ctx.response.send_message(embed=embed)
            else:
                await ctx.response.send_message(f"Invalid Hex Color Code!")
    else:
        if new_character_name is not None:
            new_character_name = str.replace(str.replace(str.title(new_character_name), ";", ""), ")", "")
            true_character_name = unidecode(new_character_name)
        else:
            new_character_name = unidecode(results[0])
            true_character_name = results[0]
        if new_nickname is not None:
            new_nickname = str.replace(str.replace(str.title(new_nickname), ";", ""), ")", "")
        else:
            new_nickname = results[1]
        if titles is not None:
            titles = str.replace(str.replace(titles, ";", ""), ")", "")
        else:
            titles = results[2]
        if description is not None:
            description = str.replace(str.replace(description, ";", ""), ")", "")
        else:
            description = results[3]
        if mythweavers is not None:
            mythweavers = str.replace(str.replace(mythweavers, ";", ""), ")", "")
            mythweavers_valid = str.lower(mythweavers[0:5])
            if mythweavers_valid != 'https':
                await ctx.followup.send(f"Mythweavers link is missing HTTPS:")
                return
        else:
            mythweavers = results[4]
        if image_link is not None:
            image_link = str.replace(str.replace(image_link, ";", ""), ")", "")
            image_link_valid = str.lower(image_link[0:5])
            if image_link_valid != 'https':
                await ctx.followup.send(f"Image link is missing HTTPS:")
                return
        else:
            image_link = results[5]
        if oath == 1:
            oath_name = 'No Oath'
        elif oath == 2:
            oath_name = 'Offerings'
        elif oath == 3:
            oath_name = 'Poverty'
        elif oath == 4:
            oath_name = 'Absolute'
        else:
            oath_name = results[6]
            print(f"printing {oath_name} as Absolute")
        if color is not None:
            regex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
            match = re.search(regex, color)
        else:
            color = results[7]
            regex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
            match = re.search(regex, color)
        if len(color) == 7 and match:
            if results is not None:
                int_color = int(color[1:], 16)
                true_name = results[0]
                if oath_name != results[6] and results[8] < 7:
                    if oath == 2:
                        await EventCommand.gold_set(self, guild_id, author, author_id, name, results[14] / 2, results[15] - results[14] / 2, results[15], 'Oath Change', 'Character Edit', 1)
                    else:
                        await EventCommand.gold_set(self, guild_id, author, author_id, name, results[14], results[15], results[15], 'Oath Change', 'Character Edit', 1)
                print(f"printing {oath_name}")
                await EventCommand.edit_character(self, true_name, true_character_name, new_character_name, guild_id, new_nickname, titles, description, oath_name, mythweavers, image_link, color, author)
                if results[23] is not None:
                    await EventCommand.edit_bio(self, guild_id, new_character_name, None, results[22])
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link, Article_ID FROM Player_Characters where Character_Name = ? or Nickname = ?", (new_character_name, new_nickname))
                player_info = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                embed = discord.Embed(title=f"Edited Character: {new_character_name}", url=f'{mythweavers}', description=f"Other Names: {titles}", color=int_color)
                embed.set_author(name=f'{author}')
                embed.set_thumbnail(url=f'{image_link}')
                embed.add_field(name="Information", value=f'**Level**: {player_info[7]}, **Mythic Tier**: {player_info[8]}', inline=False)
                embed.add_field(name="Experience", value=f'**Milestones**: {player_info[9]}, **Remaining**: {player_info[10]}')
                embed.add_field(name="Mythic", value=f'**Trials**: {player_info[11]}, **Remaining**: {player_info[12]}')
                embed.add_field(name="Current Wealth", value=f'**Current gold**: {player_info[13]} GP, **Effective Gold**: {player_info[14]} GP, **Lifetime Wealth**: {player_info[15]} GP', inline=False)
                embed.add_field(name="Current Flux", value=f'**Flux**: {player_info[16]}', inline=False)
                if player_info[6] == 'Offerings':
                    embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
                elif player_info[6] == 'Poverty':
                    embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
                elif player_info[6] == 'Absolute':
                    embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
                else:
                    embed.set_footer(text=f'{description}')
                cursor.close()
                db.close()
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=embed)
                await logging_thread.edit(name=f"{new_character_name}")
                logging_channel = await bot.fetch_channel(character_log_channel_id[0])
                logging_message = await logging_channel.fetch_message(player_info[25])
                mentions = f'<@{player_info[1]}>'
                embed = discord.Embed(title=f"{new_character_name}", url=f'{mythweavers}', description=f"Other Names: {titles}", color=int_color)
                embed.set_author(name=f'{author}')
                embed.set_thumbnail(url=f'{image_link}')
                await logging_message.edit(content=mentions, embed=embed)
                await ctx.followup.send(embed=embed)
        else:
            await ctx.followup.send(f"Invalid Hex Color Code!")


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def retire(ctx: commands.Context, character_name: str):
    """Retires your character"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = ctx.user.name
    sql = f"""SELECT True_Character_Name, Thread_ID from Player_Characters where  Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND  Nickname = ?"""
    val = (author, character_name, author, character_name)
    cursor.execute(sql, val)
    results = cursor.fetchone()
    cursor.close()
    db.close()
    if results is None:
        await ctx.response.send_message(f"there is no character registered by character name or nickname as {character_name} owned by {ctx.user.name} to unregister.", ephemeral=True)
    if results is not None:
        true_character_name = results[0]
        buttons = ["✅", "❌"]  # checkmark X symbol
        embed = discord.Embed(title=f"Are you sure you want to retire {true_character_name}?", description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                return print("timed out")
            else:
                if reaction.emoji == u"\u274C":
                    embed = discord.Embed(title=f"You have thought better of retirement", description=f"Carpe Diem my lad!", colour=discord.Colour.blurple())
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                if reaction.emoji == u"\u2705":
                    embed = discord.Embed(title=f"{true_character_name} has retired", description=f"Have a pleasant retirement.", colour=discord.Colour.red())
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                    await EventCommand.retire_character(self, guild_id, true_character_name, author)
                    source = f"Character has retired!"
                    logging_embed = log_embed(results[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, source)
                    logging_thread = guild.get_thread(results[1])
                    await logging_thread.send(embed=logging_embed)


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def levelup(interaction: discord.Interaction, character_name: str, amount: int):
    """Level up by using medium jobs from the unbelievaboat shop."""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild = interaction.guild
    guild_id = interaction.guild_id
    author = interaction.user.name
    user = interaction.user
    client = Client(os.getenv('UBB_TOKEN'))
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount >= 1:
        cursor.execute(f"SELECT Search from Admin Where Identifier = 'UBB_Medium_Job'")
        item_id = cursor.fetchone()
        try:
            inventory = await client.get_inventory_item(guild_id, author_id, item_id[0])
            if 0 < amount <= inventory.quantity:
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?", (author, character_name, author, character_name))
                player_info = cursor.fetchone()
                if player_info is not None:
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
                    max_level = cursor.fetchone()
                    true_character_name = player_info[3]
                    personal_cap = int(max_level[0]) if player_info[29] is None else player_info[29]
                    character_level = player_info[7]
                    if player_info[7] >= int(max_level[0]) or player_info[7] > personal_cap:
                        await interaction.response.send_message(f"you are currently at the level cap {max_level[0]} for the server or your personal level cap of {personal_cap}.")
                    else:
                        milestone_total = player_info[9]
                        milestones_earned = 0
                        int_max_level = int(max_level[0])
                        used = 0
                        for x in range(amount):
                            if character_level < int_max_level:
                                used = used + 1
                                new = inventory.quantity - 1
                                cursor.execute(f"SELECT Medium from AA_Milestones where level = {character_level}")
                                milestone_info = cursor.fetchone()
                                milestone_total += milestone_info[0]
                                milestones_earned += milestone_info[0]
                                cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
                                current_level = cursor.fetchone()
                                remaining = current_level[1] + current_level[2] - milestone_total
                                character_level = current_level[0]
                                if x+1 == amount or character_level == int_max_level or character_level == personal_cap:
                                    await EventCommand.adjust_milestones(self, true_character_name, milestone_total, remaining, character_level, guild_id, author)
                                    await client.delete_inventory_item(guild_id, author_id, item_id[0], used)
                                    mythic_information = mythic_calculation(guild_id, character_level, player_info[11], 0)
                                    tier = 0 if player_info[8] == 0 else mythic_information[0]
                                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                    accepted_bio_channel = cursor.fetchone()
                                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                                    character_log_channel_id = cursor.fetchone()
                                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], character_level, tier, milestone_total, remaining, player_info[11], mythic_information[1], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                    bio_message = await bio_channel.fetch_message(player_info[24])
                                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                    source = f"{player_info[2]} has leveled up to level {character_level}! using {used} medium jobs from the shop."
                                    logging_embed = log_embed(player_info[2], author, character_level, milestones_earned, milestone_total, remaining, tier, 0, player_info[11], mythic_information[1], None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, source)
                                    logging_thread = guild.get_thread(player_info[25])
                                    await logging_thread.send(embed=logging_embed)
                                    if player_info[1] != current_level[0]:
                                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {current_level[0]}")
                                        level_range = cursor.fetchone()
                                        cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Desc")
                                        level_range_max = cursor.fetchone()
                                        cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Asc")
                                        level_range_min = cursor.fetchone()
                                        cursor.execute(f"SELECT True_Character_Name from Player_Characters WHERE Player_Name = '{author}' AND level >= {level_range_min[0]} AND level <= {level_range_max[0]}")
                                        level_range_characters = cursor.fetchone()
                                        member = await guild.fetch_member(interaction.user.id)
                                        if level_range_characters is None:
                                            cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {character_level}")
                                            new_level_range = cursor.fetdchone()
                                            role1 = guild.get_role(level_range[2])
                                            role2 = guild.get_role(new_level_range[2])
                                            await member.remove_roles(role1)
                                            await member.add_roles(role2)
                                        else:
                                            cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {character_level}")
                                            new_level_range = cursor.fetchone()
                                            role2 = guild.get_role(new_level_range[2])
                                            await member.add_roles(role2)
                                        color = player_info[17]
                                        int_color = int(color[1:], 16)
                                        embed = discord.Embed(title="Mythweavers Sheet", url=f'{player_info[18]}', description=f"Other Names: {player_info[4]}", color=int_color)
                                        embed.set_author(name=f'{player_info[2]} Level Up Report')
                                        embed.set_thumbnail(url=f'{player_info[19]}')
                                        embed.add_field(name="Information", value=f'**New Level**:{character_level}', inline=False)
                                        embed.add_field(name="Experience", value=f'**Milestones**: {milestone_total}, **Remaining to next level**: {remaining}')
                                        embed.set_footer(text=f'You have spent {used} medium jobs from the store with {new} medium jobs remaining increasing your milestones by {milestones_earned}.')
                                        await interaction.response.send_message(embed=embed)
                                        break
                                    elif player_info[1] == current_level[0]:
                                        color = player_info[17]
                                        int_color = int(color[1:], 16)
                                        embed = discord.Embed(title="Mythweavers Sheet", url=f'{player_info[18]}', description=f"Other Names: {player_info[4]}", color=int_color)
                                        embed.set_author(name=f'{player_info[2]} Milestone Report')
                                        embed.set_thumbnail(url=f'{player_info[19]}')
                                        embed.add_field(name="Information", value=f'**Level**: {player_info[1]}', inline=False)
                                        embed.add_field(name="Experience", value=f'**Milestones**: {milestone_total}, **Remaining**: {remaining}')
                                        embed.set_footer(text=f'You have spent {used} medium jobs from the store with {new} medium jobs remaining increasing your milestones by {milestones_earned}.')
                                        await interaction.response.send_message(embed=embed)
                                        break
                else:
                    await interaction.response.send_message(f"{author} does not have a {character_name} registered under this Nickname or Character Name.")
            else:  # if no item is found
                await interaction.response.send_message(f"{author} only has {inventory.quantity} jobs in his inventory and cannot spend {amount}.")
        except unbelievaboat.errors.HTTPError:
            await interaction.response.send_message(f"{author} does not have any medium jobs in their inventory.")
    else:
        await interaction.response.send_message(f"Sweet brother in christ, I'm not an MMO bot, please stop trying to overflow me!")
    cursor.close()
    db.close()
    await client.close()


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def trialup(interaction: discord.Interaction, character_name: str, amount: int):
    """Tier up by using mythic trial catchups from the unbelievaboat shop. WARNING: do not use more medium jobs than you require to level up as you will LOSE milestones this way."""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = interaction.guild_id
    guild = interaction.guild
    author = interaction.user.name
    author_id = interaction.user.id
    client = Client(os.getenv('UBB_TOKEN'))
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount >= 1:
        cursor.execute(f"SELECT Search from Admin Where Identifier = 'UBB_Mythic_Trial'")
        item_id = cursor.fetchone()
        item = int(item_id[0])
        inventory = await client.get_inventory_item(guild_id, author_id, item)
        inventory_remaining = inventory.quantity
        if 0 < amount <= inventory.quantity:
            cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?", (author, character_name, author, character_name))
            player_info = cursor.fetchone()
            if player_info is not None:
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Cap'")
                max_tier = cursor.fetchone()
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
                break_point = cursor.fetchone()
                if player_info[1] <= int(break_point[0]):
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
                    tier_rate_limit = cursor.fetchone()
                else:
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
                    tier_rate_limit = cursor.fetchone()
                rate_limited_tier = floor(player_info[7] / int(tier_rate_limit[0]))
                tier_max = rate_limited_tier if rate_limited_tier <= max_tier[0] else max_tier[0]
                true_character_name = player_info[3]
                tier = player_info[8]
                print(tier)
                trial_total = player_info[11]
                used = 0
                if tier != 0:
                    if tier < tier_max:
                        for x in range(amount):
                            if tier < tier_max:
                                used = used + 1
                                trial_total = trial_total + 1
                                cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials WHERE Trials <= '{trial_total}' ORDER BY Trials DESC  LIMIT 1")
                                current_level = cursor.fetchone()
                                tier = current_level[0]
                                if x+1 == amount or tier == tier_max:
                                    inventory_remaining = inventory_remaining - used
                                    trials_required = current_level[1] + current_level[2] - trial_total
                                    await EventCommand.adjust_trials(self, character_name, trial_total, guild_id, author)
                                    await client.delete_inventory_item(guild_id, author_id, item_id[0], used)
                                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                    accepted_bio_channel = cursor.fetchone()
                                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                                    character_log_channel_id = cursor.fetchone()
                                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], tier, player_info[9], player_info[10], player_info[11] + used, trials_required, player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                    bio_message = await bio_channel.fetch_message(player_info[24])
                                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                    source = f"{author} has increased their tier to tier {tier}! using {used} Trial catch-ups from the shop."
                                    logging_embed = log_embed(player_info[2], author, None, None, None, None, tier, used, player_info[11] + used, trials_required, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, source)
                                    logging_thread = guild.get_thread(player_info[25])
                                    await logging_thread.send(embed=logging_embed)
                                    if player_info[8] != current_level[0]:
                                        await interaction.response.send_message(content=f"you have leveled up to tier {tier} using {used} mythic trial catch ups from the shop.")
                                    if player_info[2] == current_level[0]:
                                        await interaction.response.send_message(content=f"you used {used} mythic trial catch ups from the shop!")
                                    break
                    else:
                        await interaction.response.send_message(f"{true_character_name} is already at his tier cap of {tier_max}.")
                else:
                    await interaction.response.send_message(f"{true_character_name} is unable to rank his mythic tier up before his first session.")
            else:
                await interaction.response.send_message(f"{author} does not have a {character_name} registered under this nickname or character name.")
        elif inventory is None:
            await interaction.response.send_message(f"{author} does not have any trial catch ups in their inventory.")
        else:  # if no item is found
            await interaction.response.send_message(f"{author} only has {inventory.quantity} trial catch ups in his inventory and cannot spend {amount}.")
    else:
        await interaction.response.send_message(f"Sweet brother in christ, I'm not an MMO bot, please stop trying to overflow me!")
    cursor.close()
    db.close()
    await client.close()


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def pouch(interaction: discord.Interaction, character_name: str):
    """increase your wealth by using a gold pouch to WPL"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = interaction.guild_id
    author = interaction.user.name
    guild = interaction.guild
    client = Client(os.getenv('UBB_TOKEN'))
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Search from Admin Where Identifier = 'UBB_Gold_Pouch'")
    item_id = cursor.fetchone()
    try:
        inventory = await client.get_inventory_item(guild_id, author_id, item_id[0])
        if inventory is not None:
            cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?", (author, character_name, author, character_name))
            player_info = cursor.fetchone()
            if player_info is not None:
                true_character_name = player_info[3]
                new = inventory.quantity - 1
                character_level = player_info[7]
                cursor.execute(f"SELECT WPL from AA_Milestones where level = {character_level}")
                wpl_info = cursor.fetchone()
                if wpl_info[0] <= player_info[15]:
                    await interaction.response.send_message(f'You are too wealthy for the gold pouch, go rob an orphanage. Your lifetime wealth is {player_info[15]} GP against a WPL of {wpl_info[0]} GP')
                else:
                    gold = wpl_info[0] - player_info[15]
                    gold_info = gold_calculation(player_info[7], player_info[6], player_info[13], player_info[14], player_info[15], gold)
                    await EventCommand.gold_change(self, guild_id, author, author_id, true_character_name, gold_info[3], gold_info[3], gold, 'Used Unbelievaboat Pouch', 'Used Unbelievaboat Pouch')
                    cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                    transaction_id = cursor.fetchone()
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    accepted_bio_channel = cursor.fetchone()
                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + gold_info[3], player_info[14] + gold_info[3], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                    bio_message = await bio_channel.fetch_message(player_info[24])
                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                    source = f"Character has increased their wealth by {gold_info[3]} GP using a gold pouch from the shop, transaction_id: {transaction_id[0]}!"
                    logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, player_info[13] + gold_info[3], gold_info[3], player_info[14] + gold_info[3], transaction_id[0], None, None, None, None, None, None, None, None, None, None, None, source)
                    logging_thread = guild.get_thread(player_info[25])
                    await logging_thread.send(embed=logging_embed)
                    await interaction.response.send_message(content=f"you have increased your wealth by {gold_info[3]} GP using a gold pouch from the shop for the character named {character_name}.")
                    await client.delete_inventory_item(guild_id, author_id, item_id[0], 1)
            else:
                await interaction.response.send_message(f"{author} does not have a {character_name} registered under this character name or nickname.")
    except unbelievaboat.errors.HTTPError:
        await interaction.response.send_message(f"{author} does not have any gold pouches in their inventory.")
    cursor.close()
    db.close()
    await client.close()


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
@app_commands.autocomplete(title=title_lookup)
@app_commands.choices(usage=[discord.app_commands.Choice(name='Display', value=1), discord.app_commands.Choice(name='Apply Masculine Title', value=2), discord.app_commands.Choice(name='Apply Feminine Title', value=3), discord.app_commands.Choice(name='Change Gender', value=4)])
async def entitle(ctx: commands.Context, character_name: str, title: str, usage: discord.app_commands.Choice[int]):
    """Apply a title to yourself! This defaults to display the available titles."""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    guild = ctx.guild
    usage = 1 if usage == 1 else usage.value
    client = Client(os.getenv('UBB_TOKEN'))
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    print(type(title), title)
    cursor.execute(f"SELECT ID, Fame, Masculine_Name, Feminine_Name from Store_Title Where Masculine_name = ? or Feminine_name = ?", (title, title))
    item_id = cursor.fetchone()
    if usage != 1 and usage != 4 and item_id is not None:
        try:
            title_name = item_id[2] if usage == 2 else item_id[3]
            inventory = await client.get_inventory_item(guild_id, author_id, item_id[0])
            if inventory is not None:
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND  Nickname = ?", (author, character_name, author, character_name))
                player_info = cursor.fetchone()
                if player_info is not None:
                    true_character_name = player_info[3]
                    cursor.execute(f"SELECT Fame, Masculine_Name, Feminine_Name from Store_Title where Masculine_Name = ? or Feminine_Name = ?", (player_info[27], player_info[27]))
                    title_information = cursor.fetchone()
                    title_fame = 0 if title_information is None else title_information[0]
                    if item_id[1] <= title_fame:
                        await ctx.response.send_message(f'Unlike a repo-man, you do not need to collect titles. You already have the title {title_information[1]}')
                    else:
                        title_fame = item_id[1] - title_fame
                        await EventCommand.title_change(self, guild_id, author, author_id, true_character_name, title_name, player_info[27] + title_fame, player_info[30] + title_fame, f'Became the title of {title_name}', 'Used entitle!')
                        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                        accepted_bio_channel = cursor.fetchone()
                        bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], title_name, player_info[30], player_info[31])
                        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                        bio_message = await bio_channel.fetch_message(player_info[24])
                        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                        logging_embed = discord.Embed(title=f"{true_character_name} has changed their title to {title_name}", description=f"{author} has changed their title to {title_name} using {title_fame} fame from the shop.", colour=discord.Colour.blurple())
                        logging_thread = guild.get_thread(player_info[25])
                        await logging_thread.send(embed=logging_embed)
                        await ctx.response.send_message(content=f"you have changed your title to {title_name} and increased your fame by {title_fame} by using an item from shop for the character named {character_name}.", ephemeral=True)
                        await client.delete_inventory_item(guild_id, author_id, item_id[0], 1)
                else:
                    await ctx.response.send_message(f"{author} does not have a {character_name} registered under this character name or nickname.")
        except unbelievaboat.errors.HTTPError:
            await ctx.response.send_message(f"{author} does not have any {title_name} in their inventory.")
        await client.close()
    elif usage == 4:
        cursor.execute( f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND  Nickname = ?", (author, character_name, author, character_name))
        player_info = cursor.fetchone()
        if player_info is not None:
            true_character_name = player_info[3]
            cursor.execute(f"SELECT Fame, Title, Masculine_Name, Feminine_Name from Store_Title where Masculine_Name = ? or Feminine_Name = ?", (player_info[27], player_info[27]))
            title_information = cursor.fetchone()
            if title_information is not None:
                title_name = title_information[2] if player_info[27] != title_information[2] else title_information[3]
                await EventCommand.title_change(self, guild_id, author, author_id, true_character_name, title_name, player_info[27], f'Became the title of {title_name}', 'Used entitle!')
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], title_name, player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                logging_embed = discord.Embed(title=f"{true_character_name} has changed their title to {title_name}", description=f"{author} has changed their title to {title_name} using {title} from the shop.", colour=discord.Colour.blurple())
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await ctx.response.send_message( content=f"you have changed your title to {title_name} for {character_name}.", ephemeral=True)
            else:
                await ctx.response.send_message(f"{author} does not have a title registered under this character name or nickname.")
        else:
            await ctx.response.send_message(f"{author} does not have a {character_name} registered under this character name or nickname.")
    else:
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        cursor.execute(f"""SELECT COUNT(masculine_name) FROM Store_Title""")
        admin_count = cursor.fetchone()
        max_page = math.ceil(admin_count[0] / 20)
        current_page = 1
        low = 1 + ((current_page - 1) * 20)
        high = 20 + ((current_page - 1) * 20)
        cursor.execute(f"""SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"Title Store Settings Page {current_page}", description=f'This is a list of available titles', colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f"Title Store Item: {result[3]}/{result[4]}", value=f'**Effect**: {result[1]}, **Rewarded Fame**: {result[2]}', inline=False)
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                cursor.close()
                db.close()
                return print("timed out")
            else:
                previous_page = current_page
                if reaction.emoji == u"\u23EA":
                    current_page = 1
                    low = 1
                    high = 20
                elif reaction.emoji == u"\u2B05" and current_page > 1:
                    low -= 20
                    high -= 20
                    current_page -= 1
                elif reaction.emoji == u"\u27A1" and current_page < max_page:
                    low += 20
                    high += 20
                    current_page += 1
                elif reaction.emoji == u"\u23E9":
                    current_page = max_page
                    low = ((20 * max_page) - 19)
                    high = (20 * max_page)
                for button in buttons:
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(f"""SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}""")
                    pull = cursor.fetchall()
                    embed = discord.Embed(title=f"Title Store Settings Page {current_page}", description=f'This is a list of available titles', colour=discord.Colour.blurple())
                    for result in pull:
                        embed.add_field(name=f"Title Store Item: {result[3]}/{result[4]}", value=f'**Effect**: {result[1]}, **Rewarded Fame**: {result[2]}', inline=False)
                    await msg.edit(embed=embed)
    cursor.close()
    db.close()



@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
@app_commands.autocomplete(name=fame_lookup)
@app_commands.choices(modify=[discord.app_commands.Choice(name='Display', value=1), discord.app_commands.Choice(name='use', value=2)])
async def proposition(ctx: commands.Context, character_name: typing.Optional[str], name: typing.Optional[str], approver: typing.Optional[discord.Member], modify: discord.app_commands.Choice[int] = 1):
    """Proposition NPCs for Favors using your prestige!."""
    character_name = None if character_name is None else str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    guild = ctx.guild
    modify = 1 if modify == 1 else modify.value
    character_name = character_name if character_name is not None else "N/A"
    name = name if name is not None else "N/A"
    approver = approver if approver is not None else "N/A"
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame Where name = ?", (name, ))
    item_id = cursor.fetchone()
    if modify == 2 and approver != "N/A" and item_id is not None:
        cursor.execute( f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND  Nickname = ?", (author, character_name, author, character_name))
        player_info = cursor.fetchone()
        if player_info is not None:
            true_character_name = player_info[3]
            cursor.execute(f"SELECT Count(Item_name) from A_Audit_Prestige where Author_ID = ? and Character_Name = ? and Item_Name = ? and IsAllowed = ?", (author_id, character_name, name, 1))
            title_information = cursor.fetchone()
            if title_information[0] < item_id[4] and player_info[27] >= item_id[0] and player_info[30] >= item_id[1]:
                await EventCommand.proposition_open(self, guild_id, author, author_id, player_info[3], item_id[2], item_id[1], 'Attempting to open a proposition', 'Proposition Open!')
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select MAX(Transaction_ID) FROM A_Audit_Prestige WHERE Character_Name = ?", (character_name, ))
                proposition_id = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30]-item_id[1], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                logging_embed = discord.Embed(title=f"{true_character_name} has opened the following proposition of propositioned {name} ID: {proposition_id[0]}", description=f"{author} is attempting to use {item_id[1]} prestige to obtain the following effect of: \r\n {item_id[3]}.", colour=discord.Colour.blurple())
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await ctx.response.send_message(content=f"<@{approver.id}>, {player_info[2]} is attempting to proposition for {name}, with ID of {proposition_id[0]} do you accept? \r\n use the /Gamemaster Proposition command to reject or deny this request using the Proposition ID!", allowed_mentions=discord.AllowedMentions(users=True))
            elif title_information[0] >= item_id[4]:
                await ctx.response.send_message(f"{author} has met the limit for usage of this proposition.")
            elif player_info[27] < item_id[0]:
                await ctx.response.send_message(f"{author} does not have enough fame to use this proposition.")
            else:
                await ctx.response.send_message(f"{author} does not have enough prestige to use this proposition.")
        else:
            await ctx.response.send_message(f"{author} does not have a {character_name} registered under this character name or nickname.")
    elif modify == 2 and approver != "N/A" and item_id is None:
        await ctx.response.send_message(f"{name} is not an available proposition.")
    elif modify == 2 and approver == "N/A":
        await ctx.response.send_message(f"Please mention the approver of this proposition.")
    else:
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        cursor.execute(f"""SELECT COUNT(Name) FROM Store_Fame""")
        admin_count = cursor.fetchone()
        max_page = math.ceil(admin_count[0] / 20)
        current_page = 1
        low = 1 + ((current_page - 1) * 20)
        high = 20 + ((current_page - 1) * 20)
        cursor.execute(
            f"""SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"Fame Store Settings Page {current_page}", description=f'This is a list of the administratively defined items', colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f'**Name**: {result[2]}', value=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}', inline=False)
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                cursor.close()
                db.close()
                return print("timed out")
            else:
                previous_page = current_page
                if reaction.emoji == u"\u23EA":
                    current_page = 1
                    low = 1
                    high = 20
                elif reaction.emoji == u"\u2B05" and current_page > 1:
                    low -= 20
                    high -= 20
                    current_page -= 1
                elif reaction.emoji == u"\u27A1" and current_page < max_page:
                    low += 20
                    high += 20
                    current_page += 1
                elif reaction.emoji == u"\u23E9":
                    current_page = max_page
                    low = ((20 * max_page) - 19)
                    high = (20 * max_page)
                for button in buttons:
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(f"""SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}""")
                    pull = cursor.fetchall()
                    embed = discord.Embed(title=f"Fame Store Settings Page {current_page}", description=f'This is a list of the administratively defined items', colour=discord.Colour.blurple())
                    for result in pull:
                        embed.add_field(name=f'**Name**: {result[2]}', value=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}', inline=False)
                    await msg.edit(embed=embed)
                    cursor.close()
    db.close()



@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def cap(ctx: commands.Context, character_name: str, level_cap: int):
    """THIS COMMAND DISPLAYS CHARACTER INFORMATION"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    author = ctx.user.name
    guild_id = ctx.guild_id
    guild = ctx.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Character_Name FROM Player_Characters where Player_Name = ? and Character_Name = ? or  Player_Name = ? AND Nickname = ?""", (author, character_name, author, character_name))
    character_info = cursor.fetchone()
    if character_info is not None:
        await EventCommand.adjust_personal_cap(self, guild_id, author, character_name, level_cap)
        await ctx.response.send_message(f"{author} has adjusted the personal cap of {character_name} to {level_cap}.", ephemeral=True)
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Nickname = ?", (author, character_name, character_name))
        player_info = cursor.fetchone()
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
        accepted_bio_channel = cursor.fetchone()
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
        character_log_channel_id = cursor.fetchone()
        bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
        bio_message = await bio_channel.fetch_message(player_info[24])
        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
        logging_embed = discord.Embed(title=f"{character_name} has had their maximum level cap set to {level_cap}!", description=f"This character can no longer level up past this point until changed!", colour=discord.Colour.blurple())
        logging_thread = guild.get_thread(player_info[25])
        await logging_thread.send(embed=logging_embed)
    else:
        await ctx.response.send_message(f"{author} does not have a {character_name} registered under this character name or nickname.")
    cursor.close()
    db.close()


@character.command()
@app_commands.autocomplete(character_name=character_select_autocompletion)
async def display(ctx: commands.Context, player_name: typing.Optional[discord.Member], character_name: str = 'All', current_page: int = 1):
    """THIS COMMAND DISPLAYS CHARACTER INFORMATION"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    if player_name is not None:
        player_name = player_name.name
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if player_name == 'NA':
        player_name = ctx.user.name
    if character_name == 'All':
        cursor.execute(f"""SELECT COUNT(Character_Name) FROM Player_Characters where Player_Name = '{player_name}'""")
        character_count = cursor.fetchone()
        if character_count is None:
            cursor.close()
            db.close()
            ctx.response.send_message(f"{player_name} was not a valid player to obtain the characters of!")
            return
        max_page = math.ceil(character_count[0] / 5)
        if current_page >= max_page:
            current_page = max_page
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        low = 0 + (5 * (current_page-1))
        offset = 5
        cursor.execute(f"""Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Mythweavers from Player_characters WHERE player_name = '{player_name}' LIMIT {low}, {offset}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"{player_name} character page {current_page}", description=f"This is list of {player_name}'s characters", colour=discord.Colour.blurple())
        x = 0
        for result in pull:
            x += 1
            number = ordinal(x)
            embed.add_field(name=f'{number} Character', value=f'**Name**: [{result[0]}](<{result[13]}>) \r\n **Level**: {result[1]}, **Mythic Tier**: {result[2]}', inline=False)
            linkage = f""
            if result[9] is not None:
                linkage += f"**Tradition**: [{result[9]}]({result[10]})"
            if result[11] is not None:
                if result[9] is not None:
                    linkage += f" "
                linkage += f"**Template**: [{result[11]}]({result[12]})"
            if result[9] is not None or result[11] is not None:
                embed.add_field(name=f'Additional Info', value=linkage, inline=False)
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                return print("timed out")
            else:
                previous_page = current_page
                if reaction.emoji == u"\u23EA":
                    current_page = 1
                    low = 0 + (5 * (current_page - 1))
                    offset = 5
                elif reaction.emoji == u"\u2B05" and current_page > 1:
                    current_page -= 1
                    low = 0 + (5 * (current_page - 1))
                    offset = 5
                elif reaction.emoji == u"\u27A1" and current_page < max_page:
                    current_page += 1
                    low = 0 + (5 * (current_page - 1))
                    offset = 5
                elif reaction.emoji == u"\u23E9":
                    current_page = max_page
                    low = 0 + (5 * (current_page - 1))
                    offset = 5
                for button in buttons:
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(f"""Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Mythweavers from Player_characters WHERE player = '{player_name}' LIMIT {low}, {offset}""")
                    edit_pull = cursor.fetchall()
                    embed = discord.Embed(title=f"{player_name} character page {current_page}", description=f"This is list of {player_name}'s characters", colour=discord.Colour.blurple())
                    x = 0
                    for result in edit_pull:
                        x += 1
                        number = ordinal(x)
                        embed.add_field(name=f'{number} Character', value=f'**Name**: [{result[0]}](<{result[13]}>) \r\n **Level**: {result[1]}, **Mythic Tier**: {result[2]}', inline=False)
                        linkage = " "
                        if result[9] is not None:
                            linkage += f"**Tradition**: [{result[9]}]({result[10]})"
                        if result[11] is not None:
                            if result[9] is not None:
                                linkage += f" "
                            linkage += f"**Template**: [{result[11]}]({result[12]})"
                        if result[9] is not None or result[11] is not None:
                            embed.add_field(name=f'Additional Info', value=linkage, inline=False)
                    await ctx.response.send_message(embed=embed)
                    await msg.edit(embed=embed)
    elif character_name != 'All':
        sql = f"""Select True_Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Gold_Value, Oath, Fame, Prestige, Title, Article_Link from Player_characters WHERE Character_Name = ? or Nickname = ?"""
        val = (character_name, character_name)
        cursor.execute(sql, val)
        result = cursor.fetchone()
        if result is None:
            await ctx.response.send_message(f"{character_name} is not a valid Nickname or Character Name.")
            cursor.close()
            db.close()
            return
        else:
            color = result[11]
            int_color = int(color[1:], 16)
            description_field = f" "
            if result[2] is not None:
                description_field += f"**Other Names**: {result[2]}\r\n"
            if result[24] is not None:
                description_field += f"[**Backstory**](<{result[24]}>)"
            embed = discord.Embed(title="Mythweavers Sheet", url=f'{result[12]}', description=f"{description_field}", color=int_color)
            if result[23] is not None:
                author_field = f"{result[23]} {result[0]}"
            else:
                author_field = f"{result[0]}"
            embed.set_author(name=author_field)
            embed.set_thumbnail(url=f'{result[13]}')
            embed.add_field(name=f'Information', value=f'**Level**: {result[4]}, **Mythic Tier**: {result[5]} **Fame**: {result[21]}, **Prestige**: {result[22]}', inline=False)
            embed.add_field(name=f'Total Experience', value=f'**Milestones**: {result[6]}, **Remaining**:  {result[7]}')
            embed.add_field(name=f'Mythic', value=f'**Trials**: {result[8]}, **Remaining**: {result[9]}')
            embed.add_field(name="\u200B", value="\u200B")
            embed.add_field(name=f'Current Wealth', value=f'**GP**: {round(result[10],2)}')
            embed.add_field(name=f'Effective Wealth', value=f'**GP**: {round(result[19],2)}')
            embed.add_field(name="\u200B", value="\u200B")
            embed.add_field(name=f'Flux', value=f'**Flux**: {result[14]}', inline=False)
            linkage = f""
            if result[15] is not None:
                linkage += f"**Tradition**: [{result[15]}]({result[16]})"
            if result[17] is not None:
                if result[15] is not None:
                    linkage += " "
                linkage += f"**Template**: [{result[17]}]({result[18]})"
            if result[15] is not None or result[17] is not None:
                embed.add_field(name=f'Additional Info', value=linkage, inline=False)
            print(result[20])
            if result[20] == 'Offerings':
                embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
            elif result[20] == 'Poverty':
                embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
            elif result[20] == 'Absolute':
                embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
            else:
                embed.set_footer(text=f'{result[3]}')
            await ctx.response.send_message(embed=embed)
    cursor.close()
    db.close()


@character.command()
@app_commands.describe(level_range="the level range of the characters you are looking for. Keep in mind, this applies only to the preset low/med/high/max ranges your admin has set")
async def list(ctx: commands.Context, level_range: discord.Role, current_page: int = 1):
    """THIS COMMAND DISPLAYS CHARACTER INFORMATION"""
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Level FROM Level_Range WHERE Role_ID = {level_range.id} order by Level asc limit 1""")
    level_range_min = cursor.fetchone()
    cursor.execute(f"""SELECT Level FROM Level_Range WHERE Role_ID = {level_range.id} order by Level desc limit 1""")
    level_range_max = cursor.fetchone()
    if level_range_min is None:
        cursor.close()
        db.close()
        ctx.response.send_message(f"{level_range.name} was not a valid role to select", ephemeral=True)
        return
    cursor.execute(f"""SELECT COUNT(Character_Name) FROM Player_Characters where level >= {level_range_min[0]} and level <= {level_range_max[0]}""")
    character_count = cursor.fetchone()
    if character_count[0] != 0:
        max_page = math.ceil(character_count[0] / 5)
        if current_page >= max_page:
            current_page = max_page
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        low = 0 + (5 * (current_page-1))
        offset = 5
        cursor.execute(f"""Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link from Player_characters WHERE level >= {level_range_min[0]} and level <= {level_range_max[0]} LIMIT {low}, {offset}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"{level_range.name} character page {current_page}", description=f"This is list of characters in {level_range.name}", colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f'Character Name', value=f'**Name**:{result[0]}', inline=False)
            embed.add_field(name=f'Information', value=f'**Level**: {result[1]}, **Mythic Tier**: {result[2]}', inline=False)
            embed.add_field(name=f'Total Experience', value=f'**Milestones**: {result[3]}, **Milestones Remaining**: {result[4]}, **Trials**: {result[5]}, **Trials Remaining**: {result[6]}', inline=False)
            embed.add_field(name=f'Current Wealth', value=f'**GP**: {result[7]}, **Flux**: {result[8]}', inline=False)
            linkage = f""
            if result[9] is not None:
                linkage += f"**Tradition**: [{result[9]}]({result[10]})"
            if result[11] is not None:
                if result[9] is not None:
                    linkage += f" "
                linkage += f"**Template**: [{result[11]}]({result[12]})"
            if result[9] is not None or result[11] is not None:
                embed.add_field(name=f'Additional Info', value=linkage, inline=False)
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                return print("timed out")
            else:
                previous_page = current_page
                if reaction.emoji == u"\u23EA":
                    current_page = 1
                    low = 0 + (5 * (current_page - 1))
                    offset = 5
                elif reaction.emoji == u"\u2B05" and current_page > 1:
                    current_page -= 1
                    low = 0 + (5 * (current_page - 1))
                    offset = 5
                elif reaction.emoji == u"\u27A1" and current_page < max_page:
                    current_page += 1
                    low = 0 + (5 * (current_page - 1))
                    offset = 5
                elif reaction.emoji == u"\u23E9":
                    current_page = max_page
                    low = 0 + (5 * (current_page - 1))
                    offset = 5
                for button in buttons:
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(f"""Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link from Player_characters WHERE level >= {level_range_min[0]} and level <= {level_range_max[0]} LIMIT {low}, {offset}""")
                    edit_pull = cursor.fetchall()
                    embed = discord.Embed(title=f"{level_range.name} character page {current_page}", description=f"This is list of characters in {level_range.name}", colour=discord.Colour.blurple())
                    for result in edit_pull:
                        embed.add_field(name=f'Character Name', value=f'**Name**:{result[0]}', inline=False)
                        embed.add_field(name=f'Information', value=f'**Level**: {result[1]}, **Mythic Tier**: {result[2]}', inline=False)
                        embed.add_field(name=f'Total Experience', value=f'**Milestones**: {result[3]}, **Milestones Remaining**: {result[4]}, **Trials**: {result[5]}, **Trials Remaining**: {result[6]}', inline=False)
                        embed.add_field(name=f'Current Wealth', value=f'**GP**: {result[7]}, **Flux**: {result[8]}', inline=False)
                        linkage = None
                        if result[9] is not None:
                            linkage += f"**Tradition**: [{result[9]}]({result[10]})"
                        if result[11] is not None:
                            if result[9] is not None:
                                linkage += f" "
                            linkage += f"**Template**: [{result[11]}]({result[12]})"
                        if result[9] is not None or result[11] is not None:
                            embed.add_field(name=f'Additional Info', value=linkage, inline=False)
                    await msg.edit(embed=embed)
    else:
        await ctx.response.send_message(f"{level_range.name} does not have any characters within this level range.",ephemeral=True)


@character.command()
@app_commands.choices(modify=[discord.app_commands.Choice(name='Create', value=1), discord.app_commands.Choice(name='Edit', value=2)])
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def backstory(ctx: commands.Context, character_name: str, backstory: str, modify: discord.app_commands.Choice[int] = 1):
    """THIS COMMAND CREATES OR CHANGES THE BACKSTORY ASSOCIATED WITH YOUR CHARACTER"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    author = ctx.user.name
    guild_id = ctx.guild_id
    guild = ctx.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Character_Name, Article_ID, Mythweavers FROM Player_Characters where Player_Name = ? and Character_Name = ? or  Player_Name = ? AND Nickname = ?""", (author, character_name, author, character_name))
    character_info = cursor.fetchone()
    if character_info is not None:
        if modify == 1:
            if character_info[1] is not None:
                await ctx.response.send_message(f"{author} already has a backstory associated with {character_name}. If you wish to edit it, use the Edit Option of this command", ephemeral=True)
            else:
                await EventCommand.create_bio(self, guild_id, character_info[0], backstory, character_info[2])
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?", (author, character_name, author, character_name))
                player_info = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                logging_embed = discord.Embed(title=f"{character_name} has had their backstory created!", description=f"{author} has created the following [backstory](<{player_info[31]}>)", colour=discord.Colour.blurple())
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await ctx.response.send_message(f"{author} has created a backstory for {character_name}.", ephemeral=True)
        else:
            if character_info[1] is None:
                await ctx.response.send_message(f"{author} does not have a backstory associated with {character_name}. If you wish to create one, use the Create Option of this command", ephemeral=True)
            else:
                await EventCommand.edit_bio(self, guild_id, character_info[0], backstory, character_info[1])
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?", (author, character_name, author, character_name))
                player_info = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                logging_embed = discord.Embed(title=f"{character_name} has had their backstory edited!", description=f"{author} has edited the following backstory: \r\n {backstory}", colour=discord.Colour.blurple())
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await ctx.response.send_message(f"{author} has edited the backstory for {character_name}.", ephemeral=True)
    else:
        cursor.execute(f"""SELECT Character_Name FROM A_STG_Player_Characters where Player_Name = ? and Character_Name = ? or  Player_Name = ? AND Nickname = ?""", (author, character_name, author, character_name))
        character_info = cursor.fetchone()
        if character_info is not None:
            await EventCommand.edit_stage_bio(self, guild_id, character_info[0], backstory)
        else:
            await ctx.response.send_message(f"{author} does not have a {character_name} registered under this character name or nickname.", ephemeral=True)


    cursor.close()
    db.close()





@gold.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Gold Help", description=f'This is a list of Gold management commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Claim**', value=f'Claim gold that should be received through downtime!', inline=False)
    embed.add_field(name=f'**Buy**', value=f'Buy items, or send your gold out into the open wide world.', inline=False)
    embed.add_field(name=f'**Send**', value=f'Send gold to another player', inline=False)
    embed.add_field(name=f'**Consume**', value=f'Spend illiquid wealth', inline=False)
    await ctx.response.send_message(embed=embed)


@gold.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def claim(ctx: commands.Context, character_name: str, amount: float, reason: str):
    """Claim gold based on downtime activities, or through other interactions with NPCs"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    reason = str.replace(reason, ";", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount <= 0:
        await ctx.response.send_message(f"Little comrade! Please give yourself some credit! {amount} is too small to claim!")
    elif amount > 0:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Nickname = ?", (author, character_name, character_name))
        player_info = cursor.fetchone()
        if player_info is None:
            await ctx.response.send_message(f"{author} does not have a character named {character_name}")
        else:
            gold_info = gold_calculation(player_info[7], player_info[6], player_info[13], player_info[14], player_info[15], amount)
            await EventCommand.gold_change(self, guild_id, author, author_id, character_name, gold_info[3], gold_info[3], amount, reason, 'Gold_Claim')
            cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
            transaction_id = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + gold_info[3], player_info[14] + gold_info[3], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"Character has increased their wealth by {gold_info[3]} GP using a gold pouch from the shop, transaction_id: {transaction_id[0]}!"
            logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, player_info[13] + gold_info[3], gold_info[3], player_info[14] + gold_info[3], transaction_id[0], None, None, None, None, None, None, None, None, None, None, None, source)
            logging_thread = guild.get_thread(player_info[25])
            cursor.close()
            db.close()
            await logging_thread.send(embed=logging_embed)
            await ctx.response.send_message(f"{player_info[2]} has claimed {amount} gold, receiving {gold_info[3]} gold and now has {gold_info[0]} gold!.")



@gold.command()
@app_commands.describe(market_value="market value of the item regardless of crafting. Items crafted for other players have an expected value of 0.")
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def buy(ctx: commands.Context, character_name: str, expenditure: float, market_value: float, reason: str):
    """Buy items from NPCs for non-player trades and crafts. Expected Value is the MARKET price of what you are buying, not the price you are paying."""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    reason = str.replace(reason, ";", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if expenditure <= 0:
        await ctx.response.send_message(f"Little comrade! Please buy something of actual value! {expenditure} is too small to purchase anything with!")
    elif market_value < 0:
        await ctx.response.send_message(f"Little comrade! You cannot have an expected value of: {market_value}, it is too little gold to work with!")
    elif expenditure > 0:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?", (author, character_name, author, character_name))
        player_info = cursor.fetchone()
        if player_info[0] is None:
            await ctx.response.send_message(f"{ctx.user.name} does not have a character named {character_name}")
        else:
            expenditure = -abs(expenditure)
            print(player_info[13])
            print(abs(expenditure))
            if player_info[13] >= abs(expenditure):
                market_value_adjusted = market_value + expenditure
                remaining = round(expenditure + player_info[13], 2)
                gold_value = player_info[14] + market_value_adjusted
                if player_info[6] == 'Poverty':
                    max_wealth = 80 * (player_info[7] ** 2)
                    if gold_value > max_wealth:
                        await ctx.response.send_message(f"{player_info[2]} has too much money and needs to give some to charitable causes by using the 'buy' command where they receive nothing in return!")
                        return
                elif player_info[6] == 'Absolute':
                    max_wealth = 5 * player_info[7]
                    if gold_value > max_wealth:
                        await ctx.response.send_message(f"{player_info[2]} has too much money and needs to give some to charitable causes by using the 'buy' command where they receive nothing in return!")
                        return
                expenditure = round(expenditure, 2)
                market_value_adjusted = round(market_value_adjusted, 2)
                await EventCommand.gold_change(self, guild_id, author, author_id, character_name, expenditure, market_value_adjusted, market_value_adjusted, reason, 'Gold_Buy')
                cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                transaction_id = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + expenditure, player_info[14] + market_value_adjusted, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"Character of {character_name} has spent {expenditure} GP in return for {market_value} GP using the buy command, transaction_id: {transaction_id[0]}!"
                print(f"THIS IS {player_info[13] + expenditure} PLAYER INFO AND EXPENDITURE")
                print(f"this is the raw {expenditure}")
                logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, player_info[13] + expenditure, expenditure, round(player_info[14] + market_value_adjusted,2), transaction_id[0], None, None, None, None, None, None, None, None, None, None, None, source)
                logging_thread = guild.get_thread(player_info[25])
                print(expenditure)
                await logging_thread.send(embed=logging_embed)
                await ctx.response.send_message(f"{player_info[2]} has spent {abs(expenditure)} gold and has received {market_value_adjusted} in expected value return. Leaving them with {remaining} gold.")
            else:
                await ctx.response.send_message(f"{player_info[2]} does not have enough gold to make this purchase!")
    cursor.close()
    db.close()

@gold.command()
@app_commands.describe(consumption="Consume illiquid gold from having consumed or lost an item.")
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def consume(ctx: commands.Context, character_name: str, consumption: float, reason: str):
    """Buy items from NPCs for non-player trades and crafts. Expected Value is the MARKET price of what you are buying, not the price you are paying."""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    reason = str.replace(reason, ";", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if consumption <= 0:
        await ctx.response.send_message(f"MY FREN, YOU MUST BE CONSUMING GOLD. {consumption} IS FAR TOO LOW A NUMBER. REMEMBER, IF IT ISN'T TOIGHT, IT ISN'T ROIGHT.")
    else:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?", (author, character_name, author, character_name))
        player_info = cursor.fetchone()
        if player_info[0] is None:
            await ctx.response.send_message(f"{ctx.user.name} does not have a character named {character_name}")
        else:
            consumption = -abs(round(consumption,2))
            if player_info[14] - player_info[13] >= abs(consumption):
                remaining = round(consumption + player_info[14], 2)
                await EventCommand.gold_change(self, guild_id, author, author_id, character_name, player_info[13], remaining, player_info[14], reason, 'Gold_Consume')
                cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                transaction_id = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14] + consumption, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"Character of {character_name} has consumed {consumption} GP having used {reason} using the consume command, transaction_id: {transaction_id[0]}!"
                logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, None, consumption, round(player_info[14] + consumption,2), transaction_id[0], None, None, None, None, None, None, None, None, None, None, None, source)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await ctx.response.send_message(f"{player_info[2]} has consumed {abs(consumption)} gold by using {reason}. Leaving them with {remaining} illiquid wealth.")
            else:
                await ctx.response.send_message(f"{player_info[2]} clearly hasn't bought this item to consume!")
    cursor.close()
    db.close()



@gold.command()
@app_commands.autocomplete(character_from=own_character_select_autocompletion)
@app_commands.autocomplete(character_to=character_select_autocompletion)
async def send(ctx: commands.Context, character_from: str, character_to: str, amount: float, expected_value: float, reason: str):
    """Send gold to a crafter or other players for the purposes of their transactions. Expected Value is the MARKET price of what they will give you in return."""
    character_from = str.replace(str.title(character_from), ";", "")
    character_to = str.replace(str.title(character_to), ";", "")
    reason = str.replace(reason, ";", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount <= 0:
        await ctx.response.send_message(f"Little comrade! Please SEND something of actual value! {amount} is too small to claim!")
    elif expected_value < 0:
        await ctx.response.send_message(f"Expected Value cannot be less than 0!")
    elif expected_value < amount:
        await ctx.response.send_message(f"If they're charging you higher than the market value, go buy it from an NPC...")
    else:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Player_Name = ? AND Nickname = ?", (author, character_from, author, character_from))
        player_info = cursor.fetchone()
        if player_info[0] is None:
            await ctx.response.send_message(f"{author} does not have a character named or nicknamed {character_from}")
        else:
            if player_info[13] < amount:
                await ctx.response.send_message(f"Unlike America, you can't go into debt to resolve your debt. {player_info[1] - amount} leaves you too in debt.")
            else:
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? or Nickname = ? ", (character_to, character_to))
                send_info = cursor.fetchone()
                if send_info is None:
                    await ctx.response.send_message(f"Could not find a character named {character_to}!")
                else:
                    buttons = ["✅", "❌"]  # checkmark X symbol
                    embed = discord.Embed(title=f"Are you sure you want {character_from} to send {amount} GP to {character_to}?", description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
                    await ctx.response.send_message(embed=embed)
                    msg = await ctx.original_response()
                    for button in buttons:
                        await msg.add_reaction(button)
                    while True:
                        try:
                            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
                        except asyncio.TimeoutError:
                            embed.set_footer(text="Request has timed out.")
                            await msg.edit(embed=embed)
                            await msg.clear_reactions()
                            return print("timed out")
                        else:
                            if reaction.emoji == u"\u264C":
                                embed = discord.Embed(title=f"You have thought better of freely giving your money", description=f"Savings!", colour=discord.Colour.blurple())
                                await msg.edit(embed=embed)
                                await msg.clear_reactions()
                            if reaction.emoji == u"\u2705":
                                embed = discord.Embed(title=f"{character_from} has given {amount} in GP to {character_to}", description=f"Hope it was worth it.", colour=discord.Colour.red())
                                await msg.clear_reactions()
                                expected_value_adjusted = expected_value + -abs(amount)
                                print(-abs(amount))
                                print(type(-abs(amount)))
                                expected_value_adjusted = round(expected_value_adjusted, 2)
                                amount = round(amount, 2)
                                await EventCommand.gold_change(self, guild_id, author, author_id, character_from, -abs(amount), expected_value_adjusted, expected_value_adjusted, reason, 'gold send')
                                cursor.execute(f"Select MAX(Transaction_ID) from A_Audit_Gold order by Transaction_ID desc limit 1")
                                transaction_id_from = cursor.fetchone()
                                await EventCommand.gold_change(self, guild_id, send_info[0], send_info[1], send_info[2], amount, amount, amount, reason, 'Gold_Buy')
                                cursor.execute(f"Select MAX(Transaction_ID) from A_Audit_Gold order by Transaction_ID desc limit 1")
                                transaction_id_to = cursor.fetchone()
                                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                accepted_bio_channel = cursor.fetchone()
                                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + -abs(amount), player_info[14] + expected_value_adjusted, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                                bio_message = await bio_channel.fetch_message(player_info[24])
                                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                source = f"Character of {character_from} has spent {amount} GP in return for {expected_value_adjusted} using the send command, transaction_id: {transaction_id_from[0]}!"
                                logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, player_info[13] + -abs(amount), -abs(amount), player_info[14] + expected_value_adjusted, transaction_id_from[0], None, None, None, None, None, None, None, None, None, None, None, source)
                                logging_thread = guild.get_thread(player_info[25])
                                await logging_thread.send(embed=logging_embed)
                                to_bio_embed = character_embed(send_info[0], send_info[1], send_info[2], send_info[4], send_info[5], send_info[6], send_info[7], send_info[8], send_info[9], send_info[10], send_info[11], send_info[12], send_info[13] + amount, send_info[14] + expected_value_adjusted, send_info[16], send_info[17], send_info[18], send_info[19], send_info[20], send_info[21], send_info[22], send_info[23], send_info[27], send_info[28], send_info[30], send_info[31])
                                to_bio_message = await bio_channel.fetch_message(send_info[24])
                                await to_bio_message.edit(content=to_bio_embed[1], embed=to_bio_embed[0])
                                to_source = f"Character of {character_to} has received {amount} GP in return for services of {expected_value_adjusted} using the send command, transaction_id: {transaction_id_to[0]}!"
                                to_logging_embed = log_embed(send_info[0], author, None, None, None, None, None, None, None, None, send_info[13] + amount, amount, send_info[14] + amount, transaction_id_to[0], None, None, None, None, None, None, None, None, None, None, None, to_source)
                                to_logging_thread = guild.get_thread(send_info[25])
                                await to_logging_thread.send(embed=to_logging_embed)
                                await EventCommand.gold_transact(self, transaction_id_from[0], transaction_id_to[0], guild_id)
                                await EventCommand.gold_transact(self, transaction_id_to[0], transaction_id_from[0], guild_id)
                                embed.set_footer(text=f"Transaction ID was {transaction_id_from[0]}")
                                await msg.edit(embed=embed)
                                break
    cursor.close()
    db.close()


@gold.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def history(ctx: commands.Context, character_name: str, current_page: int = 1):
    """This command displays gold audit history."""
    character = str.replace(str.title(character_name), ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    sql = f"""SELECT COUNT(Character_Name) FROM A_Audit_Gold where Character_Name = ?"""
    val = [character]
    cursor.execute(sql, val)
    leaders = cursor.fetchone()
    max_page = math.ceil(leaders[0] / 8)
    if current_page >= max_page:
        current_page = max_page
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    low = 0 + (8 * (current_page-1))
    offset = 8
    cursor.execute(f"""Select Transaction_ID, Author_Name, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time from A_Audit_Gold WHERE Character_Name = ? LIMIT {low}, {offset}""", (character,))
    pull = cursor.fetchall()
    embed = discord.Embed(title=f"{character} character page {current_page}", description=f"This is list of {character}'s transactions", colour=discord.Colour.red())
    for result in pull:
        embed.add_field(name=f'Transaction Information', value=f'**Date**: {result[8]}, **Source**: {result[7]}', inline=False)
        embed.add_field(name=f'Changes:', value=f'{result[3]} Liquid GP {result[4]} Effective GP, {result[5]} Life Time GP')
        embed.add_field(name=f'Transaction:', value=f'Transaction_ID: {result[0]}, Reason: {result[6]}', inline=False)
    await ctx.response.send_message(embed=embed)
    msg = await ctx.original_response()
    for button in buttons:
        await msg.add_reaction(button)
    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
        except asyncio.TimeoutError:
            embed.set_footer(text="Request has timed out.")
            await msg.edit(embed=embed)
            await msg.clear_reactions()
            cursor.close()
            db.close()
            return print("timed out")
        else:
            previous_page = current_page
            if reaction.emoji == u"\u23EA":
                current_page = 1
                low = 0 + (8 * (current_page - 1))
                offset = 8
            elif reaction.emoji == u"\u2B05" and current_page > 1:
                current_page -= 1
                low = 0 + (8 * (current_page - 1))
                offset = 8
            elif reaction.emoji == u"\u27A1" and current_page < max_page:
                current_page += 1
                low = 0 + (8 * (current_page - 1))
                offset = 8
            elif reaction.emoji == u"\u23E9":
                current_page = max_page
                low = 0 + (8 * (current_page - 1))
                offset = 8
            for button in buttons:
                await msg.remove_reaction(button, ctx.user)
            if current_page != previous_page:
                cursor.execute(f"""Select Transaction_ID, Author_Name, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time from A_Audit_Gold WHERE Character_Name = ? LIMIT {low}, {offset}""", (character,))
                pull = cursor.fetchall()
                embed = discord.Embed(title=f"{character} character page {current_page}", description=f"This is list of {character}'s transactions", colour=discord.Colour.red())
                for result in pull:
                    embed.add_field(name=f'Transaction Information', value=f'**Date**: {result[8]}, **Source**: {result[7]}', inline=False)
                    embed.add_field(name=f'Changes:', value=f'{result[3]} Liquid GP {result[4]} Effective GP, {result[5]} Life Time GP')
                    embed.add_field(name=f'Transaction:', value=f'Transaction_ID: {result[0]}, Reason: {result[6]}', inline=False)
                await msg.edit(embed=embed)


@gamemaster.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Gamemaster Help", description=f'This is a list of GM administrative commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Create**', value=f'**GAMEMASTER**: Create a session and post an announcement!', inline=False)
    embed.add_field(name=f'**Edit**', value=f'**GAMEMASTER**: Edit the session information!', inline=False)
    embed.add_field(name=f'**Accept**', value=f'**GAMEMASTER**: Accept a character into your session group!', inline=False)
    embed.add_field(name=f'**Remove**', value=f'**GAMEMASTER**: Remove a character from your session group!', inline=False)
    embed.add_field(name=f'**Display**', value=f'**GAMEMASTER**: Display the players on your quest!',inline=False)
    embed.add_field(name=f'**Reward**', value=f'**GAMEMASTER**: Send session rewards to involved characters!', inline=False)
    embed.add_field(name=f'**Endow**', value=f'**GAMEMASTER**: Endow individual players with rewards!', inline=False)
    embed.add_field(name=f'**Notify**', value=f'**GAMEMASTER**: Notify Players of a quest!', inline=False)
    embed.add_field(name=f'**Proposition**', value=f'**GAMEMASTER**: Accept or Reject A Proposition based on the ID!', inline=False)
    embed.add_field(name=f'**Glorify**', value=f'**GAMEMASTER**: Increase or decrease characters fame and prestige!', inline=False)
    embed.add_field(name=f'**Plot**', value='**GAMEMASTER**: Create or Modify a plot for your session series!', inline=False)
    embed.add_field(name=f'**Requests**', value='**GAMEMASTER**: View player session requests!', inline=False)
    await ctx.response.send_message(embed=embed)

@player.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Player Help", description=f'This is a list of Playerside commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Join**', value=f'**PLAYER**: join a session using one your characters!', inline=False)
    embed.add_field(name=f'**Leave**', value=f'**PLAYER**: Leave a session that you have joined!', inline=False)
    embed.add_field(name=f'**Display**', value=f'**ALL**: Display the details of a session.', inline=False)
    embed.add_field(name=f'**Timesheet**', value=f'Use this to create a timesheet for your availability.', inline=False)
    embed.add_field(name=f'**Request**', value=f'Mark a session request using a character and create a session group.', inline=False)
    embed.add_field(name=f'**GroupUp**', value=f'Join in a group created by a "request".', inline=False)
    embed.add_field(name=f'**Requests**', value=f'Display Requests for a specific Group.', inline=False)
    embed.add_field(name=f'**Availability**', value=f'Display Availability of a Specific Player on a specific day of the week.', inline=False)
    await ctx.response.send_message(embed=embed)


@gamemaster.command()
@app_commands.choices(acceptance=[discord.app_commands.Choice(name='accept', value=1), discord.app_commands.Choice(name='rejectance', value=2)])
async def proposition(ctx: commands.Context, proposition_id: int, reason: typing.Optional[str], acceptance: discord.app_commands.Choice[int] = 1):
    """Accept or reject a proposition!"""
    guild_id = ctx.guild_id
    author = ctx.user.name
    guild = ctx.guild
    acceptance = 1 if acceptance == 1 else acceptance.value
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Character_Name, Item_Name from A_Audit_Prestige Where Transaction_ID = ?", (proposition_id, ))
    item_id = cursor.fetchone()
    reason = "N/A" if reason is None else reason
    if item_id is not None:
        if acceptance == 1:
            cursor.execute(f"Select Thread_ID from Player_Characters where Character_Name = ?", (item_id[0],))
            player_info = cursor.fetchone()
            logging_embed = discord.Embed(title=f"{author.capitalize()} has accepted the proposition of {item_id[0]} using {item_id[1]}!", description=f"Proposition ID: {proposition_id}", color=discord.Colour.red())
            logging_embed.add_field(name=f'Reason:', value=f'{reason}', inline=False)
            logging_thread = guild.get_thread(player_info[0])
            await logging_thread.send(embed=logging_embed)
        else:
            cursor.execute(f"Select Thread_ID from Player_Characters where Character_Name = ?", (item_id[0],))
            player_info = cursor.fetchone()
            logging_embed = discord.Embed(title=f"{author} has rejected the proposition!", description=f"Proposition ID: {proposition_id}", color=discord.Colour.red())
            logging_embed.add_field(name=f'Reason:', value=f'{reason}', inline=False)
            logging_thread = guild.get_thread(player_info[0])
            source = "proposition"
            await logging_thread.send(embed=logging_embed)
            await EventCommand.proposition_reject(self, guild_id, author, proposition_id, reason, source)
        await ctx.response.send_message(embed=logging_embed)
    cursor.close()
    db.close()


@gamemaster.command()
@app_commands.autocomplete(character=character_select_autocompletion)
async def glorify(ctx: commands.Context, character: str, fame: int, prestige: int, reason: typing.Optional[str]):
    """Add or remove from a player's fame and prestige!"""
    guild_id = ctx.guild_id
    author = ctx.user.name
    guild = ctx.guild
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    item_id = cursor.fetchone()
    reason = "N/A" if reason is None else reason
    cursor.execute(f"Select Thread_ID, Fame, Prestige from Player_Characters where Character_Name = ?", (item_id[0],))
    player_info = cursor.fetchone()
    if player_info is not None:
        logging_embed = discord.Embed(title=f"{author} has adjusted your fame or prestige!", description=f"**changed fame**: {fame} **changed prestige**: {prestige}", color=discord.Colour.red())
        logging_embed.add_field(name=f'New Totals:', value=f'**fame**: {fame + player_info[1]}, **prestige**: {prestige + player_info[2]} ', inline=False)
        logging_thread = guild.get_thread(player_info[0])
        ctx.response.send_message(embed=logging_embed)
        await logging_thread.send(embed=logging_embed)
        await EventCommand.glorify(self, guild_id, author, character, fame + player_info[1], prestige + player_info[2], reason)
    else:
        await ctx.response.send_message(f"Character {character} does not exist!")
    cursor.close()
    db.close()


# noinspection PyUnresolvedReferences
@gamemaster.command()
@app_commands.describe(hammer_time="Please use the plain code hammer time provides that appears like </>, ")
@app_commands.describe(overflow="Allow for adjust role ranges!")
@app_commands.autocomplete(plot=get_precreated_plots)
@app_commands.choices(overflow=[discord.app_commands.Choice(name='current range only!', value=1), discord.app_commands.Choice(name='include next level bracket!', value=2), discord.app_commands.Choice(name='include lower level bracket!', value=3),discord.app_commands.Choice(name='ignore role requirements!', value=4)])
async def create(interaction: discord.Interaction, session_name: str, session_range: discord.Role, player_limit: int, play_location: str, game_link: typing.Optional[str], hammer_time: str, overview: str, description: str, plot: str = '9762aebb-43ae-47d5-8c7b-30c34a55b9e5',  overflow: discord.app_commands.Choice[int] = 1):
    """Create a new session."""
    if plot is not None:
        plot = str.replace(str.replace(str.replace(str.replace(str.replace(str.title(plot), ";", ""), "(", ""), ")", ""), "[",""), "]", "")
        if ' ' in plot:
            plot = await get_precreated_plots(interaction, plot)
            plot = plot[1]
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    overflow = 1 if overflow == 1 else overflow.value
    session_range_name = session_range.name
    session_range_id = session_range.id
    if game_link is not None:
        game_link_valid = str.lower(game_link[0:4])
        if game_link_valid == 'http':
            embed = discord.Embed(title=f"{session_name}", url=f'{game_link}', description=f"Play Location: {play_location}", color=discord.Colour.red())
        else:
            game_link = 'HTTPS://' + game_link
            embed = discord.Embed(title=f"{session_name}", url=f'{game_link}', description=f"Play Location: {play_location}", color=discord.Colour.red())
    else:
        embed = discord.Embed(title=f"{session_name}", description=f"Session Range: {session_range}", color=discord.Colour.red())

    hammer_timing = hammer_time[0:3]
    if hammer_timing == "<t:":
        timing = hammer_time[3:13]
        date = "<t:" + timing + ":D>"
        hour = "<t:" + timing + ":t>"
        arrival = "<t:" + timing + ":R>"
    else:
        timing = hammer_time
        date = "<t:" + timing + ":D>"
        hour = "<t:" + timing + ":t>"
        arrival = "<t:" + timing + ":R>"
    await EventCommand.create_session(self, author, session_name, session_range_name, session_range_id, play_location, timing, game_link, guild_id, author, overview, description, player_limit, overflow, plot)
    sql = f"SELECT Session_ID from Sessions WHERE Session_Name = ? AND GM_Name = ? ORDER BY Session_ID Desc Limit 1"
    val = (session_name, author)
    cursor.execute(sql, val)
    info = cursor.fetchone()
    print(overflow)
    if overflow == 1:
        footer_text = f'Session ID: {info[0]}.'
        session_ranges = f'<@&{session_range_id}>'
    elif overflow == 2:
        cursor.execute(f"SELECT min(level), max(level) FROM Level_Range WHERE Role_ID = ?", (session_range_id,))
        session_range_info = cursor.fetchone()
        footer_text = f'Session ID: {info[0]}.'
        if session_range_info is not None and session_range_info[1] + 1 < 20:
            cursor.execute(f"SELECT Role_ID FROM Level_Range WHERE level = ?", (session_range_info[1] + 1, ))
            overflow_range_id = cursor.fetchone()
            session_ranges = f'<@&{session_range_id}> AND <@&{overflow_range_id[0]}>'
        else:
            session_ranges = f'<@&{session_range_id}>'
    elif overflow == 3:
        footer_text = f'Session ID: {info[0]}.'
        cursor.execute(f"SELECT min(level), max(level) FROM Level_Range WHERE Role_ID = ?", (session_range_id,))
        session_range_info = cursor.fetchone()
        if session_range_info is not None and session_range_info[0] - 1 > 3:
            cursor.execute(f"SELECT Role_ID FROM Level_Range WHERE level = ?", (session_range_info[0] - 1,))
            overflow_range_id = cursor.fetchone()
            session_ranges = f'<@&{session_range_id}> AND <@&{overflow_range_id[0]}>'
        else:
            session_ranges = f'<@&{session_range_id}>'
    else:
        session_ranges = f'<@&{session_range_id}>'
        footer_text = f'Session ID: {info[0]}. Any level can join.'
    try:
        embed.set_author(name=f'{author}')
        embed.add_field(name="Session Range", value=session_ranges)
        embed.add_field(name="Player Limit", value=f'{player_limit}')
        embed.add_field(name="Date & Time:", value=f'{date} at {hour} which is {arrival}', inline=False)
        embed.add_field(name="Overview:", value=f'{overview}', inline=False)
        embed.add_field(name="Description:", value=f'{description}', inline=False)
        embed.set_footer(text=footer_text)
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        sessions_channel = cursor.fetchone()
        session_channel = await bot.fetch_channel(sessions_channel[0])
        session_text = f'<@{interaction.user.id}> is running a session.\r\n{session_ranges}'
        msg = await session_channel.send(content=session_text, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        message = msg.id
        thread = await msg.create_thread(name=f"{info[0]}: {session_name}", auto_archive_duration=60, reason=f"{description}")
        await EventCommand.create_session_message(self, info[0], message, thread.id, guild_id)
        await interaction.response.send_message(f"Session created! Session ID: {info[0]}.", ephemeral=True)
        cursor.close()
        db.close()
    except discord.app_commands.errors.CommandInvokeError:
        embed = discord.Embed(title=f"{session_name}", description=f"Session Range: {session_range}", color=discord.Colour.red())
        embed.set_author(name=f'{author}')
        embed.add_field(name="Play Location", value=f'{play_location}')
        embed.add_field(name="Player Limit", value=f'{player_limit}')
        embed.add_field(name="Date & Time:", value=f'{date} at {hour} which is {arrival}', inline=False)
        embed.add_field(name="Overview:", value=f'{overview}', inline=False)
        embed.add_field(name="Description:", value=f'{description}', inline=False)
        embed.set_footer(text=footer_text)
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        sessions_channel = cursor.fetchone()
        session_channel = await bot.fetch_channel(sessions_channel[0])
        session_text = f'<@{interaction.user.id}> is running a session.\r\n{session_ranges}'
        msg = await session_channel.send(content=session_text, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        thread = await msg.create_thread(name=f"Session name: {session_name} Session ID: {info[0]}", auto_archive_duration=60, reason=f"{description}")
        message = msg.id
        await interaction.response.send_message(f"Session created! Session ID: {info[0]}.", ephemeral=True)
        await EventCommand.create_session_message(self, {info[0]}, message, thread.id, guild_id)
        cursor.close()
        db.close()


@gamemaster.command()
@app_commands.describe(overflow="Allow for adjust role ranges!")
@app_commands.choices(overflow=[discord.app_commands.Choice(name='current range only!', value=1), discord.app_commands.Choice(name='include next level bracket!', value=2),discord.app_commands.Choice(name='include lower level bracket!', value=3),discord.app_commands.Choice(name='ignore role requirements!', value=4)])
async def edit(interaction: discord.Interaction, session_id: int, session_range: typing.Optional[discord.Role], session_name: typing.Optional[str], player_limit: typing.Optional[int], play_location: typing.Optional[str], game_link: typing.Optional[str], hammer_time: typing.Optional[str], overview: typing.Optional[str], description: typing.Optional[str], overflow: typing.Optional[discord.app_commands.Choice[int]]):
    """GM: Edit an Active Session."""
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    sql = f"SELECT Message, Session_Name, Session_Range_ID, Play_Location, Play_Time, game_link, Overview, Description, Player_Limit, Session_Range, overflow from Sessions WHERE Session_ID = ? AND GM_Name = ? AND IsActive = ? ORDER BY Created_Time Desc Limit 1"
    val = (session_id, author, 1)
    cursor.execute(sql, val)
    info = cursor.fetchone()
    if info is not None:
        overflow = info[10] if overflow is None else overflow.value
        if session_range is not None:
            session_range = session_range
            session_range_name = session_range.name
            session_range_id = session_range.id
        else:
            session_range = info[2]
            session_range_id = info[2]
            session_range_name = info[9]
        if session_name is not None:
            session_name = session_name
        else:
            session_name = info[1]
        if player_limit is not None:
            player_limit = player_limit
        else:
            player_limit = info[8]
        if play_location is not None:
            play_location = play_location
        else:
            play_location = info[3]
        if game_link is not None:
            game_link_valid = game_link[0:4]
            if str.lower(game_link_valid) == 'http':
                embed = discord.Embed(title=f"{session_name}", url=f'{game_link}', description=f"Play Location: {play_location}", color=discord.Colour.blue())
            else:
                game_link = 'HTTPS://' + game_link
                embed = discord.Embed(title=f"{session_name}", url=f'{game_link}', description=f"Play Location: {play_location}", color=discord.Colour.blue())
        elif game_link is None and info[5] is not None:
            game_link = info[5]
            embed = discord.Embed(title=f"{session_name}", url=f'{game_link}', description=f"Play Location: {play_location}", color=discord.Colour.blue())
        else:
            embed = discord.Embed(title=f"{session_name}", description=f"Play Location: {play_location}", color=discord.Colour.blue())
        if hammer_time is not None:
            hammer_timing = hammer_time[0:3]
            if hammer_timing == "<t:":
                timing = hammer_time[3:13]
                date = "<t:" + timing + ":D>"
                hour = "<t:" + timing + ":t>"
                arrival = "<t:" + timing + ":R>"
            else:
                timing = hammer_time
                date = "<t:" + timing + ":D>"
                hour = "<t:" + timing + ":t>"
                arrival = "<t:" + timing + ":R>"
        else:
            timing = info[4]
            date = "<t:" + timing + ":D>"
            hour = "<t:" + timing + ":t>"
            arrival = "<t:" + timing + ":R>"
        if overview is not None:
            overview = overview
        else:
            overview = info[6]
        if description is not None:
            description = description
        else:
            description = info[7]
        print(overflow)
        print(session_id)
        if overflow == 1:
            footer_text = f'Session ID: {session_id}.'
            session_ranges = f'<@&{session_range_id}>'
        elif overflow == 2:
            footer_text = f'Session ID: {session_id}.'
            cursor.execute(f"SELECT min(level), max(level) FROM Level_Range WHERE Role_ID = ?", (session_range_id,))
            session_range_info = cursor.fetchone()
            if session_range_info is not None and session_range_info[1] + 1 < 20:
                cursor.execute(f"SELECT Role_ID FROM Level_Range WHERE level = ?", (session_range_info[1] + 1,))
                overflow_range_id = cursor.fetchone()
                session_ranges = f'<@&{session_range_id}> AND <@&{overflow_range_id[0]}>'
            else:
                session_ranges = f'<@&{session_range_id}>'
        elif overflow == 3:
            footer_text = f'Session ID: {session_id}.'
            cursor.execute(f"SELECT min(level), max(level) FROM Level_Range WHERE Role_ID = ?", (session_range_id,))
            session_range_info = cursor.fetchone()
            print(session_range_info)
            if session_range_info is not None and session_range_info[0] - 1 > 3:
                cursor.execute(f"SELECT Role_ID FROM Level_Range WHERE level = ?", (session_range_info[0] - 1,))
                overflow_range_id = cursor.fetchone()
                session_ranges = f'<@&{session_range_id}> AND <@&{overflow_range_id[0]}>'
            else:
                session_ranges = f'<@&{session_range_id}>'
        else:
            session_ranges = f'<@&{session_range_id}>'
            footer_text = f'Session ID: {session_id}. Any level can join.'
        print(footer_text)
        await EventCommand.edit_session(self, guild_id, author, session_id, session_name, session_range_name, session_range_id, play_location, timing, game_link, overflow)
        embed.set_author(name=f'{author}')
        embed.add_field(name="Session Range", value=session_ranges)
        embed.add_field(name="Play Location", value=f'{play_location}')
        embed.add_field(name="Player Limit", value=f'{player_limit}')
        embed.add_field(name="Date & Time:", value=f'{date} at {hour} which is {arrival}', inline=False)
        embed.add_field(name="Overview:", value=f'{overview}', inline=False)
        embed.add_field(name="Description:", value=f'{description}', inline=False)
        embed.set_footer(text=footer_text)
        print(info)
        session_content = f'<@{interaction.user.id}> is running a session.\r\n{session_ranges}'
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        session_channel_info = cursor.fetchone()
        session_channel = await bot.fetch_channel(session_channel_info[0])
        msg = await session_channel.fetch_message(info[0])
        role = guild.get_role(session_range_id)
        await msg.edit(embed=embed, content=session_content)
        await interaction.response.send_message(content=f"The following session of {session_name} located at {msg.jump_url} has been updated.", allowed_mentions=discord.AllowedMentions(roles=True,))
    if info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id} associated with host {author}")
    cursor.close()
    db.close()


@gamemaster.command()
async def delete(interaction: discord.Interaction, session_id: int):
    """Delete an ACTIVE Session."""
    guild_id = interaction.guild_id
    guild = interaction.guild
    author = interaction.user.name
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    sql = f"SELECT Message, Session_Thread, Session_Name from Sessions WHERE Session_ID = ? AND GM_Name = ? AND IsActive = ? ORDER BY Created_Time Desc Limit 1"
    val = (session_id, author, 1)
    cursor.execute(sql, val)
    info = cursor.fetchone()
    if info is not None:
        embed = discord.Embed(title=f"{info[1]}", description=f"This session has been cancelled.", color=discord.Colour.red())
        await EventCommand.delete_session(self, session_id, guild_id, author)
        embed.set_author(name=f'{author}')
        embed.set_footer(text=f'Session ID: {session_id}.')
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        session_channel_info = cursor.fetchone()
        session_channel = await bot.fetch_channel(session_channel_info[0])
        msg = await session_channel.fetch_message(info[0])
        await msg.edit(embed=embed)
        await interaction.response.send_message(content=f"the following session of {info[2]} located at {msg.jump_url} has been cancelled.", ephemeral=True)
        thread = guild.get_thread(info[1])
        await thread.delete()
    if info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id} associated with host {author}")
    cursor.close()
    db.close()


# noinspection PyUnresolvedReferences
@gamemaster.command()
@app_commands.autocomplete(specific_character=character_select_autocompletion)
@app_commands.describe(randomizer="for the purposes of picking a number of randomized players")
@app_commands.describe(specific_character="Picking a specific player's character. You will have to use their CHARACTER Name for this.")
async def accept(interaction: discord.Interaction, session_id: int, player_1: typing.Optional[discord.Member], player_2: typing.Optional[discord.Member], player_3: typing.Optional[discord.Member], player_4: typing.Optional[discord.Member], player_5: typing.Optional[discord.Member], player_6: typing.Optional[discord.Member], specific_character: typing.Optional[str], randomizer: int = 0):
    """GM: Accept player Sign-ups into your session for participation"""
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Session_Name, Play_location, Play_Time, game_link FROM Sessions WHERE Session_ID = '{session_id}' AND GM_Name = '{author}'")
    session_info = cursor.fetchone()
    accepted_characters = 0
    if session_info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id} associated with host {author}")
    elif randomizer < 0:
        await interaction.response.send_message(f"Cannot have a negative number of randomized players! {randomizer} is not acceptable!")
    else:
        cursor.execute(f"SELECT count(character_name) FROM Sessions_Participants WHERE Session_ID = {session_id}")
        accepted_players = cursor.fetchone()
        if accepted_players[0] < 20:
            accepted_characters += accepted_players[0]
            cursor.execute(f"SELECT count(character_name) FROM Sessions_Signups WHERE Session_ID = {session_id}")
            players = cursor.fetchone()
            print(players)
            print(accepted_characters)
            if players[0] > 0:
                timing = session_info[2]
                date = "<t:" + timing + ":D>"
                hour = "<t:" + timing + ":t>"
                arrival = "<t:" + timing + ":R>"
                mentions = f"the following players: "
                if session_info[3] is not None:
                    embed = discord.Embed(title=f"{session_info[0]}", url=f'{session_info[3]}', description=f"Date & Time: {date} at {hour} which is {arrival}", color=discord.Colour.green())
                else:
                    embed = discord.Embed(title=f"{session_info[0]}", description=f"Date & Time: {date} at {hour} which is {arrival}", color=discord.Colour.green())
                embed.set_author(name=f'{author}')
                if randomizer == 0 and player_1 is None and player_2 is None and player_3 is None and player_4 and player_5 is None and player_6 is None and specific_character is None:
                    await interaction.response.send_message(f"a session without players is like a drought with rain.")
                else:
                    if player_1 is not None:
                        player_name = player_1.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_1.id}> '
                        if player_info is None and signups_information is None:
                            embed.add_field(name=f'**Not Accepted!**:', value=f"<@{player_1.id}> had no characters signed up for this session!")
                        elif signups_information is not None:
                            embed.add_field(name=f'**No Duplicates!**:', value=f" <@{player_1.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await EventCommand.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_1.name, player_1.id, author, player_info[3])
                            embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with Player: <@{player_1.id}>!")
                    if player_2 is not None and player_2 != player_1:
                        player_name = player_2.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_2.id}> '
                        if player_info is None and signups_information is None:
                            embed.add_field(name=f'**Not Accepted!**:', value=f"<@{player_2.id}> had no characters signed up for this session!")
                        elif signups_information is not None:
                            embed.add_field(name=f'**No Duplicates!**:', value=f" <@{player_2.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await EventCommand.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_2.name, player_2.id, author, player_info[3])
                            embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with Player: <@{player_2.id}>!")
                    if player_3 is not None and player_3 != player_1 and player_3 != player_2:
                        player_name = player_3.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_3.id}> '
                        if player_info is None:
                            embed.add_field(name=f'**Not Accepted!**:', value=f"<@{player_3.id}> had no characters signed up for this session!")
                        elif signups_information is not None and signups_information is None:
                            embed.add_field(name=f'**No Duplicates!**:', value=f" <@{player_3.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await EventCommand.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_3.name, player_3.id, author, player_info[3])
                            embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with Player: <@{player_3.id}>!")
                    if player_4 is not None and player_4 != player_1 and player_4 != player_2 and player_4 != player_3:
                        player_name = player_4.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_4.id}> '
                        if player_info is None:
                            embed.add_field(name=f'**Not Accepted!**:',
                                            value=f" <@{player_4.id}> had no characters signed up for this session!")
                        elif signups_information is not None:
                            embed.add_field(name=f'**No Duplicates!**:',
                                            value=f" <@{player_4.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await EventCommand.accept_player(self, guild_id, session_info[0], session_id, player_info[0],
                                                      player_info[1], player_info[2], player_4.name, player_4.id, author,
                                                      player_info[3])
                            embed.add_field(name=f'{player_info[0]}',
                                            value=f"has been accepted with Player: <@{player_4.id}>!")
                    if player_5 is not None and player_5 != player_1 and player_5 != player_2 and player_5 != player_3 and player_5 != player_4:
                        player_name = player_5.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_5.id}> '
                        if player_info is None:
                            embed.add_field(name=f'**Not Accepted!**:',
                                            value=f" <@{player_5.id}> had no characters signed up for this session!")
                        elif signups_information is not None:
                            embed.add_field(name=f'**No Duplicates!**:',
                                            value=f" <@{player_5.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await EventCommand.accept_player(self, guild_id, session_info[0], session_id, player_info[0],
                                                      player_info[1], player_info[2], player_5.name, player_5.id, author,
                                                      player_info[3])
                            embed.add_field(name=f'{player_info[0]}',
                                            value=f"has been accepted with Player: <@{player_5.id}>!")
                    if player_6 is not None and player_6 != player_1 and player_6 != player_2 and player_6 != player_3 and player_6 != player_4 and player_6 != player_5:
                        player_name = player_6.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_6.id}> '
                        if player_info is None:
                            embed.add_field(name=f'**Not Accepted!**:',
                                            value=f" <@{player_6.id}> had no characters signed up for this session!")
                        elif signups_information is not None:
                            embed.add_field(name=f'**No Duplicates!**:',
                                            value=f" <@{player_6.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await EventCommand.accept_player(self, guild_id, session_info[0], session_id, player_info[0],
                                                      player_info[1], player_info[2], player_6.name, player_6.id, author,
                                                      player_info[3])
                            embed.add_field(name=f'{player_info[0]}',
                                            value=f"has been accepted with Player: <@{player_6.id}>!")
                    if specific_character is not None:
                        sql = f"Select Character_Name, Level, Gold_value, Player_Name, Player_ID, Tier FROM Player_Characters WHERE Character_Name = ?"
                        val = (specific_character,)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        if player_info is not None:
                            accepted_characters += 1
                            await EventCommand.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_info[3], player_info[4], author, player_info[5])
                            embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with player: @{player_info[4]}!")
                            mentions += f'<@{player_info[4]}> '
                    if randomizer > 0:
                        characters_total = players[0] - accepted_characters
                        randomizer = players[0] if randomizer > characters_total else randomizer
                        for x in range(randomizer):
                            random_number = random.randint(1, characters_total)
                            random_number -= 1
                            characters_total -= 1
                            accepted_characters += 1
                            cursor.execute(f"Select Character_Name, Level, Effective_Wealth, Player_Name, Player_ID, Tier FROM Sessions_Signups WHERE Session_ID = '{session_id}' LIMIT 1 OFFSET {random_number}")
                            player_info = cursor.fetchone()
                            print(x, player_info)
                            if accepted_characters <= 20:
                                await EventCommand.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_info[3], player_info[4], author, player_info[5])
                                embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with player: @{player_info[3]}!")
                                mentions += f'<@{player_info[4]}> '
                            else:
                                break
                    mentions += f"have been accepted!"
                    embed.set_footer(text=f"Session ID: {session_id}")
                    await interaction.response.send_message(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            else:
                print(session_info[3])
                if specific_character is not None:
                    sql = f"Select Character_Name, Level, Gold_value, Player_Name, Player_ID, Tier FROM Player_Characters WHERE Character_Name = ?"
                    val = (specific_character,)
                    cursor.execute(sql, val)
                    player_info = cursor.fetchone()
                    if player_info is not None:
                        timing = session_info[2]
                        date = "<t:" + timing + ":D>"
                        hour = "<t:" + timing + ":t>"
                        arrival = "<t:" + timing + ":R>"
                        mentions = f"the following players: "
                        if session_info[3] is not None:
                            embed = discord.Embed(title=f"{session_info[0]}", url=f'{session_info[3]}',
                                                  description=f"Date & Time: {date} at {hour} which is {arrival}",
                                                  color=discord.Colour.green())
                        else:
                            embed = discord.Embed(title=f"{session_info[0]}",
                                                  description=f"Date & Time: {date} at {hour} which is {arrival}",
                                                  color=discord.Colour.green())
                        embed.set_author(name=f'{author}')
                        accepted_characters += 1
                        await EventCommand.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_info[3], player_info[4], author, player_info[5])
                        embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with player: @{player_info[4]}!")
                        mentions += f'<@{player_info[4]}> '
                        embed.set_footer(text=f"Session ID: {session_id}")

                    else:
                        embed = discord.Embed(title=f"{session_info[0]} signups failed!", description=f"This character was not found.", color=discord.Colour.green())
                if session_info[3] is not None:
                    embed = discord.Embed(title=f"{session_info[0]} signups failed!", url=f'{session_info[3]}', description=f"there are no players signed up for this session", color=discord.Colour.green())
                else:
                    embed = discord.Embed(title=f"{session_info[0]} signups failed!", description=f"there are no players signed up for this session", color=discord.Colour.green())
                embed.set_author(name=f'{author}')
                print(embed)
                if mentions is not None:
                    await interaction.response.send_message(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
                else:
                    await interaction.response.send_message(embed=embed)
        else:
            if session_info[3] is not None:
                embed = discord.Embed(title=f"{session_info[0]} signups failed!", url=f'{session_info[3]}', description=f"20 IS THE HARD CAP. GO MAKE A SEPARATE SESSION FOR HANDLING REWARDS.", color=discord.Colour.green())
            else:
                embed = discord.Embed(title=f"{session_info[0]} signups failed!", description=f"20 IS THE HARD CAP. GO MAKE A SEPARATE SESSION FOR HANDLING REWARDS.", color=discord.Colour.green())
            embed.set_author(name=f'{author}')
            await interaction.response.send_message(embed=embed)
    cursor.close()
    db.close()


@gamemaster.command()
async def remove(interaction: discord.Interaction, session_id: int, player: discord.Member):
    """GM: Kick a player out of your session or remove them from rewards"""
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    guild = interaction.guild
    cursor.execute(f"SELECT Session_Name, Play_location, Play_Time, game_link, IsActive, Gold, Flux, Alt_Reward_All FROM Sessions WHERE Session_ID = '{session_id}'")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id}")
    else:
        if session_info[4] == 1:
            cursor.execute(f"SELECT Player_Name, Character_Name FROM Sessions_Participants WHERE Session_ID = '{session_id}' and Player_Name = '{player.name}'")
            player_info = cursor.fetchone()
            if player_info is None:
                await interaction.response.send_message(f"{player.name} does not appear to be participating in the session of {session_info[0]} with session ID: {session_id}")
            else:
                player_name = player.name
                character_name = player_info[1]
                await EventCommand.remove_player(self, guild_id, session_id, player_name, character_name, author)
                await interaction.response.send_message(f"{player.name} has been removed from Session {session_info[0]} with ID: {session_id}")
        else:
            cursor.execute(f"SELECT Player_Name, Character_Name, Level, Effective_Gold, Received_Milestones, Received_Trials, Received_Gold, Alt_Reward_Personal, Received_Fame FROM Sessions_Archive WHERE Session_ID = '{session_id}' and Player_Name = '{player.name}'")
            reward_info = cursor.fetchone()
            if reward_info is None:
                await interaction.response.send_message(
                    f"{player.name} does not appear to have participated in the session of {session_info[0]} with session ID: {session_id}")
            else:
                buttons = ["✅", "❌"]  # checkmark X symbol
                embed = discord.Embed(title=f"are you sure you want to revoke rewards from {reward_info[1]}?", description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
                await interaction.response.send_message(embed=embed)
                msg = await interaction.original_response()
                for button in buttons:
                    await msg.add_reaction(button)
                while True:
                    try:
                        reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == interaction.user.id and reaction.emoji in buttons, timeout=60.0)
                    except asyncio.TimeoutError:
                        embed.set_footer(text="Request has timed out.")
                        await msg.edit(embed=embed)
                        await msg.clear_reactions()
                        return print("timed out")
                    else:
                        if reaction.emoji == u"\u264C":
                            embed = discord.Embed(title=f"You have thought better of revoking rewards from {reward_info[1]}", description=f"Savings!", colour=discord.Colour.blurple())
                            await msg.edit(embed=embed)
                            await msg.clear_reactions()
                        if reaction.emoji == u"\u2705":
                            embed = discord.Embed(title=f"Reward Change has occurred!", description=f"Rewards Revoked from {reward_info[1]}.", colour=discord.Colour.red())
                            await msg.clear_reactions()
                            await msg.edit(embed=embed)
                            character_name = reward_info[1]
                            cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name, character_name))
                            player_info = cursor.fetchone()
                            cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                            transaction_id = cursor.fetchone()
                            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                            accepted_bio_channel = cursor.fetchone()
                            milestone_total = player_info[9] - reward_info[4]
                            level_information = level_calculation(guild_id, player_info[9], -abs(reward_info[4]), player_info[29])
                            mythic_information = mythic_calculation(guild_id, player_info[7], player_info[11], -abs(reward_info[5]))
                            await EventCommand.session_rewards(self, author, guild_id, player_info[2], level_information[0], milestone_total, level_information[1], player_info[16] - session_info[6], mythic_information[0], player_info[11] - reward_info[5], mythic_information[1], player_info[27] - reward_info[8], player[30] - reward_info[8], session_id)
                            await EventCommand.gold_change(self, guild_id, player_info[0], player_info[1], player_info[2], reward_info[6] * -1, reward_info[6] * -1, session_info[5] * -1, 'Session removing session_reward', 'removing session_reward')
                            bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], level_information[0], mythic_information[0], player_info[9] + -abs(reward_info[4]), level_information[1], player_info[11] + -abs(reward_info[5]), mythic_information[1], player_info[13] - reward_info[6], player_info[14] - reward_info[6], player_info[16] - session_info[6], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                            bio_message = await bio_channel.fetch_message(player_info[24])
                            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                            source = f"Session Reward removed with Session ID: {session_id}"
                            reward_all = None if session_info[7] is None else f"Removed the following: {session_info[7]}"
                            logging_embed = log_embed(player_info[2], author, level_information[0], -abs(reward_info[4]), player_info[9] + -abs(reward_info[4]), level_information[1], mythic_information[0], reward_info[5], player_info[11] + -abs(reward_info[5]), mythic_information[1], player_info[13] - reward_info[6], reward_info[5], player_info[14] - reward_info[6], transaction_id[0], player_info[16] - session_info[6], -abs(session_info[6]), None, None, None, None, reward_all, None, None, None, None, source)
                            logging_thread = guild.get_thread(player_info[25])
                            await logging_thread.send(embed=logging_embed)
                            cursor.close()
                            db.close()
                            await EventCommand.remove_player(self, guild_id, session_id, reward_info[0], reward_info[1], author)
    cursor.close()
    db.close()


@gamemaster.command()
@app_commands.describe(reward_all="A reward for each individual member of the party")
@app_commands.describe(party_reward="A reward for the party to divy up amongst themselves, or not. Link a google doc if reward exceeds character limit.")
@app_commands.describe(overview="This accepts either a google docs link or an overview. Use Double Spacing with the Docs link.")
async def reward(interaction: discord.Interaction, session_id: int, gold: float, easy: int = 0, medium: int = 0, hard: int = 0, deadly: int = 0, trials: int = 0, reward_all: str = None, fame: int = 2, prestige: int = 2, party_reward: str = None, overview: str = None):
    """GM: Reward Players for Participating in your session."""
    awarded_flux = 10
    if gold < 0 or easy < 0 or medium < 0 or hard < 0 or deadly < 0 or awarded_flux < 0 or trials < 0:
        await interaction.response.send_message(f"Your players might not judge you out loud for trying to give them a negative award, but I do...")
    elif gold == 0 and easy == 0 and medium == 0 and hard == 0 and deadly == 0 and awarded_flux == 0 and trials == 0 and reward_all is None and party_reward is None:
        await interaction.response.send_message(f"Your players have been rewarded wi-- wait a minute, what the fuck? No Rewards?! No! At least give them a silver or a milestone!")
    guild_id = interaction.guild_id
    guild = interaction.guild
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT GM_Name, Session_Name, Session_Range, Play_Location, Play_Time, Message, Session_Thread, IsActive, Related_Plot FROM Sessions WHERE Session_ID = {session_id} LIMIT 1""")
    session_info = cursor.fetchone()
    if session_info is not None:
        if session_info[7] == 1:
            mentions = f"Session Rewards for {session_info[1]}: "
            cursor.execute(f"""SELECT Player_Name, Player_ID, Character_Name, Level, Tier, Effective_Wealth  FROM Sessions_Participants WHERE Session_ID = {session_id}""")
            session_players = cursor.fetchall()

            if session_players == []:
                await interaction.response.send_message(f"No players could be found participating in session with {session_id} can be found!")
            elif session_players is not None:

                await interaction.response.defer(thinking=True, ephemeral=True)
                if overview is not None:
                    plot = session_info[8]
                    plot = '9762aebb-43ae-47d5-8c7b-30c34a55b9e5' if plot is None else plot
                    significance = 0
                    significance += 1 * easy + 2 * medium + 3 * hard + 4 * deadly + 2 * trials
                    significance = 5 if significance > 5 else significance
                    await EventCommand.report(self, guild_id, 2, plot, overview, session_id, author, significance)
                    cursor.execute(f"""SELECT Article_Link from Sessions where Session_ID = ?""", (session_id,))
                    session_link = cursor.fetchone()
                    embed = discord.Embed(title=f"{session_info[1]}", description=f"Session Report", url=session_link[0], color=discord.Colour.green())
                else:
                    embed = discord.Embed(title=f"{session_info[1]}", description=f"Session Report", color=discord.Colour.green())
                embed.set_footer(text=f"Session ID is {session_id}")
                for player in session_players:
                    mentions += f"<@{player[1]}> "
                    character_name = player[2]
    #                Setting Job Rewards
                    cursor.execute(f"""SELECT Easy, Medium, Hard, Deadly from AA_Milestones WHERE level = {player[3]}""")
                    job_info = cursor.fetchone()
                    easy_jobs = easy * job_info[0]
                    medium_jobs = medium * job_info[1]
                    hard_jobs = hard * job_info[2]
                    deadly_jobs = deadly * job_info[3]
                    rewarded = easy_jobs + medium_jobs + hard_jobs + deadly_jobs

    #                Done Setting Job Rewards
    #                Obtaining Character Information
                    print(f"CHARACTER NAME IS {character_name}")
                    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link, Accepted_Date FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name, character_name))
                    player_info = cursor.fetchone()
                    # The specific date you want to compare
                    end_date = datetime.datetime.strptime(player_info[32], '%Y-%m-%d %H:%M')
                    # Current date and time
                    current_date = datetime.datetime.now()
                    # Calculate the difference between dates
                    difference = current_date - end_date
                    # Get the difference in days
                    if player_info[7] >= 7:
                        if 90 <= difference.days < 120:
                            flux_multiplier = 2
                        elif difference.days >= 120:
                            flux_multiplier = 2 + math.floor((difference.days-90) / 30)
                            flux_multiplier = flux_multiplier if flux_multiplier <= 4 else 4
                        else:
                            flux_multiplier = 1
                    else:
                        flux_multiplier = 1
                    awarded_flux = 10 * flux_multiplier
                    print(f"Player flux info is {player_info[16]}")
                    flux_total = player_info[16] + awarded_flux  #Setting the Flux
                    level_info = level_calculation(guild_id, player_info[9], rewarded, player_info[29])
                    gold_info = gold_calculation(level_info[0], player_info[6], player_info[13], player_info[14], player_info[15], gold)
                    mythic_info = mythic_calculation(guild_id, level_info[0], player_info[11], trials)
                    # Building Player Reward
                    response = f"Player: <@{player[1]}>'s character has received:"
                    if gold != 0:
                        response += f" {gold_info[3]} gold with a new total of {gold_info[0]} GP!"
                    else:
                        response = response
                    if rewarded != 0:
                        response += f" {rewarded} milestones!"
                    else:
                        response = response
                    if player[3] != level_info[0]:
                        response += f" and has leveled up to {level_info[0]}!"
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {player[3]}")
                        level_range = cursor.fetchone()
                        cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Desc")
                        level_range_max = cursor.fetchone()
                        cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Asc")
                        level_range_min = cursor.fetchone()
                        sql = f"Select True_Character_Name from Player_Characters WHERE Player_Name = ? AND level >= ? AND level <= ?"
                        val = (player[0], level_range_min[0], level_range_max[0])
                        cursor.execute(sql, val)
                        level_range_characters = cursor.fetchone()
                        # user = await bot.fetch_user(player[1])
                        member = await guild.fetch_member(player[1])
                        if level_range_characters is None:
                            cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {level_info[0]}")
                            new_level_range = cursor.fetchone()
                            role1 = guild.get_role(level_range[2])
                            role2 = guild.get_role(new_level_range[2])
                            await member.remove_roles(role1)
                            await member.add_roles(role2)
                        else:
                            cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {level_info[0]}")
                            new_level_range = cursor.fetchone()
                            role2 = guild.get_role(new_level_range[2])
                            await member.add_roles(role2)
                    prestige = prestige if player_info[30] + prestige <= player_info[27] + fame else player_info[27] + fame - player_info[30]
                    if trials != 0:
                        response += f" {trials} Mythic Trials!"
                    if player[4] != mythic_info[0]:
                        response += f" and has reached a new mythic tier of {mythic_info[0]}!"
                    if fame != 0:
                        response += f" also receiving {fame} fame for a total of {player_info[27] + fame}!"
                    if prestige != 0:
                        response += f" and {prestige} prestige for a total of {player_info[30] + prestige}!"
                    if awarded_flux != 0:
                        response += f" and {awarded_flux} flux for a total of {flux_total}!"
                    embed.add_field(name=f'**Character**: {player[2]}', value=response)
                    await EventCommand.session_rewards(self, author, guild_id, player[2], level_info[0], player_info[9] + rewarded, level_info[1], flux_total, mythic_info[0], player_info[11] + trials, mythic_info[1], player_info[27] + fame, player_info[30] + prestige, f"Session {session_id} reward")
                    await EventCommand.gold_change(self, guild_id, player[0], player[1], player[2], gold_info[3], gold_info[3], gold, 'Session Reward', 'Session Reward')
                    await EventCommand.session_log_player(self, guild_id, session_id, player_info[0], player_info[1], player_info[2], player[3], player[4], player[5], rewarded, trials, gold_info[3], fame, prestige, awarded_flux)
                    cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                    transaction_id = cursor.fetchone()
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    accepted_bio_channel = cursor.fetchone()

                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], level_info[0], mythic_info[0], player_info[9] + rewarded, level_info[1], player_info[11] + trials, mythic_info[1], player_info[13] + gold_info[3], player_info[14] + gold_info[3], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27] + fame, player_info[28], player_info[30]+prestige, player_info[31])
                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                    bio_message = await bio_channel.fetch_message(player_info[24])
                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                    source = f"Session Reward with Session ID: {session_id} and transaction ID: {transaction_id[0]}"
                    logging_embed = log_embed(player_info[2], author, level_info[0], rewarded, player_info[9] + rewarded, level_info[1], mythic_info[0], trials, player_info[11] + trials, mythic_info[1], player_info[13] + gold_info[3], gold_info[3], player_info[14] + gold_info[3], transaction_id[0], flux_total, awarded_flux, None, None, None, None, reward_all, player_info[27] + fame, fame, player_info[30] + prestige, prestige, source)
                    logging_thread = guild.get_thread(player_info[25])
                    print(f"logging thread is {logging_thread} \r\nplayer thread is {player_info[25]}")
                    try:
                        print(f"attempt 1 sending to logging thread ")
                        await logging_thread.send(embed=logging_embed)
                    except AttributeError as e:
                        try:
                            print(f"attempt 2 sending to logging thread")
                            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                            eventlog_channel = cursor.fetchone()
                            event_channel = bot.get_channel(eventlog_channel[0])
                            print(f"this is the event Channel {event_channel}")
                            logging_thread = event_channel.get_thread(player_info[25])
                            print(f"this is the {logging_thread} pulled hopefully from server not memory")
                            if logging_thread is not None:
                                logging_thread.archived = False;
                            await logging_thread.send(embed=logging_embed)
                        except AttributeError as e:
                            print(f"passing")
                            mentions += f"Note! Thread is archived!"
                            pass

                await interaction.followup.send(content=f"You have successfully run this command!", ephemeral=True)
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Quest_Rewards_Channel'")
                rewards_channel = cursor.fetchone()
                reward_channel = await bot.fetch_channel(rewards_channel[0])
                reward_msg = await reward_channel.send(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
                if party_reward is not None:
                    reward_thread = await reward_msg.create_thread(name=f"Session name: {session_info[1]} Party Rewards, Session ID: {session_id}", auto_archive_duration=60, reason=f"{party_reward}")
                    reward_thread_id = reward_thread.id
                    party_reward_embed = discord.Embed(title=f"{session_info[1]}", description=f"Party Reward Display", color=discord.Colour.green())
                    party_reward_embed.set_footer(text=f"Session ID is {session_id}")
                    party_reward_embed.add_field(name=f'**Party Reward**: ', value=f"{party_reward}")
                    await reward_thread.send(embed=party_reward_embed)
                else:
                    reward_thread_id = None
                await EventCommand.session_log(self, guild_id, session_id, gold, 10, easy, medium, hard, deadly, trials, reward_all, party_reward, reward_msg.id, reward_thread_id, fame, prestige)

                cursor.close()
                db.close()
        else:
            await interaction.response.send_message(f"Session found with {session_id} but it is archived! Please submit a request to your admin to address!")
    if session_info is None:
        await interaction.response.send_message(f"No active session with {session_id} can be found!")

@gamemaster.command()
async def endow(interaction: discord.Interaction, session_id: int, player_1: typing.Optional[discord.Member], player_1_reward: typing.Optional[str], player_2: typing.Optional[discord.Member], player_2_reward: typing.Optional[str], player_3: typing.Optional[discord.Member], player_3_reward: typing.Optional[str], player_4: typing.Optional[discord.Member], player_4_reward: typing.Optional[str], player_5: typing.Optional[discord.Member], player_5_reward: typing.Optional[str], player_6: typing.Optional[discord.Member], player_6_reward: typing.Optional[str]):
    """GM: Reward Players for Participating in your session."""
    guild_id = interaction.guild_id
    guild = interaction.guild
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT GM_Name, Session_Name, Session_Range, Play_Location, Play_Time, Message FROM Sessions WHERE Session_ID = {session_id} LIMIT 1""")
    session_info = cursor.fetchone()
    await interaction.response.defer(thinking=True)
    if session_info is not None:
        embed = discord.Embed(title=f"{session_info[1]}", description=f"Personal Reward Display", color=discord.Colour.green())
        embed.set_footer(text=f"Session ID is {session_id}")
        if player_1 is not None and player_1_reward is not None:
            cursor.execute(f"""SELECT Character_Name FROM Sessions_Archive WHERE Player_Name = '{player_1.name}' AND Session_ID = {session_id}""")
            session_player_info = cursor.fetchone()
            response = f"<@{player_1.id}> "
            if session_player_info is not None:
                cursor.execute(f"""SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?""", (session_player_info[0],))
                character_info = cursor.fetchone()
                await EventCommand.session_endowment(self, author, guild_id, session_id, player_1.name, player_1_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_1_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_1_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_1.name}', value=response, inline=False)
        if player_2 is not None and player_2_reward is not None:
            cursor.execute(f"""SELECT Character_Name FROM Sessions_Archive WHERE Player_Name = '{player_2.name}' AND Session_ID = {session_id}""")
            session_player_info = cursor.fetchone()
            response = f"<@{player_2.id}> "
            if session_player_info is not None:
                cursor.execute(f"""SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?""",(session_player_info[0],))
                character_info = cursor.fetchone()
                await EventCommand.session_endowment(self, author, guild_id, session_id, player_2.name, player_2_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_2_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_2_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_2.name}', value=response, inline=False)
        if player_3 is not None and player_3_reward is not None:
            cursor.execute(f"""SELECT Character_Name FROM Sessions_Archive WHERE Player_Name = '{player_3.name}' AND Session_ID = {session_id}""")
            session_player_info = cursor.fetchone()
            response = f"<@{player_3.id}> "
            if session_player_info is not None:
                cursor.execute(f"""SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?""",(session_player_info[0],))
                character_info = cursor.fetchone()
                await EventCommand.session_endowment(self, author, guild_id, session_id, player_3.name, player_3_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_3_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_3_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_3.name}', value=response, inline=False)
        if player_4 is not None and player_4_reward is not None:
            cursor.execute(f"""SELECT Character_Name FROM Sessions_Archive WHERE Player_Name = '{player_4.name}' AND Session_ID = {session_id}""")
            session_player_info = cursor.fetchone()
            response = f"<@{player_4.id}> "
            if session_player_info is not None:
                cursor.execute(f"""SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?""",(session_player_info[0],))
                character_info = cursor.fetchone()
                await EventCommand.session_endowment(self, author, guild_id, session_id, player_4.name, player_4_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_4_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_4_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_4.name}', value=response, inline=False)
        if player_5 is not None and player_5_reward is not None:
            cursor.execute(f"""SELECT Character_Name FROM Sessions_Archive WHERE Player_Name = '{player_5.name}' AND Session_ID = {session_id}""")
            session_player_info = cursor.fetchone()
            response = f"<@{player_5.id}> "
            if session_player_info is not None:
                cursor.execute(f"""SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?""", (session_player_info[0],))
                character_info = cursor.fetchone()
                await EventCommand.session_endowment(self, author, guild_id, session_id, player_5.name, player_5_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_5_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_5_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_5.name}', value=response, inline=False)
        if player_6 is not None and player_6_reward is not None:
            cursor.execute(f"""SELECT Character_Name, Thread_ID FROM Sessions_Archive WHERE Player_Name = '{player_6.name}' AND Session_ID = {session_id}""")
            session_player_info = cursor.fetchone()
            response = f"<@{player_6.id}> "
            if session_player_info is not None:
                cursor.execute(f"""SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?""", (session_player_info[0],))
                character_info = cursor.fetchone()
                await EventCommand.session_endowment(self, author, guild_id, session_id, player_6.name, player_6_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_6_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_6_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_6.name}', value=response, inline=False)
        await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=False))
    cursor.close()
    db.close()
    if session_info is None:
        await interaction.followup.send(f"No active session with {session_id} can be found!")



@gamemaster.command()
@app_commands.describe(forego="Accept only part of a session reward!")
@app_commands.choices(forego=[discord.app_commands.Choice(name='all!', value=1), discord.app_commands.Choice(name='Forego Milestones!', value=2), discord.app_commands.Choice(name='Foregold!', value=3)])
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def claim(interaction: discord.Interaction, session_id: int, character_name: str, forego: discord.app_commands.Choice[int] = 1):
    guild_id = interaction.guild_id
    guild = interaction.guild
    author = interaction.user.name
    author_id = interaction.user.id
    user = interaction.user
    if forego == 1:
        forego = 1
    else:
        forego = forego.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    print(interaction.user.name)
    print(interaction.channel.id)
    cursor.execute(f"SELECT IsActive, GM_Name, Session_Name, Gold, Flux, Easy, Medium, Hard, Deadly, Trials, Fame, Prestige FROM Sessions WHERE Session_ID = '{session_id}' limit 1")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.response.send_message(f"No session with {session_id} can be found!")
    elif session_info[0] == 1:
        await interaction.response.send_message(f"The Session of {session_info[2]} is still active! !")
    else:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link, Accepted_Date FROM Player_Characters WHERE Player_Name = ? AND Character_Name = ? OR  Player_Name = ? AND Nickname =?", (author, character_name, author, character_name))
        validate_recipient = cursor.fetchone()
        if validate_recipient is not None:
            cursor.execute(f"SELECT Player_Name, Character_Name, Received_Milestones, Received_Trials, Received_Gold, Forego  FROM Sessions_Archive WHERE Session_ID = ? AND Player_Name = ?", (session_id, author))
            previous_rewards = cursor.fetchone()
            if previous_rewards is not None:
                print(previous_rewards[1])
                print(character_name)
                if previous_rewards[1] == character_name:
                    await interaction.response.send_message(f"you cannot claim for the same character of {character_name} when you already have claimed for them!!")
                else:
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    accepted_bio_channel = cursor.fetchone()
                    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters WHERE Character_Name = ?", (previous_rewards[1],))
                    previous_recipient = cursor.fetchone()
                    buttons = ["✅", "❌"]  # checkmark X symbol
                    embed = discord.Embed(title=f"are you sure you want to revoke rewards from {previous_recipient[2]} and claim them for {validate_recipient[2]}?", description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
                    await interaction.response.send_message(embed=embed)
                    msg = await interaction.original_response()
                    for button in buttons:
                        await msg.add_reaction(button)
                    while True:
                        try:
                            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == interaction.user.id and reaction.emoji in buttons, timeout=60.0)
                        except asyncio.TimeoutError:
                            embed.set_footer(text="Request has timed out.")
                            await msg.edit(embed=embed)
                            await msg.clear_reactions()
                            return print("timed out")
                        else:
                            if reaction.emoji == u"\u264C":
                                embed = discord.Embed(title=f"You have thought better of swapping the rewards", description=f"Savings!", colour=discord.Colour.blurple())
                                await msg.edit(embed=embed)
                                await msg.clear_reactions()
                            if reaction.emoji == u"\u2705":
                                embed = discord.Embed(title=f"Reward Change has occurred!", description=f"Rewards Revoked from {previous_recipient[2]} and claimed for {validate_recipient[2]}.",colour=discord.Colour.red())
                                await msg.clear_reactions()
                                await msg.edit(embed=embed)
                                character_name = previous_rewards[1]
                                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR  Nickname = ?", (character_name, character_name))
                                player_info = cursor.fetchone()
                                cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                                transaction_id = cursor.fetchone()
                                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                accepted_bio_channel = cursor.fetchone()
                                milestone_total = player_info[9] - previous_rewards[4]
                                level_information = level_calculation(guild_id, player_info[9], -abs(previous_rewards[4]), player_info[29])
                                mythic_information = mythic_calculation(guild_id, player_info[7], player_info[11], -abs(previous_rewards[5]))
                                await EventCommand.session_rewards(self, author, guild_id, player_info[2], level_information[0], milestone_total, level_information[1], player_info[16] - session_info[6], mythic_information[0], player_info[11] - previous_rewards[5], mythic_information[1], player_info[28] - previous_rewards[8], session_id)
                                await EventCommand.gold_change(self, guild_id, player_info[0], player_info[1], player_info[2],previous_rewards[6] * -1, previous_rewards[6] * -1, session_info[5] * -1, 'Session removing session_reward', 'removing session_reward')
                                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], level_information[0], mythic_information[0], player_info[9] + -abs(previous_rewards[4]), level_information[1], player_info[11] + -abs(previous_rewards[5]), mythic_information[1], player_info[13] - previous_rewards[6], player_info[14] - previous_rewards[6], player_info[16] - session_info[6], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                bio_message = await bio_channel.fetch_message(player_info[24])
                                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                source = f"Session Reward removed with Session ID: {session_id}"
                                reward_all = None if session_info[7] is None else f"Removed the following: {session_info[7]}"
                                logging_embed = log_embed(player_info[2], author, level_information[0], -abs(previous_rewards[4]), player_info[9] + -abs(previous_rewards[4]), level_information[1], mythic_information[0], previous_rewards[5], player_info[11] + -abs(previous_rewards[5]), mythic_information[1], player_info[13] - previous_rewards[6], previous_rewards[5], player_info[14] - previous_rewards[6], transaction_id[0], player_info[16] - session_info[6], -abs(session_info[6]), None, None, None, None, reward_all, None, None, None, None, source)
                                logging_thread = guild.get_thread(player_info[25])
                                await logging_thread.send(embed=logging_embed)
                                cursor.close()
                                db.close()
                                await EventCommand.remove_player(self, guild_id, session_id, previous_rewards[0], previous_rewards[1], author)
                                db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
                                cursor = db.cursor()
                                cursor.execute(f"""SELECT Easy, Medium, Hard, Deadly from AA_Milestones WHERE level = {validate_recipient[6]}""")
                                job_info = cursor.fetchone()
                                easy_jobs = session_info[5] * job_info[0]
                                medium_jobs = session_info[6] * job_info[1]
                                hard_jobs = session_info[7] * job_info[2]
                                deadly_jobs = session_info[8] * job_info[3]
                                rewarded = easy_jobs + medium_jobs + hard_jobs + deadly_jobs
                                rewarded = 0 if forego == 2 else rewarded
                                new_milestones = validate_recipient[8] + rewarded
                                level_information = level_calculation(guild_id, validate_recipient[8], rewarded, player_info[29])
                                print(level_information[0], validate_recipient[10], session_info[9], player_info[29])
                                mythic_information = mythic_calculation(guild_id, level_information[0], validate_recipient[10], session_info[9])
                                print(mythic_information)
                                gold_information = gold_calculation(level_information[0], validate_recipient[5], validate_recipient[12], validate_recipient[13], validate_recipient[14], session_info[3])
                                gold_received = 0 if forego == 3 else gold_information[3]
                                gold_rewarded = 0 if forego == 3 else session_info[3]
                                await EventCommand.session_rewards(self, validate_recipient[0], guild_id, character_name, level_information[0], new_milestones, level_information[1], validate_recipient[15] + session_info[4], mythic_information[0], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[26] + session_info[10],  session_id)
                                await EventCommand.gold_change(self, guild_id, validate_recipient[0], validate_recipient[1], character_name, gold_received, gold_received, gold_rewarded, 'Session Added new Claim', 'Session Claim')
                                cursor.execute(f"Select MAX(transaction_id) from A_Audit_Gold")
                                gold_transaction_id = cursor.fetchone()
                                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                accepted_bio_channel = cursor.fetchone()
                                cursor.close()
                                db.close()
                                await EventCommand.session_log_player(self, guild_id, session_id, validate_recipient[0], validate_recipient[1], validate_recipient[2], validate_recipient[6], validate_recipient[7], validate_recipient[13], rewarded, session_info[9], gold_received, session_info[10])
                                bio_embed = character_embed(validate_recipient[0], validate_recipient[1], validate_recipient[2], validate_recipient[3], validate_recipient[4], validate_recipient[5], level_information[0], mythic_information[0], new_milestones, level_information[1], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[12] + gold_received, validate_recipient[13] + gold_received, validate_recipient[15] + session_info[4], validate_recipient[16], validate_recipient[17], validate_recipient[18], validate_recipient[19], validate_recipient[20], validate_recipient[21], validate_recipient[22], validate_recipient[26] + session_info[10], validate_recipient[27], )
                                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                bio_message = await bio_channel.fetch_message(validate_recipient[23])
                                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                session_name = session_info[2]
                                embed_log = log_embed(validate_recipient[2], author, level_information[0], rewarded, new_milestones, level_information[1], mythic_information[0], session_info[9], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[12] + gold_received, gold_received, validate_recipient[13] + gold_received, gold_transaction_id[0], validate_recipient[15] + session_info[4], session_info[4], None, None, None, None, None, validate_recipient[26] + session_info[10], session_info[10], None, None, f"Session {session_name} with ID: {session_id} claimed")
                                logging_thread = guild.get_thread(validate_recipient[25])
                                await logging_thread.send(embed=embed_log)
                                await interaction.response.send_message(f"Rewards have been claimed for {character_name}!")
            else:
                cursor.execute(f"""SELECT Easy, Medium, Hard, Deadly from AA_Milestones WHERE level = {validate_recipient[6]}""")
                job_info = cursor.fetchone()
                easy_jobs = session_info[5] * job_info[0]
                medium_jobs = session_info[6] * job_info[1]
                hard_jobs = session_info[7] * job_info[2]
                deadly_jobs = session_info[8] * job_info[3]
                rewarded = easy_jobs + medium_jobs + hard_jobs + deadly_jobs
                rewarded = 0 if forego == 2 else rewarded
                new_milestones = validate_recipient[8] + rewarded
                level_information = level_calculation(guild_id, validate_recipient[8], rewarded, validate_recipient[28])
                print(level_information[0], validate_recipient[10], session_info[9], validate_recipient[28])
                mythic_information = mythic_calculation(guild_id, level_information[0], validate_recipient[10], session_info[9])
                print(mythic_information)
                gold_information = gold_calculation(level_information[0], validate_recipient[5], validate_recipient[12], validate_recipient[13], validate_recipient[14], session_info[3])
                gold_received = 0 if forego == 3 else gold_information[3]
                gold_rewarded = 0 if forego == 3 else session_info[3]
                prestige = session_info[11]
                prestige = prestige if validate_recipient[29] + prestige <= validate_recipient[26] + session_info[10] else validate_recipient[26] + session_info[10] - validate_recipient[29]
                # The specific date you want to compare
                end_date = datetime.datetime.strptime(validate_recipient[31], '%Y-%m-%d %H:%M')
                # Current date and time
                current_date = datetime.datetime.now()
                # Calculate the difference between dates
                difference =  current_date - end_date
                # Get the difference in days
                if validate_recipient[6] >= 7:
                    if 90 <= difference.days < 120:
                        flux_multiplier = 2
                    elif difference.days >= 120:
                        flux_multiplier = 2 + math.floor((difference.days - 90) / 30)
                        flux_multiplier = flux_multiplier if flux_multiplier <= 4 else 4
                    else:
                        flux_multiplier = 1
                else:
                    flux_multiplier = 1
                awarded_flux = session_info[4] * flux_multiplier
                await EventCommand.session_rewards(self, validate_recipient[0], guild_id, character_name, level_information[0], new_milestones, level_information[1], validate_recipient[15] + awarded_flux, mythic_information[0], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[26] + session_info[10], validate_recipient[29] +prestige, session_id)
                await EventCommand.gold_change(self, guild_id, validate_recipient[0], validate_recipient[1], character_name, gold_received, gold_received, gold_rewarded, 'Session Added new Claim', 'Session Claim')
                cursor.execute(f"Select MAX(transaction_id) from A_Audit_Gold")
                gold_transaction_id = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.close()
                db.close()
                await EventCommand.session_log_player(self, guild_id, session_id, validate_recipient[0], validate_recipient[1], validate_recipient[2], validate_recipient[6], validate_recipient[7], validate_recipient[13], rewarded, session_info[9], gold_received, session_info[10], prestige, awarded_flux)
                bio_embed = character_embed(validate_recipient[0], validate_recipient[1], validate_recipient[2], validate_recipient[3], validate_recipient[4], validate_recipient[5], level_information[0], mythic_information[0], new_milestones, level_information[1], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[12]+gold_received, validate_recipient[13]+gold_received, validate_recipient[15] + awarded_flux, validate_recipient[16], validate_recipient[17], validate_recipient[18], validate_recipient[19], validate_recipient[20], validate_recipient[21], validate_recipient[22], validate_recipient[26] + session_info[10], validate_recipient[27], validate_recipient[29] + prestige, validate_recipient[30])
                # cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters WHERE Player_Name = ? AND Character_Name = ? OR Nickname =?", (author, character_name, character_name))
                # (player_name, player_id, character_name, titles, description, oath, level, tier, milestones, milestones_required, trials, trials_required, gold, effective_gold, flux, color, mythweavers, image_link, tradition_name, tradition_link, template_name, template_link, fame, title, prestige):
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(validate_recipient[23])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                session_name = session_info[2]
                embed_log = log_embed(validate_recipient[2], author, level_information[0], rewarded, new_milestones, level_information[1], mythic_information[0], session_info[9], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[12]+gold_received, gold_received, validate_recipient[13]+gold_received, gold_transaction_id[0], validate_recipient[15] + awarded_flux, awarded_flux, None, None, None, None, None, validate_recipient[26] + session_info[10], session_info[10], validate_recipient[29] + prestige, prestige, f"Session {session_name} with ID: {session_id} claimed")
                logging_thread = guild.get_thread(validate_recipient[25])
                await logging_thread.send(embed=embed_log)
                await interaction.response.send_message(f"Rewards have been claimed for {character_name}!")
        else:
            await interaction.response.send_message(f"{character_name} is not a valid Character name or Nickname.")

@gamemaster.command()
async def notify(interaction: discord.Interaction, session_id: int, message: str = "Session Notice!"):
    """Notify players about an ACTIVE Session."""
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    guild = interaction.guild
    sql = f"SELECT Message, Session_Name, Session_Thread, Play_Time from Sessions WHERE Session_ID = ? AND IsActive = ? AND GM_Name = ? ORDER BY Created_Time Desc Limit 1"
    val = (session_id, 1, author)
    cursor.execute(sql, val)
    info = cursor.fetchone()
    if info is not None:
        cursor.execute(f"SELECT Player_ID FROM Sessions_Participants WHERE Session_ID = ?", (session_id,))
        participants = cursor.fetchall()
        ping_list = f"NOTICE:"
        for player in participants:
            ping_list += f"<@{player[0]}> "
        if message == "Session Notice!":
            message == f"Session Notice! Session is in <t:{info[3]}:R>"
        ping_list = ping_list + f"your GM {interaction.user.name} has the following message for you! \r\n {message}"
        quest_thread = guild.get_thread(info[2])
        await quest_thread.send(content=ping_list, allowed_mentions=discord.AllowedMentions(users=True))
    if info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id} associated with host {author}")
    cursor.close()
    db.close()


# noinspection PyUnresolvedReferences
@gamemaster.command()
@app_commands.describe(summary="Use a google drive link, or write a summary about the occasion.")
@app_commands.autocomplete(plot=get_plots)
async def plot(interaction: discord.Interaction, plot: str, summary: str):
    """Notify players about an ACTIVE Session."""
    """Sesssions Folder is: b71f939a-f72d-413b-b4d7-4ebff1e162ca"""

    plot = str.replace(str.replace(str.replace(str.replace(str.replace(str.title(plot), ";", ""), "(", ""), ")", ""), "[",""), "]", "")
    guild_id = interaction.guild_id
    author = interaction.user.name
    await interaction.response.defer(thinking=True)
    if summary is None:
        await interaction.response.send_message(f"No summary available.")
        return
    elif plot[:2] == "1-":
        type = 1
        plot_length = len(plot)
        plot_id = plot[2:plot_length]
        await EventCommand.plot(self, guild_id, type, plot_id, summary, author)

        await interaction.followup.send(f"Plot {plot_id} has been edited")
    elif plot[:2] == '2-':
        type = 2
        plot_length = len(plot)
        plot_name = plot[2:plot_length]
        await EventCommand.plot(self, guild_id, type, plot_name, summary, author)
        await interaction.followup.send(f"Plot {plot_name} has been created.")
    else:
        await interaction.followup.send(f"Please select a choice from the menu.")


@gamemaster.command()
@app_commands.describe(summary="if a link is available the summary will not be used.")
@app_commands.autocomplete(plot=get_precreated_plots)
@app_commands.autocomplete(session_id=session_lookup)
async def report(interaction: discord.Interaction, session_id: int, summary: str, plot: str = None):
    """Notify players about an ACTIVE Session."""
    """Sesssions Folder is: b71f939a-f72d-413b-b4d7-4ebff1e162ca"""
    if plot is not None:
        plot = str.replace(str.replace(str.replace(str.replace(str.replace(str.title(plot), ";", ""), "(", ""), ")", ""), "[",""), "]", "")
        if ' ' in plot or '-' not in plot:
            plot = await get_precreated_plots(interaction, plot)
            print(plot)

        if ' ' in str(session_id):
            split_session = session_id.split(':')
            session_id = split_session[0]
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    user = interaction.user
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"Select Session_ID, Session_Name, Article_Link, Article_ID, Related_Plot, easy, medium, hard, deadly, trials from Sessions where Session_ID = ? and GM_Name = ? and IsActive = 0", (session_id, author))
    session_info = cursor.fetchone()
    await interaction.response.defer(thinking=True)
    plot = session_info[4] if plot is None else plot
    plot = '9762aebb-43ae-47d5-8c7b-30c34a55b9e5' if plot is None else plot
    if session_info is None:
        await interaction.response.send_message(f"No completed Session with ID {session_id} could be found!")
    else:
        if session_info[2] is None:
            event_type = 2
            print(f"THIS IS THE EVENT TYPE OF {event_type}")
            significance = 0
            print(f"Caculating Significance")
            significance += 0 if session_info[5] is None else 1 * session_info[5]
            significance += 0 if session_info[6] is None else 2 * session_info[6]
            significance += 0 if session_info[7] is None else 3 * session_info[7]
            significance += 0 if session_info[8] is None else 4 * session_info[8]
            significance += 0 if session_info[9] is None else 2 * session_info[9]
            print(f"significance is {significance}")
            significance = 5 if significance > 5 else significance
            print(f"2 significance is {significance}")
            await EventCommand.report(self, guild_id, event_type, plot, summary, session_id, author, significance)
            cursor.execute(f"Select Session_ID, Session_Name, Article_Link, Article_ID, Related_Plot from Sessions where Session_ID = ? and IsActive = 0", (session_id,))
            session_info = cursor.fetchone()
            wa_update_channel = await bot.fetch_channel(1032422764168106134)
            await wa_update_channel.send(f"Session Report for [{session_info[1]}](<{session_info[2]}>) has been created.")
            await interaction.followup.send(f"Session Report for [{session_info[1]}](<{session_info[2]}>) has been created.")
        else:
            event_type = 1
            significance = 0
            await EventCommand.report(self, guild_id, event_type, plot, summary, session_id, author, significance)
            cursor.execute(f"Select Session_ID, Session_Name, Article_Link, Article_ID, Related_Plot from Sessions where Session_ID = ? and IsActive = 0", (session_id,))
            session_info = cursor.fetchone()
            print(significance)
            await interaction.followup.send(f"Session Report for [{session_info[1]}](<{session_info[2]}>) has been edited.")
            wa_update_channel = await bot.fetch_channel(1032422764168106134)
            await wa_update_channel.send(f"Session Report for [{session_info[1]}](<{session_info[2]}>) has been edited.")
            await wa_update_channel.send(f"Session Report for [{session_info[1]}](<{session_info[2]}>) has been edited.")
    cursor.close()
    db.close()


@player.command()
@app_commands.describe(summary="This will use a Google Drive Link if available")
@app_commands.autocomplete(session_id=player_session_lookup)
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def report(interaction: discord.Interaction, session_id: int, summary: str, character_name: str):
    """Notify players about an ACTIVE Session."""
    """Sesssions Folder is: b71f939a-f72d-413b-b4d7-4ebff1e162ca"""
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    user = interaction.user
    guild = interaction.guild
    print(f"hello?")
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"Select Session_ID, Session_Name, Article_Link, Article_ID, Related_Plot from Sessions where Session_ID = ? and IsActive = 0", (session_id,))
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.response.send_message(f"No completed Session with ID {session_id} could be found!")
    else:
        await EventCommand.session_report(self, guild_id,  summary, session_id, character_name, author)
        cursor.execute(f"Select Session_ID, Session_Name, Article_Link, Article_ID, Related_Plot from Sessions where Session_ID = ? and IsActive = 0", (session_id,))
        session_info = cursor.fetchone()
        await interaction.response.send_message(f"Session Report for [{session_info[1]}](<{session_info[2]}>) has been added to!")
    cursor.close()
    db.close()


@player.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def join(interaction: discord.Interaction, session_id: int, character_name: str):
    """PLAYER: Offer your Participation in a session."""
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    user = interaction.user
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    await interaction.response.defer(thinking=True, ephemeral=True)
    cursor.execute(f"SELECT Session_Name, Play_location, Play_Time, game_link, Session_Range_ID, Session_Range, Session_Thread, overflow FROM Sessions WHERE Session_ID = '{session_id}' AND IsActive = 1")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.followup.send(f"No active session with Session ID: {session_id} can be found!")
    else:
        quest_thread = guild.get_thread(session_info[6])
        role = interaction.guild.get_role(session_info[4])
        if role in user.roles or session_info[7] == 4 or session_info[7] == 3 or session_info[7] == 2:
            sql = f"""Select Character_Name, Level, Gold_Value, Tier from Player_Characters where Player_Name = ? and Character_Name = ? OR  Player_Name = ? AND Nickname = ?"""
            val = (author, character_name, author, character_name)
            cursor.execute(sql, val)
            character_info = cursor.fetchone()
            if character_info is None:
                await interaction.followup.send(f"Falsehoods! the Character of {character_name} either doesn't exist or belong to {author}!")
            if character_info is not None:
                cursor.execute(f"SELECT Level, Role_Name from Level_Range WHERE Role_ID = {session_info[4]}")
                level_range_info = cursor.fetchone()
                print(session_info[7])
                if level_range_info is None or session_info[7] == 4:
                    cursor.execute(f"""Select Character_Name from Sessions_Participants where Player_name = '{author}' and Session_ID = {session_id}""")
                    participation = cursor.fetchone()
                    cursor.execute(f"""Select Character_Name from Sessions_Signups where Player_name = '{author}' AND Session_ID = {session_id}""")
                    signups = cursor.fetchone()
                    if participation is None and signups is None:
                        await EventCommand.session_join(self, guild_id, session_info[0], session_id, author, author_id, character_info[0], character_info[1], character_info[2], character_info[3])
                        sql = f"""Select Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Gold_Value, Oath from Player_characters WHERE Character_Name = ? OR Nickname = ?"""
                        val = (character_name, character_name)
                        cursor.execute(sql, val)
                        result = cursor.fetchone()
                        if result is None:
                            await interaction.followup.send(f"{character_name} is not a valid Character name or Nickname.")
                            cursor.close()
                            db.close()
                            return
                        else:
                            color = result[11]
                            int_color = int(color[1:], 16)
                            embed = discord.Embed(title="Mythweavers Sheet", url=f'{result[12]}', description=f"Other Names: {result[2]}", color=int_color, timestamp=datetime.datetime.utcnow())
                            embed.set_author(name=f'{result[0]} would like to participate')
                            embed.set_thumbnail(url=f'{result[13]}')
                            embed.add_field(name="Information", value=f'**Level**: {result[4]}, **Mythic Tier**: {result[5]}', inline=True)
                            embed.add_field(name="illiquid Wealth", value=f'**GP**: {round(result[19] - result[10],2)}', inline=True)
                            linkage = f""
                            if result[15] is not None:
                                linkage += f"**Tradition**: [{result[15]}]({result[16]})"
                            if result[17] is not None:
                                if result[15] is not None:
                                    linkage += " "
                                linkage += f"**Template**: [{result[17]}]({result[18]})"
                            if result[15] is not None or result[17] is not None:
                                embed.add_field(name=f'Additional Info', value=linkage, inline=False)
                            if result[20] == 'Offerings':
                                embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
                            elif result[20] == 'Poverty':
                                embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
                            elif result[20] == 'Absolute':
                                embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
                            else:
                                embed.set_footer(text=f'{result[3]}')
                            await quest_thread.send(embed=embed, content=f"{interaction.user.mention}", allowed_mentions=discord.AllowedMentions(users=True))
                            await interaction.followup.send(content=f"You have submitted your request! Please wait for the GM to accept or deny your request!", ephemeral=True)
                    elif participation is not None:
                        await interaction.followup.send(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
                    elif signups is not None:
                        await interaction.followup.send(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
                else:
                    if session_info[7] == 3:
                        cursor.execute(f"SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_ID = {session_info[4]}")
                        new_level_range_info = cursor.fetchone()
                        cursor.execute(f"SELECT Role_Name from Level_Range WHERE level = {new_level_range_info[0]-1}")
                        overflow_level_role = cursor.fetchone()
                        overflow_level_role = overflow_level_role if overflow_level_role is not None else new_level_range_info
                        cursor.execute(f"SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_Name = ?", (overflow_level_role[0],))
                        overflow_level_range_info = cursor.fetchone()
                        overflow_level_range_info = overflow_level_range_info if overflow_level_range_info[0] is not None else new_level_range_info
                        level_range_validation = 1 if overflow_level_range_info is not None and overflow_level_range_info[0] <= character_info[1] <= new_level_range_info[1] else 0
                    elif session_info[7] == 2:
                        cursor.execute(f"SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_ID = {session_info[4]}")
                        new_level_range_info = cursor.fetchone()
                        cursor.execute(f"SELECT Role_Name from Level_Range WHERE level = {new_level_range_info[1] + 1}")
                        overflow_level_role = cursor.fetchone()
                        overflow_level_role = overflow_level_role if overflow_level_role is not None else new_level_range_info
                        cursor.execute(f"SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_Name = ?", (overflow_level_role[0],))
                        overflow_level_range_info = cursor.fetchone()
                        overflow_level_range_info = overflow_level_range_info if overflow_level_range_info[0] is not None else new_level_range_info
                        level_range_validation = 1 if overflow_level_range_info is not None and new_level_range_info[0] <= character_info[1] <= overflow_level_range_info[1] else 0
                    else:
                        cursor.execute(f"SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_ID = {session_info[4]} AND Level = {character_info[1]}")
                        new_level_range_info = cursor.fetchone()
                        level_range_validation = 1 if new_level_range_info is not None else 0
                    if level_range_validation != 1:
                        await interaction.followup.send(f"{character_info[0]} is level {character_info[1]} which is not inside the level range of {level_range_info[1]}!", ephemeral=True)
                    else:
                        cursor.execute(f"""Select Character_Name from Sessions_Participants where Player_name = '{author}' and Session_ID = {session_id}""")
                        participation = cursor.fetchone()
                        cursor.execute(f"""Select Character_Name from Sessions_Signups where Player_name = '{author}' and Session_ID = {session_id}""")
                        signups = cursor.fetchone()
                        if participation is None and signups is None:
                            await EventCommand.session_join(self, guild_id, session_info[0], session_id, author, author_id, character_info[0], character_info[1], character_info[2], character_info[3])
                            sql = f"""Select True_Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Gold_Value, Oath from Player_characters WHERE Character_Name = ? OR Nickname = ?"""
                            val = (character_name, character_name)
                            cursor.execute(sql, val)
                            result = cursor.fetchone()
                            if result is None:
                                await interaction.followup.send(f"{character_name} is not a valid Character Name or Nickname.")
                                cursor.close()
                                db.close()
                                return
                            else:
                                color = result[11]
                                int_color = int(color[1:], 16)
                                embed = discord.Embed(title="Mythweavers Sheet", url=f'{result[12]}',
                                                      description=f"Other Names: {result[2]}", color=int_color)
                                embed.set_author(name=f'{result[0]} would like to participate!')
                                embed.set_thumbnail(url=f'{result[13]}')
                                embed.add_field(name="Information", value=f'**Level**: {result[4]}, **Mythic Tier**: {result[5]}', inline=True)
                                embed.add_field(name="illiquid Wealth", value=f'**GP**: {round(result[19] - result[10],2)}', inline=True)
                                linkage = f""
                                print(result[15], result[17])
                                if result[15] is not None:
                                    linkage += f"**Tradition**: [{result[15]}]({result[16]})"
                                if result[17] is not None:
                                    if result[15] is not None:
                                        linkage += " "
                                    linkage += f"**Template**: [{result[17]}]({result[18]})"
                                if result[15] is not None or result[17] is not None:
                                    print(linkage)
                                    embed.add_field(name=f'Additional Info', value=linkage, inline=False)
                                if result[20] == 'Offerings':
                                    embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
                                elif result[20] == 'Poverty':
                                    embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
                                elif result[20] == 'Absolute':
                                    embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
                                else:
                                    embed.set_footer(text=f'{result[3]}')
                                await quest_thread.send(embed=embed, content=f"{interaction.user.mention}", allowed_mentions=discord.AllowedMentions(users=True))
                                await interaction.followup.send(content=f"You have submitted your request! Please wait for the GM to accept or deny your request!")
                        elif participation is not None:
                            await interaction.followup.send(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
                        elif signups is not None:
                            await interaction.followup.send(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
        else:
            await interaction.followup.send(f"User does not have role: {session_info[5]}! If you wish to join, obtain this role! Ensure you have a character in the correct level bracket.", ephemeral=True)

@player.command()
async def leave(interaction: discord.Interaction, session_id: int):
    """PLAYER: Rescind your Participation in a session."""
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Session_Name, Play_location, Play_Time, Game_Link FROM Sessions WHERE Session_ID = '{session_id}'")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.response.send_message(f"No active session with {session_id} can be found!")
    if session_info is not None:
        cursor.execute(f"""Select Character_Name, Level, Effective_Wealth from Sessions_Signups where Player_Name = '{author}' and Session_ID = '{session_id}'""")
        character_info = cursor.fetchone()
        if character_info is None:
            cursor.execute(f"""Select Character_Name, Level, Effective_Wealth from Sessions_Participants where Player_Name = '{author}' and Session_ID = '{session_id}'""")
            character_info = cursor.fetchone()
            if character_info is None:
                await interaction.response.send_message(f"{author} has no active character in this session!")
            if character_info is not None:
                true_name = character_info[0]
                cursor.close()
                db.close()
                await EventCommand.session_leave(self, guild_id, session_id, author, true_name)
                await interaction.response.send_message(f"{author}'s {true_name} has decided against participating in the session of '{session_info[0]}!'")
        elif character_info is not None:
            true_name = character_info[0]
            cursor.close()
            db.close()
            await EventCommand.session_leave(self, guild_id, session_id, author, true_name)
            await interaction.response.send_message(f"{author}'s {true_name} has decided against participating in the session of '{session_info[0]}!'")


@player.command()
@app_commands.describe(group="Displaying All Participants & Signups, Active Participants Only, or Potential Sign-ups Only for a session")
@app_commands.choices(group=[discord.app_commands.Choice(name='All', value=1), discord.app_commands.Choice(name='Participants', value=2), discord.app_commands.Choice(name='Sign-ups', value=3)])
async def display(ctx: commands.Context, session_id: int, group: discord.app_commands.Choice[int] = 1):
    """ALL: THIS COMMAND DISPLAYS SESSION INFORMATION"""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if group == 1:
        group = 1
    else:
        group = group.value
    cursor.execute(f"SELECT GM_Name, Session_Name, Session_Range, Play_location, Play_Time, Overview, Description, Message, IsActive FROM Sessions WHERE Session_ID = {session_id}")
    session_info = cursor.fetchone()
    if session_info is not None:
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        sessions_channel = cursor.fetchone()
        session_channel = await bot.fetch_channel(sessions_channel[0])
        msg = await session_channel.fetch_message(session_info[7])
        embed = discord.Embed(title=f"{session_info[1]}", description=f'[Session overview](<{msg.jump_url}>)!',colour=discord.Colour.blurple())
        if session_info[8] == 1:
            embed.add_field(name=f"Active Session Info", value=f"**GM**: {session_info[0]}, **Session Range**: {session_info[2]}, **Play_Location**: {session_info[3]}, **Play_Time**: <t:{session_info[4]}:D>", inline=False)
            x = 0
            print(group)
            if group == 1 or group == 2:
                cursor.execute(f"SELECT COUNT(Player_Name) FROM Sessions_Participants WHERE Session_ID = {session_id}")
                total_participants = cursor.fetchone()
                cursor.execute(f"SELECT Player_Name, Character_Name, Level, Effective_Wealth, Tier, Player_ID FROM Sessions_Participants WHERE Session_ID = {session_id}")
                participants = cursor.fetchall()
                player_total = total_participants[0]
                embed.add_field(name=f"Participant List: {player_total} players", value=" ")
                for player in participants:
                    embed.add_field(name=f'**Character**: {player[1]}', value=f"**Player**: <@{player[5]}> \n **Level**: {player[2]}, **Tier** {player[4]} \n **Effective_Wealth**: {player[3]} GP", inline=False)
                    x += 1
                    if x >= 20:
                        embed.add_field(name=f"Field Limit reached", value=f'{total_participants[0] - 20} remaining Participants', inline=False)
                        break
            else:
                player_total = 0
            if group == 1 or group == 3:
                cursor.execute(f"SELECT COUNT(Player_Name) FROM Sessions_Signups WHERE Session_ID = {session_id}")
                total_participants = cursor.fetchone()
                x = 0 + player_total
                cursor.execute(f"SELECT Player_Name, Character_Name, Level, Effective_Wealth, Tier, Player_ID FROM Sessions_Signups WHERE Session_ID = {session_id}")
                participants = cursor.fetchall()
                player_total += total_participants[0]
                embed.add_field(name=f"Sign Up List: {total_participants[0]} players", value=' ', inline=False)
                for player in participants:
                    embed.add_field(name=f'**Character**: {player[1]}', value=f"Player: <@{player[5]}>, Level: {player[2]}, Tier: {player[4]}, Effective_Wealth: {player[3]}!", inline=False)
                    x += 1
                    if x >= 20:
                        embed.add_field(name=f"Field Limit reached", value=f'{total_participants[0] - 20} remaining Sign-ups')
                        break
                embed.set_footer(text=f"Session ID: {session_id}")
            await ctx.response.send_message(embed=embed)
        else:
            cursor.execute(f"SELECT Gold, Flux, Easy, Medium, Hard, Deadly, Trials FROM Sessions WHERE Session_ID = {session_id}")
            session_reward_info = cursor.fetchone()
            embed.add_field(name=f"Inactive Session Info", value=f"**GM**: {session_info[0]}, **Session Range**: {session_info[2]}, **Play_Location**: {session_info[3]}, **Play_Time**: <t:{session_info[4]}:D>", inline=False)
            embed.add_field(name=f"Milestone Rewards", value=f"**Easy Jobs**: {session_reward_info[2]}, **Medium Jobs**: {session_reward_info[3]}, **Hard_jobs**: {session_reward_info[4]}, **Deadly_Jobs**: {session_reward_info[5]}, **Trials**: {session_reward_info[6]}", inline=False)
            embed.add_field(name=f"Currency Rewards", value=f"**Gold**: {session_reward_info[0]}, **Flux**: {session_reward_info[1]}", inline=False)
            x = 0
            cursor.execute(f"SELECT COUNT(Player_Name) FROM Sessions_Archive WHERE Session_ID = {session_id}")
            total_participants = cursor.fetchone()
            cursor.execute(f"SELECT Player_Name, Character_Name, Level, Effective_Gold, Tier, Received_Milestones, Received_Gold, Player_ID FROM Sessions_Archive WHERE Session_ID = {session_id}")
            participants = cursor.fetchall()
            player_total = total_participants[0]
            embed.add_field(name=f"Participant List: {player_total} players", value=' ', inline=False)
            for player in participants:
                embed.add_field(name=f'**Character**: {player[1]}', value=f"**Player**: <@{player[7]}> \n **Level**: {player[2]}, **Tier** {player[4]}, \n **Received Milestones**: {player[5]}, **Received Trials**: {session_info[12]} \n  **Session Effective Gold**: {player[3]}, **Received Gold**: {player[6]}", inline=False)
                x += 1
                if x >= 20:
                    embed.add_field(name=f"Field Limit reached",
                                    value=f'{total_participants[0] - 20} remaining Participants')
                    break
            embed.set_footer(text=f"Session ID: {session_id}")
            await ctx.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title=f"Display Command Failed", description=f'{session_id} could not be found in current or archived sessions!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
    cursor.close()
    db.close()


@player.command()
@app_commands.describe(change="Add or remove availability")
@app_commands.describe(day="which day of the week, if clearing all, ignore")
@app_commands.describe(utc_offset="UTC offset for your time zone")
@app_commands.describe(start_time="the start window, please use ##:## in MILITARY time, leave as 0 when clearing.")
@app_commands.describe(end_time="the close window, please use ##:## in MILITARY time, leave as 0 when clearing.")
@app_commands.choices(change=[discord.app_commands.Choice(name='Add', value=1), discord.app_commands.Choice(name='Remove', value=2), discord.app_commands.Choice(name='Clear', value=3), discord.app_commands.Choice(name='Clear All', value=4)])
@app_commands.choices(day=[discord.app_commands.Choice(name='Monday', value=1), discord.app_commands.Choice(name='Tuesday', value=2), discord.app_commands.Choice(name='Wednesday', value=3), discord.app_commands.Choice(name='Thursday', value=4), discord.app_commands.Choice(name='Friday', value=5), discord.app_commands.Choice(name='Saturday', value=6), discord.app_commands.Choice(name='Sunday', value=7)])
async def timesheet(ctx: commands.Context, day: discord.app_commands.Choice[int], utc_offset: int, start_time: str, end_time: str, change: discord.app_commands.Choice[int] = 1):
    """Update and Adjust your predicted Weekly Availability"""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    print(ctx.user.name)
    cursor.execute(f"select player_Name from player_characters where player_name = ?", (ctx.user.name,))
    player_info = cursor.fetchone()
    if change == 1:
        change = 1
    else:
        change = change.value
    if day == 1:
        day_value = 1
    else:
        day_value = day.value
    if day_value < 1 and change <4 or day_value > 7 and change < 4:
        embed = discord.Embed(title=f"Day Error", description=f'{day} is not a valid day of the week!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
        cursor.close()
        db.close()
        return
    if player_info is None:
        embed = discord.Embed(title=f"Player Error", description=f'{ctx.user.name} is not a valid player!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
        cursor.close()
        db.close()
        return
    if change > 2:
        # await EventCommand.clear_timesheet(self, guild_id, change, day, ctx.user.name)
        if change == 3:
            embed = discord.Embed(title=f"Time Sheet Update", description=f'{ctx.user.name} has cleared availability on {day}!', colour=discord.Colour.green())
            await ctx.response.send_message(embed=embed)
        if change == 4:
            embed = discord.Embed(title=f"Time Sheet Update", description=f'{ctx.user.name} has cleared all availability!', colour=discord.Colour.green())
            await ctx.response.send_message(embed=embed)
    if utc_offset < -12 or utc_offset > 12:
        embed = discord.Embed(title=f"UTC Offset Error", description=f'{utc_offset} is not a valid UTC offset!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
        cursor.close()
        db.close()
        return
    if len(start_time) != 5 or len(end_time) != 5:
        if len(start_time) == 4 or len(end_time) == 4:
            try:
                if len(start_time) == 4:
                    start_time = datetime.strptime(start_time, "%H:%M").strftime("%H:%M")
                if len(end_time) == 4:
                    end_time = datetime.strptime(end_time, "%H:%M").strftime("%H:%M")
            except:
                embed = discord.Embed(title=f"Time Error", description=f'{start_time} or {end_time} is not a valid time!', colour=discord.Colour.red())
                await ctx.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title=f"Time Error", description=f'{start_time} or {end_time} is not a valid time!', colour=discord.Colour.red())
            await ctx.response.send_message(embed=embed)
        cursor.close()
        db.close()
        return
    if int(start_time[:2]) < 0 or int(start_time[:2]) > 23 or int(end_time[:2]) < 0 or int(end_time[:2]) > 23:
        embed = discord.Embed(title=f"Time Error", description=f'{start_time} or {end_time} is not a valid time!', colour=discord.Colour.red())
        start_hours = None
        end_hours = None
        await ctx.response.send_message(embed=embed)
        cursor.close()
        db.close()
        return
    else:
        start_hours = start_time[:2]
        end_hours = end_time[:2]
    if int(start_time[len(start_time)-2:]) < 0 or int(start_time[len(start_time)-2:]) > 59 or int(end_time[len(end_time)-2:]) < 0 or int(end_time[len(end_time)-2:]) > 59:
        embed = discord.Embed(title=f"Time Error", description=f'{start_time} or {end_time} is not a valid time!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
        start_minutes = None
        end_minutes = None
        cursor.close()
        db.close()
        return
    else:
        start_minutes = 0 if int(start_time[len(start_time)-2:]) < 30 else 30
        end_minutes = 0 if int(end_time[len(end_time)-2:]) < 30 else 30
    if start_hours > end_hours:
        embed = discord.Embed(title=f"Time Error", description=f'{start_time} is after {end_time}!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
        cursor.close()
        db.close()
        return
    start_day = adjust_day(day_value, start_hours, utc_offset)
    end_day = adjust_day(day_value, end_hours, utc_offset)
    print(utc_offset)
    start_hours =int(start_hours) - utc_offset if int(start_hours) + utc_offset >= 0 else 24 + (int(start_hours) - utc_offset)
    print(f"I AM END HOURS {end_hours}")
    end_hours = int(end_hours) - utc_offset if int(end_hours) + utc_offset >= 0 else 24 + (int(end_hours) - utc_offset)
    print(f"I AM END HOURS {end_hours}")
    start_hours = int(start_hours) if int(start_hours) < 24 else int(start_hours) - 24
    end_hours = int(end_hours) if int(end_hours) < 24 else int(end_hours) - 24
    print(f"I AM END HOURS {end_hours}")
    cursor.close()
    db.close()
    validation = await EventCommand.timesheet(self, guild_id, ctx.user.name, utc_offset, start_day, start_hours, start_minutes, end_day, end_hours, end_minutes, change)
    print(validation)
    if validation == 0:
        embed = discord.Embed(title=f"Time Sheet Error", description=f'This command failed!!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
    else:
        if change == 1:
            embed = discord.Embed(title=f"Time Sheet Update", description=f'{ctx.user.name} has added availability from {start_time} to {end_time} on {day}!', colour=discord.Colour.green())
            await ctx.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title=f"Time Sheet Update", description=f'{ctx.user.name} has removed availability from {start_time} to {end_time} on {day}!', colour=discord.Colour.green())
            await ctx.response.send_message(embed=embed)


@player.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
@app_commands.describe(choice="Add or remove a session request, you can only host 1 request at a time.")
@app_commands.choices(choice=[discord.app_commands.Choice(name='Add', value=1), discord.app_commands.Choice(name='Remove', value=2)])
async def request(ctx: commands.Context, character_name: str, group_name: str, description: str, choice: discord.app_commands.Choice[int] = 1):
    """Open a session Request"""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if choice == 1:
        choice = 1
    else:
        choice = choice.value
    cursor.execute(f"select character_name from player_characters where player_name = ? and character_name = ? OR Nickname = ? and player_name = ?", (ctx.user.name, character_name, character_name, ctx.user.name))
    player_info = cursor.fetchone()
    if player_info is not None and choice == 1:
        cursor.execute(f"select group_id from Sessions_Group where Host = ?", (ctx.user.name,))
        group_info = cursor.fetchone()
        print(group_info)
        if group_info is not None:
            embed = discord.Embed(title=f"Group Request Error",
                                  description=f'{ctx.user.name} is already hosting a group!',
                                  colour=discord.Colour.red())
        else:
            cursor.close()
            db.close()
            await EventCommand.group_request(self, guild_id, ctx.user.name, character_name, group_name, choice, description)
            embed = discord.Embed(title=f"Group Request", description=f'{ctx.user.name} has added a group request!',
                                  colour=discord.Colour.green())

        await ctx.response.send_message(embed=embed)
    else:
        if choice == 2:
            cursor.execute(f"select group_id from Sessions_Group where Host = ?", (ctx.user.name,))
            group_info = cursor.fetchone()
            print(group_info)
            if group_info is not None:
                cursor.close()
                db.close()
                await EventCommand.group_request(self, guild_id, ctx.user.name, character_name, group_name, choice, description)
                embed = discord.Embed(title=f"Group Request", description=f'{ctx.user.name} has removed their group request!', colour=discord.Colour.green())
            else:
                embed = discord.Embed(title=f"Group Request Error", description=f'{ctx.user.name} could not be found to be hosting a group!', colour=discord.Colour.red())
            await ctx.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title=f"No characters with that name under this player found.")
            await ctx.response.send_message(embed=embed)


@player.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
@app_commands.describe(choice="Join or Leave a request group.")
@app_commands.choices(choice=[discord.app_commands.Choice(name='Join', value=1), discord.app_commands.Choice(name='Leave', value=2)])
async def groupup(ctx: commands.Context, group_id: int, character_name: str, choice: discord.app_commands.Choice[int] = 1):
    """Sync your Groups up for a GM to view whose in a session request group."""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if choice == 1:
        choice = 1
    else:
        choice = choice.value
    if choice == 1:
        cursor.execute(f"select group_id from Sessions_Group where group_id = ?", (group_id,))
        group = cursor.fetchone()
        if group is None:
            embed = discord.Embed(title=f"Group Request Error", description=f'Group {group_id} could not be found!', colour=discord.Colour.red())
            await ctx.response.send_message(embed=embed)
            cursor.close()
            db.close()
            return
        else:
            cursor.execute(f"select character_name from player_characters where player_name = ? and character_name = ? OR Nickname = ? and player_name = ?", (ctx.user.name, character_name, character_name, ctx.user.name))
            player_info = cursor.fetchone()
            cursor.close()
            db.close()
            if player_info is not None:
                await EventCommand.group_join(self, guild_id, group_id, ctx.user.name, character_name, choice)
                embed = discord.Embed(title=f"Group Request", description=f'{ctx.user.name} has joined group {group_id}!', colour=discord.Colour.green())
                await ctx.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title=f"No characters with that name under this player found.")
                await ctx.response.send_message(embed=embed)
    else:
        cursor.execute(f"select group_id from Sessions_Group where group_id = ?", (group_id,))
        group = cursor.fetchone()
        if group is None:
            embed = discord.Embed(title=f"Group Request Error", description=f'Group {group_id} could not be found!', colour=discord.Colour.red())
            await ctx.response.send_message(embed=embed)
            cursor.close()
            db.close()
            return
        else:
            cursor.execute(f"select character_name from player_characters where player_name = ? and character_name = ? OR Nickname = ? and player_name = ?", (ctx.user.name, character_name, character_name, ctx.user.name))
            player_info = cursor.fetchone()
            cursor.close()
            db.close()
            if player_info is not None:
                await EventCommand.group_join(self, guild_id, group_id, ctx.user.name, character_name, choice)
                embed = discord.Embed(title=f"Group Request", description=f'{ctx.user.name} has left group {group_id}!', colour=discord.Colour.green())
                await ctx.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title=f"No characters with that name under this player found.")
                await ctx.response.send_message(embed=embed)




@player.command()
@app_commands.describe(player="leave empty to display all.")
@app_commands.choices(day=[discord.app_commands.Choice(name='Monday', value=1), discord.app_commands.Choice(name='Tuesday', value=2), discord.app_commands.Choice(name='Wednesday', value=3), discord.app_commands.Choice(name='Thursday', value=4), discord.app_commands.Choice(name='Friday', value=5), discord.app_commands.Choice(name='Saturday', value=6), discord.app_commands.Choice(name='Sunday', value=7)])
async def availability(ctx: commands.Context, player: typing.Optional[discord.Member], day: discord.app_commands.Choice[int]):
    """Display historical Session Requests"""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if day == 1:
        day = "Monday"
        day_value = 1
    else:
        day_value = day.value
    if day_value < 1 or day_value > 7:
        embed = discord.Embed(title=f"Day Error", description=f'{day} is not a valid day of the week!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
        cursor.close()
        db.close()
    else:
        player = ctx.user.name if player is None else player.name
        current_page = day
        await create_timecard_plot(guild_id, player, day_value)
        print(f"where am I?")
        with open('C:\\Pathparser\\plots\\timecard_plot.png', 'rb') as f:
            picture = discord.File(f)
            await ctx.response.send_message(f"Here's the availability chart for {player} on {day.name}:", file=picture)
    cursor.close()
    db.close()

@player.command()
@app_commands.describe(group_id="leave 0 to display all.")
@app_commands.choices(day=[discord.app_commands.Choice(name='Monday', value=1), discord.app_commands.Choice(name='Tuesday', value=2), discord.app_commands.Choice(name='Wednesday', value=3), discord.app_commands.Choice(name='Thursday', value=4), discord.app_commands.Choice(name='Friday', value=5), discord.app_commands.Choice(name='Saturday', value=6), discord.app_commands.Choice(name='Sunday', value=7)])
async def requests(ctx: commands.Context, day: discord.app_commands.Choice[int], group_id: int = 0):
    """Display historical Session Requests"""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if day == 1:
        day_value = 1
    else:
        day_value = day.value
    if day_value < 1 or day_value > 7:
        embed = discord.Embed(title=f"Day Error", description=f'{day} is not a valid day of the week!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
        cursor.close()
        db.close()
    else:
        if group_id == 0:
            buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
            cursor.execute(f"""SELECT COUNT(Player_Name) FROM Sessions_Presign""")
            admin_count = cursor.fetchone()
            max_page = math.ceil(admin_count[0] / 10)
            current_page = 1
            low = 1 + ((current_page - 1) * 10)
            high = 20 + ((current_page - 1) * 10)
            cursor.execute(f"""SELECT Group_ID, Group_Name, Host, Created_date, Description from Sessions_Group WHERE ROWID BETWEEN {low} and {high}""")
            pull = cursor.fetchall()
            embed = discord.Embed(title=f"Group Request Settings Page {current_page}", description=f'This a list of groups that have requested a session', colour=discord.Colour.blurple())
            for result in pull:
                embed.add_field(name=f'**Group Name**: {result[1]}', value=f'**Host Name**: {result[2]} **Request Date:**: {result[3]}, \r\n **Description**: {result[4]}', inline=False)
                cursor.execute(f"""SELECT Player_Name, Character_Name from Sessions_Presign WHERE group_id = {result[0]}""")
                presigns = cursor.fetchall()
                player_list = "Group Members: \r\n"
                for presign in presigns:
                    player_list += f"**{presign[0]}**: {presign[1]} \r\n"
                embed.add_field(name=f'**Group Members**', value=player_list, inline=False)
            await ctx.response.send_message(embed=embed)
            msg = await ctx.original_response()
            for button in buttons:
                await msg.add_reaction(button)
            while True:
                try:
                    reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
                except asyncio.TimeoutError:
                    embed.set_footer(text="Request has timed out.")
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                    cursor.close()
                    db.close()
                    return print("timed out")
                else:
                    previous_page = current_page
                    if reaction.emoji == u"\u23EA":
                        current_page = 1
                        low = 1
                        high = 20
                    elif reaction.emoji == u"\u2B05" and current_page > 1:
                        low -= 20
                        high -= 20
                        current_page -= 1
                    elif reaction.emoji == u"\u27A1" and current_page < max_page:
                        low += 20
                        high += 20
                        current_page += 1
                    elif reaction.emoji == u"\u23E9":
                        current_page = max_page
                        low = ((20 * max_page) - 19)
                        high = (20 * max_page)
                    for button in buttons:
                        await msg.remove_reaction(button, ctx.user)
                    if current_page != previous_page:
                        cursor.execute(
                            f"""SELECT Group_ID, Group_Name, Host, Created_date, Description from Sessions_Group WHERE ROWID BETWEEN {low} and {high}""")
                        pull = cursor.fetchall()
                        embed = discord.Embed(title=f"Group Request Settings Page {current_page}",
                                              description=f'This a list of groups that have requested a session',
                                              colour=discord.Colour.blurple())
                        for result in pull:
                            embed.add_field(name=f'**Group Name**: {result[1]}',
                                            value=f'**Host Name**: {result[2]} **Request Date:**: {result[3]}, \r\n **Description**: {result[4]}',
                                            inline=False)
                            cursor.execute(
                                f"""SELECT Player_Name, Character_Name from Sessions_Presign WHERE group_id = {result[0]}""")
                            presigns = cursor.fetchall()
                            player_list = "Group Members: \r\n"
                            for presign in presigns:
                                player_list += f"**{presign[0]}**: {presign[1]} \r\n"
                            embed.add_field(name=f'**Group Members**', value=player_list, inline=False)
                        await msg.edit(embed=embed)
                        cursor.close()
        else:
            #Specific Group Specified
            cursor.execute(f"Select Group_ID from Sessions_Group where Group_ID = ?", (group_id,))
            group_base = cursor.fetchone()
            if group_base is not None:
                cursor.execute(f"select SG.Group_Name, SG.Group_ID,  SP.Player_Name, SP.Character_Name from Sessions_Presign as SP LEFT JOIN Sessions_Group as SG on SP.Group_ID = SG.Group_ID where SP.Group_ID = ?", (group_id,))
                group_info = cursor.fetchall()
                embed = discord.Embed(title=f"Group Request {group_id}", description=f'This is a list of the players in the group', colour=discord.Colour.blurple())
                timecard_info = []
                cursor.execute(f'select "UTC_Offset" from player_timecard where Player_Name = {ctx.user.name}')
                author_timecard_info = cursor.fetchone()
                if author_timecard_info is not None:
                    utc_offset = author_timecard_info[0]
                else:
                    utc_offset = 0
                for result in group_info:
                    time_columns = [
                        "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30",
                        "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30",
                        "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                        "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
                        "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30",
                        "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30"
                    ]
                    if utc_offset > 0:
                        day_1_columns_to_select = []
                        day_2_columns_to_select = []
                        minmax_time = utc_offset * 60
                        day_1_instance = 0
                        day_2_instance = 0
                        for col in time_columns:
                            col_minutes = time_to_minutes(col)
                            if minmax_time <= col_minutes <= 1440:
                                day_1_columns_to_select.append(f'"{col}"')
                                day_1_instance += 1
                            if minmax_time >= col_minutes >= 0:
                                day_2_instance += 1
                                day_2_columns_to_select.append(f'"{col}"')
                        # Build the SQL query dynamically
                        day_1_set_clause = ', '.join(day_1_columns_to_select)
                        day_2_set_clause = ', '.join(day_2_columns_to_select)
                        cursor.execute(f'SELECT {day_1_set_clause} from player_timecard where Player_Name = {result[2]} and day = {day_value}')
                        player_timecard_info_1 = cursor.fetchone()
                        cursor.execute(f'SELECT {day_2_set_clause} from player_timecard where Player_Name = {result[2]} and day = {day_value + 1}')
                        player_timecard_info_2 = cursor.fetchone()
                        if player_timecard_info_1 is not None and player_timecard_info_2 is not None:
                            timecard_info.append(player_timecard_info_1)
                            timecard_info.append(player_timecard_info_2)
                        elif player_timecard_info_1 is not None and player_timecard_info_2 is None:
                            timecard_info.append(player_timecard_info_1)
                            timecard_info.append(time_columns[day_1_instance:])
                        elif player_timecard_info_2 is not None and player_timecard_info_1 is None:
                            timecard_info.append(time_columns[:day_2_instance])
                            timecard_info.append(player_timecard_info_2)
                    elif utc_offset < 0:
                        day_1_columns_to_select = []
                        day_2_columns_to_select = []
                        minmax_time = 1440 - utc_offset * 60
                        day_1_instance = 0
                        day_2_instance = 0
                        for col in time_columns:
                            col_minutes = time_to_minutes(col)
                            if minmax_time <= col_minutes <= 1440:
                                day_1_columns_to_select.append(f'"{col}"')
                                day_1_instance += 1
                            if minmax_time >= col_minutes >= 0:
                                day_2_instance += 1
                                day_2_columns_to_select.append(f'"{col}"')
                        # Build the SQL query dynamically
                        day_1_set_clause = ', '.join(day_1_columns_to_select)
                        day_2_set_clause = ', '.join(day_2_columns_to_select)
                        cursor.execute(
                            f'SELECT {day_1_set_clause} from player_timecard where Player_Name = {result[2]} and day = {day_value - 1}')
                        player_timecard_info_1 = cursor.fetchone()
                        cursor.execute(f'SELECT {day_2_set_clause} from player_timecard where Player_Name = {result[2]} and day = {day_value}')
                        player_timecard_info_2 = cursor.fetchone()
                        if player_timecard_info_1 is not None and player_timecard_info_2 is not None:
                            timecard_info.append(player_timecard_info_1)
                            timecard_info.append(player_timecard_info_2)
                        elif player_timecard_info_1 is not None and player_timecard_info_2 is None:
                            timecard_info.append(player_timecard_info_1)
                            timecard_info.append(time_columns[day_1_instance:])
                        elif player_timecard_info_2 is not None and player_timecard_info_1 is None:
                            timecard_info.append(time_columns[:day_2_instance])
                            timecard_info.append(player_timecard_info_2)    
                    else:
                        day_1_columns_to_select = []
                        # Build the SQL query dynamically
                        day_1_set_clause = ', '.join(time_columns)
                        cursor.execute(f'SELECT {day_1_set_clause} from player_timecard where Player_Name = {result[2]} and day = {day_value - 1}')
                        player_timecard_info_1 = cursor.fetchone()
                        if player_timecard_info_1 is not None:
                            timecard_info.append(player_timecard_info_1)
                await ctx.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title=f"Group Request Error", description=f'Group {group_id} could not be found!', colour=discord.Colour.red())
                await ctx.response.send_message(embed=embed)
                cursor.close()
                db.close()
                return
            group_info = cursor.fetchall()
    cursor.close()
    db.close()


@gamemaster.command()
async def questify(ctx: commands.Context, group_id: int):
    """Delete a session request as you transition it over into a session."""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"Select Group_ID from Sessions_Group where Group_ID = ?", (group_id,))
    group_base = cursor.fetchone()
    if group_base is not None:
        await EventCommand.clear_group(self, guild_id, group_id)
        embed = discord.Embed(title=f"Group Request {group_id}", description=f'Group {group_id} has been deleted!', colour=discord.Colour.green())
        await ctx.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title=f"Group Request Error", description=f'Group {group_id} could not be found!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
    cursor.close()
    db.close()


@gamemaster.command()
@app_commands.describe(group="Displaying All Participants & Signups, Active Participants Only, or Potential Sign-ups Only for a session")
@app_commands.choices(group=[discord.app_commands.Choice(name='All', value=1), discord.app_commands.Choice(name='Participants', value=2), discord.app_commands.Choice(name='Sign-ups', value=3)])
async def display(ctx: commands.Context, session_id: int, group: discord.app_commands.Choice[int] = 1):
    """ALL: THIS COMMAND DISPLAYS SESSION INFORMATION"""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT GM_Name, Session_Name, Session_Range, Play_location, Play_Time, Overview, Description, Message, IsActive FROM Sessions WHERE Session_ID = {session_id}")
    session_info = cursor.fetchone()
    if group == 1:
        group = 1
    else:
        group = group.value
    if session_info is not None:
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        sessions_channel = cursor.fetchone()
        session_channel = await bot.fetch_channel(sessions_channel[0])
        msg = await session_channel.fetch_message(session_info[7])
        embed = discord.Embed(title=f"{session_info[1]}", description=f'[Session overview](<{msg.jump_url}>)!',colour=discord.Colour.blurple())
        if session_info[8] == 1:
            embed.add_field(name=f"Active Session Info", value=f"**GM**: {session_info[0]}, **Session Range**: {session_info[2]}, **Play_Location**: {session_info[3]}, **Play_Time**: <t:{session_info[4]}:D>", inline=False)
            x = 0
            print(group)
            if group == 1 or group == 2:
                cursor.execute(f"SELECT COUNT(Player_Name) FROM Sessions_Participants WHERE Session_ID = {session_id}")
                total_participants = cursor.fetchone()
                cursor.execute(f"SELECT Player_Name, Character_Name, Level, Effective_Wealth, Tier, Player_ID FROM Sessions_Participants WHERE Session_ID = {session_id}")
                participants = cursor.fetchall()
                player_total = total_participants[0]
                embed.add_field(name=f"Participant List: {player_total} players", value=" ")
                for player in participants:
                    embed.add_field(name=f'**Character**: {player[1]}', value=f"**Player**: <@{player[5]}> \n **Level**: {player[2]}, **Tier** {player[4]} \n **Effective_Wealth**: {player[3]} GP", inline=False)
                    x += 1
                    if x >= 20:
                        embed.add_field(name=f"Field Limit reached", value=f'{total_participants[0] - 20} remaining Participants', inline=False)
                        break
            else:
                player_total = 0
            if group == 1 or group == 3:
                cursor.execute(f"SELECT COUNT(Player_Name) FROM Sessions_Signups WHERE Session_ID = {session_id}")
                total_participants = cursor.fetchone()
                x = 0 + player_total
                cursor.execute(f"SELECT Player_Name, Character_Name, Level, Effective_Wealth, Tier, Player_ID FROM Sessions_Signups WHERE Session_ID = {session_id}")
                participants = cursor.fetchall()
                player_total += total_participants[0]
                embed.add_field(name=f"Sign Up List: {total_participants[0]} players", value=' ', inline=False)
                for player in participants:
                    embed.add_field(name=f'**Character**: {player[1]}', value=f"Player: <@{player[5]}>, Level: {player[2]}, Tier: {player[4]}, Effective_Wealth: {player[3]}!", inline=False)
                    x += 1
                    if x >= 20:
                        embed.add_field(name=f"Field Limit reached", value=f'{total_participants[0] - 20} remaining Sign-ups')
                        break
                embed.set_footer(text=f"Session ID: {session_id}")
            await ctx.response.send_message(embed=embed)
        else:
            cursor.execute(f"SELECT Gold, Flux, Easy, Medium, Hard, Deadly, Trials FROM Sessions WHERE Session_ID = {session_id}")
            session_reward_info = cursor.fetchone()
            embed.add_field(name=f"Inactive Session Info", value=f"**GM**: {session_info[0]}, **Session Range**: {session_info[2]}, **Play_Location**: {session_info[3]}, **Play_Time**: <t:{session_info[4]}:D>", inline=False)
            embed.add_field(name=f"Milestone Rewards", value=f"**Easy Jobs**: {session_reward_info[2]}, **Medium Jobs**: {session_reward_info[3]}, **Hard_jobs**: {session_reward_info[4]}, **Deadly_Jobs**: {session_reward_info[5]}, **Trials**: {session_reward_info[6]}", inline=False)
            embed.add_field(name=f"Currency Rewards", value=f"**Gold**: {session_reward_info[0]}, **Flux**: {session_reward_info[1]}", inline=False)
            x = 0
            cursor.execute(f"SELECT COUNT(Player_Name) FROM Sessions_Archive WHERE Session_ID = {session_id}")
            total_participants = cursor.fetchone()
            cursor.execute(f"SELECT Player_Name, Character_Name, Level, Effective_Gold, Tier, Received_Milestones, Received_Gold, Player_ID FROM Sessions_Archive WHERE Session_ID = {session_id}")
            participants = cursor.fetchall()
            player_total = total_participants[0]
            embed.add_field(name=f"Participant List: {player_total} players", value=' ', inline=False)
            for player in participants:
                embed.add_field(name=f'**Character**: {player[1]}', value=f"**Player**: <@{player[7]}> \n **Level**: {player[2]}, **Tier** {player[4]}, \n **Received Milestones**: {player[5]}, **Received Trials**: {session_info[12]} \n  **Session Effective Gold**: {player[3]}, **Received Gold**: {player[6]}", inline=False)
                x += 1
                if x >= 20:
                    embed.add_field(name=f"Field Limit reached",
                                    value=f'{total_participants[0] - 20} remaining Participants')
                    break
            embed.set_footer(text=f"Session ID: {session_id}")
            await ctx.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title=f"Display Command Failed", description=f'{session_id} could not be found in current or archived sessions!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
    cursor.close()
    db.close()


@bot.tree.command(name="test", description="testing")
async def self(interaction: discord.Interaction):
    name = interaction.user
    await interaction.response.send_message(f"Hello {name}! I was made by a fucking idiot")


@bot.tree.command(name="ping", description="pings the user")
async def self(interaction: discord.Interaction):
    embed = discord.Embed(title=f"{interaction.user.name}", description=f" ")
    embed.add_field(name="test", value=f'testing', inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="drink", description="drinks the user")
async def drink(interaction: discord.Interaction, item: str):
    await interaction.response.send_message(f"drinks /{item}")


@drink.autocomplete("item")
async def drink_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    for drink_choice in ['beer', 'milk', 'tea', 'coffe', 'juice']:
        if current.lower() in drink_choice.lower():
            data.append(app_commands.Choice(name=drink_choice, value=drink_choice))
    return data

class InputView(discord.ui.View):
    def __init__(self):
        super().__init__()
    @discord.ui.button(label="Enter Multi-line Text", style=discord.ButtonStyle.primary)
    async def enter_text_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Please enter your multi-line text. Type `END` on a new line to finish.", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        collected_text = []
        while True:
            try:
                msg = await bot.wait_for('message', check=check, timeout=300.0)  # 5 minutes timeout
                if msg.content.strip().upper() == "END":
                    break
                collected_text.append(msg.content)
            except asyncio.TimeoutError:
                await interaction.followup.send("You took too long to respond!", ephemeral=True)
                return

        final_text = "\n".join(collected_text)
        await interaction.followup.send(f"Collected multi-line text:\n{final_text}", ephemeral=True)


@bot.tree.command(name='multiline')
async def multiline_command(ctx):
    view = InputView()
    await ctx.response.send_message("Click the button to enter multi-line text:", view=view)


@bot.event
async def on_disconnect():
    print("Bot is disconnecting.")

bot.run(os.getenv('DISCORD_TOKEN'))
