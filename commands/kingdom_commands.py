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


@dataclass
class HexImprovementInfo:
    improvement: str
    road_multiplier: int
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
            "SELECT Building FROM Buildings_Blueprints WHERE Building LIKE ? Limit 20",
            (f"%{current}%",))
        blueprint_list = await cursor.fetchall()
        for blueprint in blueprint_list:
            if current in blueprint[0]:
                data.append(app_commands.Choice(name=blueprint[0], value=blueprint[0]))
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
        for hexes in hex_list:
            if current in hexes[0]:
                data.append(app_commands.Choice(name=hexes[0], value=hexes[0]))

    return data


async def hex_improvement_autocomplete(
        interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
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


async def leadership_autocomplete(
        interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
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
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
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


async def settlement_autocomplete(interaction: discord.Interaction, current: str
                                  ) -> typing.List[app_commands.Choice[str]]:
    data = []
    guild_id = interaction.guild_id
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
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
            logging.exception(f"Error in LeadershipModifier callback: {e}")
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
                modifier=self.economy_modified + self.loyalty_modified + self.stability_modified,
                economy=self.economy_modified,
                loyalty=self.loyalty_modified,
                stability=self.stability_modified
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
        password: str,
        government: str,
        alignment: str) -> str:
    try:
        hashed_password = encrypt_password(password)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
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
                await cursor.execute(
                    "INSERT Into Kingdoms_Custom(Kingdom, Control_DC, Economy, Loyalty, Stability, Fame, Unrest, Consumption) VALUES (?, 0, 0, 0, 0, 0, 0, 0)",
                    (kingdom,))
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
                    "UPDATE Settlements SET Corruption = Corruption + ?, Crime = Crime + ?, Law = Law + ?, Lore = Lore + ?, Productivity = Productivity + ?, Society = Society + ? WHERE Kingdom = ?",
                    (sum_corruption, sum_crime, sum_law, sum_lore, sum_productivity, sum_society,
                     old_kingdom_info.kingdom))
            await cursor.execute(
                "UPDATE Kingdoms SET Kingdom = ?, Password = ?, Government = ?, Alignment = ?, Economy = ?, Loyalty = ?, Stability = ? WHERE Kingdom = ?",
                (new_kingdom, government, alignment, old_kingdom_info.economy, old_kingdom_info.loyalty,
                 old_kingdom_info.stability, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE Kingdoms_Custom SET Kingdom = ? WHERE Kingdom = ?",
                                 (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE settlements SET Kingdom = ? WHERE Kingdom = ?",
                                 (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE settlements_Custom SET Kingdom = ? WHERE Kingdom = ?",
                                 (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute("UPDATE Hexes SET Kingdom = ? WHERE Kingdom = ?",
                                 (new_kingdom, old_kingdom_info.kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Kingdoms", "Edit",
                 f"Edited the kingdom of {old_kingdom_info.kingdom} to {new_kingdom}"))
            await db.commit()
            return f"The kingdom of {old_kingdom_info.kingdom} has been edited to {new_kingdom}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error creating a kingdom: {e}")
        return "An error occurred while creating a kingdom."


async def delete_a_kingdom(
        guild_id: int, author: int, kingdom: str) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("DELETE FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM Kingdoms_Custom WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM settlements WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM settlements_Custom WHERE Kingdom = ?", (kingdom,))
            await cursor.execute("DELETE FROM Hexes WHERE Kingdom = ?", (kingdom,))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Kingdoms", "Delete", f"Deleted the kingdom of {kingdom}"))
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
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Build_Points FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
            kingdom_info = await cursor.fetchone()
            if kingdom_info is None:
                return "The kingdom does not exist."
            if amount < 0:
                amount = max(amount, -kingdom_info[0])
            await cursor.execute("UPDATE Kingdoms SET Build_Points = Build_Points + ? WHERE Kingdom = ?",
                                 (amount, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Kingdoms", "Increase BP",
                 f"Increased the build points of {kingdom} by {amount}"))
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
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Stabilization_Points FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
            kingdom_info = await cursor.fetchone()
            if kingdom_info is None:
                return "The kingdom does not exist."
            if amount < 0:
                amount = min(amount, -kingdom_info[0])
            await cursor.execute(
                "UPDATE Kingdoms SET Stabilization_Points = Stabilization_Points + ? WHERE Kingdom = ?",
                (amount, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Kingdoms", "Increase SP",
                 f"Increased the stabilization points of {kingdom} by {amount}"))
            await db.commit()
            return f"The stabilization points of {kingdom} have been increased by {amount}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error increasing stabilization points: {e}")
        return "An error occurred while increasing stabilization points."


async def fetch_kingdom(
        guild_id: int,
        kingdom: str) -> typing.Union[KingdomInfo, None]:
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
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
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
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
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
        cursor = await db.cursor()
        await cursor.execute(
            """SELECT Building, Build_Points, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Settlement_Limit, District_Limit, Description FROM Buildings_Blueprints WHERE Building = ?""",
            (building,))
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
            """SELECT Improvement, Road_Multiplier, Build_Points, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation, Cavernous, Coastline, Desert, Forest, Hills, Jungle, Marsh, Mountains, Plains, Water FROM Hexes_Improvements WHERE Improvement = ?""",
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
                "SELECT Economy, Loyalty, Stability, Unrest FROM Leadership WHERE Kingdom = ? AND Title = ?",
                (kingdom, title))
            leader_info = await cursor.fetchone()
            if leader_info is None:
                return "The leader does not exist."
            (old_economy, old_loyalty, old_stability, old_unrest) = leader_info
            sum_economy = economy - old_economy
            sum_loyalty = loyalty - old_loyalty
            sum_stability = stability - old_stability
            await cursor.execute(
                "UPDATE Leadership Set Character_Name = ?, Stat = ?, Modifier = ?, Economy = ?, Loyalty = ?, Stability = ? WHERE Kingdom = ? AND Title = ?",
                (character_name, stat, modifier, economy, loyalty, stability, kingdom, title))
            await cursor.execute(
                "UPDATE Kingdoms SET Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ? WHERE Kingdom = ?",
                (sum_economy, sum_loyalty, sum_stability, -old_unrest, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Leadership", "Update",
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
                "SELECT Economy, Loyalty, Stability, Unrest FROM Leadership WHERE Kingdom = ? AND Title = ?",
                (kingdom, title))
            leader_info = await cursor.fetchone()
            await cursor.execute(
                "SELECT VPEconomy, VPLoyalty, VPStability, VPUnrest FROM AA_Leadership WHERE Title = ?", (title,))
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
                "UPDATE Leadership SET Character_Name = 'Vacant', Economy = ?, Loyalty = ? , Stability = ?, Unrest = ? WHERE Kingdom = ? AND Title = ?",
                (base_economy, base_loyalty, base_stability, base_unrest, kingdom, title))
            await cursor.execute(
                "UPDATE Kingdoms SET Economy = Economy - ?, Loyalty = Loyalty - ?, Stability = Stability - ?, Unrest = Unrest - ? WHERE Kingdom = ?",
                (sum_economy, sum_loyalty, sum_stability, sum_unrest, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Leadership", "Remove", f"Removed the leader of {kingdom}"))
            await db.commit()
            return f"The leader of {kingdom} has been removed."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error removing leader: {e}")
        return "An error occurred while removing the leader."


async def claim_hex(
        guild_id: int,
        author: int,
        kingdom: str,
        hex_terrain: str) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Kingdom FROM Hexes WHERE Hex_Terrain = ? and Improvement is Null",
                                 (hex_terrain,))
            hex_info = await cursor.fetchone()
            if hex_info is not None:
                await cursor.execute(
                    "Update Hexes set Amount = Amount + 1 WHERE Hex_Terrain = ? and improvement is Null",
                    (hex_terrain,))
            else:
                await cursor.execute("INSERT INTO Hexes (Kingdom, Hex_Terrain, Amount) VALUES (?, ?, 1)",
                                     (kingdom, hex_terrain))
            await cursor.execute("UPDATE Kingdoms SET Size = Size + 1, Control_DC = Control_DC + 1 WHERE Kingdom = ?",
                                 (kingdom,))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Hexes", "Claim", f"Claimed the hex of {hex_terrain}"))
            await db.commit()
            return f"The hex of {hex_terrain} has been claimed by {kingdom}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error claiming hex: {e}")
        return "An error occurred while claiming the hex."


async def relinquish_hex(
        guild_id: int,
        author: int,
        kingdom: str,
        hex_terrain: str) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Kingdom FROM Hexes WHERE Hex_Terrain = ? and Improvement is Null",
                                 (hex_terrain,))
            hex_info = await cursor.fetchone()
            if hex_info is None:
                return "The hex does not exist."
            await cursor.execute("Update Hexes set Amount = Amount - 1 WHERE Hex_Terrain = ? and improvement is Null",
                                 (hex_terrain,))
            await cursor.execute("UPDATE Kingdoms SET Size = Size - 1, Control_DC = Control_DC - 1 WHERE Kingdom = ?",
                                 (kingdom,))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Hexes", "relinquish", f"Unclaimed the hex of {hex_terrain}"))
            await db.commit()
            return f"The hex of {hex_terrain} has been unclaimed by {kingdom}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error unclaiming hex: {e}")
        return "An error occurred while unclaiming the hex."


async def add_improvement(
        guild_id: int,
        author: int,
        kingdom: str,
        hex_information: HexImprovementInfo,
        hex_terrain: str
) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "SELECT Amount FROM Hexes WHERE Hex_Terrain = ? and Improvement = Null",
                (hex_terrain,))
            availability = await cursor.fetchone()
            if not availability:
                return f"No hexes of {hex_terrain} are available for improvement."
            elif availability[0] == 1:
                await cursor.execute(
                    "DELETE FROM Hexes WHERE Hex_Terrain = ? and Improvement = Null",
                    (hex_terrain,))
            else:
                await cursor.execute(
                    "UPDATE Hexes SET Amount = Amount - 1 WHERE Hex_Terrain = ? and Improvement = Null",
                    (hex_terrain,))
            await cursor.execute("SELECT Amount FROM Hexes WHERE Hex_Terrain = ? and Improvement = ?",
                                 (hex_terrain, hex_information.improvement))
            hex_info = await cursor.fetchone()
            if not hex_info:
                await cursor.execute(
                    "INSERT INTO Hexes (Kingdom, Hex_Terrain, Amount, Improvement, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        kingdom, hex_terrain, hex_information.improvement, hex_information.economy,
                        hex_information.loyalty,
                        hex_information.stability, hex_information.unrest, hex_information.consumption,
                        hex_information.defence, hex_information.taxation))
            else:
                await cursor.execute(
                    "UPDATE Hexes SET Amount = Amount + 1 WHERE Hex_Terrain = ? and Improvement = ?",
                    (hex_terrain, hex_information.improvement))
            await cursor.execute(
                "Update Kingdoms SET Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ?, Consumption = Consumption + ? WHERE Kingdom = ?",
                (hex_information.economy, hex_information.loyalty, hex_information.stability, hex_information.unrest,
                 hex_information.consumption, hex_information.defence, hex_information.taxation, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Hexes", "Add Improvement",
                 f"Added the improvement of {hex_information.improvement} to the hex of {hex_terrain}"))
            await db.commit()
            return f"The improvement of {hex_information.improvement} has been added to the hex of {hex_terrain}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error adding improvement: {e}")
        return "An error occurred while adding the improvement."


async def remove_improvement(
        guild_id: int,
        author: int,
        kingdom: str,
        hex_information: HexImprovementInfo,
        hex_terrain: str
) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "SELECT Amount FROM Hexes WHERE Hex_Terrain = ? and Improvement = ?",
                (hex_terrain, hex_information.improvement))
            availability = await cursor.fetchone()
            if not availability:
                return f"No hexes of {hex_terrain} have the improvement of {hex_information.improvement}."
            elif availability[0] == 1:
                await cursor.execute(
                    "DELETE FROM Hexes WHERE Hex_Terrain = ? and Improvement = ?",
                    (hex_terrain, hex_information.improvement))
            else:
                await cursor.execute(
                    "UPDATE Hexes SET Amount = Amount - 1 WHERE Hex_Terrain = ? and Improvement = ?",
                    (hex_terrain, hex_information.improvement))
            await cursor.execute(
                "Update Kingdoms SET Economy = Economy - ?, Loyalty = Loyalty - ?, Stability = Stability - ?, Unrest = Unrest - ?, Consumption = Consumption - ? WHERE Kingdom = ?",
                (hex_information.economy, hex_information.loyalty, hex_information.stability, hex_information.unrest,
                 hex_information.consumption, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Hexes", "Remove Improvement",
                 f"Removed the improvement of {hex_information.improvement} from the hex of {hex_terrain}"))
            await db.commit()
            return f"The improvement of {hex_information.improvement} has been removed from the hex of {hex_terrain}."
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error removing improvement: {e}")
        return "An error occurred while removing the improvement."


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
                    Building, Constructed, Lots, 
                    Economy, Loyalty, Stability, 
                    Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, 
                    Danger, Defence, Base_Value, Spellcasting, Supply) 
                    VALUES 
                    (?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?)""",
                    (kingdom, settlement,
                     building_info.building, amount, building_info.lots,
                     building_info.economy, building_info.loyalty, building_info.stability,
                     building_info.fame, building_info.unrest, building_info.corruption, building_info.crime,
                     building_info.productivity, building_info.law, building_info.lore, building_info.society,
                     building_info.danger, building_info.defence, building_info.base_value, building_info.spellcasting,
                     building_info.supply))
            else:
                await cursor.execute(
                    "Update Buildings Set Constructed = Constructed + ? WHERE Building = ? and Settlement = ?",
                    (amount, building_info.building, settlement))
            new_population_adjustment = amount * building_info.lots * 250
            new_lots_adjustment = amount * building_info.lots
            new_dc_adjustment = math.floor((size + new_lots_adjustment) / 36) - math.floor(size / 36)
            await cursor.execute(
                "Update Kingdoms Set Control_DC = Control_DC + ?, population = population + ?, Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ? WHERE Kingdom = ?",
                (new_dc_adjustment, new_population_adjustment, building_info.economy, building_info.loyalty,
                 building_info.stability, building_info.unrest, kingdom))
            await cursor.execute(
                "Update Settlements set size = size + ?, population = population + ?, Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ? WHERE Settlement = ?",
                (new_lots_adjustment, new_population_adjustment, building_info.economy, building_info.loyalty,
                 building_info.stability, building_info.unrest, settlement))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Buildings", "Add",
                 f"Added the building of {building_info.building} to the settlement of {settlement}"))
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
                "Update Kingdoms Set Control_DC = Control_DC - ?, population = population - ?, Economy = Economy - ?, Loyalty = Loyalty - ?, Stability = Stability - ?, Unrest = Unrest - ? WHERE Kingdom = ?",
                (new_dc_adjustment, new_population_adjustment, building_info.economy, building_info.loyalty,
                 building_info.stability, building_info.unrest, kingdom))
            await cursor.execute(
                "Update Settlements set size = size - ?, population = population - ?, Economy = Economy - ?, Loyalty = Loyalty - ?, Stability = Stability - ?, Unrest = Unrest - ? WHERE Settlement = ?",
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


async def claim_settlement(
        guild_id: int,
        author: int,
        kingdom: str,
        settlement: str) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT Kingdom FROM Settlements WHERE Settlement = ?", (settlement,))
            settlement_info = await cursor.fetchone()
            if settlement_info is not None:
                return "The settlement is already claimed."
            await cursor.execute(
                "INSERT INTO Settlements (Kingdom, Settlement, Size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay) VALUES (?, ?, 1, 250, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)",
                (kingdom, settlement))
            await cursor.execute(
                "INSERT INTO Settlements_Custom (Kingdom, Settlement, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply) VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)",
                (kingdom, settlement))
            await cursor.execute("UPDATE Kingdoms SET Control_DC = Control_DC + 1 WHERE Kingdom = ?", (kingdom,))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Settlements", "Claim", f"Claimed the settlement of {settlement}"))
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
            await cursor.execute("SELECT Kingdom FROM Settlements WHERE Settlement = ?", (settlement,))
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
                    "UPDATE Kingdoms SET Population = population - ?, Economy = Economy - ?, Loyalty = Loyalty - ?, Stability = Stability - ?, Unrest = Unrest - ? WHERE Kingdom = ?",
                    (population_adjustment, economy * constructed, loyalty * constructed, stability * constructed,
                     unrest * constructed, kingdom))
            control_dc = math.floor(control_dc_lots / 36)
            await cursor.execute("DELETE FROM Buildings WHERE Kingdom = ? and Settlement = ?", (kingdom, settlement))
            await cursor.execute("DELETE FROM Settlements WHERE Settlement = ?", (settlement,))
            await cursor.execute("DELETE FROM Settlements_Custom WHERE Settlement = ?", (settlement,))
            await cursor.execute("UPDATE Kingdoms SET Control_DC = Control_DC - 1 - ? WHERE Kingdom = ?",
                                 (control_dc, kingdom))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Settlements", "relinquish",
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
        description='Commands related to leadership management',
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
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("""select Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'""",
                                     {'kingdom': kingdom})
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

    @kingdom_group.command(name="modify", description="Modify a kingdom")
    @app_commands.autocomplete(old_kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(new_government=government_autocompletion)
    @app_commands.autocomplete(new_alignment=alignment_autocomplete)
    async def modify(self, interaction: discord.Interaction, old_kingdom: str, new_kingdom: typing.Optional[str],
                     old_password: typing.Optional[str],
                     new_password: typing.Optional[str], new_government: typing.Optional[str],
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
                    await cursor.execute("UPDATE Kingdoms SET Password = ? WHERE Kingdom = ?",
                                         (new_password, old_kingdom))
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
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
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
                        gold_value_change=Decimal(0),
                        gold_value_max_change=Decimal(0),
                        is_transaction=False
                    )
                    if gold_reward[0] < cost / 2:
                        await interaction.followup.send(
                            content=f"The character of {character_name} has the oath of {character_info[4]}, this would make selling build points of negligible valuable.")
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
                            source="Adjust BP Commands",
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
                        await shared_functions.log_embed(bot=self.bot, thread=character_info[5],
                                                         guild=interaction.guild, change=update_character_log)
                        await shared_functions.character_embed(guild=interaction.guild, character_name=character_name)
                        await interaction.followup.send(
                            content=f"The character of {character_name} has sold {bought_points} build points for {gold_reward[0]} GP.")
                else:
                    maximum_points = math.floor(character_info[0] / 4000)
                    bought_points = min(amount, maximum_points)
                    cost = bought_points * 4000
                    adjusted_bp_result = await adjust_bp(interaction.guild_id, interaction.user.id, kingdom,
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
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, Stabilization_Points FROM Kingdoms WHERE Kingdom = ?",
                                     (kingdom,))
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
                        gold_value_change=Decimal(0),
                        gold_value_max_change=Decimal(0),
                        is_transaction=False
                    )
                    if gold_reward[0] < cost / 2:
                        await interaction.followup.send(
                            content=f"The character of {character_name} has the oath of {character_info[4]}, this would make selling stabilization points negligibly valuable.")
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
                        await shared_functions.log_embed(bot=self.bot, thread=character_info[5],
                                                         guild=interaction.guild, change=update_character_log)
                        await shared_functions.character_embed(guild=interaction.guild, character_name=character_name)
                        await interaction.followup.send(
                            content=f"The character of {character_name} has sold {bought_points} build points for {gold_reward[0]} GP.")
                else:
                    maximum_points = math.floor(character_info[0] / 4000)
                    bought_points = min(amount, maximum_points)
                    cost = bought_points * 4000
                    adjusted_bp_result = await adjust_sp(interaction.guild_id, interaction.user.id, kingdom,
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

    @leadership_group.command(name="modify",
                              description="Modify a leader, by changing their ability score or who is in charge")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(title=leadership_autocomplete)
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def modify_leadership(self, interaction: discord.Interaction, kingdom, password, character_name, title,
                                modifier):
        """This command is used to modify a leader's ability score or who is in charge of a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password, Hexes FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute(
                    "SELECT Ability, Economy, Loyalty, Stability FROM Leadership WHERE Kingdom = ? AND Title = ?",
                    (kingdom, title))
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
                await interaction.response.send_message("Please select an attribute:", view=view)
            # Store the message object
            view.message = await interaction.original_response()
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error modifying leadership: {e}")
            await interaction.followup.send(content="An error occurred while modifying leadership.")

    @leadership_group.command(name="remove", description="Remove a leader from a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(title=leadership_autocomplete)
    async def remove(self, interaction: discord.Interaction, kingdom: str, password: str, title: str):
        """This command is used to remove a leader and make it a vacant position"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
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
    async def claim(self, interaction: discord.Interaction, kingdom: str, password: str, hex_terrain: str):
        """This command is used to claim a hex for a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("SELECT Hex_Terrain FROM AA_Hex_Terrains WHERE Hex_Terrain = ?", (hex_terrain,))
                hex_results = await cursor.fetchone()
                if not hex_results:
                    await interaction.followup.send(content=f"The hex terrain of {hex_terrain} does not exist.")
                    return
                status = await claim_hex(guild_id=interaction.guild_id, author=interaction.user.id, kingdom=kingdom,
                                         hex_terrain=hex_terrain)
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error claiming hex: {e}")
            await interaction.followup.send(content="An error occurred while claiming a hex.")

    @hex_group.command(name="relinquish", description="relinquish a hex for a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(hex_terrain=hex_terrain_autocomplete)
    async def relinquish_hex(self, interaction: discord.Interaction, kingdom: str, password: str, hex_terrain: str):
        """This command is used to relinquish a hex for a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("SELECT Hex_Terrain FROM AA_Hex_Terrains WHERE Hex_Terrain = ?", (hex_terrain,))
                hex_results = await cursor.fetchone()
                if not hex_results:
                    await interaction.followup.send(content=f"The hex terrain of {hex_terrain} does not exist.")
                    return
                status = await relinquish_hex(interaction.guild_id, interaction.user.id, kingdom, hex_terrain)
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error unclaiming hex: {e}")
            await interaction.followup.send(content="An error occurred while unclaiming a hex.")

    @hex_group.command(name="improve", description="Add an improvement to a hex")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(hex_terrain=hex_terrain_autocomplete)
    @app_commands.autocomplete(improvement=hex_improvement_autocomplete)
    async def add_improvement(self, interaction: discord.Interaction, kingdom: str, password: str, hex_terrain: str,
                              improvement: str):
        """This command is used to add an improvement to a hex"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
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
                status = await add_improvement(interaction.guild_id, interaction.user.id, kingdom, hex_information,
                                               hex_terrain)
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error adding improvement: {e}")
            await interaction.followup.send(content="An error occurred while adding an improvement.")

    @hex_group.command(name="degrade", description="Remove an improvement from a hex")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    @app_commands.autocomplete(hex_terrain=hex_terrain_autocomplete)
    @app_commands.autocomplete(improvement=hex_improvement_autocomplete)
    async def remove_improvement(self, interaction: discord.Interaction, kingdom: str, password: str, hex_terrain: str,
                                 improvement: str):
        """This command is used to remove an improvement from a hex"""
        await interaction.response.defer(thinking=True)
        try:
            async with (aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite")) as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
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

    @settlement_group.command(name="claim", description="Claim a settlement for a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_autocomplete)
    async def claim_settlement(self, interaction: discord.Interaction, kingdom: str, password: str, settlement: str):
        """This command is used to claim a settlement for a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Password FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
            status = await claim_settlement(interaction.guild_id, interaction.user.id, kingdom, settlement)
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
                await cursor.execute("SELECT Password FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
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
                await cursor.execute("SELECT Password, bp FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("Select Size from Settlements where Settlement = ?", (settlement,))
                settlement_info = await cursor.fetchone()
                if settlement_info is None:
                    await interaction.followup.send(content="The settlement is not claimed.")
                    return
                building_info = await fetch_building(interaction.guild_id, building)
                cost = building_info.build_points * amount
                if cost > kingdom_results[1]:
                    await interaction.followup.send(
                        fcontent="The kingdom does not have enough build points. it has {kingdom_results[1]} and needs {cost}.")
                    return
                await cursor.execute("UPDATE Kingdoms SET bp = bp - ? WHERE Kingdom = ?", (cost, kingdom))
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
                await cursor.execute("SELECT Password, BP FROM Kingdoms WHERE Kingdom = ?", (kingdom,))
                kingdom_results = await cursor.fetchone()
                if not kingdom_results:
                    await interaction.followup.send(content=f"The kingdom of {kingdom} does not exist.")
                    return
                valid_password = validate_password(password, kingdom_results[0])
                if not valid_password:
                    await interaction.followup.send(content="The password provided is incorrect.")
                    return
                await cursor.execute("Select Size from Settlements where Settlement = ?", (settlement,))
                settlement_info = await cursor.fetchone()
                if not settlement_info:
                    await interaction.followup.send(content="The settlement is not claimed.")
                    return
                building_info = await fetch_building(interaction.guild_id, building)
                status = await remove_building(guild_id=interaction.guild_id, author=interaction.user.id,
                                               kingdom=kingdom, settlement=settlement, building_info=building_info,
                                               amount=amount, size=settlement_info[0])
                bp_return = (building_info.build_points * status[1]) * .5
                await cursor.execute("UPDATE Kingdoms SET BP = BP + ? WHERE Kingdom = ?", (bp_return, kingdom))
                await interaction.followup.send(content=status[0])
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error destroying building: {e}")
            await interaction.followup.send(content="An error occurred while destroying a building.")


class KingdomView(shared_functions.ShopView):
    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int, interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, interaction=interaction,
                         content="")
        self.max_items = None  # Cache total number of items
        self.content = None

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""

        statement = """
                        SELECT KB.Kingdom, KB.Government, KB.Alignment, KB.Control_DC, KB.Build_Points, 
                        KB.Stabilization_Points, KB.Size, KB.Population, KB.Economy, KB.Loyalty, KB.Stability,
                        KB.Unrest, KB.Consumption, 
                        Custom.Control_DC, Custom.Economy, Custom.Loyalty, Custom.Stability, Custom.Unrest, Custom.Consumption
                        FROM Kingdoms as KB left join Kingdoms_Custom as Custom on KB.Kingdom = Custom.Kingdom 
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
            title=f"Kingdoms",
            description=f"Page {current_page} of {total_pages}")
        for item in self.results:
            (kingdom, government, alignment, control_dc, build_points, stabilization_points, size, population, economy,
             loyalty, stability, unrest, consumption, custom_control_dc, custom_economy, custom_loyalty,
             custom_stability, custom_unrest, custom_consumption) = item
            self.embed.add_field(name=f'**__Kingdom__**: {kingdom}, Control DC: {control_dc}', value=f"""
            **Government**: {government}, **Alignment**: {alignment}\n
            **Resources**: {build_points} BP, {stabilization_points} SP\n
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
                cursor = await db.execute("SELECT COUNT(*) FROM Kingdoms")
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
                SELECT KB.Kingdom, KB.Settlement, KB.Size, KB.Population, KB.Corruption, KB.Crime, KB.Productivity, KB.Law, KB.Lore, KB.Society, KB.Danger, KB.Defence,
                KB.Base_Value, KB.Spellcasting, KB.Supply, KB.Decay, Custom.Corruption, Custom.Crime, Custom.Productivity, Custom.Law, Custom.Lore, Custom.Society, Custom.Danger, Custom.Defence,
                Custom.Base_Value, Custom.Spellcasting, Custom.Supply
                FROM Settlements as KB left join Settlements_Custom as Custom on kb.settlement = custom.settlement WHERE Kingdom = ? Limit ? Offset ?
                """
                cursor = await db.execute(statement, (self.kingdom, self.limit, self.offset))
            else:
                statement = """
                SELECT KB.Kingdom, KB.Settlement, KB.Size, KB.Population, KB.Corruption, KB.Crime, KB.Productivity, KB.Law, KB.Lore, KB.Society, KB.Danger, KB.Defence,
                KB.Base_Value, KB.Spellcasting, KB.Supply, KB.Decay, Custom.Corruption, Custom.Crime, Custom.Productivity, Custom.Law, Custom.Lore, Custom.Society, Custom.Danger, Custom.Defence,
                Custom.Base_Value, Custom.Spellcasting, Custom.Supply
                FROM Settlements as KB left join Settlements_Custom as Custom on kb.settlement = custom.settlement Limit ? Offset ?
                """
                cursor = await db.execute(statement, (self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        if self.kingdom:
            self.embed = discord.Embed(
                title=f"Settlements for {self.kingdom}",
                description=f"Page {current_page} of {total_pages}")
        else:
            self.embed = discord.Embed(
                title=f"Settlements",
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
                    cursor = await db.execute("SELECT COUNT(*) FROM Settlements WHERE Kingdom = ?",
                                              (self.kingdom,))
                else:
                    cursor = await db.execute("SELECT COUNT(*) FROM Settlements")
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
                        from Hexes WHERE Kingdom = ? Limit ? Offset ?
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
                cursor = await db.execute("SELECT COUNT(*) FROM Hexes WHERE Kingdom = ?",
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
                        FROM Hexes_Improvements Limit ? Offset ?
                    """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.limit, self.offset))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        current_page = (self.offset // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(
            title=f"Improvements for Hexes",
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
                cursor = await db.execute("SELECT COUNT(*) FROM Hexes_Improvements")
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
                cursor = await db.execute("SELECT COUNT(*) FROM Buildings_Blueprints")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items
