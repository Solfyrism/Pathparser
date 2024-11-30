import math
import typing
import discord
import bcrypt
import numpy as np
import pycountry
import pycountry_convert
from discord.ext import commands
from discord import app_commands
from typing import List, Optional
import aiosqlite
import pytz
import datetime
from zoneinfo import ZoneInfo, available_timezones
import logging
from dateutil import parser
import os
from matplotlib import pyplot as plt
from pywaclient.api import BoromirApiClient as WaClient
from unidecode import unidecode

import shared_functions
from commands import gamemaster_commands
#autocompletes functions for kingdom
async def alignment_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment LIKE ? Limit 20",
            (f"%{current}%",))
        alignment_list = await cursor.fetchall()
        for alignment in alignment_list:
            if current in alignment[0]:
                (alignment_name, economy, loyalty, stability) = alignment
                data.append(app_commands.Choice(
                    name=f"{alignment_name} Economy: {economy}, Loyalty: {loyalty}, Stability: {stability}",
                    value=alignment_name))
    return data


async def blueprint_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Building FROM Buildings_Blueprints WHERE Building LIKE ? Limit 20",
            (f"%{current}%",))
        blueprint_list = await cursor.fetchall()
        for blueprint in blueprint_list:
            if current in blueprint[0]:
                data.append(app_commands.Choice(name=blueprint[0], value=blueprint[0]))
    return data


async def government_autocompletion(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Government from AA_Government WHERE Government LIKE ? Limit 20",
            (f"%{current}%",))
        government_list = await cursor.fetchall()
        for government in government_list:
            if current in government[0]:
                data.append(app_commands.Choice(name=government[0], value=government[0]))

    return data


async def hex_terrain_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Hex_Terrain from AA_Hex_Terrains WHERE Hex_Terrain LIKE ? Limit 20",
            (f"%{current}%",))
        hex_list = await cursor.fetchall()
        for hexes in hex_list:
            if current in hexes[0]:
                data.append(app_commands.Choice(name=hexes[0], value=hexes[0]))

    return data


async def hex_improvement_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Improvement FROM Hexes_Improvements WHERE Improvement LIKE ? Limit 20",
            (f"%{current}%",))
        improvement_list = await cursor.fetchall()
        for improvement in improvement_list:
            if current in improvement[0]:
                data.append(app_commands.Choice(name=improvement[0], value=improvement[0]))
    return data


async def leadership_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Title from AA_Leadership_Roles WHERE Effect LIKE ? Limit 20",
            (f"%{current}%",))
        title_list = await cursor.fetchall()
        for title in title_list:
            if current in title[0]:
                data.append(app_commands.Choice(name=title[0], value=title[0]))
    return data


async def kingdom_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT kingdom from Kingdoms WHERE Kingdom LIKE ? Limit 20",
            (f"%{current}%",))
        kingdom_list = await cursor.fetchall()
        for kingdom in kingdom_list:
            if current in kingdom[0]:
                data.append(app_commands.Choice(name=kingdom[0], value=kingdom[0]))

    return data


async def settlement_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[
    app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Settlement FROM settlements WHERE Settlement LIKE ? Limit 20",
            (f"%{current}%",))
        settlement_list = await cursor.fetchall()
        for settlement in settlement_list:
            if current in settlement[0]:
                data.append(app_commands.Choice(name=settlement[0], value=settlement[0]))
    return data



#Purpose FUnctions
def encrypt_password(plain_password: str):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed_password

def validate_password(plain_password, stored_hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), stored_hashed_password)


async def create_a_kingdom(
        guild_id: int,
        author: str,
        kingdom: str,
        password: str,
        government: str,
        alignment: str) -> str:
    try:
        hashed_password = encrypt_password(password)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("""select Kingdom FROM Kingdoms where Kingdom = '{kingdom}'""")
            kingdom_presence = await cursor.fetchone()
            if kingdom_presence is not None:
                return "The kingdom already exists."
            await cursor.execute(
                """select Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = '{alignment}'""")
            alignment_type = await cursor.fetchone()
            if alignment_type is None:
                return "Invalid alignment."
            await cursor.execute("""select Government FROM AA_Government WHERE Government = '{government}'""")
            government_type = await cursor.fetchone()
            if government_type is None:
                return "Invalid government type."
            if alignment_type is not None and kingdom_presence is None and government_type is not None:
                (economy, loyalty, stability) = alignment_type
                await cursor.execute("""
                INSERT INTO Kingdoms (Kingdom, Password, Government, Alignment, Economy, Loyalty, Stability, 
                Fame, Unrest, Consumption, Size, Population, Control_DC, Build_Points, Stabilization_Points) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 0, 0, 0)
                """, (kingdom, hashed_password, government, alignment, economy, loyalty, stability))
                await cursor.execute(
                    """Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)""",
                    (author, datetime.datetime.now(), "Kingdoms", "Create", f"Created the kingdom of {kingdom}"))
                await db.commit()
                return f"Congratulations, you have created the kingdom of {kingdom}."

    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error creating a kingdom: {e}")
        return "An error occurred while creating a kingdom."


class KingdomCommands(commands.Cog, name='Kingdom'):
    def __init__(self, bot):
        self.bot = bot

    kingdom_group = discord.app_commands.Group(
        name='kingdom',
        description='Commands related to playing'
    )

    @kingdom_group.command()
    @app_commands.autocomplete(government=government_autocompletion)
    async def create(self, interaction: discord.Interaction, kingdom: str, password: str, government: str,
                     alignment: str):
        """This creates allows a player to create a new kingdom"""
        await interaction.response.defer(thinking=True)
        try:

            kingdom_create = await create_a_kingdom(
                guild_id=interaction.guild_id,
                author=interaction.user.name,
                kingdom=kingdom,
                alignment=alignment,
                government=government,
                password=password)
            await interaction.followup.send(content=kingdom_create)
        except Exception as e:
            logging.exception(f"Error creating a kingdom: {e}")
            await interaction.followup.send(content="An error occurred while creating a kingdom.")

    @kingdom_group.command()
    async def destroy(self, interaction: discord.Interaction, kingdom: str, password: str):
        """This is a player command to remove a kingdom THEY OWN from play"""
        kingdom = str.replace(str.title(kingdom), ";", "")
        password = str.replace(password, ";", "")
        guild_id = interaction.guild_id
        author = interaction.user.name
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute("""select Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
        result = cursor.fetchone()
        cursor.close()
        db.close()
        if result is None:
            status = f"the kingdom which you have elected to make a war crime out of couldn't be found."
            await interaction.response.send_message(content=status)
        if result is not None and result[1] == password:
            status = f"The Kingdom of {kingdom} can no longer be found, whether it be settlements, political figures, or Buildings"
            await Event.destroy_kingdom(self, kingdom, guild_id, author)
            await interaction.response.send_message(content=status)
        else:
            status = f"You have entered an invalid password for this kingdom."
            await interaction.response.send_message(content=status)

    @kingdom_group.command()
    async def modify(self, interaction: discord.Interaction, old_kingdom: str, new_kingdom: str, old_password: str,
                     new_password: str, new_government: str, new_alignment: str):
        """This is a player command to modify a kingdom THEY OWN."""
        new_kingdom = str.replace(str.title(new_kingdom), ";", "")
        old_kingdom = str.replace(str.title(old_kingdom), ";", "")
        new_government = str.replace(str.title(new_government), ";", "")
        new_alignment = str.replace(str.upper(new_alignment), ";", "")
        new_password = str.replace(new_password, ";", "")
        old_password = str.replace(old_password, ";", "")
        guild_id = interaction.guild_id
        author = interaction.user.name
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute("""select Kingdom, Password FROM Kingdoms where Kingdom = '{old_kingdom}'""",
                       {'Kingdom': old_kingdom})
        result = cursor.fetchone()
        cursor.execute(
            """select Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = '{new_alignment}'""",
            {'Alignment': new_alignment})
        alignment_validity = cursor.fetchone()
        cursor.execute("""select Government FROM AA_Government WHERE Government = '{new_government}'""",
                       {'Government': new_government})
        government_validity = cursor.fetchone()
        cursor.close()
        db.close()
        if alignment_validity is None:
            await interaction.response.send_message(content=f"{new_alignment} is not a invalid alignment.")
            return
        if government_validity is None:
            await interaction.response.send_message(content=f"Government type of {new_government} does not exist.")
            return
        if result is None:
            status = f"The kingdom of {old_kingdom} which you have attempted to modify was doesn't exist."
            await interaction.response.send_message(status)
        elif old_password != result[1]:
            status = f"H-Have you lied to me slash commander-kun? That password wasn't correct for the kingdom of {kingdom}!"
            await interaction.response.send_message(status)
        elif result is not None and result[1] == old_password:
            await Event.modify_kingdom(self, old_kingdom, new_kingdom, new_password, new_government, new_alignment,
                                       guild_id, author)
            status = f"the specified kingdom of {old_kingdom} has been modified with the relevant changes to make it into {new_kingdom}"
            await interaction.response.send_message(status)

    @kingdom_group.command()
    async def display(self, interaction: discord.Interaction, current_page: int = 1):
        """This displays all kingdoms stored in the database"""
        guild_id = interaction.guild.id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        cursor.execute("Select COUNT(Kingdom) FROM Kingdoms")
        kingdom_count = cursor.fetchone()
        max_page = math.ceil(kingdom_count[0] / 5)
        if current_page >= max_page:
            current_page = max_page
        low = 1 + ((current_page - 1) * 5)
        high = 5 + ((current_page - 1) * 5)
        cursor.execute("Select Search from Admin where identifier = 'Decay'")
        decay = cursor.fetchone()
        if decay[0]:  # IF THE SERVER HAS DECAY ON
            cursor.execute(
                """select Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}""")
            pull = cursor.fetchall()
            embed = discord.Embed(title=f"Kingdoms page {current_page}", description=f'This is list of kingdoms',
                                  colour=discord.Colour.blurple())
            for result in pull:
                embed.add_field(name=f'Kingdom info',
                                value=f'**Kingdom**: {result[0]}, **Govt**: {result[1]} **Alignment**: {result[2]}',
                                inline=False)
                embed.add_field(name=f'Kingdom Control', value=f'**Control DC**: {result[3]}, **BP**: {result[4]}')
                embed.add_field(name=f'Kingdom Stats',
                                value=f'**Hex**: {result[6]} **Pop**: {result[7]} **Cons**: {result[13]}')
            await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()
            for button in buttons:
                await msg.add_reaction(button)
            while True:
                try:
                    reaction, user = await bot.wait_for('reaction_add', check=lambda reaction,
                                                                                     user: user.id == interaction.user.id and reaction.emoji in buttons,
                                                        timeout=60.0)
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
                        await msg.remove_reaction(button, interaction.user)
                    if current_page != previous_page:
                        cursor.execute(
                            "Select Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}")
                        edit_pull = cursor.fetchall()
                        embed = discord.Embed(title=f"Kingdoms page {current_page}",
                                              description=f'This is list of kingdoms', colour=discord.Colour.blurple())
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
            cursor.execute(
                """select Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}""")
            pull = cursor.fetchall()
            embed = discord.Embed(title=f"Kingdoms page {current_page}", description=f'This is list of kingdoms',
                                  colour=discord.Colour.blurple())
            for result in pull:
                embed.add_field(name=f'Kingdom info',
                                value=f'**Kingdom**: {result[0]}, **Govt**: {result[1]} **Alignment**: {result[2]}',
                                inline=False)
                embed.add_field(name=f'Kingdom Control',
                                value=f'**Control DC**: {result[3]}, **BP**: {result[4]}, **SP**: {result[5]}')
                embed.add_field(name=f'Kingdom Stats',
                                value=f'**Hex**: {result[6]} **Pop**: {result[7]} **Cons**: {result[13]}')
            await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()
            for button in buttons:
                await msg.add_reaction(button)
            while True:
                try:
                    reaction, user = await bot.wait_for('reaction_add', check=lambda reaction,
                                                                                     user: user.id == interaction.user.id and reaction.emoji in buttons,
                                                        timeout=60.0)
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
                        await msg.remove_reaction(button, interaction.user)
                    if current_page != previous_page:
                        cursor.execute(
                            "Select Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}")
                        edit_pull = cursor.fetchall()
                        embed = discord.Embed(title=f"Kingdoms page {current_page}",
                                              description=f'This is list of kingdoms', colour=discord.Colour.blurple())
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

    @kingdom_group.command()
    async def detail(self, interaction: discord.Interaction, kingdom: str, custom_stats: bool = False):
        """This displays the detailed information of a specific kingdom"""
        kingdom = str.replace(str.title(kingdom), ";", "")
        guild_id = interaction.guild_id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        if custom_stats:
            cursor.execute(
                "Select Control_DC, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms_Custom where Kingdom = '{kingdom}'")
            kingdom_info = cursor.fetchone()
            if kingdom_info is None:
                await interaction.response.send_message(f'The kingdom of {kingdom_info} could not be found.')
            if kingdom_info is not None:
                embed = discord.Embed(title=f"Kingdom of {kingdom}",
                                      description=f'Here is the full view of this Custom Information for this kingdom',
                                      colour=discord.Colour.blurple())
                embed.add_field(name=f'Control_DC', value=f'{kingdom_info[0]}')
                embed.add_field(name=f'Economy', value=f'{kingdom_info[1]}')
                embed.add_field(name=f'Loyalty', value=f'{kingdom_info[2]}')
                embed.add_field(name=f'Stability', value=f'{kingdom_info[3]}')
                embed.add_field(name=f'Fame', value=f'{kingdom_info[4]}')
                embed.add_field(name=f'Unrest', value=f'{kingdom_info[5]}')
                embed.add_field(name=f'Consumption', value=f'{kingdom_info[6]}')
                await interaction.response.send_message(embed=embed)
        cursor.execute("Select Search from Admin where identifier = 'Decay'")
        decay = cursor.fetchone()
        if decay[0]:
            if not custom_stats:
                cursor.execute(
                    """select Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms where Kingdom = '{kingdom}'""",
                    {'Kingdom': kingdom})
                kingdom_info = cursor.fetchone()
                if kingdom_info is None:
                    await interaction.response.send_message(f'The kingdom of {kingdom} could not be found.')
                if kingdom_info is not None:
                    embed = discord.Embed(title=f"Kingdom of {kingdom}",
                                          description=f'Here is the full view of this kingdom',
                                          colour=discord.Colour.blurple())
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
                    await interaction.response.send_message(embed=embed)
        if not decay[0]:
            if not custom_stats:
                cursor.execute(
                    """select Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms where Kingdom = '{kingdom}'""",
                    {'Kingdom': kingdom})
                kingdom_info = cursor.fetchone()
                if kingdom_info is None:
                    await interaction.response.send_message(f'The kingdom of {kingdom} could not be found.')
                if kingdom_info is not None:
                    embed = discord.Embed(title=f"Kingdom of {kingdom}",
                                          description=f'Here is the full view of this kingdom',
                                          colour=discord.Colour.blurple())
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
                    await interaction.response.send_message(embed=embed)

        cursor.close()
        db.close()

    """THIS CALLS FOR A SINGULAR KINGDOM OR IT'S CUSTOM INFORMATION"""

    @kingdom_group.command()
    @app_commands.autocomplete(character_name=own_character_select_autocompletion)
    async def bp(self, interaction: discord.Interaction, kingdom: str, password: str, character_name: str, amount: int):
        """This modifies the number of build points in a kingdom"""
        kingdom = str.replace(str.title(kingdom), ";", "")
        password = str.replace(password, ";", "")
        character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
        guild_id = interaction.guild_id
        author = interaction.user.name
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute("""select Kingdom, Password, Build_Points FROM Kingdoms where Kingdom = '{kingdom}'""",
                       {'Kingdom': kingdom})
        result = cursor.fetchone()
        sql = """select True_Character_Name, Gold from Player_Characters where Player_Name = ? and Character_Name = ? OR Nickname = ?"""
        val = (author, character_name, character_name)
        cursor.execute(sql, val)
        character_info = cursor.fetchone()
        if character_info is None:
            await interaction.response.send_message(
                f"Falsehoods! the Character of {character_name} either doesn't exist or belong to {author}!")
        elif character_info is not None:
            cost = amount * 4000
            gold_value = character_info[1] - cost
            if gold_value < 0:
                await interaction.response.send_message(
                    f"Sell yourself into slavery if you want to buy these points! We don't accept debt at this shop!")
            if gold_value >= 0:
                if result is None:
                    await interaction.response.send_message(
                        f"Bollocks! The kingdom of {kingdom} was not a valid kingdom to give building points to!")
                    return
                if result[1] != password:
                    await interaction.response.send_message(
                        f"The password provided for the kingdom of {kingdom} was inaccurate!!")
                if result is not None and result[1] == password:
                    build_points = result[2] + amount
                    if build_points < 0:
                        await interaction.response.send_message(
                            f"Impossible! the kingdom of {kingdom} would have {build_points} remaining build points and go into anarchy!!")
                    if build_points >= 0:
                        await Event.adjust_build_points(self, kingdom, amount, guild_id, character_info[0], author)
                        await interaction.response.send_message(
                            f"the kingdom of {kingdom} has been adjusted by {amount} build points and has a new value of {build_points}! {character_info[0]} has been charged {cost} GP leaving {gold_value} remaining!")

    """We can make this ALL settlements for that kingdom, or a specific settlement"""

    @kingdom_group.command()
    @app_commands.autocomplete(character_name=own_character_select_autocompletion)
    async def sp(self, interaction: discord.Interaction, kingdom: str, password: str, character_name: str, amount: int):
        """This modifies the Stability Points for a kingdom"""
        kingdom = str.replace(str.title(kingdom), ";", "")
        password = str.replace(password, ";", "")
        character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
        guild_id = interaction.guild_id
        author = interaction.user.name
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute("Select Search from Admin where identifier = 'Decay'")
        decay = cursor.fetchone()
        if decay[0]:  # IF THE SERVER HAS DECAY ON
            cursor.execute(
                """select Kingdom, Password, Stabilization_Points FROM Kingdoms where Kingdom = '{kingdom}'""",
                {'Kingdom': kingdom})
            result = cursor.fetchone()
            sql = """select True_Character_Name, Gold from Player_Characters where Character_Name = ? or Nickname = ?"""
            val = (character_name, character_name)
            cursor.execute(sql, val)
            character_info = cursor.fetchone()
            cost = amount * 4000
            gold_value = character_info[1] - cost
            if character_info is None:
                await interaction.response.send_message(
                    f"Falsehoods! the Character of {character_name} either doesn't exist or belong to {author}!")
            elif character_info is not None:
                if gold_value < 0:
                    await interaction.response.send_message(
                        f"Sell yourself into slavery if you want to buy these points! We don't accept debt at this shop!")
                elif gold_value >= 0:
                    if result is None:
                        await interaction.response.send_message(
                            f"You fool! The kingdom of {kingdom} a valid kingdom to give building points to!")
                        return
                    if result[1] != password:
                        await interaction.response.send_message(
                            f"The password provided for the kingdom of {kingdom} was inaccurate!!")
                    if result is not None and result[1] == password:
                        stabilization_points = result[2] + amount
                        if stabilization_points < 0:
                            await interaction.response.send_message(
                                f"Impossible! the kingdom of {kingdom} would have {stabilization_points} remaining stabilization_points and go into anarchy!!")
                        if stabilization_points >= 0:
                            await Event.adjust_stabilization_points(self, kingdom, amount, guild_id, author,
                                                                    character_info[0])
                            await interaction.response.send_message(
                                f"The kingdom of {kingdom} has been adjusted by {amount} Stabilization Points and has a new value of {stabilization_points}! {character_info[0]} has been charged {cost} GP leaving {gold_value} remaining!")
            if not decay[0]:
                await interaction.response.send_message(f"this server does not have decay enabled!")

    """We can make this ALL settlements for that kingdom, or a specific settlement"""
