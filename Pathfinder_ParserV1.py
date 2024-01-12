import datetime
import re
import shutil
import typing
import discord
import sqlite3
import os
from discord import app_commands
from discord.ext import commands
from Event2 import Event
from unbelievaboat import Client
import unbelievaboat
import asyncio
import math
import random
from math import floor
from dotenv import load_dotenv; load_dotenv()
from unidecode import unidecode

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


def character_embed(player_name, character_name, titles, description, level, tier, milestones, milestones_required, trials, trials_required, gold, effective_gold, flux, color, mythweavers, image_link, tradition_name, tradition_link, template_name, template_link, player_id):
    int_color = int(color[1:], 16)
    embed = discord.Embed(title=f"{character_name}", url=f'{mythweavers}', description=f"Other Names: {titles}", color=int_color)
    embed.set_author(name=f'{player_name}')
    embed.set_thumbnail(url=f'{image_link}')
    embed.add_field(name="Information", value=f'**Level**: {level}, **Mythic Tier**: {tier}', inline=False)
    embed.add_field(name="Experience", value=f'**Milestones**: {milestones}, **Remaining**: {milestones_required}')
    embed.add_field(name="Mythic", value=f'**Trials**: {trials}, **Remaining**: {trials_required}', inline=True)
    embed.add_field(name="Current Wealth", value=f'**GP**: {gold}, **Effective** {effective_gold} GP', inline=False)
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
    embed.set_footer(text=f'{description}')
    message = f"<@{player_id}>"
    return embed, message


def log_embed(character_name, author, level, milestone_change, milestones_total, milestones_remaining, tier, trial_change, trials, trials_remaining, gold, gold_change, effective_gold, transaction_id, flux, flux_change, tradition_name, tradition_link, template_name, template_link, alternate_reward, source):
    embed = discord.Embed(title=f"{character_name}", description=f"Character Change", color=discord.Colour.blurple())
    embed.set_author(name=f'{author}')
    if milestone_change is not None:
        embed.add_field(name="Milestone Change", value=f'**Level**: {level}, **Milestone Change**: {milestone_change}, **Total Milestones**: {milestones_total}, **Milestones Remaining**: {milestones_remaining}', inline=False)
    if trial_change is not None:
        embed.add_field(name="Trial Change", value=f'**Mythic Tier**: {tier}, **Trial Change**: {trial_change}, **Total Trials**: {trials}, **Trials Remaining**: {trials_remaining}', inline=False)
    if gold_change is not None:
        embed.add_field(name="Wealth Changes", value=f'**Gold**: {gold}, **Gold Change**: {gold_change}, **Effective Gold**: {effective_gold} GP **Transaction_ID**: {transaction_id}', inline=False)
    if flux_change is not None:
        embed.add_field(name="Flux Change", value=f'**Flux**: {flux}, **Flux Change**: {flux_change}', inline=False)
    if tradition_name is not None:
        embed.add_field(name="Tradition Change", value=f'**Tradition**: [{tradition_name}]({tradition_link})', inline=False)
    if template_name is not None:
        embed.add_field(name="Template Change", value=f'**Template**: [{template_name}]({template_link})', inline=False)
    if alternate_reward is not None:
        embed.add_field(name="other rewards", value=f'{alternate_reward}', inline=False)
    embed.set_footer(text=f"{source}")
    return embed


def level_calculation(guild_id, milestone_total, rewarded):
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    new_milestone_total = milestone_total + rewarded
    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
    max_level = cursor.fetchone()
    cursor.execute(
        f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{new_milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
    current_level = cursor.fetchone()
    int_max_level = int(max_level[0])
    if int_max_level < current_level[0]:
        cursor.execute(
            f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Level = {int_max_level} ORDER BY Minimum_Milestones DESC  LIMIT 1")
        current_level = cursor.fetchone()
        true_level = int(max_level[0])
    else:
        cursor.execute(
            f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{new_milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
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
    trials_required = current_mythic_information[1] + current_mythic_information[2] - trial_total
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
    return gold_total, gold_value_total, gold_value_max_total, difference

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
        await Event.create_kingdom(self, kingdom, password, government, alignment, economy, loyalty, stability, guild_id, author)
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
        await Event.destroy_kingdom(self, kingdom, guild_id, author)
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
    cursor.execute(f"""SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{old_kingdom}'""",  {'Kingdom': old_kingdom})
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
        await Event.modify_kingdom(self, old_kingdom, new_kingdom, new_password, new_government, new_alignment, guild_id, author)
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
    sql = f"""Select True_Character_Name, Gold from Player_Characters where Player_Name = ? and Character_Name = ? OR Nickname = ?"""
    val = (author, character_name, character_name)
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
                    await Event.adjust_build_points(self, kingdom, amount, guild_id, character_info[0], author)
                    await interaction.response.send_message(f"the kingdom of {kingdom} has been adjusted by {amount} build points and has a new value of {build_points}! {character_info[0]} has been charged {cost} GP leaving {gold_value} remaining!")
"""We can make this ALL settlements for that kingdom, or a specific settlement"""


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
        sql = f"""Select True_Character_Name, Gold from Player_Characters where Character_Name = ? or Nickname = ?"""
        val = (character_name, character_name)
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
                        await Event.adjust_stabilization_points(self, kingdom, amount, guild_id, author, character_info[0])
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
        await Event.create_blueprint(self, building, build_points, lots, economy, loyalty, stability, fame, unrest, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spell_casting, supply, settlement_limit, district_limit, description, guild_id, author)
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
        await Event.remove_blueprint(self, building, guild_id, author)
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
        await Event.modify_blueprint(self, building, build_points, lots, economy, loyalty, stability, fame, unrest, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting, supply, settlement_limit, district_limit, description, guild_id, author)
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
        await Event.customize_kingdom_modifiers(self, kingdom, control_dc, economy, loyalty, stability, fame, unrest, consumption, guild_id, author)
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
        await Event.custom_settlement_modifiers(self, kingdom, settlement, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting, supply, guild_id, author)


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
            await Event.settlement_decay_set(self, kingdom, settlement, decay, guild_id, author)
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
        await Event.add_hex_improvements(self, improvement, build_points, road_multiplier, economy, loyalty, stability, unrest, consumption, defence, taxation, cavernous, coastline, desert, forest, hills, jungle, marsh, mountain, plains, water, guild_id, author)
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
        await Event.remove_hex_improvement(self, improvement, guild_id, author)
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
            await Event.modify_hex_improvement(self, old_improvement, new_improvement, new_build_points, new_road_multiplier, new_economy, new_loyalty, new_stability, new_unrest, new_consumption, new_defence, new_taxation, new_cavernous, new_coastline, new_desert, new_forest, new_hills, new_jungle, new_marsh, new_mountains, new_plains, new_water, guild_id, author)
        elif result1[0] == result2[0]:
            await Event.modify_hex_improvement(self, old_improvement, new_improvement, new_build_points, new_road_multiplier, new_economy, new_loyalty, new_stability, new_unrest, new_consumption, new_defence, new_taxation, new_cavernous, new_coastline, new_desert, new_forest, new_hills, new_jungle, new_marsh, new_mountains, new_plains, new_water, guild_id, author)
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
    await Event.balance_tables(self, guild_id, author)
    status = f"TABLE UPDATE HAS BEEN COMPLETED"
    await ctx.response.send_message(status)


@admin.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Admin Help", description=f'This is a list of Admin help commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**character_milestones**', value=f'Modifies the milestones associated with a character.', inline=False)
    embed.add_field(name=f'**character_trials**', value=f'Modifies the trials associated with a character.', inline=False)
    embed.add_field(name=f'**gold_adjust**', value=f'Modifies the gold that a character has.', inline=False)
    embed.add_field(name=f'**undo_transaction**', value=f'Undo a gold transaction=.', inline=False)
    embed.add_field(name=f'**Flux_Adjust**', value=f'Modifies the flux that a character has', inline=False)
    embed.add_field(name=f'**session**', value=f'alter the reward from a session.', inline=False)
    embed.add_field(name=f'**ubb_inventory**', value=f'Display the inventory of a user in order to find information.', inline=False)
    embed.add_field(name=f'**settings_display**', value=f'Display the various Administrative Defined Settings.', inline=False)
    embed.add_field(name=f'**settings_define**', value=f'Define an Administrative Setting.', inline=False)
    embed.add_field(name=f'**level_cap**', value=f'Set a new level cap and set all player characters levels as appropriate.', inline=False)
    embed.add_field(name=f'**Tier_cap**', value=f'Set a new tier cap and set all player characters levels as appropriate.', inline=False)
    embed.add_field(name=f'**level_range**', value=f'Define a role and range for a level range.', inline=False)
    embed.add_field(name=f'**reset_database**', value=f'Reset the Server Database to Defaults.', inline=False)
    embed.add_field(name=f'**clean_playerbase**', value=f'Clean out a or all inactive player characters from player characters and gold history and .', inline=False)
    embed.add_field(name=f'**manage**', value=f'Accept or reject a player registration attempt, or clean out historical ones.', inline=False)
    embed.add_field(name=f'**customize**', value=f'Administrative: Apply a Tradition or Template for a character', inline=False)
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
    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name,character_name))
    player_info = cursor.fetchone()
    if player_info is None:
        await ctx.response.send_message(f"{author} does not have {character_name} registered to their account.")
    if player_info is not None:
        if job_name == 'None' or amount == 0 and misc_milestones == 0:
            await ctx.response.send_message("No Change in Milestones!", ephemeral=True)
        else:
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
            max_level = cursor.fetchone()
            int_max_level = int(max_level[0])
            if job_name is not None:
                character_level = player_info[7] if level is None else level
                cursor.execute(f"SELECT {job_name} from AA_Milestones where level = {character_level}")
                milestone_info = cursor.fetchone()
                milestone_total = milestone_info[0] + misc_milestones + player_info[2]
                adjust_milestones = milestone_info[0] + misc_milestones
            else:
                milestone_total = player_info[2] + misc_milestones
                adjust_milestones = misc_milestones
            cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones < '{milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
            current_level = cursor.fetchone()
            if current_level[0] < int_max_level:
                character_level = character_level
                remaining = current_level[1] + current_level[2] - milestone_total
            else:
                character_level = int_max_level
                cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE level = '{character_level}'")
                current_level = cursor.fetchone()
                remaining = current_level[1] + current_level[2] - milestone_total
            if current_level is None:
                await ctx.response.send_message(f"Comrade, one cannot degrade this character: {character_name} past level 3, please train them to  best level up in the future!")
            else:
                await Event.adjust_milestones(self, character_name, milestone_total, remaining, character_level, guild_id, author)
                if character_level != player_info[1]:
                    cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {player_info[5]}")
                    level_range = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Desc")
                    level_range_max = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Asc")
                    level_range_min = cursor.fetchone()
                    cursor.execute(f"Select True_Character_Name from Player_Characters WHERE Player_Name = {player_info[0]} AND level >= {level_range_min[0]} AND level <= {level_range_max[0]}")
                    level_range_characters = cursor.fetchone()
                    member = await guild.fetch_member(player_info[4])
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    accepted_bio_channel = cursor.fetchone()
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                    character_log_channel_id = cursor.fetchone()
                    bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], character_level, player_info[8], milestone_total, remaining, player_info[11], player_info[12], player_info[13], player_info[14],  player_info[16] , player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                    bio_message = await bio_channel.fetch_message(player_info[24])
                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                    source = f"admin adjusted milestones by {adjust_milestones} for {character_name}"
                    logging_embed = log_embed(player_info[0], author, character_level, adjust_milestones, milestone_total, remaining, None, None, None, None, None, None, None, None, None, None, None, None,None, None, None, source)
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
    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name,character_name))
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
                bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14],  player_info[16] , player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"admin adjusted trials by {amount} for {character_name}"
                logging_embed = log_embed(player_info[0], author, None, None, None, None, trial_info[0], amount, total_trials, trial_info[1] + trial_info[2] - total_trials, None, None, None, None, None, None, None, None,None, None, None, source)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await Event.adjust_trials(self, character_name, total_trials, guild_id, author)
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
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ? OR Nickname = ?",(character_name, character_name))
        player_info = cursor.fetchone()
        if player_info is None:
            await ctx.response.send_message(f"There is no character with the name or nickname of {character_name}.")
        else:
            amount = 0 if amount is None else amount
            gold_info = gold_calculation(player_info[7], player_info[6], player_info[13], player_info[14], player_info[15], amount)
            lifetime_gold_change = lifetime_gold if lifetime_gold is not None else amount
            effective_gold_change = effective_gold if effective_gold is not None else gold_info[3]
            await Event.gold_change(self, guild_id, author, author_id, player_info[3], gold_info[3], effective_gold_change, lifetime_gold_change, reason, 'Admin Gold Adjust')
            cursor.execute(f'SELECT MAX(Transaction_ID) FROM Gold_History Order By Transaction_ID DESC LIMIT 1')
            transaction_id = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + gold_info[3], player_info[14] + effective_gold_change,  player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"admin adjusted gold by {amount} for {character_name}"
            logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, player_info[13] + gold_info[3], gold_info[3], player_info[14] + effective_gold_change, transaction_id[0], None, None, None, None, None, None, None, source)
            logging_thread = guild.get_thread(player_info[25])
            await logging_thread.send(embed=logging_embed)
            embed = discord.Embed(title=f"Admin Gold Change", description=f'Gold Adjustment Transaction', colour=discord.Colour.blurple())
            embed.add_field(name=f'**Adjustments**', value=f'Gold change: {gold_info[3]}, Effective Gold Change: {effective_gold_change}, Lifetime Wealth Change: {lifetime_gold_change}', inline=False)
            embed.add_field(name=f"**Totals**", value=f"Gold Total: {player_info[13] + gold_info[3]}, Effective Gold Total: {player_info[14] + effective_gold_change}, Lifetime Wealth Total: {player_info[15] + lifetime_gold_change}", inline=False)
            embed.set_footer(text=f"Transaction ID: {transaction_id[0]}")
            await ctx.response.send_message(embed=embed)
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
    cursor.execute(f"Select Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_value_max FROM Gold_History WHERE Transaction_ID = {transaction_id}")
    transaction_info = cursor.fetchone()
    if transaction_info is not None:
        embed = discord.Embed(title=f"Undoing Transaction: {transaction_id}", description=f'Undoing a transaction', colour=discord.Colour.red())
        """Help commands for the associated tree"""
        mentions = f"The Below Transaction has been cancelled for {transaction_info[2]}, <@{transaction_info[1]}>"
        gold = transaction_info[3] * -1
        effective_gold = transaction_info[4] * -1
        max_effective_gold = transaction_info[5] * -1
        embed.add_field(name=f"**{transaction_info[2]}'s Transaction Info:**", value=f'**Gold:** {transaction_info[3]} GP, **Effective Gold**: {transaction_info[4]} GP, **Lifetime Gold**: {transaction_info[5]}.', inline=False)
        cursor.execute(f"Select Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_value_max, Transaction_ID FROM Gold_History WHERE Related_Transaction_ID = {transaction_id}")
        related_transaction_info = cursor.fetchone()
        await Event.undo_transaction(self, guild_id, transaction_id, gold, effective_gold, max_effective_gold, transaction_info[2], transaction_info[0])
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
        accepted_bio_channel = cursor.fetchone()
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
        character_log_channel_id = cursor.fetchone()
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ?",(transaction_info[2],))
        player_info = cursor.fetchone()
        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
        bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + gold, player_info[14] + effective_gold, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
        bio_message = await bio_channel.fetch_message(player_info[24])
        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
        source = f"admin undid transaction {transaction_id}"
        logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, player_info[13] + gold, gold, player_info[14] + effective_gold, transaction_id, None, None, None, None, None, None, None, source)
        logging_thread = guild.get_thread(player_info[25])
        await logging_thread.send(embed=logging_embed)
        if related_transaction_info is not None:
            mentions = f"and for {transaction_info[2]}, <@{transaction_info[1]}>!"
            """Help commands for the associated tree"""
            gold = related_transaction_info[3] * -1
            effective_gold = related_transaction_info[4] * -1
            max_effective_gold = related_transaction_info[5] * -1
            cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ?",(related_transaction_info[2],))
            player_info = cursor.fetchone()
            embed.add_field(name=f"**{related_transaction_info[2]}'s Transaction Info:**", value=f'**Gold:** {related_transaction_info[3]} GP, **Effective Gold**: {related_transaction_info[4]} GP, **Lifetime Gold**: {related_transaction_info[5]}.', inline=False)
            await Event.undo_transaction(self, guild_id, related_transaction_info[6], gold, effective_gold, max_effective_gold, related_transaction_info[0], related_transaction_info[2])
            bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7],player_info[8], player_info[9], player_info[10], player_info[11],player_info[12], player_info[13] + gold, player_info[14] + effective_gold,player_info[16], player_info[17], player_info[18], player_info[19],player_info[20], player_info[21], player_info[22], player_info[23],player_info[1])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"admin undid transaction {transaction_id}"
            logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None,player_info[13] + gold, gold, player_info[14] + effective_gold, transaction_id,None, None, None, None, None, None, source)
            logging_thread = guild.get_thread(player_info[25])
            await logging_thread.send(embed=logging_embed)
    else:
        mentions = f"This Transaction was not a valid transaction to undo!!"
        embed = discord.Embed(title=f"Command Failed! Undo Transaction: {transaction_id}", description=f'This Command Failed', colour=discord.Colour.red())
    await ctx.response.send_message(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
    cursor.close()
    db.close()


@admin.command()
async def session_management(interaction: discord.Interaction, session_id: int, gold: typing.Optional[int], easy: typing.Optional[int], medium: typing.Optional[int], hard: typing.Optional[int], deadly: typing.Optional[int], milestones: typing.Optional[int], flux: typing.Optional[int], trials: typing.Optional[int], reward_all: typing.Optional[str], party_reward: typing.Optional[str]):
    """Update Session Information and alter the rewards received by the players"""
    guild_id = interaction.guild_id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT GM_Name, Session_Name, Play_Time, Session_Range, Gold, Flux, Easy, Medium, Hard, Deadly, Milestones, Trials, Alt_Reward_All, Alt_Reward_Party, Session_Thread, Message FROM Sessions WHERE Session_ID = {session_id} and IsActive = 0 LIMIT 1""")
    session_simple = cursor.fetchone()
    cursor.execute(f"""SELECT Player_Name, Character_Name,  Level, Received_Milestones, Effective_Gold, Received_Gold, Player_ID FROM Sessions_Archive WHERE Session_ID = {session_id}""")
    session_complex = cursor.fetchall()
    if session_simple is None:
        await interaction.response.send_message(f'invalid session ID of {session_id}')
    else:
        if gold is not None and gold < 0 or easy is not None and easy < 0 or medium is not None and medium < 0 or hard is not None and hard < 0 or deadly is not None and deadly < 0 or milestones is not None and milestones < 0 or flux is not None and flux < 0 or trials is not None and trials < 0:
            await interaction.response.send_message(f"Minimum Session Rewards may only be 0, if a player receives a lesser reward, have them claim the transaction.")
        elif gold is None and easy is None and medium is None and hard is None and deadly is None and milestones is None and flux is None and trials is NoWAne:
            embed = discord.Embed(title="Session Report", description=f"a report of the session: {session_simple[1]}", color=discord.Color.blue())
            embed.set_author(name=f'{session_simple[0]}')
            embed.add_field(name="Session Info", value=f'**GM:** {session_simple[0]} \n **Level Range**: {session_simple[3]}, **Gold**: {session_simple[4]}, **Flux**:{session_simple[5]}, **Trials**: {session_simple[10]}', inline=False)
            embed.add_field(name="Job Info", value=f'**Easy**: {session_simple[6]}, **Medium**:{session_simple[7]}, **Hard**: {session_simple[8]}, **Deadly**: {session_simple[9]}', inline=False)
            for player in session_complex:
                embed.add_field(name="Character Info", value=f'Player: {player[0]} Character:{player[1]} \n **Level**: {player[2]} \n **Milestones Received**: {player[3]} **Gold Received**: {player[5]}', inline=False)
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
            milestones = session_simple[10] if milestones is None else milestones
            trials = session_simple[11] if trials is None else trials
            reward_all = session_simple[12] if reward_all is None else reward_all
            party_reward = session_simple[13] if party_reward is None else party_reward
            embed = discord.Embed(title="Session Report", description=f"a report of the session: {session_simple[1]}", color=discord.Color.blue())
            embed.set_author(name=f'{session_simple[0]}')
            embed.add_field(name="Session Info", value=f'**GM:** {session_simple[0]} \n **Level Range**: {session_simple[3]}, **Gold**: {gold}, **Flux**:{flux}, **Trials**: {trials}', inline=False)
            embed.add_field(name="Job Info", value=f'**Easy**: {easy}, **Medium**:{medium}, **Hard**: {hard}, **Deadly**: {deadly}, **Misc**: {milestones}', inline=False)
            x = 0
            if party_reward is not None:
                thread = guild.get_thread(session_simple[14])
                party_reward_embed = discord.Embed(title="Party Reward", description=f"Party Reward for {session_simple[1]}", color=discord.Color.blue())
                party_reward_embed.set_author(name=f'{session_simple[0]}')
                party_reward_embed.add_field(name="Reward Info", value=f'{party_reward}', inline=False)
                await thread.send(f"{party_reward_embed}")
            for player in session_complex:
                x += 1
                cursor.execute(f"""SELECT Easy, Medium, Hard, Deadly from AA_Milestones WHERE level = {player[2]}""")
                job_info = cursor.fetchone()
                easy_jobs = (easy - session_simple[6]) * job_info[0]
                medium_jobs = (medium - session_simple[7]) * job_info[1]
                hard_jobs = (hard - session_simple[8]) * job_info[2]
                deadly_jobs = (deadly - session_simple[9]) * job_info[3]
                milestones_value = (milestones - session_simple[10])
                rewarded = easy_jobs + medium_jobs + hard_jobs + deadly_jobs + milestones_value
                new_milestones = player[3] + rewarded
                # SETTING WHAT THE LEVEL WILL BE.
                cursor.execute(f"SELECT Milestones, Tier, Trials, Gold, Gold_Value, Gold_Value_Max, Flux, Oath FROM Player_Characters WHERE Character_Name = ?",(player[1],))
                current_info = cursor.fetchone()
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ?",(player[1],))
                player_info = cursor.fetchone()
                new_milestone_total = player_info[9] + rewarded
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
                max_level = cursor.fetchone()
                int_max_level = int(max_level[0])
                cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{new_milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
                current_level = cursor.fetchone()
                if int_max_level < current_level[0]:
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
                trials_total = player_info[11] + trials - session_simple[11]
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
#                CREATING THE GOLD VARIABLES (REQUIRES LEVEL TO BE ALREADY SET)
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
                await Event.session_rewards(self, player[0], guild_id, player[1],  true_level, new_milestone_total, remaining, flux_total, true_tier, trials_total, trials_required, session_id)
                await Event.gold_change(self, guild_id, player[0], player[6], player[1], difference, difference, gold, 'Session Reward', 'Session Reward')
                await Event.update_session_log_player(self, guild_id, session_id, player[1], rewarded, trials, difference)
                embed.add_field(name="Character Info", value=f'Player: {player[0]} Character:{player[1]} \n **Level**: {true_level} \n **Milestone change**: {rewarded} **Gold change**: {difference}', inline=False)
                cursor.execute(f'SELECT MAX(Transaction_ID) FROM Gold_History Order By Transaction_ID DESC LIMIT 1')
                transaction_id = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], true_level, true_tier, new_milestone_total, remaining, trials_total, trials_required, player_info[13] + difference, player_info[14] + difference, flux_total, player_info[17], player_info[18], player_info[19], player_info[20], player_info[21],player_info[22], player_info[23], player_info[1])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"admin adjusted session {session_id}"
                logging_embed = log_embed(player_info[0], player_info[2], true_level, rewarded, new_milestone_total, remaining, true_tier,  trials - session_simple[11], trials_total, trials_required, player_info[13] + difference, difference, player_info[14] + difference, transaction_id[0], flux_total, flux - session_simple[5], None, None, None, None, reward_all, source)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
            await Event.update_session_log(self, guild_id, session_id, gold, flux, easy, medium, hard, deadly, trials, reward_all, party_reward)
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
            await Event.update_settings(self, guild_id, author, new_search, identifier)
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
        await Event.update_level_cap(self, guild_id, author, new_level)
        cursor.execute(f"SELECT Minimum_Milestones FROM AA_Milestones where Level = {new_level}")
        level_info = cursor.fetchone()
        minimum_milestones = level_info[0]
        cursor.execute(f"SELECT COUNT(Character_Name) FROM Player_Characters WHERE Milestones >= {minimum_milestones}")
        count_of_characters = cursor.fetchone()
        cursor.execute(f"SELECT Player_Name, Player_ID, Character_Name, Level FROM Player_Characters WHERE Milestones >= {minimum_milestones} LIMIT 20")
        characters_info = cursor.fetchall()
        embed = discord.Embed(title=f"New Level Cap", description=f'The Server level cap has been adjusted', colour=discord.Colour.blurple())
        if count_of_characters is not None:
            x = 0
            character_count = count_of_characters[0]
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            for characters in characters_info:
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
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ?",(player[1],))
                player_info = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], new_level, player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21],player_info[22], player_info[23], player_info[1])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"admin adjusted adjusted level cap to {new_level}"
                logging_embed = log_embed(player_info[0], author, new_level, 0, player_info[9], player_info[10], player_info[8],  0, player_info[11], player_info[12], None, None, None, None, None, None, None, None, None, None, None, source)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
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
        await interaction.response.send_message(embed=embed)
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
    if new_tier < 1:
        await interaction.response.send_message(f"Negative Mythic Tiers? More like... Negative Brain Cells AMIRITE? {new_tier} is not valid")
    elif new_tier > 10:
        await interaction.response.send_message(f"Just make them gods already damnit?! {new_tier} is too high!")
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
        await Event.update_tier_cap(self, guild_id, author, new_tier, minimum_level)
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
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ?",(characters[3],))
                player_info = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"admin adjusted adjusted tier cap to {new_tier}"
                logging_embed = log_embed(player_info[0], author, None, None, None,None, new_tier, 0, player_info[11], player_info[12], None, None, None, None, None, None, None, None, None, None, None, source)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
            if character_count <= 20:
                embed.set_footer(text=f"Are all the characters who have been adjusted to a new new_tier.")
            else:
                character_count -= 20
                embed.set_footer(text="And {character_count[0]} more have obtained a new tier")
        if count_of_characters is None:
            embed.add_field(name=f"**No Characters Changed:**", value=f"The server cap is now {new_tier} but no characters meet the minimum milestones.", inline=False)
        await interaction.response.send_message(embed=embed)
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
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name, character_name))
        player_info = cursor.fetchone()
        if player_info is None:
            await ctx.response.send_message(f"There is no character named {character_name} that can be found by their name or nickname")
        elif player_info is not None:
            true_name = player_info[2]
            new_flux = player_info[16] + amount
            await Event.flux(self, guild_id, true_name, amount, new_flux,  author)
            response = f"{character_name}'s Flux has changed by {amount} to become {new_flux}."
            await ctx.response.send_message(response)
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14],  player_info[16] + amount, player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"admin adjusted gold by {amount} for {character_name}"
            logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, new_flux, amount, None, None, None, None, None, source)
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
        await Event.set_range(self, guild_id, author, role_name, role_id, minimum_level, maximum_level)
        embed = discord.Embed(title=f"Range Update", description=f'a new role name and role ID has been applied', colour=discord.Colour.green())
        embed.add_field(name=f'**Role**', value=f'{role_name} with ID: {role_id}.', inline=False)
        embed.add_field(name=f'**Range**', value=f'{minimum_level} level to {maximum_level} level have been updated', inline=False)
        await ctx.response.send_message(embed=embed)


@admin.command()
@app_commands.describe(certainty="is life short?")
@app_commands.choices(certainty=[discord.app_commands.Choice(name='YOLO', value=1), discord.app_commands.Choice(name='No', value=2)])
async def reset_database(ctx: commands.Context, certainty: discord.app_commands.Choice[int]):
    """Perform a database reset, remember to reassign role ranges and server settings!"""
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
                        await Event.wipe_unapproved(self, wiped[0], guild_id, author)



@admin.command()
@app_commands.autocomplete(character_name=stg_character_select_autocompletion)
@app_commands.describe(cleanse="Optional: supply a number ending with D or W to remove users who have not been accepted within that period!")
@app_commands.describe(status="Accepted players are moved into active and posted underneath!")
@app_commands.choices(status=[discord.app_commands.Choice(name='Accepted!', value=1), discord.app_commands.Choice(name='Rejected!', value=2)])
async def manage(ctx: commands.Context, character_name: str, player_id: typing.Optional[int], status: discord.app_commands.Choice[int] = 1, cleanse: str = None):
    """accept a player into your accepted bios, or clean out the stage tables!"""
    guild = ctx.guild
    guild_id = ctx.guild_id
    if character_name is None and cleanse is None:
        await ctx.response.send_message(f"NOTHING COMPLETED, RUN DURATION: 1 BAJILLION Eternities?", ephemeral=True)
    elif cleanse is not None or character_name is not None and status.value == 2 or player_id is not None and status == 2:
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = ctx.user.name
        if status.value == 2:
            overall_wipe_list = []
            character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
            embed = discord.Embed(title=f"The Following Players will have their staged characters removed:",
                                  description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
            if character_name is not None:
                cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where character_name = ?", (character_name,))
                player_id_info = cursor.fetchone()
                if player_id_info is not None:
                    overall_wipe_list.append(character_name)
                    embed.add_field(name=f"{player_id_info[0]}'s character will be removed from stage", value=f"The character of {character_name} will be removed!!")
                else:
                    embed.add_field(name=f"{character_name} could not be found in the database.", value=f"This character name had no characters associated with it..")
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
                            await Event.wipe_unapproved(self, wiped, guild_id, author)
    else:
        guild_id = ctx.guild_id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = ctx.user.name
        character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
        cursor.execute(f"Select distinct(True_Character_Name), count(Character_Name) from A_STG_Player_Characters where character_name = ?", (character_name,))
        player_id_info = cursor.fetchone()
        if player_id_info is not None:
            await Event.create_character(self, guild_id, author, player_id_info[0])
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            cursor.execute(f"SELECT Player_Name, True_Character_Name, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_Value_Max, Mythweavers, Image_Link, Color, Flux, Player_ID FROM Player_Characters WHERE Character_Name = ?", (character_name,))
            character_info = cursor.fetchone()
            color = character_info[15]
            int_color = int(color[1:], 16)
            mentions = f'<@{character_info[17]}>'
            embed = discord.Embed(title=f"{character_info[1]}", url=f'{character_info[13]}', description=f"Other Names: {character_info[2]}", color=int_color)
            embed.set_author(name=f'{character_info[0]}')
            embed.set_thumbnail(url=f'{character_info[14]}')
            embed.add_field(name="Information", value=f'**Level**: 3, **Mythic Tier**: 0', inline=False)
            embed.add_field(name="Experience", value=f'**Milestones**: 0, **Remaining**: 3')
            embed.add_field(name="Mythic", value=f'**Trials**: 0, **Remaining**: 0')
            embed.add_field(name="Current Wealth", value=f'**GP**: {character_info[10]}', inline=False)
            embed.add_field(name="Current Flux", value=f'**Flux**: 0')
            embed.set_footer(text=f'{character_info[3]}')
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.send(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            embed = discord.Embed(title=f"{character_info[1]}", url=f'{character_info[13]}', description=f"Other Names: {character_info[2]}", color=int_color)
            embed.set_author(name=f'{character_info[0]}')
            embed.set_thumbnail(url=f'{character_info[14]}')
            character_log_channel = await bot.fetch_channel(character_log_channel_id[0])
            character_log_message = await character_log_channel.send(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            thread = await character_log_message.create_thread(name=f'{character_info[1]}')
            await Event.log_character(self, guild_id, character_name, bio_message.id, character_log_message.id, thread.id)
            await ctx.response.send_message(content=f"{character_name} has been accepted into the server!")
            cursor.execute(f"SELECT Search FROM Admin WHERE Identifier = 'Approved_Character'")
            approved_character = cursor.fetchone()
            member = await guild.fetch_member(character_info[17])
            role1 = guild.get_role(int(approved_character[0]))
            await member.add_roles(role1)

        else:
            await ctx.response.send_message(f"{character_name} could not be found in the database.", ephemeral=True)


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
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = ctx.user.name
    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ?",(character_name, character_name))
    player_info = cursor.fetchone()
    cursor.close()
    db.close()
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
        await Event.customize_characters(self, guild_id, author, player_info[3], destination_name, destination_link, customized_name, link, flux_remaining, flux_cost)
        embed = discord.Embed(title=f"{destination_name_pretty} change for {player_info[3]}", description=f"<@{player_info[1]}>'s {player_info[3]} has spent {flux_cost} flux leaving them with {player_info[16] - flux_cost} flux!", colour=discord.Colour.blurple())
        embed.add_field(name=f'**{destination_name_pretty} Information:**', value=f'[{customized_name}](<{link}>)', inline=False)
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
        accepted_bio_channel = cursor.fetchone()
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
        character_log_channel_id = cursor.fetchone()
        bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16] + flux_cost, player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
        bio_message = await bio_channel.fetch_message(player_info[24])
        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
        source = f"changed a template or tradition for {character_name}"
        logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, player_info[16] - flux_cost, flux_cost, tradition_name, tradition_link, template_name, template_link, None, source)
        logging_thread = guild.get_thread(player_info[25])
        await logging_thread.send(embed=logging_embed)
        await ctx.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))




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
        await Event.claim_settlement(self, kingdom, settlement, guild_id, author)


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
        await Event.destroy_settlement(self, kingdom, settlement, guild_id, author)
        await ctx.response.send_message(status)
    elif settlement_result is None:
        status = f"You cannot have {kingdom} make a war crime out of {settlement} if it doesn't exist!"
        await ctx.response.send_message(status)


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
        await Event.modify_settlement(self, kingdom, old_settlement, new_settlement, guild_id, author)


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
async def displayall(ctx: commands.Context, kingdom: str, settlement: str,  current_page: int = 1):
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
        await Event.construct_building(self, kingdom, settlement, building, amount, guild_id, author)


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
        await Event.destroy_building(self, kingdom, settlement, building, amount, guild_id, author)


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
        await Event.modify_leader(self, kingdom, leader, title, modifier, column, economy_modifier, loyalty_modifier, stability_modifier, guild_id, author)
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
        await Event.remove_leader(self, kingdom, title, guild_id, author)
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
        await Event.claim_hex(self, kingdom, hex_terrain, guild_id, author)
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
        await Event.relinquish_hex(self, kingdom, hex_terrain, guild_id, author)
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
                await Event.improve_hex(self, kingdom, hex_terrain, improvement, guild_id, author)
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
        await Event.diminish_hex(self, kingdom, hex_terrain, improvement, guild_id, author)
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
    await ctx.response.send_message(embed=embed)


@character.command()
@app_commands.describe(oath="Determining future gold gain from sessions and gold claims.")
@app_commands.choices(oath=[discord.app_commands.Choice(name='No Oath', value=1), discord.app_commands.Choice(name='Oath of Offerings', value=2), discord.app_commands.Choice(name='Oath of Poverty', value=3), discord.app_commands.Choice(name='Oath of Absolute Poverty', value=4)])
@app_commands.describe(nickname='a shorthand way to look for your character in displays')
async def register(ctx: commands.Context, character_name: str, mythweavers: str, image_link: str, nickname: str = None, titles: str = None, description: str = None, oath: discord.app_commands.Choice[int] = 1, color: str = '#5865F2'):
    """Register your character"""
    if character_name is not None:
        true_character_name = str.replace(str.replace(str.title(character_name), ";", ""), ")", "")
        character_name = unidecode(true_character_name)
    else:
        await ctx.response.send_message(f"Character Name is required")
        return
    if nickname is not None:
        nickname = str.replace(str.replace(str.title(nickname), ";", ""), ")", "")
    if titles is not None:
        titles = str.replace(str.replace(titles, ";", ""), ")", "")
    if description is not None:
        description = str.replace(str.replace(description, ";", ""), ")", "")
    if mythweavers is not None:
        mythweavers = str.replace(str.replace(mythweavers, ";", ""), ")", "")
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
        if results is None and results2 is None:
            int_color = int(color[1:], 16)
            await Event.stage_character(self, true_character_name, character_name, author, author_id, guild_id, nickname, titles, description, oath_name, mythweavers, image_link, color)
            await Event.stg_gold_change(self, guild_id, author, author_id, character_name, starting_gold, starting_gold, 3000, 'Character Creation', 'Character Create')
            embed = discord.Embed(title=f"{character_name}", url=f'{mythweavers}', description=f"Other Names: {titles}", color=int_color)
            embed.set_author(name=f'{author}')
            embed.set_thumbnail(url=f'{image_link}')
            embed.add_field(name="Information", value=f'**Level**: 3, **Mythic Tier**: 0', inline=False)
            embed.add_field(name="Experience", value=f'**Milestones**: 0, **Remaining**: 3')
            embed.add_field(name="Mythic", value=f'**Trials**: 0, **Remaining**: 0')
            embed.add_field(name="Current Wealth", value=f'**GP**: {starting_gold}', inline=False)
            embed.add_field(name="Current Flux", value=f'**Flux**: 0')
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
                await Event.fix_character(self, guild_id, character_name)
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
    name = str.replace(str.replace(str.title(name), ";", ""), ")", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    sql = f"""Select True_Character_Name, Nickname, Titles, Description, Mythweavers, Image_Link, Oath, Color, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Gold_Value, Gold_Value_Max, Flux from Player_Characters where Player_Name = ? AND Character_Name = ? OR Nickname = ?"""
    val = (author, name, name)
    cursor.execute(sql, val)
    results = cursor.fetchone()
    if results is None:
        sql = f"""Select True_Character_Name, Nickname, Titles, Description, Mythweavers, Image_Link, Oath, Color, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Gold_Value, Gold_Value_Max, Flux, Character_Name from A_STG_Player_Characters where Player_Name = ? AND Character_Name = ? OR Nickname = ?"""
        val = (author, name, name)
        cursor.execute(sql, val)
        results = cursor.fetchone()
        if results is None:
            await ctx.response.send_message(f"Cannot find any {name} owned by {author} with the supplied name or nickname.")
        else:
            if new_character_name is not None:
                new_character_name = str.replace(str.replace(str.title(new_character_name), ";", ""), ")", "")
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
            if mythweavers is not None:
                mythweavers = str.replace(str.replace(mythweavers, ";", ""), ")", "")
                mythweavers_valid = str.lower(mythweavers[0:5])
                if mythweavers_valid != 'https':
                    await ctx.response.send_message(f"Mythweavers link is missing HTTPS:")
                    return
            else:
                mythweavers = results[4]
            if image_link is not None:
                image_link = str.replace(str.replace(image_link, ";", ""), ")", "")
                image_link_valid = str.lower(image_link[0:5])
                if image_link_valid != 'https':
                    await ctx.response.send_message(f"Image link is missing HTTPS:")
                    return
            else:
                image_link = results[5]
            if oath == 1:
                oath_name = 'No Oath'
            if oath == 2:
                oath_name = 'Offerings'
            elif oath == 3:
                oath_name = 'Poverty'
            elif oath == 4:
                oath_name = 'Absolute'
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
                    await Event.edit_stg_character(self, true_name, true_character_name, new_character_name, guild_id,
                                               new_nickname, titles, description, oath_name, mythweavers, image_link,
                                               color, author)
                    embed = discord.Embed(title=f"Edited Character: {new_character_name}", url=f'{mythweavers}',
                                          description=f"Other Names: {titles}", color=int_color)
                    embed.set_author(name=f'{author}')
                    embed.set_thumbnail(url=f'{image_link}')
                    embed.add_field(name="Information", value=f'**Level**: {results[8]}, **Mythic Tier**: {results[9]}',
                                    inline=False)
                    embed.add_field(name="Experience",
                                    value=f'**Milestones**: {results[10]}, **Remaining**: {results[11]}')
                    embed.add_field(name="Mythic", value=f'**Trials**: {results[12]}, **Remaining**: {results[13]}')
                    embed.add_field(name="Current Wealth",
                                    value=f'**Current gold**: {results[14]} GP, **Effective Gold**: {results[15]} GP, **Lifetime Wealth**: {results[16]} GP',
                                    inline=False)
                    embed.add_field(name="Current Flux", value=f'**Flux**: {results[17]}', inline=False)
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
            mythweavers_valid = mythweavers[0:4]
            if mythweavers_valid != 'HTTPS':
                await ctx.response.send_message(f"Mythweavers link is missing HTTPS:")
                return
        else:
            mythweavers = results[4]
        if image_link is not None:
            image_link = str.replace(str.replace(image_link, ";", ""), ")", "")
            image_link_valid = image_link[0:4]
            if image_link_valid != 'HTTPS':
                await ctx.response.send_message(f"Image link is missing HTTPS:")
                return
        else:
            image_link = results[5]
        if oath == 1:
            oath_name = 'No Oath'
        if oath == 2:
            oath_name = 'Offerings'
        elif oath == 3:
            oath_name = 'Poverty'
        elif oath == 4:
            oath_name = 'Absolute'
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

            if results is not None:
                int_color = int(color[1:], 16)
                true_name = results[0]
                await Event.edit_character(self, true_name, true_character_name, new_character_name, guild_id, new_nickname, titles, description, oath_name, mythweavers, image_link, color, author)
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ? or Nickname = ?", (new_character_name, new_nickname))
                player_info = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ? or Nickname = ?", (new_character_name, new_nickname))
                player_info = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                embed = discord.Embed(title=f"Edited Character: {new_character_name}", url=f'{mythweavers}', description=f"Other Names: {titles}", color=int_color)
                embed.set_author(name=f'{author}')
                embed.set_thumbnail(url=f'{image_link}')
                embed.add_field(name="Information", value=f'**Level**: {results[8]}, **Mythic Tier**: {results[9]}', inline=False)
                embed.add_field(name="Experience", value=f'**Milestones**: {results[10]}, **Remaining**: {results[11]}')
                embed.add_field(name="Mythic", value=f'**Trials**: {results[12]}, **Remaining**: {results[13]}')
                embed.add_field(name="Current Wealth", value=f'**Current gold**: {results[14]} GP, **Effective Gold**: {results[15]} GP, **Lifetime Wealth**: {results[16]} GP', inline=False)
                embed.add_field(name="Current Flux", value=f'**Flux**: {results[17]}', inline=False)
                embed.set_footer(text=f'{description}')
                cursor.close()
                db.close()
                await ctx.response.send_message(embed=embed)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=embed)
        else:
            await ctx.response.send_message(f"Invalid Hex Color Code!")


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
    sql = f"""SELECT True_Character_Name, Thread_ID from Player_Characters where  Player_Name = ? AND Character_Name = ? or Nickname = ?"""
    val = (author, character_name, character_name)
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
                    await Event.retire_character(self, guild_id, true_character_name, author)
                    source = f"Character has retired!"
                    logging_embed = log_embed(results[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, source)
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
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Nickname = ?", (author, character_name, character_name))
                player_info = cursor.fetchone()
                if player_info is not None:
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
                    max_level = cursor.fetchone()
                    true_character_name = player_info[3]
                    character_level = player_info[7]
                    if player_info[7] >= int(max_level[0]):
                        await interaction.response.send_message(f"you are currently at the level cap for the server.")
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
                                if x+1 == amount or character_level == int_max_level:
                                    await Event.adjust_milestones(self, true_character_name, milestone_total, remaining, character_level, guild_id, author)
                                    await client.delete_inventory_item(guild_id, author_id, item_id[0], used)
                                    mythic_information = mythic_calculation(guild_id, character_level, player_info[11], 0)
                                    tier = 0 if player_info[8] == 0 else mythic_information[0]
                                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                    accepted_bio_channel = cursor.fetchone()
                                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                                    character_log_channel_id = cursor.fetchone()
                                    bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], character_level, tier, milestone_total, remaining, player_info[11], mythic_information[1], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
                                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                    bio_message = await bio_channel.fetch_message(player_info[24])
                                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                    source = f"{author} has leveled up to level {character_level}! using {used} medium jobs from the shop."
                                    logging_embed = log_embed(player_info[0], author, character_level, milestones_earned, milestone_total, remaining, tier, 0, player_info[11], mythic_information[1], None, None, None, None, None, None, None, None, None, None, None, source)
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
                                        color = player_info[17]
                                        int_color = int(color[1:], 16)
                                        embed = discord.Embed(title="Mythweavers Sheet", url=f'{player_info[18]}', description=f"Other Names: {player_info[4]}", color=int_color)
                                        embed.set_author(name=f'{player_info[2]} Level Up Report')
                                        embed.set_thumbnail(url=f'{player_info[19]}')
                                        embed.add_field(name="Information", value=f'**New Level**:{character_level}', inline=False)
                                        embed.add_field(name="Experience", value=f'**Milestones**: {milestone_total}, **Remaining to next level**: {remaining}')
                                        embed.set_footer(text=f'You have spent {used} medium jobs from the store with {new} medium jobs remaining increasing your milestones by {milestones_earned}.')
                                        await interaction.response.send_message(embed=embed)

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
            cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Nickname = ?", (author, character_name, character_name))
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
                trial_total = player_info[11]
                used = 0
                if tier == 0:
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
                                    await Event.adjust_trials(self, character_name, trial_total, guild_id, author)
                                    await client.delete_inventory_item(guild_id, author_id, item_id[0], used)
                                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                    accepted_bio_channel = cursor.fetchone()
                                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                                    character_log_channel_id = cursor.fetchone()
                                    bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], tier, player_info[9], player_info[10], player_info[11] + used, trials_required, player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
                                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                    bio_message = await bio_channel.fetch_message(player_info[24])
                                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                    source = f"{author} has increased their tier to tier {tier}! using {used} medium jobs from the shop."
                                    logging_embed = log_embed(player_info[0], author, None, None, None, None, tier, used, player_info[11] + used, trials_required, None, None, None, None, None, None, None, None, None, None, None, source)
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
            cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Nickname = ?", (author, character_name, character_name))
            player_info = cursor.fetchone()
            if player_info is not None:
                true_character_name = player_info[3]
                new = inventory.quantity - 1
                character_level = player_info[7]
                cursor.execute(f"SELECT WPL from AA_Milestones where level = {character_level}")
                wpl_info = cursor.fetchone()
                if wpl_info[0] <= player_info[15]:
                    await interaction.response.send_message(f'You are too wealthy for the gold pouch, go rob an orphanage. Your lifetime wealth is {player_info[4]} GP against a WPL of {wpl_info[0]} GP')
                else:
                    gold = wpl_info[0] - player_info[15]
                    gold_info = gold_calculation(player_info[7], player_info[6], player_info[13], player_info[14], player_info[15], gold)
                    await Event.gold_change(self, guild_id, author, author_id, true_character_name, gold_info[3], gold_info[3], gold, 'Used Unbelievaboat Pouch', 'Used Unbelievaboat Pouch')
                    cursor.execute(f'SELECT MAX(Transaction_ID) FROM Gold_History Order By Transaction_ID DESC LIMIT 1')
                    transaction_id = cursor.fetchone()
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    accepted_bio_channel = cursor.fetchone()
                    bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + gold_info[3], player_info[14] + gold_info[3], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                    bio_message = await bio_channel.fetch_message(player_info[24])
                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                    source = f"Character has increased their wealth by {gold_info[3]} GP using a gold pouch from the shop, transaction_id: {transaction_id[0]}!"
                    logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, player_info[13] + gold_info[3], gold_info[3], player_info[14] + gold_info[3], transaction_id[0], None, None, None, None, None, None, None, source)
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
@app_commands.autocomplete(character_name=character_select_autocompletion)
async def display(ctx: commands.Context, character_name: str = 'All', player_name: str = 'NA', current_page: int = 1):
    """THIS COMMAND DISPLAYS CHARACTER INFORMATION"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    player_name = str.replace(player_name, ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if player_name == 'NA':
        player_name = ctx.user
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
        cursor.execute(f"""Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link from Player_characters WHERE player_name = '{player_name}' LIMIT {low}, {offset}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"{player_name} character page {current_page}", description=f"This is list of {player_name}'s characters", colour=discord.Colour.blurple())
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
                    cursor.execute(f"""Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link from Player_characters WHERE player = '{player_name}' LIMIT {low}, {offset}""")
                    edit_pull = cursor.fetchall()
                    embed = discord.Embed(title=f"{player_name} character page {current_page}", description=f"This is list of {player_name}'s characters", colour=discord.Colour.blurple())
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
                    await ctx.response.send_message(embed=embed)
                    await msg.edit(embed=embed)
    elif character_name != 'All':
        sql = f"""Select True_Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Gold_Value from Player_characters WHERE Character_Name = ? or Nickname = ?"""
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
            embed = discord.Embed(title="Mythweavers Sheet", url=f'{result[12]}', description=f"Other Names: {result[2]}", color=int_color)
            embed.set_author(name=f'{result[0]}')
            embed.set_thumbnail(url=f'{result[13]}')
            embed.add_field(name="Information", value=f'**Level**: {result[4]}, **Mythic Tier**: {result[5]}', inline=False)
            embed.add_field(name="Experience", value=f'**Milestones**: {result[6]}, **Remaining**: {result[7]}')
            embed.add_field(name="Mythic", value=f'**Trials**: {result[8]}, **Remaining**: {result[9]}')
            embed.add_field(name="Current Wealth", value=f'**GP**: {result[10]}, **Effective Wealth**: {result[19]}', inline=False)
            embed.add_field(name="Current Flux", value=f'**Flux**: {result[14]}')
            linkage = f""
            if result[15] is not None:
                linkage += f"**Tradition**: [{result[15]}]({result[16]})"
            if result[17] is not None:
                if result[15] is not None:
                    linkage += " "
                linkage += f"**Template**: [{result[17]}]({result[18]})"
            if result[15] is not None or result[17] is not None:
                embed.add_field(name=f'Additional Info', value=linkage, inline=False)
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


@gold.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Gold Help", description=f'This is a list of Gold management commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Claim**', value=f'Claim gold that should be received through downtime!', inline=False)
    embed.add_field(name=f'**Buy**', value=f'Buy items, or send your gold out into the open wide world.', inline=False)
    embed.add_field(name=f'**Send**', value=f'Send gold to another player', inline=False)
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
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Nickname = ?", (author, character_name, character_name))
        player_info = cursor.fetchone()
        if player_info is None:
            await ctx.response.send_message(f"{author} does not have a character named {character_name}")
        else:
            gold_info = gold_calculation(player_info[7], player_info[6], player_info[13], player_info[14], player_info[15], amount)
            await Event.gold_change(self, guild_id, author, author_id, character_name, gold_info[3], gold_info[3], amount, reason, 'Gold_Claim')
            cursor.execute(f'SELECT MAX(Transaction_ID) FROM Gold_History Order By Transaction_ID DESC LIMIT 1')
            transaction_id = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + gold_info[3], player_info[14] + gold_info[3], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"Character has increased their wealth by {gold_info[3]} GP using a gold pouch from the shop, transaction_id: {transaction_id[0]}!"
            logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, player_info[13] + gold_info[3], gold_info[3], player_info[14] + gold_info[3], transaction_id[0], None, None, None, None, None, None, None, source)
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
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Nickname = ?", (author, character_name, character_name))
        player_info = cursor.fetchone()
        if player_info[0] is None:
            await ctx.response.send_message(f"{ctx.user.name} does not have a character named {character_name}")
        else:
            expenditure = -abs(expenditure)
            print(player_info[13])
            print(abs(expenditure))
            if player_info[13] >= abs(expenditure):
                market_value_adjusted = market_value + expenditure
                remaining = expenditure + player_info[13]
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
                await Event.gold_change(self, guild_id, author, author_id, character_name, expenditure, market_value_adjusted, market_value_adjusted, reason, 'Gold_Buy')
                cursor.execute(f'SELECT MAX(Transaction_ID) FROM Gold_History Order By Transaction_ID DESC LIMIT 1')
                transaction_id = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + expenditure, player_info[14] + market_value_adjusted, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"Character of {character_name} has spent {expenditure} GP in return for {market_value} GP using the buy command, transaction_id: {transaction_id[0]}!"
                logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, player_info[13] + expenditure, expenditure, player_info[14] + market_value_adjusted, transaction_id[0], None, None, None, None, None, None, None, source)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await ctx.response.send_message(f"{player_info[2]} has spent {abs(expenditure)} gold and has received {market_value_adjusted} in expected value return. Leaving them with {remaining} gold.")
            else:
                await ctx.response.send_message(f"{player_info[2]} does not have enough gold to make this purchase!")
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
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Player_Name = ? AND Nickname = ?", (author, character_from, author, character_from))
        player_info = cursor.fetchone()
        if player_info[0] is None:
            await ctx.response.send_message(f"{author} does not have a character named or nicknamed {character_from}")
        else:
            if player_info[1] - amount < 0:
                await ctx.response.send_message(f"Unlike America, you can't go into debt to resolve your debt. {player_info[1] - amount} leaves you too in debt.")
            else:
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ? and Player_Name != ? or Nickname = ? and Player_Name != ?", (character_to, author, character_to, author))
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
                                await Event.gold_change(self, guild_id, author, author_id, character_from, -abs(amount), expected_value_adjusted, expected_value_adjusted, reason, 'gold send')
                                cursor.execute(f"Select MAX(Transaction_ID) from Gold_History order by Transaction_ID desc limit 1")
                                transaction_id_from = cursor.fetchone()
                                await Event.gold_change(self, guild_id, send_info[0], send_info[1], send_info[2], amount, amount, amount, reason, 'Gold_Buy')
                                cursor.execute(f"Select MAX(Transaction_ID) from Gold_History order by Transaction_ID desc limit 1")
                                transaction_id_to = cursor.fetchone()
                                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                accepted_bio_channel = cursor.fetchone()
                                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + amount, player_info[14] + expected_value_adjusted, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
                                bio_message = await bio_channel.fetch_message(player_info[24])
                                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                source = f"Character of {character_from} has spent {amount} GP in return for {expected_value_adjusted} using the send command, transaction_id: {transaction_id_from[0]}!"
                                logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, player_info[13] + amount, amount, player_info[14] + expected_value_adjusted, transaction_id_from[0], None, None, None, None, None, None, source)
                                logging_thread = guild.get_thread(player_info[25])
                                await logging_thread.send(embed=logging_embed)
                                to_bio_embed = character_embed(send_info[0], send_info[2], send_info[3], send_info[4], send_info[7], send_info[8], send_info[9], send_info[10], send_info[11], send_info[12], send_info[13] + amount, send_info[14] + expected_value_adjusted, send_info[16], send_info[17], send_info[18], send_info[19], send_info[20], send_info[21], send_info[22], send_info[23], send_info[1])
                                to_bio_message = await bio_channel.fetch_message(send_info[24])
                                await to_bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                to_source = f"Character of {character_to} has received {amount} GP in return for services of {expected_value_adjusted} using the send command, transaction_id: {transaction_id_to[0]}!"
                                to_logging_embed = log_embed(send_info[0], author, None, None, None, None, None, None, None, None, send_info[13] + amount, amount, send_info[14] + amount, transaction_id_to, None, None, None, None, None, None, source)
                                to_logging_thread = guild.get_thread(send_info[25])
                                await to_logging_thread.send(embed=logging_embed)
                                await Event.gold_transact(self, transaction_id_from[0], transaction_id_to[0], guild_id)
                                await Event.gold_transact(self, transaction_id_to[0], transaction_id_from[0], guild_id)
                                embed.set_footer(text=f"Transaction Idea was {transaction_id_from[0]}")
                                await msg.edit(embed=embed)
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
    sql = f"""SELECT COUNT(Character_Name) FROM Gold_History where Character_Name = ?"""
    val = [character]
    cursor.execute(sql, val)
    leaders = cursor.fetchone()
    max_page = math.ceil(leaders[0] / 8)
    if current_page >= max_page:
        current_page = max_page
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    low = 0 + (8 * (current_page-1))
    offset = 8
    cursor.execute(f"""Select Transaction_ID, Author_Name, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time from Gold_History WHERE Character_Name = ? LIMIT {low}, {offset}""", (character,))
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
                cursor.execute(f"""Select Transaction_ID, Author_Name, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time from Gold_History WHERE Character_Name = ? LIMIT {low}, {offset}""", (character,))
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
    embed.add_field(name=f'**Reward**', value=f'**GAMEMASTER**: Send session rewards to involved characters!', inline=False)
    embed.add_field(name=f'**Endow**', value=f'**GAMEMASTER**: Endow individual players with rewards!', inline=False)
    await ctx.response.send_message(embed=embed)

@player.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Player Help", description=f'This is a list of Playerside commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Join**', value=f'**PLAYER**: join a session using one your characters!', inline=False)
    embed.add_field(name=f'**Leave**', value=f'**PLAYER**: Leave a session that you have joined!', inline=False)
    embed.add_field(name=f'**Display**', value=f'**ALL**: Display the details of a session.', inline=False)
    await ctx.response.send_message(embed=embed)


@gamemaster.command()
@app_commands.describe(hammer_time="Please use the plain code hammer time provides that appears like </>, ")
async def create(interaction: discord.Interaction, session_name: str, session_range: discord.Role,  player_limit: int, play_location: str, game_link: typing.Optional[str], hammer_time: str, overview: str, description: str):
    """Create a new session."""
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
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
    await Event.create_session(self, author, session_name, session_range_name, session_range_id, play_location, timing, game_link, guild_id, author, overview, description, player_limit)
    sql = f"SELECT Session_ID from Sessions WHERE Session_Name = ? AND GM_Name = ? ORDER BY Session_ID Desc Limit 1"
    val = (session_name, author)
    cursor.execute(sql, val)
    info = cursor.fetchone()
    try:
        embed.set_author(name=f'{author}')
        embed.add_field(name="Session Range", value=f'<@&{session_range_id}>')
        embed.add_field(name="Player Limit", value=f'{player_limit}')
        embed.add_field(name="Date & Time:", value=f'{date} at {hour} which is {arrival}', inline=False)
        embed.add_field(name="Overview:", value=f'{overview}', inline=False)
        embed.add_field(name="Description:", value=f'{description}', inline=False)
        embed.set_footer(text=f'Session ID: {info[0]}.')
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        sessions_channel = cursor.fetchone()
        session_channel = await bot.fetch_channel(sessions_channel[0])
        session_text = f'<@{interaction.user.id}> is running a session.\r\n{session_range.mention}'
        msg = await session_channel.send(content=session_text, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        await interaction.response.send_message(f"Session created! Session ID: {info[0]}.")
        message = msg.id
        thread = await msg.create_thread(name=f"{session_name}", auto_archive_duration=60, reason=f"{description}")
        await Event.create_session_message(self, info[0], message, thread.id, guild_id)
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
        embed.set_footer(text=f'Session ID: {info[0]}.')
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        sessions_channel = cursor.fetchone()
        session_channel = await bot.fetch_channel(sessions_channel[0])
        session_text = f'<@{interaction.user.id}> is running a session.\r\n{session_range.mention}'
        msg = await session_channel.send(content=session_text, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        thread = await msg.create_thread(name=f"Session name: {session_name} Session ID: {info[0]}", auto_archive_duration=60, reason=f"{description}")
        message = msg.id
        await interaction.response.send_message(f"Session created! Session ID: {info[0]}.")
        await Event.create_session_message(self, {info[0]}, message, thread.id, guild_id)
        cursor.close()
        db.close()


@gamemaster.command()
async def edit(interaction: discord.Interaction,  session_id: int, session_range: typing.Optional[discord.Role], session_name: typing.Optional[str], player_limit: typing.Optional[int], play_location: typing.Optional[str], game_link: typing.Optional[str], hammer_time: typing.Optional[str], overview: typing.Optional[str], description: typing.Optional[str]):
    """GM: Edit an Active Session."""
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    sql = f"SELECT Message, Session_Name, Session_Range_ID, Play_Location, Play_Time, game_link, Overview, Description, Player_Limit, Session_Range from Sessions WHERE Session_ID = ? AND GM_Name = ? AND IsActive = ? ORDER BY Created_Time Desc Limit 1"
    val = (session_id, author, 1)
    cursor.execute(sql, val)
    info = cursor.fetchone()
    if info is not None:
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
            description = info[6]
        if description is not None:
            description = description
        else:
            description = info[7]
        await Event.edit_session(self, guild_id, author,  session_id, session_name, session_range_name, session_range_id, play_location, timing, game_link)
        embed.set_author(name=f'{author}')
        embed.add_field(name="Session Range", value=f'<@&{session_range_id}>')
        embed.add_field(name="Play Location", value=f'{play_location}')
        embed.add_field(name="Player Limit", value=f'{player_limit}')
        embed.add_field(name="Date & Time:", value=f'{date} at {hour} which is {arrival}', inline=False)
        embed.add_field(name="Overview:", value=f'{overview}', inline=False)
        embed.add_field(name="Description:", value=f'{description}', inline=False)
        embed.set_footer(text=f'Session ID: {session_id}.')
        print(info)
        session_content = f'<@&{session_range_id}>'
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
    author = interaction.user.name
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    sql = f"SELECT Message, Session_Name from Sessions WHERE Session_ID = ? AND GM_Name = ? AND IsActive = ? ORDER BY Created_Time Desc Limit 1"
    val = (session_id, author, 1)
    cursor.execute(sql, val)
    info = cursor.fetchone()
    if info is not None:
        embed = discord.Embed(title=f"{info[1]}", description=f"This session has been cancelled.", color=discord.Colour.red())
        await Event.delete_session(self, session_id, guild_id, author)
        embed.set_author(name=f'{author}')
        embed.set_footer(text=f'Session ID: {session_id}.')
        msg = await interaction.channel.fetch_message(info[0])
        await msg.edit(embed=embed)
        await interaction.response.send_message(content=f"the following session of {info[1]} located at {msg.jump_url} has been cancelled.")
    if info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id} associated with host {author}")
    cursor.close()
    db.close()


# noinspection PyUnresolvedReferences
@gamemaster.command()
@app_commands.autocomplete(specific_character=character_select_autocompletion)
@app_commands.describe(randomizer="for the purposes of picking a number of randomized players")
@app_commands.describe(specific_character="Picking a specific player's character. You will have to use their CHARACTER Name for this.")
async def accept(interaction: discord.Interaction, session_id: int, player_1: typing.Optional[discord.Member], player_2: typing.Optional[discord.Member], player_3: typing.Optional[discord.Member], player_4: typing.Optional[discord.Member], player_5: typing.Optional[discord.Member], player_6: typing.Optional[discord.Member], specific_character: typing.Optional[str],  randomizer: int = 0):
    """GM: Accept player Sign-ups into your session for participation"""
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Session_Name, Play_location, Play_Time, game_link FROM Sessions WHERE Session_ID = '{session_id}' AND GM_Name = '{author}'")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id} associated with host {author}")
    elif randomizer < 0:
        await interaction.response.send_message(f"Cannot have a negative number of randomized players! {randomizer} is not acceptable!")
    else:
        cursor.execute(f"SELECT count(character_name) FROM Sessions_Signups WHERE Session_ID = {session_id}")
        players = cursor.fetchone()
        print(players)
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
            if randomizer == 0 and player_1 is None and player_2 is None and player_3 is None and player_4 is None and specific_character is None:
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
                        await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_1.name, player_1.id, author, player_info[3])
                        embed.add_field(name=f'**Player**: {player_info[0]}', value=f"has been accepted with Player: <@{player_1.id}>!")
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
                        await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_2.name, player_2.id, author, player_info[3])
                        embed.add_field(name=f'**Player**: {player_info[0]}', value=f"has been accepted with Player: <@{player_2.id}>!")
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
                        await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_3.name, player_3.id, author, player_info[3])
                        embed.add_field(name=f'**Character**: {player_info[0]}', value=f"has been accepted with Player: <@{player_3.id}>!")
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
                        await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0],
                                                  player_info[1], player_info[2], player_4.name, player_4.id, author,
                                                  player_info[3])
                        embed.add_field(name=f'**Character**: {player_info[0]}',
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
                        await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0],
                                                  player_info[1], player_info[2], player_5.name, player_5.id, author,
                                                  player_info[3])
                        embed.add_field(name=f'**Character**: {player_info[0]}',
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
                        await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0],
                                                  player_info[1], player_info[2], player_6.name, player_6.id, author,
                                                  player_info[3])
                        embed.add_field(name=f'**Character**: {player_info[0]}',
                                        value=f"has been accepted with Player: <@{player_6.id}>!")
                if specific_character is not None:
                    sql = f"Select Character_Name, Level, Gold_value, Player_Name, Player_ID, Tier FROM Player_Characters WHERE Character_Name = ?"
                    val = (specific_character,)
                    cursor.execute(sql, val)
                    player_info = cursor.fetchone()
                    if player_info is not None and player_info[3] != player_1.id and player_info[3] != player_2.id and player_info[3] != player_3.id and player_info[3] != player_4.id and player_info[3] != player_5.id and player_info[3] != player_6.id:
                        await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_info[3], player_info[4], author, player_info[5])
                        embed.add_field(name=f'**Character**: {player_info[0]}', value=f"has been accepted with player: @{player_info[4]}!")
                        mentions += f'<@{player_info[4]}> '
                if randomizer > 0:
                    characters_total = players[0]
                    randomizer = players[0] if randomizer > characters_total else randomizer
                    for x in range(randomizer):
                        random_number = random.randint(1, characters_total)
                        random_number -= 1
                        characters_total -= 1
                        cursor.execute(f"Select Character_Name, Level, Effective_Wealth, Player_Name, Player_ID, Tier FROM Sessions_Signups WHERE Session_ID = '{session_id}' LIMIT 1 OFFSET {random_number}")
                        player_info = cursor.fetchone()
                        await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_info[3], player_info[4], author, player_info[5])
                        embed.add_field(name=f'**Character**: {player_info[0]}', value=f"has been accepted with player: @{player_info[3]}!")
                        mentions += f'<@{player_info[4]}> '

                mentions += f"have been accepted!"
                embed.set_footer(text=f"Session ID: {session_id}")
                await interaction.response.send_message(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))

        else:
            if session_info[3] is None:
                embed = discord.Embed(title=f"{session_info[0]} signups failed!",
                                      description=f"there are no players signed up for this session",
                                      color=discord.Colour.green())
            else:
                embed = discord.Embed(title=f"{session_info[0]} signups failed!", url=f'{session_info[3]}', description=f"there are no players signed up for this session", color=discord.Colour.green())
            embed.set_author(name=f'{author}')
            await interaction.response.send_message(embed=embed)
    cursor.close()
    db.close()


@gamemaster.command()
async def remove(interaction: discord.Interaction, session_id: int, player: discord.Member):
    """GM: Kick a player out of your session"""
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Session_Name, Play_location, Play_Time, game_link FROM Sessions WHERE Session_ID = '{session_id}'")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id}")
    else:
        cursor.execute(f"SELECT Player_Name, Character_Name FROM Sessions_Participants WHERE Session_ID = '{session_id}' and Player_Name = '{player.name}'")
        player_info = cursor.fetchone()
        if player_info is None:
            await interaction.response.send_message(f"{player.name} does not appear to be participating in the session of {session_info[0]} with session ID: {session_id}")
        else:
            player_name = player.name
            character_name = player_info[1]
            await Event.remove_player(self, guild_id, session_id, player_name, character_name, author)
            await interaction.response.send_message(f"{player.name} has been removed from Session {session_info[0]} with ID: {session_id}")
    cursor.close()
    db.close()


@gamemaster.command()
@app_commands.describe(reward_all="A reward for each individual member of the party")
@app_commands.describe(party_reward="A reward for the party to divy up amongst themselves, or not. Link a google doc if reward exceeds character limit.")
async def reward(interaction: discord.Interaction, session_id: int, gold: float, easy: int = 0, medium: int = 0, hard: int = 0, deadly: int = 0, milestones: int = 0, flux: int = 10, trials: int = 0, reward_all: str = None, party_reward: str = None):
    """GM: Reward Players for Participating in your session."""
    if gold < 0 or easy < 0 or medium < 0 or hard < 0 or deadly < 0 or milestones < 0 or flux < 0 or trials < 0:
        await interaction.response.send_message(f"Your players might not judge you out loud for trying to give them a negative award, but I do...")
    elif gold == 0 and easy == 0 and medium == 0 and hard == 0 and deadly == 0 and milestones == 0 and flux == 0 and trials == 0 and reward_all is None and party_reward is None:
        await interaction.response.send_message(f"Your players have been rewarded wi-- wait a minute, what the fuck? No Rewards?! No! At least give them a silver or a milestone!")
    guild_id = interaction.guild_id
    guild = interaction.guild
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT GM_Name, Session_Name, Session_Range, Play_Location, Play_Time, Message, Session_Thread FROM Sessions WHERE Session_ID = {session_id} LIMIT 1""")
    session_info = cursor.fetchone()
    if session_info is not None:
        mentions = f"Session Rewards for {session_info[1]}: "
        cursor.execute(f"""SELECT Player_Name, Player_ID, Character_Name, Level, Tier, Effective_Wealth  FROM Sessions_Participants WHERE Session_ID = {session_id}""")
        session_players = cursor.fetchall()
        if session_players == []:
            await interaction.response.send_message(f"No players could be found participating in session with {session_id} can be found!")
        elif session_players is not None:
            await interaction.response.defer(thinking=True)
            if party_reward is not None:
                thread = guild.get_thread(session_info[6])
                party_reward_embed = discord.Embed(title="Party Reward", description=f"Party Reward for {session_info[1]}", color=discord.Color.blue())
                party_reward_embed.set_author(name=f'{session_info[0]}')
                party_reward_embed.add_field(name="Reward Info", value=f'{party_reward}', inline=False)
                await thread.send(f"{party_reward_embed}")
            embed = discord.Embed(title=f"{session_info[1]}", description=f"Reward Display", color=discord.Colour.green())
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
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name, character_name))
                player_info = cursor.fetchone()
                flux_total = player_info[16] + flux  #Setting the Flux
                level_info = level_calculation(guild_id, player_info[9], rewarded)
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
                else:
                    response = response
                if trials != 0:
                    response += f" {trials} Mythic Trials!"
                else:
                    response = response
                if player[4] != mythic_info[0]:
                    response += f" and has reached a new mythic tier of {mythic_info[0]}!"
                else:
                    response = response
                if flux != 0:
                    response += f" {flux} flux!"
                else:
                    response = response
                embed.add_field(name=f'**Character**: {player[2]}', value=response)
                await Event.session_rewards(self, author, guild_id, player[2], level_info[0], player_info[9] + rewarded, level_info[1], flux_total, mythic_info[0], player_info[11] + trials, mythic_info[1], session_id)
                await Event.gold_change(self, guild_id, player[0], player[1], player[2], gold_info[3], gold_info[3], gold, 'Session Reward', 'Session Reward')
                await Event.session_log_player(self, guild_id, session_info[0], session_info[1], session_id, player_info[0], player_info[1], player_info[2], player[3], player[4], player[5], rewarded, trials, gold_info[3])
                cursor.execute(f'SELECT MAX(Transaction_ID) FROM Gold_History Order By Transaction_ID DESC LIMIT 1')
                transaction_id = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[2], player_info[3], player_info[4], level_info[0], mythic_info[0], player_info[9] + rewarded, level_info[1], player_info[11] + trials, mythic_info[1], player_info[13] + gold_info[3], player_info[14] + gold_info[3], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[1])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"Session Reward with Session ID: {session_id} and transaction ID: {transaction_id[0]}"
                logging_embed = log_embed(player_info[0], author, level_info[0], rewarded, player_info[9] + rewarded, level_info[1], mythic_info[0], trials, player_info[11] + trials, mythic_info[1], player_info[13] + gold_info[3], gold_info[3], player_info[14] + gold_info[3], transaction_id[0], flux_total, flux, None, None, None, None, reward_all, source)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
            await Event.session_log(self, guild_id, session_id, gold, flux, easy, medium, hard, deadly, trials, reward_all, party_reward)
            await interaction.followup.send(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            cursor.close()
            db.close()
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
    interaction.response.defer(thinking=True)
    if session_info is not None:
        embed = discord.Embed(title=f"{session_info[1]}", description=f"Personal Reward Display", color=discord.Colour.green())
        embed.set_footer(text=f"Session ID is {session_id}")
        if player_1 is not None and player_1_reward is not None:
            cursor.execute(f"""SELECT True_Character_Name, Thread_ID FROM Sessions_Archive WHERE Player_Name = {player_1.name} AND Session_ID = {session_id}""")
            player_info = cursor.fetchone()
            response = f"<@{player_1.id}> "
            if player_info is not None:
                await Event.session_endowment(self, author, guild_id, session_id, player_1.name, player_1_reward)
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_1_reward, source)
                logging_thread = guild.get_thread(player_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_1_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_1.name}', value=response, inline=False)
        if player_2 is not None and player_2_reward is not None:
            cursor.execute(f"""SELECT True_Character_Name, Thread_ID FROM Sessions_Archive WHERE Player_Name = {player_2.name} AND Session_ID = {session_id}""")
            player_info = cursor.fetchone()
            response = f"<@{player_2.id}> "
            if player_info is not None:
                await Event.session_endowment(self, author, guild_id, session_id, player_2.name, player_2_reward)
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_2_reward, source)
                logging_thread = guild.get_thread(player_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_2_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_2.name}', value=response, inline=False)
        if player_3 is not None and player_3_reward is not None:
            cursor.execute(f"""SELECT True_Character_Name, Thread_ID FROM Sessions_Archive WHERE Player_Name = {player_3.name} AND Session_ID = {session_id}""")
            player_info = cursor.fetchone()
            response = f"<@{player_3.id}> "
            if player_info is not None:
                await Event.session_endowment(self, author, guild_id, session_id, player_3.name, player_3_reward)
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_3_reward, source)
                logging_thread = guild.get_thread(player_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_3_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_3.name}', value=response, inline=False)
        if player_4 is not None and player_4_reward is not None:
            cursor.execute(f"""SELECT True_Character_Name, Thread_ID FROM Sessions_Archive WHERE Player_Name = {player_4.name} AND Session_ID = {session_id}""")
            player_info = cursor.fetchone()
            response = f"<@{player_4.id}> "
            if player_info is not None:
                await Event.session_endowment(self, author, guild_id, session_id, player_4.name, player_4_reward)
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_4_reward, source)
                logging_thread = guild.get_thread(player_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_4_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_4.name}', value=response, inline=False)
        if player_5 is not None and player_5_reward is not None:
            cursor.execute(f"""SELECT True_Character_Name, Thread_ID FROM Sessions_Archive WHERE Player_Name = {player_5.name} AND Session_ID = {session_id}""")
            player_info = cursor.fetchone()
            response = f"<@{player_5.id}> "
            if player_info is not None:
                await Event.session_endowment(self, author, guild_id, session_id, player_5.name, player_5_reward)
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_5_reward, source)
                logging_thread = guild.get_thread(player_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_5_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_5.name}', value=response, inline=False)
        if player_6 is not None and player_6_reward is not None:
            cursor.execute(f"""SELECT True_Character_Name, Thread_ID FROM Sessions_Archive WHERE Player_Name = {player_5.name} AND Session_ID = {session_id}""")
            player_info = cursor.fetchone()
            response = f"<@{player_6.id}> "
            if player_info is not None:
                await Event.session_endowment(self, author, guild_id, session_id, player_6.name, player_6_reward)
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_6_reward, source)
                logging_thread = guild.get_thread(player_info[1])
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
@app_commands.describe(rewards="Accept only part of a session reward!")
@app_commands.choices(rewards=[discord.app_commands.Choice(name='all!', value=1), discord.app_commands.Choice(name='milestones only!', value=2),discord.app_commands.Choice(name='gold only!', value=3)])
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def claim(interaction: discord.Interaction, session_id: int, character_name: str, rewards: discord.app_commands.Choice[int] = 1):
    guild_id = interaction.guild_id
    guild = interaction.guild
    author = interaction.user.name
    author_id = interaction.user.id
    user = interaction.user
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT GM_Name, Session_Name, Session_Range, Play_location, Play_Time, Gold, Level, Flux, Easy, Medium, Hard, Deadly, Milestones, Trials, Message, Session_Range, Alt_Reward_All, Alt_Reward_Party, Session_Thread FROM Sessions_Archive WHERE Session_ID = '{session_id}' AND GM_Name = '{author}' limit 1")
    session_info = cursor.fetchone()
    if session_info is not None:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters WHERE Player_Name = ? AND Character_Name = ? OR Nickname =?", (author, character_name, character_name))
        validate_recipient = cursor.fetchone()
        if validate_recipient is not None:
            cursor.execute(f"SELECT Session_Name, Character_Name, Player_Name, Gold, Level, Flux, Easy, Medium, Hard, Deadly, Milestones, Trials, Received_Milestones, Received_Gold  FROM Sessions_Archive WHERE Session_ID = ? AND GM_Name = ? AND Player_Name = ?", (session_id, author, author))
            previous_rewards = cursor.fetchone()
            if previous_rewards is not None:
                print(previous_rewards[1])
                print(character_name)
                if previous_rewards[1] == character_name:
                    await interaction.response.send_message(
                        f"you cannot claim for the same character of {character_name} when you already have claimed for them!!")
                else:
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    accepted_bio_channel = cursor.fetchone()
                    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters WHERE Character_Name = ?", (previous_rewards[1],))
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
                                level_information = level_calculation(guild_id, previous_recipient[9], -abs(previous_rewards[12]))
                                mythic_information = mythic_calculation(guild_id, level_information[0], previous_recipient[11], -abs(previous_rewards[11]))
                                gold_information = gold_calculation(level_information[0], previous_recipient[6], previous_recipient[13], previous_recipient[14], previous_recipient[15], -abs(previous_rewards[3]))
                                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID FROM Player_Characters WHERE Character_Name = ?",(previous_rewards[1],))
                                new_information = cursor.fetchone()
                                await Event.session_rewards(self, previous_recipient[0], guild_id, previous_recipient[3], level_information[0], previous_recipient[9] + -abs(previous_rewards[11]),level_information[1], previous_recipient[16] - previous_rewards[5], mythic_information[0], previous_recipient[8] + -abs(previous_rewards[11]), mythic_information[1], session_id)
                                await Event.gold_change(self, guild_id, previous_recipient[0], previous_recipient[1], previous_recipient[3], -abs(previous_rewards[13]), -abs(previous_rewards[13]), -abs(previous_rewards[3]), 'Session Removed Old Claim', 'Session Claim')
                                cursor.execute(f"Select MAX(transaction_id) from Gold_History")
                                transaction_id = cursor.fetchone()
                                await Event.session_unreward(self, author, guild_id, previous_recipient[3], session_id)
                                bio_embed = character_embed(previous_recipient[0], previous_recipient[2], previous_recipient[4], previous_recipient[5], level_information[0], mythic_information[0], previous_recipient[9] + -abs(previous_rewards[11]), level_information[1], previous_recipient[11] - session_info[13], mythic_information[1], gold_information[0], gold_information[1], previous_recipient[16] - previous_rewards[5], previous_recipient[17], previous_recipient[18], previous_recipient[19], previous_recipient[20], previous_recipient[21], previous_recipient[22], previous_recipient[23], previous_recipient[1])
                                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                bio_message = await bio_channel.fetch_message(previous_recipient[24])
                                await bio_message.edit(content=bio_embed[1],embed=bio_embed[0])
                                source = f"Session {session_info[1]} with ID: {session_id} no longer claimed"
                                logging_embed = log_embed(previous_recipient[2], author, level_information[0], -abs(previous_rewards[12]), previous_recipient[9] + -abs(previous_rewards[11]), level_information[1], mythic_information[0], session_info[13], previous_recipient[10] - session_info[13], mythic_information[1], previous_recipient[14] - previous_rewards[13], -abs(previous_rewards[13]), previous_recipient[15] - previous_rewards[13], transaction_id[0], previous_recipient[16] - previous_rewards[5],  -abs(previous_rewards[5]), None, None, None, None, None, source)
                                logging_thread = guild.get_thread(previous_recipient[26])
                                await logging_thread.send(embed=logging_embed)
                                cursor.execute(f"""SELECT Easy, Medium, Hard, Deadly from AA_Milestones WHERE level = {validate_recipient[6]}""")
                                job_info = cursor.fetchone()
                                easy_jobs = session_info[8] * job_info[0]
                                medium_jobs = session_info[9] * job_info[1]
                                hard_jobs = session_info[10] * job_info[2]
                                deadly_jobs = session_info[11] * job_info[3]
                                milestones_value = session_info[12]
                                rewarded = easy_jobs + medium_jobs + hard_jobs + deadly_jobs + milestones_value
                                new_milestones = validate_recipient[8] + rewarded
                                new_level_information = level_calculation(guild_id, new_milestones, rewarded)
                                new_mythic_information = mythic_calculation(guild_id, new_level_information[0], validate_recipient[10], session_info[13])
                                new_gold_information = gold_calculation(new_level_information[0], validate_recipient[5], validate_recipient[12], validate_recipient[13], validate_recipient[14], session_info[5])
                                await Event.session_rewards(self, validate_recipient[0], guild_id, character_name, new_level_information[0], validate_recipient[8] + rewarded, new_level_information[1], validate_recipient[15] + previous_rewards[5], new_mythic_information[0], validate_recipient[7] + previous_rewards[11], new_mythic_information[1], session_id)
                                await Event.gold_change(self, guild_id, validate_recipient[0], validate_recipient[1], character_name, new_gold_information[3], new_gold_information[3], previous_rewards[3], 'Session Added new Claim', 'Session Claim')
                                cursor.execute(f"Select MAX(transaction_id) from Gold_History")
                                transaction_id = cursor.fetchone
                                await Event.session_log_player(self, guild_id, session_info[0], session_info[1], session_id, validate_recipient[0], validate_recipient[1], validate_recipient[2], validate_recipient[6], validate_recipient[7], validate_recipient[13], rewarded, previous_rewards[11], gold_information[3])
                                bio_embed = character_embed(validate_recipient[0], validate_recipient[2], validate_recipient[3], validate_recipient[4], new_level_information[0], new_mythic_information[0],new_milestones, new_level_information[1], validate_recipient[10] + session_info[13], new_mythic_information[1],new_gold_information[0], new_gold_information[1],validate_recipient[15] + session_info[7], validate_recipient[16],validate_recipient[17], validate_recipient[18], validate_recipient[19], validate_recipient[20], validate_recipient[21], validate_recipient[22], validate_recipient[1])
                                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                bio_message = await bio_channel.fetch_message(validate_recipient[23])
                                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                source = f"Session {session_info[1]} with ID: {session_id} claimed"
                                logging_embed = log_embed(validate_recipient[2], author, new_level_information[0], rewarded, new_milestones, new_level_information[1], new_mythic_information[0], session_info[13], validate_recipient[10] + session_info[13], new_mythic_information[1], new_gold_information[0], new_gold_information[3], new_gold_information[1], transaction_id[0], validate_recipient[15] + session_info[7], session_info[7], None, None, None, None, None, source)
                                logging_thread = guild.get_thread(validate_recipient[25])
                                await logging_thread.send(embed=logging_embed)
                                await msg.clear_reactions()
                                cursor.close()
                                db.close()
            else:
                cursor.execute(
                    f"""SELECT Easy, Medium, Hard, Deadly from AA_Milestones WHERE level = {validate_recipient[6]}""")
                job_info = cursor.fetchone()
                easy_jobs = session_info[8] * job_info[0]
                medium_jobs = session_info[9] * job_info[1]
                hard_jobs = session_info[10] * job_info[2]
                deadly_jobs = session_info[11] * job_info[3]
                milestones_value = session_info[12]
                rewarded = easy_jobs + medium_jobs + hard_jobs + deadly_jobs + milestones_value
                new_milestones = validate_recipient[8] + rewarded
                level_information = level_calculation(guild_id, validate_recipient[8], rewarded)
                mythic_information = mythic_calculation(guild_id, level_information[0], validate_recipient[10], session_info[13])
                gold_information = gold_calculation(level_information[0], validate_recipient[5], validate_recipient[12], validate_recipient[13], validate_recipient[14], session_info[5])
                await Event.session_rewards(self, validate_recipient[0], guild_id, character_name, level_information[0], validate_recipient[8] + rewarded, level_information[1], validate_recipient[15] + session_info[7], mythic_information[0], validate_recipient[7] + session_info[13], mythic_information[1], session_id)
                await Event.gold_change(self, guild_id, validate_recipient[0], validate_recipient[1], character_name, gold_information[3], gold_information[3], session_info[7], 'Session Added new Claim', 'Session Claim')
                cursor.execute(f"Select MAX(transaction_id) from Gold_History")
                gold_transaction_id = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.close()
                db.close()
                await Event.session_log_player(self, guild_id, session_info[0], session_info[1], session_id, validate_recipient[0], validate_recipient[1], validate_recipient[2], validate_recipient[6], validate_recipient[7], validate_recipient[13], rewarded, previous_rewards[11], gold_information[3])
                bio_embed = character_embed(validate_recipient[0], validate_recipient[2], validate_recipient[3], validate_recipient[4], level_information[0], mythic_information[0], new_milestones, level_information[1], validate_recipient[10] + session_info[13], mythic_information[1], gold_information[0], gold_information[1], validate_recipient[15] + session_info[7], validate_recipient[16], validate_recipient[17], validate_recipient[18], validate_recipient[19], validate_recipient[20], validate_recipient[21], validate_recipient[22], validate_recipient[1])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(validate_recipient[23])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                session_name = session_info[1]
                embed_log = log_embed(validate_recipient[2], author, level_information[0], rewarded, new_milestones, level_information[1], mythic_information[0], session_info[13], validate_recipient[10] + session_info[13], mythic_information[1], gold_information[0], gold_information[3], gold_information[1], gold_transaction_id[0], validate_recipient[15] + session_info[7], session_info[7], None, None, None, None, f"Session {session_name} with ID: {session_id} claimed")
                logging_thread = guild.get_thread(validate_recipient[25])
                await logging_thread.send(embed=embed_log)
                await interaction.response.send_message(f"Rewards have been claimed for {character_name}!")
        else:
            await interaction.response.send_message(f"{character_name} is not a valid Character name or Nickname.")
    else:
        await interaction.response.send_message(f"No active session with {session_id} can be found!")

@player.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def join(interaction: discord.Interaction, session_id: int, character_name: str):
    """PLAYER: Offer your Participation in a session."""
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    user = interaction.user
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Session_Name, Play_location, Play_Time, game_link, Session_Range_ID, Session_Range FROM Sessions WHERE Session_ID = '{session_id}'")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.response.send_message(f"No active session with Session ID: {session_id} can be found!")
    else:
        role = interaction.guild.get_role(session_info[4])
        if role in user.roles:
            sql = f"""Select Character_Name, Level, Gold_Value, Tier from Player_Characters where Player_Name = ? and Character_Name = ? OR Nickname = ?"""
            val = (author, character_name, character_name)
            cursor.execute(sql, val)
            character_info = cursor.fetchone()
            if character_info is None:
                await interaction.response.send_message(f"Falsehoods! the Character of {character_name} either doesn't exist or belong to {author}!")
            if character_info is not None:
                cursor.execute(f"SELECT Level, Role_Name from Level_Range WHERE Role_ID = {session_info[4]}")
                level_range_info = cursor.fetchone()
                if level_range_info is None:
                    cursor.execute(f"""Select Character_Name from Sessions_Participants where Player_name = '{author}' and Session_ID = {session_id}""")
                    participation = cursor.fetchone()
                    cursor.execute(f"""Select Character_Name from Sessions_Signups where Player_name = '{author}' AND Session_ID = {session_id}""")
                    signups = cursor.fetchone()
                    if participation is None and signups is None:
                        await Event.session_join(self, guild_id, session_info[0], session_id, author, author_id, character_info[0], character_info[1], character_info[2], character_info[3])
                        sql = f"""Select Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link from Player_characters WHERE Character_Name = ? OR Nickname = ?"""
                        val = (character_name, character_name)
                        cursor.execute(sql, val)
                        result = cursor.fetchone()
                        if result is None:
                            await interaction.response.send_message(f"{character_name} is not a valid Character name or Nickname.")
                            cursor.close()
                            db.close()
                            return
                        else:
                            color = result[11]
                            int_color = int(color[1:], 16)
                            embed = discord.Embed(title="Mythweavers Sheet", url=f'{result[12]}', description=f"Other Names: {result[2]}", color=int_color)
                            embed.set_author(name=f'{result[0]} would like to participate')
                            embed.set_thumbnail(url=f'{result[13]}')
                            embed.add_field(name="Information", value=f'**Level**: {result[4]}, **Mythic Tier**: {result[5]}', inline=False)
                            embed.add_field(name="Experience", value=f'**Milestones**: {result[6]}, **Remaining**: {result[7]}')
                            embed.add_field(name="Mythic", value=f'**Trials**: {result[8]}, **Remaining**: {result[9]}',
                                            inline=True)
                            embed.add_field(name="Current Wealth", value=f'**GP**: {result[10]}', inline=False)
                            embed.add_field(name="Current Flux", value=f'**Flux**: {result[14]}')
                            linkage = f""
                            if result[15] is not None:
                                linkage += f"**Tradition**: [{result[15]}]({result[16]})"
                            if result[17] is not None:
                                if result[15] is not None:
                                    linkage += " "
                                linkage += f"**Template**: [{result[17]}]({result[18]})"
                            if result[15] is not None or result[17] is not None:
                                embed.add_field(name=f'Additional Info', value=linkage, inline=False)
                            embed.set_footer(text=f'{result[3]}')
                            await interaction.response.send_message(embed=embed)
                    elif participation is not None:
                        await interaction.response.send_message(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
                    elif signups is not None:
                        await interaction.response.send_message(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
                else:
                    cursor.execute(f"SELECT level, Role_Name from Level_Range WHERE Role_ID = {session_info[4]} AND Level = {character_info[1]}")
                    new_level_range_info = cursor.fetchone()
                    if new_level_range_info is None:
                        await interaction.response.send_message(f"{character_info[0]} is level {character_info[1]} which is not inside the level range of {level_range_info[1]}!", ephemeral=True)
                    else:
                        cursor.execute(f"""Select Character_Name from Sessions_Participants where Player_name = '{author}' and Session_ID = {session_id}""")
                        participation = cursor.fetchone()
                        cursor.execute(f"""Select Character_Name from Sessions_Signups where Player_name = '{author}' and Session_ID = {session_id}""")
                        signups = cursor.fetchone()
                        if participation is None and signups is None:
                            await Event.session_join(self, guild_id, session_info[0], session_id, author, author_id, character_info[0], character_info[1], character_info[2], character_info[3])
                            sql = f"""Select True_Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link from Player_characters WHERE Character_Name = ? OR Nickname = ?"""
                            val = (character_name, character_name)
                            cursor.execute(sql, val)
                            result = cursor.fetchone()
                            if result is None:
                                await interaction.response.send_message(f"{character_name} is not a valid Character Name or Nickname.")
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
                                embed.add_field(name="Information",
                                                value=f'**Level**: {result[4]}, **Mythic Tier**: {result[5]}',
                                                inline=False)
                                embed.add_field(name="Experience",
                                                value=f'**Milestones**: {result[6]}, **Remaining**: {result[7]}',
                                                inline=True)
                                embed.add_field(name="Mythic",
                                                value=f'**Trials**: {result[8]}, **Remaining**: {result[9]}',
                                                inline=True)
                                embed.add_field(name="Current Wealth", value=f'**GP**: {result[10]}', inline=False)
                                embed.add_field(name="Current Flux", value=f'**Flux**: {result[14]}')
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
                                embed.set_footer(text=f'{result[3]}')
                                await interaction.response.send_message(embed=embed)
                        elif participation is not None:
                            await interaction.response.send_message(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
                        elif signups is not None:
                            await interaction.response.send_message(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
        else:
            await interaction.response.send_message(f"User does not have role: {session_info[5]}! If you wish to join, obtain this role! Ensure you have a character in the correct level bracket.", ephemeral=True)


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
        cursor.execute(f"""Select Character_Name, Level, Effective_Wealth from Sessions_Signups where Player_Name = '{author}'""")
        character_info = cursor.fetchone()
        if character_info is None:
            cursor.execute(f"""Select Character_Name, Level, Effective_Wealth from Sessions_Participants where Player_Name = '{author}'""")
            character_info = cursor.fetchone()
            if character_info is None:
                await interaction.response.send_message(f"{author} has no active character in this session!")
            if character_info is not None:
                true_name = character_info[0]
                await Event.session_leave(self, guild_id, session_id, author, true_name)
                await interaction.response.send_message(f"{author}'s {true_name} has decided against participating in the session of '{session_info[0]}!'")
        elif character_info is not None:
            true_name = character_info[0]
            await Event.session_leave(self, guild_id, session_id, author, true_name)
            await interaction.response.send_message(f"{author}'s {true_name} has decided against participating in the session of '{session_info[0]}!'")


@player.command()
@app_commands.describe(group="Displaying All Participants & Signups, Active Participants Only, or Potential Sign-ups Only for a session")
@app_commands.choices(group=[discord.app_commands.Choice(name='All', value=1), discord.app_commands.Choice(name='Participants', value=2), discord.app_commands.Choice(name='Sign-ups', value=3)])
async def display(ctx: commands.Context, session_id: int, group: discord.app_commands.Choice[int] = 1):
    """ALL: THIS COMMAND DISPLAYS SESSION INFORMATION"""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
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
            cursor.execute(f"SELECT Gold, Flux, Easy, Medium, Hard, Deadly, Milestones, Trials FROM Sessions WHERE Session_ID = {session_id}")
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
    await interaction.response.send_message(f"pong")


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




@bot.event
async def on_disconnect():
    print("Bot is disconnecting.")

bot.run(os.getenv('DISCORD_TOKEN'))
