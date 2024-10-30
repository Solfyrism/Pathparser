import logging
from math import floor
from typing import List, Optional, Tuple, Union
import discord
import re
import unbelievaboat
from unidecode import unidecode
from discord.ext import commands
from discord import app_commands
import datetime
import os
from pywaclient.api import BoromirApiClient as WaClient
import aiosqlite
import shared_functions
from shared_functions import name_fix
from decimal import Decimal

# *** GLOBAL VARIABLES *** #
os.chdir("C:\\pathparser")


# LEVEL INFORMATION
async def get_max_level(cursor, guild_id: int) -> Optional[int]:
    await cursor.execute("SELECT Search FROM Admin WHERE Identifier = ?", ('Level_Cap',))
    row = await cursor.fetchone()
    if row is not None:
        return int(row[0])
    logging.error(f"Level cap not found for guild {guild_id}")
    return None


def calculate_milestones(
        milestone_values: Tuple[Optional[int], Optional[int], Optional[int], Optional[int]],
        multipliers: List[int],
        misc: int
) -> int:
    milestones = [
        (value if value is not None else 0) * multiplier
        for value, multiplier in zip(milestone_values, multipliers)
    ]
    return sum(milestones) + misc


async def get_new_level_info(
        cursor,
        total_milestones: int,
        maximum_level: int
) -> Optional[Tuple[int, int, int]]:
    await cursor.execute(
        "SELECT Level, Minimum_Milestones, Milestones_to_level FROM AA_Milestones "
        "WHERE Minimum_Milestones <= ? AND Level <= ? "
        "ORDER BY Minimum_Milestones DESC LIMIT 1",
        (total_milestones, maximum_level)
    )
    row = await cursor.fetchone()
    if row is not None:
        return row
    logging.error(
        f"No level information found for total milestones {total_milestones} "
        f"and level cap {maximum_level}"
    )
    return None


async def level_calculation(
        cursor: aiosqlite.Cursor,
        guild,
        guild_id: int,
        author_id,
        character_name: str,
        personal_cap: int,
        level: int,
        base: int,
        easy: int,
        medium: int,
        hard: int,
        deadly: int,
        misc: int
) -> Union[Tuple[int, int, int, int, int], int]:
    """
    Calculates the new level and milestone requirements for a character.
    ...

    Returns:
    - Tuple[int, int, int, int]: New level, minimum milestones, milestones to level, milestones required.
    - int: Returns -1 in case of an error.
    """
    return_value = -1  # Default return value in case of error
    try:
        logging.debug(f"Connected to database for guild {guild_id}")

        # Get maximum level cap
        max_level = await get_max_level(cursor, guild_id)
        if max_level is None:
            return return_value
        logging.debug(f"Max level cap for guild {guild_id} is {max_level}")

        # Get milestone information
        await cursor.execute(
            "SELECT easy, medium, hard, deadly FROM AA_Milestones WHERE level = ?",
            (level,)
        )

        milestone_information = await cursor.fetchone()
        if milestone_information is None:
            logging.error(f"Milestone information not found for level {level}")
            return return_value
        logging.debug(f"Milestone information for level {level}: {milestone_information}")

        # Calculate milestones
        multipliers = [easy, medium, hard, deadly]
        new_milestone_total = calculate_milestones(milestone_information, multipliers, misc)
        logging.debug(f"Calculated new milestone total: {new_milestone_total}")

        # Determine maximum level
        maximum_level = min(max_level, personal_cap)
        logging.debug(f"Maximum level for character '{character_name}': {maximum_level}")

        # Get new level information
        total_milestones = base + new_milestone_total
        new_level_info = await get_new_level_info(cursor, total_milestones, maximum_level)
        if new_level_info is None:
            return return_value
        new_level, min_milestones, milestones_to_level = new_level_info
        logging.debug(
            f"New level information: Level={new_level}, "
            f"Minimum_Milestones={min_milestones}, Milestones_to_level={milestones_to_level}"
        )

        # Update player character
        milestones_required = min_milestones + milestones_to_level - new_milestone_total
        await cursor.execute(
            "UPDATE Player_Characters SET Level = ?, Milestones = ?, Milestones_Required = ? "
            "WHERE Character_Name = ?",
            (new_level, total_milestones, milestones_required, character_name)
        )
        await cursor.connection.commit()
        logging.info(
            f"Updated character '{character_name}': Level={new_level}, "
            f"Milestones={total_milestones}, Milestones_Required={milestones_required}"
        )
        await level_ranges(cursor, guild, author_id, level, new_level)
        return_value = (new_level, total_milestones, min_milestones, milestones_to_level, milestones_required)
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error in level calculation for character '{character_name}': {e}")
    return return_value


async def level_ranges(cursor: aiosqlite.Cursor, guild, author_id: int, level: int, new_level: int) -> None:
    try:
        await cursor.execute("SELECT Level, Role_Name, Role_ID FROM Level_Range WHERE level = ?", (new_level,))
        new_role = await cursor.fetchone()
        if new_role is None:
            logging.error(f"Role not found for level {new_level}")
            return None
        else:
            member = guild.get_member(author_id)
            new_level_range_role = guild.get_role(new_role[2])
            member.add_roles(new_level_range_role)
            await cursor.execute("SELECT Role_name FROM Level_Range WHERE level = ?", (level,))
            old_role = await cursor.fetchone()
            if old_role is not None:
                await cursor.execute("SELECT Min(Level), Max(Level) from Level_Range where Role_Name = ?",
                                     (old_role[0],))
                old_role_range = await cursor.fetchone()
                await cursor.execute(
                    "SELECT Character_Name from Player_Characters where Player_ID = ? AND level > ? AND LEVEL < ?",
                    (author_id, old_role_range[0], old_role_range[1]))
                character = await cursor.fetchone()
                if character is None:
                    old_level_range_role = guild.get_role(old_role[0])
                    member.remove_roles(old_level_range_role)
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error in level ranges for <@{author_id}> with error: {e}")
        return None


# Mythic Information
async def get_max_mythic(cursor, guild_id: int, level: int) -> Optional[int]:
    await cursor.execute("SELECT Search FROM Admin WHERE Identifier = ?", ('Tier_Cap',))
    max_tier = await cursor.fetchone()
    await cursor.execute("SELECT Search FROM Admin WHERE Identifier = ?", ('Tier_Rate_Limit_1',))
    rate_limit_1 = await cursor.fetchone()
    await cursor.execute("SELECT Search FROM Admin WHERE Identifier = ?", ('Tier_Rate_Limit_2',))
    rate_limit_2 = await cursor.fetchone()
    await cursor.execute("SELECT Search FROM Admin WHERE Identifier = ?", ('Tier_Rate_Limit_Breakpoint',))
    rate_limit_breakpoint = await cursor.fetchone()
    if rate_limit_2 is not None and rate_limit_1 is not None and rate_limit_breakpoint is not None:
        rate_limit_max = floor(level / rate_limit_1[0]) if level < rate_limit_breakpoint[0] else floor(
            level / rate_limit_2[0])
    else:
        rate_limit_max = 99
    if max_tier is not None:
        return min(rate_limit_max, max_tier[0])
    else:
        logging.error(f"Mythic cap not found for guild {guild_id}")
        return None


async def get_new_tier_info(
        cursor,
        total_milestones: int,
        maximum_level: int
) -> Optional[Tuple[int, int, int]]:
    await cursor.execute(
        "SELECT Level, Minimum_Milestones, Milestones_to_level FROM AA_Milestones "
        "WHERE Minimum_Milestones <= ? AND Level <= ? "
        "ORDER BY Minimum_Milestones DESC LIMIT 1",
        (total_milestones, maximum_level)
    )
    row = await cursor.fetchone()
    if row is not None:
        return row
    logging.error(
        f"No level information found for total milestones {total_milestones} "
        f"and level cap {maximum_level}"
    )
    return None


async def mythic_calculation(cursor, character_name, level, trials, trial_change) -> (Union[Tuple[int, int, int], int]):
    try:
        # Call limiters and restrictions.
        await cursor.execute("SELECT Search from Admin WHERE Identifier = 'Mythic_Cap'")
        max_mythic = await cursor.fetchone()
        await cursor.execute("SELECT Search from Admin WHERE Identifier = 'Tier_Rate_limit_1'")
        tier_rate_limit_1 = await cursor.fetchone()
        await cursor.execute("SELECT Search from Admin WHERE Identifier = 'Tier_Rate_limit_2'")
        tier_rate_limit_2 = await cursor.fetchone()
        await cursor.execute("SELECT Search from Admin WHERE Identifier = 'Tier_Rate_limit_Breakpoint'")
        tier_rate_limit_breakpoint = await cursor.fetchone()
        tier_rate_limit_modifier = tier_rate_limit_1[0] if level < tier_rate_limit_breakpoint[0] else tier_rate_limit_2[
            0]
        tier_max = floor(trials / tier_rate_limit_modifier) if floor(trials / tier_rate_limit_modifier) <= max_mythic[
            0] else max_mythic[0]
        # Call the mythic tier information.
        await cursor.execute(
            f"SELECT Tier, Trials, Trials_Required from AA_Mythic  WHERE Trials <= ? AND Tier <= ? ORDER BY Trials DESC  LIMIT 1",
            (trials + trial_change, tier_max))
        new_mythic_information = await cursor.fetchone()
        # Update Mythic tier if you changed the trial amount.
        await cursor.execute(
            f"UPDATE Player_Characters SET Tier = ?, Trials = ?, Trials_Required = ? WHERE Character_Name = ?",
            (new_mythic_information[0], trials + trial_change,
             new_mythic_information[1] + new_mythic_information[2] - trials + trial_change, character_name))
        await cursor.commit()
        # return mythic tier, trials, and mythic trials remaining.
        return_value = (new_mythic_information[0], trials + trial_change,
                        new_mythic_information[1] + new_mythic_information[2] - trial_change - trials)
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error in mythic calculation for {character_name} with error: {e}")
        return_value = -1
    return return_value


async def gold_calculation(
        cursor: aiosqlite.Cursor,
        interaction: discord.Interaction,
        character_name: str,
        level: int,
        oath: str,
        gold: int,
        gold_value: int,
        gold_value_max: int,
        gold_change: int,
        source: str,
        reason: str
) -> Union[Tuple[int, int, int, int], int, str]:
    return_value = -1
    time = datetime.datetime.now()
    try:
        if gold_change > 0:
            if oath == 'Offerings':
                # Only half the gold change is applied
                difference = int(gold_change * 0.5)
                gold_total = gold + difference
                gold_value_total = gold_value + difference
            elif oath in ('Poverty', 'Absolute'):
                max_gold = 80 * level * level if oath == 'Poverty' else level * 5
                if gold_value >= max_gold:
                    # Cannot gain more gold
                    difference = 0
                elif gold_value + gold_change > max_gold:
                    # Cap the gold gain to reach max_gold
                    difference = max_gold - gold_value
                else:
                    difference = gold_change
                gold_total = gold + difference
                gold_value_total = gold_value + difference
            else:
                # Other oaths gain gold normally
                difference = gold_change
                gold_total = gold + difference
                gold_value_total = gold_value + difference
        else:
            # For gold loss, apply the change directly
            difference = gold_change
            gold_total = gold + difference
            gold_value_total = gold_value + difference

        # Ensure gold values are not negative
        if gold_total < 0 or gold_value_total < 0:
            return_value = "Gold cannot be negative."
        else:
            gold_value_max_total = gold_value_max
            # Update the database
            await cursor.execute(
                "UPDATE Player_Characters SET Gold = ?, Gold_Value = ?, Gold_Value_Max = ? WHERE Character_Name = ?",
                (Decimal(gold_total), Decimal(gold_value_total), Decimal(gold_value_max_total), character_name)
            )
            await cursor.connection.commit()
            sql = "INSERT INTO A_Audit_Gold(Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
            val = (
                interaction.user.name, interaction.user.id, character_name, Decimal(gold_total),
                Decimal(gold_value_total),
                Decimal(gold_value_max_total), reason, source, time)
            await cursor.execute(sql, val)
            await cursor.connection.commit()
            await cursor.execute("SELECT Max(transaction_id) FROM A_Audit_Gold")
            transaction_id = await cursor.fetchone()
            logging.info(f"Gold updated for character '{character_name}', transaction_id: {transaction_id[0]}.")
            return_value = (
                Decimal(gold_total), Decimal(gold_value_total), Decimal(gold_value_max_total), transaction_id[0])
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error in gold calculation for character '{character_name}': {e}")
    return return_value


async def ubb_inventory_check(guild_id: int, author_id: int, item_id: int, amount: int) -> int:
    client = unbelievaboat.Client(os.getenv('UBB_TOKEN'))
    try:
        inventory = await client.get_inventory_item(guild_id, author_id, item_id[0])
        inventory_remaining = inventory.quantity
        amount = min(amount, inventory_remaining)
        return amount
    except unbelievaboat.errors.HTTPError:
        logging.exception(f"Failed to retrieve inventory item {item_id[0]} for user {author_id}")
        return 0


async def flux_calculation(cursor, character_name, flux, flux_change):
    try:
        flux_total = flux + flux_change
        await cursor.execute(
            f"UPDATE Player_Characters SET Flux = ? WHERE Character_Name = ?",
            (flux_total, character_name))
        await cursor.commit()
        return_value = flux_total
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error in flux calculation for {character_name} with error: {e}")
        return_value = -1
    return return_value


async def stg_character_embed(cursor, character_name) -> (Union[Tuple[discord.Embed, str], str]):
    try:
        # 7 7 1
        await cursor.execute(
            "SELECT player_name, player_id, True_Character_Name, Titles, Description, Oath, Level, "
            "Tier, Milestones, Milestones_Required, Trials, Trials_Required, Color, Mythweavers, "
            "Image_Link"
            " FROM A_STG_Player_Characters WHERE Character_Name = ?", (character_name,))
        character_info = await cursor.fetchone()
        color = character_info[12]
        int_color = int(color[1:], 16)
        description_field = f" "
        if character_info[3] is not None:
            description_field += f"**Other Names**: {character_info[3]} \r\n"  # Titles
        if character_info[4] is not None:  # Description
            description_field += f"[**Description**](<{character_info[4]}>)"
        titled_character_name = character_info[2]
        embed = discord.Embed(title=f"{titled_character_name}", url=f'{character_info[13]}',
                              description=f"{description_field}",  # Character Name, Mythweavers, Description
                              color=int_color)
        embed.set_author(name=f'{character_info[0]}')  # Player Name
        embed.set_thumbnail(url=f'{character_info[14]}')  # Image Link
        embed.add_field(name="Information",
                        value=f'**Level**: {character_info[6]}, '
                              f'**Mythic Tier**: {character_info[7]}',
                        # Level, Tier, Fame, Prestige
                        inline=False)
        embed.add_field(name="Experience",
                        value=f'**Milestones**: {character_info[8]}, '
                              f'**Remaining**: {character_info[9]}')  # Milestones, Remaining Milestones
        embed.add_field(name="Mythic",
                        value=f'**Trials**: {character_info[10]}, '
                              f'**Remaining**: {character_info[11]}')  # Trials, Remaining Trials
        description = character_info[4]
        if character_info[5] == 'Offerings':
            embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
        elif character_info[5] == 'Poverty':
            embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
        elif character_info[5] == 'Absolute':
            embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
        else:
            embed.set_footer(text=f'{description}')
        message = f"<@{character_info[1]}>"
        return_message = embed, message

    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"An error occurred whilst building character embed for '{character_name}': {e}")
        return_message = f"An error occurred whilst building character embed for '{character_name}'."
    return return_message


# noinspection PyUnresolvedReferences
class CharacterCommands(commands.GroupCog, name='character'):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help', description='Help commands for the character tree')
    async def help(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        embed = discord.Embed(title=f"Character Help", description=f'This is a list of Character commands',
                              colour=discord.Colour.blurple())
        try:
            embed.add_field(name=f'**Register**', value=f'Register your character!', inline=False)
            embed.add_field(name=f'**Retire**', value=f'Retire a registered character!', inline=False)
            embed.add_field(name=f'**levelup**', value=f'Use Medium Jobs from the unbelievaboat shop.', inline=False)
            embed.add_field(name=f'**trialup**', value=f'Use Trial Catch Ups from the unbelievaboat shop', inline=False)
            embed.add_field(name=f'**Pouch**', value=f'Use Gold Pouches from the unbelievaboat shop.', inline=False)
            embed.add_field(name=f'**Display**', value=f'View information about a character.', inline=False)
            embed.add_field(name=f'**List**', value=f'View information about characters in a level range.',
                            inline=False)
            embed.add_field(name=f'**Edit**',
                            value=f'Change the Character Name, Mythweavers, Image, Nickname, Titles, Description, Oath of your character, or color of your embed.',
                            inline=False)
            embed.add_field(name=f'**Entitle**',
                            value=f'Use an approved title item from the unbelievaboat Store. NOTE: Your most famous title is the one that will be used.',
                            inline=False)
            embed.add_field(name=f'**Proposition**', value=f'Use your prestigious status to proposition an act.',
                            inline=False)
            embed.add_field(name=f'**Cap**', value=f'Stop yourself from leveling! For reasons only you understand.',
                            inline=False)
            embed.add_field(name=f'**Backstory**',
                            value=f'Give your character a backstory if they do not already have one.',
                            inline=False)
            await interaction.followup.send(embed=embed)
        except discord.errors.HTTPException:
            logging.exception(f"Error in help command")
            await interaction.channel.send(embed=embed)
        finally:
            return

    @app_commands.command(name='register', description='register a character')
    @app_commands.describe(oath="Determining future gold gain from sessions and gold claims.")
    @app_commands.choices(oath=[discord.app_commands.Choice(name='No Oath', value=1),
                                discord.app_commands.Choice(name='Oath of Offerings', value=2),
                                discord.app_commands.Choice(name='Oath of Poverty', value=3),
                                discord.app_commands.Choice(name='Oath of Absolute Poverty', value=4)])
    @app_commands.describe(nickname='a shorthand way to look for your character in displays')
    async def register(self, interaction: discord.Interaction, character_name: str, mythweavers: str, image_link: str,
                       nickname: str = None,
                       titles: str = None, description: str = None, oath: discord.app_commands.Choice[int] = 1,
                       color: str = '#5865F2', backstory: str = None):
        await interaction.response.defer(thinking=True)
        guild_id = interaction.guild_id
        author = interaction.user.name
        author_id = interaction.user.id
        time = datetime.datetime.now()
        oath_name = 'No Oath' if oath == 1 else oath.name
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                if character_name is not None:
                    true_character_name, character_name = name_fix(character_name)
                else:
                    await interaction.response.send_message(f"Character Name is required")
                    return
                if nickname is not None:
                    _, nickname = name_fix(nickname)
                if titles is not None:
                    titles, _ = name_fix(titles)
                if description is not None:
                    description = str.replace(description, ";", "")
                if mythweavers is not None:
                    mythweavers = str.replace(str.replace(str.lower(mythweavers), ";", ""), ")", "")
                    mythweavers_valid = str.lower(mythweavers[0:5])
                    if mythweavers_valid != 'https':
                        await interaction.response.send_message(f"Mythweavers link is missing HTTPS:", ephemeral=True)
                        return
                else:
                    await interaction.response.send_message(f"Mythweavers link is required", ephemeral=True)
                    return
                if image_link is not None:
                    image_link = str.replace(str.replace(image_link, ";", ""), ")", "")
                    image_link_valid = str.lower(image_link[0:5])
                    if image_link_valid != 'https':
                        await interaction.response.send_message(f"Image link is missing HTTPS:")
                        return
                else:
                    await interaction.response.send_message(f"image link is required", ephemeral=True)
                    return
                regex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
                match = re.search(regex, color)
                if len(color) == 7 and match:
                    await cursor.execute(
                        "SELECT Player_Name, Character_Name from Player_Characters where Character_Name = ?",
                        (character_name,))
                    results = cursor.fetchone()
                    await cursor.execute(
                        "SELECT Player_Name, Character_Name from A_STG_Player_Characters where Character_Name = ?",
                        (character_name,))
                    results2 = cursor.fetchone()
                    if results is None and results2 is None:
                        try:
                            sql = "insert into A_STG_Player_Characters (Player_Name, Player_ID, Character_Name, True_Character_Name, Nickname, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Flux, Color, Mythweavers, Image_Link, Backstory, Date_Created) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
                            val = (
                                author, author_id, character_name, true_character_name, nickname, titles, description,
                                oath_name, 3, 0, 0, 3, 0, 0, 0, color, mythweavers, image_link, backstory, time)
                            await cursor.execute(sql, val)
                            await conn.commit()
                            embed = await stg_character_embed(cursor, character_name)
                            await interaction.response.send_message(embed=embed)
                        except discord.errors.HTTPException:
                            embed[0].set_thumbnail(
                                url=f'https://cdn.discordapp.com/attachments/977939245463392276/1194140952789536808/download.jpg?ex=65af456d&is=659cd06d&hm=1613025f9f1c1263823881c91a81fc4b93831ff91df9f4a84c813e9fab6467e9&')
                            embed[0].set_footer(text=f'Oops! You used a bad URL, please fix it.')
                            await interaction.response.send_message(embed=embed)
                            sql = f"Update A_STG_Player_Characters SET Image_Link = ? AND Mythweavers = ? WHERE Character_Name = ?"
                            val = (
                                "https://cdn.discordapp.com/attachments/977939245463392276/1194140952789536808/download.jpg?ex=65af456d&is=659cd06d&hm=1613025f9f1c1263823881c91a81fc4b93831ff91df9f4a84c813e9fab6467e9&",
                                "https://cdn.discordapp.com/attachments/977939245463392276/1194141019088891984/super_saiyan_mr_bean_by_zakariajames6_defpqaz-fullview.jpg?ex=65af457d&is=659cd07d&hm=57bdefe2d376face6a842a7b7a5ed8021e854a64e798f901824242c4a939a37b&",
                                character_name)
                            await cursor.execute(sql, val)
                            await conn.commit()
                    else:
                        await interaction.response.send_message(
                            f"{character_name} has already been registered by {author}",
                            ephemeral=True)
                else:
                    await interaction.followup.send(f"Invalid Hex Color Code!", ephemeral=True)
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(f"An error occurred whilst building character embed for '{character_name}': {e}")
                interaction.response.send_message = f"An error occurred whilst building character embed for '{character_name}' Error: {e}."

    @app_commands.command(name='edit', description='edit your character')
    @app_commands.autocomplete(name=shared_functions.own_character_select_autocompletion)
    @app_commands.describe(oath="Determining future gold gain from sessions and gold claims.")
    @app_commands.choices(oath=[discord.app_commands.Choice(name='No Oath', value=1),
                                discord.app_commands.Choice(name='Oath of Offerings', value=2),
                                discord.app_commands.Choice(name='Oath of Poverty', value=3),
                                discord.app_commands.Choice(name='Oath of Absolute Poverty', value=4),
                                discord.app_commands.Choice(name='No Change', value=5)])
    @app_commands.describe(new_nickname='a shorthand way to look for your character in displays')
    async def edit(self, interaction: discord.Interaction, name: str, new_character_name: str = None,
                   mythweavers: str = None,
                   image_link: str = None, new_nickname: str = None, titles: str = None, description: str = None,
                   oath: discord.app_commands.Choice[int] = 5, color: str = None):
        guild_id = interaction.guild_id
        guild = interaction.guild
        author = interaction.user.name
        interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                sql = ("Select True_Character_Name, Nickname, Titles, Description, Mythweavers, Image_Link, Oath, "
                       "Color, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, "
                       "Gold, Gold_Value, Gold_Value_Max, Flux, Thread_ID, Fame, Title, "
                       "Personal_Cap, Prestige, Article_Link FROM Player_Characters "
                       "where Player_Name = ? AND Character_Name = ? OR Player_Name = ? AND  Nickname = ?")
                val = (author, name, author, name)
                await cursor.execute(sql, val)
                results = await cursor.fetchone()
                await interaction.response.defer(thinking=True, ephemeral=True)
                if results is None:
                    sql = f"Select True_Character_Name, Nickname, Titles, Description, Mythweavers, Image_Link, Oath, Color, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Gold_Value, Gold_Value_Max, Flux, Character_Name from A_STG_Player_Characters where Player_Name = ? AND Character_Name = ? OR  Player_Name = ? AND Nickname = ?"
                    val = (author, name, author, name)
                    await cursor.execute(sql, val)
                    results = cursor.fetchone()
                    if results is None:
                        await interaction.followup.send(
                            f"Cannot find any {name} owned by {author} with the supplied name or nickname.")
                    else:
                        if new_character_name is not None:
                            true_character_name, new_character_name = name_fix(new_character_name)
                        else:
                            true_character_name = results[0]
                            new_character_name = results[18]
                        if new_nickname is not None:
                            new_nickname, _ = name_fix(new_nickname)
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
                            mythweavers = str.replace(str.replace(str.lower(mythweavers), ";", ""), ")", "")
                            mythweavers_valid = str.lower(mythweavers[0:5])
                            if mythweavers_valid != 'https':
                                await interaction.response.send_message(f"Mythweavers link is missing HTTPS:")
                                return
                        else:
                            mythweavers = results[4]
                        if image_link is not None:
                            image_link = str.replace(str.replace(image_link, ";", ""), ")", "")
                            image_link_valid = str.lower(image_link[0:5])
                            print(image_link_valid)
                            if image_link_valid != 'https':
                                await interaction.response.send_message(f"Image link is missing HTTPS:")
                                return
                        else:
                            image_link = results[5]
                        oath = 'No Change' if oath == 5 else oath.name
                        if oath == 'No Change':
                            oath_name = results[6]
                        else:
                            oath_name = oath
                        if color is not None:
                            regex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
                            match = re.search(regex, color)
                        else:
                            color = results[7]
                            regex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
                            match = re.search(regex, color)
                        if len(color) == 7 and match:
                            true_name = results[0]
                            await cursor.execute("update a_stg_player_characters set "
                                                 "True_Character_Name = ?, Character_Name = ?, Nickname = ?, Titles = ?,"
                                                 " Description = ?, Mythweavers = ?, Image_Link = ?, Oath = ?, "
                                                 "Color = ? "
                                                 "where True_Character_Name = ?", (
                                                     true_character_name, new_character_name, new_nickname, titles,
                                                     description, mythweavers, image_link, oath_name, color, true_name))
                            embed = await stg_character_embed(cursor, new_character_name)
                            await interaction.response.send_message(embed=embed)
                        else:
                            await interaction.response.send_message(f"Invalid Hex Color Code!")
                else:

                    if new_character_name is not None:
                        new_character_name, true_character_name = name_fix(new_character_name)
                        character_changes = shared_functions.CharacterChange(character_name=new_character_name,
                                                                             author=author,
                                                                             source='Character Edit')
                    else:
                        new_character_name, true_character_name = name_fix(results[0])
                        character_changes = shared_functions.CharacterChange(character_name=new_character_name,
                                                                             author=author,
                                                                             source='Character Edit')
                    if new_nickname is not None:
                        new_nickname, _ = name_fix(new_nickname)
                    else:
                        new_nickname = results[1]
                    if titles is not None:
                        titles = str.replace(str.replace(titles, ";", ""), ")", "")
                        character_changes.titles = titles
                    else:
                        titles = results[2]
                    if description is not None:
                        description = str.replace(str.replace(description, ";", ""), ")", "")
                        character_changes.description = description
                    else:
                        description = results[3]
                    if mythweavers is not None:
                        mythweavers = str.replace(str.replace(mythweavers, ";", ""), ")", "")
                        mythweavers_valid = str.lower(mythweavers[0:5])
                        character_changes.mythweavers = mythweavers
                        if mythweavers_valid != 'https':
                            await interaction.followup.send(f"Mythweavers link is missing HTTPS:")
                            return
                    else:
                        mythweavers = results[4]
                    if image_link is not None:
                        image_link = str.replace(str.replace(image_link, ";", ""), ")", "")
                        image_link_valid = str.lower(image_link[0:5])
                        character_changes.image_link = image_link
                        if image_link_valid != 'https':
                            await interaction.followup.send(f"Image link is missing HTTPS:")
                            return
                    else:
                        image_link = results[5]
                    oath = 'No Change' if oath == 5 else oath.name
                    if oath == 'No Change':
                        oath_name = results[6]
                    else:
                        oath_name = oath
                        character_changes.oath = oath_name
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
                            if oath_name != results[6] and results[8] < 7:
                                if oath == 'Offerings':
                                    # Only half the gold change is applied
                                    gold_total = Decimal(results[14] * 0.5)
                                    gold_value_total = results[15] - gold_total
                                    gold_value_total_max = gold_value_total
                                elif oath in ('Poverty', 'Absolute'):
                                    max_gold = 80 * results[8] * results[8] if oath == 'Poverty' else results[8] * 5
                                    if results[15] >= max_gold:
                                        # Cannot gain more gold
                                        gold_total = gold + max_gold - results[15]
                                        gold_value_total = max_gold
                                        gold_value_total_max = results[16]
                                    else:
                                        gold_total = results[14]
                                        gold_value_total = results[15]
                                        gold_value_total_max = results[16]
                                else:
                                    # Other oaths gain gold normally
                                    gold_total = results[14]
                                    gold_value_total = results[15]
                                    gold_value_total_max = results[15]
                                await cursor.execute(
                                    "UPDATE Player_Characters SET Gold = ?, Gold_Value = ?, Gold_Value_Max = ? WHERE Character_Name = ?",
                                    (Decimal(gold_total), Decimal(gold_value_total), Decimal(gold_value_total_max),
                                     character_name)
                                )
                                await conn.commit()
                                sql = "INSERT INTO A_Audit_Gold(Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
                                val = (interaction.user.name, interaction.user.id, character_name, Decimal(gold_total),
                                       Decimal(gold_value_total), Decimal(gold_value_max_total), 'Oaths were Changed',
                                       'Character Edit', datetime.datetime.now())
                                await cursor.execute(sql, val)
                                await cursor.connection.commit()
                                await cursor.execute("SELECT Max(transaction_id) FROM A_Audit_Gold")
                                transaction_id = await cursor.fetchone()
                                logging.info(
                                    f"Gold updated for character '{character_name}' Transaction ID: {transaction_id[0]}.")
                            if results[23] is not None:
                                pass
                                # await EventCommand.edit_bio(self, guild_id, new_character_name, None, results[22])
                            await cursor.execute(
                                "update Player_Characters set True_Character_Name = ?, Character_Name = ?, Nickname = ?, Titles = ?, Description = ?, Mythweavers = ?, Image_Link = ?, Oath = ?, Color = ? where Character_Name = ?",
                                (
                                    true_character_name, new_character_name, new_nickname, titles, description,
                                    mythweavers,
                                    image_link, oath_name, color, name))
                            await conn.commit()
                            await cursor.execute("Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                            character_log_channel_id = await cursor.fetchone()
                            char_embed = await character_embed(cursor, new_character_name)
                            bio_channel = await bot.fetch_channel(char_embed[3])
                            bio_message = await bio_channel.fetch_message(player_info[24])
                            await bio_message.edit(content=char_embed[1], embed=char_embed[0])
                            embed = char_embed[0]
                            if oath_name == 'Offerings':
                                embed.set_footer(text=f'Character Successfully Updated! \r\n {description}',
                                                 icon_url=f'https://i.imgur.com/dSuLyJd.png')
                            elif oath_name[6] == 'Poverty':
                                embed.set_footer(text=f'Character Successfully Updated! \r\n {description}',
                                                 icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
                            elif oath_name[6] == 'Absolute':
                                embed.set_footer(text=f'Character Successfully Updated! \r\n {description}',
                                                 icon_url=f'https://i.imgur.com/ibE5vSY.png')
                            else:
                                embed.set_footer(text=f'Character Successfully Updated! \r\n {description}')
                            character_logging_embed = shared_functions.log_embed(character_changes)
                            logging_thread = guild.get_thread(player_info[25])
                            await logging_thread.send(embed=embed)
                            await logging_thread.edit(name=f"{new_character_name}")
                            logging_channel = await bot.fetch_channel(character_log_channel_id[0])
                            logging_message = await logging_channel.fetch_message(player_info[25])
                            mentions = f'<@{player_info[1]}>'
                            embed = discord.Embed(title=f"{new_character_name}", url=f'{mythweavers}',
                                                  description=f"Other Names: {titles}", color=int_color)
                            embed.set_author(name=f'{author}')
                            embed.set_thumbnail(url=f'{image_link}')
                            await logging_message.edit(content=mentions, embed=embed)
                            await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"Invalid Hex Color Code!")
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(f"An error occurred whilst building character embed for '{character_name}': {e}")
                interaction.response.send_message = f"An error occurred whilst building character embed for '{character_name}' Error: {e}."

    @app_commands.command(name='retire', description='retire a character')
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def retire(self, interaction: discord.Interaction, character_name: str):
        guild_id = interaction.guild_id
        guild = interaction.guild
        author = interaction.user.name
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                _, character_name = name_fix(character_name)
                sql = """
                    SELECT True_Character_Name, Thread_ID 
                    FROM Player_Characters 
                    WHERE Player_Name = ? AND (Character_Name = ? OR Nickname = ?)
                """
                val = (author, character_name, character_name)
                await cursor.execute(sql, val)
                results = await cursor.fetchone()
                if results is None:
                    await interaction.followup.send(
                        f"There is no character registered by character name or nickname as {character_name} owned by {interaction.user.name} to unregister.",
                        ephemeral=True
                    )
                else:
                    true_character_name = results[0]
                    view = RetirementView(character_name, interaction.user.id, guild_id)
                    await interaction.followup.send(content='You are retiring me?! But you love me!', view=view)
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(f"An error occurred in the retire command whilst looking for '{character_name}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst looking for '{character_name}'. Error: {e}.",
                    ephemeral=True
                )

    @app_commands.command(name='levelup', description='level up your character')
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def levelup(self, interaction: discord.Interaction, character_name: str, amount: int):
        guild_id = interaction.guild_id
        guild = interaction.guild
        author = interaction.user.name
        author_id = interaction.user.id
        await interaction.response.defer(thinking=True)
        if amount >= 1:
            async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
                cursor = await conn.cursor()
                try:
                    await cursor.execute("SELECT Character_Name, Personal_Cap, Level, Milestone, tier, trials")
                    player_info = await cursor.fetchone()
                    if player_info is None:
                        await interaction.followup.send(
                            f"Character {character_name} not found.",
                            ephemeral=True
                        )
                    else:
                        server_max_level = await get_max_level(cursor, guild_id)
                        (character_name, personal_cap, level, starting_base, tier, trials) = player_info
                        base = starting_base
                        max_level = min(server_max_level, personal_cap)
                        if level >= max_level:
                            await interaction.followup.send(
                                f"{character_name} is already at the maximum level of {max_level}.",
                                ephemeral=True
                            )
                        else:
                            await cursor.execute("SELECT Search from Admin Where Identifier = 'UBB_Medium_Job'")
                            item_id = await cursor.fetchone()
                            item = await ubb_inventory_check(guild_id, interaction.user.id, int(item_id[0]), amount)
                            if item == 0:
                                await interaction.followup.send(
                                    f"Insufficient Medium Jobs to level up {character_name}.",
                                    ephemeral=True
                                )
                            else:
                                x = 1
                                new_level_info = (0, 0, 0, 0, 0)
                                while x <= item and level <= max_level:
                                    x += 1
                                    new_level_info = await level_calculation(cursor, guild, guild_id, author_id,
                                                                             character_name, personal_cap, level, base,
                                                                             0, 1, 0, 0, 0)
                                    level = new_level_info[0]
                                    base = new_level_info[1]
                                client = unbelievaboat.Client(os.getenv('UBB_TOKEN'))
                                await client.delete_inventory_item(guild_id, author_id, item_id[0], used)
                                mythic_results = await mythic_calculation(cursor, character_name, level, trials, 0)
                                character_embed = await shared_functions.character_embed(cursor, character_name, guild)
                                character_changes = shared_functions.CharacterChange(character_name=character_name,
                                                                                     author=author, source='Level Up',
                                                                                     level=level,
                                                                                     milestone_change=base - starting_base,
                                                                                     milestones_total=base,
                                                                                     milestones_remaining=
                                                                                     new_level_info[4])
                                if mythic_results[0] != tier:
                                    character_changes.tier = mythic_results[0]
                                    character_changes.trials = mythic_results[1]
                                    character_changes.trials_remaining = mythic_results[2]
                                character_log = await shared_functions.log_embed(character_changes, guild,
                                                                                 logging_thread_id, self.bot)
                                await interaction.followup.send(embed=character_log, ephemeral=True)
                except aiosqlite.Error as e:
                    logging.exception(f"A SQLite error occurred in the levelup command for: '{character_name}!: {e}")
                    await interaction.followup.send(
                        f"A SQLite error occurred in the levelup command for: '{character_name}'. Error: {e}.",
                        ephemeral=True
                    )
                except unbelievaboat.errors.HTTPError as e:
                    logging.exception(f"An error occurred contacting unbelievabot API! check {item_id}!: {e}")
                    await interaction.followup.send(
                        f"An error occurred contacting unbelievabot API! check {item_id}!: Error: {e}.",
                        ephemeral=True
                    )
        else:
            await interaction.followup.send("You must use at least one job.")
            return

    @app_commands.command(name='trialup', description='Apply mythic tiers to your character')
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def Trialup(self, interaction: discord.Interaction, character_name: str, amount: int):
        guild_id = interaction.guild_id
        guild = interaction.guild
        author = interaction.user.name
        await interaction.response.defer(thinking=True)
        if amount >= 1:
            async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
                cursor = await conn.cursor()
                try:
                    await cursor.execute("SELECT Character_Name, Personal_Cap, Level, tier, trials")
                    player_info = await cursor.fetchone()
                    if player_info is None:
                        await interaction.followup.send(
                            f"Character {character_name} not found.",
                            ephemeral=True
                        )
                    else:
                        (character_name, personal_cap, level, tier, trials) = player_info
                        character_max_mythic = await get_max_mythic(cursor, guild_id, level)
                        base = trials
                        if tier >= character_max_mythic:
                            await interaction.followup.send(
                                f"{character_name} is already at the maximum tier of {max_level}.",
                                ephemeral=True
                            )
                        else:
                            await cursor.execute("SELECT Search from Admin Where Identifier = 'UBB_Medium_Job'")
                            item_id = await cursor.fetchone()
                            item = await ubb_inventory_check(guild_id, interaction.user.id, int(item_id[0]), amount)
                            if item == 0:
                                await interaction.followup.send(
                                    f"Insufficient Mythic Trials to apply to {character_name}.",
                                    ephemeral=True
                                )
                            else:
                                x = 1
                                new_mythic_info = (0, 0, 0)
                                while x <= item and tier <= character_max_mythic:
                                    x += 1
                                    mythic_results = await mythic_calculation(cursor, character_name, level, trials, 1)
                                    tier = new_level_info[0]
                                    trials = new_level_info[1]
                                client = unbelievaboat.Client(os.getenv('UBB_TOKEN'))
                                await client.delete_inventory_item(guild_id, author_id, item_id[0], used)
                                character_embed = await shared_functions.character_embed(cursor, character_name, guild)
                                character_changes = shared_functions.CharacterChange(character_name=character_name,
                                                                                     author=author, source='Trial Up!',
                                                                                     tier=tier,
                                                                                     trial_change=trials - base,
                                                                                     trials_remaining=new_mythic_info[
                                                                                         2], trials=trials)
                                character_log = await shared_functions.log_embed(character_changes, guild,
                                                                                 logging_thread_id, self.bot)
                                await interaction.followup.send(embed=character_log, ephemeral=True)
                except aiosqlite.Error as e:
                    logging.exception(f"A SQLite error occurred in the trialup command for: '{character_name}!: {e}")
                    await interaction.followup.send(
                        f"A SQLite error occurred in the trialup command for: '{character_name}'. Error: {e}.",
                        ephemeral=True
                    )
                except unbelievaboat.errors.HTTPError as e:
                    logging.exception(f"An error occurred contacting unbelievabot API! check {item_id}!: {e}")
                    await interaction.followup.send(
                        f"An error occurred contacting unbelievabot API! check {item_id}!: Error: {e}.",
                        ephemeral=True
                    )
        else:
            await interaction.followup.send("You must use at least one mythic trial.")

    @app_commands.command(name='pouch', description='Use a gold pouch to enrich your character')
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def pouch(self, interaction: discord.Interaction, character_name: str):
        guild_id = interaction.guild_id
        guild = interaction.guild
        author = interaction.user.name
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute("SELECT Character_Name, Level, Gold, Gold_Value, Gold_Value_Max")
                player_info = await cursor.fetchone()
                if player_info is None:
                    await interaction.followup.send(
                        f"Character {character_name} not found.",
                        ephemeral=True
                    )
                else:
                    (character_name, personal_cap, level, gold, gold_value, gold_value_max) = player_info
                    await cursor.execute("SELECT WPL FROM AA_Milestones WHERE LEVEL =?", (level,))
                    gold_pouch = await cursor.fetchone()
                    if gold_pouch is None:
                        await interaction.followup.send(
                            f"Gold Pouch for level {level} not found.",
                            ephemeral=True
                        )
                    else:
                        gold_pouch = gold_pouch[0]
                        if gold_value >= gold_pouch:
                            await interaction.followup.send(
                                f"{character_name} is already at the maximum gold pouch value of {gold_pouch} with their total wealth of {gold_value_max}.",
                                ephemeral=True
                            )
                        else:
                            await cursor.execute("SELECT Search from Admin Where Identifier = 'UBB_Gold_Pouch'")
                            item_id = await cursor.fetchone()
                            item = await ubb_inventory_check(guild_id, interaction.user.id, int(item_id[0]), 1)
                            if item <= 0:
                                await interaction.followup.send(
                                    f"Insufficient Gold Pouches to apply to {character_name}.",
                                    ephemeral=True
                                )
                            else:
                                gold_result = gold_calculation(cursor, character_name, level, gold, gold_value,
                                                               gold_value_max, gold_pouch - gold_value_max)
                                if gold_result[0] <= gold or gold_result[1] <= gold_value:
                                    await interaction.followup.send(
                                        f"Your oaths foreswear further reward of gold!",
                                        ephemeral=True
                                    )
                                else:
                                    client = unbelievaboat.Client(os.getenv('UBB_TOKEN'))
                                    await client.delete_inventory_item(guild_id, author_id, item_id[0], 1)
                                    character_embed = await shared_functions.character_embed(cursor, character_name,
                                                                                             guild)
                                    character_changes = shared_functions.CharacterChange(character_name=character_name,
                                                                                         author=author,
                                                                                         source=f'Pouch with transaction id of {gold_result[3]}',
                                                                                         gold_change=gold_result[
                                                                                                         0] - gold,
                                                                                         gold_value=gold_result[1],
                                                                                         gold_value_max=gold_result[2])
                                    character_log = await shared_functions.log_embed(character_changes, guild,
                                                                                     logging_thread_id, self.bot)
                                    await interaction.followup.send(embed=character_log, ephemeral=True)
            except aiosqlite.Error as e:
                logging.exception(f"A SQLite error occurred in the pouch command for: '{character_name}!: {e}")
                await interaction.followup.send(
                    f"A SQLite error occurred in the pouch command for: '{character_name}'. Error: {e}.",
                    ephemeral=True
                )
            except unbelievaboat.errors.HTTPError as e:
                logging.exception(f"An error occurred contacting unbelievabot API! check {item_id}!: {e}")
                await interaction.followup.send(
                    f"An error occurred contacting unbelievabot API! check {item_id}!: Error: {e}.",
                    ephemeral=True
                )

    @app_commands.command(name='entitle', description='give a special title to a character')
    @app_commands.autocomplete(title=shared_functions.title_lookup)
    @app_commands.choices(usage=[discord.app_commands.Choice(name='Display', value=1),
                                 discord.app_commands.Choice(name='Apply Masculine Title', value=2),
                                 discord.app_commands.Choice(name='Apply Feminine Title', value=3),
                                 discord.app_commands.Choice(name='Change Gender', value=4)])
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def entitle(self, interaction: discord.Interaction, character_name: str, title: str,
                      usage: discord.app_commands.Choice[int]):
        guild_id = interaction.guild_id
        guild = interaction.guild
        author = interaction.user.name
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute("SELECT COUNT(masculine_name) FROM Store_Title")
                admin_count = await cursor.fetchone()
                max_page = math.ceil(admin_count[0] / 20)
                current_page = max_page if current_page > max_page else current_page
                low = 1 + ((current_page - 1) * 20)
                high = 20 + ((current_page - 1) * 20)
                statement = "SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN ? and ?"
                view = ShopView(cursor, character_name, interaction.user.id, guild_id, low, high, statement,
                                display_type)
                await interaction.followup.send(content='Counting!: 0!', view=view)
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(f"An error occurred in the retire command whilst looking for '{character_name}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst looking for '{character_name}'. Error: {e}.",
                    ephemeral=True
                )


"""

@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
@app_commands.autocomplete(title=title_lookup)
@app_commands.choices(usage=[discord.app_commands.Choice(name='Display', value=1),
                             discord.app_commands.Choice(name='Apply Masculine Title', value=2),
                             discord.app_commands.Choice(name='Apply Feminine Title', value=3),
                             discord.app_commands.Choice(name='Change Gender', value=4)])
async def entitle(interaction: discord.Interaction, character_name: str, title: str, usage: discord.app_commands.Choice[int]):
    "Apply a title to yourself! This defaults to display the available titles."
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = interaction.guild_id
    author = interaction.user.name
    guild = interaction.guild
    usage = 1 if usage == 1 else usage.value
    client = Client(os.getenv('UBB_TOKEN'))
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    print(type(title), title)
    cursor.execute(
        f"SELECT ID, Fame, Masculine_Name, Feminine_Name from Store_Title Where Masculine_name = ? or Feminine_name = ?",
        (title, title))
    item_id = cursor.fetchone()
    if usage != 1 and usage != 4 and item_id is not None:
        try:
            title_name = item_id[2] if usage == 2 else item_id[3]
            inventory = await client.get_inventory_item(guild_id, author_id, item_id[0])
            if inventory is not None:
                cursor.execute(
                    f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND  Nickname = ?",
                    (author, character_name, author, character_name))
                player_info = cursor.fetchone()
                if player_info is not None:
                    true_character_name = player_info[3]
                    cursor.execute(
                        f"SELECT Fame, Masculine_Name, Feminine_Name from Store_Title where Masculine_Name = ? or Feminine_Name = ?",
                        (player_info[27], player_info[27]))
                    title_information = cursor.fetchone()
                    title_fame = 0 if title_information is None else title_information[0]
                    if item_id[1] <= title_fame:
                        await interaction.response.send_message(
                            f'Unlike a repo-man, you do not need to collect titles. You already have the title {title_information[1]}')
                    else:
                        title_fame = item_id[1] - title_fame
                        await EventCommand.title_change(self, guild_id, author, author_id, true_character_name,
                                                        title_name, player_info[27] + title_fame,
                                                        player_info[30] + title_fame,
                                                        f'Became the title of {title_name}', 'Used entitle!')
                        cursor.execute("Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                        accepted_bio_channel = cursor.fetchone()
                        bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4],
                                                    player_info[5], player_info[6], player_info[7], player_info[8],
                                                    player_info[9], player_info[10], player_info[11], player_info[12],
                                                    player_info[13], player_info[14], player_info[16], player_info[17],
                                                    player_info[18], player_info[19], player_info[20], player_info[21],
                                                    player_info[22], player_info[23], player_info[27], title_name,
                                                    player_info[30], player_info[31])
                        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                        bio_message = await bio_channel.fetch_message(player_info[24])
                        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                        logging_embed = discord.Embed(
                            title=f"{true_character_name} has changed their title to {title_name}",
                            description=f"{author} has changed their title to {title_name} using {title_fame} fame from the shop.",
                            colour=discord.Colour.blurple())
                        logging_thread = guild.get_thread(player_info[25])
                        await logging_thread.send(embed=logging_embed)
                        await interaction.response.send_message(
                            content=f"you have changed your title to {title_name} and increased your fame by {title_fame} by using an item from shop for the character named {character_name}.",
                            ephemeral=True)
                        await client.delete_inventory_item(guild_id, author_id, item_id[0], 1)
                else:
                    await interaction.response.send_message(
                        f"{author} does not have a {character_name} registered under this character name or nickname.")
        except unbelievaboat.errors.HTTPError:
            await interaction.response.send_message(f"{author} does not have any {title_name} in their inventory.")
        await client.close()
    elif usage == 4:
        cursor.execute(
            f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND  Nickname = ?",
            (author, character_name, author, character_name))
        player_info = cursor.fetchone()
        if player_info is not None:
            true_character_name = player_info[3]
            cursor.execute(
                f"SELECT Fame, Title, Masculine_Name, Feminine_Name from Store_Title where Masculine_Name = ? or Feminine_Name = ?",
                (player_info[27], player_info[27]))
            title_information = cursor.fetchone()
            if title_information is not None:
                title_name = title_information[2] if player_info[27] != title_information[2] else title_information[3]
                await EventCommand.title_change(self, guild_id, author, author_id, true_character_name, title_name,
                                                player_info[27], f'Became the title of {title_name}', 'Used entitle!')
                cursor.execute("Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4],
                                            player_info[5], player_info[6], player_info[7], player_info[8],
                                            player_info[9], player_info[10], player_info[11], player_info[12],
                                            player_info[13], player_info[14], player_info[16], player_info[17],
                                            player_info[18], player_info[19], player_info[20], player_info[21],
                                            player_info[22], player_info[23], player_info[27], title_name,
                                            player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                logging_embed = discord.Embed(title=f"{true_character_name} has changed their title to {title_name}",
                                              description=f"{author} has changed their title to {title_name} using {title} from the shop.",
                                              colour=discord.Colour.blurple())
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await interaction.response.send_message(
                    content=f"you have changed your title to {title_name} for {character_name}.", ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"{author} does not have a title registered under this character name or nickname.")
        else:
            await interaction.response.send_message(
                f"{author} does not have a {character_name} registered under this character name or nickname.")
    else:
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        cursor.execute("SELECT COUNT(masculine_name) FROM Store_Title")
        admin_count = cursor.fetchone()
        max_page = math.ceil(admin_count[0] / 20)
        current_page = 1
        low = 1 + ((current_page - 1) * 20)
        high = 20 + ((current_page - 1) * 20)
        cursor.execute(
            f"SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"Title Store Settings Page {current_page}",
                              description=f'This is a list of available titles', colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f"Title Store Item: {result[3]}/{result[4]}",
                            value=f'**Effect**: {result[1]}, **Rewarded Fame**: {result[2]}', inline=False)
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
                    await msg.remove_reaction(button, interaction.user)
                if current_page != previous_page:
                    cursor.execute(
                        f"SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}")
                    pull = cursor.fetchall()
                    embed = discord.Embed(title=f"Title Store Settings Page {current_page}",
                                          description=f'This is a list of available titles',
                                          colour=discord.Colour.blurple())
                    for result in pull:
                        embed.add_field(name=f"Title Store Item: {result[3]}/{result[4]}",
                                        value=f'**Effect**: {result[1]}, **Rewarded Fame**: {result[2]}', inline=False)
                    await msg.edit(embed=embed)
    cursor.close()
    db.close()


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
@app_commands.autocomplete(name=fame_lookup)
@app_commands.choices(
    modify=[discord.app_commands.Choice(name='Display', value=1), discord.app_commands.Choice(name='use', value=2)])
async def proposition(interaction: discord.Interaction, character_name: typing.Optional[str], name: typing.Optional[str],
                      approver: typing.Optional[discord.Member], modify: discord.app_commands.Choice[int] = 1):
    "Proposition NPCs for Favors using your prestige!."
    character_name = None if character_name is None else str.replace(
        str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = interaction.guild_id
    author = interaction.user.name
    guild = interaction.guild
    modify = 1 if modify == 1 else modify.value
    character_name = character_name if character_name is not None else "N/A"
    name = name if name is not None else "N/A"
    approver = approver if approver is not None else "N/A"
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute("SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame Where name = ?",
                   (name,))
    item_id = cursor.fetchone()
    if modify == 2 and approver != "N/A" and item_id is not None:
        cursor.execute(
            f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND  Nickname = ?",
            (author, character_name, author, character_name))
        player_info = cursor.fetchone()
        if player_info is not None:
            true_character_name = player_info[3]
            cursor.execute(
                f"SELECT Count(Item_name) from A_Audit_Prestige where Author_ID = ? and Character_Name = ? and Item_Name = ? and IsAllowed = ?",
                (author_id, character_name, name, 1))
            title_information = cursor.fetchone()
            if title_information[0] < item_id[4] and player_info[27] >= item_id[0] and player_info[30] >= item_id[1]:
                await EventCommand.proposition_open(self, guild_id, author, author_id, player_info[3], item_id[2],
                                                    item_id[1], 'Attempting to open a proposition', 'Proposition Open!')
                cursor.execute("Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute("Select MAX(Transaction_ID) FROM A_Audit_Prestige WHERE Character_Name = ?",
                               (character_name,))
                proposition_id = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4],
                                            player_info[5], player_info[6], player_info[7], player_info[8],
                                            player_info[9], player_info[10], player_info[11], player_info[12],
                                            player_info[13], player_info[14], player_info[16], player_info[17],
                                            player_info[18], player_info[19], player_info[20], player_info[21],
                                            player_info[22], player_info[23], player_info[27], player_info[28],
                                            player_info[30] - item_id[1], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                logging_embed = discord.Embed(
                    title=f"{true_character_name} has opened the following proposition of propositioned {name} ID: {proposition_id[0]}",
                    description=f"{author} is attempting to use {item_id[1]} prestige to obtain the following effect of: \r\n {item_id[3]}.",
                    colour=discord.Colour.blurple())
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await interaction.response.send_message(
                    content=f"<@{approver.id}>, {player_info[2]} is attempting to proposition for {name}, with ID of {proposition_id[0]} do you accept? \r\n use the /Gamemaster Proposition command to reject or deny this request using the Proposition ID!",
                    allowed_mentions=discord.AllowedMentions(users=True))
            elif title_information[0] >= item_id[4]:
                await interaction.response.send_message(f"{author} has met the limit for usage of this proposition.")
            elif player_info[27] < item_id[0]:
                await interaction.response.send_message(f"{author} does not have enough fame to use this proposition.")
            else:
                await interaction.response.send_message(f"{author} does not have enough prestige to use this proposition.")
        else:
            await interaction.response.send_message(
                f"{author} does not have a {character_name} registered under this character name or nickname.")
    elif modify == 2 and approver != "N/A" and item_id is None:
        await interaction.response.send_message(f"{name} is not an available proposition.")
    elif modify == 2 and approver == "N/A":
        await interaction.response.send_message(f"Please mention the approver of this proposition.")
    else:
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        cursor.execute("SELECT COUNT(Name) FROM Store_Fame")
        admin_count = cursor.fetchone()
        max_page = math.ceil(admin_count[0] / 20)
        current_page = 1
        low = 1 + ((current_page - 1) * 20)
        high = 20 + ((current_page - 1) * 20)
        cursor.execute(
            f"SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"Fame Store Settings Page {current_page}",
                              description=f'This is a list of the administratively defined items',
                              colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f'**Name**: {result[2]}',
                            value=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}',
                            inline=False)
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
                    await msg.remove_reaction(button, interaction.user)
                if current_page != previous_page:
                    cursor.execute(
                        f"SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}")
                    pull = cursor.fetchall()
                    embed = discord.Embed(title=f"Fame Store Settings Page {current_page}",
                                          description=f'This is a list of the administratively defined items',
                                          colour=discord.Colour.blurple())
                    for result in pull:
                        embed.add_field(name=f'**Name**: {result[2]}',
                                        value=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}',
                                        inline=False)
                    await msg.edit(embed=embed)
                    cursor.close()
    db.close()


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def cap(interaction: discord.Interaction, character_name: str, level_cap: int):
    "THIS COMMAND DISPLAYS CHARACTER INFORMATION"
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    author = interaction.user.name
    guild_id = interaction.guild_id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(
        f"SELECT Character_Name FROM Player_Characters where Player_Name = ? and Character_Name = ? or  Player_Name = ? AND Nickname = ?",
        (author, character_name, author, character_name))
    character_info = cursor.fetchone()
    if character_info is not None:
        await EventCommand.adjust_personal_cap(self, guild_id, author, character_name, level_cap)
        await interaction.response.send_message(f"{author} has adjusted the personal cap of {character_name} to {level_cap}.",
                                        ephemeral=True)
        cursor.execute(
            f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Nickname = ?",
            (author, character_name, character_name))
        player_info = cursor.fetchone()
        cursor.execute("Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
        accepted_bio_channel = cursor.fetchone()
        cursor.execute("Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
        character_log_channel_id = cursor.fetchone()
        bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5],
                                    player_info[6], player_info[7], player_info[8], player_info[9], player_info[10],
                                    player_info[11], player_info[12], player_info[13], player_info[14], player_info[16],
                                    player_info[17], player_info[18], player_info[19], player_info[20], player_info[21],
                                    player_info[22], player_info[23], player_info[27], player_info[28], player_info[30],
                                    player_info[31])
        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
        bio_message = await bio_channel.fetch_message(player_info[24])
        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
        logging_embed = discord.Embed(title=f"{character_name} has had their maximum level cap set to {level_cap}!",
                                      description=f"This character can no longer level up past this point until changed!",
                                      colour=discord.Colour.blurple())
        logging_thread = guild.get_thread(player_info[25])
        await logging_thread.send(embed=logging_embed)
    else:
        await interaction.response.send_message(
            f"{author} does not have a {character_name} registered under this character name or nickname.")
    cursor.close()
    db.close()


@character.command()
@app_commands.autocomplete(character_name=character_select_autocompletion)
async def display(interaction: discord.Interaction, player_name: typing.Optional[discord.Member], character_name: str = 'All',
                  current_page: int = 1):
    "THIS COMMAND DISPLAYS CHARACTER INFORMATION"
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    if player_name is not None:
        player_name = player_name.name
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if player_name == 'NA':
        player_name = interaction.user.name
    if character_name == 'All':
        cursor.execute("SELECT COUNT(Character_Name) FROM Player_Characters where Player_Name = '{player_name}'")
        character_count = cursor.fetchone()
        if character_count is None:
            cursor.close()
            db.close()
            interaction.response.send_message(f"{player_name} was not a valid player to obtain the characters of!")
            return
        max_page = math.ceil(character_count[0] / 5)
        if current_page >= max_page:
            current_page = max_page
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        low = 0 + (5 * (current_page - 1))
        offset = 5
        cursor.execute(
            f"Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Mythweavers from Player_characters WHERE player_name = '{player_name}' LIMIT {low}, {offset}")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"{player_name} character page {current_page}",
                              description=f"This is list of {player_name}'s characters",
                              colour=discord.Colour.blurple())
        x = 0
        for result in pull:
            x += 1
            number = ordinal(x)
            embed.add_field(name=f'{number} Character',
                            value=f'**Name**: [{result[0]}](<{result[13]}>) \r\n **Level**: {result[1]}, **Mythic Tier**: {result[2]}',
                            inline=False)
            linkage = f""
            if result[9] is not None:
                linkage += f"**Tradition**: [{result[9]}]({result[10]})"
            if result[11] is not None:
                if result[9] is not None:
                    linkage += f" "
                linkage += f"**Template**: [{result[11]}]({result[12]})"
            if result[9] is not None or result[11] is not None:
                embed.add_field(name=f'Additional Info', value=linkage, inline=False)
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
                    await msg.remove_reaction(button, interaction.user)
                if current_page != previous_page:
                    cursor.execute(
                        f"Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Mythweavers from Player_characters WHERE player = '{player_name}' LIMIT {low}, {offset}")
                    edit_pull = cursor.fetchall()
                    embed = discord.Embed(title=f"{player_name} character page {current_page}",
                                          description=f"This is list of {player_name}'s characters",
                                          colour=discord.Colour.blurple())
                    x = 0
                    for result in edit_pull:
                        x += 1
                        number = ordinal(x)
                        embed.add_field(name=f'{number} Character',
                                        value=f'**Name**: [{result[0]}](<{result[13]}>) \r\n **Level**: {result[1]}, **Mythic Tier**: {result[2]}',
                                        inline=False)
                        linkage = " "
                        if result[9] is not None:
                            linkage += f"**Tradition**: [{result[9]}]({result[10]})"
                        if result[11] is not None:
                            if result[9] is not None:
                                linkage += f" "
                            linkage += f"**Template**: [{result[11]}]({result[12]})"
                        if result[9] is not None or result[11] is not None:
                            embed.add_field(name=f'Additional Info', value=linkage, inline=False)
                    await interaction.response.send_message(embed=embed)
                    await msg.edit(embed=embed)
    elif character_name != 'All':
        sql = f"Select True_Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Gold_Value, Oath, Fame, Prestige, Title, Article_Link from Player_characters WHERE Character_Name = ? or Nickname = ?"
        val = (character_name, character_name)
        cursor.execute(sql, val)
        result = cursor.fetchone()
        if result is None:
            await interaction.response.send_message(f"{character_name} is not a valid Nickname or Character Name.")
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
            embed = discord.Embed(title="Mythweavers Sheet", url=f'{result[12]}', description=f"{description_field}",
                                  color=int_color)
            if result[23] is not None:
                author_field = f"{result[23]} {result[0]}"
            else:
                author_field = f"{result[0]}"
            embed.set_author(name=author_field)
            embed.set_thumbnail(url=f'{result[13]}')
            embed.add_field(name=f'Information',
                            value=f'**Level**: {result[4]}, **Mythic Tier**: {result[5]} **Fame**: {result[21]}, **Prestige**: {result[22]}',
                            inline=False)
            embed.add_field(name=f'Total Experience', value=f'**Milestones**: {result[6]}, **Remaining**:  {result[7]}')
            embed.add_field(name=f'Mythic', value=f'**Trials**: {result[8]}, **Remaining**: {result[9]}')
            embed.add_field(name="\u200B", value="\u200B")
            embed.add_field(name=f'Current Wealth', value=f'**GP**: {round(result[10], 2)}')
            embed.add_field(name=f'Effective Wealth', value=f'**GP**: {round(result[19], 2)}')
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
            await interaction.response.send_message(embed=embed)
    cursor.close()
    db.close()


@character.command()
@app_commands.describe(
    level_range="the level range of the characters you are looking for. Keep in mind, this applies only to the preset low/med/high/max ranges your admin has set")
async def list(interaction: discord.Interaction, level_range: discord.Role, current_page: int = 1):
    "THIS COMMAND DISPLAYS CHARACTER INFORMATION"
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute("SELECT Level FROM Level_Range WHERE Role_ID = {level_range.id} order by Level asc limit 1")
    level_range_min = cursor.fetchone()
    cursor.execute("SELECT Level FROM Level_Range WHERE Role_ID = {level_range.id} order by Level desc limit 1")
    level_range_max = cursor.fetchone()
    if level_range_min is None:
        cursor.close()
        db.close()
        interaction.response.send_message(f"{level_range.name} was not a valid role to select", ephemeral=True)
        return
    cursor.execute(
        f"SELECT COUNT(Character_Name) FROM Player_Characters where level >= {level_range_min[0]} and level <= {level_range_max[0]}")
    character_count = cursor.fetchone()
    if character_count[0] != 0:
        max_page = math.ceil(character_count[0] / 5)
        if current_page >= max_page:
            current_page = max_page
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        low = 0 + (5 * (current_page - 1))
        offset = 5
        cursor.execute(
            f"Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link from Player_characters WHERE level >= {level_range_min[0]} and level <= {level_range_max[0]} LIMIT {low}, {offset}")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"{level_range.name} character page {current_page}",
                              description=f"This is list of characters in {level_range.name}",
                              colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f'Character Name', value=f'**Name**:{result[0]}', inline=False)
            embed.add_field(name=f'Information', value=f'**Level**: {result[1]}, **Mythic Tier**: {result[2]}',
                            inline=False)
            embed.add_field(name=f'Total Experience',
                            value=f'**Milestones**: {result[3]}, **Milestones Remaining**: {result[4]}, **Trials**: {result[5]}, **Trials Remaining**: {result[6]}',
                            inline=False)
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
                    await msg.remove_reaction(button, interaction.user)
                if current_page != previous_page:
                    cursor.execute(
                        f"Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link from Player_characters WHERE level >= {level_range_min[0]} and level <= {level_range_max[0]} LIMIT {low}, {offset}")
                    edit_pull = cursor.fetchall()
                    embed = discord.Embed(title=f"{level_range.name} character page {current_page}",
                                          description=f"This is list of characters in {level_range.name}",
                                          colour=discord.Colour.blurple())
                    for result in edit_pull:
                        embed.add_field(name=f'Character Name', value=f'**Name**:{result[0]}', inline=False)
                        embed.add_field(name=f'Information',
                                        value=f'**Level**: {result[1]}, **Mythic Tier**: {result[2]}', inline=False)
                        embed.add_field(name=f'Total Experience',
                                        value=f'**Milestones**: {result[3]}, **Milestones Remaining**: {result[4]}, **Trials**: {result[5]}, **Trials Remaining**: {result[6]}',
                                        inline=False)
                        embed.add_field(name=f'Current Wealth', value=f'**GP**: {result[7]}, **Flux**: {result[8]}',
                                        inline=False)
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
        await interaction.response.send_message(f"{level_range.name} does not have any characters within this level range.",
                                        ephemeral=True)


@character.command()
@app_commands.choices(
    modify=[discord.app_commands.Choice(name='Create', value=1), discord.app_commands.Choice(name='Edit', value=2)])
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def backstory(interaction: discord.Interaction, character_name: str, backstory: str,
                    modify: discord.app_commands.Choice[int] = 1):
    "THIS COMMAND CREATES OR CHANGES THE BACKSTORY ASSOCIATED WITH YOUR CHARACTER"
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    author = interaction.user.name
    guild_id = interaction.guild_id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(
        f"SELECT Character_Name, Article_ID, Mythweavers FROM Player_Characters where Player_Name = ? and Character_Name = ? or  Player_Name = ? AND Nickname = ?",
        (author, character_name, author, character_name))
    character_info = cursor.fetchone()
    if character_info is not None:
        if modify == 1:
            if character_info[1] is not None:
                await interaction.response.send_message(
                    f"{author} already has a backstory associated with {character_name}. If you wish to edit it, use the Edit Option of this command",
                    ephemeral=True)
            else:
                await EventCommand.create_bio(self, guild_id, character_info[0], backstory, character_info[2])
                cursor.execute("Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute("Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
                cursor.execute(
                    f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?",
                    (author, character_name, author, character_name))
                player_info = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4],
                                            player_info[5], player_info[6], player_info[7], player_info[8],
                                            player_info[9], player_info[10], player_info[11], player_info[12],
                                            player_info[13], player_info[14], player_info[16], player_info[17],
                                            player_info[18], player_info[19], player_info[20], player_info[21],
                                            player_info[22], player_info[23], player_info[27], player_info[28],
                                            player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                logging_embed = discord.Embed(title=f"{character_name} has had their backstory created!",
                                              description=f"{author} has created the following [backstory](<{player_info[31]}>)",
                                              colour=discord.Colour.blurple())
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await interaction.response.send_message(f"{author} has created a backstory for {character_name}.",
                                                ephemeral=True)
        else:
            if character_info[1] is None:
                await interaction.response.send_message(
                    f"{author} does not have a backstory associated with {character_name}. If you wish to create one, use the Create Option of this command",
                    ephemeral=True)
            else:
                await EventCommand.edit_bio(self, guild_id, character_info[0], backstory, character_info[1])
                cursor.execute("Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute("Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
                cursor.execute(
                    f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?",
                    (author, character_name, author, character_name))
                player_info = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4],
                                            player_info[5], player_info[6], player_info[7], player_info[8],
                                            player_info[9], player_info[10], player_info[11], player_info[12],
                                            player_info[13], player_info[14], player_info[16], player_info[17],
                                            player_info[18], player_info[19], player_info[20], player_info[21],
                                            player_info[22], player_info[23], player_info[27], player_info[28],
                                            player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                logging_embed = discord.Embed(title=f"{character_name} has had their backstory edited!",
                                              description=f"{author} has edited the following backstory: \r\n {backstory}",
                                              colour=discord.Colour.blurple())
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await interaction.response.send_message(f"{author} has edited the backstory for {character_name}.",
                                                ephemeral=True)
    else:
        cursor.execute(
            f"SELECT Character_Name FROM A_STG_Player_Characters where Player_Name = ? and Character_Name = ? or  Player_Name = ? AND Nickname = ?",
            (author, character_name, author, character_name))
        character_info = cursor.fetchone()
        if character_info is not None:
            await EventCommand.edit_stage_bio(self, guild_id, character_info[0], backstory)
        else:
            await interaction.response.send_message(
                f"{author} does not have a {character_name} registered under this character name or nickname.",
                ephemeral=True)

    cursor.close()
    db.close()
"""


# Modified RetirementView with character deletion
class RetirementView(discord.ui.View):
    """A view that allows a user to confirm or cancel the retirement of their character."""

    def __init__(self, character_name, user_id, guild_id):
        super().__init__(timeout=180)
        self.character_name = character_name
        self.user_id = user_id
        self.guild_id = guild_id
        self.message = None  # Will be set when the view is sent

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure that only the user who initiated the retirement can interact with the buttons."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You cannot interact with this button.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label='Confirm Retirement', style=discord.ButtonStyle.danger)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the confirmation of character retirement."""
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as conn:
            try:
                # Optional: Check if character exists before deletion
                sql_check = """
                    SELECT 1 FROM Player_Characters
                    WHERE Player_ID = ? AND (Character_Name = ? OR Nickname = ?)
                """
                row = await conn.execute_fetchone(sql_check,
                                                  (interaction.user.id, self.character_name, self.character_name))
                if not row:
                    await interaction.response.edit_message(
                        content="Character not found or already retired.",
                        view=None
                    )
                    return

                # Proceed with deletion
                sql_delete = """
                    DELETE FROM Player_Characters 
                    WHERE Player_ID = ? AND (Character_Name = ? OR Nickname = ?)
                """
                await conn.execute(sql_delete, (interaction.user.id, self.character_name, self.character_name))
                await conn.commit()
                await interaction.response.edit_message(
                    content="Character successfully retired and deleted from the database.",
                    view=None
                )
            except Exception as e:
                logging.exception(f"Failed to delete character '{self.character_name}': {e}")
                await interaction.followup.send(
                    "An unexpected error occurred while trying to retire your character. Please try again later or contact support.",
                    ephemeral=True
                )

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.secondary)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the cancellation of character retirement."""
        await interaction.response.edit_message(
            content="Character retirement cancelled.",
            view=None
        )

    async def on_timeout(self):
        """Disable buttons when the view times out."""
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException as e:
                logging.error(f"Failed to edit message on timeout: {e}")


class ShopView(discord.ui.View):
    """Base class for shop views with pagination."""
    def __init__(self, user_id, cursor, low, high):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.cursor = cursor
        self.low = low
        self.high = high
        self.results = []
        self.embed = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure that only the user who initiated the view can interact with the buttons."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You cannot interact with this button.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label='<', style=discord.ButtonStyle.danger)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle moving to the previous page."""
        if self.low > 1:
            self.high -= 20
            self.low -= 20
            await self.update_results()
            await self.create_embed()
            await interaction.response.edit_message(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.response.send_message("You are on the first page.", ephemeral=True)

    @discord.ui.button(label='>', style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle moving to the next page."""
        # Assume you have a method to check the max number of items
        max_items = await self.get_max_items()
        if self.high < max_items:
            self.high += 20
            self.low += 20
            await self.update_results()
            await self.create_embed()
            await interaction.response.edit_message(
                embed=self.embed,
                view=self
            )
        else:
            await interaction.response.send_message("You are on the last page.", ephemeral=True)

    async def update_results(self):
        """Fetch the results for the current page. To be implemented in subclasses."""
        raise NotImplementedError

    async def create_embed(self):
        """Create the embed for the current page. To be implemented in subclasses."""
        raise NotImplementedError

    async def get_max_items(self):
        """Get the total number of items. To be implemented in subclasses."""
        raise NotImplementedError


class TitleShopView(ShopView):
    def __init__(self, user_id, cursor, low, high):
        super().__init__(user_id, cursor, low, high)

    async def update_results(self):
        """Fetch the title results for the current page."""
        statement = "SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title LIMIT ? OFFSET ?"
        await self.cursor.execute(statement, (20, self.low - 1))
        self.results = await self.cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        self.embed = discord.Embed(title="Titles", description="List of available titles")
        for title in self.results:
            self.embed.add_field(
                name=f"ID: {title[0]} - {title[3]} / {title[4]}",
                value=f"Effect: {title[1]}, Fame: {title[2]}",
                inline=False
            )

    async def get_max_items(self):
        """Get the total number of titles."""
        await self.cursor.execute("SELECT COUNT(*) FROM Store_Title")
        count = await self.cursor.fetchone()
        return count[0]


logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='application.log',  # Log to a file
    filemode='a'  # Append to the file
)
