import asyncio
import datetime
import logging
import math
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
                 stability: float, hexes: int, modifier: int):
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

        # Attribute Selection
        if options is None or len(options) == 0:
            self.stop()
        elif len(options) == 1:
            self.attribute = options[0].value
            # Proceed to modifier selection
            asyncio.create_task(self.proceed_to_modifier_selection())
        else:
            # Multiple attributes, show selection
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
            await cursor.execute(
                """select Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = ?""", (alignment,))
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
                INSERT INTO kb_Kingdoms (
                Kingdom, Password, Government, Alignment, Region, Size, Population, 
                Economy, Loyalty, Stability, 
                Fame, Unrest, Consumption,
                Control_DC, Build_Points,
                Stored_seafood, Stored_meat, Stored_grain, Stored_produce,
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
        await cursor.execute("""SELECT SUM(VPEconomy), SUM(VPLoyalty), SUM(VPStability), SUM(VPUnrest) FROM AA_Leadership_Roles""")
        vp_info = await cursor.fetchone()
        await cursor.execute("""UPDATE kb_Kingdoms SET Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ? WHERE Kingdom = ?""",
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
                (new_corruption, new_crime, new_law, new_lore, new_productivity, new_society) = new_government_info
                (old_corruption, old_crime, old_law, old_lore, old_productivity, old_society) = old_government_info
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
        amount: int) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Build_Points FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
            kingdom_info = await cursor.fetchone()
            if kingdom_info is None:
                return "The kingdom does not exist."
            if amount < 0:
                amount = max(amount, -kingdom_info[0])
            await cursor.execute("UPDATE kb_Kingdoms SET Build_Points = Build_Points + ? WHERE Kingdom = ?",
                                 (amount, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "kb_Kingdoms", "Increase BP",
                 f"Increased the build points of {kingdom} by {amount}"))
            await db.commit()
            return f"The build points of {kingdom} have been increased by {amount}."
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
                "UPDATE kb_Leadership Set Character_Name = ?, Stat = ?, Modifier = ?, Economy = ?, Loyalty = ?, Stability = ?, unrest = ? WHERE Kingdom = ? AND Title = ?",
                (character_name, stat, modifier, economy, loyalty, stability, 0, kingdom, title))
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
                "UPDATE kb_Leadership SET Character_Name = 'Vacant', Stat = Null, Modifier = Null, Economy = ?, Loyalty = ? , Stability = ?, Unrest = ? WHERE Kingdom = ? AND Title = ?",
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
            await cursor.execute("UPDATE kb_Kingdoms SET Size = Size + 1, Control_DC = Control_DC + 1 WHERE Kingdom = ?",
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
            await cursor.execute("Update kb_hexes set Kingdom = Null WHERE Hex_ID = ? and Kingdom = ?", (hex_id, kingdom))
            await cursor.execute("UPDATE kb_Kingdoms SET Size = Size - 1, Control_DC = Control_DC - 1 WHERE Kingdom = ?",
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
                max_amount = min(base_hex_info[f'{improvement_info["Type"]}'] - constructed, amount, build_points // cost_modifier)
                build_cost = max_amount * cost_modifier
            else:
                max_amount = min(base_hex_info[f'{improvement_info["Type"]}'] - constructed, amount)
                build_cost = 0
            await cursor.execute("Update Kingdoms Set Build_Points = Build_Points - ?, economy = economy + ?, Loyalty = loyalty + ?, Stability = stability + ?, Unrest = unrest + ? WHERE Kingdom = ?",
                                 (build_cost, improvement_info['Economy'] * max_amount, improvement_info['Loyalty'] * max_amount, improvement_info['Stability'] * max_amount, improvement_info['Unrest'] * max_amount,  kingdom))
            if not availability:
                await cursor.execute("""
                INSERT into KB_Hexes_Constructed(ID, Full_Name, Type, Subtype, Quality, Amount, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation) 
                VALUES 
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (hex_id, improvement_info['Full_name'], improvement_info['Type'], improvement_info['Subtype'], improvement_info['Quality'], max_amount, improvement_info['Economy'], improvement_info['Loyalty'], improvement_info['Stability'], improvement_info['Unrest'], improvement_info['Consumption'], improvement_info['Defence'], improvement_info['Taxation']))
            else:
                await cursor.execute(
                    "UPDATE kb_hexes_constructed SET Amount = Amount + ? WHERE Full_Name = ? and ID = ?",
                    (max_amount, improvement, hex_id))
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
                (amount, amount * hex_information.economy, amount * hex_information.loyalty, amount * hex_information.stability, amount * hex_information.unrest,
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
            await cursor.execute("Select Amount from KB_Hexes_Constructed where Full_Name = ? and id = ?", (old_full_name, hex_Id))
            availability = await cursor.fetchone()
            if not availability:
                return f"No improvements of {old_full_name} are present."
            amount = min(amount, availability[0])
            await cursor.execute("Select Full_Name from KB_Hexes_Improvements where Full_Name = ? and id = ?", (new_full_name,hex_id))
            new_improvement = await cursor.fetchone()
            if not new_improvement:
                return f"No improvements of {new_full_name} are present."
            await cursor.execute("Select Amount from KB_Hexes_Constructed where Full_Name = ?", (new_full_name,))
            new_availability = await cursor.fetchone()
            if availability[0] == amount and not new_availability:
                await cursor.execute("UPDATE KB_Hexes_Constructed set Full_Name = ? where Full_Name = ? and id = ?", (new_full_name, old_full_name, hex_id))
            elif availability[0] == amount and new_availability:
                await cursor.execute("UPDATE KB_Hexes_Constructed set Amount = Amount + ? where Full_Name = ? and id = ?", (amount, new_full_name, hex_id))
                await cursor.execute("DELETE from KB_Hexes_Constructed where Full_Name = ? and id = ?", (old_full_name,hex_id))
            elif availability[0] != amount and not new_availability:
                await cursor.execute("UPDATE KB_Hexes_Constructed set Amount = Amount - ? where Full_Name = ? and id = ?", (amount, old_full_name, hex_id))
                await cursor.execute("""INSERT into KB_Hexes_Constructed (ID, Full_Name, Type, Subtype, Quality, Amount, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation)
                SELECT ?, full_name, Type, Subtype, Quality, ?, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation FROM KB_Hexes_Improvements where Full_Name = ?""", (hex_id, amount, new_full_name))
            else:
                await cursor.execute("UPDATE KB_Hexes_Constructed set Amount = Amount + ? where Full_Name = ? and id = ?", (amount, new_full_name, hex_id))
                await cursor.execute("UPDATE KB_Hexes_Constructed set Amount = Amount - ? where Full_Name = ? and id = ?", (amount, old_full_name, hex_id))
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


class KingdomCommands(commands.Cog, name='Kingdom'):
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
                await cursor.execute("""select Kingdom, Password FROM kb_Kingdoms where Kingdom = ?""",(kingdom,))
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
            if new_password:
                new_password = encrypt_password(new_password)
                async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                    cursor = await db.cursor()
                    await cursor.execute("UPDATE kb_Kingdoms SET Password = ? WHERE Kingdom = ?",
                                         (new_password, old_kingdom))
                    await db.commit()
            kingdom_info.password = new_password if new_password else kingdom_info.password
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
                        gold=character_info[0],
                        gold_value=character_info[1],
                        gold_value_max=character_info[2],
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
                        gold=Decimal(character_info[0]),
                        gold_value=Decimal(character_info[1]),
                        gold_value_max=Decimal(character_info[2]),
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
        except (aiosqlite, TypeError, ValueError) as e:
            logging.exception(f"Error increasing build points: {e}")
            await interaction.followup.send(content="An error occurred while increasing build points.")

    @leadership_group.command(name="modify",
                              description="Modify a leader, by changing their ability score or who is in charge")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(title=leadership_autocomplete)
    @app_commands.autocomplete(character_name=shared_functions.character_select_autocompletion)
    async def modify_leadership(self, interaction: discord.Interaction, kingdom: str, password: str, character_name: str, title: str,
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
                await cursor.execute(
                    "SELECT Ability, Economy, Loyalty, Stability FROM AA_Leadership_Roles WHERE Title = ?",
                    (title, ))
                leadership_info = await cursor.fetchone()
                (ability, economy, loyalty, stability) = leadership_info
                abilities = ability.split(" / ")
                options = [
                    discord.SelectOption(label=ability) for ability in abilities
                ]
                additional = 1 if title != "Ruler" and kingdom_results[1] < 26 else 2
                additional = 3 if title == "Ruler" and kingdom_results[1] < 101 else additional
                view = LeadershipView(
                    options, interaction.guild_id, interaction.user.id, kingdom, title, character_name,
                    additional, economy, loyalty, stability, kingdom_results[1], modifier=modifier
                )
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
    @app_commands.autocomplete(hex_terrain=hex_terrain_autocomplete)
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
                    await interaction.followup.send(content=f"The hex of {hex_id} is already claimed by {hex_results[0]}.")
                    return
                elif hex_results[1] != kingdom_results[1]:
                    await interaction.followup.send(content=f"The hex of {hex_id} is not in the kingdom's region of {kingdom_results[1]}.")
                    return
                status = await claim_hex(guild_id=interaction.guild_id, author=interaction.user.id, kingdom=kingdom,
                                         hex_id=hex_id)
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error claiming hex: {e}")
            await interaction.followup.send(content="An error occurred while claiming a hex.")

    @hex_group.command(name="relinquish", description="relinquish a hex for a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(hex_terrain=hex_terrain_autocomplete)
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
    @app_commands.autocomplete(hex_terrain=hex_terrain_autocomplete)
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
                await cursor.execute("SELECT Password, Build_Points, Size FROM kb_Kingdoms WHERE Kingdom = ?", (kingdom,))
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
    async def claim_settlement(self, interaction: discord.Interaction, kingdom: str, password: str, settlement: str, hex_id: int):
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
                    await interaction.followup.send(content="The hex has improvements built upon it and cannot share them with a settlement!")
                    return
                status = await claim_a_settlement(interaction.guild_id, interaction.user.id, kingdom, settlement, hex_id)
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

                await cursor.execute("SELECT Kingdom from KB_Buildings_Permits where Kingdom = ? AND Building_Name = ?", (kingdom, building))
                permits = await cursor.fetchone()
                if permits is None:
                    await interaction.followup.send(content="The kingdom does not have a permit for this building.")
                    return
                building_info = await fetch_building(interaction.guild_id, building)
                cost = building_info.build_points * amount
                await cursor.execute("SELECT SUM(Amount * Quality) from KB_Buildings where Kingdom = ? and Settlement = ? and Subtype = 'Housing'", (kingdom, settlement))
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
                    await cursor.execute("UPDATE KB_Buildings SET Discounted = Discounted + ? WHERE Kingdom = ? and Settlement = ? and Full_Name = ?", (discounted_change, kingdom, settlement, full_name))
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

    @settlement_group.command(name="Upgrade", description="upgrade a building in a settlement")
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
                await cursor.execute("Select Amount from KB_Buildings where Kingdom = ? and Settlement = ? and Full_Name = ?", (kingdom, settlement, building))
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



    @settlement_group.command(name="Repurpose", description="Change the behavior of a building")
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
                await cursor.execute("Select Amount from KB_Buildings where Kingdom = ? and Settlement = ? and Full_Name = ?", (kingdom, settlement, old_purpose))
                settlement_info = await cursor.fetchone()
                if not settlement_info:
                    await interaction.followup.send(content=f"Settlement of {settlement} has no {old_purpose} buildings built!")
                    return
                amount = min(amount, settlement_info[0])
                await cursor.execute("Select Amount from KB_Buildings where Kingdom = ? and Settlement = ? and Full_Name = ?", (kingdom, settlement, new_purpose))
                new_building_count = await cursor.fetchone()
                old_building_info = await fetch_building(interaction.guild_id, old_purpose)
                new_building_info = await fetch_building(interaction.guild_id, new_purpose)
                if old_building_info.type != new_building_info.type:
                    await interaction.followup.send(content=f"Building types do not match!")
                    return
                if not new_building_count and amount == settlement_info[0]:
                    await cursor.execute("UPDATE KB_Buildings Set Full_Name = ?, Subtype = ? where Kingdom = ? and Settlement = ? and Full_Name = ?", (new_purpose, new_building_info.subtype, kingdom, settlement, old_purpose))
                elif new_building_count and amount == settlement_info[0]:
                    await cursor.execute("UPDATE KB_Buildings Set Amount = Amount + ? where Kingdom = ? and Settlement = ? and Full_Name = ?", (amount, kingdom, settlement, new_purpose))
                    await cursor.execute("DELETE FROM KB_Buildings where Kingdom = ? and Settlement = ? and Full_Name = ?", (kingdom, settlement, old_purpose))
                else:
                    await cursor.execute("UPDATE KB_Buildings Set Amount = Amount + ? where Kingdom = ? and Settlement = ? and Full_Name = ?", (amount, kingdom, settlement, new_purpose))
                    await cursor.execute("UPDATE KB_Buildings Set Amount = Amount - ? where Kingdom = ? and Settlement = ? and Full_Name = ?", (amount, kingdom, settlement, old_purpose))
                await interaction.followup.send(content=f"{amount} {old_purpose} buildings have been repurposed into {new_purpose}!")
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error repurposing building: {e}")
            await interaction.followup.send(content="An error occurred while repurposing a building.")





class KingdomView(shared_functions.ShopView):
    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int, interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, interaction=interaction,
                         content="")
        self.max_items = None  # Cache total number of items
        self.content = None

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""

        statement = """
                        SELECT kb_Kingdom, kb_Government, kb_Alignment, kb_Control_DC, kb_Build_Points, 
                        kb_Size, kb_Population, kb_Economy, kb_Loyalty, kb_Stability,
                        kb_Unrest, kb_Consumption, 
                        Custom.Control_DC, Custom.Economy, Custom.Loyalty, Custom.Stability, Custom.Unrest, Custom.Consumption
                        FROM kb_Kingdoms as KB left join kb_Kingdoms_Custom as Custom on kb_Kingdom = Custom.Kingdom 
                        Limit ? Offset ?
                    """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(
            title=f"kb_Kingdoms",
            description=f"Page {current_page} of {total_pages}")
        for item in self.results:
            (kingdom, government, alignment, control_dc, build_points, size, population, economy,
             loyalty, stability, unrest, consumption, custom_control_dc, custom_economy, custom_loyalty,
             custom_stability, custom_unrest, custom_consumption) = item
            self.embed.add_field(name=f'**__Kingdom__**: {kingdom}, Control DC: {control_dc}', value=f"""
            **Government**: {government}, **Alignment**: {alignment}\n
            **Resources**: {build_points} BP, \n
            **Size**: {size}, **Population**: {population}\n
            **Economy**: {economy}, **Loyalty**: {loyalty}, **Stability**: {stability}\n
            **Unrest**: {unrest}, **Consumption**: {consumption}\n
            **Unique Modifiers** **Control DC Adjustment**: {custom_control_dc}, \n
             **Economy Adjustment**: {custom_economy} **Loyalty Adjustment**: {custom_loyalty}, **Stability Adjustment**: {custom_stability}\n
            **Unrest Adjustment**: {custom_unrest}, **Consumption Adjustment**: {custom_consumption}""", inline=False)
            '''self.embed.add_field(name="**Command Card Adjustments**", value=f"""
            **Control DC Adjustment**: {custom_control_dc}, \n
            **Economy Adjustment**: {custom_economy} **Loyalty Adjustment**: {custom_loyalty}, **Stability Adjustment**: {custom_stability}\n   
            **Unrest Adjustment**: {custom_unrest}, **Consumption Adjustment**: {custom_consumption}""", inline=False)'''

    async def get_max_items(self):
        """Get the total number of titles."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM kb_Kingdoms")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class SettlementView(shared_functions.ShopView):
    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int, interaction: discord.Interaction, kingdom: str):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, interaction=interaction,
                         content="")
        self.max_items = None  # Cache total number of items
        self.content = None
        self.kingdom = kingdom

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""

        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            if self.kingdom:
                statement = """ 
                SELECT kb_Kingdom, kb_Settlement, kb_Size, kb_Population, kb_Corruption, kb_Crime, kb_Productivity, kb_Law, kb_Lore, kb_Society, kb_Danger, kb_Defence,
                kb_Base_Value, kb_Spellcasting, kb_Supply, kb_Decay, Custom.Corruption, Custom.Crime, Custom.Productivity, Custom.Law, Custom.Lore, Custom.Society, Custom.Danger, Custom.Defence,
                Custom.Base_Value, Custom.Spellcasting, Custom.Supply
                FROM kb_settlements as KB left join kb_settlements_Custom as Custom on kb_settlement = custom.settlement WHERE Kingdom = ? Limit ? Offset ?
                """
                cursor = await db.execute(statement, (self.kingdom, self.limit, self.offset))
            else:
                statement = """
                SELECT kb_Kingdom, kb_Settlement, kb_Size, kb_Population, kb_Corruption, kb_Crime, kb_Productivity, kb_Law, kb_Lore, kb_Society, kb_Danger, kb_Defence,
                kb_Base_Value, kb_Spellcasting, kb_Supply, kb_Decay, Custom.Corruption, Custom.Crime, Custom.Productivity, Custom.Law, Custom.Lore, Custom.Society, Custom.Danger, Custom.Defence,
                Custom.Base_Value, Custom.Spellcasting, Custom.Supply
                FROM kb_settlements as KB left join kb_settlements_Custom as Custom on kb_settlement = custom.settlement Limit ? Offset ?
                """
                cursor = await db.execute(statement, (self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        if self.kingdom:
            self.embed = discord.Embed(
                title=f"kb_settlements for {self.kingdom}",
                description=f"Page {current_page} of {total_pages}")
        else:
            self.embed = discord.Embed(
                title=f"kb_settlements",
                description=f"Page {current_page} of {total_pages}")

        for item in self.results:
            (group_id, player_name) = item
            self.embed.add_field(name=f'**Player**: {player_name}', value=f'**Group**: {group_id}', inline=False)
            (kingdom, settlement, size, population, corruption, crime, productivity, law, lore, society, danger, defence,
             base_value, spellcasting, supply, decay, custom_corruption, custom_crime, custom_productivity, custom_law,
             custom_lore, custom_society, custom_danger, custom_defence, custom_base_value, custom_spellcasting,
             custom_supply) = item
            self.embed.add_field(name=f'**Kingdom**: {kingdom} **Settlement**: {settlement}', value=f"""
            **Size**: {size}, **Population**: {population}\n
            **Corruption**: {corruption}, **Crime**: {crime}, **Productivity**: {productivity}\n
            **Law**: {law}, **Lore**: {lore}, **Society**: {society}\n
            **Danger**: {danger}, **Defence**: {defence}\n
            **Base Value**: {base_value}, **Spellcasting**: {spellcasting}, **Supply**: {supply}\n
            **Decay**: {decay}\n
            **Custom Modifiers** **Corruption**: {custom_corruption}, **Crime**: {custom_crime}, **Productivity**: {custom_productivity}\n
            **Law**: {custom_law}, **Lore**: {custom_lore}, **Society**: {custom_society}\n
            **Danger**: {custom_danger}, **Defence**: {custom_defence}\n
            **Base Value**: {custom_base_value}, **Spellcasting**: {custom_spellcasting}, **Supply**: {custom_supply}
            """, inline=False)
            '''self.embed.add_field(name="**Command Card Adjustments**", value=f"""
            **Corruption**: {custom_corruption}, **Crime**: {custom_crime}, **Productivity**: {custom_productivity}\n
            **Law**: {custom_law}, **Lore**: {custom_lore}, **Society**: {custom_society}\n
            **Danger**: {custom_danger}, **Defence**: {custom_defence}\n
            **Base Value**: {custom_base_value}, **Spellcasting**: {custom_spellcasting}, **Supply**: {custom_supply}
            """, inline=False)'''
    async def get_max_items(self):
        """Get the total number of titles."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                if self.kingdom:
                    cursor = await db.execute("SELECT COUNT(*) FROM kb_settlements WHERE Kingdom = ?",
                                              (self.kingdom,))
                else:
                    cursor = await db.execute("SELECT COUNT(*) FROM kb_settlements")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class HexView(shared_functions.ShopView):
    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int, kingdom: str,
                 interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, interaction=interaction,
                         content="")
        self.max_items = None  # Cache total number of items
        self.content = None
        self.kingdom = kingdom

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""

        statement = """
                        SELECT 
                        Kingdom, Hex_Terrain, Amount, Improvement,
                        Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation
                        from kb_hexes WHERE Kingdom = ? Limit ? Offset ?
                    """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.kingdom, self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(
            title=f"Hexes for {self.kingdom}",
            description=f"Page {current_page} of {total_pages}")

        for item in self.results:
            (kingdom, hex_terrain, amount, improvement, economy, loyalty, stability, unrest, consumption, defence,
             taxation) = item
            self.embed.add_field(name=f'**Improvement**: {improvement} **Hex Terrain**: {hex_terrain}', value=f"""
            **Amount**: {amount}\n
            **Economy**: {economy}, **Loyalty**: {loyalty}, **Stability**: {stability}\n
            **Unrest**: {unrest}, **Consumption**: {consumption}\n
            **Defence**: {defence}, **Taxation**: {taxation}""", inline=False)
    async def get_max_items(self):
        """Get the total number of titles."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM kb_hexes WHERE Kingdom = ?",
                                          (self.kingdom,))
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class ImprovementView(shared_functions.ShopView):
    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int,
                 interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, interaction=interaction,
                         content="")
        self.max_items = None  # Cache total number of items
        self.content = None

    def if_value_then_True(self, value):
        if value:
            return True
        return False

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""

        statement = """
                        SELECT Improvement, Road_Multiplier, Build_Points,
                        Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation,
                        Cavernous, Coastline, Desert, Forest, Hill, Jungle, Marsh, Mountain, Plains, Swamp, Tundra, Water
                        FROM kb_Hexes_Improvements Limit ? Offset ?
                    """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(
            title=f"Improvements for kb_hexes",
            description=f"Page {current_page} of {total_pages}")

        for item in self.results:
            (improvement, road_multiplier, build_points, economy, loyalty, stability, unrest, consumption, defence,
             taxation, cavernous, coastline, desert, forest, hill, jungle, marsh, mountain, plains, swamp, tundra,
             water) = item
            base_text = """**Road Multiplier**: {road_multiplier}, **Build Points**: {build_points}\n
            **Economy**: {economy}, **Loyalty**: {loyalty}, **Stability**: {stability}\n
            **Unrest**: {unrest}, **Consumption**: {consumption}\n
            **Defence**: {defence}, **Taxation**: {taxation}\n 
            __**Available Terrains***__\n"""
            available_terrains = []
            if cavernous:
                available_terrains.append("Cavernous")
            if coastline:
                available_terrains.append("Coastline")
            if desert:
                available_terrains.append("Desert")
            if forest:
                available_terrains.append("Forest")
            if hill:
                available_terrains.append("Hill")
            if jungle:
                available_terrains.append("Jungle")
            if marsh:
                available_terrains.append("Marsh")
            if mountain:
                available_terrains.append("Mountain")
            if plains:
                available_terrains.append("Plains")
            if swamp:
                available_terrains.append("Swamp")
            if tundra:
                available_terrains.append("Tundra")
            if water:
                available_terrains.append("Water")
            available_terrains = ", ".join(available_terrains)
            base_text += f"{available_terrains}"
            self.embed.add_field(name=f'**Improvement**: {improvement}', value=base_text)

    async def get_max_items(self):
        """Get the total number of titles."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM kb_Hexes_Improvements")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class BlueprintView(shared_functions.ShopView):
    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int,
                 interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, interaction=interaction,
                         content="")
        self.max_items = None  # Cache total number of items
        self.content = None

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""

        statement = """
                        SELECT 
                        Building, Build_Points, Economy, Loyalty, Stability, Fame, Unrest,
                        Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence,
                        Base_Value, Spellcasting, Supply,
                        Settlement_Limit, District_Limit, Description
                        from Buildings Limit ? Offset ?
                    """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.group_id, self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(
            title=f"Blueprints",
            description=f"Page {current_page} of {total_pages}")

        for item in self.results:
            (building, build_points, economy, loyalty, stability, fame, unrest, corruption, crime, productivity, law,
             lore, society, danger, defence, base_value, spellcasting, supply, decay, settlement_limit, district_limit,
             description) = item
            self.embed.add_field(name=f'**Building**: {building}, Cost: {build_points}', value=f"""
            **Economy**: {economy}, **Loyalty**: {loyalty}, **Stability**: {stability}, **Fame**: {fame}\n
            **Unrest**: {unrest}, **Corruption**: {corruption}, **Crime**: {crime}, **Productivity**: {productivity}\n
            **Law**: {law}, **Lore**: {lore}, **Society**: {society}, **Danger**: {danger}\n
            **Defence**: {defence}, **Base Value**: {base_value}, **Spellcasting**: {spellcasting}, **Supply**: {supply}\n
            **Settlement Limit**: {settlement_limit}, **District Limit**: {district_limit}\n
            **Description**: {description}""", inline=False)


    async def get_max_items(self):
        """Get the total number of titles."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM kb_Buildings_Blueprints")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items



logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='application.log',  # Log to a file
    filemode='a'  # Append to the file
)
