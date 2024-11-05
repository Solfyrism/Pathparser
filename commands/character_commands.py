import logging
import typing
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

# *** GLOBAL VARIABLES *** #
os.chdir("C:\\pathparser")


class CalculationAidFunctionError(Exception):
    pass


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
) -> Tuple[int, int, int, int, int, int]:
    """
    Calculates the new level and milestone requirements for a character.
    ...

    Returns:
    - Tuple[int, int, int, int]: New level, minimum milestones, milestones to level, milestones required.
    - int: Returns -1 in case of an error.
    """
    try:
        logging.debug(f"Connected to database for guild {guild_id}")

        # Get maximum level cap
        max_level = await get_max_level(cursor, guild_id)
        if max_level is None:
            logging.error(f"Max level cap not found for guild {guild_id}")
            raise CalculationAidFunctionError(f"Max level cap not found for guild {guild_id}")

        logging.debug(f"Max level cap for guild {guild_id} is {max_level}")

        # Get milestone information
        await cursor.execute(
            "SELECT easy, medium, hard, deadly FROM AA_Milestones WHERE level = ?",
            (level,)
        )

        milestone_information = await cursor.fetchone()
        if milestone_information is None:
            logging.error(f"Milestone information not found for level {level}")
            raise CalculationAidFunctionError(f"Milestone information not found for level {level}")
        logging.debug(f"Milestone information for level {level}: {milestone_information}")

        # Calculate milestones
        multipliers = [easy, medium, hard, deadly]
        awarded_milestone_total = calculate_milestones(milestone_information, multipliers, misc)
        logging.debug(f"Calculated awarded milestone total: {awarded_milestone_total}")

        # Determine maximum level
        maximum_level = min(max_level, personal_cap)
        logging.debug(f"Maximum level for character '{character_name}': {maximum_level}")

        # Get new level information
        total_milestones = base + awarded_milestone_total
        new_level_info = await get_new_level_info(cursor, total_milestones, maximum_level)
        if new_level_info is None:
            raise CalculationAidFunctionError(
                f"Error in level calculation for character '{character_name}': No level information found")
        new_level, min_milestones, milestones_to_level = new_level_info
        logging.debug(
            f"New level information: Level={new_level}, "
            f"Minimum_Milestones={min_milestones}, Milestones_to_level={milestones_to_level}"
        )

        # Update player character
        milestones_required = min_milestones + milestones_to_level - total_milestones
        logging.info(
            f"Updated character '{character_name}': Level={new_level}, "
            f"Milestones={total_milestones}, Milestones_Required={milestones_required}"
        )
        await level_ranges(cursor, guild, author_id, level, new_level)
        return_value = (
            new_level,
            total_milestones,
            min_milestones,
            milestones_to_level,
            milestones_required,
            awarded_milestone_total)
        return return_value
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error in level calculation for character '{character_name}': {e}")
        raise CalculationAidFunctionError(f"Error in level calculation for character '{character_name}': {e}")


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


async def mythic_calculation(cursor, character_name, level, trials, trial_change) -> Tuple[int, int, int, int]:
    try:
        logging.info(
            f"Calculating mythic for character '{character_name}', level {level}, trials {trials}, trial_change {trial_change}")
        # Call limiters and restrictions.
        trial_total = trials + trial_change
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
        tier_max = floor(level / tier_rate_limit_modifier) if floor(level / tier_rate_limit_modifier) <= max_mythic[
            0] else max_mythic[0]
        # Call the mythic tier information.
        await cursor.execute(
            "SELECT Tier, Trials, Trials_Required from AA_Mythic  WHERE Trials <= ? AND Tier <= ? ORDER BY Trials DESC  LIMIT 1",
            (trial_total, tier_max))
        new_mythic_information = await cursor.fetchone()
        (tier, trials_minimum, trials_required) = new_mythic_information
        trials_remaining = trials_minimum + trials_required - trial_change - trials

        # return mythic tier, trials, and mythic trials remaining.
        return_value = (
            tier,
            trial_total,
            trials_remaining,
            trial_change)
        return return_value
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error in mythic calculation for {character_name} with error: {e}")
        raise CalculationAidFunctionError(f"Error in mythic calculation for {character_name} with error: {e}")


async def gold_calculation(
        guild_id: int,
        author_name: str,
        author_id: int,
        character_name: str,
        level: int,
        oath: str,
        gold: float,
        gold_value: float,
        gold_value_max: float,
        gold_change: float,
        gold_value_change: float,
        gold_value_max_change: float,
        source: str,
        reason: str
) -> Union[Tuple[int, int, int, int], int, str]:
    time = datetime.datetime.now()
    try:
        if gold_change > 0:
            gold_value += gold_value_change
            gold_value_max_total = gold_value_max + gold_value_max_change
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
            gold_value_total = gold_value + difference + gold_value_change
            gold_value_max_total = gold_value_max + gold_value_max_change
        # Ensure gold values are not negative
        if gold_total < 0 or gold_value_total < 0:
            return_value = "Gold cannot be negative."
            return return_value
        else:
            async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
                cursor = await conn.cursor()
                # Update the database
                sql = "INSERT INTO A_Audit_Gold(Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time) VALUES(?, ?, ?, cast(? as numeric(16,2)), cast(? as numeric(16,2)), cast(? as numeric(16,2)), ?, ?, ?)"
                val = (
                    author_name, author_id, character_name,
                    difference,
                    gold_value_change + difference,
                    gold_change + gold_value_max_change, reason, source, time)
                await cursor.execute(sql, val)
                await conn.commit()
                await cursor.execute("SELECT Max(transaction_id) FROM A_Audit_Gold")
                transaction_id = await cursor.fetchone()
                logging.info(f"Gold updated for character '{character_name}', transaction_id: {transaction_id[0]}.")
                return_value = (
                    difference,
                    gold_total,
                    gold_value_total,
                    gold_value_max_total,
                    transaction_id[0])
                return return_value
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error in gold calculation for character '{character_name}': {e}")
        raise CalculationAidFunctionError(f"Error in gold calculation for character '{character_name}': {e}")


def essence_calculation(character_name: str, essence: int, essence_change: int,
                        accepted_date: typing.Optional[str]):
    try:
        if accepted_date is not None:
            start_date = datetime.datetime.strptime(accepted_date, '%Y-%m-%d %H:%M')
            current_date = datetime.datetime.now()
            date_difference = (current_date - start_date).days
            if 90 <= date_difference < 120:
                essence_multiplier = 2
            elif date_difference >= 120:
                essence_multiplier = 2 + floor((date_difference - 90) / 30)
                essence_multiplier = essence_multiplier if essence_multiplier <= 4 else 4
            else:
                essence_multiplier = 1
            essence_change *= essence_multiplier
        logging.info(f"Calculating essence for character '{character_name}'")
        essence_total = essence + essence_change
        return_value = essence_total, essence_change
        return return_value
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(f"Error in essence calculation for {character_name} with error: {e}")
        raise CalculationAidFunctionError(f"Error in essence calculation for {character_name} with error: {e}")


async def ubb_inventory_check(guild_id: int, author_id: int, item_id: int, amount: int) -> int:
    client = unbelievaboat.Client(os.getenv('UBB_TOKEN'))
    try:
        logging.info(f"Retrieving inventory item {item_id} for user {author_id}")
        inventory = await client.get_inventory_item(guild_id, author_id, item_id[0])
        inventory_remaining = inventory.quantity
        amount = min(amount, inventory_remaining)
        return amount
    except unbelievaboat.errors.HTTPError:
        logging.exception(f"Failed to retrieve inventory item {item_id[0]} for user {author_id}")
        return 0


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
class CharacterCommands(commands.Cog, name='character'):
    def __init__(self, bot):
        self.bot = bot

    character_group = discord.app_commands.Group(
        name='character',
        description='Commands related to characters'
    )

    @character_group.command(name='help', description='Help commands for the character tree')
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

    @character_group.command(name='register', description='register a character')
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
                            sql = "insert into A_STG_Player_Characters (Player_Name, Player_ID, Character_Name, True_Character_Name, Nickname, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Essence, Color, Mythweavers, Image_Link, Backstory, Date_Created) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
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
                await interaction.response.send_messagef(
                    "An error occurred whilst building character embed for '{character_name}' Error: {e}.",
                    ephemeral=True)

    @character_group.command(name='edit', description='edit your character')
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
                       "Gold, Gold_Value, Gold_Value_Max, Essence, Thread_ID, Fame, Title, "
                       "Personal_Cap, Prestige, Article_Link FROM Player_Characters "
                       "where Player_Name = ? AND Character_Name = ? OR Player_Name = ? AND  Nickname = ?")
                val = (author, name, author, name)
                await cursor.execute(sql, val)
                results = await cursor.fetchone()
                await interaction.response.defer(thinking=True, ephemeral=True)
                if results is None:
                    sql = "SELECT True_Character_Name, Nickname, Titles, Description, Mythweavers, Image_Link, Oath, Color, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Gold_Value, Gold_Value_Max, Essence, Character_Name from A_STG_Player_Characters where Player_Name = ? AND Character_Name = ? OR  Player_Name = ? AND Nickname = ?"
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
                                    gold_total = results[14] * 0.5
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
                                    "UPDATE Player_Characters SET Gold = CAST(? as numeric(16,2)), Gold_Value = CAST(? as numeric(16,2)), Gold_Value_Max = CAST(? as numeric(16,2)) WHERE Character_Name = ?",
                                    (gold_total, gold_value_total, gold_value_total_max,
                                     character_name)
                                )
                                await conn.commit()
                                sql = "INSERT INTO A_Audit_Gold(Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
                                val = (interaction.user.name, interaction.user.id, character_name, gold_total,
                                       gold_value_total, gold_value_max_total, 'Oaths were Changed',
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
                            char_embed = await character_embed(character_name=new_character_name, guild=guild)
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
                await interaction.response.send_message(
                    f"An error occurred whilst building character embed for '{character_name}' Error: {e}.",
                    ephemeral=True)

    @character_group.command(name='retire', description='retire a character')
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

    @character_group.command(name='levelup', description='level up your character')
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
                                character_updates = shared_functions.UpdateCharacter(
                                    level_package=(level, base, new_level_info[4]),
                                    character_name=character_name
                                )
                                if tier != mythic_results[0]:
                                    character_updates.mythic_package = (
                                        mythic_results[0], mythic_results[1], mythic_results[4])
                                await shared_functions.update_character(
                                    guild_id=guild_id,
                                    change=character_updates
                                )
                                character_embed = await shared_functions.character_embed(character_name=character_name,guild=guild)
                                character_changes = shared_functions.CharacterChange(
                                    character_name=character_name,
                                    author=author,
                                    source='Level Up',
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

    @character_group.command(name='trialup', description='Apply mythic tiers to your character')
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
                                    mythic_results = await mythic_calculation(cursor, character_name, level, total_trials, 1)
                                    (tier, total_trials, trials_remaining, trial_change) = mythic_results
                                client = unbelievaboat.Client(os.getenv('UBB_TOKEN'))
                                await client.delete_inventory_item(guild_id, author_id, item_id[0], used)
                                character_updates = shared_functions.UpdateCharacter(
                                    mythic_package=(tier, trials, trials_remaining),
                                    character_name=character_name
                                )
                                await shared_functions.update_character(
                                    guild_id=guild_id,
                                    change=character_updates
                                )
                                character_embed = await shared_functions.character_embed(character_name=character_name, guild=guild)
                                character_changes = shared_functions.CharacterChange(
                                    character_name=character_name,
                                    author=author,
                                    source='Trial Up!',
                                    tier=tier,
                                    trial_change=x,
                                    trials_remaining=trials_remaining,
                                    trials=trials)
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

    @character_group.command(name='pouch', description='Use a gold pouch to enrich your character')
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
                                gold_result = gold_calculation(
                                    guild_id=guild_id,
                                    character_name=character_name,
                                    author_name=author,
                                    author_id=author_id,
                                    level=level,
                                    oath=oath,
                                    gold=gold,
                                    gold_value=gold_value,
                                    gold_value_max=gold_value_max,
                                    gold_change=gold_pouch - gold_value_max,
                                    gold_value_change=float(0),
                                    gold_value_max_change=float(0),
                                    source='Gold Pouch',
                                    reason='Gold Pouch')
                                (calculated_difference, calculated_gold, calculated_gold_value,
                                 calculated_gold_value_max) = gold_result
                                if calculated_gold <= gold or calculated_gold_value <= gold_value:
                                    await interaction.followup.send(
                                        f"Your oaths foreswear further reward of gold!",
                                        ephemeral=True
                                    )
                                else:
                                    client = unbelievaboat.Client(os.getenv('UBB_TOKEN'))
                                    await client.delete_inventory_item(guild_id, author_id, item_id[0], 1)
                                    character_updates = shared_functions.UpdateCharacter(
                                        gold_package=(gold, gold_value, gold_value_max),
                                        character_name=character_name
                                    )
                                    await shared_functions.update_character(
                                        cursor=cursor,
                                        change=character_updates
                                    )
                                    character_embed = await shared_functions.character_embed(character_name=character_name,
                                                                                             guild=guild)
                                    character_changes = shared_functions.CharacterChange(
                                        character_name=character_name,
                                        author=author,
                                        source=f'Pouch with transaction id of {gold_result[3]}',
                                        gold_change=calculated_difference,
                                        gold=calculated_gold,
                                        effective_gold=calculated_gold_value)
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

    # Nested group
    entitle_group = discord.app_commands.Group(
        name='entitle',
        description='Event settings commands',
        parent=character_group
    )

    @entitle_group.command(name='display', description='Display titles from the store!')
    async def display_titles(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        guild = interaction.guild
        author = interaction.user.name
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                offset = 1
                limit = 20
                view = TitleShopView(interaction.user.id, guild_id, offset, limit)
                await view.update_results()
                await view.create_embed()
                await view.update_buttons()
                await interaction.followup.send(embed=view.embed, view=view)
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(f"An error occurred in the retire command whilst looking for '{character_name}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst looking for '{character_name}'. Error: {e}.",
                    ephemeral=True
                )

    @entitle_group.command(name='use', description='Use a title from the store!')
    @app_commands.autocomplete(title=shared_functions.title_lookup)
    @app_commands.choices(gender=[discord.app_commands.Choice(name='Masculine', value=1),
                                  discord.app_commands.Choice(name='Feminine', value=2)])
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def use(self, interaction: discord.Interaction, character_name: str, title: str,
                  gender: discord.app_commands.Choice[int]):
        guild_id = interaction.guild_id
        guild = interaction.guild
        author = interaction.user.name
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute(
                    "select True_character_name, title, fame, Logging_ID from Player_Characters where Player_Name = ? and (Character_Name = ? or Nickname = ?)",
                    (author, character_name, character_name))
                #               player validation to confirm if player is the owner of the character and they exist.
                player_info = await cursor.fetchone()
                if player_info is None:
                    await interaction.followup.send(
                        f"Character {character_name} not found.",
                        ephemeral=True
                    )
                else:  # Player found
                    (true_character_name, player_title, player_fame, logging_id) = player_info
                    await cursor.execute(
                        "SELECT ID, Fame, Masculine_Name, Feminine_Name from Store_Title where Masculine_name = ? or Feminine_name = ?",
                        (title, title))
                    title_information = await cursor.fetchone()  # Title validation
                    if title_information is None:
                        await interaction.followup.send(
                            f"Title {title} not found.",
                            ephemeral=True
                        )
                    else:  # Title Found
                        title_name = title_information[1] if gender.value == 1 else title_information[2]
                        title_fame = 0 if title_information is None else title_information[0]
                        if player_title is not None:
                            logging.info(
                                f"Player has a title {player_title}, validating if it is superior to the new title.")
                            await cursor.execute(
                                "SELECT ID, Fame, Masculine_Name, Feminine_Name from Store_Title where Masculine_name = ? or Feminine_name = ?",
                                (player_title, player_title))
                            previous_title_information = await cursor.fetchone()
                            if previous_title_information[1] >= title_fame:
                                await interaction.followup.send(
                                    f"{author} already has the superior title {previous_title_information[2]}",
                                    ephemeral=True
                                )
                                return
                            else:  # New Title is superior, remove fame from the older title.
                                title_fame -= previous_title_information[1]
                        ubb_validation = await ubb_inventory_check(guild_id,
                                                                   interaction.user.id,
                                                                   title_information[0],
                                                                   1)
                        if ubb_validation == 0:  # UBB Validation to ensure they have the title in their inventory.
                            await interaction.followup.send(
                                f"Insufficient titles to apply to {character_name}.",
                                ephemeral=True
                            )
                        else:  # Title is in inventory
                            await cursor.execute(
                                "UPDATE Player_Characters SET Title = ?, Fame = ? WHERE Character_Name = ?",
                                (title_name, player_fame + title_fame, character_name))
                            await conn.commit()
                            client = unbelievaboat.Client(os.getenv('UBB_TOKEN'))
                            await client.delete_inventory_item(guild_id, author_id, title_information[0])
                            character_bio = await shared_functions.character_embed(character_name=character_name, guild=guild)
                            character_changes = shared_functions.CharacterChange(character_name=character_name,
                                                                                 author=author,
                                                                                 source=f'Entitle applying the title of {title_name}',
                                                                                 fame=title_fame,
                                                                                 total_fame=player_fame + title_fame)
                            character_log = await shared_functions.log_embed(character_changes, guild,
                                                                             logging_thread_id, self.bot)
                            await interaction.followup.send(embed=character_log, ephemeral=True)
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(f"An error occurred in the retire command whilst looking for '{character_name}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst looking for '{character_name}'. Error: {e}.",
                    ephemeral=True
                )

    @entitle_group.command(name='swap', description='change the gender for your title!')
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def swap(self, interaction: discord.Interaction, character_name: str):
        guild_id = interaction.guild_id
        guild = interaction.guild
        author = interaction.user.name
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute(
                    'SELECT True_Character_Name, Title, Fame, Logging_ID FROM Player_Characters WHERE Player_Name = ? AND (Character_Name = ? OR Nickname = ?)',
                    (author, character_name, character_name))
                player_info = await cursor.fetchone()
                if player_info is None:
                    await interaction.followup.send(
                        f"Character {character_name} not found.",
                        ephemeral=True
                    )
                else:  # Character Found
                    (true_character_name, player_title, player_fame, logging_id) = player_info
                    if player_title is None:
                        await interaction.followup.send(
                            f"{author} does not have a title to swap.",
                            ephemeral=True
                        )
                    else:  # Character has title to swap
                        await cursor.execute(
                            "SELECT ID, Fame, Masculine_Name, Feminine_Name from Store_Title where Masculine_name = ? or Feminine_name = ?",
                            (player_title, player_title))
                        title_information = await cursor.fetchone()
                        if title_information is None:
                            logging.info(f'Title of {player_title} not found despite being assigned!')
                            await interaction.followup.send(
                                f"Title {player_title} not found.",
                                ephemeral=True
                            )
                        else:  # Title Found
                            title_name = title_information[2] if player_title == title_information[3] else \
                                title_information[3]
                            await cursor.execute(
                                "UPDATE Player_Characters SET Title = ?, Fame = ? WHERE Character_Name = ?",
                                (title_name, player_fame - title_fame, character_name))
                            await conn.commit()
                            character_bio = await shared_functions.character_embed(character_name=character_name, guild=guild)
                            character_changes = shared_functions.CharacterChange(character_name=character_name,
                                                                                 author=author,
                                                                                 source=f'Entitle swapping the gender of {player_title}',
                                                                                 total_fame=player_fame)
                            character_log = await shared_functions.log_embed(character_changes, guild,
                                                                             logging_thread_id, self.bot)
                            await interaction.followup.send(embed=character_log, ephemeral=True)
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"An error occurred in the retire command whilst looking for '{character_name}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst looking for '{character_name}'. Error: {e}.",
                    ephemeral=True
                )

                # Nested group

    prestige_group = discord.app_commands.Group(
        name='prestige',
        description='Event settings commands',
        parent=character_group
    )

    @prestige_group.command(name='display',
                            description='Display available options from the store.')
    async def display_prestige(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        guild = interaction.guild
        author = interaction.user.name
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                offset = 1
                limit = 20
                view = FameShopView(interaction.user.id, guild_id, offset, limit)
                await view.update_results()
                await view.create_embed()
                await view.update_buttons()
                await interaction.followup.send(embed=view.embed, view=view)
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(f"Couldn't display the store options: {e}")
                await interaction.followup.send(
                    f"An error occurred whilst displaying the store options. Error: {e}.")

    @prestige_group.command(
        name='request',
        description='Request something of a GM using your prestige as a resource.'
    )
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    @app_commands.autocomplete(name=shared_functions.fame_lookup)
    async def request(
            self,
            interaction: discord.Interaction,
            character_name: str,
            name: str,
            approver: discord.Member
    ):
        guild_id = interaction.guild_id
        author_id = interaction.user.id
        author_name = interaction.user.name

        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
                cursor = await conn.cursor()

                # Fetch player information
                await cursor.execute(
                    """
                    SELECT True_Character_Name, Character_Name, Fame, Prestige, Logging_Thread
                    FROM Player_Characters
                    WHERE Player_Name = ? AND (Character_Name = ? OR Nickname = ?)
                    """,
                    (author_name, character_name, character_name)
                )
                player_info = await cursor.fetchone()

                if player_info is None:
                    await interaction.followup.send(
                        f"{author_name} does not have a character named '{character_name}' registered.",
                        ephemeral=True
                    )
                    return

                (true_character_name, character_name, fame, prestige, logging_thread) = player_info

                # Fetch item information
                await cursor.execute(
                    """
                    SELECT Fame_Required, Prestige_Cost, Name, Use_Limit
                    FROM Store_Fame
                    WHERE Item_Name = ?
                    """,
                    (name,)
                )
                item_info = await cursor.fetchone()

                if item_info is None:
                    await interaction.followup.send(
                        f"The item '{name}' does not exist in the store.",
                        ephemeral=True
                    )
                    return

                (fame_required, prestige_cost, item_name, use_limit) = item_info

                # Check usage count
                await cursor.execute(
                    """
                    SELECT COUNT(Item_Name)
                    FROM A_Audit_Prestige
                    WHERE Author_ID = ? AND Character_Name = ? AND Item_Name = ? AND IsAllowed = 1
                    """,
                    (author_id, character_name, name)
                )
                usage_count_row = await cursor.fetchone()
                usage_count = usage_count_row[0] if usage_count_row else 0

                # Validate conditions
                if usage_count >= use_limit:
                    await interaction.followup.send(
                        f"{author_name} has reached the usage limit for this item.",
                        ephemeral=True
                    )
                    return

                if prestige < prestige_cost:
                    await interaction.followup.send(
                        f"{author_name} does not have enough prestige to use this item.",
                        ephemeral=True
                    )
                    return

                if fame < fame_required:
                    await interaction.followup.send(
                        f"{author_name} does not have enough fame to use this item.",
                        ephemeral=True
                    )
                    return

                # Insert proposition request
                await cursor.execute(
                    """
                    INSERT INTO A_Audit_Prestige
                    (Author_ID, Character_Name, Item_Name, Prestige_Cost, IsAllowed, Time)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (author_id, character_name, name, prestige_cost, 0, datetime.datetime.now())
                )
                await conn.commit()

                # Retrieve the proposition ID
                await cursor.execute(
                    "SELECT MAX(Transaction_ID) FROM A_Audit_Prestige WHERE Character_Name = ?",
                    (character_name,)
                )
                proposition_id_row = await cursor.fetchone()
                proposition_id = proposition_id_row[0] if proposition_id_row else None

                if proposition_id is None:
                    await interaction.followup.send(
                        "Failed to create the proposition request.",
                        ephemeral=True
                    )
                    return

                # Create and send the PropositionView
                view = PropositionView(
                    allowed_user_id=approver.id,
                    requester_name=author_name,
                    character_name=character_name,
                    item_name=name,
                    prestige_cost=prestige_cost,
                    proposition_id=proposition_id,
                    bot=self.bot,
                    prestige=prestige,
                    logging_thread=logging_thread
                )
                await view.create_embed()

                content = (
                    f"{approver.mention}, {author_name} is requesting '{name}' with proposition ID {proposition_id}.\n"
                    "Do you accept or reject this proposition?"
                )
                await interaction.followup.send(
                    content=content,
                    embed=view.embed,
                    view=view,
                    allowed_mentions=discord.AllowedMentions(users=True)
                )

        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(
                f"An error occurred in the 'request' command for '{character_name}': {e}"
            )
            await interaction.followup.send(
                f"An error occurred while processing your request: {e}",
                ephemeral=True
            )

    @prestige_group.command(
        name='history',
        description='View your proposition history.'
    )
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    @app_commands.autocomplete(name=shared_functions.fame_lookup)
    async def history(self, interaction: discord.Interaction, character_name: str, name: typing.Optional[str],
                      page_number: int = 1):
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)

        try:
            async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
                cursor = await conn.cursor()

                # Decide which query to execute based on whether 'name' is provided
                if name is not None:
                    await cursor.execute(
                        "SELECT COUNT(*) FROM A_Audit_Prestige WHERE Character_Name = ? AND Item_Name = ?",
                        (character_name, name)
                    )
                else:
                    await cursor.execute(
                        "SELECT COUNT(*) FROM A_Audit_Prestige WHERE Character_Name = ?",
                        (character_name,)
                    )

                count_row = await cursor.fetchone()
                proposition_count = count_row[0] if count_row else 0

                if proposition_count == 0:
                    await interaction.followup.send(
                        f"No propositions found for '{character_name}'.",
                        ephemeral=True
                    )
                    return

                # Set up pagination variables
                page_number = min(max(page_number, 1), math.ceil(proposition_count / 20))
                items_per_page = 20
                offset = (page_number - 1) * items_per_page

                # Create and send the view with the results
                view = PrestigeHistoryView(
                    user_id=interaction.user.id,
                    guild_id=guild_id,
                    character_name=character_name,
                    item_name=name,
                    limit=items_per_page,
                    offset=offset
                )
                await view.create_embed(results)
                await interaction.followup.send(embed=view.embed, view=view)

        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(
                f"An error occurred in the 'history' command while fetching data for '{character_name}': {e}"
            )
            await interaction.followup.send(
                f"An error occurred while fetching your proposition history. Please try again later.",
                ephemeral=True
            )

    @character_group.command(name='cap', description='Set the personal cap of a character')
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def cap(self, interaction: discord.Interaction, character_name: str, level_cap: int):
        """Set the personal level cap of a character."""
        try:
            # Clean and validate input
            character_name_cleaned = unidecode(str.title(character_name)).replace(";", "").replace(")", "")
            author_name = interaction.user.name
            author_id = interaction.user.id
            guild_id = interaction.guild_id
            guild = interaction.guild

            # Defer the response to allow for processing time
            await interaction.response.defer(thinking=True)

            # Validate level_cap input
            if not 1 <= level_cap <= 20:
                await interaction.followup.send(
                    f"Level cap must be between 1 and 20. You provided: {level_cap}",
                    ephemeral=True
                )
                return

            # Connect to the database
            async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
                cursor = await conn.cursor()

                # Fetch character information
                await cursor.execute(
                    """
                    SELECT Character_Name, Milestones, Level, Trials, Thread_ID
                    FROM Player_Characters
                    WHERE Player_Name = ? AND (Character_Name = ? OR Nickname = ?)
                    """,
                    (author_name, character_name_cleaned, character_name_cleaned)
                )
                character_info = await cursor.fetchone()

                if character_info is None:
                    await interaction.followup.send(
                        f"Character '{character_name}' not found.",
                        ephemeral=True
                    )
                    return

                (character_name_db, milestones, level, trials, thread_id) = character_info

                # Update the personal cap in the database
                await cursor.execute(
                    "UPDATE Player_Characters SET Personal_Cap = ? WHERE Character_Name = ?",
                    (level_cap, character_name_db)
                )
                await conn.commit()

                # Initialize character changes
                character_changes = shared_functions.CharacterChange(
                    character_name=character_name_db,
                    author=author_name,
                    source=f'Cap Adjustment to {level_cap}'
                )
                if level_cap < level:
                    # Perform level calculation
                    character_updates = shared_functions.UpdateCharacter(character_name=character_name_db)
                    try:
                        level_result = await level_calculation(
                            cursor=cursor,
                            guild=guild,
                            guild_id=guild_id,
                            author_id=author_id,
                            character_name=character_name_db,
                            personal_cap=level_cap,
                            level=level,
                            base=milestones,
                            easy=0,
                            medium=0,
                            hard=0,
                            deadly=0,
                            misc=0
                        )

                        # Check if level_result is a tuple
                        if isinstance(level_result, tuple):
                            (calculated_level,
                             calculated_total_milestones,
                             min_milestones,
                             calculated_remaining_milestones,
                             milestones_required,
                             awarded_milestone_total) = level_result
                            character_updates.level_package = (
                                calculated_level, calculated_total_milestones, calculated_remaining_milestones)
                            character_changes.level = calculated_level
                            character_changes.milestone_change = 0
                            character_changes.milestones_total = calculated_total_milestones
                            character_changes.milestones_remaining = calculated_remaining_milestones
                        else:
                            # Handle unexpected return type
                            character_changes.source += " Error adjusting level: Unexpected result from level calculation."
                            logging.error(f"Unexpected result from level_calculation: {level_result}")

                    except LevelCalculationError as e:
                        character_changes.source += f" Error adjusting level: {e}"
                        logging.exception(f"Level calculation error for character '{character_name_db}': {e}")
                    # Perform mythic calculation
                    try:
                        mythic_result = await mythic_calculation(
                            cursor=cursor,
                            character_name=character_name_db,
                            level=level,
                            trials=trials,
                            trial_change=0
                        )

                        if isinstance(mythic_result, tuple):
                            (tier, total_trials, trials_remaining, trial_change) = mythic_result
                            character_updates.mythic_package = (tier, total_trials, trials_remaining)
                            character_changes.tier = tier
                            character_changes.trials = total_trials
                            character_changes.trial_change = 0
                            character_changes.trials_remaining = trials_remaining
                        else:
                            # Handle unexpected return type
                            character_changes.source += " Error adjusting mythic: Unexpected result from mythic calculation."
                            logging.error(f"Unexpected result from mythic_calculation: {mythic_result}")

                    except CalculationAidFunctionError as e:
                        character_changes.source += f" Error adjusting mythic: {e}"
                        logging.exception(f"Mythic calculation error for character '{character_name_db}': {e}")

                    # update the character
                    await shared_functions.update_character(cursor=cursor, change=character_updates)
                # Create and send the log embed
                character_log = await shared_functions.log_embed(character_changes, guild, thread_id, self.bot)
                await interaction.followup.send(embed=character_log, ephemeral=True)

                # Create and send the character embed
                character_embed = await shared_functions.character_embed(character_name=character_name_db, guild=guild)
                await interaction.followup.send(embed=character_embed, ephemeral=True)

        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(f"An error occurred in the 'cap' command: {e}")
            await interaction.followup.send(
                "An unexpected error occurred while processing your request. Please try again later.",
                ephemeral=True
            )

    display_group = discord.app_commands.Group(
        name='display',
        description='level_range group commands',
        parent=character_group
    )

    @display_group.command(name='display',
                           description='display all character information or specific character information')
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    async def display_info(self, interaction: discord.Interaction, player_name: typing.Optional[discord.Member],
                           character_name: typing.Optional[str],
                           page_number: int = 1):
        """Display character information.
        Display A specific view when a specific character is provided,
        refine the list of characters when a specific player is provided."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)

        try:
            async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
                cursor = await conn.cursor()

                # Decide which query to execute based on whether 'name' is provided
                if not player_name:
                    await cursor.execute("SELECT COUNT(Character_Name) FROM Player_Characters")
                else:
                    await cursor.execute("SELECT COUNT(Character_Name) FROM Player_Characters WHERE Player_Name = ?",
                                         (player_name.name,))
                character_count = await cursor.fetchone()
                (character_count,) = character_count
                if character_name:
                    view_type = 2
                    await cursor.execute("SELECT character_name from Player_Characters where Character_Name = ?",
                                         (character_name,))
                    character = await cursor.fetchone()
                    if not character:
                        await interaction.followup.send(
                            f"Character '{character_name}' not found.",
                            ephemeral=True
                        )
                        return
                    else:
                        await cursor.execute(
                            "SELECT character_name from Player_Characters where Character_Name = ? ORDER BY True_Character_Name asc",
                            (character_name,))
                        results = await cursor.fetchall()
                        offset = results.index(character[0])
                else:
                    view_type = 1

                # Set up pagination variables
                page_number = min(max(page_number, 1), math.ceil(character_count / 20))
                items_per_page = 5 if view_type == 1 else 1
                offset = (page_number - 1) * items_per_page if view_type == 1 else offset

                # Create and send the view with the results
                view = CharacterDisplayView(
                    user_id=interaction.user.id,
                    guild_id=guild_id,
                    player_name=player_name,
                    character_name=character_name,
                    limit=items_per_page,
                    offset=offset,
                    view_type=view_type
                )
                await view.update_results()
                await view.create_embed()
                await interaction.followup.send(embed=view.embed, view=view)

        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(
                f"An error occurred whilst fetching data! input values of player_name: {player_name}, character_name: {character_name}': {e}"
            )
            await interaction.followup.send(
                f"An error occurred whilst fetching data. Please try again later.",
                ephemeral=True
            )

    @display_group.command(name='level_range', description='Display all characters in a level range')
    @app_commands.describe(
        level_range="the level range of the characters you are looking for. Keep in mind, this applies only to the preset low/med/high/max ranges your admin has set")
    async def display_level_range(self, interaction: discord.Interaction, level_range: discord.Role,
                                  current_page: int = 1):
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
                cursor = await conn.cursor()
                await cursor.execute("Select min(level), max(level) from Level_Range where Role_ID = ?",
                                     (level_range.id,))
                level_range_info = await cursor.fetchone()
                if not level_range_info:
                    await interaction.followup.send(
                        f"Level range {level_range.name} not found.",
                        ephemeral=True
                    )
                    return
                else:
                    level_range_min, level_range_max = level_range_info
                    await cursor.execute("SELECT COUNT(Character_Name) FROM Player_Characters WHERE ? <= level <= ?",
                                         (level_range_min, level_range_max))
                character_count = await cursor.fetchone()
                (character_count,) = character_count
                view_type = 1

                # Set up pagination variables
                page_number = min(max(page_number, 1), math.ceil(character_count / 20))
                items_per_page = 5 if view_type == 1 else 1
                offset = (page_number - 1) * items_per_page if view_type == 1 else offset

                # Create and send the view with the results
                view = LevelRangeDisplayView(
                    user_id=interaction.user.id,
                    guild_id=guild_id,
                    level_range_min=level_range_min,
                    level_range_max=level_range_max,
                    limit=items_per_page,
                    offset=offset,
                    view_type=view_type
                )
                await view.update_results()
                await view.create_embed()
                await interaction.followup.send(embed=view.embed, view=view)

        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(
                f"An error occurred in the 'display level_range' command while fetching data for '{level_range.name}': {e}"
            )
            await interaction.followup.send(
                f"An error occurred while fetching level_range information. Please try again later.",
                ephemeral=True
            )

    @character_group.command(name='backstory', description='give or edit the backstory of your character')
    @app_commands.autocomplete(character_name=shared_functions.own_character_select_autocompletion)
    @app_commands.describe(
        backstory="The backstory you wish to give to your character, you may use a google drive share link")
    async def backstory(self, interaction: discord.Interaction, character_name: str, backstory: str):
        """Give or edit the backstory of a character."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
                cursor = await conn.cursor()
                await cursor.execute(
                    "SELECT Character_Name, Article_ID, Mythweavers, Thread_ID FROM Player_Characters WHERE Player_Name = ? AND (Character_Name = ? OR Nickname = ?)",
                    (interaction.user.name, character_name, character_name)
                )
                character_info = await cursor.fetchone()
                if not character_info:
                    await interaction.followup.send(
                        f"Character '{character_name}' not found.",
                        ephemeral=True
                    )
                    return
                else:
                    (character_name, article_id, mythweavers, logging_thread_id) = character_info
                    if not character_info[1]:
                        await cursor.execute("SELECT Search FROM Admin WHERE Identifier = 'WA_Backstory_Category'")
                        category = await cursor.fetchone()
                        if not category:
                            await interaction.followup.send(
                                "Backstory category not found in the database.",
                                ephemeral=True
                            )
                            return
                        else:
                            article = await shared_functions.put_wa_article(guild_id=guild_id, template='person',
                                                                            category=category[0])
                            await cursor.execute(
                                "Update Player_Characters SET Article_ID = ?, Article_Link = ? WHERE Character_Name = ?",
                                (article['id'], article['url'], character_name))
                            await conn.commit()
                            await shared_functions.character_embed(character_name=character_name,
                                                                   guild=interaction.guild)
                            character_changes = shared_functions.CharacterChange(character_name=character_name,
                                                                                 author=interaction.user.name,
                                                                                 source=f'Backstory creation',
                                                                                 backstory=article['url'])
                            character_log = await shared_functions.log_embed(character_changes, interaction.guild,
                                                                             logging_thread_id, self.bot)
                            await interaction.followup.send(embed=character_log, ephemeral=True)
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(
                f"an error occured in the backstory command for '{character_name}': {e}"
            )
            await interaction.followup.send(
                f"An error occurred while fetching your proposition history. Please try again later.",
                ephemeral=True
            )


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


# Modified ShopView with additional logic
class TitleShopView(shared_functions.ShopView):
    def __init__(self, user_id, guild_id, offset, limit):
        super().__init__(user_id, guild_id, offset, limit)
        self.max_items = None  # Cache total number of items

    async def update_results(self):
        """Fetch the title results for the current page."""
        statement = """
            SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name
            FROM Store_Title
            LIMIT ? OFFSET ?
        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.limit, self.offset - 1))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        current_page = ((self.offset - 1) // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(title="Titles", description=f"Page {current_page} of {total_pages}")
        for title in self.results:
            self.embed.add_field(
                name=f"ID: {title[0]} - {title[3]} / {title[4]}",
                value=f"Effect: {title[1]}, Fame: {title[2]}",
                inline=False
            )

    async def get_max_items(self):
        """Get the total number of titles."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM Store_Title")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class PrestigeShopView(shared_functions.ShopView):
    def __init__(self, user_id, guild_id, offset, limit):
        super().__init__(user_id, guild_id, offset, limit)
        self.max_items = None  # Cache total number of items

    async def update_results(self):
        """Fetch the title results for the current page."""
        statement = """
            SELECT ID, fame_Required, Prestige_Cost, Name, Effect, Use_Limit
            FROM Store_Fame 
            LIMIT ? OFFSET ?
        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.limit, self.offset - 1))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        current_page = ((self.offset - 1) // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(title="Fame Store", description=f"Page {current_page} of {total_pages}")
        for fame in self.results:
            self.embed.add_field(name=f'**Name**: {fame[2]}',
                                 value=f'**Fame Required**: {fame[0]} **Prestige Cost**: {fame[1]}, **Limit**: {fame[4]} '
                                       f'\r\n **Effect**: {fame[3]}',
                                 inline=False)

    async def get_max_items(self):
        """Get the total number of titles."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM Store_Title")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class PrestigeHistoryView(shared_functions.ShopView):
    def __init__(self, user_id, guild_id, offset, limit, character_name, item_name):
        super().__init__(user_id, guild_id, offset, limit)
        self.max_items = None  # Cache total number of items
        self.character_name = character_name
        self.item_name = item_name

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""
        if self.item_name is None:
            statement = """
                SELECT Item_Name, Prestige_Cost, Transaction_ID, Time, IsAllowed
                FROM A_Audit_Prestige WHERE Character_Name = ? 
                ORDER BY Transaction_ID DESC LIMIT ? OFFSET ? 
            """
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute(statement, (self.character_name, self.limit, self.offset - 1))
                self.results = await cursor.fetchall()

        else:
            statement = """
                            SELECT Item_Name, Prestige_Cost, Transaction_ID, Time, IsAllowed
                            FROM A_Audit_Prestige WHERE Character_Name = ? AND Item_Name = ?
                            ORDER BY Transaction_ID DESC LIMIT ? OFFSET ? 
                        """
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute(statement, (self.character_name, self.item_name, self.limit, self.offset - 1))
                self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        current_page = ((self.offset - 1) // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(title=f"Prestige History for {self.character_name}",
                                   description=f"Page {current_page} of {total_pages}")
        for fame in self.results:
            (item_name, prestige_cost, transaction_id, time, isallowed) = fame
            allowed = "Approved" if isallowed == 1 else "Rejected"
            self.embed.add_field(name=f'**Item Name**: {item_name}',
                                 value=f'**Prestige Cost**: {prestige_cost} **Transaction ID**: {transaction_id}, **Allowed**: {allowed} '
                                       f'\r\n **Time**: {time}',
                                 inline=False)

    async def get_max_items(self):
        """Get the total number of titles."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                if not self.character_name:
                    cursor = await db.execute("SELECT COUNT(*) FROM Player_Characters")
                else:
                    cursor = await db.execute("SELECT COUNT(*) FROM Player_Characters WHERE Player_Name = ?",
                                              (self.character_name,))
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


# Dual View Type Views
class CharacterDisplayView(shared_functions.ShopView):
    def __init__(self, user_id, guild_id, offset, limit, player_name, character_name, view_type):
        super().__init__(user_id, guild_id, offset, limit, view_type)
        self.max_items = None  # Cache total number of items
        self.character_name = character_name
        self.view_type = view_type
        self.player_name = player_name

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""
        if not self.player_name:
            statement = """SELECT player_name, player_id, True_Character_Name, Title, Titles, Description, Oath, Level, 
                            Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, 
                            Essence, Fame, Prestige, Color, Mythweavers, Image_Link, Tradition_Name, 
                            Tradition_Link, Template_Name, Template_Link, Article_Link
                            FROM Player_Characters ORDER BY True_Character_Name ASC LIMIT ? OFFSET ?"""
            val = (self.limit, self.offset - 1)

        else:
            statement = """SELECT player_name, True_Character_Name, Title, Titles, Description, Oath, Level, 
                            Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, 
                            Essence, Fame, Prestige, Color, Mythweavers, Image_Link, Tradition_Name, 
                            Tradition_Link, Template_Name, Template_Link, Article_Link
                            FROM Player_Characters WHERE Player_Name = ? ORDER BY True_Character_Name ASC LIMIT ? OFFSET ? """
            val = (self.player_name, self.limit, self.offset - 1)
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, val)
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        if self.view_type == 1:
            if not self.player_name:
                current_page = ((self.offset - 1) // self.limit) + 1
                total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
                self.embed = discord.Embed(title=f"Character Summary",
                                           description=f"Page {current_page} of {total_pages}")
            else:
                current_page = ((self.offset - 1) // self.limit) + 1
                total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
                self.embed = discord.Embed(title=f"Character Summary for {self.player_name}",
                                           description=f"Page {current_page} of {total_pages}")
            for result in self.results:
                (player_name, true_character_name, title, titles, description, oath, level, tier, milestones,
                 milestones_required, trials, trials_required, gold, gold_value, essence, fame, prestige, color,
                 mythweavers, image_link, tradition_name, tradition_link, template_name, template_link,
                 article_link) = result
                self.embed.add_field(name=f'Character Name', value=f'**Name**:{true_character_name}')
                self.embed.add_field(name=f'Information',
                                     value=f'**Level**: {level}, **Mythic Tier**: {tier}')
                self.embed.add_field(name=f'Total Experience',
                                     value=f'**Milestones**: {milestones}, **Milestones Remaining**: {milestones_required}, **Trials**: {trials}, **Trials Remaining**: {trials_required}')
                self.embed.add_field(name=f'Current Wealth', value=f'**GP**: {gold}, **Essence**: {essence}')
                linkage = None
                if not tradition_name:
                    linkage += f"**Tradition**: [{tradition_name}]({tradition_link})"
                if not template_link:
                    if not tradition_name:
                        linkage += f" "
                    linkage += f"**Template**: [{template_name}]({template_link})"
                if not tradition_name or not template_name:
                    self.embed.add_field(name=f'Additional Info', value=linkage, inline=False)
        else:
            current_page = ((self.offset - 1) // self.limit) + 1
            total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
            for result in self.results:
                (player_name, true_character_name, title, titles, description, oath, level, tier, milestones,
                 milestones_required, trials, trials_required, gold, gold_value, essence, fame, prestige, color,
                 mythweavers, image_link, tradition_name, tradition_link, template_name, template_link,
                 article_link) = result
                self.embed = discord.Embed(title=f"Detailed view for {true_character_name}",
                                           description=f"Page {current_page} of {total_pages}",
                                           color=int(color[1:], 16))
                self.embed.set_author(name=f'{player_name}')
                self.embed.set_thumbnail(url=f'{image_link}')
                self.embed.add_field(name=f'Character Name', value=f'**Name**:{true_character_name}')
                self.embed.add_field(name=f'Information',
                                     value=f'**Level**: {level}, **Mythic Tier**: {tier}')
                self.embed.add_field(name=f'Total Experience',
                                     value=f'**Milestones**: {milestones}, **Milestones Remaining**: {milestones_required}, **Trials**: {trials}, **Trials Remaining**: {trials_required}')
                self.embed.add_field(name=f'Current Wealth',
                                     value=f'**GP**: {gold}, **Illiquid GP**: {gold_value - gold} **Essence**: {essence}')
                self.embed.add_field(name=f'Fame and Prestige', value=f'**Fame**: {fame}, **Prestige**: {prestige}')
                linkage = None
                if not tradition_name:
                    linkage += f"**Tradition**: [{tradition_name}]({tradition_link})"
                if not template_link:
                    if not tradition_name:
                        linkage += f" "
                    linkage += f"**Template**: [{template_name}]({template_link})"
                if not tradition_name or not template_name:
                    self.embed.add_field(name=f'Additional Info', value=linkage, inline=False)
                if oath == 'Offerings':
                    self.embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
                elif oath == 'Poverty':
                    self.embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
                elif oath == 'Absolute':
                    self.embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
                else:
                    self.embed.set_footer(text=f'{description}')

    async def get_max_items(self):
        """Get the total number of titles."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                if not self.player_name:
                    cursor = await db.execute("SELECT COUNT(*) FROM Player_Characters")
                else:
                    cursor = await db.execute("SELECT COUNT(*) FROM Player_Characters WHERE Player_Name = ?",
                                              (self.player_name,))
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items

    async def on_view_change(self):
        self.view_type = 1 if self.view_type == 2 else 2
        if self.view_type == 1:
            self.limit = 5  # Change the limit to 5 for the sumamry view
        else:
            self.limit = 1  # Change the limit to 1 for the detailed view


class LevelRangeDisplayView(shared_functions.ShopView):
    def __init__(self, user_id, guild_id, offset, limit, level_range_min, level_range_max, view_type):
        super().__init__(user_id, guild_id, offset, limit, view_type)
        self.max_items = None  # Cache total number of items
        self.view_type = view_type
        self.level_range_max = level_range_max
        self.level_range_min = level_range_min

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""
        statement = """SELECT player_name, player_id, True_Character_Name, Title, Titles, Description, Oath, Level, 
                        Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, 
                        Essence, Fame, Prestige, Color, Mythweavers, Image_Link, Tradition_Name, 
                        Tradition_Link, Template_Name, Template_Link, Article_Link
                        FROM Player_Characters WHERE ? <= level <= ? ORDER BY True_Character_Name ASC LIMIT ? OFFSET ? """
        val = (self.limit, self.offset - 1)
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, val)
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        if self.view_type == 1:
            if not self.player_name:
                current_page = ((self.offset - 1) // self.limit) + 1
                total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
                self.embed = discord.Embed(title=f"Character Summary",
                                           description=f"Page {current_page} of {total_pages}")
            else:
                current_page = ((self.offset - 1) // self.limit) + 1
                total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
                self.embed = discord.Embed(title=f"Character Summary for {self.player_name}",
                                           description=f"Page {current_page} of {total_pages}")
            for result in self.results:
                (player_name, true_character_name, title, titles, description, oath, level, tier, milestones,
                 milestones_required, trials, trials_required, gold, gold_value, essence, fame, prestige, color,
                 mythweavers, image_link, tradition_name, tradition_link, template_name, template_link,
                 article_link) = result
                self.embed.add_field(name=f'Character Name', value=f'**Name**:{true_character_name}')
                self.embed.add_field(name=f'Information',
                                     value=f'**Level**: {level}, **Mythic Tier**: {tier}')
                self.embed.add_field(name=f'Total Experience',
                                     value=f'**Milestones**: {milestones}, **Milestones Remaining**: {milestones_required}, **Trials**: {trials}, **Trials Remaining**: {trials_required}')
                self.embed.add_field(name=f'Current Wealth', value=f'**GP**: {gold}, **Essence**: {essence}')
                linkage = None
                if not tradition_name:
                    linkage += f"**Tradition**: [{tradition_name}]({tradition_link})"
                if not template_link:
                    if not tradition_name:
                        linkage += f" "
                    linkage += f"**Template**: [{template_name}]({template_link})"
                if not tradition_name or not template_name:
                    self.embed.add_field(name=f'Additional Info', value=linkage, inline=False)
        else:
            current_page = ((self.offset - 1) // self.limit) + 1
            total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
            for result in self.results:
                (player_name, true_character_name, title, titles, description, oath, level, tier, milestones,
                 milestones_required, trials, trials_required, gold, gold_value, essence, fame, prestige, color,
                 mythweavers, image_link, tradition_name, tradition_link, template_name, template_link,
                 article_link) = result
                self.embed = discord.Embed(title=f"Detailed view for {true_character_name}",
                                           description=f"Page {current_page} of {total_pages}",
                                           color=int(color[1:], 16))
                self.embed.set_author(name=f'{player_name}')
                self.embed.set_thumbnail(url=f'{image_link}')
                self.embed.add_field(name=f'Character Name', value=f'**Name**:{true_character_name}')
                self.embed.add_field(name=f'Information',
                                     value=f'**Level**: {level}, **Mythic Tier**: {tier}')
                self.embed.add_field(name=f'Total Experience',
                                     value=f'**Milestones**: {milestones}, **Milestones Remaining**: {milestones_required}, **Trials**: {trials}, **Trials Remaining**: {trials_required}')
                self.embed.add_field(name=f'Current Wealth',
                                     value=f'**GP**: {gold}, **Illiquid GP**: {gold_value - gold} **Essence**: {essence}')
                self.embed.add_field(name=f'Fame and Prestige', value=f'**Fame**: {fame}, **Prestige**: {prestige}')
                linkage = None
                if not tradition_name:
                    linkage += f"**Tradition**: [{tradition_name}]({tradition_link})"
                if not template_link:
                    if not tradition_name:
                        linkage += f" "
                    linkage += f"**Template**: [{template_name}]({template_link})"
                if not tradition_name or not template_name:
                    self.embed.add_field(name=f'Additional Info', value=linkage, inline=False)
                if oath == 'Offerings':
                    self.embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
                elif oath == 'Poverty':
                    self.embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
                elif oath == 'Absolute':
                    self.embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
                else:
                    self.embed.set_footer(text=f'{description}')

    async def get_max_items(self):
        """Get the total number of titles."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM Player_Characters WHERE ? <= level <= ?",
                                          (self.level_range_min, self.level_range_max))
            count = await cursor.fetchone()
            self.max_items = count[0]
        return self.max_items

    async def on_view_change(self):
        self.view_type = 1 if self.view_type == 2 else 2
        if self.view_type == 1:
            self.limit = 5  # Change the limit to 5 for the sumamry view
        else:
            self.limit = 1  # Change the limit to 1 for the detailed view


# Modified AcknowledgementView with additional logic
class PropositionView(shared_functions.AcknowledgementView):
    def __init__(
            self,
            allowed_user_id: int,
            requester_name: str,
            character_name: str,
            item_name: str,
            prestige_cost: int,
            proposition_id: int,
            bot: commands.Bot,
            prestige: int,
            logging_thread: int
    ):
        super().__init__(allowed_user_id)
        self.requester_name = requester_name
        self.character_name = character_name
        self.item_name = item_name
        self.prestige_cost = prestige_cost
        self.proposition_id = proposition_id
        self.bot = bot
        self.prestige = prestige
        self.logging_thread = logging_thread
        self.embed = None

    async def accepted(self, interaction: discord.Interaction):
        """Handle the approval logic."""
        # Update the database to mark the proposition as accepted
        # Adjust prestige, log the transaction, notify the requester, etc.
        await self.update_proposition_status(is_allowed=1)
        self.embed = discord.Embed(
            title="Proposition Accepted",
            description=f"The proposition {self.proposition_id} has been accepted.",
            color=discord.Color.green()
        )
        # Additional logic such as notifying the requester

    async def rejected(self, interaction: discord.Interaction):
        """Handle the rejection logic."""
        # Update the database to mark the proposition as rejected
        await self.update_proposition_status(is_allowed=-1)
        self.embed = discord.Embed(
            title="Proposition Rejected",
            description=f"The proposition {self.proposition_id} has been rejected.",
            color=discord.Color.red()
        )
        # Additional logic such as notifying the requester

    async def create_embed(self):
        """Create the initial embed for the proposition."""
        self.embed = discord.Embed(
            title="Proposition Request",
            description=(
                f"**Requester:** {self.requester_name}\n"
                f"**Character:** {self.character_name}\n"
                f"**Item:** {self.item_name}\n"
                f"**Prestige Cost:** {self.prestige_cost}\n"
                f"**Proposition ID:** {self.proposition_id}"
            ),
            color=discord.Color.blue()
        )

    async def update_proposition_status(self, is_allowed: int):
        """Update the proposition status in the database."""
        # Implement database update logic here
        # For example:
        async with aiosqlite.connect(f"Pathparser_{self.interaction.guild_id}.sqlite") as conn:
            await conn.execute(
                "UPDATE A_Audit_Prestige SET IsAllowed = ? WHERE Transaction_ID = ?",
                (is_allowed, self.proposition_id)
            )
            await conn.commit()
            await conn.execute(
                "UPDATE Player_Characters SET Prestige = Prestige - ? WHERE Character_Name = ?",
                (self.prestige_cost, self.proposition_id)
            )
            await conn.commit()

        # Additional logic such as adjusting prestige points


logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='application.log',  # Log to a file
    filemode='a'  # Append to the file
)
