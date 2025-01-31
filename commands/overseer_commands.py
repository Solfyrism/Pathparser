import math
import datetime
import logging
import math
import random
import typing

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands
import shared_functions
from commands import kingdom_commands


async def add_blueprint(
        guild_id,
        author,
        building,
        build_points,
        lots,
        economy,
        loyalty,
        stability,
        fame,
        unrest,
        corruption,
        crime,
        productivity,
        law,
        lore,
        society,
        danger,
        defence,
        base_value,
        spellcasting,
        supply,
        settlement_limit,
        district_limit,
        description) -> str:  # This will add a new blueprint for players to use.
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("""select building FROM Buildings_Blueprints where building = ? LIMIT 1;""",
                                 (building,))
            result = await cursor.fetchone()
            if result is None:
                await cursor.execute(
                    """
                    INSERT INTO Buildings_Blueprints
                    (building, build_points, lots, 
                    economy, loyalty, stability, fame, unrest, 
                    corruption, crime, productivity, law, lore, society, danger, defence, 
                    base_value, spell_casting, supply, settlement_limit, district_limit, description) 
                    VALUES 
                    (?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?);""",
                    (building, build_points, lots, economy, loyalty, stability, fame, unrest,
                     corruption, crime, productivity, law, lore, society, danger, defence, base_value,
                     spellcasting, supply, settlement_limit, district_limit, description))
                await cursor.execute(
                    """Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)""",
                    (author, datetime.datetime.now(), "Blueprints", "Create", f"Created the blueprints of {building}"))
                await db.commit()
                function_status = f"Congratulations you have allowed the construction of **{building}**"
                return function_status
            if result is not None:
                function_status = f"you have already allowed the construction of **{building}**"
                return function_status
    except (TypeError, ValueError, aiosqlite.Error) as error:
        logging.exception(f"Error in add_blueprint: {error}")
        return "An error occurred while adding a blueprint."


async def remove_blueprint(
        guild_id: int,
        author: int,
        building: str) -> str:  # This will remove a blueprint from play.
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("""select Building FROM Buildings_Blueprints WHERE Building = '{building}'""")
            result = await cursor.fetchone()
            if result is None:
                status = f"The building of {building} did not previously exist."
                await db.commit()
                return status
            if result is not None:
                status = f"You have done the YEETETH of this particular building which is {building}."
                await cursor.execute("""Delete FROM Buildings_Blueprints WHERE Building = '{building}'""")
                await cursor.execute(
                    "Select Kingdom, Settlement, Building, Constructed, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Settlement_Limit, District_Limit, Description FROM KB_Settlements WHERE Building = ?",
                    (building,))
                built_buildings = await cursor.fetchall()
                for built_building in built_buildings:
                    (kingdom, settlement, building, constructed, lots, economy, loyalty, stability, fame, unrest,
                     corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting,
                     supply, settlement_limit, district_limit, description) = built_building
                    await cursor.execute("SELECT Size from KB_Settlements WHERE Kingdom = ? AND Settlement = ?",
                                         (kingdom, settlement))
                    size = await cursor.fetchone()
                    adjusted_dc = math.floor(size[0] / 36) - math.floor((size[0] - (lots * constructed) / 36))
                    await cursor.execute(
                        "Update KB_Settlements SET Size = size - ?, population = population - ?, corruption = corruption - ?, crime = crime - ?, productivity = productivity - ?, law = law - ?, lore = lore - ?, society = society - ?, danger = danger - ?, defence = defence - ?, base_value = base_value - ?, spellcasting = spellcasting - ?, supply = supply - ? WHERE Kingdom = ? AND Settlement = ?",
                        (lots * constructed, lots * 250 * constructed, economy * constructed, loyalty * constructed,
                         stability * constructed, fame * constructed, unrest * constructed, corruption * constructed,
                         crime * constructed, productivity * constructed, law * constructed, lore * constructed,
                         society * constructed, danger * constructed, defence * constructed, base_value * constructed,
                         spellcasting * constructed, supply * constructed, kingdom, settlement))
                    await cursor.execute(
                        "Update KB_Kingdoms set population = population - ?, Control_DC = Control_DC - ?, Economy = Economy - ?, Loyalty = Loyalty - ?, Stability = Stability - ?, Fame = Fame - ?, Unrest = Unrest - ?, Consumption = Consumption - ? WHERE Kingdom = ?",
                        (lots * 250 * constructed, adjusted_dc, economy * constructed, loyalty * constructed,
                         stability * constructed, fame * constructed, unrest * constructed, corruption * constructed,
                         kingdom))
                await cursor.execute("Delete FROM KB_Settlements WHERE Building = ?", (building,))
                await cursor.execute(
                    "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                    (
                    author, datetime.datetime.now(), "KB_Settlements", "Update", f"Removed the building of {building}"))
                await db.commit()
                return status
    except (TypeError, ValueError, aiosqlite.Error) as error:
        logging.exception(f"Error in remove_blueprint: {error}")
        return "An error occurred while removing a blueprint."


async def modify_blueprint(
        guild_id: int,
        author: int,
        old_blueprint_info: kingdom_commands.BuildingInfo,
        building: typing.Optional[str] = None,
        build_points: typing.Optional[int] = None,
        lots: typing.Optional[int] = None,
        economy: typing.Optional[int] = None,
        loyalty: typing.Optional[int] = None,
        stability: typing.Optional[int] = None,
        fame: typing.Optional[int] = None,
        unrest: typing.Optional[int] = None,
        corruption: typing.Optional[int] = None,
        crime: typing.Optional[int] = None,
        productivity: typing.Optional[int] = None,
        law: typing.Optional[int] = None,
        lore: typing.Optional[int] = None,
        society: typing.Optional[int] = None,
        danger: typing.Optional[int] = None,
        defence: typing.Optional[int] = None,
        base_value: typing.Optional[int] = None,
        spell_casting: typing.Optional[int] = None,
        supply: typing.Optional[int] = None,
        settlement_limit: typing.Optional[int] = None,
        district_limit: typing.Optional[int] = None,
        description: typing.Optional[str] = None) -> str:
    try:
        building = building if building else old_blueprint_info.building
        build_points = build_points if build_points else old_blueprint_info.build_points
        lots = lots if lots else old_blueprint_info.lots
        economy = economy if economy else old_blueprint_info.economy
        loyalty = loyalty if loyalty else old_blueprint_info.loyalty
        stability = stability if stability else old_blueprint_info.stability
        fame = fame if fame else old_blueprint_info.fame
        unrest = unrest if unrest else old_blueprint_info.unrest
        corruption = corruption if corruption else old_blueprint_info.corruption
        crime = crime if crime else old_blueprint_info.crime
        productivity = productivity if productivity else old_blueprint_info.productivity
        law = law if law else old_blueprint_info.law
        lore = lore if lore else old_blueprint_info.lore
        society = society if society else old_blueprint_info.society
        danger = danger if danger else old_blueprint_info.danger
        defence = defence if defence else old_blueprint_info.defence
        base_value = base_value if base_value else old_blueprint_info.base_value
        spell_casting = spell_casting if spell_casting else old_blueprint_info.spellcasting
        supply = supply if supply else old_blueprint_info.supply
        settlement_limit = settlement_limit if settlement_limit else old_blueprint_info.settlement_limit
        district_limit = district_limit if district_limit else old_blueprint_info.district_limit
        description = description if description else old_blueprint_info.description
        net_lots = lots - old_blueprint_info.lots
        net_economy = economy - old_blueprint_info.economy
        net_loyalty = loyalty - old_blueprint_info.loyalty
        net_stability = stability - old_blueprint_info.stability
        net_fame = fame - old_blueprint_info.fame
        net_unrest = unrest - old_blueprint_info.unrest
        net_corruption = corruption - old_blueprint_info.corruption
        net_crime = crime - old_blueprint_info.crime
        net_productivity = productivity - old_blueprint_info.productivity
        net_law = law - old_blueprint_info.law
        net_lore = lore - old_blueprint_info.lore
        net_society = society - old_blueprint_info.society
        net_danger = danger - old_blueprint_info.danger
        net_defence = defence - old_blueprint_info.defence
        net_base_value = base_value - old_blueprint_info.base_value
        net_spell_casting = spell_casting - old_blueprint_info.spellcasting
        net_supply = supply - old_blueprint_info.supply
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()

            await cursor.execute(
                "Select Kingdom, Settlement, Building, Constructed, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Settlement_Limit, District_Limit, Description FROM KB_Settlements WHERE Building = ?",
                (building,))
            built_buildings = await cursor.fetchall()
            for built_building in built_buildings:
                (kingdom, settlement, building, constructed, lots, economy, loyalty, stability, fame, unrest,
                 corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting,
                 supply, settlement_limit, district_limit, description) = built_building
                await cursor.execute("SELECT Size from KB_Settlements WHERE Kingdom = ? AND Settlement = ?",
                                     (kingdom, settlement))
                size = await cursor.fetchone()
                adjusted_dc = math.floor(size[0] / 36) - math.floor((size[0] + (net_lots * constructed) / 36))
                await cursor.execute(
                    "Update KB_Settlements SET Size = size + ?, population = population + ?, corruption = corruption + ?, crime = crime + ?, productivity = productivity + ?, law = law + ?, lore = lore + ?, society = society + ?, danger = danger + ?, defence = defence + ?, base_value = base_value + ?, spellcasting = spellcasting + ?, supply = supply + ? WHERE Kingdom = ? AND Settlement = ?",
                    (net_lots * constructed, net_lots * 250 * constructed, net_economy * constructed,
                     net_loyalty * constructed,
                     net_stability * constructed, net_fame * constructed, net_unrest * constructed,
                     net_corruption * constructed,
                     net_crime * constructed, net_productivity * constructed, net_law * constructed,
                     net_lore * constructed,
                     net_society * constructed, net_danger * constructed, net_defence * constructed,
                     net_base_value * constructed,
                     net_spell_casting * constructed, net_supply * constructed, kingdom, settlement))
                await cursor.execute(
                    "Update KB_Kingdoms set population = population + ?, Control_DC = Control_DC + ?, Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Fame = Fame + ?, Unrest = Unrest + ?, Consumption = Consumption + ? WHERE Kingdom = ?",
                    (net_lots * 250 * constructed, adjusted_dc, net_economy * constructed, net_loyalty * constructed,
                     net_stability * constructed, net_fame * constructed, net_unrest * constructed,
                     net_corruption * constructed,
                     kingdom))
            await cursor.execute(
                "UPDATE Buildings_Blueprints SET building = ?, build_points = ?, lots = ?, economy = ?, loyalty = ?, stability = ?, fame = ?, unrest = ?, corruption = ?, crime = ?, productivity = ?, law = ?, lore = ?, society = ?, danger = ?, defence = ?, base_value = ?, spell_casting = ?, supply = ?, settlement_limit = ?, district_limit = ?, description = ? WHERE building = ?",
                (building, build_points, lots, economy, loyalty, stability, fame, unrest, corruption, crime,
                 productivity, law, lore, society, danger, defence, base_value, spell_casting, supply, settlement_limit,
                 district_limit, description, old_blueprint_info.building))
            await cursor.execute(
                "UPDATE Buildings set building = ?, lots = ?, economy = ?, loyalty = ?, stability = ?, fame = ?, unrest = ?, corruption = ?, crime = ?, productivity = ?, law = ?, lore = ?, society = ?, danger = ?, defence = ?, base_value = ?, spell_casting = ?, supply = ?, settlement_limit = ?, district_limit = ?, description = ? WHERE building = ?",
                (building, lots, economy, loyalty, stability, fame, unrest, corruption, crime, productivity, law, lore,
                 society, danger, defence, base_value, spell_casting, supply, settlement_limit, district_limit,
                 description, old_blueprint_info.building))
            await cursor.execute(
                "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "Blueprints", "Update", f"Updated the blueprints of {building}"))
    except (TypeError, ValueError, aiosqlite.Error) as error:
        logging.exception(f"Error in modify_blueprint: {error}")
        return "An error occurred while modifying a blueprint."


async def customize_kingdom_modifiers(
        guild_id: int,
        author: int,
        kingdom: str,
        control_dc: typing.Optional[int],
        economy: typing.Optional[int],
        loyalty: typing.Optional[int],
        stability: typing.Optional[int],
        fame: typing.Optional[int],
        unrest: typing.Optional[int],
        consumption: typing.Optional[int],
        region: typing.Optional[str]) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("""select Kingdom, Password FROM KB_Kingdoms where Kingdom = ?""", (kingdom,))
            result = await cursor.fetchone()
            if result is None:
                status = f"the kingdom of {kingdom} which you have attempted to set new modifiers for couldn't be found."
                await db.commit()
                return status
            if result is not None:
                await cursor.execute(
                    "SELECT Control_DC, Economy, loyalty, Stability, Fame, Unrest, Consumption, Region FROM KB_Kingdoms_Custom WHERE Kingdom = ?",
                    (kingdom,))
                result = await cursor.fetchone()
                (
                    old_control_dc, old_economy, old_loyalty, old_stability, old_fame, old_unrest,
                    old_consumption, old_region) = result
                control_dc = control_dc if isinstance(control_dc, int) else old_control_dc
                economy = economy if isinstance(economy, int) else old_economy
                loyalty = loyalty if isinstance(loyalty, int) else old_loyalty
                stability = stability if isinstance(stability, int) else old_stability
                fame = fame if isinstance(fame, int) else old_fame
                unrest = unrest if isinstance(unrest, int) else old_unrest
                consumption = consumption if isinstance(consumption, int) else old_consumption
                if region != old_region:
                    await cursor.execute("UPDATE KB_Kingdoms SET Region = ? WHERE Kingdom = ?", (region, kingdom))
                    await cursor.execute("UPDATE KB_Hexes SET Region = ? WHERE Kingdom = ?", (region, kingdom))

                await cursor.execute(
                    "UPDATE KB_Kingdoms_Custom SET Control_DC = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ?, Consumption = ? WHERE Kingdom = ?",
                    (control_dc, economy, loyalty, stability, fame, unrest, consumption, kingdom))

                await cursor.execute(
                    "UPDATE KB_Kingdoms SET Control_DC = Control_DC + ?, Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Fame = Fame + ?, Unrest = Unrest + ?, Consumption = Consumption + ? WHERE Kingdom = ?",
                    (control_dc - old_control_dc, economy - old_economy, loyalty - old_loyalty,
                     stability - old_stability, fame - old_fame, unrest - old_unrest, consumption - old_consumption,
                     kingdom))

                await cursor.execute(
                    "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                    (author, datetime.datetime.now(), "KB_Kingdoms", "Update",
                     f"Updated the custom modifiers of {kingdom}"))
                await db.commit()
                status = f"The kingdom of {kingdom} which you have set new modifiers for has been adjusted"
                return status
    except (TypeError, ValueError, aiosqlite.Error) as error:
        logging.exception(f"Error in customize_kingdom_modifiers: {error}")
        return "An error occurred while customizing kingdom modifiers."


async def custom_settlement_modifiers(
        guild_id: int,
        author: int,
        kingdom: str,
        settlement: str,
        corruption: typing.Optional[int],
        crime: typing.Optional[int],
        productivity: typing.Optional[int],
        law: typing.Optional[int],
        lore: typing.Optional[int],
        society: typing.Optional[int],
        danger: typing.Optional[int],
        defence: typing.Optional[int],
        base_value: typing.Optional[int],
        spellcasting: typing.Optional[int],
        supply: typing.Optional[int]) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("""select Settlement FROM KB_Settlements WHERE Settlement = ? AND Kingdom = ?""",
                                 (settlement, kingdom))
            result = await cursor.fetchone()
            if result is None:
                status = f"you cannot apply custom modifiers if the settlement of {settlement} doesn't exist for the kingdom of {kingdom}!"
                await db.commit()
                return status
            if result is not None:
                await cursor.execute(
                    "SELECT Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply FROM KB_Settlements_Custom WHERE Kingdom = ? AND Settlement = ?",
                    (kingdom, settlement))
                result = await cursor.fetchone()
                (old_corruption, old_crime, old_productivity, old_law, old_lore, old_society, old_danger, old_defence,
                 old_base_value, old_spellcasting, old_supply) = result
                corruption = corruption if corruption else old_corruption
                crime = crime if crime else old_crime
                productivity = productivity if productivity else old_productivity
                law = law if law else old_law
                lore = lore if lore else old_lore
                society = society if society else old_society
                danger = danger if danger else old_danger
                defence = defence if defence else old_defence
                base_value = base_value if base_value else old_base_value
                spellcasting = spellcasting if spellcasting else old_spellcasting
                supply = supply if supply else old_supply

                await cursor.execute(
                    "UPDATE KB_Settlements_Custom SET Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ? WHERE Kingdom = ? AND Settlement = ?",
                    (corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting,
                     supply, kingdom, settlement))
                await cursor.execute(
                    "UPDATE KB_Settlements SET Corruption = Corruption + ?, Crime = Crime + ?, Productivity = Productivity + ?, Law = Law + ?, Lore = Lore + ?, Society = Society + ?, Danger = Danger + ?, Defence = Defence + ?, Base_Value = Base_Value + ?, Spellcasting = Spellcasting + ?, Supply = Supply + ? WHERE Kingdom = ? AND Settlement = ?",
                    (corruption - old_corruption, crime - old_crime, productivity - old_productivity, law - old_law,
                     lore - old_lore, society - old_society, danger - old_danger, defence - old_defence,
                     base_value - old_base_value, spellcasting - old_spellcasting, supply - old_supply, kingdom,
                     settlement))
                await cursor.execute(
                    "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                    (author, datetime.datetime.now(), "KB_Settlements", "Update",
                     f"Updated the custom modifiers of {settlement}"))
                await db.commit()
                status = f"You have modified the settlement of {settlement} congratulations!"
                return status
    except (TypeError, ValueError, aiosqlite.Error) as error:
        logging.exception(f"Error in custom_settlement_modifiers: {error}")
        return "An error occurred while customizing settlement modifiers."


"""
async def settlement_decay_set(
        guild_id: int,
        author: int,
        kingdom: str,
        settlement: str,
        decay: int) -> str:
    try:
        async with shared_functions.config_cache.lock:
            configs = shared_functions.config_cache.cache.get(guild_id)
            if configs:
                decay_bool = configs.get('Decay')
        if decay_bool == 'False':
            return "Decay is disabled on this server."
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("Select Kingdom FROM KB_Settlements where Kingdom = ? AND Settlement = ?",
                                 (kingdom, settlement))
            result = await cursor.fetchone()
            if result is None:
                status = f"You have failed to specify a valid settlement to adjust the decay!!"
                await db.commit()
                return status
            if result is not None:
                await cursor.execute("UPDATE KB_Settlements SET Decay = ? WHERE Kingdom = ? AND Settlement = ?",
                                     (decay, kingdom, settlement))
                await cursor.execute(
                    "Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                    (author, datetime.datetime.now(), "KB_Settlements", "Update", f"Updated the decay of {settlement}"))
                await db.commit()
                status = f"The settlement of {settlement} within the kingdom of {kingdom} has had it's decay set to {decay}!"
                return status
    except (TypeError, ValueError, aiosqlite.Error) as error:
        logging.exception(f"Error in settlement_decay_set: {error}")
        return "An error occurred while setting settlement decay."
"""


async def add_hex_improvements(
        guild_id: int,
        author: int,
        improvement: str,
        road_multiplier: int,
        build_points: int,
        economy: int,
        loyalty: int,
        stability: int,
        unrest: int,
        consumption: int,
        defence: int,
        taxation: int,
        cavernous: int,
        coastline: int,
        desert: int,
        forest: int,
        hills: int,
        jungle: int,
        marsh: int,
        mountain: int,
        plains: int,
        water: int) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("""select Improvement from KB_Hexes_Improvements where Improvement = ?""",
                                 (improvement,))
            result = await cursor.fetchone()
            if result is None:
                await cursor.execute(
                    """INSERT INTO KB_Hexes_Improvements (
                    Improvement, Road_Multiplier, Build_Points, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation, Cavernous, Coastline, Desert, Forest, Hills, Jungle, Marsh, Mountain, Plains, Water) 
                    VALUES 
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                    (improvement, road_multiplier, build_points, economy, loyalty, stability, unrest, consumption,
                     defence, taxation, cavernous, coastline, desert, forest, hills, jungle, marsh, mountain, plains,
                     water))
                await cursor.execute(
                    """Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)""",
                    (author, datetime.datetime.now(), "KB_Hexes_Improvements", "Create",
                     f"Created the hex improvement of {improvement}"))
                await db.commit()
                status = f"You have allowed the creation the new hex improvement: {improvement}!"
                return status
            else:
                status = f"You cannot add a improvement with the same name of {improvement}!"
                return status
    except (TypeError, ValueError, aiosqlite.Error) as error:
        logging.exception(f"Error in add_hex_improvements: {error}")
        return "An error occurred while adding a hex improvement."


async def remove_hex_improvements(
        guild_id: int,
        author: int,
        improvement: str) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("""select Improvement FROM KB_Hexes_Improvements WHERE Improvement = ?""",
                                 (improvement,))
            result = await cursor.fetchone()
            if result is None:
                status = f"The improvement of {improvement} did not previously exist."
                await db.commit()
                return status
            else:
                await cursor.execute("""Delete FROM KB_Hexes_Improvements WHERE Improvement = ?""", (improvement,))
                await cursor.execute(
                    """Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)""",
                    (author, datetime.datetime.now(), "KB_Hexes_Improvements", "Delete",
                     f"Deleted the hex improvement of {improvement}"))
                await db.commit()
                status = f"You have removed the hex improvement of {improvement}!"
                return status
    except (TypeError, ValueError, aiosqlite.Error) as e:
        logging.exception(f"Error in remove_hex_improvements: {e}")
        return "An error occurred while removing a hex improvement."


async def modify_hex_improvements(
        guild_id: int,
        author: int,
        old_hex_info: kingdom_commands.HexImprovementInfo,
        improvement: typing.Optional[str] = None,
        road_multiplier: typing.Optional[int] = None,
        build_points: typing.Optional[int] = None,
        economy: typing.Optional[int] = None,
        loyalty: typing.Optional[int] = None,
        stability: typing.Optional[int] = None,
        unrest: typing.Optional[int] = None,
        consumption: typing.Optional[int] = None,
        defence: typing.Optional[int] = None,
        taxation: typing.Optional[int] = None,
        cavernous: typing.Optional[int] = None,
        coastline: typing.Optional[int] = None,
        desert: typing.Optional[int] = None,
        forest: typing.Optional[int] = None,
        hills: typing.Optional[int] = None,
        jungle: typing.Optional[int] = None,
        marsh: typing.Optional[int] = None,
        mountain: typing.Optional[int] = None,
        plains: typing.Optional[int] = None,
        water: typing.Optional[int] = None) -> str:
    try:
        improvement = improvement if improvement else old_hex_info.improvement
        road_multiplier = road_multiplier if road_multiplier else old_hex_info.road_multiplier
        build_points = build_points if build_points else old_hex_info.build_points
        economy = economy if economy else old_hex_info.economy
        loyalty = loyalty if loyalty else old_hex_info.loyalty
        stability = stability if stability else old_hex_info.stability
        unrest = unrest if unrest else old_hex_info.unrest
        consumption = consumption if consumption else old_hex_info.consumption
        defence = defence if defence else old_hex_info.defence
        taxation = taxation if taxation else old_hex_info.taxation
        cavernous = cavernous if cavernous else old_hex_info.cavernous
        coastline = coastline if coastline else old_hex_info.coastline
        desert = desert if desert else old_hex_info.desert
        forest = forest if forest else old_hex_info.forest
        hills = hills if hills else old_hex_info.hills
        jungle = jungle if jungle else old_hex_info.jungle
        marsh = marsh if marsh else old_hex_info.marsh
        mountain = mountain if mountain else old_hex_info.mountains
        plains = plains if plains else old_hex_info.plains
        water = water if water else old_hex_info.water
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            difference_economy = economy - old_hex_info.economy
            difference_loyalty = loyalty - old_hex_info.loyalty
            difference_stability = stability - old_hex_info.stability
            difference_unrest = unrest - old_hex_info.unrest
            difference_consumption = consumption - old_hex_info.consumption
            difference_defence = defence - old_hex_info.defence
            difference_taxation = taxation - old_hex_info.taxation
            await cursor.execute("SELECT Kingdom, Amount from KB_Hexes WHERE Improvement = ?", (improvement,))
            improvements = await cursor.fetchall()
            for improvement in improvements:
                (kingdom, amount) = improvement
                await cursor.execute(
                    "UPDATE KB_Hexes SET Economy = ?, Loyalty = ?, Stability = ?, Unrest = ?, Consumption = ?, Defence = ?, Taxation = ?, Cavernous = ?, Coastline = ?, Desert =  ?, Forest = ?, Hills = ?, Jungle = ?, Marsh = ?, Mountain = ?, Plains = ?, Water = ? WHERE Improvement = ?",
                    (economy, loyalty, stability, unrest, consumption, defence, taxation, cavernous, coastline, desert,
                     forest, hills, jungle, marsh, mountain, plains, water, improvement))
                await cursor.execute(
                    "UPDATE KB_Kingdoms SET Economy = Economy + ?, Loyalty = Loyalty + ?, Stability = Stability + ?, Unrest = Unrest + ?, Consumption = Consumption + ?, Defence = Defence + ?, Taxation = Taxation + ? WHERE Kingdom = ?",
                    (difference_economy * amount, difference_loyalty * amount, difference_stability * amount,
                     difference_unrest * amount, difference_consumption * amount, difference_defence * amount,
                     difference_taxation * amount, kingdom))
            await cursor.execute("""select Improvement FROM KB_Hexes_Improvements WHERE Improvement = ?""",
                                 (improvement,))
            result = await cursor.fetchone()
            if result is None:
                await cursor.execute(
                    """UPDATE KB_Hexes_Improvements SET Improvement = ?, Road_Multiplier = ?, Build_Points = ?, Economy = ?, Loyalty = ?, Stability = ?, Unrest = ?, Consumption = ?, Defence = ?, Taxation = ?, Cavernous = ?, Coastline = ?, Desert = ?, Forest = ?, Hills = ?, Jungle = ?, Marsh = ?, Mountain = ?, Plains = ?, Water = ? WHERE Improvement = ?""",
                    (improvement, road_multiplier, build_points, economy, loyalty, stability, unrest, consumption,
                     defence, taxation, cavernous, coastline, desert, forest, hills, jungle, marsh, mountain, plains,
                     water, old_hex_info.improvement))
                await cursor.execute(
                    """Insert into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)""",
                    (author, datetime.datetime.now(), "KB_Hexes_Improvements", "Update",
                     f"Updated the hex improvement of {improvement}"))
                await db.commit()
                status = f"The hex improvement of {improvement} has been modified!"
                return status
            else:
                status = f"You cannot modify a hex improvement with the same name of {improvement}!"
                return status
    except (TypeError, ValueError, aiosqlite.Error) as e:
        logging.exception(f"Error in modify_hex_improvements: {e}")
        return "An error occurred while modifying a hex improvement."


async def rebalance_kingdom_building(
        guild_id: int,
        author: int) -> str:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "UPDATE KB_Kingdoms SET Control_DC = 1, Size = 1, Economy = 0, Loyalty = 0, Stability = 0, Fame = 0, Unrest = 0, Consumption = 0")
            await cursor.execute(
                "UPDATE KB_Settlements SET Size = 1, Population = 1, Economy = 0, Loyalty = 0, Stability = 0, Fame = 0, Unrest = 0, Corruption = 0, Crime = 0, Productivity = 0, Law = 0, Lore = 0, Society = 0, Danger = 0, Defence = 0, Base_Value = 0, Spellcasting = 0, Supply = 0")
            await cursor.execute(
                "INSERT into A_Audit_All (Author, Timestamp, Database_Changed, Modification, Reason) VALUES (?, ?, ?, ?, ?)",
                (author, datetime.datetime.now(), "KB_Kingdoms", "Update", "Rebalanced all kingdom buildings"))
            await db.commit()
            await cursor.execute("SELECT Kingdom from KB_Kingdoms")
            kingdoms = await cursor.fetchall()
            for kingdom in kingdoms:
                await rebalance_settlements(db, kingdom[0])
                await rebalance_hexes(db, kingdom[0])
            status = "All kingdom buildings have been rebalanced."

            return status

    except (TypeError, ValueError, aiosqlite.Error) as e:
        logging.exception(f"Error in rebalance_kingdom_building: {e}")
        return "An error occurred while balancing kingdom buildings."


async def rebalance_hexes(
        db: aiosqlite.Connection,
        kingdom: str) -> None:
    cursor = await db.cursor()
    await cursor.execute(
        "SELECT Improvement, Amount, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation FROM KB_Hexes WHERE Kingdom = ?",
        (kingdom,))
    improvements = await cursor.fetchall()
    total_hexes = 0
    total_economy = 0
    total_loyalty = 0
    total_stability = 0
    total_unrest = 0
    total_consumption = 0
    total_defence = 0
    total_taxation = 0
    for improvement in improvements:
        (improvement, amount, economy, loyalty, stability, unrest, consumption, defence, taxation) = improvement
        total_hexes += amount
        total_economy += economy * amount
        total_loyalty += loyalty * amount
        total_stability += stability * amount
        total_unrest += unrest * amount
        total_consumption += consumption * amount
        total_defence += defence * amount
        total_taxation += taxation * amount
    await cursor.execute(
        "Update KB_Kingdoms SET Control_DC = Control_DC + ?, Size = Size + ?, economy = economy + ?, loyalty = loyalty + ?, stability = stability + ?, unrest = unrest + ?, consumption = consumption + ?, defence = defence + ?, taxation = taxation + ? WHERE Kingdom = ?",
        (total_hexes, total_hexes, total_economy, total_loyalty, total_stability, total_unrest, total_consumption,
         total_defence, total_taxation, kingdom))
    await db.commit()


async def rebalance_settlements(
        db: aiosqlite.Connection,
        kingdom: str) -> None:
    cursor = await db.cursor()
    await cursor.execute("SELECT Settlement FROM KB_Settlements WHERE Kingdom = ?", (kingdom,))
    settlements = await cursor.fetchall()
    total_size = 0
    total_economy = 0
    total_loyalty = 0
    total_stability = 0
    total_fame = 0
    total_unrest = 0
    for settlement in settlements:
        buildings = await rebalance_buildings(db, kingdom, settlement[0])
        (size, economy, loyalty, stability, fame, unrest) = buildings
        total_size += size
        total_economy += economy
        total_loyalty += loyalty
        total_stability += stability
        total_fame += fame
        total_unrest += unrest
    await cursor.execute(
        "Update KB_Kingdoms SET Control_DC = Control_DC + ?, Size = Size + ?, economy = economy + ?, loyalty = loyalty + ?, stability = stability + ?, fame = fame + ?, unrest = unrest + ? WHERE Kingdom = ?",
        (math.floor(total_size / 36), total_size, total_economy, total_loyalty, total_stability, total_fame,
         total_unrest, kingdom))


async def rebalance_buildings(
        db: aiosqlite.Connection,
        kingdom: str,
        settlement: str) -> typing.Tuple[int, int, int, int, int, int]:
    cursor = await db.cursor()
    await cursor.execute("SELECT Building, Constructed FROM KB_Settlements WHERE Kingdom = ? AND Settlement = ?",
                         (kingdom, settlement))
    buildings = await cursor.fetchall()
    size = 0
    economy = 0
    loyalty = 0
    stability = 0
    fame = 0
    unrest = 0
    for building in buildings:
        (building, constructed) = building
        await cursor.execute("SELECT Lots, Economy, Loyalty, Stability, Fame, Unrest FROM Buildings WHERE Building = ?",
                             (building,))
        building_info = await cursor.fetchone()
        (lots, economy, loyalty, stability, fame, unrest) = building_info
        size += lots * constructed
        economy += economy * constructed
        loyalty += loyalty * constructed
        stability += stability * constructed
        fame += fame * constructed
        unrest += unrest * constructed
    await cursor.execute(
        "UPDATE KB_Settlements SET Size = ?, population = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ? WHERE Kingdom = ? AND Settlement = ?",
        (size, size * 250, economy, loyalty, stability, fame, unrest, kingdom, settlement))
    await db.commit()
    return size, economy, loyalty, stability, fame, unrest


class OverseerCommands(commands.Cog, name='overseer'):
    def __init__(self, bot):
        self.bot = bot

    overseer_group = discord.app_commands.Group(
        name='overseer',
        description='Commands related to kingdom management'
    )

    kingdom_group = discord.app_commands.Group(
        name='kingdom',
        description='Commands related to kingdom management',
        parent=overseer_group
    )

    settlement_group = discord.app_commands.Group(
        name='settlement',
        description='Commands related to settlement management',
        parent=overseer_group
    )

    hex_group = discord.app_commands.Group(
        name='hex',
        description='Commands related to settlement management',
        parent=overseer_group
    )

    blueprint_group = discord.app_commands.Group(
        name='blueprint',
        description='Commands related to blueprint management',
        parent=overseer_group
    )

    leadership_group = discord.app_commands.Group(
        name='leadership',
        description='Commands related to event management',
        parent=overseer_group
    )

    event_group = discord.app_commands.Group(
        name='event',
        description='Commands related to event management',
        parent=overseer_group
    )

    @overseer_group.command()
    async def help(self, interaction: discord.Interaction):
        """Help commands for the associated tree"""
        embed = discord.Embed(title=f"Overseer Help", description=f'This is a list of Overseer help commands',
                              colour=discord.Colour.blurple())
        embed.add_field(name=f'**blueprint_add**',  # Done
                        value=f'The command for an overseer to create a new blueprint for players to use..',
                        inline=False)
        embed.add_field(name=f'**blueprint_remove**', value=f'This command removes blueprints from player usage.',
                        # Done
                        inline=False)
        embed.add_field(name=f'**blueprint_modify**',
                        value=f'This command modifies a blueprint that is already in use.',  # Done
                        inline=False)
        embed.add_field(name=f'**kingdom_modifiers**',  # Done
                        value=f'This command adjusts the custom modifiers associated with a kingdom.', inline=False)
        embed.add_field(name=f'**settlement_modifiers**',  # Done
                        value=f'This command adjusts the custom modifiers associated with a settlement.', inline=False)
        embed.add_field(name=f'**settlement_decay**',  # Done
                        value=f'This command modifies the multiplier for stabilization points a settlement requires in order to build.',
                        inline=False)  # Done
        embed.add_field(name=f'**improvement_add**',
                        value=f'This command adds a new hex improvement for players to build',
                        inline=False)  # Done
        embed.add_field(name=f'**improvement_remove**',  # Done
                        value=f'This command removes hex improvements from options players can build.', inline=False)
        embed.add_field(name=f'**improvement_modify**',  # Done
                        value=f'This command modifies hex improvements that are available to build, or have been built',
                        inline=False)  # Done
        embed.add_field(name=f'**kingdom_tables_rebalance**',  # Done
                        value=f'Forced the kingdom and settlement tables to rebalance.', inline=False)
        await interaction.response.send_message(embed=embed)

    @kingdom_group.command(name='modifiers', description='Adjust the custom modifiers associated with a kingdom')
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    @app_commands.autocomplete(region=shared_functions.region_autocomplete)
    async def kingdom_modifiers(self, interaction: discord.Interaction, kingdom: str, region: typing.Optional[str], control_dc: typing.Optional[int],
                                economy: typing.Optional[int], loyalty: typing.Optional[int],
                                stability: typing.Optional[int], fame: typing.Optional[int],
                                unrest: typing.Optional[int], consumption: typing.Optional[int]):
        """Adjust the custom modifiers associated with a kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            status = await customize_kingdom_modifiers(interaction.guild_id, interaction.user.id, kingdom, control_dc,
                                                       economy, loyalty, stability, fame, unrest, consumption, region)
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in kingdom_modifiers: {e}")
            await interaction.followup.send("An error occurred while customizing kingdom modifiers.")

    @kingdom_group.command(name='rebalance', description='Forced the kingdom and settlement tables to rebalance.')
    async def kingdom_rebalance(self, interaction: discord.Interaction):
        """Forced the kingdom and settlement tables to rebalance."""
        await interaction.response.defer(thinking=True)
        try:
            status = await rebalance_kingdom_building(interaction.guild_id, interaction.user.id)
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in kingdom_rebalance: {e}")
            await interaction.followup.send("An error occurred while balancing kingdom buildings.")

    @kingdom_group.command(name='overpower', description='Overpower a kingdom and assume direct control.')
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    async def kingdom_overpower(self, interaction: discord.Interaction, kingdom: str, password: str, character_name: str):
        """Overpower a kingdom and assume direct control."""
        await interaction.response.defer(thinking=True)
        try:
            new_password = await kingdom_commands.encrypt_password(password)
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("Update KB_Kingdoms SET Password = ? WHERE Kingdom = ?", (new_password, kingdom))
                await cursor.execute("Update KB_Leadership SET Character_Name = ?, Player_ID = ? where kingdom = ?", (character_name, interaction.user.id, kingdom))
                await db.commit()
                await interaction.followup.send("You have successfully overpowered the kingdom, assigning yourself as King and setting all leaders to be you.")

        except (TypeError, ValueError) as e:
            logging.exception(f"Error in kingdom_overpower: {e}")
            await interaction.followup.send("An error occurred while overpowering a kingdom.")


    @kingdom_group.command(name="build_points", description="Adjust the build points of a kingdom.")
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    async def kingdom_build_points(self, interaction: discord.Interaction, kingdom: str, build_points: int):
        """Adjust the build points of a kingdom."""
        await interaction.response.defer(thinking=True)
        try:
            status = await kingdom_commands.adjust_bp(interaction.guild_id, interaction.user.id, kingdom, build_points)
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in kingdom_build_points: {e}")
            await interaction.followup.send("An error occurred while adjusting kingdom build points.")

    @settlement_group.command(name='modifiers', description='Adjust the custom modifiers associated with a settlement')
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    @app_commands.autocomplete(settlement=kingdom_commands.settlement_autocomplete)
    async def settlement_modifiers(self, interaction: discord.Interaction, kingdom: str, settlement: str,
                                   corruption: typing.Optional[int], crime: typing.Optional[int],
                                   productivity: typing.Optional[int], law: typing.Optional[int],
                                   lore: typing.Optional[int], society: typing.Optional[int],
                                   danger: typing.Optional[int], defence: typing.Optional[int],
                                   base_value: typing.Optional[int], spellcasting: typing.Optional[int],
                                   supply: typing.Optional[int]):
        """Adjust the custom modifiers associated with a settlement"""
        await interaction.response.defer(thinking=True)
        try:
            status = await custom_settlement_modifiers(interaction.guild_id, interaction.user.id, kingdom, settlement,
                                                       corruption, crime, productivity, law, lore, society, danger,
                                                       defence, base_value, spellcasting, supply)
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in settlement_modifiers: {e}")
            await interaction.followup.send("An error occurred while customizing settlement modifiers.")

    @settlement_group.command(name='build', description='Add buildings in a specified settlement.')
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    @app_commands.autocomplete(settlement=kingdom_commands.settlement_autocomplete)
    async def build_in_settlement(self, interaction: discord.Interaction, kingdom: str, settlement: str, building: str,
                                  amount: int):
        """Add a new blueprint for players to use."""
        await interaction.response.defer(thinking=True)
        try:
            building_info = await kingdom_commands.fetch_building(interaction.guild_id, building)
            if building_info is None:
                await interaction.followup.send(f"The building of {building} does not exist.")
                return
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("Select Size from KB_Settlements where Kingdom = ? AND Settlement = ?",
                                     (kingdom, settlement))
                size = await cursor.fetchone()
                status = await kingdom_commands.add_building(
                    guild_id=interaction.guild_id,
                    author=interaction.user.id,
                    kingdom=kingdom,
                    settlement=settlement,
                    amount=amount,
                    building_info=building_info,
                    size=size[0])
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in build_in_settlement: {e}")
            await interaction.followup.send("An error occurred while adding a building to a settlement.")

    @settlement_group.command(name='remove', description='Remove buildings from a specified KB_Settlements.')
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    @app_commands.autocomplete(settlement=kingdom_commands.settlement_autocomplete)
    async def remove_from_settlement(self, interaction: discord.Interaction, kingdom: str, settlement: str,
                                     building: str, amount: int):
        """Remove buildings from a specified settlement."""
        await interaction.response.defer(thinking=True)
        try:
            building_info = await kingdom_commands.fetch_building(interaction.guild_id, building)
            if building_info is None:
                await interaction.followup.send(f"The building of {building} does not exist.")
                return
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("Select Size from KB_Settlements where Kingdom = ? AND Settlement = ?",
                                     (kingdom, settlement))
                size = await cursor.fetchone()
                status = await kingdom_commands.remove_building(
                    guild_id=interaction.guild_id,
                    author=interaction.user.id,
                    kingdom=kingdom,
                    settlement=settlement,
                    amount=amount,
                    building_info=building_info,
                    size=size[0])
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in remove_from_settlement: {e}")
            await interaction.followup.send("An error occurred while removing a building from a settlement.")

    @hex_group.command(name='add', description='Add a new hex improvement for players to build')
    async def add_hex_improvement(
            self, interaction: discord.Interaction, improvement: str, road_multiplier: int,
            build_points: int, economy: int, loyalty: int, stability: int, unrest: int,
            consumption: int, defence: int, taxation: int, cavernous: int, coastline: int,
            desert: int, forest: int, hills: int, jungle: int, marsh: int, mountain: int,
            plains: int, water: int):
        """Add a new hex improvement for players to build"""
        await interaction.response.defer(thinking=True)
        try:
            status = await add_hex_improvements(
                interaction.guild_id,
                interaction.user.id,
                improvement,
                road_multiplier,
                build_points,
                economy, loyalty, stability, unrest, consumption, defence, taxation,
                cavernous, coastline, desert, forest, hills, jungle, marsh, mountain, plains, water)
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in add_hex_improvement: {e}")
            await interaction.followup.send("An error occurred while adding a hex improvement.")

    @hex_group.command(name='remove', description='Remove hex improvements from options players can build.')
    async def remove_hex_improvement(self, interaction: discord.Interaction, improvement: str):
        """Remove hex improvements from options players can build."""
        await interaction.response.defer(thinking=True)
        try:
            status = await remove_hex_improvements(interaction.guild_id, interaction.user.id, improvement)
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in remove_hex_improvement: {e}")
            await interaction.followup.send("An error occurred while removing a hex improvement.")

    @hex_group.command(name='modify',
                       description='Modify hex improvements that are available to build, or have been built')
    async def modify_hex_improvement(
            self, interaction: discord.Interaction, improvement: str,
            road_multiplier: typing.Optional[int], build_points: typing.Optional[int],
            economy: typing.Optional[int], loyalty: typing.Optional[int],
            stability: typing.Optional[int], unrest: typing.Optional[int],
            consumption: typing.Optional[int], defence: typing.Optional[int],
            taxation: typing.Optional[int], cavernous: typing.Optional[int],
            coastline: typing.Optional[int], desert: typing.Optional[int],
            forest: typing.Optional[int], hills: typing.Optional[int],
            jungle: typing.Optional[int], marsh: typing.Optional[int],
            mountain: typing.Optional[int], plains: typing.Optional[int],
            water: typing.Optional[int]):
        """Modify hex improvements that are available to build, or have been built"""
        await interaction.response.defer(thinking=True)
        try:
            old_hex_info = await kingdom_commands.fetch_hex_improvement(interaction.guild_id, improvement)
            status = await modify_hex_improvements(
                guild_id=interaction.guild_id,
                author=interaction.user.id,
                old_hex_info=old_hex_info,
                improvement=improvement,
                road_multiplier=road_multiplier,
                build_points=build_points,
                economy=economy,
                loyalty=loyalty,
                stability=stability,
                unrest=unrest,
                consumption=consumption,
                defence=defence,
                taxation=taxation,
                cavernous=cavernous,
                coastline=coastline,
                desert=desert,
                forest=forest,
                hills=hills,
                jungle=jungle,
                marsh=marsh,
                mountain=mountain,
                plains=plains,
                water=water)
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in modify_hex_improvement: {e}")
            await interaction.followup.send("An error occurred while modifying a hex improvement.")

    @hex_group.command(name='create', description='create and add a hex into play.')
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    @app_commands.autocomplete(terrain=kingdom_commands.hex_terrain_autocomplete)
    @app_commands.autocomplete(region=shared_functions.region_autocomplete)
    @app_commands.choices(
        behavior=[discord.app_commands.Choice(name='set', value=1),
                  discord.app_commands.Choice(name='random', value=2)])
    async def add_hex(self, interaction: discord.Interaction, kingdom: str, terrain: str, region: str, farm: int,
                      ore: int, stone: int, wood: int, fish: int, behavior: discord.app_commands.Choice[int] = 1):
        await interaction.response.defer(thinking=True)
        try:
            behavior_value = behavior.value if isinstance(behavior, discord.app_commands.Choice) else 1
            if behavior_value == 2:
                farm = random.randint(1, farm)
                ore = random.randint(1, ore)
                stone = random.randint(1, stone)
                wood = random.randint(1, wood)
                fish = random.randint(1, fish)
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("INSERT INTO KB_Hexes (Kingdom, Hex_Terrain, Region, Farm, Ore, Stone, wood, fish) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                     (kingdom, terrain, region, farm, ore, stone, wood, fish))
                await cursor.execute("SELECT Max(ID) from KB_Hexes")
                hex_id = await cursor.fetchone()
                if kingdom:
                    await cursor.execute("UPDATE KB_Kingdoms SET Control_DC = Control_DC + 1 WHERE Kingdom = ?", (kingdom,))
                    status = f"The hex with ID {hex_id[0]} has been created and added to the kingdom of {kingdom}!\r\nit can support {farm} farms, {ore} mines, {stone} quarries, {wood} woodcutters and {fish} fisheries."
                else:
                    status = f"The hex with ID {hex_id[0]}has been created!\r\nit can support {farm} farms, {ore} mines, {stone} quarries, {wood} woodcutters and {fish} fisheries."
                await db.commit()

                await interaction.followup.send(status)
        except(TypeError, ValueError) as e:
            logging.exception(f"Error in add_hex: {e}")
            await interaction.followup.send("An error occurred while adding a hex.")

    @hex_group.command(name='edit', description='edit a hex in play.')
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    @app_commands.autocomplete(terrain=kingdom_commands.hex_terrain_autocomplete)
    @app_commands.autocomplete(region=shared_functions.region_autocomplete)
    @app_commands.choices(
        behavior=[discord.app_commands.Choice(name='set', value=1),
                  discord.app_commands.Choice(name='random', value=2)])
    async def edit_hex(self, interaction: discord.Interaction, hex_id: int, kingdom: typing.Optional[str], terrain: typing.Optional[str], region: typing.Optional[str], farm: typing.Optional[int],
                      ore: typing.Optional[int], stone: typing.Optional[int], wood: typing.Optional[int], fish: typing.Optional[int], behavior: discord.app_commands.Choice[int] = 1):
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Kingdom, Region, Hex_Terrain, Farm, Ore, Stone, Wood, Fish From KB_Hexes where ID = ?", (hex_id,))
                hex_info = await cursor.fetchone()
                if not hex_info:
                    await interaction.followup.send("The hex with that ID does not exist.")
                    return
                change_kingdom = kingdom if kingdom else hex_info[0]
                change_kingdom = None if change_kingdom == "None" else change_kingdom
                region = region if region else hex_info[1]
                terrain = terrain if terrain else hex_info[2]

            behavior_value = behavior.value if isinstance(behavior, discord.app_commands.Choice) else 1
            if behavior_value == 2:
                farm = random.randint(1, farm) if farm else hex_info[3]
                ore = random.randint(1, ore) if ore else hex_info[4]
                stone = random.randint(1, stone) if stone else hex_info[5]
                wood = random.randint(1, wood) if wood else hex_info[6]
                fish = random.randint(1, fish) if fish else hex_info[7]
            else:
                farm = farm if farm else hex_info[3]
                ore = ore if ore else hex_info[4]
                stone = stone if stone else hex_info[5]
                wood = wood if wood else hex_info[6]
                fish = fish if fish else hex_info[7]
            await cursor.execute(
                "UPDATE KB_Hexes SET Kingdom = ?, Terrain = ?, Region = ?, Farm = ?, Ore = ?, Stone = ?, wood = ?, fish = ? WHERE ID = ?",
                (change_kingdom, terrain, region, farm, ore, stone, wood, fish, hex_id))
            await cursor.execute("UPDATE KB_Hexes_Constructed SET Kingdom = ? WHERE ID = ?", (change_kingdom, hex_id))
            if kingdom != hex_info[0]:
                await cursor.execute("UPDATE KB_Kingdoms SET Control_DC = Control_DC - 1 WHERE Kingdom = ?",
                                     (hex_info[0],))
                if kingdom:
                    await cursor.exeucte("UPDATE KB_Kingdoms SET Control_DC = Control_DC + 1 WHERE Kingdom = ?", (kingdom,))
                    status = f"The hex with ID {hex_id} has been updated and added to the kingdom of {kingdom}!\r\nit can support {farm} farms, {ore} mines, {stone} quarries, {wood} woodcutters,and {fish} fisheries."
                else:
                    status = f"The hex with ID {hex_id} has been updated and removed from the original kingdom!\r\nit can support {farm} farms, {ore} mines, {stone} quarries, {wood} woodcutters, and {fish} fisheries."
            else:
                status = f"The hex with ID {hex_id}has been updated!\r\nit can support {farm} farms, {ore} mines, {stone} quarries, {wood} woodcutters, and {fish} fisheries."
            await db.commit()

            await interaction.followup.send(status)
        except(TypeError, ValueError) as e:
            logging.exception(f"Error in add_hex: {e}")
            await interaction.followup.send("An error occurred while adding a hex.")

    @hex_group.command(name='delete', description='delete a hex from play.')
    async def delete_hex(self, interaction: discord.Interaction, hex_id: int):
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Kingdom from KB_Hexes where ID = ?", (hex_id,))
                kingdom = await cursor.fetchone()
                if not kingdom:
                    await interaction.followup.send("The hex with that ID does not exist.")
                    return
                await cursor.execute("DELETE FROM KB_Hexes where ID = ?", (hex_id,))
                await cursor.execute("DELETE FROM KB_Hexes_Constructed where ID = ?", (hex_id,))

                await cursor.execute("UPDATE KB_Kingdoms SET Control_DC = Control_DC - 1 WHERE Kingdom = ?", (kingdom[0],))
                await db.commit()
                await interaction.followup.send(f"The hex with ID {hex_id} has been deleted.")
        except(TypeError, ValueError) as e:
            logging.exception(f"Error in delete_hex: {e}")
            await interaction.followup.send("An error occurred while deleting a hex.")

    @blueprint_group.command(name='add', description='Add a new blueprint for players to use.')
    async def add_blueprint(
            self,
            interaction: discord.Interaction,
            name: str,
            lots: int,
            economy: int,
            loyalty: int,
            stability: int,
            fame: int,
            unrest: int,
            build_points: int,
            defence: int,
            corruption: int,
            crime: int,
            productivity: int,
            law: int,
            lore: int,
            society: int,
            danger: int,
            base_value: int,
            spellcasting: int,
            supply: int,
            district_limit: int,
            settlement_limit: int,
            description: str
    ):
        """Add a new blueprint for players to use."""
        await interaction.response.defer(thinking=True)
        try:
            status = await add_blueprint(
                guild_id=interaction.guild_id,
                author=interaction.user.id,
                building=name,
                build_points=build_points,
                lots=lots,
                economy=economy,
                loyalty=loyalty,
                stability=stability,
                fame=fame,
                unrest=unrest,
                defence=defence,
                corruption=corruption,
                crime=crime,
                productivity=productivity,
                law=law,
                lore=lore,
                society=society,
                danger=danger,
                base_value=base_value,
                spellcasting=spellcasting,
                supply=supply,
                district_limit=district_limit,
                settlement_limit=settlement_limit,
                description=description
            )
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in add_blueprint: {e}")
            await interaction.followup.send("An error occurred while adding a blueprint.")

    @blueprint_group.command(name='remove', description='This command removes blueprints from player usage.')
    async def remove_blueprint(self, interaction: discord.Interaction, name: str):
        """This command removes blueprints from player usage."""
        await interaction.response.defer(thinking=True)
        try:
            status = await remove_blueprint(interaction.guild_id, interaction.user.id, name)
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in remove_blueprint: {e}")
            await interaction.followup.send("An error occurred while removing a blueprint.")

    @blueprint_group.command(name='modify', description='This command modifies a blueprint that is already in use.')
    async def modify_blueprint(
            self, interaction: discord.Interaction, old_name: str,
            name: typing.Optional[str],
            size: typing.Optional[int],
            economy: typing.Optional[int], loyalty: typing.Optional[int],
            stability: typing.Optional[int], fame: typing.Optional[int],
            unrest: typing.Optional[int], corruption: typing.Optional[int],
            crime: typing.Optional[int], productivity: typing.Optional[int],
            law: typing.Optional[int], lore: typing.Optional[int],
            society: typing.Optional[int], danger: typing.Optional[int],
            defence: typing.Optional[int], base_value: typing.Optional[int],
            spellcasting: typing.Optional[int], supply: typing.Optional[int],
            settlement_limit: typing.Optional[int], district_limit: typing.Optional[int],
            description: typing.Optional[str]):
        """This command modifies a blueprint that is already in use."""
        await interaction.response.defer(thinking=True)
        try:
            old_blueprint = await kingdom_commands.fetch_building(interaction.guild_id, old_name)
            status = await modify_blueprint(
                guild_id=interaction.guild_id,
                author=interaction.user.id,
                old_blueprint_info=old_blueprint,
                building=name,
                lots=size,
                economy=economy,
                loyalty=loyalty,
                stability=stability,
                fame=fame,
                unrest=unrest,
                corruption=corruption,
                crime=crime,
                productivity=productivity,
                law=law,
                lore=lore,
                society=society,
                danger=danger,
                defence=defence,
                base_value=base_value,
                spell_casting=spellcasting,
                supply=supply,
                settlement_limit=settlement_limit,
                district_limit=district_limit,
                description=description
            )

            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in modify_blueprint: {e}")
            await interaction.followup.send("An error occurred while modifying a blueprint.")



    @leadership_group.command(name="modify",
                              description="Modify a leader, by changing their ability score or who is in charge")
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    @app_commands.autocomplete(title=kingdom_commands.leadership_autocomplete)
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

                await cursor.execute(
                    "SELECT Ability, Economy, Loyalty, Stability FROM AA_Leadership_Roles WHERE Title = ?",
                    (title,))
                leadership_info = await cursor.fetchone()
                (ability, economy, loyalty, stability) = leadership_info
                abilities = ability.split(" / ")
                options = [
                    discord.SelectOption(label=ability) for ability in abilities
                ]

                additional = 1 if title != "Ruler" and kingdom_results[1] < 26 else 2
                additional = 3 if title == "Ruler" and kingdom_results[1] < 101 else additional
                view = kingdom_commands.LeadershipView(
                    options, interaction.guild_id, interaction.user.id, kingdom, title, character_name,
                    additional, economy, loyalty, stability, kingdom_results[1], modifier=modifier,
                    recipient_id=interaction.user.id)

                await interaction.followup.send("Please select an attribute:", view=view)
            # Store the message object
            view.message = await interaction.original_response()
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error modifying  Leadership: {e}")
            await interaction.followup.send(content="An error occurred while modifying  Leadership.")

    @leadership_group.command(name="remove", description="Remove a leader from a kingdom")
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    @app_commands.autocomplete(title=kingdom_commands.leadership_autocomplete)
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
                status = await kingdom_commands.remove_leader(interaction.guild_id, interaction.user.id, kingdom, title)
                await interaction.followup.send(content=status)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"Error removing leader: {e}")
            await interaction.followup.send(content="An error occurred while removing the leader.")


    @event_group.command(name="create", description="Create a new event for the kingdom")
    @app_commands.choices(
        scale=[discord.app_commands.Choice(name='Kingdom Event', value=1),
             discord.app_commands.Choice(name='Settlement Event', value=0)])
    @app_commands.choices(
        hex=[discord.app_commands.Choice(name='affects a hex', value=1),
                  discord.app_commands.Choice(name='does not affect hexes', value=0)])
    @app_commands.choices(
        requirements=[discord.app_commands.Choice(name='succeed at one check', value=1),
                  discord.app_commands.Choice(name='succeed at both checks', value=2)])
    @app_commands.choices(
        type=[discord.app_commands.Choice(name='beneficial', value=1),
                  discord.app_commands.Choice(name='problematic', value=2)])
    @app_commands.choices(
        first_check=[discord.app_commands.Choice(name='Loyalty', value=1),
                     discord.app_commands.Choice(name='Stability', value=2),
                     discord.app_commands.Choice(name='Economy', value=3)])
    @app_commands.choices(
        second_check=[discord.app_commands.Choice(name='Loyalty', value=1),
                     discord.app_commands.Choice(name='Stability', value=2),
                     discord.app_commands.Choice(name='Economy', value=3),
                     discord.app_commands.Choice(name='Demand Building', value=4),
                     discord.app_commands.Choice(name='Demand Improvement', value=5)])
    @app_commands.autocomplete(shared_functions.region_autocomplete)
    async def create_event(
            self, interaction: discord.Interaction, scale: discord.app_commands[int], likelihood: int, name: str, description: str, special: typing.Optional[str],
            type: discord.app_commands.Choice[int], first_check: typing.Optional[discord.app_commands.Choice[int]],
            second_check: typing.Optional[discord.app_commands.Choice[int]], region: str = 'All',
            hex: discord.app_commands.Choice[int] = 0, requirements: discord.app_commands.Choice[int] = 0):
        """Create a new event for the kingdom"""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT Name from KB_Events where Name = ?", (name,))
                event = await cursor.fetchone()
                if event:
                    await interaction.followup.send("An event with that name already exists.")
                    return
                await cursor.execute("INSERT INTO KB_Events (scale, likelihood, Region, Name, Description, Special, Type, First_Check, Second_Check, Hex, Success_Requirements) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                     (scale, likelihood, region, name, description, special, type.value, first_check.value, second_check.value, hex, requirements.value))
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in create_event: {e}")
            await interaction.followup.send("An error occurred while creating an event.")




logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='application.log',  # Log to a file
    filemode='a'  # Append to the file
)

"""
    @kingdom_group.command(name="stabilization_points", description="Adjust the stabilization points of a kingdom.")
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    async def kingdom_stabilization_points(self, interaction: discord.Interaction, kingdom: str,
                                           stabilization_points: int):
        "Adjust the stabilization points of a kingdom."
        await interaction.response.defer(thinking=True)
        try:
            status = await kingdom_commands.adjust_sp(interaction.guild_id, interaction.user.id, kingdom,
                                                      stabilization_points)
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in kingdom_stabilization_points: {e}")
            await interaction.followup.send("An error occurred while adjusting kingdom stabilization points.")
"""

"""
    @settlement_group.command(name='decay',
                              description='Modify the multiplier for stabilization points a settlement requires in order to build.')
    @app_commands.autocomplete(kingdom=kingdom_commands.kingdom_autocomplete)
    @app_commands.autocomplete(settlement=kingdom_commands.settlement_autocomplete)
    async def settlement_decay(self, interaction: discord.Interaction, kingdom: str, settlement: str, decay: int):
        "Modify the multiplier for stabilization points a settlement requires in order to build."
        await interaction.response.defer(thinking=True)
        try:
            status = await settlement_decay_set(interaction.guild_id, interaction.user.id, kingdom, settlement, decay)
            await interaction.followup.send(status)
        except (TypeError, ValueError) as e:
            logging.exception(f"Error in settlement_decay: {e}")
            await interaction.followup.send("An error occurred while setting settlement decay.")
"""
