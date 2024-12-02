import math
import typing
from dataclasses import dataclass
from decimal import Decimal

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
from commands import gamemaster_commands, character_commands


# Dataclasses
@dataclass
class KingdomInfo:
    kingdom: str
    password: Optional[str] = None
    government: Optional[str] = None
    alignment: Optional[str] = None
    control_dc: Optional[int] = None
    build_points: Optional[int] = None
    stabilization_points: Optional[int] = None
    size: Optional[int] = None
    population: Optional[int] = None
    economy: Optional[int] = None
    loyalty: Optional[int] = None
    stability: Optional[int] = None
    fame: Optional[int] = None
    unrest: Optional[int] = None
    consumption: Optional[int] = None

@dataclass
class SettlementInfo:
    kingdom: str
    settlement: str
    size: Optional[int] = None
    population: Optional[int] = None
    corruption: Optional[int] = None
    crime: Optional[int] = None
    productivity: Optional[int] = None
    law: Optional[int] = None
    lore: Optional[int] = None
    society: Optional[int] = None
    danger: Optional[int] = None
    defence: Optional[int] = None
    base_value: Optional[int] = None
    spellcasting: Optional[int] = None
    supply: Optional[int] = None
    decay: Optional[int] = None

@dataclass
class BuildingInfo:
    building: str
    build_points: int
    lots: int
    economy: int
    loyalty: int
    stability: int
    fame: int
    unrest: int
    corruption: int
    crime: int
    productivity: int
    law: int
    lore: int
    society: int
    danger: int
    defence: int
    base_value: int
    spellcasting: int
    supply: int
    settlement_limit: int
    district_limit: int
    description: str


# autocompletes functions for kingdom
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


# Purpose FUnctions
def encrypt_password(plain_password: str):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed_password


def validate_password(plain_password, stored_hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), stored_hashed_password)


class AttributeSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(
            placeholder='Select an Attribute...',
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            self.view.attribute = self.values[0]

            await self.view.leadership_modifier_select
        except Exception as e:
            logging.exception(f"Error in AttributeSelect callback: {e}")
            await interaction.response.send_message(
                "An error occurred while selecting the attribute.", ephemeral=False
            )
            self.view.stop()


class LeadershipModifier(discord.ui.Select):
    def __init__(self, options):
        super().__init__(
            placeholder='Select a kingdom stat to modify...',
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            self.view.attribute = self.values[0]

            await self.view.leadership_modifier_select
        except Exception as e:
            logging.exception(f"Error in LeadershipModifier callback: {e}")
            await interaction.response.send_message(
                "An error occurred while selecting the modifier.", ephemeral=False
            )
            self.view.stop()

class LeadershipView(discord.ui.View):
    def __init__(self, options, guild_id: int, user_id: int, kingdom: str, role: str, character_name: str, additional: int, economy: int, loyalty: int, stability: int, hexes: int):
        super().__init__()
        self.guild_id = guild_id
        self.user_id = user_id
        self.kingdom = kingdom
        self.role = role
        self.character_name = character_name
        self.economy = economy
        self.economy_modified = 0
        self.loyalty = loyalty
        self.loyalty_modified = 0
        self.stability = stability
        self.stability_modified = 0
        self.hexes = hexes
        self.additional=additional

        if options is None:
            self.stop()

        if len(options) == 1: # Only a single option, so we can skip the attribute select and process.
            self.attribute = options[0].value
            if economy + loyalty + stability > 1: # In most systems this means that the there are 2 fields applicable.
                # Need to build options based on which is present.
                self.leadership_modifier_select = LeadershipModifier(options=options)
                self.add_item(self.leadership_modifier_select)
            else:
                ... # Only A single option, so we can skip the next step and process.
        else:
            self.add_item(AttributeSelect(options=options))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure that only the user who initiated the view can interact with the buttons."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You cannot interact with this button.",
                ephemeral=False
            )
            return False
        return True

    async def leadership_modifier_select(self):
        if self.additional > 0:
            self.additional -= 1
            # define options based off economy, loyalty, and stability.
            if self.economy + self.loyalty + self.stability > 1: # In most systems this means that the there are 2 fields applicable.
                self.add_item(LeadershipModifier(options=options)) #OPTIONS IS NOT DEFINED HERE
        else:
            await update_leader(
                guild_id=self.guild_id,
                author=self.user_id,
                kingdom=self.kingdom,
                title=self.role,
                character_name=self.character_name,
                stat=self.attribute,
                modifier=self.economy_modified,
                economy=self.economy_modified,
                loyalty=self.loyalty_modified,
                stability=self.stability_modified
            )


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
            await cursor.execute("""select Kingdom FROM Kingdoms where Kingdom = ?""", (kingdom,))
            kingdom_presence = await cursor.fetchone()
            if kingdom_presence is not None:
                return "The kingdom already exists."
            await cursor.execute(
                """select Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = ?""", (alignment,))
            alignment_type = await cursor.fetchone()
            if alignment_type is None:
                return "Invalid alignment."
            await cursor.execute("""select Government FROM AA_Government WHERE Government = ?""", (government,))
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
                await cursor.execute("INSERT Into Kingdoms_Custom(Kingdom, Control_DC, Economy, Loyalty, Stability, Fame, Unrest, Consumption) VALUES (?, 0, 0, 0, 0, 0, 0, 0)", (kingdom,))
                await db.commit()
                return f"Congratulations, you have created the kingdom of {kingdom}."

    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error creating a kingdom: {e}")
        return "An error occurred while creating a kingdom."


async def edit_a_kingdom(
        guild_id: int,
        author: str,
        old_kingdom_info: KingdomInfo,
        new_kingdom: str,
        government: str,
        alignment: str) -> str:
    try:
        new_kingdom = old_kingdom_info.kingdom if not new_kingdom else new_kingdom
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            cursor = await db.cursor()
            if alignment is not None:
                await cursor.execute("""select Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = ?""", (old_kingdom_info.alignment,))
                old_alignment_info = await cursor.fetchone()
                await cursor.execute(
                    """select Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = ?""", (alignment,))
                new_alignment_info = await cursor.fetchone()
                if new_alignment_info is None:
                    return "Invalid alignment."
                old_kingdom_info.economy += new_alignment_info[1] - old_alignment_info[1]
                old_kingdom_info.loyalty += new_alignment_info[2] - old_alignment_info[2]
                old_kingdom_info.stability += new_alignment_info[3] - old_alignment_info[3]
            if government is not None:
                await cursor.execute("SELECT Government, Corruption, Crime, Law, Lore, Productivity, Society FROM AA_Government WHERE Government = ?", (old_kingdom_info.government,))
                old_government_info = await cursor.fetchone()
                await cursor.execute("SELECT Government, Corruption, Crime, Law, Lore, Productivity, Society FROM AA_Government WHERE Government = ?", (government,))
                new_government_info = await cursor.fetchone()
                if new_government_info is None:
                    return "Invalid government type."
                (new_corruption, new_crime, new_law, new_lore, new_productivity, new_society) = new_government_info
                (old_corruption, old_crime, old_law, old_lore, old_productivity, old_society) = old_government_info
                sum_corruption = new_corruption - old_corruption
                sum_crime = new_crime - old_crime
                sum_law = new_law - old_law
                sum_lore = new_lore - old_lore
                sum_productivity = new_productivity - old_productivity
                sum_society = new_society - old_society
                await cursor.execute("UPDATE Settlements SET Corruption = Corruption + ?, Crime = Crime + ?, Law = Law + ?, Lore = Lore + ?, Productivity = Productivity + ?, Society = Society + ? WHERE Kingdom = ?", (sum_corruption, sum_crime, sum_law, sum_lore, sum_productivity, sum_society, old_kingdom))
            await cursor.execute("UPDATE Kingdoms SET Kingdom = ?, Password = ?, Government = ?, Alignment = ?, Economy = ?, Loyalty = ?, Stability = ? WHERE Kingdom = ?", (new_kingdom, government, alignment, old_kingdom_info.economy, old_kingdom_info.loyalty, old_kingdom_info.stability, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE Kingdoms_Custom SET Kingdom = ? WHERE Kingdom = ?", (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE settlements SET Kingdom = ? WHERE Kingdom = ?", (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE settlements_Custom SET Kingdom = ? WHERE Kingdom = ?", (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE Hexes SET Kingdom = ? WHERE Kingdom = ?", (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)", (author, datetime.datetime.now(), "Kingdoms", "Edit", f"Edited the kingdom of {old_kingdom_info.kingdom} to {new_kingdom}"))
            await db.commit()
            return f"The kingdom of {old_kingdom_info.kingdom} has been edited to {new_kingdom}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error creating a kingdom: {e}")
        return "An error occurred while creating a kingdom."


async def delete_a_kingdom(
        guild_id: int, author: str, kingdom: str) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("DELETE FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM Kingdoms_Custom WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM settlements WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM settlements_Custom WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM Hexes WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)", (author, datetime.datetime.now(), "Kingdoms", "Delete", f"Deleted the kingdom of {kingdom}"))
            await db.commit()
            return f"The kingdom of {kingdom} has been deleted, it's holdings cleared, and it's hexes freed."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error deleting a kingdom: {e}")
        return "An error occurred while deleting a kingdom."

async def adjust_bp(
        guild_id: int,
        author: int,
        kingdom: str,
        amount: int) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Build_Points FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
            kingdom_info = await cursor.fetchone()
            if kingdom_info is None:
                return "The kingdom does not exist."
            if amount < 0:
                amount = max(amount, -kingdom_info[0])
            await cursor.execute("UPDATE Kingdoms SET Build_Points = Build_Points + ? WHERE Kingdom = ?", (amount, kingdom))
            await cursor.execute("Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)", (author, datetime.datetime.now(), "Kingdoms", "Increase BP", f"Increased the build points of {kingdom} by {amount}"))
            await db.commit()
            return f"The build points of {kingdom} have been increased by {amount}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error increasing build points: {e}")
        return "An error occurred while increasing build points."


async def adjust_sp(
        guild_id: int,
        author: int,
        kingdom: str,
        amount: int) -> str:
    try:
        async with shared_functions.config_cache.lock:
            configs = shared_functions.config_cache.cache.get(guild_id)
            if configs:
                decay_bool = configs.get('Decay')
        if decay_bool == 'False':
            return "Decay is disabled on this server."
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Stabilization_Points FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
            kingdom_info = await cursor.fetchone()
            if kingdom_info is None:
                return "The kingdom does not exist."
            if amount < 0:
                amount = min(amount, -kingdom_info[0])
            await cursor.execute("UPDATE Kingdoms SET Stabilization_Points = Stabilization_Points + ? WHERE Kingdom = ?", (amount, kingdom))
            await cursor.execute("Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)", (author, datetime.datetime.now(), "Kingdoms", "Increase SP", f"Increased the stabilization points of {kingdom} by {amount}"))
            await db.commit()
            return f"The stabilization points of {kingdom} have been increased by {amount}."


async def fetch_kingdom(
        guild_id: int,
        kingdom: str) -> typing.Union[KingdomInfo, None]:
    async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        await cursor.execute(
            """SELECT Kingdom, Password, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption FROM Kingdoms WHERE Kingdom = ?""",
            (kingdom,))
        kingdom_info = await cursor.fetchone()
        if kingdom_info is not None:
            return KingdomInfo(*kingdom_info)
        return None

async def fetch_settlement(
        guild_id: int,
        settlement: str) -> typing.Union[SettlementInfo, None]:
    async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        await cursor.execute(
            """SELECT Kingdom, Settlement, Size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay FROM settlements WHERE Settlement = ?""",
            (settlement,))
        settlement_info = await cursor.fetchone()
        if settlement_info is not None:
            return SettlementInfo(*settlement_info)
        return None


async def fetch_building(
        guild_id: int,
        building: str) -> typing.Union[BuildingInfo, None]:
    async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
        cursor = await db.cursor()
        await cursor.execute(
            """SELECT Building, Build_Points, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Settlement_Limit, District_Limit, Description FROM Buildings_Blueprints WHERE Building = ?""",
            (building,))
        building_info = await cursor.fetchone()
        if building_info is not None:
            return BuildingInfo(*building_info)
        return None

async def update_leader(
        guild_id: int,
        author: int,
        kingdom: str,
        title: str,
        character_name: str,
        stat: str,
        modifier: int,
        economy: int,
        loyalty: int,
        stability: int
        ) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Ecomomy, Loyalty, Stability, Unrest FROM Leadership WHERE Kingdom = ? AND Title = ?", (kingdom, title))
            leader_info = await cursor.fetchone()
            if leader_info is None:
                return "The leader does not exist."
            (old_economy, old_loyalty, old_stability, old_unrest) = leader_info
            sum_economy = economy - old_economy
            sum_loyalty = loyalty - old_loyalty
            sum_stability = stability - old_stability
            await cursor.execute("UPDATE Leadership Set Character_Name = ?, Stat = ?, Modifier = ?, Economy = ?, Loyalty = ?, Stability = ? WHERE Kingdom = ? AND Title = ?", (character_name, stat, modifier, economy, loyalty, stability, kingdom, title))
            await cursor.execute("UPDATE Kingdoms SET Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ? WHERE Kingdom = ?", (sum_economy, sum_loyalty, sum_stability, -old_unrest, kingdom))
            await cursor.execute("Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)", (author, datetime.datetime.now(), "Leadership", "Update", f"Updated the leader of {kingdom} to {character_name}"))
            await db.commit()

    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error updating leader: {e}")
        return "An error occurred while updating the leader."


class KingdomCommands(commands.Cog, name='Kingdom'):
    def __init__(self, bot):
        self.bot = bot

    kingdom_group = discord.app_commands.Group(
        name='kingdom',
        description='Commands related to playing'
    )

    leadership_group = discord.app_commands.Group(
        name='leadership',
        description='Commands related to playing',
        parent=kingdom_group
    )



    @kingdom_group.command(name="create", description="Create a kingdom")
    @app_commands.autocomplete(government=government_autocompletion)
    @app_commands.autocomplete(alignment=alignment_autocomplete)
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

    @kingdom_group.command(name="destroy", description="Remove a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    async def destroy(self, interaction: discord.Interaction, kingdom: str, password: str):
        """This is a player command to remove a kingdom THEY OWN from play"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}_test.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("""select Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
                result = await cursor.fetchone()
                if result is None:
                    status = f"the kingdom which you have elected to make a war crime out of couldn't be found."
                    await interaction.followup.send(content=status)
                    return
                valid_password = validate_password(password, result[1])
                if valid_password:
                    status = await delete_a_kingdom(interaction.guild_id, kingdom)
                    await interaction.followup.send(content=status)
                else:
                    status = f"You have entered an invalid password for this kingdom."
                    await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error deleting a kingdom: {e}")
            await interaction.followup.send(content="An error occurred while deleting a kingdom.")

    @kingdom_group.command(name="modify", description="Modify a kingdom")
    @app_commands.autocomplete(old_kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(new_government=government_autocompletion)
    @app_commands.autocomplete(new_alignment=alignment_autocomplete)
    async def modify(self, interaction: discord.Interaction, old_kingdom: str, new_kingdom: typing.Optional[str], old_password: typing.Optional[str],
                     new_password: typing.Optional[str], new_government: typing.Optional[str], new_alignment: typing.Optional[str]):
        """This is a player command to modify a kingdom THEY OWN."""
        await interaction.response.defer(thinking=True)
        try:
            kingdom_info = await fetch_kingdom(interaction.guild_id, old_kingdom)
            if not kingdom_info:
                await interaction.followup.send(content=f"The kingdom of {old_kingdom} does not exist.")
                return
            valid_password = validate_password(old_password, kingdom_info.password)
            if not valid_password:
                await interaction.followup.send(content="The password provided is incorrect.")
                return
            if new_password:
                new_password = encrypt_password(new_password)
                async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}_test.sqlite") as db:
                    cursor = await db.cursor()
                    await cursor.execute("UPDATE Kingdoms SET Password = ? WHERE Kingdom = ?", (new_password, old_kingdom))
                    await db.commit()
            status = await edit_a_kingdom(
                guild_id=interaction.guild_id,
                author=interaction.user.name,
                old_kingdom_info=kingdom_info,
                new_kingdom=new_kingdom,
                government=new_government,
                alignment=new_alignment)
            await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error fetching kingdom: {e}")
            await interaction.followup.send(content="An error occurred while fetching kingdom.")
            return


    @kingdom_group.command(name="build_points", description="Adjust the build points of a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def bp(self, interaction: discord.Interaction, kingdom: str, password: str, character_name: str, amount: int):
        """This modifies the number of build points in a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}_test.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, Build_Points FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("SELECT Gold, Gold_Value, Gold_Value_Max, Level, Oath, Thread_ID FROM Player_Characters WHERE Player_ID = ? AND (Character_Name = ? OR Nickname = ?)", (interaction.user.id, character_name, character_name))
                character_info = await cursor.fetchone()
                if not character_info:
                    await interaction.followup.send(content=f"The character of {character_name} does not exist.")
                    return
                if amount < 0:
                    bought_points = max(amount, -kingdom_results[1])
                    cost = bought_points * 4000
                    gold_reward = await character_commands.gold_calculation(
                        guild_id=interaction.guild_id,
                        author_name=interaction.user.name,
                        author_id=interaction.user.id,
                        character_name=character_name,
                        level= character_info[3],
                        oath=character_info[4],
                        gold=character_info[0],
                        gold_value=character_info[1],
                        gold_value_max=character_info[2],
                        gold_change=Decimal(cost),
                        reason="selling build points",
                        source="Adjust BP COmmands",
                        gold_value_change=Decimal(0),
                        gold_value_max_change=Decimal(0),
                        is_transaction=False
                    )
                    if gold_reward[0] < cost / 2:
                        await interaction.followup.send(content=f"The character of {character_name} has the oath of {character_info[4]}, this would make selling build points negligably valuable.")
                        return
                    else:
                        await adjust_bp(interaction.guild_id, interaction.user.id, kingdom, bought_points)
                        gold_reward = await character_commands.gold_calculation(
                            guild_id=interaction.guild_id,
                            author_name=interaction.user.name,
                            author_id=interaction.user.id,
                            character_name=character_name,
                            level=character_info[3],
                            oath=character_info[4],
                            gold=character_info[0],
                            gold_value=character_info[1],
                            gold_value_max=character_info[2],
                            gold_change=Decimal(cost),
                            reason="selling build points",
                            source="Adjust BP COmmands",
                            gold_value_change=Decimal(0),
                            gold_value_max_change=Decimal(0),
                        )
                        update_character_info = shared_functions.UpdateCharacterData(
                            character_name=character_name,
                            gold_package=(gold_reward[0], gold_reward[1], gold_reward[2])
                        )
                        update_character_log = shared_functions.CharacterChange(
                          author=interaction.user.name,
                            character_name=character_name,
                            transaction_id=gold_reward[4],
                            gold_change=gold_reward[0],
                            gold=gold_reward[1],
                            gold_value=gold_reward[2],
                            gold_value_max=gold_reward[3],
                            source=f"Adjust BP Command selling {bought_points} build points",
                        )
                        await shared_functions.update_character(interaction.guild_id, update_character_info)
                        await shared_functions.log_embed(bot=self.bot, thread=character_info[5], guild=interaction.guild, change=update_character_log)
                        await shared_functions.character_embed(guild=interaction.guild, character_name=character_name)
                        await interaction.followup.send(content=f"The character of {character_name} has sold {bought_points} build points for {gold_reward[0]} GP.")
                else:
                    maximum_points = math.floor(character_info[0] / 4000)
                    bought_points = min(amount, maximum_points)
                    cost = bought_points * 4000
                    adjusted_bp_result = await adjust_bp(interaction.guild_id, interaction.user.id, kingdom, bought_points)
                    gold_used = await character_commands.gold_calculation(
                            guild_id=interaction.guild_id,
                            author_name=interaction.user.name,
                            author_id=interaction.user.id,
                            character_name=character_name,
                            level=character_info[3],
                            oath=character_info[4],
                            gold=Decimal(character_info[0]),
                            gold_value=Decimal(character_info[1]),
                            gold_value_max=Decimal(character_info[2]),
                            gold_change=-Decimal(cost),
                            reason="selling build points",
                            source="Adjust BP COmmands",
                            gold_value_change=Decimal(0),
                            gold_value_max_change=Decimal(0),
                        )
                    update_character_info = shared_functions.UpdateCharacterData(
                        character_name=character_name,
                        gold_package=(gold_used[0], gold_used[1], gold_used[2])
                    )
                    update_character_log = shared_functions.CharacterChange(
                        author=interaction.user.name,
                        character_name=character_name,
                        transaction_id=gold_used[4],
                        gold_change=gold_used[0],
                        gold=gold_used[1],
                        gold_value=gold_used[2],
                        gold_value_max=gold_used[3],
                        source=f"Adjust BP Command buying {bought_points} build points",
                    )
                    await shared_functions.update_character(interaction.guild_id, update_character_info)
                    await shared_functions.log_embed(bot=self.bot, thread=character_info[5], guild=interaction.guild,
                                                     change=update_character_log)
                    await shared_functions.character_embed(guild=interaction.guild, character_name=character_name)
                    await interaction.followup.send(adjusted_bp_result)
        except (aiosqlite, TypeError, ValueError) as e:
            logging.exception(f"Error increasing build points: {e}")
            await interaction.followup.send(content="An error occurred while increasing build points.")


    @kingdom_group.command(name='stabilization_points', description='Adjust the stabilization points of a kingdom')
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def sp(self, interaction: discord.Interaction, kingdom: str, password: str, character_name: str, amount: int):
        """This modifies the Stability Points for a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with shared_functions.config_cache.lock:
                configs = shared_functions.config_cache.cache.get(interaction.guild_id)
                if configs:
                    decay_bool = configs.get('Decay')
            if decay_bool == 'False':
                return "Decay is disabled on this server."
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}_test.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, Stabilization_Points FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("SELECT Gold, Gold_Value, Gold_Value_Max, Level, Oath, Thread_ID FROM Player_Characters WHERE Player_ID = ? AND (Character_Name = ? OR Nickname = ?)", (interaction.user.id, character_name, character_name))
                character_info = await cursor.fetchone()
                if not character_info:
                    await interaction.followup.send(content=f"The character of {character_name} does not exist.")
                    return
                if amount < 0:
                    bought_points = max(amount, -kingdom_results[1])
                    cost = bought_points * 4000
                    gold_reward = await character_commands.gold_calculation(
                        guild_id=interaction.guild_id,
                        author_name=interaction.user.name,
                        author_id=interaction.user.id,
                        character_name=character_name,
                        level= character_info[3],
                        oath=character_info[4],
                        gold=character_info[0],
                        gold_value=character_info[1],
                        gold_value_max=character_info[2],
                        gold_change=Decimal(cost),
                        reason="selling build points",
                        source="Adjust BP COmmands",
                        gold_value_change=Decimal(0),
                        gold_value_max_change=Decimal(0),
                        is_transaction=False
                    )
                    if gold_reward[0] < cost / 2:
                        await interaction.followup.send(content=f"The character of {character_name} has the oath of {character_info[4]}, this would make selling stabilization points negligibly valuable.")
                        return
                    else:
                        await adjust_sp(interaction.guild_id, interaction.user.id, kingdom, bought_points)
                        gold_reward = await character_commands.gold_calculation(
                            guild_id=interaction.guild_id,
                            author_name=interaction.user.name,
                            author_id=interaction.user.id,
                            character_name=character_name,
                            level=character_info[3],
                            oath=character_info[4],
                            gold=character_info[0],
                            gold_value=character_info[1],
                            gold_value_max=character_info[2],
                            gold_change=Decimal(cost),
                            reason="selling Stabilization points",
                            source="Adjust SP Commands",
                            gold_value_change=Decimal(0),
                            gold_value_max_change=Decimal(0),
                        )
                        update_character_info = shared_functions.UpdateCharacterData(
                            character_name=character_name,
                            gold_package=(gold_reward[0], gold_reward[1], gold_reward[2])
                        )
                        update_character_log = shared_functions.CharacterChange(
                          author=interaction.user.name,
                            character_name=character_name,
                            transaction_id=gold_reward[4],
                            gold_change=gold_reward[0],
                            gold=gold_reward[1],
                            gold_value=gold_reward[2],
                            gold_value_max=gold_reward[3],
                            source=f"Adjust SP Command selling {bought_points} build points",
                        )
                        await shared_functions.update_character(interaction.guild_id, update_character_info)
                        await shared_functions.log_embed(bot=self.bot, thread=character_info[5], guild=interaction.guild, change=update_character_log)
                        await shared_functions.character_embed(guild=interaction.guild, character_name=character_name)
                        await interaction.followup.send(content=f"The character of {character_name} has sold {bought_points} build points for {gold_reward[0]} GP.")
                else:
                    maximum_points = math.floor(character_info[0] / 4000)
                    bought_points = min(amount, maximum_points)
                    cost = bought_points * 4000
                    adjusted_bp_result = await adjust_sp(interaction.guild_id, interaction.user.id, kingdom, bought_points)
                    gold_used = await character_commands.gold_calculation(
                            guild_id=interaction.guild_id,
                            author_name=interaction.user.name,
                            author_id=interaction.user.id,
                            character_name=character_name,
                            level=character_info[3],
                            oath=character_info[4],
                            gold=Decimal(character_info[0]),
                            gold_value=Decimal(character_info[1]),
                            gold_value_max=Decimal(character_info[2]),
                            gold_change=-Decimal(cost),
                            reason="selling build points",
                            source="Adjust BP COmmands",
                            gold_value_change=Decimal(0),
                            gold_value_max_change=Decimal(0),
                        )
                    update_character_info = shared_functions.UpdateCharacterData(
                        character_name=character_name,
                        gold_package=(gold_used[0], gold_used[1], gold_used[2])
                    )
                    update_character_log = shared_functions.CharacterChange(
                        author=interaction.user.name,
                        character_name=character_name,
                        transaction_id=gold_used[4],
                        gold_change=gold_used[0],
                        gold=gold_used[1],
                        gold_value=gold_used[2],
                        gold_value_max=gold_used[3],
                        source=f"Adjust BP Command buying {bought_points} stabilization points",
                    )
                    await shared_functions.update_character(interaction.guild_id, update_character_info)
                    await shared_functions.log_embed(bot=self.bot, thread=character_info[5], guild=interaction.guild,
                                                     change=update_character_log)
                    await shared_functions.character_embed(guild=interaction.guild, character_name=character_name)
                    await interaction.followup.send(adjusted_bp_result)
        except (aiosqlite, TypeError, ValueError) as e:
            logging.exception(f"Error increasing build points: {e}")
            await interaction.followup.send(content="An error occurred while increasing build points.")

    @leadership_group.command(name="modify", description="Modify a leader, by changing their ability score or who is in charge")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def modify_leadership(self, kingdom, password, character_name, modifier):
        """This command is used to modify a leader's ability score or who is in charge of a kingdom"""
        ...
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



class LeadershipView(discord.ui.View):
    def __init__(self, user_id: int, guild_id: int, modifiers: dict):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.guild_id = guild_id
        self.modifiers = modifiers  # Dictionary of attribute names and their modifiers

        # Dynamically create buttons and add callbacks
        for attribute in self.modifiers.keys():
            button = discord.ui.Button(
                label=attribute.capitalize(),
                style=discord.ButtonStyle.primary
            )
            button.callback = self.create_roll_callback(leadership_role)  # Assign callback
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure that only the user who initiated the view can interact with the buttons."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You cannot interact with this button.",
                ephemeral=False
            )
            return False
        return True

    def create_roll_callback(self, leadership_role: str):
        """Generate a callback function for rolling the given attribute."""

        async def callback(interaction: discord.Interaction):
            roll = random.randint(1, 20)
            content = f"**Rolling :game_die: {attribute.capitalize()}** base: {roll}: total: {roll + self.modifiers[attribute]}"
            content += ":broken_heart: **Critical Failure**" if roll == 1 else ""
            content += ":sparkles: **Critical Success**" if roll == 20 else ""
            await interaction.response.send_message(content=content)

        return callback
