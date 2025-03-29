import asyncio
import datetime
import logging
import math
import random
import typing
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
import aiosqlite
import bcrypt
import discord
from discord import app_commands
from discord.ext import commands
from unidecode import unidecode
import shared_functions
from commands import character_commands

settlement_dict = {
    "Corruption": "Corruption",
    "Crime": "Crime",
    "Productivity": "Productivity",
    "Law": "Law",
    "Lore": "Lore",
    "Society": "Society",
    "Danger": "Danger",
    "Defence": "Defence",
    "Base Value": "Base_Value",
    "Spellcasting": "Spellcasting",
    "Supply": "Supply",
}
kingdom_dict = {
    "Size": "Size",
    "Population": "Population",
    "Unallocated Population": "Unallocated_Population",
    "Economy": "Economy",
    "Loyalty": "Loyalty",
    "Stability": "Stability",
    "Fame": "Fame",
    "Unrest": "Unrest",
    "Consumption": "Consumption",
}


# Dataclasses
@dataclass
class KingdomInfo:
    kingdom: str
    password: Optional[str] = None
    government: Optional[str] = None
    alignment: Optional[str] = None
    control_dc: Optional[int] = None
    build_points: Optional[int] = None

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
    full_name: str
    type: str
    subtype: str
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
    upgrade: str
    discount: str
    tier: int


@dataclass
class HexImprovementInfo:
    full_name: str
    name: str
    subtype: str
    build_points: int
    economy: int
    loyalty: int
    stability: int
    unrest: int
    consumption: int
    defence: int
    taxation: int
    cavernous: int
    coastline: int
    desert: int
    forest: int
    hills: int
    jungle: int
    marsh: int
    mountains: int
    plains: int
    water: int
    source: int
    size: int


def safe_min(a, b):
    """Safely add two values together, treating None as zero and converting to Decimal if necessary."""
    # Treat None as zero
    a = a if a is not None else 0
    b = b if b is not None else 0

    # If either value is a Decimal, convert both to Decimal
    if isinstance(a, int) or isinstance(b, int):
        a = int(a)
        b = int(b)

    return max(min(a, b), 0)


def safe_sub(a, b):
    """Safely add two values together, treating None as zero and converting to Decimal if necessary."""
    # Treat None as zero
    a = a if a is not None else 0
    b = b if b is not None else 0

    # If either value is a Decimal, convert both to Decimal
    if isinstance(a, int) or isinstance(b, int):
        a = int(a)
        b = int(b)

    return a - b


# autocompletes functions for kingdom
async def alignment_autocomplete(interaction: discord.Interaction, current: str
                                 ) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
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


async def blueprint_autocomplete(interaction: discord.Interaction, current: str
                                 ) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Building FROM kb_Buildings_Blueprints WHERE Building LIKE ? Limit 20",
            (f"%{current}%",))
        blueprint_list = await cursor.fetchall()
        for blueprint in blueprint_list:
            if current in blueprint[0]:
                data.append(app_commands.Choice(name=blueprint[0], value=blueprint[0]))
    return data


async def improvement_subtype_autocomplete(interaction: discord.Interaction, current: str
                                           ) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Full_Name, Subtype FROM KB_Hexes_Improvements WHERE Full_Name LIKE ? AND Type = 'Farm' Limit 20",
            (f"%{current}%",))
        blueprint_list = await cursor.fetchall()
        for blueprint in blueprint_list:
            if current in blueprint[0]:
                data.append(app_commands.Choice(name=f"{blueprint[0]} produces {blueprint[1]}", value=blueprint[0]))
    return data


async def blueprint_repurpose_autocomplete(interaction: discord.Interaction, current: str
                                           ) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Full_name FROM kb_Buildings_Blueprints WHERE Full_Name LIKE ? AND (Subtype in ('Magical Items', 'Magical Consumables', 'Textile', 'Mundane Exotic', 'Mundane Complex', 'Metallurgy', 'Weaponry') OR Type = 'Granary') Limit 20",
            (f"%{current}%",))
        blueprint_list = await cursor.fetchall()
        for blueprint in blueprint_list:
            if current in blueprint[0]:
                data.append(app_commands.Choice(name=blueprint[0], value=blueprint[0]))
    return data


async def blueprint_upgrade_autocomplete(interaction: discord.Interaction, current: str
                                         ) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Full_Name, Upgrade From Kb_Building_Blueprints WHERE Upgrade is not Null and Full_Name like ? Limit 20",
            (f"%{current}%",))
        blueprint_list = await cursor.fetchall()
        for blueprint in blueprint_list:
            if current in blueprint[0]:
                data.append(app_commands.Choice(name=f"{blueprint[0]} - {blueprint[1]}", value=blueprint[0]))
    return data


async def government_autocompletion(
        interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
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


async def hex_terrain_autocomplete(
        interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Hex_Terrain from AA_Hex_Terrains WHERE Hex_Terrain LIKE ? Limit 20",
            (f"%{current}%",))
        hex_list = await cursor.fetchall()
        for kb_hexes in hex_list:
            if current in kb_hexes[0]:
                data.append(app_commands.Choice(name=kb_hexes[0], value=kb_hexes[0]))

    return data


async def hex_improvement_autocomplete(
        interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Improvement FROM kb_Hexes_Improvements WHERE Improvement LIKE ? Limit 20",
            (f"%{current}%",))
        improvement_list = await cursor.fetchall()
        for improvement in improvement_list:
            if current in improvement[0]:
                data.append(app_commands.Choice(name=improvement[0], value=improvement[0]))
    return data


async def leadership_autocomplete(
        interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))

        await cursor.execute(
            "SELECT Title from AA_Leadership_Roles WHERE Title LIKE ? Limit 20",
            (f"%{current}%",))
        title_list = await cursor.fetchall()

        for title in title_list:
            if current in title[0]:
                data.append(app_commands.Choice(name=title[0], value=title[0]))
    return data


async def kingdom_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT kingdom from kb_Kingdoms WHERE Kingdom LIKE ? Limit 20",
            (f"%{current}%",))
        kingdom_list = await cursor.fetchall()
        for kingdom in kingdom_list:
            if current in kingdom[0]:
                data.append(app_commands.Choice(name=kingdom[0], value=kingdom[0]))

    return data


async def settlement_autocomplete(interaction: discord.Interaction, current: str
                                  ) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        current = unidecode(str.title(current))
        await cursor.execute(
            "SELECT Settlement FROM kb_settlements WHERE Settlement LIKE ? Limit 20",
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
    hashed_password = bcrypt.hashpw(plain_password.encode(), salt)
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
            await interaction.response.defer()
            self.view.attribute = self.values[0]
            # Remove the attribute select from the view
            self.view.clear_items()
            # Proceed to modifier selection
            await self.view.proceed_to_modifier_selection()
        except Exception as e:
            logging.exception(f"Error in AttributeSelect callback: {e}")
            await interaction.followup.send(
                "An error occurred while selecting the attribute.", ephemeral=True
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
            await interaction.response.defer()
            selected_modifier = self.values[0]
            modifier_value = getattr(self.view, selected_modifier.lower())
            # Update the modified value
            setattr(self.view, f'{selected_modifier.lower()}_modified', modifier_value)
            self.view.modifier_selection_count += 1
            # Remove previous modifier select
            self.view.clear_items()
            # Proceed to the next modifier selection
            await self.view.proceed_to_modifier_selection()
        except Exception as e:
            logging.exception(f"Error in  LeadershipModifier callback: {e}")
            await interaction.followup.send(
                "An error occurred while selecting the modifier.", ephemeral=True
            )
            self.view.stop()


class LeadershipView(discord.ui.View):
    def __init__(self, options, guild_id: int, user_id: int, kingdom: str, role: str,
                 character_name: str, additional: int, economy: float, loyalty: float,
                 stability: float, hexes: int, modifier: int, recipient_id: int):
        super().__init__()
        self.options = options  # Store options
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
        self.recipient_id = recipient_id
        self.additional = additional
        self.modifier_selection_count = 0  # Counter for modifiers selected
        self.modifier = modifier

        # Determine which modifiers are applicable
        self.modifier_fields = []
        if self.economy > 0:
            self.modifier_fields.append('Economy')
        if self.loyalty > 0:
            self.modifier_fields.append('Loyalty')
        if self.stability > 0:
            self.modifier_fields.append('Stability')
        print(self.modifier_fields, len(self.modifier_fields), options, len(options))
        # Attribute Selection
        if options is None or len(options) == 0:
            self.stop()
        elif len(options) == 1:
            print("singular attribute")
            self.attribute = options[0].value
            # Proceed to modifier selection
            asyncio.create_task(self.proceed_to_modifier_selection())
        else:
            # Multiple attributes, show selection
            print("Multiple attributes")
            self.add_item(AttributeSelect(options=options))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You cannot interact with this button.",
                ephemeral=True
            )
            return False
        return True

    async def proceed_to_modifier_selection(self):
        if self.modifier_selection_count < len(self.modifier_fields):
            # Create options for modifiers
            options = [
                discord.SelectOption(label=field, value=field)
                for field in self.modifier_fields
                if getattr(self, f'{field.lower()}_modified') == 0  # Skip already selected
            ]
            if options:
                # Remove previous modifier select if exists
                for child in self.children.copy():
                    if isinstance(child, LeadershipModifier):
                        self.remove_item(child)
                # Add new modifier select
                self.add_item(LeadershipModifier(options=options))
                # Edit the message to update the view
                await self.message.edit(content="Please select a kingdom stat to modify:", view=self)
            else:
                # All modifiers selected
                await self.finish_selection()
        else:
            # No modifiers to select
            await self.finish_selection()

    async def finish_selection(self):
        # Remove all items from the view
        self.clear_items()
        # Provide feedback to the user
        confirmation_message = (
            f"You have completed the selection process for your role '{self.role}' "
            f"in kingdom '{self.kingdom}'."
        )
        # Update the leader with the selected attributes and modifiers
        try:
            await update_leader(
                guild_id=self.guild_id,
                author=self.user_id,
                kingdom=self.kingdom,
                title=self.role,
                character_name=self.character_name,
                stat=self.attribute,
                modifier=self.modifier,
                player_id=self.recipient_id,
                economy=self.modifier if self.economy_modified else 0,
                loyalty=self.modifier if self.loyalty_modified else 0,
                stability=self.modifier if self.stability_modified else 0
            )
            # Edit the original message to show confirmation
            await self.message.edit(content=confirmation_message, view=None)
        except Exception as e:
            logging.exception(f"Error in finish_selection: {e}")
            # Inform the user of the error
            await self.message.edit(
                content="An error occurred while updating your leadership role.", view=None
            )
        # Stop the view
        self.stop()


async def create_a_kingdom(
        guild_id: int,
        author: str,
        kingdom: str,
        region: str,
        password: str,
        government: str,
        alignment: str) -> str:
    try:
        hashed_password = encrypt_password(password)
        async with aiosqlite.connect(f"pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("""select Kingdom FROM KB_Kingdoms where Kingdom = ?""", (kingdom,))
            kingdom_presence = await cursor.fetchone()
            if kingdom_presence is not None:
                return "The kingdom already exists."
            await cursor.execute("""select Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = ?""", (alignment,))
            alignment_type = await cursor.fetchone()
            print(alignment_type)
            if alignment_type is None:
                return "Invalid alignment."
            await cursor.execute("""select Government FROM AA_Government WHERE Government = ?""", (government,))
            government_type = await cursor.fetchone()
            if government_type is None:
                return "Invalid government type."
            if alignment_type is not None and kingdom_presence is None and government_type is not None:
                (economy, loyalty, stability) = alignment_type
                await cursor.execute("""
                INSERT INTO kb_Kingdoms (
                Kingdom, Password, Government, Alignment, Region, Size, Population, 
                Economy, Loyalty, Stability, 
                Fame, Unrest, Consumption,
                Control_DC, Build_Points,
                Stored_seafood, Stored_meat, Stored_grain, Stored_produce
                ) VALUES (
                ?, ?, ?, ?, ?, 0, 0, 
                ?, ?, ?,
                0, 0, 0,
                0, 0,
                0, 0, 0, 0
                )
                """, (kingdom, hashed_password, government, alignment, region, economy, loyalty, stability))
                await cursor.execute(
                    """Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)""",
                    (author, datetime.datetime.now(), "kb_Kingdoms", "Create", f"Created the kingdom of {kingdom}"))
                await cursor.execute(
                    "INSERT Into kb_Kingdoms_Custom(Kingdom, Control_DC, Economy, Loyalty, Stability, Fame, Unrest, Consumption) VALUES (?, 0, 0, 0, 0, 0, 0, 0)",
                    (kingdom,))
                await generate_leadership(kingdom, db)
                await db.commit()
                return f"Congratulations, you have created the kingdom of {kingdom}."

    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error creating a kingdom: {e}")
        return "An error occurred while creating a kingdom."


async def generate_leadership(
        kingdom: str,
        db: aiosqlite.Connection):
    try:
        cursor = await db.cursor()
        await cursor.execute("""
        INSERT INTO kb_Leadership (Kingdom, Title, Character_Name, Stat, Modifier, Economy,  Loyalty, Stability, Unrest)
        SELECT ?, Title, 'Vacant', 0, Null, VPEconomy, VPLoyalty, VPStability, VPUnrest FROM AA_Leadership_Roles
        """, (kingdom,))
        await cursor.execute(
            """SELECT SUM(VPEconomy), SUM(VPLoyalty), SUM(VPStability), SUM(VPUnrest) FROM AA_Leadership_Roles""")
        vp_info = await cursor.fetchone()
        await cursor.execute(
            """UPDATE kb_Kingdoms SET Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ? WHERE Kingdom = ?""",
            (vp_info[0], vp_info[1], vp_info[2], vp_info[3], kingdom))
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error generating leadership: {e}")
        return f"An error occurred while generating leadership. {e}"


async def generate_permissions(
        db: aiosqlite.Connection,
        kingdom: str):
    try:
        cursor = await db.cursor()
        await cursor.execute("""
        INSERT INTO KB_Building_Permits (Kingdom, Building_Name, Building_ID)
        SELECT ?, Building, Building_ID FROM KB_Buildings_Blueprints WHERE Tier = 0
        """, (kingdom,))
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error generating permissions: {e}")
        return f"An error occurred while generating permissions. {e}"


async def edit_a_kingdom(
        guild_id: int,
        author: str,
        old_kingdom_info: KingdomInfo,
        new_kingdom: str,
        government: str,
        alignment: str) -> str:
    try:
        new_kingdom = old_kingdom_info.kingdom if not new_kingdom else new_kingdom
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            if alignment is not None:
                await cursor.execute(
                    """select Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = ?""",
                    (old_kingdom_info.alignment,))
                old_alignment_info = await cursor.fetchone()
                await cursor.execute(
                    """select Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = ?""",
                    (alignment,))
                new_alignment_info = await cursor.fetchone()
                if new_alignment_info is None:
                    return "Invalid alignment."
                old_kingdom_info.economy += new_alignment_info[1] - old_alignment_info[1]
                old_kingdom_info.loyalty += new_alignment_info[2] - old_alignment_info[2]
                old_kingdom_info.stability += new_alignment_info[3] - old_alignment_info[3]
            if government is not None:
                await cursor.execute(
                    "SELECT Government, Corruption, Crime, Law, Lore, Productivity, Society FROM AA_Government WHERE Government = ?",
                    (old_kingdom_info.government,))
                old_government_info = await cursor.fetchone()
                await cursor.execute(
                    "SELECT Government, Corruption, Crime, Law, Lore, Productivity, Society FROM AA_Government WHERE Government = ?",
                    (government,))
                new_government_info = await cursor.fetchone()
                if new_government_info is None:
                    return "Invalid government type."
                (new_government_type, new_corruption, new_crime, new_law, new_lore, new_productivity, new_society) = new_government_info
                (old_government_type, old_corruption, old_crime, old_law, old_lore, old_productivity, old_society) = old_government_info
                sum_corruption = new_corruption - old_corruption
                sum_crime = new_crime - old_crime
                sum_law = new_law - old_law
                sum_lore = new_lore - old_lore
                sum_productivity = new_productivity - old_productivity
                sum_society = new_society - old_society
                await cursor.execute(
                    "UPDATE kb_settlements SET Corruption = Corruption + ?, Crime = Crime + ?, Law = Law + ?, Lore = Lore + ?, Productivity = Productivity + ?, Society = Society + ? WHERE Kingdom = ?",
                    (sum_corruption, sum_crime, sum_law, sum_lore, sum_productivity, sum_society,
                     old_kingdom_info.kingdom))
            await cursor.execute(
                "UPDATE kb_Kingdoms SET Kingdom = ?, Password = ?, Government = ?, Alignment = ?, Economy = ?, Loyalty = ?, Stability = ? WHERE Kingdom = ?",
                (
                    new_kingdom,
                    old_kingdom_info.password,
                    government,
                    alignment,
                    old_kingdom_info.economy,
                    old_kingdom_info.loyalty,
                    old_kingdom_info.stability,
                    old_kingdom_info.kingdom))
            await cursor.execute("UPDATE kb_Kingdoms_Custom SET Kingdom = ? WHERE Kingdom = ?",
                                 (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE kb_settlements SET Kingdom = ? WHERE Kingdom = ?",
                                 (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE kb_settlements_Custom SET Kingdom = ? WHERE Kingdom = ?",
                                 (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE kb_hexes SET Kingdom = ? WHERE Kingdom = ?",
                                 (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE KB_Trade SET Source_Kingdom = ? WHERE Source_Kingdom = ?",
                                 (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE KB_Trade SET End_Kingdom = ? WHERE End_Kingdom = ?",
                                    (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE KB_Buildings_Permits SET Kingdom = ? WHERE Kingdom = ?",
                                    (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE KB_Leadership SET Kingdom = ? WHERE Kingdom = ?",
                                    (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE KB_Armies SET Kingdom = ? WHERE Kingdom = ?",
                                    (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE KB_Events_Active SET Kingdom = ? WHERE Kingdom = ?",
                                    (new_kingdom, old_kingdom_info.kingdom))

            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "kb_Kingdoms", "Edit",
                 f"Edited the kingdom of {old_kingdom_info.kingdom} to {new_kingdom}"))
            await db.commit()
            return f"The kingdom of {old_kingdom_info.kingdom} has been edited to {new_kingdom}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error editing a kingdom: {e}")
        return "An error occurred while editing a kingdom."


async def delete_a_kingdom(
        guild_id: int, author: int, kingdom: str) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("DELETE FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM kb_Kingdoms_Custom WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM kb_settlements WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM kb_settlements_Custom WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM kb_hexes WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM KB_Trade WHERE Source_Kingdom = ? OR End_Kingdom = ?", (kingdom, kingdom))
            await cursor.execute("DELETE FROM KB_Buildings_Permits WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM KB_Leadership WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM KB_Armies WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM KB_Events_Active where Kingdom = ?", (kingdom,))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "kb_Kingdoms", "Delete", f"Deleted the kingdom of {kingdom}"))
            await db.commit()
            return f"The kingdom of {kingdom} has been deleted, its holdings cleared, and its hexes freed."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error deleting a kingdom: {e}")
        return "An error occurred while deleting a kingdom."


async def adjust_bp(
        guild_id: int,
        author: int,
        kingdom: str,
        amount: int,
        apply_unrest: bool = True) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            return_string = f"The build points of {kingdom} have been increased by {amount}."
            await cursor.execute("SELECT Build_Points FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
            kingdom_info = await cursor.fetchone()

            if kingdom_info is None:
                return "The kingdom does not exist."
            if apply_unrest and amount < 0:
                await cursor.execute(
                    "UPDATE kb_Kingdoms SET Unrest = Unrest + ? WHERE Kingdom = ?",
                    (abs(amount), kingdom))
                return_string += f" Unrest has been increased by {abs(amount)}."
            if amount < 0:
                amount = max(amount, -kingdom_info[0])
            await cursor.execute("UPDATE kb_Kingdoms SET Build_Points = Build_Points + ? WHERE Kingdom = ?",
                                 (amount, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "kb_Kingdoms", "Increase BP",
                 f"Increased the build points of {kingdom} by {amount}"))
            await db.commit()

            return return_string
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error increasing build points: {e}")
        return "An error occurred while increasing build points."


"""
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
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Stabilization_Points FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
            kingdom_info = await cursor.fetchone()
            if kingdom_info is None:
                return "The kingdom does not exist."
            if amount < 0:
                amount = min(amount, -kingdom_info[0])
            await cursor.execute(
                "UPDATE kb_Kingdoms SET Stabilization_Points = Stabilization_Points + ? WHERE Kingdom = ?",
                (amount, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "kb_Kingdoms", "Increase SP",
                 f"Increased the stabilization points of {kingdom} by {amount}"))
            await db.commit()
            return f"The stabilization points of {kingdom} have been increased by {amount}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error increasing stabilization points: {e}")
        return "An error occurred while increasing stabilization points."
"""


async def fetch_kingdom(
        guild_id: int,
        kingdom: str) -> typing.Union[KingdomInfo, None]:
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        await cursor.execute(
            """SELECT Kingdom, Password, Government, Alignment, Control_DC, Build_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption FROM kb_Kingdoms WHERE Kingdom = ?""",
            (kingdom,))
        kingdom_info = await cursor.fetchone()
        if kingdom_info is not None:
            return KingdomInfo(*kingdom_info)
        return None


async def fetch_settlement(
        guild_id: int,
        settlement: str) -> typing.Union[SettlementInfo, None]:
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        await cursor.execute(
            """SELECT Kingdom, Settlement, Size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay FROM kb_settlements WHERE Settlement = ?""",
            (settlement,))
        settlement_info = await cursor.fetchone()
        if settlement_info is not None:
            return SettlementInfo(*settlement_info)
        return None


async def fetch_building(
        guild_id: int,
        building: str) -> typing.Union[BuildingInfo, None]:
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        await cursor.execute(
            """SELECT Full_Name, Type, Subtype, Quality, Build_Points, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Settlement_Limit, District_Limit, Description, Upgrade, Discount, Tier FROM kb_Buildings_Blueprints WHERE Full_Name = ? OR Type = ?""",
            (building, building))
        building_info = await cursor.fetchone()
        if building_info is not None:
            return BuildingInfo(*building_info)
        return None


async def fetch_hex_improvement(
        guild_id: int,
        improvement: str) -> typing.Union[HexImprovementInfo, None]:
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        await cursor.execute(
            """SELECT Full_name, Name, Subtype, Quality, Build_Points, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation, Cavernous, Coastline, Desert, Forest, Hills, Jungle, Marsh, Mountains, Plains, Water, Source, Size FROM kb_Hexes_Improvements WHERE Improvement = ?""",
            (improvement,))
        improvement_info = await cursor.fetchone()
        if improvement_info is not None:
            return HexImprovementInfo(*improvement_info)
        return None


async def update_leader(
        guild_id: int,
        author: int,
        kingdom: str,
        title: str,
        player_id: int,
        character_name: str,
        stat: str,
        modifier: int,
        economy: int,
        loyalty: int,
        stability: int
) -> str:
    try:

        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "SELECT Economy, Loyalty, Stability, Unrest FROM kb_Leadership WHERE Kingdom = ? AND Title = ?",
                (kingdom, title))
            leader_info = await cursor.fetchone()
            if leader_info is None:
                return "The leader does not exist."
            (old_economy, old_loyalty, old_stability, old_unrest) = leader_info
            sum_economy = economy - old_economy
            sum_loyalty = loyalty - old_loyalty
            sum_stability = stability - old_stability
            await cursor.execute(
                "UPDATE kb_Leadership Set Character_Name = ?, Player_ID = ?, Stat = ?, Modifier = ?, Economy = ?, Loyalty = ?, Stability = ?, unrest = ? WHERE Kingdom = ? AND Title = ?",
                (character_name, player_id, stat, modifier, economy, loyalty, stability, 0, kingdom, title))
            await cursor.execute(
                "UPDATE kb_Kingdoms SET Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ? WHERE Kingdom = ?",
                (sum_economy, sum_loyalty, sum_stability, -old_unrest, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "kb_Leadership", "Update",
                 f"Updated the leader of {kingdom} to {character_name}"))
            await db.commit()

    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error updating leader: {e}")
        return "An error occurred while updating the leader."


async def remove_leader(
        guild_id: int,
        author: int,
        kingdom: str,
        title: str) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "SELECT Economy, Loyalty, Stability, Unrest FROM kb_Leadership WHERE Kingdom = ? AND Title = ?",
                (kingdom, title))
            leader_info = await cursor.fetchone()
            await cursor.execute(
                "SELECT VPEconomy, VPLoyalty, VPStability, VPUnrest FROM AA_Leadership_Roles WHERE Title = ?", (title,))
            base_info = await cursor.fetchone()
            (base_economy, base_loyalty, base_stability, base_unrest) = base_info
            if leader_info is None:
                return "The leader does not exist."
            (old_economy, old_loyalty, old_stability, old_unrest) = leader_info
            sum_economy = -old_economy + base_economy
            sum_loyalty = -old_loyalty + base_loyalty
            sum_stability = -old_stability + base_stability
            sum_unrest = -old_unrest + base_unrest
            await cursor.execute(
                "UPDATE kb_Leadership SET Character_Name = 'Vacant', Player_ID = Null, Stat = Null, Modifier = Null, Economy = ?, Loyalty = ? , Stability = ?, Unrest = ? WHERE Kingdom = ? AND Title = ?",
                (base_economy, base_loyalty, base_stability, base_unrest, kingdom, title))
            await cursor.execute(
                "UPDATE kb_Kingdoms SET Economy = Economy - ?, Loyalty = Loyalty - ?, Stability = Stability - ?, Unrest = Unrest - ? WHERE Kingdom = ?",
                (sum_economy, sum_loyalty, sum_stability, sum_unrest, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "kb_Leadership", "Remove", f"Removed the leader of {kingdom}"))
            await db.commit()
            return f"The leader of {kingdom} has been removed."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error removing leader: {e}")
        return "An error occurred while removing the leader."


async def claim_hex(
        guild_id: int,
        author: int,
        kingdom: str,
        hex_id: int) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("Update KB_Hexes set Kingdom = ? WHERE Hex_ID = ?", (kingdom, hex_id))
            await cursor.execute(
                "UPDATE kb_Kingdoms SET Size = Size + 1, Control_DC = Control_DC + 1 WHERE Kingdom = ?",
                (kingdom,))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Hexes", "Claim", f"Claimed the hex of {hex_id}"))
            await db.commit()
            return f"The hex of {hex_id} has been claimed by {kingdom}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error claiming hex: {e}")
        return "An error occurred while claiming the hex."


async def relinquish_hex(
        guild_id: int,
        author: int,
        kingdom: str,
        hex_id: int) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("Update kb_hexes set Kingdom = Null WHERE Hex_ID = ? and Kingdom = ?",
                                 (hex_id, kingdom))
            await cursor.execute(
                "UPDATE kb_Kingdoms SET Size = Size - 1, Control_DC = Control_DC - 1 WHERE Kingdom = ?",
                (kingdom,))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Hexes", "relinquish", f"Unclaimed the hex of {hex_id}"))
            await db.commit()
            return f"The hex of {hex_id} has been unclaimed by {kingdom}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error unclaiming hex: {e}")
        return "An error occurred while unclaiming the hex."


async def add_an_improvement(
        guild_id: int,
        hex_id: int,
        kingdom: str,
        improvement: str,
        amount: int,
        build_points: int,
        kingdom_size: int,
        iscost: bool = True
) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Kingdom, Hex_Terrain, Farm, Ore, Stone, Wood FROM KB_Hexes WHERE ID = ?",
                                 (hex_id,))
            base_hex_info = await cursor.fetchone()
            if not base_hex_info:
                return f"The hex terrain of {hex_id} does not exist."
            if base_hex_info['Kingdom'] != kingdom:
                return f"The hex terrain of {hex_id} is not in the kingdom of {kingdom}."
            await cursor.execute(
                """SELECT Full_name, Type, Subtype, Quality, Build_Points, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation, Cavernous, Coastline, Desert, Forest, Hills, Jungle, Marsh, Mountains, Plains, Water, Source, Size FROM kb_Hexes_Improvements WHERE full_name = ?""",
                (improvement,))
            improvement_info = await cursor.fetchone()
            if not improvement_info:
                return f"The improvement of {improvement} does not exist."
            if improvement_info[f'{base_hex_info["Hex_Terrain"]}'] == 0:
                return f"The improvement of {improvement} cannot be built on {base_hex_info['Hex_Terrain']}."
            if improvement_info['Size'] > kingdom_size:
                return f"The improvement of {improvement} requires a kingdom size of {improvement_info['Size']} or greater."
            await cursor.execute("Select Sum(Amount) From KB_Hexes_Constructed where Type = ? and Hex_ID = ?",
                                 (improvement_info['Type'], hex_id))
            constructed = await cursor.fetchone()
            constructed = constructed[0] if constructed[0] else 0
            if constructed >= base_hex_info['Type']:
                return f"The improvement of {improvement} has reached its maximum amount. \r\nIf it is a farm You may want to convert an existing improvement to a different type."
            await cursor.execute("SELECT Amount FROM kb_hexes_constructed WHERE full_name = ? and Improvement = ?",
                                 (improvement, hex_id))
            availability = await cursor.fetchone()
            if iscost:
                cost_modifier = improvement_info['Build_Points'] * improvement_info[f'{base_hex_info["Hex_Terrain"]}']
                max_amount = min(base_hex_info[f'{improvement_info["Type"]}'] - constructed, amount,
                                 build_points // cost_modifier)
                build_cost = max_amount * cost_modifier
            else:
                max_amount = min(base_hex_info[f'{improvement_info["Type"]}'] - constructed, amount)
                build_cost = 0
            await cursor.execute(
                "Update Kingdoms Set Build_Points = Build_Points - ?, economy = economy + ?, Loyalty = loyalty + ?, Stability = stability + ?, Unrest = unrest + ? WHERE Kingdom = ?",
                (build_cost, improvement_info['Economy'] * max_amount, improvement_info['Loyalty'] * max_amount,
                 improvement_info['Stability'] * max_amount, improvement_info['Unrest'] * max_amount, kingdom))
            if not availability:
                await cursor.execute("""
                INSERT into KB_Hexes_Constructed(ID, Full_Name, Type, Subtype, Quality, Amount, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation) 
                VALUES 
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (hex_id, improvement_info['Full_name'], improvement_info['Type'], improvement_info['Subtype'],
                      improvement_info['Quality'], max_amount, improvement_info['Economy'], improvement_info['Loyalty'],
                      improvement_info['Stability'], improvement_info['Unrest'], improvement_info['Consumption'],
                      improvement_info['Defence'], improvement_info['Taxation']))
            else:
                await cursor.execute(
                    "UPDATE kb_hexes_constructed SET Amount = Amount + ? WHERE Full_Name = ? and ID = ?",
                    (max_amount, improvement, hex_id))
            await cursor.execute("UPDATE kb_Kingdoms_Custom SET Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ? WHERE Kingdom = ?",
                                    (improvement_info['Economy'] * max_amount, improvement_info['Loyalty'] * max_amount,
                                    improvement_info['Stability'] * max_amount, improvement_info['Unrest'] * max_amount, kingdom))
            return f"The improvement of {improvement} has been added to the hex of {hex_id}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error adding improvement: {e}")
        return f"An error occurred while adding the improvement. {e}"


async def remove_improvement(
        guild_id: int,
        author: int,
        kingdom: str,
        hex_information: HexImprovementInfo,
        hex_id: int,
        amount: int
) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "SELECT Amount FROM kb_hexes_constructed WHERE ID = ? and Full_Name = ?",
                (hex_id, hex_information.full_name))
            availability = await cursor.fetchone()
            if not availability:
                return f"Hex {hex_id} has no the improvements of {hex_information.improvement}."
            amount = min(amount, availability[0])
            if availability[0] == amount:
                await cursor.execute(
                    "DELETE FROM kb_hexes WHERE Hex_Terrain = ? and Improvement = ?",
                    (hex_id, hex_information.full_name))
            else:
                await cursor.execute(
                    "UPDATE kb_hexes SET Amount = Amount - ? WHERE ID = ? and Full_Name = ?",
                    (amount, hex_id, hex_information.full_name))
            await cursor.execute(
                "Update kb_Kingdoms SET size = size - ?, Economy = Economy - ?, Loyalty = Loyalty - ?, Stability = Stability - ?, Unrest = Unrest - ? WHERE Kingdom = ?",
                (amount, amount * hex_information.economy, amount * hex_information.loyalty,
                 amount * hex_information.stability, amount * hex_information.unrest,
                 hex_information.consumption, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Hexes", "Remove Improvement",
                 f"Removed the improvement of {hex_information.improvement} from the hex of {hex_id}"))
            await db.commit()
            return f"The improvement of {hex_information.improvement} has been removed from the hex of {hex_id}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error removing improvement: {e}")
        return "An error occurred while removing the improvement."


async def repurpose_an_improvement(
        guild_id: int,
        hex_id: int,
        old_full_name: str,
        new_full_name: str,
        amount: int):
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("Select Amount from KB_Hexes_Constructed where Full_Name = ? and id = ?",
                                 (old_full_name, hex_id))
            availability = await cursor.fetchone()
            if not availability:
                return f"No improvements of {old_full_name} are present."
            amount = min(amount, availability[0])
            await cursor.execute("Select Full_Name from KB_Hexes_Improvements where Full_Name = ? and id = ?",
                                 (new_full_name, hex_id))
            new_improvement = await cursor.fetchone()
            if not new_improvement:
                return f"No improvements of {new_full_name} are present."
            await cursor.execute("Select Amount from KB_Hexes_Constructed where Full_Name = ?", (new_full_name,))
            new_availability = await cursor.fetchone()
            if availability[0] == amount and not new_availability:
                await cursor.execute("UPDATE KB_Hexes_Constructed set Full_Name = ? where Full_Name = ? and id = ?",
                                     (new_full_name, old_full_name, hex_id))
            elif availability[0] == amount and new_availability:
                await cursor.execute(
                    "UPDATE KB_Hexes_Constructed set Amount = Amount + ? where Full_Name = ? and id = ?",
                    (amount, new_full_name, hex_id))
                await cursor.execute("DELETE from KB_Hexes_Constructed where Full_Name = ? and id = ?",
                                     (old_full_name, hex_id))
            elif availability[0] != amount and not new_availability:
                await cursor.execute(
                    "UPDATE KB_Hexes_Constructed set Amount = Amount - ? where Full_Name = ? and id = ?",
                    (amount, old_full_name, hex_id))
                await cursor.execute("""INSERT into KB_Hexes_Constructed (ID, Full_Name, Type, Subtype, Quality, Amount, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation)
                SELECT ?, full_name, Type, Subtype, Quality, ?, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation FROM KB_Hexes_Improvements where Full_Name = ?""",
                                     (hex_id, amount, new_full_name))
            else:
                await cursor.execute(
                    "UPDATE KB_Hexes_Constructed set Amount = Amount + ? where Full_Name = ? and id = ?",
                    (amount, new_full_name, hex_id))
                await cursor.execute(
                    "UPDATE KB_Hexes_Constructed set Amount = Amount - ? where Full_Name = ? and id = ?",
                    (amount, old_full_name, hex_id))
            await db.commit()
            return f"{amount} improvements of {old_full_name} have been repurposed to {new_full_name}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error repurposing improvement: {e}")
        return "An error occurred while repurposing the improvement."


async def add_building(
        guild_id: int,
        author: int,
        kingdom: str,
        settlement: str,
        building_info: BuildingInfo,
        size: int,
        amount) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Building FROM Buildings WHERE Building = ? and Settlement = ?",
                                 (building_info.building, settlement))
            building_presence = await cursor.fetchone()
            if not building_presence:
                await cursor.execute(
                    """INSERT INTO Buildings (
                    Kingdom, Settlement, 
                    Full_Name, Type, Subtype, Constructed, Lots, 
                    Economy, Loyalty, Stability, 
                    Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, 
                    Danger, Defence, Base_Value, Spellcasting, Supply, Discounted) 
                    VALUES 
                    (?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, 0)""",
                    (kingdom, settlement,
                     building_info.full_name, building_info.type, building_info.subtype, amount, building_info.lots,
                     building_info.economy, building_info.loyalty, building_info.stability,
                     building_info.fame, building_info.unrest, building_info.corruption, building_info.crime,
                     building_info.productivity, building_info.law, building_info.lore, building_info.society,
                     building_info.danger, building_info.defence, building_info.base_value, building_info.spellcasting,
                     building_info.supply))
            else:
                await cursor.execute(
                    "Update Buildings Set Constructed = Constructed + ? WHERE Building = ? and Settlement = ?",
                    (amount, building_info.full_name, settlement))
            new_population_adjustment = amount * building_info.lots * 250
            new_lots_adjustment = amount * building_info.lots
            new_dc_adjustment = math.floor((size + new_lots_adjustment) / 36) - math.floor(size / 36)
            await cursor.execute(
                "Update kb_Kingdoms Set Control_DC = Control_DC + ?, population = population + ?, Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ? WHERE Kingdom = ?",
                (new_dc_adjustment, new_population_adjustment, building_info.economy, building_info.loyalty,
                 building_info.stability, building_info.unrest, kingdom))
            await cursor.execute(
                "Update kb_settlements set size = size + ?, population = population + ?, Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ? WHERE Settlement = ?",
                (new_lots_adjustment, new_population_adjustment, building_info.economy, building_info.loyalty,
                 building_info.stability, building_info.unrest, settlement))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Buildings", "Add",
                 f"Added the building of {building_info.full_name} to the settlement of {settlement}"))
            await db.commit()
            return f"{amount} building(s) of {building_info.building} have been added. Costing {building_info.build_points * amount} build points."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error adding building: {e}")
        return "An error occurred while adding the building."


async def remove_building(
        guild_id: int,
        author: int,
        kingdom: str,
        settlement: str,
        building_info: BuildingInfo,
        size: int,
        amount) -> tuple[str, int]:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Constructed FROM Buildings WHERE Building = ? and Settlement = ?",
                                 (building_info.building, settlement))
            building_presence = await cursor.fetchone()
            if not building_presence:
                return f"No buildings of {building_info.building} are present in the settlement of {settlement}.", 0
            built = building_presence[0]
            amount = min(int(built), amount)
            if amount == built:
                await cursor.execute("DELETE FROM Buildings WHERE Building = ? and Settlement = ?",
                                     (building_info.building, settlement))
            else:
                await cursor.execute(
                    "Update Buildings Set Constructed = Constructed - ? WHERE Building = ? and Settlement = ?",
                    (amount, building_info.building, settlement))
            new_population_adjustment = amount * building_info.lots * 250
            new_lots_adjustment = amount * building_info.lots
            new_dc_adjustment = math.floor((size - new_lots_adjustment) / 36) - math.floor(size / 36)
            await cursor.execute(
                "Update kb_Kingdoms Set Control_DC = Control_DC - ?, population = population - ?, Economy = Economy - ?, Loyalty = Loyalty - ?, Stability = Stability - ?, Unrest = Unrest - ? WHERE Kingdom = ?",
                (new_dc_adjustment, new_population_adjustment, building_info.economy, building_info.loyalty,
                 building_info.stability, building_info.unrest, kingdom))
            await cursor.execute(
                "Update kb_settlements set size = size - ?, population = population - ?, Economy = Economy - ?, Loyalty = Loyalty - ?, Stability = Stability - ?, Unrest = Unrest - ? WHERE Settlement = ?",
                (new_lots_adjustment, new_population_adjustment, building_info.economy, building_info.loyalty,
                 building_info.stability, building_info.unrest, settlement))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Buildings", "Remove",
                 f"Removed the building of {building_info.building} from the settlement of {settlement}"))
            await db.commit()
            return f"{amount} building(s) of {building_info.building} have been removed. Refunding {(building_info.build_points * amount) * .5} build points.", amount
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error removing building: {e}")
        return "An error occurred while removing the building.", 0


async def claim_a_settlement(
        guild_id: int,
        author: int,
        kingdom: str,
        settlement: str,
        hex_id: int) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()

            await cursor.execute(
                "INSERT INTO kb_settlements (Kingdom, Settlement, Size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay, hex_id) VALUES (?, ?, 1, 250, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ?)",
                (kingdom, settlement, hex_id))
            await cursor.execute(
                "INSERT INTO kb_settlements_Custom (Kingdom, Settlement, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply) VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)",
                (kingdom, settlement))
            await cursor.execute("UPDATE kb_Kingdoms SET Control_DC = Control_DC + 1 WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("UPDATE KB_Hexes set IsTown = 1 WHERE ID = ?", (hex_id,))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "kb_settlements", "Claim", f"Claimed the settlement of {settlement}"))
            await db.commit()
            return f"The settlement of {settlement} has been claimed by {kingdom}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error claiming settlement: {e}")
        return "An error occurred while claiming the settlement."


async def relinquish_settlement(
        guild_id: int,
        author: int,
        kingdom: str,
        settlement: str) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Kingdom, Hex_ID FROM kb_settlements WHERE Settlement = ?", (settlement,))
            settlement_info = await cursor.fetchone()
            if settlement_info is None:
                return "The settlement is not claimed."
            await cursor.execute(
                "SELECT Building, Constructed, Lots, Economy, Loyalty, Stability, Unrest FROM Buildings WHERE Kingdom = ? and Settlement = ?",
                (kingdom, settlement))
            building_info = await cursor.fetchall()
            control_dc_lots = 0
            for building in building_info:
                (building, constructed, lots, economy, loyalty, stability, unrest) = building
                population_adjustment = lots * 250 * constructed
                control_dc_lots += lots * constructed
                await cursor.execute(
                    "UPDATE kb_Kingdoms SET Population = population - ?, Economy = Economy - ?, Loyalty = Loyalty - ?, Stability = Stability - ?, Unrest = Unrest - ? WHERE Kingdom = ?",
                    (population_adjustment, economy * constructed, loyalty * constructed, stability * constructed,
                     unrest * constructed, kingdom))
            control_dc = math.floor(control_dc_lots / 36)
            await cursor.execute("DELETE FROM Buildings WHERE Kingdom = ? and Settlement = ?", (kingdom, settlement))
            await cursor.execute("DELETE FROM kb_settlements WHERE Settlement = ?", (settlement,))
            await cursor.execute("DELETE FROM kb_settlements_Custom WHERE Settlement = ?", (settlement,))
            await cursor.execute("UPDATE KB_Hexes set IsTown = 0 WHERE ID = ?", (settlement_info[1],))
            await cursor.execute("UPDATE kb_Kingdoms SET Control_DC = Control_DC - 1 - ? WHERE Kingdom = ?",
                                 (control_dc, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "kb_settlements", "relinquish",
                 f"Unclaimed the settlement of {settlement}"))
            await db.commit()
            return f"The settlement of {settlement} has been unclaimed by {kingdom}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error unclaiming settlement: {e}")
        return "An error occurred while unclaiming the settlement."


class KingdomCommands(commands.Cog, name='kingdom'):
    def __init__(self, bot):
        self.bot = bot

    kingdom_group = discord.app_commands.Group(
        name='kingdom',
        description='Commands related to kingdom management'
    )

    leadership_group = discord.app_commands.Group(
        name='leadership',
        description='Commands related to Leadership management',
        parent=kingdom_group
    )

    hex_group = discord.app_commands.Group(
        name='hex',
        description='Commands related to hex management',
        parent=kingdom_group
    )

    settlement_group = discord.app_commands.Group(
        name='settlement',
        description='Commands related to settlement management',
        parent=kingdom_group
    )

    @kingdom_group.command(name="create", description="Create a kingdom")
    @app_commands.autocomplete(government=government_autocompletion)
    @app_commands.autocomplete(alignment=alignment_autocomplete)
    @app_commands.autocomplete(region=shared_functions.region_autocomplete)
    async def create(
            self,
            interaction: discord.Interaction,
            kingdom: str,
            password: str,
            region: str,
            government: str,
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
                region=region,
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
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("""select Kingdom, Password FROM kb_Kingdoms where Kingdom = ?""", (kingdom,))
                result = await cursor.fetchone()
                if result is None:
                    status = f"the kingdom which you have elected to make a war crime out of couldn't be found."
                    await interaction.followup.send(content=status)
                    return
                valid_password = validate_password(password, result[1])
                if valid_password:
                    status = await delete_a_kingdom(guild_id=interaction.guild_id, author=interaction.user.id,
                                                    kingdom=kingdom)
                    await interaction.followup.send(content=status)
                else:
                    status = f"You have entered an invalid password for this kingdom."
                    await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error deleting a kingdom: {e}")
            await interaction.followup.send(content="An error occurred while deleting a kingdom.")

    @kingdom_group.command(name="edit", description="Modify a kingdom")
    @app_commands.autocomplete(old_kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(new_government=government_autocompletion)
    @app_commands.autocomplete(new_alignment=alignment_autocomplete)
    async def edit(
            self,
            interaction: discord.Interaction,
            old_kingdom: str,
            new_kingdom: typing.Optional[str],
            old_password: typing.Optional[str],
            new_password: typing.Optional[str],
            new_government: typing.Optional[str],
            new_alignment: typing.Optional[str]):
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
            kingdom_info.password = new_password if new_password else kingdom_info.password
            status = await edit_a_kingdom(
                guild_id=interaction.guild_id,
                author=interaction.user.name,
                old_kingdom_info=kingdom_info,
                new_kingdom=new_kingdom,
                government=new_government,
                alignment=new_alignment)
            await interaction.followup.send(content=status)
            if new_password:
                new_password = encrypt_password(new_password)
                async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                    cursor = await db.cursor()
                    await cursor.execute("UPDATE kb_Kingdoms SET Password = ? WHERE Kingdom = ?",
                                         (new_password, old_kingdom))
                    await db.commit()
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error fetching kingdom: {e}")
            await interaction.followup.send(content="An error occurred while fetching kingdom.")
            return

    @kingdom_group.command(name="build_points", description="Adjust the build points of a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def bp(
            self,
            interaction: discord.Interaction,
            kingdom: str,
            password: str,
            character_name: str,
            amount: int):
        """This modifies the number of build points in a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, Build_Points FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute(
                    "SELECT Gold, Gold_Value, Gold_Value_Max, Level, Oath, Thread_ID FROM Player_Characters WHERE Player_ID = ? AND (Character_Name = ? OR Nickname = ?)",
                    (interaction.user.id, character_name, character_name))
                character_info = await cursor.fetchone()
                if not character_info:
                    await interaction.followup.send(content=f"The character of {character_name} does not exist.")
                    return
                (gold, gold_value, gold_value_max, level, oath, thread_id) = character_info
                if amount < 0:
                    bought_points = max(amount, -kingdom_results[1])
                    cost = bought_points * 4000
                    gold_reward = await character_commands.gold_calculation(
                        guild_id=interaction.guild_id,
                        author_name=interaction.user.name,
                        author_id=interaction.user.id,
                        character_name=character_name,
                        level=character_info[3],
                        oath=character_info[4],
                        gold=Decimal(gold),
                        gold_value=Decimal(gold_value),
                        gold_value_max=Decimal(gold_value_max),
                        gold_change=Decimal(cost),
                        reason="selling build points",
                        source="Adjust BP Commands",
                        gold_value_change=Decimal(cost),
                        gold_value_max_change=Decimal(cost),
                        is_transaction=False
                    )
                    await adjust_bp(interaction.guild_id, interaction.user.id, kingdom, bought_points)

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
                    await shared_functions.log_embed(
                        bot=self.bot,
                        thread=character_info[5],
                        guild=interaction.guild,
                        change=update_character_log)
                    await shared_functions.character_embed(guild=interaction.guild, character_name=character_name)
                    await interaction.followup.send(
                        content=f"The character of {character_name} has sold {bought_points} build points for {gold_reward[0]} GP.")
                else:
                    maximum_points = math.floor(character_info[0] / 4000)
                    bought_points = min(amount, maximum_points)
                    cost = bought_points * 4000
                    adjusted_bp_result = await adjust_bp(
                        interaction.guild_id,
                        interaction.user.id,
                        kingdom,
                        bought_points)
                    gold_used = await character_commands.gold_calculation(
                        guild_id=interaction.guild_id,
                        author_name=interaction.user.name,
                        author_id=interaction.user.id,
                        character_name=character_name,
                        level=character_info[3],
                        oath=character_info[4],
                        gold=Decimal(gold),
                        gold_value=Decimal(gold_value),
                        gold_value_max=Decimal(gold_value_max),
                        gold_change=-Decimal(cost),
                        reason="selling build points",
                        source="Adjust BP Commands",
                        gold_value_change=-Decimal(cost),
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
                    await shared_functions.log_embed(
                        bot=self.bot,
                        thread=character_info[5],
                        guild=interaction.guild,
                        change=update_character_log)
                    await shared_functions.character_embed(
                        guild=interaction.guild,
                        character_name=character_name)
                    await interaction.followup.send(adjusted_bp_result)
        except (aiosqlite, TypeError, ValueError, character_commands.CalculationAidFunctionError) as e:
            logging.exception(f"Error increasing build points: {e}")
            await interaction.followup.send(content="An error occurred while increasing build points.")

    @leadership_group.command(name="modify",
                              description="Modify a leader, by changing their ability score or who is in charge")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(title=leadership_autocomplete)
    @app_commands.autocomplete(character_name=shared_functions.character_select_autocompletion)
    async def modify_leadership(self, interaction: discord.Interaction, kingdom: str, password: str,
                                character_name: str, title: str,
                                modifier: int):
        """This command is used to modify a leader's ability score or who is in charge of a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, Size FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("Select Player_ID, Character_Name from Player_Characters where Character_Name = ?",
                                     (character_name,))
                recipient = await cursor.fetchone()
                recipient_id = recipient[0]
                await cursor.execute(
                    "SELECT Ability, Economy, Loyalty, Stability FROM AA_Leadership_Roles WHERE Title = ?",
                    (title,))
                leadership_info = await cursor.fetchone()
                (ability, economy, loyalty, stability) = leadership_info
                abilities = ability.split(" / ")
                options = [
                    discord.SelectOption(label=ability) for ability in abilities
                ]

                additional = 1
                if title == "Ruler":
                    additional = 1 if kingdom_results[1] < 26 else 2
                    additional = 3 if kingdom_results[1] > 101 else additional
                print(additional, economy, loyalty, stability)
                view = LeadershipView(
                    options, interaction.guild_id, interaction.user.id, kingdom, title, character_name,
                    additional, economy, loyalty, stability, kingdom_results[1], modifier=modifier,
                    recipient_id=recipient_id)

                await interaction.followup.send("Please select an attribute:", view=view)
            # Store the message object
            view.message = await interaction.original_response()
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error modifying  Leadership: {e}")
            await interaction.followup.send(content="An error occurred while modifying  Leadership.")

    @leadership_group.command(name="remove", description="Remove a leader from a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(title=leadership_autocomplete)
    async def remove(self, interaction: discord.Interaction, kingdom: str, password: str, title: str):
        """This command is used to remove a leader and make it a vacant position"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                status = await remove_leader(interaction.guild_id, interaction.user.id, kingdom, title)
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error removing leader: {e}")
            await interaction.followup.send(content="An error occurred while removing the leader.")

    @hex_group.command(name="claim", description="Claim a hex for a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    async def claim(self, interaction: discord.Interaction, kingdom: str, password: str, hex_id: int):
        """This command is used to claim a hex for a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, Region FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("SELECT Kingdom, Region FROM KB_Hexes WHERE ID = ?", (hex_id,))
                hex_results = await cursor.fetchone()
                if not hex_results:
                    await interaction.followup.send(content=f"The hex of {hex_id} does not exist.")
                    return
                elif hex_results[0]:
                    await interaction.followup.send(
                        content=f"The hex of {hex_id} is already claimed by {hex_results[0]}.")
                    return
                elif hex_results[1] != kingdom_results[1]:
                    await interaction.followup.send(
                        content=f"The hex of {hex_id} is not in the kingdom's region of {kingdom_results[1]}.")
                    return
                status = await claim_hex(guild_id=interaction.guild_id, author=interaction.user.id, kingdom=kingdom,
                                         hex_id=hex_id)
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error claiming hex: {e}")
            await interaction.followup.send(content="An error occurred while claiming a hex.")

    @hex_group.command(name="relinquish", description="relinquish a hex for a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    async def relinquish_hex(self, interaction: discord.Interaction, kingdom: str, password: str, hex_id: int):
        """This command is used to relinquish a hex for a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("SELECT Hex_ID FROM KB_Hexes WHERE Hex_ID = ? and Kingdom = ?", (hex_id, kingdom))
                hex_results = await cursor.fetchone()
                if not hex_results:
                    await interaction.followup.send(content=f"The hex terrain of {hex_id} does not exist.")
                    return
                status = await relinquish_hex(interaction.guild_id, interaction.user.id, kingdom, hex_id)
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error unclaiming hex: {e}")
            await interaction.followup.send(content="An error occurred while unclaiming a hex.")

    @hex_group.command(name="improve", description="Add an improvement to a hex")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(improvement=hex_improvement_autocomplete)
    async def add_improvement(
            self,
            interaction: discord.Interaction,
            kingdom: str,
            password: str,
            hex_id: int,
            improvement: str,
            amount: int):
        """This command is used to add an improvement to a hex"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, Build_Points, Size FROM kb_Kingdoms WHERE Kingdom = ?",
                                     (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results['Password'])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return

                status = await add_an_improvement(
                    guild_id=interaction.guild_id,
                    hex_id=hex_id,
                    kingdom=kingdom,
                    improvement=improvement,
                    amount=amount,
                    build_points=kingdom_results['Build_Points'],
                    kingdom_size=kingdom_results['Size']
                )
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error adding improvement: {e}")
            await interaction.followup.send(content="An error occurred while adding an improvement.")

    @hex_group.command(name="degrade", description="Remove an improvement from a hex")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(hex_terrain=hex_terrain_autocomplete)
    @app_commands.autocomplete(improvement=hex_improvement_autocomplete)
    async def remove_improvement(
            self,
            interaction: discord.Interaction,
            kingdom: str,
            password: str,
            hex_terrain: str,
            improvement: str):
        """This command is used to remove an improvement from a hex"""
        await interaction.response.defer(thinking=True)
        try:
            async with (aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite")) as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                hex_information = await fetch_hex_improvement(interaction.guild_id, improvement)
                if not hex_information:
                    await interaction.followup.send(content=f"The improvement of {improvement} does not exist.")
                    return
                status = await remove_improvement(interaction.guild_id, interaction.user.id, kingdom, hex_information,
                                                  hex_terrain)
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error removing improvement: {e}")
            await interaction.followup.send(content="An error occurred while removing an improvement.")

    @hex_group.command(name='repurpose', description='Change the behavior of an improvement')
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(original_purpose=improvement_subtype_autocomplete)
    @app_commands.autocomplete(new_purpose=improvement_subtype_autocomplete)
    async def repurpose_improvement(
            self,
            interaction: discord.Interaction,
            hex_id: int,
            kingdom: str,
            original_purpose: str,
            new_purpose: str,
            password: str,
            amount: int):
        """This command is used to repurpose an improvement in a hex"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                status = await repurpose_an_improvement(
                    guild_id=interaction.guild_id,
                    hex_id=hex_id,
                    new_full_name=new_purpose,
                    old_full_name=original_purpose,
                    amount=amount
                )
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error repurposing improvement: {e}")
            await interaction.followup.send(content="An error occurred while repurposing an improvement.")

    @settlement_group.command(name="claim", description="Claim a settlement for a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    async def claim_settlement(self, interaction: discord.Interaction, kingdom: str, password: str, settlement: str,
                               hex_id: int):
        """This command is used to claim a settlement for a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return

                await cursor.execute("SELECT Kingdom FROM kb_settlements WHERE Settlement = ?", (settlement,))
                settlement_info = await cursor.fetchone()
                if settlement_info is not None:
                    await interaction.followup.send(content="A settlement with this name is already claimed.")
                await cursor.execute("SELECT ID, IsTown from KB_Hexes where ID = ?", (hex_id,))
                hex_results = await cursor.fetchone()
                if not hex_results:
                    await interaction.followup.send(content=f"The hex of {hex_id} does not exist.")
                    return
                if hex_results[1]:
                    await interaction.followup.send(content="The hex is already a town.")
                    return
                await cursor.execute("Select Count(Full_Name) from KB_Hexes_Constructed Where ID = ?", (hex_id,))
                improvements = await cursor.fetchone()
                if improvements[0] > 0:
                    await interaction.followup.send(
                        content="The hex has improvements built upon it and cannot share them with a settlement!")
                    return
                status = await claim_a_settlement(interaction.guild_id, interaction.user.id, kingdom, settlement,
                                                  hex_id)
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error claiming settlement: {e}")
            await interaction.followup.send(content="An error occurred while claiming a settlement.")

    @settlement_group.command(name="relinquish", description="relinquish a settlement for a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(settlement=settlement_autocomplete)
    async def relinquish_settlement(self, interaction: discord.Interaction, kingdom: str, password: str,
                                    settlement: str):
        """This command is used to relinquish a settlement for a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
            status = await relinquish_settlement(interaction.guild_id, interaction.user.id, kingdom, settlement)
            await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error unclaiming settlement: {e}")
            await interaction.followup.send(content="An error occurred while unclaiming a settlement.")

    @settlement_group.command(name="build", description="Build a building in a settlement")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(settlement=settlement_autocomplete)
    @app_commands.autocomplete(building=blueprint_autocomplete)
    async def build_building(self, interaction: discord.Interaction, kingdom: str, password: str, settlement: str,
                             building: str, amount: int):
        """This command is used to build a building in a settlement"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, bp FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("Select Size from kb_settlements where Settlement = ?", (settlement,))
                settlement_info = await cursor.fetchone()
                if settlement_info is None:
                    await interaction.followup.send(content="The settlement is not claimed.")
                    return

                await cursor.execute("SELECT Kingdom from KB_Buildings_Permits where Kingdom = ? AND Building_Name = ?",
                                     (kingdom, building))
                permits = await cursor.fetchone()
                if permits is None:
                    await interaction.followup.send(content="The kingdom does not have a permit for this building.")
                    return
                building_info = await fetch_building(interaction.guild_id, building)
                cost = building_info.build_points * amount
                await cursor.execute(
                    "SELECT SUM(Amount * Quality) from KB_Buildings where Kingdom = ? and Settlement = ? and Subtype = 'Housing'",
                    (kingdom, settlement))
                supply = await cursor.fetchone()
                if settlement_info[0] + (amount * building_info.supply) > supply[0]:
                    await interaction.followup.send(
                        content=f"The settlement does not have enough housing. it has {supply[0]} and needs {settlement_info[0] + (amount * building_info.supply)}.")
                    return
                await cursor.execute("""
                SELECT Build.Full_Name, sum(Build.amount), sum(Build.discounted) from KB_Buildings Build 
                left join KB_Buildings_Blueprints Blue on Blue.Full_Name = Build.Full_Name 
                where Build.Kingdom = ? and Build.Settlement = ? and Build.Full_Name = ? and Blue.discount like ?
                group by Build.Full_Name""", (kingdom, settlement, building, f"%{building_info.type}%"))
                discount_info = await cursor.fetchall()
                discount_count = amount
                for discount in discount_info:
                    (full_name, amount_built, discounted) = discount
                    discountable = amount_built - discounted
                    discounted_change = min(discountable, discount_count)
                    discount_count -= min(discountable, discount_count)
                    await cursor.execute(
                        "UPDATE KB_Buildings SET Discounted = Discounted + ? WHERE Kingdom = ? and Settlement = ? and Full_Name = ?",
                        (discounted_change, kingdom, settlement, full_name))
                    if discount_count == 0:
                        break
                cost -= building_info.build_points * .5 * (amount - discount_count)
                if cost > kingdom_results[1]:
                    await interaction.followup.send(
                        content=f"The kingdom does not have enough build points. it has {kingdom_results[1]} and needs {cost}.")
                    return
                await cursor.execute("UPDATE kb_Kingdoms SET bp = bp - ? WHERE Kingdom = ?", (cost, kingdom))
                await db.commit()

                status = await add_building(guild_id=interaction.guild_id, author=interaction.user.id, kingdom=kingdom,
                                            settlement=settlement, building_info=building_info, amount=amount,
                                            size=settlement_info[0])
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error building building: {e}")
            await interaction.followup.send(content="An error occurred while building a building.")

    @settlement_group.command(name="destroy", description="Destroy a building in a settlement")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(settlement=settlement_autocomplete)
    @app_commands.autocomplete(building=blueprint_autocomplete)
    async def destroy_building(self, interaction: discord.Interaction, kingdom: str, password: str, settlement: str,
                               building: str, amount: int):
        """This command is used to destroy a building in a settlement"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, BP FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("Select Size from kb_settlements where Settlement = ?", (settlement,))
                settlement_info = await cursor.fetchone()
                if not settlement_info:
                    await interaction.followup.send(content="The settlement is not claimed.")
                    return
                building_info = await fetch_building(interaction.guild_id, building)
                status = await remove_building(guild_id=interaction.guild_id, author=interaction.user.id,
                                               kingdom=kingdom, settlement=settlement, building_info=building_info,
                                               amount=amount, size=settlement_info[0])
                bp_return = (building_info.build_points * status[1]) * .5
                await cursor.execute("UPDATE kb_Kingdoms SET BP = BP + ? WHERE Kingdom = ?", (bp_return, kingdom))
                await interaction.followup.send(content=status[0])
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error destroying building: {e}")
            await interaction.followup.send(content="An error occurred while destroying a building.")

    @settlement_group.command(name="upgrade", description="upgrade a building in a settlement")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(settlement=settlement_autocomplete)
    @app_commands.autocomplete(building=blueprint_upgrade_autocomplete)
    async def upgrade_building(
            self, interaction: discord.Interaction, kingdom: str, password: str, settlement: str,
            building: str, amount: int):
        """This command is used to upgrade a building in a settlement"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, BP FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute(
                    "Select Amount from KB_Buildings where Kingdom = ? and Settlement = ? and Full_Name = ?",
                    (kingdom, settlement, building))
                settlement_info = await cursor.fetchone()
                if not settlement_info:
                    await interaction.followup.send(content=f"Settlement of {settlement} has no {building}s built!")
                    return
                amount = min(amount, settlement_info[0])
                old_building_info = await fetch_building(interaction.guild_id, building)
                new_building_info = await fetch_building(interaction.guild_id, old_building_info.upgrade)
                cost = (new_building_info.build_points - old_building_info.build_points) * amount
                if cost > kingdom_results[1]:
                    await interaction.followup.send(
                        content=f"The kingdom does not have enough build points. it has {kingdom_results[1]} and needs {cost}.")
                    return
                await cursor.execute("UPDATE kb_Kingdoms SET BP = BP - ? WHERE Kingdom = ?", (cost, kingdom))
                await remove_building(guild_id=interaction.guild_id, author=interaction.user.id, kingdom=kingdom,
                                      settlement=settlement, building_info=old_building_info, amount=amount)
                status = await add_building(guild_id=interaction.guild_id, author=interaction.user.id, kingdom=kingdom,
                                            settlement=settlement, building_info=new_building_info, amount=amount,
                                            size=settlement_info[0])
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error upgrading building: {e}")
            await interaction.followup.send(content="An error occurred while upgrading a building.")

    @settlement_group.command(name="repurpose", description="Change the behavior of a building")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(settlement=settlement_autocomplete)
    @app_commands.autocomplete(old_purpose=blueprint_repurpose_autocomplete)
    @app_commands.autocomplete(new_purpose=blueprint_repurpose_autocomplete)
    async def repurpose_building(
            self, interaction: discord.Interaction, kingdom: str, password: str, settlement: str,
            old_purpose: str, new_purpose: str, amount: int):
        """This command is used to repurpose a building in a settlement"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, BP FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute(
                    "Select Amount from KB_Buildings where Kingdom = ? and Settlement = ? and Full_Name = ?",
                    (kingdom, settlement, old_purpose))
                settlement_info = await cursor.fetchone()
                if not settlement_info:
                    await interaction.followup.send(
                        content=f"Settlement of {settlement} has no {old_purpose} buildings built!")
                    return
                amount = min(amount, settlement_info[0])
                await cursor.execute(
                    "Select Amount from KB_Buildings where Kingdom = ? and Settlement = ? and Full_Name = ?",
                    (kingdom, settlement, new_purpose))
                new_building_count = await cursor.fetchone()
                old_building_info = await fetch_building(interaction.guild_id, old_purpose)
                new_building_info = await fetch_building(interaction.guild_id, new_purpose)
                if old_building_info.type != new_building_info.type:
                    await interaction.followup.send(content=f"Building types do not match!")
                    return
                if not new_building_count and amount == settlement_info[0]:
                    await cursor.execute(
                        "UPDATE KB_Buildings Set Full_Name = ?, Subtype = ? where Kingdom = ? and Settlement = ? and Full_Name = ?",
                        (new_purpose, new_building_info.subtype, kingdom, settlement, old_purpose))
                elif new_building_count and amount == settlement_info[0]:
                    await cursor.execute(
                        "UPDATE KB_Buildings Set Amount = Amount + ? where Kingdom = ? and Settlement = ? and Full_Name = ?",
                        (amount, kingdom, settlement, new_purpose))
                    await cursor.execute(
                        "DELETE FROM KB_Buildings where Kingdom = ? and Settlement = ? and Full_Name = ?",
                        (kingdom, settlement, old_purpose))
                else:
                    await cursor.execute(
                        "UPDATE KB_Buildings Set Amount = Amount + ? where Kingdom = ? and Settlement = ? and Full_Name = ?",
                        (amount, kingdom, settlement, new_purpose))
                    await cursor.execute(
                        "UPDATE KB_Buildings Set Amount = Amount - ? where Kingdom = ? and Settlement = ? and Full_Name = ?",
                        (amount, kingdom, settlement, old_purpose))
                await interaction.followup.send(
                    content=f"{amount} {old_purpose} buildings have been repurposed into {new_purpose}!")
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error repurposing building: {e}")
            await interaction.followup.send(content="An error occurred while repurposing a building.")

    @kingdom_group.command(name="event", description="display and handle kingdom events")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.choices(
        intent=[discord.app_commands.Choice(name='Problematic', value=1),
                discord.app_commands.Choice(name='Ongoing', value=2),
                discord.app_commands.Choice(name='Temporary', value=3)]
    )
    async def kingdom_event(self, interaction: discord.Interaction, kingdom: str, password: str, intent: int):
        """This command is used to display and handle kingdom events"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                view = KingdomEventView(user_id=interaction.user.id, guild_id=interaction.guild_id, intent=intent,
                                        kingdom=kingdom)
                await view.update_results()
                await view.create_embed()
                await view.send()
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error displaying kingdom events: {e}")
            await interaction.followup.send(content="An error occurred while displaying kingdom events.")

    trade_group = discord.app_commands.Group(
        name='trade',
        description='Commands related to kingdom management',
        parent=kingdom_group
    )

    @trade_group.command(name="request", description="Request a trade route to another kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(target_kingdom=kingdom_autocomplete)
    async def request_trade(
            self, interaction: discord.Interaction, kingdom: str, password: str, target_kingdom: str,
            seafood: typing.Optional[int], husbandry: typing.Optional[int], produce: typing.Optional[int],
            grain: typing.Optional[int],
            ore: typing.Optional[int], lumber: typing.Optional[int], stone: typing.Optional[int],
            raw_textiles: typing.Optional[int],
            textiles: typing.Optional[int], metallurgy: typing.Optional[int], woodworking: typing.Optional[int],
            stoneworking: typing.Optional[int],
            magical_consumables: typing.Optional[int], magical_items: typing.Optional[int],
            mundane_exotic: typing.Optional[int], mundane_complex: typing.Optional[int]
    ):
        """This command is used to request a trade route to another kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute(
                    "SELECT Character_Name, PLayer_ID FROM KB_Leadership WHERE Kingdom = ? And Title = Ruler",
                    (target_kingdom,))
                target_kingdom_results = await cursor.fetchone()
                if not target_kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {target_kingdom} does not exist.")
                    return
                (target_ruler_name, target_ruler_id) = target_kingdom_results
                await cursor.execute(
                    "SELECT Character_Name, PLayer_ID FROM KB_Leadership WHERE Kingdom = ? And Title = Ruler",
                    (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                (source_ruler_name, source_ruler_id) = kingdom_results
                await cursor.execute("SELECT * FROM KB_Trade WHERE Source_Kingdom = ? AND Target_Kingdom = ?",
                                     (kingdom, target_kingdom))
                trade_results = await cursor.fetchone()
                if trade_results:
                    await interaction.followup.send(content="There is already a trade route between these kingdoms. You have to end it before starting a new one.")
                    return

                await cursor.execute("""
                SELECT 
                SUM(Husbandry), SUM(Produce), SUM(Grain), SUM(Seafood), 
                SUM(Ore), SUM(Stone), SUM(Wood), SUM(Raw_Textiles),
                SUM(Textiles), SUM(Metallurgy), SUM(Woodworking), SUM(Stoneworking),
                SUM(Magical_Consumables), SUM(Magical_Items), SUM(Mundane_Exotic), SUM(Mundane_Complex)
                FROM KB_Trade 
                WHERE Source_Kingdom = ?
                """, (kingdom,))
                trade_results = await cursor.fetchone()
                (trade_husbandry, trade_produce, trade_grain, trade_seafood,
                 trade_ore, trade_stone, trade_wood, trade_raw_textiles,
                 trade_textiles, trade_metallurgy, trade_woodworking, trade_stoneworking,
                 trade_magical_consumables, trade_magical_items, trade_mundane_exotic, trade_mundane_complex
                 ) = trade_results
                await cursor.execute("""
                SELECT 
                    SUM(CASE WHEN subtype = 'Grain' THEN amount * quality ELSE 0 END) AS Grain_total,
                    SUM(CASE WHEN subtype = 'Produce' THEN amount * quality ELSE 0 END) AS Produce_total
                    SUM(CASE WHEN subtype = 'Husbandry' THEN amount * quality ELSE 0 END) AS Husbandry_total
                    SUM(CASE WHEN subtype = 'Seafood' THEN amount * quality ELSE 0 END) AS Seafood_total
                    SUM(CASE WHEN subtype = 'Ore' THEN amount * quality ELSE 0 END) AS ore_total
                    SUM(CASE WHEN subtype = 'Stone' THEN amount * quality ELSE 0 END) AS stone_total
                    SUM(CASE WHEN subtype = 'Wood' THEN amount * quality ELSE 0 END) AS wood_total
                    SUM(CASE WHEN subtype = 'Raw Textiles' THEN amount * quality ELSE 0 END) AS raw_textile_total
                FROM KB_Hexes_Constructed 
                WHERE kingdom = ?;""", (kingdom,))
                resources = await cursor.fetchone()
                (grain_total, produce_total, husbandry_total, seafood_total, ore_total, stone_total, lumber_total,
                 raw_textiles_total) = resources
                await cursor.execute("""
                SELECT 
                    SUM(CASE WHEN subtype = 'Textiles' THEN amount * quality ELSE 0 END) AS Textiles_total,
                    SUM(CASE WHEN subtype = 'Metallurgy' THEN amount * quality ELSE 0 END) AS Metallurgy_total,
                    SUM(CASE WHEN subtype = 'Woodworking' THEN amount * quality ELSE 0 END) AS Woodworking_total,
                    SUM(CASE WHEN subtype = 'Stoneworking' THEN amount * quality ELSE 0 END) AS Stoneworking_total,
                    SUM(CASE WHEN subtype = 'Magical Consumables' THEN amount * quality ELSE 0 END) AS magical_consumables_total,
                    SUM(CASE WHEN subtype = 'Magical Items' THEN amount * quality ELSE 0 END) AS magical_items_total,
                    SUM(CASE WHEN subtype = 'Mundane Exotic' THEN amount * quality ELSE 0 END) AS mundane_exotic_total,
                    SUM(CASE WHEN subtype = 'Mundane Complex' THEN amount * quality ELSE 0 END) AS mundane_complex_total
                FROM KB_Buildings 
                WHERE kingdom = ?;""", (kingdom,))
                goods = await cursor.fetchone()
                (textiles_total, metallurgy_total, woodworking_total, stoneworking_total, magical_consumables_total,
                 magical_items_total, mundane_exotic_total, mundane_complex_total) = goods
                tradeable_husbandry = safe_min(husbandry, safe_sub(husbandry_total, trade_husbandry))
                tradeable_produce = safe_min(produce, safe_sub(produce_total, trade_produce))
                tradeable_grain = safe_min(grain, safe_sub(grain_total, trade_grain))
                tradeable_seafood = safe_min(seafood, safe_sub(seafood_total, trade_seafood))
                tradeable_ore = safe_min(ore, safe_sub(ore_total, trade_ore))
                tradeable_stone = safe_min(stone, safe_sub(stone_total, trade_stone))
                tradeable_wood = safe_min(lumber, safe_sub(lumber_total, trade_wood))
                tradeable_raw_textiles = safe_min(raw_textiles, safe_sub(raw_textiles_total, trade_raw_textiles))
                tradeable_textiles = safe_min(textiles, safe_sub(textiles_total, trade_textiles))
                tradeable_metallurgy = safe_min(metallurgy, safe_sub(metallurgy_total, trade_metallurgy))
                tradeable_woodworking = safe_min(woodworking, safe_sub(woodworking_total, trade_woodworking))
                tradeable_stoneworking = safe_min(stoneworking, safe_sub(stoneworking_total, trade_stoneworking))
                tradeable_magical_consumables = safe_min(magical_consumables,
                                                         safe_sub(magical_consumables_total, trade_magical_consumables))
                tradeable_magical_items = safe_min(magical_items, safe_sub(magical_items_total, trade_magical_items))
                tradeable_mundane_exotic = safe_min(mundane_exotic,
                                                    safe_sub(mundane_exotic_total, trade_mundane_exotic))
                tradeable_mundane_complex = safe_min(mundane_complex,
                                                     safe_sub(mundane_complex_total, trade_mundane_complex))
                view = TradeView(
                    allowed_user_id=target_ruler_id,
                    requester_name=interaction.user.name,
                    requester_id=interaction.user.id,
                    character_name=source_ruler_name,
                    recipient_name=target_ruler_name,
                    requesting_kingdom=kingdom,
                    sending_kingdom=target_kingdom,
                    bot=self.bot,
                    guild_id=interaction.guild_id,
                    interaction=interaction,
                    seafood=tradeable_seafood,
                    husbandry=tradeable_husbandry,
                    produce=tradeable_produce,
                    grain=tradeable_grain,
                    ore=tradeable_ore,
                    lumber=tradeable_wood,
                    stone=tradeable_stone,
                    raw_textiles=tradeable_raw_textiles,
                    textiles=tradeable_textiles,
                    metallurgy=tradeable_metallurgy,
                    woodworking=tradeable_woodworking,
                    stoneworking=tradeable_stoneworking,
                    magical_consumables=tradeable_magical_consumables,
                    magical_items=tradeable_magical_items,
                    mundane_exotic=tradeable_mundane_exotic,
                    mundane_complex=tradeable_mundane_complex
                )

                await view.create_embed()
                await view.send_initial_message()
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error requesting trade route: {e}")
            await interaction.followup.send(content="An error occurred while requesting a trade route.")

    @trade_group.command(name="cancel", description="Cancel a trade route with another kingdom")
    @app_commands.choices(
        intent=[discord.app_commands.Choice(name='outgoing', value=1),
                discord.app_commands.Choice(name='incoming', value=2)])
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(target_kingdom=kingdom_autocomplete)
    async def cancel_trade(
            self,
            interaction: discord.Interaction,
            kingdom: str,
            password: str,
            target_kingdom: str,
            intent: int
    ):
        """This command is used to cancel a trade route with another kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute(
                    "SELECT Character_Name, PLayer_ID FROM KB_Leadership WHERE Kingdom = ? And Title = Ruler",
                    (target_kingdom,))
                target_kingdom_results = await cursor.fetchone()
                if not target_kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {target_kingdom} does not exist.")
                    return
                (target_ruler_name, target_ruler_id) = target_kingdom_results
                await cursor.execute(
                    "SELECT Character_Name, PLayer_ID FROM KB_Leadership WHERE Kingdom = ? And Title = Ruler",
                    (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                (source_ruler_name, source_ruler_id) = kingdom_results
                statement = """
                SELECT Source_Kingdom, End_Kingdom, 
                Husbandry, Seafood, Grain, Produce
                Ore, Stone, Wood, Raw_Textiles, Textiles, Metallurgy, Woodworking, Stoneworking,
                Magical_Consumables, Magical_Items, Mundane_Exotic, Mundane_Complex
                FROM KB_Trade
                WHERE Source_Kingdom = ? AND End_Kingdom = ?"""
                if intent == 2:
                    await cursor.execute(statement, (target_kingdom, kingdom))
                else:
                    await cursor.execute(statement, (kingdom, target_kingdom))
                trade_results = await cursor.fetchone()
                if not trade_results:
                    await interaction.followup.send(content="No trade route exists between these kingdoms.")
                    return
                (source_kingdom, end_kingdom, husbandry, seafood, grain, produce, ore, stone, wood, raw_textiles,
                    textiles, metallurgy, woodworking, stoneworking, magical_consumables, magical_items, mundane_exotic,
                    mundane_complex) = trade_results
                embed = discord.Embed(
                    title=f"Trade Route Cancellation",
                    description=f"{source_ruler_name} is canceling a trade route with {target_ruler_name}."
                )
                if any((husbandry, seafood, grain, produce)):
                    embed.add_field(name="Food", value=f"Husbandry: {husbandry}, Seafood: {seafood}, Grain: {grain}, Produce: {produce}")
                if any((ore, stone, wood, raw_textiles)):
                    embed.add_field(name="Resources", value=f"Ore: {ore}, Stone: {stone}, Wood: {wood}, Raw Textiles: {raw_textiles}")
                if any((textiles, metallurgy, woodworking, stoneworking)):
                    embed.add_field(name="Goods", value=f"Textiles: {textiles}, Metallurgy: {metallurgy}, Woodworking: {woodworking}, Stoneworking: {stoneworking}")
                if any((magical_consumables, magical_items, mundane_exotic, mundane_complex)):
                    embed.add_field(name="Items", value=f"Magical Consumables: {magical_consumables}, Magical Items: {magical_items}, Mundane Exotic: {mundane_exotic}, Mundane Complex: {mundane_complex}")
                content = f"<@{interaction.user.id}> is cancelling their trade with <@{target_ruler_id}>"
                await interaction.followup.send(content=content, embed=embed, allowed_mentions=discord.AllowedMentions.users)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error canceling trade route: {e}")
            await interaction.followup.send(content="An error occurred while canceling a trade route.")

    population_group = discord.app_commands.Group(
        name='population',
        description='Commands related to kingdom management',
        parent=kingdom_group
    )

    @population_group.command(name="bid", description="Bid for a portion of the population pool")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    async def bid_population(self, interaction: discord.Interaction, kingdom: str, password: str, amount: int):
        """This command is used to bid for a portion of the population pool"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, Build_Points, Region FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                amount = min(amount, kingdom_results[1])
                await cursor.execute("Select Build_points from KB_Population_Bids where Kingdom = ?", (kingdom,))
                population_bid = await cursor.fetchone()
                if not population_bid:
                    await cursor.execute("INSERT INTO KB_Population_Bids (Kingdom, Amount, Region) VALUES (?, ?, ?)", (kingdom, amount, kingdom_results[2]))
                    await interaction.followup.send(content=f"{amount} Build Points have been bid for population on.")
                else:
                    await cursor.execute("UPDATE KB_Population_Bids SET Amount = Amount + ? WHERE Kingdom = ?", (amount, kingdom))
                    await interaction.followup.send(content=f"{amount} Build Points have been added to the population bid.")
                await cursor.execute("UPDATE kb_Kingdoms SET Build_Points = Build_Points - ? WHERE Kingdom = ?", (amount, kingdom))
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error bidding on population: {e}")
            await interaction.followup.send(content="An error occurred while bidding on population.")

    @population_group.command(name="display", description="Display the current population bid")
    @app_commands.autocomplete(region=shared_functions.region_autocomplete)
    async def display_population(self, interaction: discord.Interaction, region: str):
        """This command is used to display the current population bid"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Population FROM KB_Population WHERE region = ?", (region,))
                region = await cursor.fetchone()
                if not region:
                    await interaction.followup.send(content=f"The region of {region} does not exist.")
                    return
                await cursor.execute("SELECT sum(Amount) FROM KB_Population_Bids WHERE Region = ?", (region,))
                total_bid = await cursor.fetchone()
                await cursor.execute("SELECT Kingdom, Amount FROM KB_Population_Bids WHERE Region = ?", (region,))
                bids = await cursor.fetchall()
                if not bids:
                    await interaction.followup.send(content="There are no bids for this region.")
                    return
                embed = discord.Embed(
                    title=f"Population Bids for {region}",
                    description="The following kingdoms have bid for this region."
                )
                list_of_kingdoms = ""
                for idx, bid in enumerate(bids):
                    (kingdom, amount) = bid
                    list_of_kingdoms += f"{kingdom} has bid {amount} BP, potentially claiming {(amount / total_bid[0]) * region[0]} people.\r\n"
                    if idx % 10 == 0:
                        embed.add_field(name="Bids", value=list_of_kingdoms)
                        list_of_kingdoms = ""
                embed.add_field(name="Bids", value=list_of_kingdoms)
                await interaction.followup.send(embed=embed)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error displaying population bid: {e}")
            await interaction.followup.send(content="An error occurred while displaying the population bid.")


    army_group = discord.app_commands.Group(
        name='army',
        description='Commands related to kingdom management',
        parent=kingdom_group
    )

    @army_group.command(name="create", description="Create an army")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    async def create_army(self, interaction: discord.Interaction, kingdom: str, password: str, army_name: str, consumption_size: int):
        """This command is used to create an army"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("Select Army_Name from KB_Armies where Kingdom = ? and Army_Name = ?", (kingdom, army_name))
                army = await cursor.fetchone()
                if army:
                    await cursor.execute("UPDATE KB_Armies SET consumption_size = ? WHERE Kingdom = ? and Army_Name = ?", (consumption_size, kingdom, army_name))
                    await interaction.followup.send(content=f"Army {army_name} has been updated.")
                else:
                    await cursor.execute("INSERT INTO KB_Armies (Kingdom, Army_Name, consumption_size) VALUES (?, ?, ?)", (kingdom, army_name, consumption_size))
                    await interaction.followup.send(content=f"Army {army_name} has been created.")
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error creating army: {e}")
            await interaction.followup.send(content="An error occurred while creating an army.")

    @army_group.command(name="delete", description="Delete an army")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    async def delete_army(self, interaction: discord.Interaction, kingdom: str, password: str, army_name: str):
        """This command is used to delete an army"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("Select Army_Name from KB_Armies where Kingdom = ? and Army_Name = ?", (kingdom, army_name))
                army = await cursor.fetchone()
                if not army:
                    await interaction.followup.send(content=f"Army {army_name} does not exist.")
                    return
                await cursor.execute("DELETE FROM KB_Armies where Kingdom = ? and Army_Name = ?", (kingdom, army_name))
                await interaction.followup.send(content=f"Army {army_name} has been deleted.")
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error deleting army: {e}")
            await interaction.followup.send(content="An error occurred while deleting an army.")

class KingdomView(shared_functions.ShopView):
    """
    A paginated view for displaying kingdom data (kb_Kingdoms).
    """

    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int, interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, interaction=interaction,
                         content="")
        self.max_items = None
        self.content = None
        self.results = []
        self.embed = None

    async def update_results(self):
        """
        Fetch the kingdom rows for the current page.
        """
        statement = """
            SELECT 
                kb_Kingdom, kb_Government, kb_Alignment, kb_Control_DC, kb_Build_Points, 
                kb_Size, kb_Population, kb_Economy, kb_Loyalty, kb_Stability,
                kb_Unrest, kb_Consumption, 
                Custom.Control_DC, Custom.Economy, Custom.Loyalty, Custom.Stability, 
                Custom.Unrest, Custom.Consumption
            FROM kb_Kingdoms AS KB
            LEFT JOIN kb_Kingdoms_Custom AS Custom ON kb_Kingdom = Custom.Kingdom
            LIMIT ? OFFSET ?
        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """
        Create the embed that shows the currently fetched kingdom rows.
        """
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1

        self.embed = discord.Embed(
            title="kb_Kingdoms",
            description=f"Page {current_page} of {total_pages}"
        )

        for item in self.results:
            (
                kingdom, government, alignment, control_dc, build_points, size, population,
                economy, loyalty, stability, unrest, consumption,
                custom_control_dc, custom_economy, custom_loyalty,
                custom_stability, custom_unrest, custom_consumption
            ) = item

            # Build your string for the embed field
            description = (
                f"**Government**: {government}, **Alignment**: {alignment}\n"
                f"**Resources**: {build_points} BP\n"
                f"**Size**: {size}, **Population**: {population}\n"
                f"**Economy**: {economy}, **Loyalty**: {loyalty}, **Stability**: {stability}\n"
                f"**Unrest**: {unrest}, **Consumption**: {consumption}\n"
                f"**Unique Modifiers**\n"
                f" - Control DC Adjustment: {custom_control_dc}\n"
                f" - Economy Adjustment: {custom_economy} | Loyalty Adjustment: {custom_loyalty}\n"
                f" - Stability Adjustment: {custom_stability}\n"
                f" - Unrest Adjustment: {custom_unrest} | Consumption Adjustment: {custom_consumption}"
            )

            self.embed.add_field(
                name=f"**Kingdom**: {kingdom}, Control DC: {control_dc}",
                value=description,
                inline=False
            )

    async def get_max_items(self):
        """
        Return the total number of kingdoms.
        """
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM kb_Kingdoms")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class SettlementView(shared_functions.ShopView):
    """
    A paginated view for displaying settlement data (kb_settlements).
    """

    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int,
                 interaction: discord.Interaction, kingdom: typing.Optional[str]):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, interaction=interaction,
                         content="")
        self.max_items = None
        self.content = None
        self.results = []
        self.embed = None
        self.kingdom = kingdom

    async def update_results(self):
        """
        Fetch settlement rows for the current page, optionally filtered by kingdom.
        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            if self.kingdom:
                statement = """ 
                    SELECT 
                        kb_Kingdom, kb_Settlement, kb_Size, kb_Population, 
                        kb_Corruption, kb_Crime, kb_Productivity, kb_Law, kb_Lore, kb_Society, 
                        kb_Danger, kb_Defence, kb_Base_Value, kb_Spellcasting, kb_Supply, kb_Decay,
                        Custom.Corruption, Custom.Crime, Custom.Productivity, Custom.Law, 
                        Custom.Lore, Custom.Society, Custom.Danger, Custom.Defence,
                        Custom.Base_Value, Custom.Spellcasting, Custom.Supply
                    FROM kb_settlements AS KB
                    LEFT JOIN kb_settlements_Custom AS Custom 
                        ON KB.kb_Settlement = Custom.Settlement
                    WHERE KB.Kingdom = ?
                    LIMIT ? OFFSET ?
                """
                cursor = await db.execute(statement, (self.kingdom, self.limit, self.offset))
            else:
                statement = """
                    SELECT 
                        kb_Kingdom, kb_Settlement, kb_Size, kb_Population, 
                        kb_Corruption, kb_Crime, kb_Productivity, kb_Law, kb_Lore, kb_Society, 
                        kb_Danger, kb_Defence, kb_Base_Value, kb_Spellcasting, kb_Supply, kb_Decay,
                        Custom.Corruption, Custom.Crime, Custom.Productivity, Custom.Law, 
                        Custom.Lore, Custom.Society, Custom.Danger, Custom.Defence,
                        Custom.Base_Value, Custom.Spellcasting, Custom.Supply
                    FROM kb_settlements AS KB
                    LEFT JOIN kb_settlements_Custom AS Custom 
                        ON KB.kb_Settlement = Custom.Settlement
                    LIMIT ? OFFSET ?
                """
                cursor = await db.execute(statement, (self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """
        Create the embed showing settlement data for the current page.
        """
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1

        if self.kingdom:
            self.embed = discord.Embed(
                title=f"Settlements in {self.kingdom}",
                description=f"Page {current_page} of {total_pages}"
            )
        else:
            self.embed = discord.Embed(
                title="Settlements",
                description=f"Page {current_page} of {total_pages}"
            )

        for row in self.results:
            (
                kingdom, settlement, size, population,
                corruption, crime, productivity, law, lore, society,
                danger, defence, base_value, spellcasting, supply, decay,
                custom_corruption, custom_crime, custom_productivity, custom_law,
                custom_lore, custom_society, custom_danger, custom_defence,
                custom_base_value, custom_spellcasting, custom_supply
            ) = row

            desc = (
                f"**Size**: {size}, **Population**: {population}\n"
                f"**Corruption**: {corruption}, **Crime**: {crime}, **Productivity**: {productivity}\n"
                f"**Law**: {law}, **Lore**: {lore}, **Society**: {society}\n"
                f"**Danger**: {danger}, **Defence**: {defence}\n"
                f"**Base Value**: {base_value}, **Spellcasting**: {spellcasting}, **Supply**: {supply}\n"
                f"**Decay**: {decay}\n\n"
                f"**Custom Modifiers**\n"
                f" - Corruption: {custom_corruption}, Crime: {custom_crime}, Productivity: {custom_productivity}\n"
                f" - Law: {custom_law}, Lore: {custom_lore}, Society: {custom_society}\n"
                f" - Danger: {custom_danger}, Defence: {custom_defence}\n"
                f" - Base Value: {custom_base_value}, Spellcasting: {custom_spellcasting}, Supply: {custom_supply}"
            )

            self.embed.add_field(
                name=f"{kingdom} - {settlement}",
                value=desc,
                inline=False
            )

    async def get_max_items(self):
        """
        Return the total number of settlements, optionally filtered by kingdom.
        """
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                if self.kingdom:
                    cursor = await db.execute(
                        "SELECT COUNT(*) FROM kb_settlements WHERE Kingdom = ?",
                        (self.kingdom,)
                    )
                else:
                    cursor = await db.execute("SELECT COUNT(*) FROM kb_settlements")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class HexView(shared_functions.ShopView):
    """
    A paginated view for displaying hex data (kb_hexes) for a particular kingdom.
    """

    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int,
                 kingdom: str, interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, interaction=interaction,
                         content="")
        self.max_items = None
        self.results = []
        self.embed = None
        self.kingdom = kingdom

    async def update_results(self):
        """
        Fetch hex rows for the current page for the given kingdom.
        """
        statement = """
            SELECT 
                Kingdom, Hex_Terrain, Amount, Improvement,
                Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation
            FROM kb_hexes
            WHERE Kingdom = ?
            LIMIT ? OFFSET ?
        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.kingdom, self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """
        Create the embed showing hex data for the current page.
        """
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(
            title=f"Hexes for {self.kingdom}",
            description=f"Page {current_page} of {total_pages}"
        )

        for row in self.results:
            (
                kingdom, hex_terrain, amount, improvement,
                economy, loyalty, stability, unrest, consumption, defence, taxation
            ) = row

            desc = (
                f"**Amount**: {amount}\n"
                f"**Economy**: {economy}, **Loyalty**: {loyalty}, **Stability**: {stability}\n"
                f"**Unrest**: {unrest}, **Consumption**: {consumption}\n"
                f"**Defence**: {defence}, **Taxation**: {taxation}"
            )

            self.embed.add_field(
                name=f"Improvement: {improvement} | Terrain: {hex_terrain}",
                value=desc,
                inline=False
            )

    async def get_max_items(self):
        """
        Return the total number of hexes for the given kingdom.
        """
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM kb_hexes WHERE Kingdom = ?",
                    (self.kingdom,)
                )
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class ImprovementView(shared_functions.ShopView):
    """
    A paginated view for displaying possible improvements for hexes (kb_Hexes_Improvements).
    """

    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int,
                 interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, interaction=interaction,
                         content="")
        self.max_items = None
        self.results = []
        self.embed = None

    async def update_results(self):
        """
        Fetch improvement rows for the current page.
        """
        statement = """
            SELECT 
                Improvement, Road_Multiplier, Build_Points,
                Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation,
                Cavernous, Coastline, Desert, Forest, Hill, Jungle, Marsh, Mountain, 
                Plains, Swamp, Tundra, Water
            FROM kb_Hexes_Improvements
            LIMIT ? OFFSET ?
        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """
        Create the embed showing each improvement's stats.
        """
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(
            title="Hex Improvements",
            description=f"Page {current_page} of {total_pages}"
        )

        for row in self.results:
            (
                improvement, road_multiplier, build_points,
                economy, loyalty, stability, unrest, consumption, defence, taxation,
                cavernous, coastline, desert, forest, hill, jungle, marsh, mountain,
                plains, swamp, tundra, water
            ) = row

            # Gather all possible terrains
            terrains = []
            if cavernous: terrains.append("Cavernous")
            if coastline: terrains.append("Coastline")
            if desert: terrains.append("Desert")
            if forest: terrains.append("Forest")
            if hill: terrains.append("Hill")
            if jungle: terrains.append("Jungle")
            if marsh: terrains.append("Marsh")
            if mountain: terrains.append("Mountain")
            if plains: terrains.append("Plains")
            if swamp: terrains.append("Swamp")
            if tundra: terrains.append("Tundra")
            if water: terrains.append("Water")
            terrain_str = ", ".join(terrains)

            desc = (
                f"**Road Multiplier**: {road_multiplier}, **Build Points**: {build_points}\n"
                f"**Economy**: {economy}, **Loyalty**: {loyalty}, **Stability**: {stability}\n"
                f"**Unrest**: {unrest}, **Consumption**: {consumption}\n"
                f"**Defence**: {defence}, **Taxation**: {taxation}\n\n"
                f"__Available Terrains__:\n{terrain_str}"
            )

            self.embed.add_field(
                name=f"Improvement: {improvement}",
                value=desc,
                inline=False
            )

    async def get_max_items(self):
        """
        Return the total number of improvements in kb_Hexes_Improvements.
        """
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM kb_Hexes_Improvements")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class BlueprintView(shared_functions.ShopView):
    """
    A paginated view for displaying building blueprint data (kb_Buildings_Blueprints).
    """

    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int,
                 interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, interaction=interaction,
                         content="")
        self.max_items = None
        self.results = []
        self.embed = None

    async def update_results(self):
        """
        Fetch building blueprint rows for the current page.
        NOTE: We unify the table references to 'kb_Buildings_Blueprints'.
        """
        statement = """
            SELECT 
                Building, Build_Points, Economy, Loyalty, Stability, Fame, Unrest,
                Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence,
                Base_Value, Spellcasting, Supply,
                Settlement_Limit, District_Limit, Description
            FROM kb_Buildings_Blueprints
            LIMIT ? OFFSET ?
        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """
        Create the embed showing building blueprint data for the current page.
        """
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(
            title="Building Blueprints",
            description=f"Page {current_page} of {total_pages}"
        )

        for row in self.results:
            (
                building, build_points, economy, loyalty, stability, fame, unrest,
                corruption, crime, productivity, law, lore, society, danger, defence,
                base_value, spellcasting, supply,
                settlement_limit, district_limit, description
            ) = row

            desc = (
                f"**Economy**: {economy}, **Loyalty**: {loyalty}, **Stability**: {stability}, **Fame**: {fame}\n"
                f"**Unrest**: {unrest}, **Corruption**: {corruption}, **Crime**: {crime}, **Productivity**: {productivity}\n"
                f"**Law**: {law}, **Lore**: {lore}, **Society**: {society}, **Danger**: {danger}\n"
                f"**Defence**: {defence}, **Base Value**: {base_value}, **Spellcasting**: {spellcasting}, **Supply**: {supply}\n"
                f"**Settlement Limit**: {settlement_limit}, **District Limit**: {district_limit}\n"
                f"**Description**: {description}"
            )

            self.embed.add_field(
                name=f"{building} (Cost: {build_points} BP)",
                value=desc,
                inline=False
            )

    async def get_max_items(self):
        """
        Return the total number of building blueprints in kb_Buildings_Blueprints.
        """
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM kb_Buildings_Blueprints")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class KingdomEventView(discord.ui.View):
    """Base class for shop views with pagination."""

    def __init__(self, user_id: int, guild_id: int, interaction: discord.Interaction,
                 kingdom: str,
                 intent: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.guild_id = guild_id
        self.interaction = interaction
        self.kingdom = kingdom
        self.intent = intent
        self.offset = 0
        self.limit = 10
        self.event_list = []
        self.max = None
        self.embed = None
        self.message = None
        self.results = None
        # Initialize buttons

    async def update_buttons(self):
        self.clear_items()
        await self.update_results()
        max_items = await self.get_max_items()
        first_page = self.offset <= 0
        last_page = self.offset + self.limit >= max_items

        first_page_button = discord.ui.Button(label='First Page', style=discord.ButtonStyle.primary, row=1)
        first_page_button.disabled = first_page
        previous_page_button = discord.ui.Button(label='Previous Page', style=discord.ButtonStyle.primary, row=1)
        previous_page_button.disabled = first_page
        change_page_button = discord.ui.Button(label='Change View', style=discord.ButtonStyle.primary, row=1)
        next_page_button = discord.ui.Button(label='Next Page', style=discord.ButtonStyle.primary, row=1)
        next_page_button.disabled = last_page
        last_page_button = discord.ui.Button(label='Last Page', style=discord.ButtonStyle.primary, row=1)
        last_page_button.disabled = last_page

        first_page_button.callback = self.first_page
        previous_page_button.callback = self.previous_page
        change_page_button.callback = self.change_page
        next_page_button.callback = self.next_page
        last_page_button.callback = self.last_page

        self.add_item(first_page_button)
        self.add_item(previous_page_button)
        self.add_item(change_page_button)
        self.add_item(next_page_button)
        self.add_item(last_page_button)

        for idx, event in enumerate(self.event_list):
            button = discord.ui.Button(label=event[0], style=discord.ButtonStyle.primary, row=2 + idx // 5)
            button.callback = self.create_button_callback(event)
            self.add_item(button)

    def create_button_callback(self, event):
        async def button_callback(interaction: discord.Interaction):
            await self.roll_check(interaction, event)

        return button_callback

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
        if self.offset == 0:
            await interaction.response.send_message("You are already on the first page.", ephemeral=True)
            return
        self.offset = 0
        await self.update_buttons()
        await self.create_embed()
        await interaction.edit_original_response(
            embed=self.embed,
            view=self
        )

    async def previous_page(self, interaction: discord.Interaction):
        """Handle moving to the previous page."""
        await interaction.response.defer()
        if self.offset > 0:
            self.offset -= self.limit
            if self.offset < 0:
                self.offset = 0

            await self.update_buttons()
            await self.create_embed()
            await interaction.edit_original_response(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.followup.send("You are on the first page.", ephemeral=True)

    async def change_page(self, interaction: discord.Interaction):
        """Handle changing the view."""
        await interaction.response.defer()
        self.offset = 0
        if self.intent == 1:
            self.intent = 2
        elif self.intent == 2:
            self.intent = 3
        elif self.intent == 3:
            self.intent = 1
        await self.update_buttons()
        await self.create_embed()
        await interaction.edit_original_response(
            embed=self.embed,
            view=self
        )

    async def next_page(self, interaction: discord.Interaction):
        """Handle moving to the next page."""
        await interaction.response.defer()
        max_items = await self.get_max_items()
        if self.offset + self.limit < max_items:
            self.offset += self.limit
            await self.update_buttons()
            await self.create_embed()
            await interaction.edit_original_response(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.followup.send("You are on the last page.", ephemeral=True)

    async def last_page(self, interaction: discord.Interaction):
        """Handle moving to the last page."""
        await interaction.response.defer()
        max_items = await self.get_max_items()
        last_page_offset = (max_items // self.limit) * self.limit
        if self.offset != last_page_offset:
            self.offset = last_page_offset
            await self.update_buttons()
            await self.create_embed()
            await interaction.edit_original_response(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.followup.send("You are on the last page.", ephemeral=True)

    async def send_initial_message(self):
        """Send the initial message with the view."""
        try:
            await self.update_buttons()
            await self.create_embed()
            await self.interaction.followup.send(
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
                await self.message.edit(embed=self.embed, view=self)
            except discord.HTTPException as e:
                logging.error(f"Failed to edit message on timeout: {e}")

    async def update_results(self):
        """Fetch the results for the current page. To be implemented in subclasses."""
        if self.intent == 1:
            statement = """
                            SELECT ID, Type, Kingdom, Settlement, Hex, Name, Effect, Duration, Check_A, Check_A_Status, Check_B, Check_B_Status
                            FROM KB_Events_Active 
                            WHERE Kingdom = ? AND Type = 'Problematic' 
                            Limit ? Offset ?
                        """
            event_statement = """
                        SELECT ID, Type, Kingdom, Settlement, Hex, Name, Effect, Duration, Check_A, Check_A_Status, Check_B, Check_B_Status
                        FROM KB_Events_Active 
                        WHERE Kingdom = ? AND Type = 'Problematic'  AND (Check_A IS NOT NULL OR Check_B IS NOT NULL)
                        Limit ? Offset ?
                        """
        elif self.intent == 2:
            statement = """
                        SELECT ID, Type, Kingdom, Settlement, Hex, Name, Effect, Duration, Check_A, Check_A_Status, Check_B, Check_B_Status
                        FROM KB_Events_Active 
                        WHERE Kingdom = ? 
                        Limit ? Offset ?
                        """
            event_statement = """
            SELECT ID, Type, Kingdom, Settlement, Hex, Name, Effect, Duration, Check_A, Check_A_Status, Check_B, Check_B_Status
            FROM KB_Events_Active 
            WHERE Kingdom = ?  AND (Check_A IS NOT NULL OR Check_B IS NOT NULL)
            Limit ? Offset ?
            """
        else:
            statement = """
                            SELECT ID, Type, Kingdom, Settlement, Hex, Name, Effect, Duration, Check_A, Check_A_Status, Check_B, Check_B_Status
                            FROM KB_Events_Active 
                            WHERE Kingdom = ? AND Duration > 0 
                            Limit ? Offset ?
                        """
            event_statement = """
                                SELECT Name, Kingdom, Settlement, Check_A, Check_B, Check_A_Status, Check_B_Status
                                FROM KB_Events_Active 
                                WHERE Kingdom = ? AND Duration > 0 AND (Check_A IS NOT NULL OR Check_B IS NOT NULL)
                                Limit ? Offset ?
                        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(statement, (self.kingdom, self.limit, self.offset))
            self.results = await cursor.fetchall()
            await cursor.execute(event_statement, (self.kingdom, self.limit, self.offset))
            self.event_list = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the current page. To be implemented in subclasses."""
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        if self.intent == 1:
            self.embed = discord.Embed(
                title=f"Problematic Events for {self.kingdom}",
                description=f"Page {current_page} of {total_pages}")
        elif self.intent == 2:
            self.embed = discord.Embed(
                title=f"Ongoing Events for {self.kingdom}",
                description=f"Page {current_page} of {total_pages}")
        elif self.intent == 3:
            self.embed = discord.Embed(
                title=f"Temporary Events for {self.kingdom}",
                description=f"Page {current_page} of {total_pages}")
        for item in self.results:
            (id, type, kingdom, settlement, hex, name, effect, duration, check_a, check_a_status, check_b,
             check_b_status) = item
            status_dict = {0: "Not Attempted", 1: "Passed", -1: "Failed"}
            duration = f"{duration} turns" if duration > 0 else "Ongoing"
            field_content = f"**Type**: {type}, Duration: {duration}"
            field_content += f", **Settlement**: {settlement}" if settlement else ""
            field_content += f", **Hex**: {hex}" if hex else ""
            field_content += f"\r\n{effect}"
            field_content += f"\r\n**{check_b}**: {status_dict[check_a_status]}" if check_a else ""
            field_content += f"\r\n**{check_b}**: {status_dict[check_b_status]}" if check_b else ""
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute(
                    "SELECT Name, Severity, Type, Value, Reroll FROM KB_Events_Consequence where Name = ? Order BY Severity asc",
                    (name,))
                unforeseen_consequences = await cursor.fetchall()
                consequence_rolltype_dict = {0: "Set", 1: "Randomized", 2: "Per building sharing this trait",
                                             3: "Percentile Effect", 4: "Randomized with 'exploding' reroll on max",
                                             5: "Singular Effect that explodes on Max"}
                if type == "Problematic":
                    consequence_severity_dict = {0: "No Action or failed rolls", 1: "Passed 1 Check",
                                                 2: "passed 2 checks"}
                else:
                    consequence_severity_dict = {0: "No Action Required"}
                for consequence in unforeseen_consequences:
                    (name, severity, type, value, reroll) = consequence
                    field_content += f"\r\n**Consequence**: {name}, **Severity**: {consequence_severity_dict[severity]}, **Effects**: {type}, **Value**: {value}, **Reroll**: {consequence_rolltype_dict[reroll]}"
            self.embed.add_field(name=f'**Event**: {name} ID: {id}', value=field_content, inline=False)

    async def get_max_items(self):
        """Get the total number of items. To be implemented in subclasses."""
        if self.intent == 1:
            statement = """
                            SELECT COUNT(*) 
                            FROM KB_Events_Active 
                            WHERE Kingdom = ? AND Type = 'Problematic'
                        """
        elif self.intent == 2:
            statement = """
                            SELECT COUNT(*) 
                            FROM KB_Events_Active 
                            WHERE Kingdom = ?
                        """
        elif self.intent == 3:
            statement = """
                            SELECT COUNT(*) 
                            FROM KB_Events_Active 
                            WHERE Kingdom = ? AND Duration > 0
                        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.kingdom,))
            count = await cursor.fetchone()
            return count[0]

    async def roll_check(self, interaction: discord.Interaction, event: aiosqlite.Row):
        """Prompt the user to roll Check_A and Check_B if available."""
        await interaction.response.defer()
        (event_id, event_name, kingdom, settlement, hex, name, effect, duration, check_a, check_a_status, check_b,
         check_b_status) = event
        check_prompts = []
        if check_a:
            check_prompts.append(f"**Roll for {check_a}**")
        if check_b:
            check_prompts.append(f"**Roll for {check_b}**")

        check_prompt_text = "\n".join(check_prompts) if check_prompts else "No checks required."

        embed = discord.Embed(
            title=f"Event Roll: {event_name} (ID: {event_id})",
            description=check_prompt_text,
            color=discord.Color.blue()
        )
        view = CheckButton(check_a=check_a, check_b=check_b, kingdom=self.kingdom, settlement=None,
                           guild_id=self.guild_id, event_id=event_id)

        await interaction.followup.send(embed=embed, ephemeral=True, view=view)


class CheckButton(discord.ui.View):
    def __init__(self, check_a: str, check_b: str, kingdom: str, settlement: typing.Optional[str], guild_id: int,
                 event_id):
        super().__init__(timeout=9000)
        self.check_a = check_a
        self.check_b = check_b
        self.kingdom = kingdom
        self.guild_id = guild_id
        self.event_id = event_id
        self.settlement = settlement
        if check_a:
            button = discord.ui.Button(label=check_a, style=discord.ButtonStyle.primary, row=1)
            button.callback = self.create_button_callback(check=check_a, version="A")
            self.add_item(button)
        if check_b:
            button = discord.ui.Button(label=check_b, style=discord.ButtonStyle.primary, row=1)
            button.callback = self.create_button_callback(check=check_b, version="B")
            self.add_item(button)

    def create_button_callback(self, check: str, version: str):
        async def button_callback(interaction: discord.Interaction):
            await self.handle_button_check(interaction, check=check, version=version)

        return button_callback

    async def handle_button_check(self, interaction: discord.Interaction, check: str, version: str):
        try:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                if version == "A":
                    await cursor.execute("SELECT Check_A_Status, Name from KB_Events_Active where ID = ?",
                                         (self.event_id,))
                elif version == "B":
                    await cursor.execute("SELECT Check_B_Status, Name from KB_Events_Active where ID = ?",
                                         (self.event_id,))
                check_status = await cursor.fetchone()
                if check_status[0] != 0:
                    await interaction.response.send_message(
                        f"{check} has already been rolled for.", ephemeral=True
                    )
                    return
                if check == "Loyalty":
                    statement = "SELECT Control_DC, Loyalty From KB_Kingdoms where Kingdom = ?"
                elif check == "Stability":
                    statement = "SELECT  Control_DC, Stability From KB_Kingdoms where Kingdom = ?"
                elif check == "Economy":
                    statement = "SELECT  Control_DC, Economy From KB_Kingdoms where Kingdom = ?"
                await cursor.execute(statement, (self.kingdom,))
                result = await cursor.fetchone()
                await cursor.execute("Select Bonus, Penalty FROM KB_Events WHERE Name = ?", (check_status[1],))
                bonus_penalty = await cursor.fetchone()
                check_result = random.randint(1, 20) + result[1]
                if bonus_penalty[0]:
                    check_bonus = kingdom_dict.get(bonus_penalty[0], None)
                    check_bonus = settlement_dict.get(bonus_penalty[0], None) if not check_bonus else check_bonus
                    if check_bonus:
                        await cursor.execute(
                            f"SELECT Sum(Amount) from KB_Buildings Where Kingdom = ? and Settlement = ? AND {check_bonus} > 0",
                            (self.kingdom, self.settlement))
                    else:
                        await cursor.execute(
                            "SELECT Sum(Amount) from KB_Buildings Where Kingdom = ? and Settlement = ? AND Type = ?",
                            (self.kingdom, self.settlement, bonus_penalty[1]))
                    check_bonus = await cursor.fetchone()
                    check_result += check_bonus[0]
                elif bonus_penalty[1]:
                    check_penalty = kingdom_dict.get(bonus_penalty[1], None)
                    check_penalty = settlement_dict.get(bonus_penalty[1],
                                                        None) if not check_penalty else check_penalty
                    if check_penalty:
                        await cursor.execute(
                            f"SELECT Sum(Amount) from KB_Buildings Where Kingdom = ? and Settlement = ? AND {check_penalty} > 0",
                            (self.kingdom, self.settlement))
                    else:
                        await cursor.execute(
                            "SELECT Sum(Amount) from KB_Buildings Where Kingdom = ? and Settlement = ? AND Type = ?",
                            (self.kingdom, self.settlement, bonus_penalty[1]))
                    check_penalty = await cursor.fetchone()
                    check_result -= check_penalty[0]
                final_response = f"Rolling for {check} with a result of {check_result}."
                final_result = 1 if check_result >= result[0] else -1
                final_response += f"\n{check} check {'passed' if final_result == 1 else 'failed'}"
                if version == "A":
                    statement = "UPDATE KB_Events_Active Set Check_A_Status = ? where ID = ?"
                else:
                    statement = "UPDATE KB_Events_Active Set Check_B_Status = ? where ID = ?"
                await cursor.execute(statement, (final_result, self.event_id))
                await db.commit()
                await interaction.response.send_message(content=final_response, ephemeral=True)
                self.view.stop()
        except Exception as e:
            logging.exception(f"Error in Checkbutton callback: {e}")
            await interaction.response.send_message(
                "An error occurred while finalizing your availability.", ephemeral=True
            )


class TradeView(shared_functions.RecipientAcknowledgementView):
    def __init__(
            self,
            allowed_user_id: int,
            requester_name: str,
            requester_id: int,
            character_name: str,
            recipient_name: str,
            requesting_kingdom: str,
            sending_kingdom: str,
            seafood: int,
            husbandry: int,
            grain: int,
            produce: int,
            textiles: int,
            metallurgy: int,
            woodworking: int,
            stoneworking: int,
            magical_consumables: int,
            magical_items: int,
            mundane_exotic: int,
            mundane_complex: int,
            lumber: int,
            stone: int,
            ore: int,
            raw_textiles: int,
            bot: commands.Bot,
            guild_id: int,
            interaction: discord.Interaction
    ):
        super().__init__(allowed_user_id=allowed_user_id, interaction=interaction,
                         content=f"<@{allowed_user_id}>, please accept or request this transaction.")
        self.guild_id = guild_id
        self.requester_name = requester_name
        self.requester_id = requester_id
        self.character_name = character_name
        self.recipient_name = recipient_name  # Name of the recipient
        self.bot = bot
        self.embed = None
        self.requesting_kingdom = requesting_kingdom
        self.sending_kingdom = sending_kingdom
        self.seafood = seafood
        self.husbandry = husbandry
        self.grain = grain
        self.produce = produce
        self.textiles = textiles
        self.metallurgy = metallurgy
        self.woodworking = woodworking
        self.stoneworking = stoneworking
        self.magical_consumables = magical_consumables
        self.magical_items = magical_items
        self.mundane_exotic = mundane_exotic
        self.mundane_complex = mundane_complex
        self.lumber = lumber
        self.stone = stone
        self.ore = ore
        self.raw_textiles = raw_textiles

    async def accepted(self, interaction: discord.Interaction):
        """Handle the approval logic."""
        # Update the database to mark the proposition as accepted
        # Adjust prestige, log the transaction, notify the requester, etc.

        self.embed = discord.Embed(
            title=f"<@{self.requester_id}>'s Kingdom of {self.requesting_kingdom} has opened trade with <@{self.allowed_user_id}>'s kingdom of {self.sending_kingdom}",
            description=f"The request of trade has been accepted by <@{self.allowed_user_id}>'s {self.sending_kingdom}.",
            color=discord.Color.green()
        )
        # Additional logic such as notifying the requester
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """INSERT INTO KB_Trade (Source_Kingdom, End_Kingdom, Seafood, Husbandry, Grain, Produce, Lumber, Stone, Metal, Raw_Textiles, Textiles, Metallurgy, Woodworking, Stoneworking, Magical_Consumables, Magical_Items, Mundane_Exotic, Mundane_Complex) "
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.sending_kingdom, self.requesting_kingdom, self.seafood, self.husbandry, self.grain, self.produce,
                 self.lumber, self.stone, self.metal, self.raw_textiles, self.textiles, self.metallurgy,
                 self.woodworking, self.stoneworking, self.magical_consumables, self.magical_items, self.mundane_exotic,
                 self.mundane_complex))
            await conn.commit()

    async def rejected(self, interaction: discord.Interaction):
        """Handle the rejection logic."""
        # Update the database to mark the proposition as rejected
        self.embed = discord.Embed(
            title=f"{self.character_name}'s Transaction Rejected",
            description=f"The request of \r\n {self.reason} \r\n has been rejected by <@{self.allowed_user_id}>'s {self.recipient_name}.",
            color=discord.Color.red()
        )
        # Additional logic such as notifying the requester

    async def create_embed(self):
        """Create the initial embed for the proposition."""
        self.embed = discord.Embed(
            title=f"{self.character_name}'s Trade Request",
            description=f"{self.character_name} has requested to trade with {self.recipient_name}.\n"
                        f"Please accept or reject this transaction.",
            color=discord.Color.blurple()
        )
        if any((self.seafood, self.produce, self.grain, self.husbandry)):
            self.embed.add_field(name="Food",
                                 value=f"Seafood: {self.seafood}\nProduce: {self.produce}\nGrain: {self.grain}\nHusbandry: {self.husbandry}")
        if any((self.ore, self.stone, self.lumber, self.raw_textiles)):
            self.embed.add_field(name="Raw Materials",
                                 value=f"Ore: {self.ore}\nStone: {self.stone}\nLumber: {self.lumber}\nRaw Textiles: {self.raw_textiles}")
        if any((self.textiles, self.metallurgy, self.woodworking, self.stoneworking)):
            self.embed.add_field(name="Crafts",
                                 value=f"Textiles: {self.textiles}\nMetallurgy: {self.metallurgy}\nWoodworking: {self.woodworking}\nStoneworking: {self.stoneworking}")
        if any((self.magical_consumables, self.magical_items, self.mundane_exotic, self.mundane_complex)):
            self.embed.add_field(name="Specialty",
                                 value=f"Magical Consumables: {self.magical_consumables}\nMagical Items: {self.magical_items}\nMundane Exotic: {self.mundane_exotic}\nMundane Complex: {self.mundane_complex}")
        self.embed.set_author(name=self.requester_name)
        self.embed.set_footer(text="Please accept or reject this transaction before it expires.")


logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='application.log',  # Log to a file
    filemode='a'  # Append to the file
)
