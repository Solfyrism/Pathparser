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
from decimal import Decimal, ROUND_HALF_UP
from shared_functions import name_fix
import commands.character_commands as character_commands

# *** GLOBAL VARIABLES *** #
os.chdir("C:\\pathparser")


async def transaction_reverse(cursor: aiosqlite.Cursor, transaction_id: int, author_id: int, author_name: str,
                              reason: str) -> (
        Union[tuple[int, int, str, float, float, float, float], str]):
    try:
        await cursor.execute(
            "Select Character_Name, Gold_value, Effective_Gold_Value, Effective_gold_value_max, source_command, Related_Transaction_ID FROM A_Audit_Gold WHERE Transaction_ID = ?",
            (transaction_id,))
        gold_info = await cursor.fetchone()
        if not gold_info:
            return_value = f"There is no transaction with the ID of {transaction_id}."
            return return_value
        else:
            (character_name, gold, effective_gold, max_effective_gold, source_command,
             related_transaction_id) = gold_info
            await cursor.execute(
                "select gold, gold_value, gold_value_max, Thread_ID from Player_Characters where Character_Name = ?",
                (character_name,))
            player_info = await cursor.fetchone()
            if not player_info:
                return_value = f"There is no character with the name or nickname of {character_name}! Cannot undo transaction!"
                return return_value
            else:
                (gold_total, gold_value_total, gold_value_max_total, thread_id) = player_info
                await cursor.execute(
                    "UPDATE Player_Characters SET Gold = ?, Gold_Value = ?, Gold_Value_Max = ? WHERE Character_Name = ?",
                    (
                        gold_total - gold, gold_value_total - effective_gold, gold_value_max_total - max_effective_gold,
                        character_name))
                cursor.connection.commit()
                await cursor.execute(
                    "INSERT into A_Audit_Gold (Character_Name, Author_Name, Author_ID, Gold, Gold_Value, Effective_Gold_Value, Effective_Gold_value_max, Related_Transaction_ID, Reason, Source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        character_name, author_name, author_id, -gold, -effective_gold, -max_effective_gold,
                        transaction_id,
                        reason, 'undo transaction'))
                cursor.connection.commit()
                await cursor.execute("Select MAX(Transaction_ID) FROM A_Audit_Gold")
                new_transaction_id = await cursor.fetchone()
                new_transaction_id = new_transaction_id[0]
                return_value = (new_transaction_id, related_transaction_id, character_name, -gold, gold_total - gold,
                                gold_value_total - effective_gold, gold_value_max_total - max_effective_gold)
                return return_value
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(
            f"an error occurred for {author_name} whilst undoing transaction with id {transaction_id}': {e}")
        return_value = f"an error occurred for {author_name} whilst undoing transaction with id {transaction_id} Error: {e}."
        return return_value


async def session_reward_reversal(
        interaction: discord.Interaction,
        session_id: int,
        character_name: str,
        author_name: str,
        session_level: int,
        session_gold: float,
        session_info: Union[tuple, aiosqlite.Row],
        source: str) -> (
        Union[shared_functions.CharacterChange, str]):
    if not session_info:
        return f'invalid session ID of {session_id}'
    else:
        async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                (info_player_id, info_player_name, info_character_name, info_level, info_tier, info_effective_gold,
                 info_received_milestones, info_received_trials, info_received_gold, info_received_fame,
                 info_received_prestige, info_received_essence, info_transaction_id) = session_info
                await cursor.execute(
                    "SELECT True_Character_Name, Oath, Level, Tier, Milestones, Trials, Gold, Gold_Value, Gold_Value_Max, Essence, Thread_ID, Accepted_Date, Fame, Prestige FROM Player_Characters WHERE Character_Name = ? OR Nickname = ?",
                    (character_name, character_name))
                player_info = await cursor.fetchone()
                if not player_info:
                    return f"there is no {character_name} registered."
                else:
                    (true_character_name, oath, character_level, tier, milestones, trials, gold, gold_value,
                     gold_value_max,
                     essence, thread_id, accepted_date, fame, prestige) = player_info
                    try:
                        return_level = await character_commands.level_calculation(
                            level=session_level,
                            guild=interaction.guild,
                            guild_id=interaction.guild.id,
                            base=milestones,
                            personal_cap=0,
                            easy=0,
                            medium=0,
                            hard=0,
                            deadly=0,
                            misc=-info_received_milestones,
                            author_id=interaction.user.id,
                            character_name=character_name)
                    except character_commands.CalculationAidFunctionError as e:
                        return_level = f"An error occurred whilst adjusting levels for {character_name} \r\n"
                        logging.exception(f"Error in level calculation: {e}")
                    level_value = session_level if isinstance(return_level, str) else character_level[0]
                    try:
                        return_mythic = await character_commands.mythic_calculation(
                            character_name=character_name,
                            level=level_value,
                            trials=trials,
                            trial_change=-info_received_trials,
                            guild_id=interaction.guild.id)
                        return_mythic = return_mythic if tier != return_mythic[
                            0] or info_received_trials != 0 else 0
                    except character_commands.CalculationAidFunctionError as e:
                        return_mythic = f"An error occurred whilst adjusting trials for {character_name} \r\n"
                        logging.exception(f"Error in Mythic calculation: {e}")
                    try:
                        return_gold = await character_commands.gold_calculation(
                            guild_id=interaction.guild.id,
                            character_name=character_name,
                            level=level_value,
                            oath=oath,
                            gold=gold,
                            author_name=interaction.user.name,
                            author_id=interaction.user.id,
                            gold_value=gold_value,
                            gold_value_max=gold_value_max,
                            gold_change=-info_received_gold,
                            gold_value_change=Decimal(0),
                            gold_value_max_change=-Decimal(session_gold),
                            reason='Session Backout',
                            source=source
                        )
                    except character_commands.CalculationAidFunctionError as e:
                        return_gold = f"An error occurred whilst adjusting gold for {character_name} \r\n"
                        logging.exception(f"Error in gold calculation: {e}")
                    try:
                        return_essence = character_commands.calculate_essence(
                            character_name=character_name,
                            essence=essence,
                            essence_change=-info_received_essence,
                            accepted_date=accepted_date)
                    except character_commands.CalculationAidFunctionError as e:
                        return_essence = f"An error occurred whilst adjusting essence for {character_name} \r\n"
                        logging.exception(f"Error in essence calculation: {e}")
                    if isinstance(return_level, tuple) and \
                            (isinstance(return_mythic, tuple) or isinstance(return_mythic, int)) and \
                            isinstance(return_gold, tuple) and \
                            isinstance(return_essence, tuple):
                        await cursor.execute("DELETE FROM Sessions_Archive WHERE Session_ID = ? AND Character_Name = ?",
                                             (session_id, character_name))
                        cursor.connection.commit()
                    return_fame = (fame - info_received_fame, -info_received_fame, prestige - info_received_prestige,
                                   -info_received_prestige)
                    character_updates = shared_functions.UpdateCharacterData(character_name=character_name)
                    character_changes = shared_functions.CharacterChange(
                        character_name=character_name,
                        author=interaction.user.name,
                        source=source)
                    if isinstance(return_level, tuple):
                        (new_level,
                         total_milestones,
                         min_milestones,
                         milestones_to_level,
                         milestones_required,
                         awarded_total_milestones) = return_level
                        character_updates.level_package = (new_level, total_milestones, min_milestones)
                        character_changes.level = new_level
                        character_changes.milestones_total = total_milestones
                        character_changes.milestones_remaining = min_milestones
                        character_changes.milestone_change = awarded_total_milestones
                    if isinstance(return_mythic, tuple):
                        (new_tier, total_trials, trials_required, trial_change) = return_mythic
                        character_updates.trial_package = (new_tier, total_trials, trials_required)
                        character_changes.tier = new_tier
                        character_changes.trials = total_trials
                        character_changes.trials_remaining = trials_required
                        character_changes.trial_change = trial_change
                    if isinstance(return_gold, tuple):
                        (calculated_difference, gold_total, gold_value_total, gold_value_max_total,
                         transaction_id) = return_gold
                        character_updates.gold_package = (gold_total, gold_value_total, gold_value_max_total)
                        character_changes.gold = gold_total
                        character_changes.gold_change = calculated_difference
                        character_changes.effective_gold = gold_value_total
                        character_changes.effective_gold_max = gold_value_max_total
                        character_changes.transaction_id = transaction_id
                    if isinstance(return_essence, tuple):
                        (essence_total, essence_change) = return_essence
                        character_updates.essence_package = essence_total
                        character_changes.essence = essence_total
                        character_changes.essence_change = essence_change
                    if isinstance(return_fame, tuple):
                        (fame, fame_change, prestige, prestige_change) = return_fame
                        character_updates.fame_package = (fame, prestige)
                        character_changes.fame = fame
                        character_changes.fame_change = fame_change
                        character_changes.prestige = prestige
                        character_changes.prestige_change = prestige_change
                    await shared_functions.update_character(
                        guild_id=interaction.guild.id,
                        change=character_updates)
                    return character_changes
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"an error occurred for {author_name} whilst rewarding session with ID {session_id} for character {character_name}': {e}")
                return f"An error occurred whilst adjusting session with ID '{session_id}' for {character_name} Error: {e}."


async def session_reward_calculation(interaction: discord.Interaction, session_id: int,
                                     character_name: str, author_name: str, session_level: int, source: str) -> (
        Union[shared_functions.CharacterChange, str]):
    async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}.sqlite") as conn:
        cursor = await conn.cursor()
        # try:
        await cursor.execute(
            "SELECT GM_Name, Session_Name, Play_Time, Session_Range, Gold, Essence, Easy, Medium, Hard, Deadly, Trials, Alt_Reward_All, Alt_Reward_Party, Session_Thread, Message, Rewards_Message, Rewards_Thread, Fame, Prestige FROM Sessions WHERE Session_ID = ? and IsActive = 0 LIMIT 1",
            (session_id,))
        session_info = await cursor.fetchone()
        if not session_info:
            return f'invalid session ID of {session_id}'
        else:
            (gm_name, session_name, play_time, session_range, session_gold, session_essence, session_easy,
             session_medium, session_hard, session_deadly, session_trials, session_alt_reward_all,
             session_alt_reward_party, session_session_thread, session_message, session_rewards_message,
             session_rewards_thread, session_fame, session_prestige) = session_info
            await cursor.execute(
                "SELECT Player_ID, True_Character_Name, Oath, Level, Tier, Milestones, Trials, Gold, Gold_Value, Gold_Value_Max, Essence, Thread_ID, Accepted_Date, Fame, Prestige FROM Player_Characters WHERE Character_Name = ? OR Nickname = ?",
                (character_name, character_name))
            player_info = await cursor.fetchone()
            if not player_info:
                return f"there is no {character_name} registered."
            else:
                (player_id, true_character_name, oath, character_level, tier, milestones, trials, gold, gold_value,
                 gold_value_max,
                 essence, thread_id, accepted_date, fame, prestige) = player_info
                try:
                    return_level = await character_commands.level_calculation(
                        level=session_level,
                        guild=interaction.guild,
                        guild_id=interaction.guild.id,
                        personal_cap=0,
                        base=milestones,
                        easy=session_easy,
                        medium=session_medium,
                        hard=session_hard,
                        deadly=session_deadly,
                        misc=0,
                        author_id=interaction.user.id,
                        character_name=character_name)
                except character_commands.CalculationAidFunctionError as e:
                    return_level = f"An error occurred whilst adjusting levels for {character_name} \r\n"
                    logging.exception(f"Error in level calculation: {e}")
                level_value = session_level if isinstance(return_level, str) else character_level[0]
                try:
                    return_mythic = await character_commands.mythic_calculation(
                        guild_id=interaction.guild.id,
                        character_name=character_name,
                        level=level_value,
                        trials=trials,
                        trial_change=session_trials)
                    return_mythic = return_mythic if tier != return_mythic[
                        0] or session_trials != 0 else "No Change in Mythic"
                except character_commands.CalculationAidFunctionError as e:
                    return_mythic = f"An error occurred whilst adjusting trials for {character_name} \r\n"
                    logging.exception(f"Error in mythic calculation: {e}")
                try:
                    return_gold = await character_commands.gold_calculation(
                        guild_id=interaction.guild_id,
                        character_name=character_name,
                        level=level_value,
                        oath=oath,
                        gold=gold,
                        gold_value=gold_value,
                        gold_value_max=gold_value_max,
                        gold_change=session_gold,
                        gold_value_change=Decimal(0),
                        gold_value_max_change=Decimal(0),
                        author_name=author_name,
                        author_id=interaction.user.id,
                        reason='Session Reward',
                        source=source)
                except character_commands.CalculationAidFunctionError as e:
                    return_gold = f"An error occurred whilst adjusting gold for {character_name} \r\n"
                    logging.exception(f"Error in gold calculation: {e}")
                try:
                    return_essence = character_commands.calculate_essence(
                        character_name=character_name,
                        essence=essence,
                        essence_change=session_essence,
                        accepted_date=accepted_date)
                except character_commands.CalculationAidFunctionError as e:
                    return_essence = f"An error occurred whilst adjusting essence for {character_name} \r\n"
                    logging.exception(f"Error in essence calculation: {e}")
                return_fame = (fame + session_fame, session_fame, prestige + session_prestige, session_prestige)
                character_updates = shared_functions.UpdateCharacterData(character_name=character_name)
                character_changes = shared_functions.CharacterChange(
                    character_name=character_name,
                    author=interaction.user.name,
                    source=source)
                if isinstance(return_level, tuple):
                    (
                        new_level,
                        total_milestones,
                        min_milestones,
                        milestones_to_level,
                        milestones_required,
                        awarded_total_milestones) = return_level
                    character_updates.level_package = (new_level, total_milestones, min_milestones)
                    character_changes.level = new_level
                    character_changes.milestones_total = total_milestones
                    character_changes.milestones_remaining = min_milestones
                    character_changes.milestone_change = awarded_total_milestones
                else:
                    awarded_total_milestones = None
                if isinstance(return_mythic, tuple):
                    (new_tier, total_trials, trials_required, trial_change) = return_mythic
                    character_updates.trial_package = (new_tier, total_trials, trials_required)
                    character_changes.tier = new_tier
                    character_changes.trials = total_trials
                    character_changes.trials_remaining = trials_required
                    character_changes.trial_change = trial_change
                else:
                    trial_change = None
                if isinstance(return_gold, tuple):
                    (calculated_difference, gold_total, gold_value_total, gold_value_max_total,
                     transaction_id) = return_gold
                    character_updates.gold_package = (gold_total, gold_value_total, gold_value_max_total)
                    character_changes.gold = gold_total
                    character_changes.gold_change = calculated_difference
                    character_changes.effective_gold = gold_value_total
                    character_changes.effective_gold_max = gold_value_max_total
                    character_changes.transaction_id = transaction_id
                else:
                    transaction_id = None
                if isinstance(return_essence, tuple):
                    (essence_total, essence_change) = return_essence
                    character_updates.essence_package = essence_total
                    character_changes.essence = essence_total
                    character_changes.essence_change = essence_change
                else:
                    essence_change = None
                if isinstance(return_fame, tuple):
                    (fame, fame_change, prestige, prestige_change) = return_fame
                    character_updates.fame_package = (fame, prestige)
                    character_changes.fame = fame
                    character_changes.fame_change = fame_change
                    character_changes.prestige = prestige
                    character_changes.prestige_change = prestige_change
                await shared_functions.update_character(guild_id=interaction.guild.id,
                                                        change=character_updates)
                await cursor.execute(
                    "insert into Sessions_Archive (Session_ID, Player_ID, Character_Name, Level, Tier, "
                    "Effective_Gold, Received_Milestones, Received_Trials, Received_Gold, Received_Fame, "
                    "Received_Prestige, Received_Essence, Gold_Transaction_ID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (session_id, player_id, character_name, character_level, tier, awarded_total_milestones,
                     awarded_total_milestones, trial_change, transaction_id,
                     fame_change, prestige_change, essence_change, transaction_id))
                await conn.commit()
                return character_changes


"""    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(
            f"an error occurred for {author_name} whilst rewarding session with ID {session_id} for character {character_name}': {e}")
        return f"An error occurred whilst adjusting session with ID '{session_id}' for {character_name} Error: {e}."
"""


def safe_add(a, b):
    # Treat None as zero
    a = a if a is not None else 0
    b = b if b is not None else 0

    # If either value is a Decimal, convert both to Decimal
    if isinstance(a, float) or isinstance(b, float):
        a = float(a)
        b = float(b)

    return a + b


async def session_log_player(cursor: aiosqlite.Cursor,
                             interaction: discord.Interaction,
                             bot,
                             session_id: int,
                             player_id: int,
                             character_name: str,
                             thread_id: int,
                             source: str,
                             packaged_session_info: tuple,
                             return_level: tuple,
                             return_trial: tuple,
                             return_gold: tuple,
                             return_essence: tuple):
    try:
        character_changes = shared_functions.CharacterChange(
            character_name=character_name,
            author=interaction.user.name,
            source=source)
        if isinstance(return_level, tuple):
            (new_level, total_milestones, min_milestones, milestones_to_level, milestones_required,
             awarded_total_milestones) = return_level
            character_changes.level = new_level
            character_changes.milestones_total = total_milestones
            character_changes.milestones_remaining = min_milestones
            character_changes.milestone_change = awarded_total_milestones
        else:
            awarded_total_milestones = 0
        if isinstance(return_trial, tuple):
            (new_tier, total_trials, trials_required, trial_change) = return_trial
            character_changes.tier = new_tier
            character_changes.trials = total_trials
            character_changes.trials_remaining = trials_required
            character_changes.trial_change = trial_change
        elif isinstance(return_trial, int):
            trial_change = 0
        else:
            trial_change = 0
        if isinstance(return_gold, tuple):
            (calculated_difference, gold_total, gold_value_total, gold_value_max_total, transaction_id) = return_gold
            character_changes.gold = gold_total
            character_changes.gold_change = calculated_difference
            character_changes.effective_gold = gold_value_total
            character_changes.effective_gold_max = gold_value_max_total
            character_changes.transaction_id = transaction_id
        else:
            calculated_difference = 0
            transaction_id = 0
        if isinstance(return_essence, tuple):
            (essence_total, essence_change) = return_essence
            character_changes.essence = essence_total
            character_changes.essence_change = essence_change
        else:
            essence_change = 0
        (player_name, player_id, original_level, original_tier, original_effective_gold) = packaged_session_info
        await cursor.execute("INSERT INTO Session_Log (Session_ID, Player_ID, Character_Name, Level, "
                             "Tier, Effective_Gold, Received_Milestones, Received_Trials, Received_Gold, "
                             "Received_Fame, Received_Prestige, Received_Essence, Gold_Transaction_ID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             (
                                 session_id, player_id, character_name, original_level, original_tier,
                                 original_effective_gold,
                                 awarded_total_milestones, trial_change, calculated_difference, 0, 0, essence_change,
                                 transaction_id))
        await shared_functions.character_embed(character_name=character_name,
                                               guild=interaction.guild)
        await shared_functions.log_embed(change=character_changes, guild=interaction.guild,
                                         thread=thread_id, bot=bot)
        return f"<@{player_id}>'s {character_name} has been successfully updated!"
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(
            f"an error occurred for {interaction.user.name} whilst updating bio & log with ID {session_id} for character {character_name}': {e}")
        return f"<@{player_id}>'s {character_name} encountered an error whilst being updated! Error: {e}."


# noinspection PyUnresolvedReferences
class AdminCommands(commands.Cog, name='admin'):
    def __init__(self, bot):
        self.bot = bot

    admin_group = discord.app_commands.Group(
        name='admin',
        description='Commands related to administration'
    )

    @admin_group.command(name='help', description='Help commands for the character tree')
    async def help(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            embed = discord.Embed(title=f"Admin Help", description=f'This is a list of Admin help commands',
                                  colour=discord.Colour.blurple())
            embed.add_field(name=f'**Character Commands**',
                            value=f'**/Character_Milestones**: Modifies the milestones associated with a character. \r\n' +
                                  f'**/admin character_trials**: Modifies the trials associated with a character. \r\n' +
                                  f'**/admin gold_adjust**: Modifies the gold that a character has. \r\n ' +
                                  f'**/admin Essence_Adjust**: Modifies the essence that a character has. \r\n ' +
                                  f'**/admin customize**: Apply a Tradition or Template for a character \r\n' +
                                  f'**/admin manage**: Accept or reject a player registration attempt, or clean out historical ones. \r\n ' +
                                  f'**/admin undo_transaction**: undo a player transaction', inline=False)
            embed.add_field(name=f'**Database Commands**',
                            value=f'**/settings_display**: Display the various Administrative Defined Settings\r\n' +
                                  f'**/admin settings_define**: Define an Administrative Setting.\r\n' +
                                  f'**/admin level_cap**: Set a new level cap and set all player characters levels as appropriate.\r\n' +
                                  f'**/admin Tier_cap**: Set a new tier cap and set all player characters levels as appropriate.\r\n' +
                                  f'**/admin level_range**: Define a role and range for a level range.\r\n' +
                                  f'**/admin reset_database**: Reset the Server Database to Defaults.\r\n' +
                                  f'**/admin clean_playerbase**: Clean out a or all inactive player characters from player characters and gold history and session history.',
                            inline=False)
            embed.add_field(name=f"**Utility Commands**",
                            value=f'**/admin session_adjust**: alter the reward from a session.\r\n' +
                                  f'**/admin ubb_inventory**: Display the inventory of a user in order to find information.',
                            inline=False)
            embed.add_field(name=f"**Fame Commands**",
                            value=f'**/admin fame_store**: Add, edit, or remove items from the fame store.\r\n' +
                                  f'**/admin title_store**: Add, edit, or remove items from the title store.\r\n',
                            inline=False)
            await interaction.followup.send(embed=embed)
        except discord.errors.HTTPException:
            logging.exception(f"Error in help command")
        finally:
            return

    character_group = discord.app_commands.Group(
        name='character',
        description='Event settings commands',
        parent=admin_group
    )

    @character_group.command(name="milestones",
                             description="commands for adding or removing milestones from a character")
    @app_commands.autocomplete(character_name=shared_functions.character_select_autocompletion)
    @app_commands.describe(job='What kind of job you are adding')
    @app_commands.choices(
        job=[discord.app_commands.Choice(name='Easy', value=1), discord.app_commands.Choice(name='Medium', value=2),
             discord.app_commands.Choice(name='Hard', value=3), discord.app_commands.Choice(name='Deadly', value=4),
             discord.app_commands.Choice(name='None', value=5)])
    @app_commands.describe(level="The character level for the adjustment: Default at 0 to use current level.")
    async def character_milestones(self, interaction: discord.Interaction, character_name: str, amount: int,
                                   job: discord.app_commands.Choice[int], level: typing.Optional[int],
                                   misc_milestones: int = 0):
        """Adjusts the milestone number a PC has."""
        _, unidecode_name = name_fix(character_name)
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                if amount == 0 and misc_milestones == 0:
                    await interaction.followup.send("No Change in Milestones!", ephemeral=True)
                elif job == 'None' and misc_milestones == 0:
                    await interaction.followup.send("No Change in Milestones!", ephemeral=True)
                else:
                    await cursor.execute(
                        "Select True_Character_Name, Character_Name, Thread_ID, Level, Milestones, Tier, Trials, Personal_Cap FROM Player_Characters where Character_Name = ? OR Nickname = ?",
                        (unidecode_name, unidecode_name))
                    player_info = await cursor.fetchone()
                    if not player_info:
                        await interaction.followup.send(f"There is no player character with this name or nickname..")
                    if player_info:
                        (true_character_name, character_name, thread_id, character_level, milestones, tier, trials,
                         personal_cap) = player_info
                        character_level = level if level is not None else character_level
                        easy = amount if job.name == 'Easy' else 0
                        medium = amount if job.name == 'Medium' else 0
                        hard = amount if job.name == 'Hard' else 0
                        deadly = amount if job.name == 'Deadly' else 0
                        level_adjustment = await character_commands.level_calculation(
                            character_name=character_name,
                            level=character_level,
                            guild=guild,
                            guild_id=guild_id,
                            personal_cap=personal_cap,
                            base=milestones,
                            easy=easy,
                            medium=medium,
                            hard=hard,
                            deadly=deadly,
                            misc=misc_milestones)
                        (new_level,
                         total_milestones,
                         min_milestones,
                         milestones_to_level,
                         milestones_required,
                         awarded_total_milestones) = level_adjustment
                        mythic_adjustment = await character_commands.mythic_calculation(
                            guild_id=guild_id,
                            character_name=character_name,
                            level=new_level,
                            trials=trials,
                            trial_change=0)
                        (new_tier, total_trials, trials_required, trial_change) = mythic_adjustment
                        character_changes = shared_functions.CharacterChange(
                            character_name=character_name,
                            author=interaction.user.name,
                            level=new_level,
                            milestones_total=total_milestones,
                            milestone_change=awarded_total_milestones,
                            milestones_remaining=min_milestones,
                            source=f"admin adjusted milestones by {amount} for {character_name}")
                        if new_tier != tier:
                            character_changes.tier = new_tier
                            character_changes.trials = total_trials
                            character_changes.trials_remaining = trials_required
                            character_changes.trial_change = 0
                        character_log = await shared_functions.log_embed(change=character_changes, guild=guild,
                                                                         thread=thread_id, bot=self.bot)
                        await shared_functions.character_embed(
                            character_name=character_name,
                            guild=guild)
                        await interaction.followup.send(embed=character_log,
                                                        content=f"milestone changes for {character_name} have been made.")
            except (aiosqlite.Error, TypeError, ValueError, character_commands.CalculationAidFunctionError) as e:
                logging.exception(
                    f"an error occurred for {interaction.user.name} whilst adjusting milestones for {character_name}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst adjusting milestones for '{character_name}' Error: {e}.", ephemeral=True)

    @character_group.command(name="trials",
                             description="commands for adding or removing mythic trials from a character")
    @app_commands.autocomplete(character_name=shared_functions.character_select_autocompletion)
    async def trial_adjustment(self, interaction: discord.Interaction, character_name: str, amount: int):
        """Adjust the number of Mythic Trials a character possesses"""
        _, unidecode_name = name_fix(character_name)
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute(
                    "Select True_Character_Name, Character_Name, Level, Tier, Trials  FROM Player_Characters where Character_Name = ? OR Nickname = ?",
                    (character_name, character_name))
                player_info = cursor.fetchone()
                if amount == 0:
                    await interaction.followup.send(f"No changes to trial total required.")
                else:
                    if not player_info:
                        await interaction.followup.send(
                            f"there is no {character_name} registered.")
                    else:
                        (true_character_name, character_name, character_level, tier, trials) = player_info
                        mythic_adjustment = await character_commands.mythic_calculation(
                            character_name=character_name,
                            level=character_level,
                            trials=trials,
                            trial_change=amount,
                            guild_id=guild_id)
                        (new_tier, total_trials, trials_required, trial_change) = mythic_adjustment
                        character_changes = shared_functions.CharacterChange(
                            character_name=character_name,
                            author=interaction.user.name,
                            tier=new_tier,
                            trials=total_trials,
                            trials_remaining=trials_required,
                            trial_change=amount,
                            source=f"admin adjusted trials by {amount} for {character_name}")
                        character_log = await shared_functions.log_embed(change=character_changes, guild=guild,
                                                                         thread=thread_id, bot=self.bot)
                        await shared_functions.character_embed(
                            character_name=character_name,
                            guild=guild)
                        await interaction.followup.send(embed=character_log,
                                                        content=f"Trial changes for {character_name} have been made.")
            except (aiosqlite.Error, TypeError, ValueError, character_commands.CalculationAidFunctionError) as e:
                logging.exception(
                    f"an error occurred for {interaction.user.name} whilst adjusting trials for {character_name}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst adjusting trials for '{character_name}' Error: {e}.", ephemeral=True)

    @character_groupcommand(name="essence",
                            description="commands for adding or removing essence from a character")
    @app_commands.autocomplete(character_name=character_select_autocompletion)
    async def essence(self, interaction: discord.Interaction, character_name: str, amount: int):
        """Adjust the essence a PC has"""
        _, unidecode_name = name_fix(character_name)
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute(
                    "Select True_Character_Name, Character_Name, Essence, Thread_ID FROM Player_Characters where Character_Name = ? OR Nickname = ?",
                    (unidecode_name, unidecode_name))
                player_info = await cursor.fetchone()
                if amount == 0:
                    await interaction.followup.send(f"No changes to essence total required.")
                else:
                    if not player_info:
                        await interaction.followup.send(
                            f"there is no {character_name} registered.")
                    else:
                        (true_character_name, character_name, essence, thread_id) = player_info
                        essence_adjustment = character_commands.calculate_essence(
                            character_name=character_name,
                            essence=essence,
                            essence_change=amount,
                            accepted_date=None
                        )
                        (new_essence, essence_change) = essence_adjustment
                        character_updates = shared_functions.UpdateCharacterData(
                            character_name=character_name,
                            essence=new_essence)
                        await shared_functions.update_character(
                            guild_id=guild.id,
                            change=character_updates)
                        character_changes = shared_functions.CharacterChange(
                            character_name=character_name,
                            author=interaction.user.name,
                            essence=new_essence,
                            essence_change=essence_change,
                            source=f"admin adjusted essence by {amount} for {character_name}")
                        character_log = await shared_functions.log_embed(change=character_changes, guild=guild,
                                                                         thread=thread_id, bot=self.bot)
                        await shared_functions.character_embed(
                            character_name=character_name,
                            guild=guild)
                        await interaction.followup.send(embed=character_log,
                                                        content=f"Essence changes for {character_name} have been made.")
            except (aiosqlite.Error, TypeError, ValueError, character_commands.CalculationAidFunctionError) as e:
                logging.exception(
                    f"an error occurred for {interaction.user.name} whilst adjusting essence for {character_name}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst adjusting essence for '{character_name}' Error: {e}.", ephemeral=True)

    @character_group.command(name="gold_adjust",
                             description="commands for adding or removing gold from a character")
    @app_commands.autocomplete(character_name=shared_functions.character_select_autocompletion)
    async def gold_adjust(
            self,
            interaction: discord.Interaction,
            character_name: str,
            reason: str,
            amount: float = 0.0,
            effective_gold: float = 0.0,
            lifetime_gold: float = 0.0
    ):
        """Adjust the gold a PC has"""
        _, unidecode_name = name_fix(character_name)
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)

        # Convert input values to Decimal
        amount = Decimal(str(amount))
        effective_gold = Decimal(str(effective_gold))
        lifetime_gold = Decimal(str(lifetime_gold))

        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                if amount == 0 and effective_gold == 0 and lifetime_gold == 0:
                    await interaction.followup.send(
                        "If you don't intend to change anything, why initiate the command?",
                        ephemeral=True
                    )
                    return

                await cursor.execute(
                    """
                    SELECT True_Character_Name, Character_Name, Level, Oath,
                           Gold, Gold_Value, Gold_Value_max, Thread_ID
                    FROM Player_Characters
                    WHERE Character_Name = ? OR Nickname = ?
                    """,
                    (unidecode_name, unidecode_name)
                )
                player_info = await cursor.fetchone()

                if not player_info:
                    await interaction.followup.send(
                        f"No character found with the name or nickname '{character_name}'.",
                        ephemeral=True
                    )
                    return

                (true_character_name, character_name, character_level, oath,
                 gold, gold_value, gold_value_max, thread_id) = player_info

                # Convert fetched values to Decimal
                gold = Decimal(str(gold))
                gold_value = Decimal(str(gold_value))
                gold_value_max = Decimal(str(gold_value_max))

                gold_result = await character_commands.gold_calculation(
                    guild_id=guild_id,
                    author_id=interaction.user.id,
                    author_name=interaction.user.name,
                    character_name=character_name,
                    level=character_level,
                    oath=oath,
                    gold=gold,
                    gold_value=gold_value,
                    gold_value_max=gold_value_max,
                    gold_change=amount,
                    gold_value_change=effective_gold,
                    gold_value_max_change=lifetime_gold,
                    source='Admin Gold Adjust',
                    reason=reason
                )

                (adjusted_gold_change, gold_total, new_effective_gold,
                 gold_value_max_total, transaction_id) = gold_result

                gold_package = (gold_total, new_effective_gold, gold_value_max_total)
                character_updates = shared_functions.UpdateCharacterData(
                    character_name=character_name,
                    gold_package=gold_package
                )
                await shared_functions.update_character(
                    guild_id=guild_id,
                    change=character_updates
                )

                character_changes = shared_functions.CharacterChange(
                    character_name=character_name,
                    author=interaction.user.name,
                    gold=gold_total,
                    gold_change=adjusted_gold_change,
                    effective_gold=new_effective_gold,
                    transaction_id=transaction_id,
                    source=f"Admin adjusted gold by {amount} for {character_name} for {reason}"
                )

                character_log = await shared_functions.log_embed(
                    change=character_changes,
                    guild=guild,
                    thread=thread_id,
                    bot=self.bot
                )
                await shared_functions.character_embed(
                    character_name=character_name,
                    guild=guild
                )
                await interaction.followup.send(
                    embed=character_log,
                    content=f"Gold changes for {character_name} have been made."
                )
            except Exception as e:
                logging.exception(
                    f"An error occurred for {interaction.user.name} while adjusting gold for {character_name}: {e}"
                )
                await interaction.followup.send(
                    f"An error occurred while adjusting gold for '{character_name}'. Error: {e}.",
                    ephemeral=True
                )

    gold_group = discord.app_commands.Group(
        name='gold',
        description='gold commands',
        parent=admin_group
    )

    @gold_group.command(name="undo_transaction",
                        description="commands for undoing a transaction")
    @app_commands.autocomplete(character_name=shared_functions.character_select_autocompletion)
    async def undo_transaction(self, interaction: discord.Interaction, reason: str,
                               transaction_id: int):
        guild_id = interaction.guild_id
        guild = interaction.guild

        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                transaction_undo = await transaction_reverse(
                    cursor=cursor, transaction_id=transaction_id,
                    author_id=interaction.user.id, author_name=interaction.user.name, reason=reason)
                if isinstance(transaction_undo, str):
                    await interaction.followup.send(transaction_undo, ephemeral=True)
                else:
                    (new_transaction_id, related_transaction_id, character_name, amount, gold_total, gold_value_total,
                     gold_value_max_total) = transaction_undo
                    character_changes = shared_functions.CharacterChange(
                        character_name=character_name,
                        author=interaction.user.name,
                        gold=Decimal(gold_total),
                        gold_change=Decima(amount),
                        transaction_id=transaction_id,
                        source=f"admin undid the transaction of transaction ID: {transaction_id} reducing gold by {amount} for {character_name} for {reason} \r\n New Transaction ID of {new_transaction_id}")
                    character_log = await shared_functions.log_embed(
                        change=character_changes,
                        guild=guild,
                        thread=thread_id,
                        bot=self.bot)
                    await shared_functions.character_embed(
                        character_name=character_name,
                        guild=guild)
                    content = f"undid transaction {transaction_id} for {character_name} with a new transaction id of {new_transaction_id}."
                    if related_transaction_id:
                        related_transaction_undo = await transaction_reverse(
                            cursor=cursor, transaction_id=transaction_id,
                            author_id=interaction.user.id, author_name=interaction.user.name, reason=reason)
                        if isinstance(related_transaction_undo, str):
                            content += f"\r\n {related_transaction_undo}"
                        else:
                            (new_transaction_id, _, character_name, amount, gold_total, gold_value_total,
                             gold_value_max_total) = related_transaction_undo
                            character_changes = shared_functions.CharacterChange(
                                character_name=character_name,
                                author=interaction.user.name,
                                gold=Decimal(gold_total),
                                gold_change=Decimal(amount),
                                transaction_id=transaction_id,
                                source=f"admin undid the transaction of transaction ID: {transaction_id} reducing gold by {amount} for {character_name} for {reason} \r\n New Transaction ID of {new_transaction_id}")
                            character_log = await shared_functions.log_embed(
                                change=character_changes,
                                guild=guild,
                                thread=thread_id,
                                bot=self.bot)
                            await shared_functions.character_embed(
                                character_name=character_name,
                                guild=guild)
                            content += f"\r\n undid related transaction {transaction_id} for {character_name} with a new transaction id of {new_transaction_id}."
                    await interaction.followup.send(embed=character_log, content=content)
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"an error occurred for {interaction.user.name} whilst undoing a gold transaction with ID: {transaction_id}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst undoing a gold transaction with ID: '{transaction_id}' Error: {e}.",
                    ephemeral=True)

    session_group = discord.app_commands.Group(
        name='session',
        description='session commands',
        parent=admin_group
    )

    @session_group.command(name="management", description="command for managing sessions")
    async def management(self, interaction: discord.Interaction, session_id: int, gold: typing.Optional[int],
                         easy: typing.Optional[int], medium: typing.Optional[int], hard: typing.Optional[int],
                         deadly: typing.Optional[int], essence: typing.Optional[int],
                         trials: typing.Optional[int],
                         reward_all: typing.Optional[str], party_reward: typing.Optional[str],
                         fame: typing.Optional[int], prestige: typing.Optional[int]):
        """Update Session Information and alter the rewards received by the players"""
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute(
                    "SELECT GM_Name, Session_Name, Play_Time, Session_Range, Gold, Essence, Easy, Medium, Hard, Deadly, Trials, Alt_Reward_All, Alt_Reward_Party, Session_Thread, Message, Rewards_Message, Rewards_Thread, Fame, Prestige FROM Sessions WHERE Session_ID = ? and IsActive = 0 LIMIT 1",
                    (session_id,))
                session_info = await cursor.fetchone()
                if not session_info:
                    await interaction.followup.send(f'invalid session ID of {session_id}')
                else:
                    (gm_name, session_name, play_time, session_range, session_gold, session_essence, session_easy,
                     session_medium, session_hard, session_deadly, session_trials, session_alt_reward_all,
                     session_alt_reward_party, session_session_thread, session_message, session_rewards_message,
                     session_rewards_thread, session_fame, session_prestige) = session_info
                    rewarded_gold = session_gold if not gold else gold
                    rewarded_essence = session_essence if not essence else essence
                    rewarded_easy = session_easy if easy is None else easy
                    rewarded_medium = session_medium if medium is None else medium
                    rewarded_hard = session_hard if hard is None else hard
                    rewarded_deadly = session_deadly if deadly is None else deadly
                    rewarded_trials = session_trials if trials is None else trials
                    rewarded_reward_all = session_alt_reward_all if reward_all is None else reward_all
                    rewarded_reward_party = session_alt_reward_party if party_reward is None else party_reward
                    rewarded_fame = session_fame if fame is None else fame
                    rewarded_prestige = session_prestige if prestige is None else prestige
                    await cursor.execute("update Sessions set IsActive = 0, "
                                         "gold = ?, essence = ?, easy = ?, medium = ?, hard = ?, deadly = ?, trials = ?, "
                                         "fame = ?, prestige = ?, alt_reward_party = ?, alt_reward_all = ? where Session_ID = ?",
                                         (
                                             rewarded_gold, rewarded_essence, rewarded_easy, rewarded_medium,
                                             rewarded_hard,
                                             rewarded_deadly, rewarded_trials, rewarded_fame, rewarded_prestige,
                                             rewarded_reward_party,
                                             rewarded_reward_all, session_id))
                    await conn.commit()
                    if rewarded_gold < 0 or rewarded_easy < 0 or rewarded_medium < 0 or rewarded_hard < 0 or rewarded_deadly < 0 or rewarded_essence < 0 or rewarded_trials < 0:
                        await interaction.followup.send(
                            f"Minimum Session Rewards may only be 0, if a player receives a lesser reward, have them claim the transaction.")
                    else:
                        await cursor.execute(
                            "Select Player_ID, Player_Name, Character_Name, Level, Tier, Effective_Gold, Received_Milestones, Received_Trials, Received_Gold, Received_Fame, Received_Prestige, Received_Essence, Gold_Transaction_ID FROM Sessions_Archive WHERE Session_ID = ?",
                            (session_id,))
                        session_complex = await cursor.fetchall()
                        if not session_complex:
                            await interaction.followup.send(f"there are no players registered for this session.")
                        else:
                            embed = discord.Embed(title="Session Adjustment Report",
                                                  description=f"a report of the session: {session_name}",
                                                  color=discord.Color.blue())
                            for idx, player in enumerate(session_complex):
                                (player_id, player_name, character_name, level, tier, effective_gold,
                                 received_milestones,
                                 received_trials, received_gold, received_fame, received_prestige, received_essence,
                                 gold_transaction_id) = player
                                field = f"{player_name}'s {character_name}: \r\n"
                                await cursor.execute(
                                    "SELECT True_Character_Name, milestones, trials, Fame, Prestige, Thread_ID from Player_Characters WHERE Character_Name = ? OR Nickname = ?",
                                    (character_name, character_name))
                                player_info = await cursor.fetchone()
                                if not player_info:
                                    field += f"Character {character_name} not found. \r\n"
                                else:
                                    (true_character_name, milestones, trials, fame, prestige, thread_id) = player_info
                                    remove_rewards = await session_reward_reversal(
                                        interaction=interaction,
                                        session_id=session_id,
                                        character_name=character_name,
                                        author_name=gm_name,
                                        session_level=level,
                                        session_info=player,
                                        session_gold=received_gold,
                                        source="Session Reward")
                                    if isinstance(remove_rewards, str):
                                        field += "failed to remove rewards, skipping adjustment. \r\n "
                                    else:
                                        add_rewards = await session_reward_calculation(
                                            interaction=interaction,
                                            session_id=session_id,
                                            character_name=character_name,
                                            author_name=gm_name,
                                            session_level=level,
                                            source="Session Adjustment",
                                        )
                                        numeric_fields = ['milestone_change', 'milestones_total',
                                                          'milestones_remaining',
                                                          'trial_change', 'trials', 'trials_remaining',
                                                          'gold_change',
                                                          'essence_change', 'fame_change', 'prestige_change']
                                        for field in numeric_fields:
                                            a_value = getattr(add_rewards, field)
                                            r_value = getattr(remove_rewards, field)
                                            new_value = safe_add(a_value, r_value)
                                            setattr(add_rewards, field, new_value)
                                        await shared_functions.log_embed(change=add_rewards, guild=guild,
                                                                         thread=thread_id, bot=self.bot)
                                        await shared_functions.character_embed(
                                            character_name=character_name,
                                            guild=guild)
                                        field += f"Rewards adjusted for {character_name}. \r\n"
                                        if idx < 20:
                                            embed.add_field(name=f"{player_name}'s {character_name}",
                                                            value=field, inline=False)
                                        elif idx == 21:
                                            embed.add_field(name=f"Additional Players",
                                                            value="Additional players have been adjusted, please check the session log for more information.",
                                                            inline=False)
                            await interaction.followup.send(embed=embed)
            except (aiohttp.ClientError, aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"an error occurred for {interaction.user.name} whilst adjusting session with ID {session_id}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst adjusting session with ID '{session_id}' Error: {e}.", ephemeral=True)

    settings_group = discord.app_commands.Group(
        name='settings',
        description='Database Settings commands',
        parent=admin_group
    )

    @settings_group.command(name="ubb_inventory", description="Display a unbelievaboat player's inventory")
    async def ubb_inventory(self, interaction: discord.Interaction, player: discord.Member):
        """Display a player's inventory to identify their owned items and set the serverside items for pouches, milestones, and other"""
        guild_id = interaction.guild_id
        client = unbelievaboat.Client(os.getenv('UBB_TOKEN'))
        try:
            shop = await client.get_inventory_items_all(guild_id, player.id)
            if shop is not None:
                embed = discord.Embed(title=f"UBB Inventory", description=f'UBB inventory',
                                      colour=discord.Colour.blurple())
                for idx, item in enumerate(shop.items):
                    if idx <= 20:
                        embed.add_field(name=f'**new item**', value=f'{item}', inline=False)
                    if idx == 21:
                        embed.add_field(name=f'**Additional Items**',
                                        value=f'Additional items exist, please narrow down the inventory for more information. Yes I could paginate this. No. I will not. Use a Dummy player with less items',
                                        inline=False)
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"This player does not have any items in their inventory.")
        except unbelievaboat.errors.HTTPError as e:
            logging.exception(f"An error occurred whilst trying to get the inventory for {player.name}: {e}")
            await interaction.followup.send(
                f"An error occurred whilst trying to get the inventory for {player.name}: {e}")

    @settings_group.command(name='display',
                            description='Display server settings')
    @app_commands.autocomplete(setting=shared_functions.settings_autocomplete)
    async def display(self, interaction: discord.Interaction, setting: typing.Optional[str],
                      page_number: int = 1):
        """Display server setting information. This is used to know to where key server settings are pointing to."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)

        try:
            async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
                cursor = await conn.cursor()

                # Decide which query to execute based on whether 'name' is provided
                await cursor.execute("SELECT COUNT(Search) FROM Admin")
                item_count = await cursor.fetchone()
                (item_count,) = item_count
                if setting:
                    view_type = 2
                    await cursor.execute("SELECT Identifier from Player_Characters where Identifier = ?",
                                         (setting,))
                    setting = await cursor.fetchone()
                    if not setting:
                        await interaction.followup.send(
                            f"Character '{setting}' not found.",
                            ephemeral=True
                        )
                        return
                    else:
                        await cursor.execute(
                            "SELECT Identifier from Admin ORDER BY True_Character_Name asc")
                        results = await cursor.fetchall()
                        offset = results.index(character[0]) + 1
                else:
                    view_type = 1

                # Set up pagination variables
                page_number = min(max(page_number, 1), math.ceil(item_count / 20))
                items_per_page = 20 if view_type == 1 else 1
                offset = (page_number - 1) * items_per_page if view_type == 1 else offset

                # Create and send the view with the results
                view = SettingDisplayView(
                    user_id=interaction.user.id,
                    guild_id=guild_id,
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

    @settings_group.command(name='update',
                            description='update server settings')
    @app_commands.autocomplete(setting=shared_functions.settings_autocomplete)
    async def update_setting(self, interaction: discord.Interaction, setting: str, revision: str):
        """This allows the admin to adjust a serverside setting"""
        guild_id = interaction.guild_id
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await interaction.response.defer(thinking=True)
                if not setting:
                    await interaction.followup.send(f"cannot replace a search key with None")
                elif not revision:
                    await interaction.followup.send(f"Yeah... that would break shit, no")
                else:
                    await cursor.execute(
                        "Select Search, Type, Identifier, Description FROM Admin where Identifier = '{identifier}'")
                    information = await cursor.fetchone()
                    if information:
                        if information[1] == 'Channel':
                            revision = int(revision)
                            channel = interaction.guild.get_channel(revision)
                            if not channel:
                                channel = interaction.guild.fetch_channel(revision)
                            if not channel:
                                await interaction.followup.send("Error: Could not find the requested channel.")
                                return
                        elif information[2] == 'level':
                            await cursor.execute("SELECT Max(Level) from Milestone_System")
                            max_level = await cursor.fetchone()
                            if int(revision) > max_level[0]:
                                await interaction.followup.send(
                                    f"Your server does not have a milestone system for above level {max_level[0]}")
                                return
                        elif information[2] == 'Tier':
                            await cursor.execute("SELECT Max(Tier) from AA_Trials")
                            max_tier = await cursor.fetchone()
                            if int(revision) > max_tier[0]:
                                await interaction.followup.send(
                                    f"Your server does not have a milestone system for above tier {max_tier[0]}")
                                return
                        elif information[1] == 'UBB':
                            client = unbelievaboat.Client(os.getenv('UBB_TOKEN'))
                            item = await client.get_store_item(guild_id, int(revision))
                            if not item:
                                await interaction.followup.send("Error: Could not find the requested item.")
                                return
                        await cursor.execute("Update Admin set Identifier = ? WHERE Search = ?", (setting, revision))
                        await conn.commit()
                    else:
                        await interaction.followup.send('The identifier you have supplied is incorrect.')
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"An error occurred whilst updating data! input values of setting: {setting}, revision: {revision}': {e}"
                )
                await interaction.followup.send(
                    f"An error occurred whilst updating data. Please try again later.",
                    ephemeral=True
                )

    @settings_group.command(name='level_cap', description='command for adjusting the level cap of the server')
    async def level_cap(self, interaction: discord.Interaction, new_level: int):
        """This allows the admin to adjust the server wide level cap"""
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute("SELECT MIN(level), MAX(level) from Milestone_System")
                level_minmax = await cursor.fetchone()
                if new_level < level_minmax[0]:
                    await interaction.followup.send(
                        f"Your server does not have a milestone system for below level {level_minmax[0]}")
                elif new_level > level_minmax[1]:
                    await interaction.followup.send(
                        f"Your server does not have a milestone system for above level {level_minmax[1]}")
                else:
                    await cursor.execute("Select minimum_milestones FROM Milestone_System where Level = ?",
                                         (new_level,))
                    new_level_info = await cursor.fetchone()
                    if new_level_info:
                        minimum_milestones = new_level_info[0]
                        await cursor.execute(
                            "SELECT True_Character_Name, Character_Name, Level, Milestones, Tier, Trials, personal_cap FROM Player_Characters WHERE Milestones >= ?",
                            (minimum_milestones,))
                        characters_to_adjust = await cursor.fetchall()
                        if characters_to_adjust:
                            cap_embed = discord.Embed(title=f"Level Cap Adjustment",
                                                      description=f'{interaction.user.name} Adjusting the level cap to {new_level}')
                            for idx, character in enumerate(characters_to_adjust):
                                try:
                                    (true_character_name, character_name, character_level, milestones, tier, trials,
                                     personal_cap) = character
                                    level_adjustment = await character_commands.level_calculation(
                                        character_name=character_name,
                                        level=character_level,
                                        guild=guild,
                                        guild_id=guild_id,
                                        personal_cap=personal_cap,
                                        base=milestones,
                                        easy=0,
                                        medium=0,
                                        hard=0,
                                        deadly=0,
                                        misc=0)
                                    (new_level,
                                     total_milestones,
                                     min_milestones,
                                     milestones_to_level,
                                     milestones_required,
                                     awarded_total_milestones) = level_adjustment
                                    mythic_adjustment = await character_commands.mythic_calculation(
                                        guild_id=guild_id,
                                        character_name=character_name,
                                        level=new_level,
                                        trials=trials,
                                        trial_change=0)
                                    (new_tier, total_trials, trials_required, trial_change) = mythic_adjustment
                                    character_updates = shared_functions.update_character_data(
                                        character_name=character_name,
                                        level_package=(new_level, total_milestones, milestones_to_level),
                                    )
                                    character_changes = shared_functions.CharacterChange(
                                        character_name=character_name,
                                        author=interaction.user.name,
                                        level=new_level,
                                        milestones_total=total_milestones,
                                        milestone_change=awarded_total_milestones,
                                        milestones_remaining=min_milestones,
                                        source=f"admin adjusted level cap to {new_level}")
                                    if new_tier != tier:
                                        character_updates.trial_package = (new_tier, total_trials, trials_required)
                                        character_changes.tier = new_tier
                                        character_changes.trials = total_trials
                                        character_changes.trials_remaining = trials_required
                                        character_changes.trial_change = 0
                                    await shared_functions.update_character(
                                        guild_id=guild_id,
                                        change=character_updates
                                    )
                                    await shared_functions.log_embed(
                                        change=character_changes,
                                        guild=guild,
                                        thread=thread_id, bot=self.bot)
                                    await shared_functions.character_embed(
                                        character_name=character_name,
                                        guild=guild)
                                    if idx <= 20:
                                        cap_embed.add_field(
                                            name=f"{true_character_name}",
                                            value=f"{true_character_name} has been leveled up to {new_level}.",
                                            inline=False)
                                    elif idx == 21:
                                        additional_characters = true_character_name
                                    else:
                                        additional_characters += f", {true_character_name}"
                                except (aiosqlite.Error, TypeError, ValueError) as e:
                                    logging.exception(
                                        f"An error occurred whilst looping level cap! input values of: {new_level}, {true_character_name} in server {interaction.guild.id} by {interaction.user.name}: {e}"
                                    )

                            if idx >= 21:
                                cap_embed.add_field(name=f"Additional Characters",
                                                    value=f"{idx} additional characters have been adjusted.\r\n{additional_characters}",
                                                    inline=False)
                            await interaction.followup.send(embed=cap_embed)
                            logging.info(
                                f"{interaction.user.name} has adjusted the tier cap to {new_level} for {guild.name} with {idx} characters adjusted.")
                        else:
                            await interaction.followup.send(
                                f"Your server does not have any characters that meet the minimum milestone requirement for level {new_level}")
                    else:
                        await interaction.followup.send(
                            f"Your server does not have a milestone system for level {new_level}")
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"An error occurred whilst updating level cap! input values of: {new_level} in server {interaction.guild.id} by {interaction.user.name}': {e}"
                )
                await interaction.followup.send(
                    f"An error occurred whilst fetching data. Please try again later.",
                    ephemeral=True
                )

    @settings_group.command(name='tier_cap', description='command for adjusting the tier cap of the server')
    async def tier_cap(self, interaction: discord.Interaction, new_tier: int):
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute("SELECT MIN(tier), MAX(tier) from AA_Trials")
                tier_minmax = await cursor.fetchone()
                if new_tier < tier_minmax[0]:
                    await interaction.followup.send(
                        f"Your server does not have a milestone system for below tier {tier_minmax[0]}")
                elif new_tier > tier_minmax[1]:
                    await interaction.followup.send(
                        f"Your server does not have a milestone system for above tier {tier_minmax[1]}")
                else:
                    await cursor.execute("Select Trials FROM AA_Trials where Tier = ?", (tier_minmax,))
                    new_tier_info = await cursor.fetchone()
                    if new_tier_info:
                        minimum_milestones = new_tier_info[0]
                        await cursor.execute(
                            "SELECT True_Character_Name, Character_Name, Tier, Trials FROM Player_Characters WHERE Trials >= ?",
                            (minimum_milestones,))
                        characters_to_adjust = await cursor.fetchall()
                        if characters_to_adjust:
                            cap_embed = discord.Embed(title=f"Tier Cap Adjustment",
                                                      description=f'{interaction.user.name} Adjusting the tier cap to {new_tier}')
                            for idx, character in enumerate(characters_to_adjust):
                                (true_character_name, character_name, tier, trials) = character
                                mythic_adjustment = await character_commands.mythic_calculation(
                                    guild_id=guild_id,
                                    character_name=character_name,
                                    level=character_level,
                                    trials=trials,
                                    trial_change=0)
                                (new_tier, total_trials, trials_required, trial_change) = mythic_adjustment
                                character_updates = shared_functions.update_character_data(
                                    character_name=character_name,
                                    trial_package=(new_tier, total_trials, trials_required)
                                )
                                character_changes = shared_functions.CharacterChange(
                                    character_name=character_name,
                                    author=interaction.user.name,
                                    tier=new_tier,
                                    trials=total_trials,
                                    trials_remaining=trials_required,
                                    trial_change=0,
                                    source=f"admin adjusted level cap to {new_level}")
                                await shared_functions.update_character(
                                    guild_id=guild_id,
                                    change=character_updates
                                )
                                await shared_functions.log_embed(
                                    change=character_changes,
                                    guild=guild,
                                    thread=thread_id,
                                    bot=self.bot)
                                await shared_functions.character_embed(
                                    character_name=character_name,
                                    guild=guild)
                                if idx <= 20:
                                    cap_embed.add_field(name=f"{true_character_name}",
                                                        value=f"{true_character_name} has been leveled up to {new_level}.",
                                                        inline=False)
                                elif idx == 21:
                                    additional_characters = true_character_name
                                else:
                                    additional_characters += f", {true_character_name}"
                            if idx >= 21:
                                cap_embed.add_field(name=f"Additional Characters",
                                                    value=f"{idx} additional characters have been adjusted.\r\n{additional_characters}",
                                                    inline=False)
                            await interaction.followup.send(embed=cap_embed)
                            logging.info(
                                f"{interaction.user.name} has adjusted the tier cap to {new_tier} for {guild.name} with {idx} characters adjusted.")
                        else:
                            await interaction.followup.send(
                                f"Your server does not have any characters that meet the minimum trial requirement for tier {new_tier}")
                    else:
                        await interaction.followup.send(
                            f"Your server does not have a milestone system for tier {new_tier}")
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"An error occurred whilst updating tier cap! input values of: {new_tier} in server {interaction.guild.id} by {interaction.user.name}': {e}"
                )
                await interaction.followup.send(
                    f"An error occurred whilst fetching data. Please try again later.",
                    ephemeral=True
                )

    milestone_group = discord.app_commands.Group(
        name='milestone',
        description='Update the level, WPL, and other information in the milestone system',
        parent=admin_group
    )

    @milestone_group.command(name='milestones',
                             description='command for adjusting the milestone floor of a level among other things.')
    @app_commands.describe(
        level="The level you wish to adjust the milestone floor for or to add a new level into the range.")
    @app_commands.describe(
        minimum_milestones="The minimum number of milestones required to reach the level. Set as -1 to delete the level.")
    async def define_milestone(self, interaction: discord.Interaction, level: int, minimum_milestones: int):
        """This allows the admin to adjust the milestone floor of a level among other things."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute("SELECT level, minimum_milestones, wpl, wpl_heroic FROM Milestone_System WHERE Level = ?",
                                     (level - 1,))
                lower_level_info = await cursor.fetchone()
                await cursor.execute("SELECT level, minimum_milestones FROM Milestone_System WHERE Level = ?", (level,))
                center_level_info = await cursor.fetchone()
                await cursor.execute("SELECT level, minimum_milestones FROM Milestone_System WHERE Level = ?",
                                     (level + 1,))
                higher_level_info = await cursor.fetchone()
                if lower_level_info:
                    if minimum_milestones == -1:
                        lower_milestones_required = 999 if not higher_level_info else higher_level_info[1] - \
                                                                                      lower_level_info[1]
                    else:
                        (lower_level, lower_milestones) = lower_level_info
                        lower_milestones_required = minimum_milestones - lower_milestones
                        if lower_milestones_required < 0:
                            await interaction.followup.send(
                                f"Your input of level: {level} minimum_milestones: {minimum_milestones} cannot be less than level: {lower_level} minimum_milestones: {lower_milestones}.")
                            return
                    await cursor.execute("UPDATE Milestone_System SET milestones_required = ? WHERE Level = ?",
                                         (lower_milestones_required, lower_level_info[0]))
                    await conn.commit()
                if higher_level_info:
                    (higher_level, higher_milestones) = higher_level_info
                    if minimum_milestones > higher_milestones:
                        await interaction.followup.send(
                            f"Your input of level: {level} minimum_milestones: {minimum_milestones} cannot be more than level: {higher_level} minimum_milestones: {higher_milestones}.")
                        return
                    center_milestones_required = higher_milestones - minimum_milestones
                else:
                    center_milestones_required = 99999
                if center_level_info:
                    if minimum_milestones == -1:
                        await cursor.execute("DELETE FROM Milestone_System WHERE Level = ?", (level,))
                        await interaction.followup.send(f"Level of {level} removed from milestone system.")
                    else:
                        await cursor.execute("UPDATE Milestone_System SET milestones_required = ? WHERE Level = ?",
                                             (center_milestones_required, level))
                        await interaction.followup.send(f"Level of {level} updated in milestone system.")
                else:
                    wpl = 0 if not lower_level_info else lower_level_info[2]
                    wpl_heroic = 0 if not lower_level_info else lower_level_info[3]
                    await cursor.execute("INSERT INTO Milestone_System (Level, Milestones_Required, WPL, WPL_Heroic) VALUES (?, ?, ?, ?)",
                                         (level, center_milestones_required, wpl, wpl_heroic))
                    await interaction.followup.send(f"Level of {level} added to milestone system. PLEASE REMEMBER TO UPDATE WPL VALUES.")
                await conn.commit()
                center_milestones_range = minimum_milestones if minimum_milestones != -1 else center_level_info[1]
                upper_milestone_range = 99999 if not higher_level_info else higher_level_info[1]
                await cursor.execute("Select character_name, level, milestones, trials, personal_cap FROM Player_Characters WHERE ? < Minimum_Milestones < ?",(center_milestones_range, upper_milestone_range))
                characters_to_adjust = await cursor.fetchall()
                for character in characters_to_adjust:
                    (character_name, level, milestones, trials, personal_cap) = character
                    level_adjustment = await character_commands.level_calculation(
                        character_name=character_name,
                        level=level,
                        guild=guild,
                        guild_id=guild_id,
                        personal_cap=personal_cap,
                        base=milestones,
                        easy=0,
                        medium=0,
                        hard=0,
                        deadly=0,
                        misc=0)
                    (new_level,
                     total_milestones,
                     min_milestones,
                     milestones_to_level,
                     milestones_required,
                     awarded_total_milestones) = level_adjustment
                    mythic_adjustment = await character_commands.mythic_calculation(
                        guild_id=guild_id,
                        character_name=character_name,
                        level=new_level,
                        trials=trials,
                        trial_change=0)
                    (new_tier, total_trials, trials_required, trial_change) = mythic_adjustment
                    character_updates = shared_functions.update_character_data(
                        character_name=character_name,
                        level_package=(new_level, total_milestones, milestones_to_level),
                    )
                    character_changes = shared_functions.CharacterChange(
                        character_name=character_name,
                        author=interaction.user.name,
                        level=new_level,
                        milestones_total=total_milestones,
                        milestone_change=awarded_total_milestones,
                        milestones_remaining=min_milestones,
                        source=f"admin adjusted level cap to {new_level}")
                    if new_tier != tier:
                        character_updates.trial_package = (new_tier, total_trials, trials_required)
                        character_changes.tier = new_tier
                        character_changes.trials = total_trials
                        character_changes.trials_remaining = trials_required
                        character_changes.trial_change = 0
                    await shared_functions.update_character(
                        guild_id=guild_id,
                        change=character_updates
                    )
                    await shared_functions.log_embed(
                        change=character_changes,
                        guild=guild,
                        thread=thread_id, bot=self.bot)
                    await shared_functions.character_embed(
                        character_name=character_name,
                        guild=guild)

            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"An error occurred whilst milestones! input values of: level: {level}, minimum_milestones{minimum_milestones} in server {interaction.guild.id} by {interaction.user.name}': {e}"
                )
                await interaction.followup.send(
                    f"An error occurred whilst fetching data. Please try again later.",
                    ephemeral=True
                )

    @milestone_group.command(name='wpl',
                             description='command for adjusting the wealth per level and heroic WPL of a level.')
    async def define_wpl(self, interaction: discord.Interaction, level: int, wpl: int, wpl_heroic: int):
        """This allows the admin to adjust the milestone floor of a level among other things."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute("SELECT Level, WPL, WPL_Heroic FROM Milestone_System WHERE Level = ?", (level,))
                center_level_info = await cursor.fetchone()
                if center_level_info:
                    await cursor.execute("SELECT Level, WPL, WPL_Heroic FROM Milestone_System WHERE Level = ?",
                                         (level - 1,))
                    lower_level_info = await cursor.fetchone()
                    await cursor.execute("SELECT Level, WPL, WPL_Heroic FROM Milestone_System WHERE Level = ?",
                                         (level + 1,))
                    higher_level_info = await cursor.fetchone()
                    if lower_level_info:
                        (lower_level, lower_wpl, lower_wpl_heroic) = lower_level_info
                        if wpl < lower_wpl or wpl_heroic < lower_wpl_heroic:
                            await interaction.followup.send(
                                f"Your input of level: {level} WPL: {wpl} wpl_heroic: {wpl_heroic} cannot be less than level: {lower_level} WPL: {lower_wpl} Heroic WPL: {lower_wpl_heroic}.")
                            return
                    if higher_level_info:
                        (higher_level, higher_wpl, higher_wpl_heroic) = higher_level_info
                        if wpl > higher_wpl or wpl_heroic < higher_wpl_heroic:
                            await interaction.followup.send(
                                f"Your input of level: {level} WPL: {wpl} wpl_heroic: {wpl_heroic} cannot be less than level: {higher_level} WPL: {higher_wpl} Heroic WPL: {higher_wpl_heroic}.")
                            return
                    await cursor.execute("UPDATE Milestone_System SET WPL = ?, WPL_Heroic = ? WHERE Level = ?",
                                         (wpl, wpl_heroic, level))
                else:
                    await interaction.followup.send(
                        f"Your server does not have a milestone system for level {level}")
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"An error occurred whilst milestones! input values of: level: {level}, minimum_milestones{minimum_milestones} in server {interaction.guild.id} by {interaction.user.name}': {e}"
                )
                await interaction.followup.send(
                    f"An error occurred whilst fetching data. Please try again later.",
                    ephemeral=True
                )

    @milestone_group.command(name='jobs', description='command for adjusting the job rewards for a session.')
    async def define_jobs(self, interaction: discord.Interaction, easy: discord.Optional[int],
                          medium: discord.Optional[int], hard: discord.Optional[int], deadly: discord.Optional[int]):
        """This allows the admin to adjust the milestone floor of a level among other things."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute("SELECT easy, medium, hard, deadly FROM Milestone_System WHERE Level = ?",
                                     (level,))
                level_info = await cursor.fetchone()
                if level_info:
                    (info_easy, info_medium, info_hard, info_deadly) = level_info
                    new_easy = easy if easy is not None else info_easy
                    new_medium = medium if medium is not None else info_medium
                    new_hard = hard if hard is not None else info_hard
                    new_deadly = deadly if deadly is not None else info_deadly
                    if new_easy < 0 or new_medium < 0 or new_hard < 0 or new_deadly < 0:
                        await interaction.followup.send(
                            "Why do you hate your players so fucking much that you want to have them get a negative reward on a job?!")
                    elif new_easy < new_medium or new_medium < new_hard or new_hard < new_deadly:
                        await interaction.followup.send(
                            f"Please give your players higher rewards on more punishing jobs. the punishment is the job. \r\n Easy: {new_easy}, Medium: {new_medium}, Hard: {new_hard}, Deadly: {new_deadly}")
                    else:
                        await cursor.execute(
                            "Update Milestone_System SET Easy = ?, Medium = ?, Hard = ?, Deadly = ? where level = ?",
                            (new_easy, new_medium, new_hard, new_deadly, level))
                        await cursor.commit()
                        await interaction.followup.send(
                            f"Successfully updated level: {level} to have the following rewards \r\n Easy: {new_easy}, Medium: {new_medium}, Hard: {new_hard}, Deadly: {new_deadly}")
                else:
                    await interaction.followup.send(f"Your server does not have a milestone system for level {level}")
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"An error occurred whilst milestones! input values of: level: {level}, minimum_milestones{minimum_milestones} in server {interaction.guild.id} by {interaction.user.name}': {e}"
                )
                await interaction.followup.send(
                    f"An error occurred whilst fetching data. Please try again later.",
                    ephemeral=True
                )

    @milestone_group.command(name='display',
                             description='Display milestone settings')
    @app_commands.autocomplete(setting=shared_functions.settings_autocomplete)
    async def display_milestones(self, interaction: discord.Interaction, page_number: int = 1):
        """Display Milestone Information and further context about levels."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)

        try:
            async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as conn:
                cursor = await conn.cursor()

                # Decide which query to execute based on whether 'name' is provided
                await cursor.execute("SELECT COUNT(level) FROM Milestone_System")
                item_count = await cursor.fetchone()
                item_count = item_count[0]

                # Set up pagination variables
                page_number = min(max(page_number, 1), math.ceil(item_count / 20))
                items_per_page = 20
                offset = (page_number - 1) * items_per_page

                # Create and send the view with the results
                view = MilestoneDisplayView(
                    user_id=interaction.user.id,
                    guild_id=guild_id,
                    limit=items_per_page,
                    offset=offset,
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


"""@admin.command()
@app_commands.describe(certainty="is life short?")
@app_commands.choices(
    certainty=[discord.app_commands.Choice(name='YOLO', value=1), discord.app_commands.Choice(name='No', value=2)])
async def reset_database(interaction: discord.Interaction, certainty: discord.app_commands.Choice[int]):
    "Perform a database reset, remember to reassign role ranges and server settings!"
    if certainty == 1:
        certainty = 1
    else:
        certainty = certainty.value
    if certainty.value == 1:
        guild_id = interaction.guild_id
        buttons = ["✅", "❌"]  # checkmark X symbol
        embed = discord.Embed(title=f"Are you sure you want to reset the server database??",
                              description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
        await interaction.followup.send(embed=embed)
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
                if reaction.emoji == u"\u264C":
                    embed = discord.Embed(title=f"You have thought better of freely giving your money",
                                          description=f"Savings!", colour=discord.Colour.blurple())
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                if reaction.emoji == u"\u2705":
                    embed = discord.Embed(title=f"Database Reset has occurred!",
                                          description=f"Say Farewell to a world you used to know.",
                                          colour=discord.Colour.red())
                    await msg.clear_reactions()
                    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    shutil.copyfile(f"C:/pathparser/pathparser_{guild_id}.sqlite",
                                    f"C:/pathparser/pathparser_{guild_id}_{time}.sqlite")
                    shutil.copyfile(f"C:/pathparser/pathparser.sqlite", f"C:/pathparser/pathparser_{guild_id}.sqlite")
                    await msg.edit(embed=embed)
    else:
        await interaction.followup.send(f"I'M FIRING MY LAS--- What?")


@admin.command()
@app_commands.describe(player_wipe="if yes, remove all inactive players!")
@app_commands.choices(
    player_wipe=[discord.app_commands.Choice(name='No!', value=1), discord.app_commands.Choice(name='Yes!', value=2)])
async def clean_playerbase(interaction: discord.Interaction, player: typing.Optional[discord.Member],
                           player_id: typing.Optional[int], player_wipe: discord.app_commands.Choice[int] = 1):
    "Clean out the entire playerbase or clean out a specific player's character by mentioning them or using their role!"
    if player_wipe == 1:
        player_wipe = 1
    else:
        player_wipe = player_wipe.value
    if player_wipe == 1 and player_id is None and player is None:
        await interaction.followup.send(f"Pick Something that lets me end someone! Please?", ephemeral=True)
    else:
        guild_id = interaction.guild_id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = interaction.user.name
        overall_wipe_list = []
        embed = discord.Embed(title=f"The Following Players will have their characters removed:",
                              description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
        if player_id is not None:
            cursor.execute(
                "Select distinct(Player_Name), count(Character_Name) from Player_Characters where Player_ID = {player_id}")
            player_id_info = cursor.fetchone()
            if player_id_info is not None:
                overall_wipe_list.append(player_id)
                embed.add_field(name=f"{player_id_info[0]}'s characters will be removed",
                                value=f"this player had {player_id_info[1]} characters!")
            else:
                embed.add_field(name=f"{player_id} could not be found in the database.",
                                value=f"This ID had no characters associated with it..")
        if player is not None:
            cursor.execute(
                "Select distinct(Player_Name), count(Character_Name) from Player_Characters where Player_ID = {player.id}")
            player_id_info = cursor.fetchone()
            if player_id_info is not None:
                embed.add_field(name=f"{player_id_info}'s characters will be removed",
                                value=f"This player had {player_id_info[2]} characters who will be removed.")
                overall_wipe_list.append(player.id)
            else:
                embed.add_field(name=f"{player.name} could not be found in the database.",
                                value=f"This user had no characters associated with it..")
        if player_wipe == 2:
            guild = interaction.guild
            cursor.execute("Select distinct(Player_ID), count(Character_Name) from Player_Characters")
            player_id_info = cursor.fetchall()
            wipe_tuple = None
            x = 0
            for inactive_player in player_id_info:
                member = guild.get_member(inactive_player[0])
                if member is None:
                    x += 1
                    overall_wipe_list.append(inactive_player[0])
                    if x <= 20:
                        embed.add_field(name=f"{player_id_info[0]}'s characters will be removed",
                                        value=f"this player had {player_id_info[1]} characters!")
                else:
                    x = x
                    wipe_tuple = wipe_tuple
            embed.set_footer(text=f"{x} Total Players were inactive and are being removed!")
        else:
            embed.add_field(name=f"No Player Characters could be found in the database.",
                            value=f"This ID had no characters associated with it..")
        guild_id = interaction.guild_id
        buttons = ["✅", "❌"]  # checkmark X symbol
        await interaction.followup.send(embed=embed)
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
                if reaction.emoji == u"\u264C":
                    embed = discord.Embed(title=f"You have thought better of freely giving your money",
                                          description=f"Savings!", colour=discord.Colour.blurple())
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                if reaction.emoji == u"\u2705":
                    embed = discord.Embed(title=f"Database Reset has occurred!",
                                          description=f"Say Farewell to a world you used to know.",
                                          colour=discord.Colour.red())
                    await msg.clear_reactions()
                    await msg.edit(embed=embed)
                    for wiped in overall_wipe_list:
                        await Event.wipe_unapproved(self, wiped[0], guild_id, author)


@admin.command()
@app_commands.autocomplete(character_name=stg_character_select_autocompletion)
@app_commands.describe(
    cleanse="Optional: supply a number ending with D or W to remove users who have not been accepted within that period!")
@app_commands.describe(status="Accepted players are moved into active and posted underneath!")
@app_commands.choices(status=[discord.app_commands.Choice(name='Accepted!', value=1),
                              discord.app_commands.Choice(name='Rejected!', value=2)])
async def manage(interaction: discord.Interaction, character_name: str, player_id: typing.Optional[int],
                 status: discord.app_commands.Choice[int] = 1, cleanse: str = None):
    "accept a player into your accepted bios, or clean out the stage tables!"
    guild = interaction.guild
    guild_id = interaction.guild_id
    if status == 1:
        status = 1
    else:
        status = status.value
    if character_name is None and cleanse is None:
        await interaction.followup.send(f"NOTHING COMPLETED, RUN DURATION: 1 BAJILLION Eternities?", ephemeral=True)
    elif cleanse is not None or character_name is not None and status == 2 or player_id is not None and status == 2:
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = interaction.user.name
        if status == 2:
            overall_wipe_list = []
            character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
            embed = discord.Embed(title=f"The Following Players will have their staged characters removed:",
                                  description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
            if character_name is not None:
                cursor.execute(
                    "Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where character_name = ?",
                    (character_name,))
                player_id_info = cursor.fetchone()
                if player_id_info is not None:
                    overall_wipe_list.append(character_name)
                    embed.add_field(name=f"{player_id_info[0]}'s character will be removed from stage",
                                    value=f"The character of {character_name} will be removed!")
                else:
                    embed.add_field(name=f"{character_name} could not be found in the database.",
                                    value=f"This character name had no characters associated with it.")
            if cleanse is not None:
                if cleanse.endswith('D'):
                    cleanse = cleanse.replace('D', '')
                    cursor.execute(
                        "Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where Created_Date <= date('now', '-{cleanse} days')")
                    player_id_info = cursor.fetchall()
                    x = 0
                    for inactive_player in player_id_info:
                        x += 1
                        overall_wipe_list.append(inactive_player[0])
                        if x <= 20:
                            embed.add_field(name=f"{player_id_info[0]}'s characters will be removed",
                                            value=f"this player had {player_id_info[1]} characters!")
                    embed.set_footer(text=f"{x} Total Players were inactive and are being removed!")
                elif cleanse.endswith('W'):
                    cleanse = cleanse.replace('W', '')
                    cursor.execute(
                        "Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where Created_Date <= date('now', '-{cleanse} weeks')")
                    player_id_info = cursor.fetchall()
                    x = 0
                    for inactive_player in player_id_info:
                        x += 1
                        overall_wipe_list.append(inactive_player[0])
                        if x <= 20:
                            embed.add_field(name=f"{player_id_info[0]}'s characters will be removed",
                                            value=f"this player had {player_id_info[1]} characters!")
                    embed.set_footer(text=f"{x} Total Players were inactive and are being removed!")
                else:
                    embed.add_field(name=f"Invalid Duration",
                                    value=f"Please use a number ending in D for days or W for weeks.")
            buttons = ["✅", "❌"]  # checkmark X symbol
            await interaction.followup.send(embed=embed)
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
                    if reaction.emoji == "❌":
                        embed = discord.Embed(title=f"you have reconsidered wiping a character",
                                              description=f"life is a kindness, do not waste it!",
                                              colour=discord.Colour.blurple())
                        await msg.edit(embed=embed)
                        await msg.clear_reactions()
                    if reaction.emoji == u"\u2705":
                        embed = discord.Embed(title=f"Character wipe has been approved!",
                                              description=f"Getting rid of outdated characters.",
                                              colour=discord.Colour.red())
                        await msg.clear_reactions()
                        await msg.edit(embed=embed)
                        print(overall_wipe_list)
                        print(type(overall_wipe_list))
                        for wiped in overall_wipe_list:
                            await Event.wipe_unapproved(self, wiped, guild_id, author)
    else:
        e = None
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)
        except Exception as e:
            print(e)
            pass
        guild_id = interaction.guild_id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = interaction.user.name
        character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
        cursor.execute("Select True_Character_Name, tmp_bio from A_STG_Player_Characters where character_name = ?",
                       (character_name,))
        player_id_info = cursor.fetchone()
        if player_id_info is not None:
            try:
                e = None
                await Event.create_bio(self, guild_id, player_id_info[0], player_id_info[1])
            except Exception as e:
                print(e)
                pass
            await Event.create_character(self, guild_id, author, player_id_info[0])
            cursor.execute("Select Search FROM Admin WHERE Identifier = 'Approved_Character'")
            approved_character = cursor.fetchone()
            cursor.execute("Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute("Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            cursor.execute(
                "Select Player_Name, True_Character_Name, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_Value_Max, Mythweavers, Image_Link, Color, Essence, Player_ID, Oath, Article_Link FROM Player_Characters WHERE Character_Name = ?",
                (character_name,))
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
            embed = discord.Embed(title=f"{character_info[1]}", url=f'{character_info[13]}',
                                  description=f"{description_field}", color=int_color)
            embed.set_author(name=f'{character_info[0]}')
            embed.set_thumbnail(url=f'{character_info[14]}')
            embed.add_field(name="Information", value=f'**Level**: 3, **Mythic Tier**: 0, **Fame**: 0', inline=False)
            embed.add_field(name="Experience", value=f'**Milestones**: 0, **Remaining**: 3')
            embed.add_field(name="Mythic", value=f'**Trials**: 0, **Remaining**: 0')
            embed.add_field(name="Current Wealth", value=f'**GP**: {character_info[10]}', inline=False)
            embed.add_field(name="Current Essence", value=f'**Essence**: 0')
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
            bio_message = await bio_channel.send(content=mentions, embed=embed,
                                                 allowed_mentions=discord.AllowedMentions(users=True))
            embed = discord.Embed(title=f"{character_info[1]}", url=f'{character_info[13]}',
                                  description=f"Other Names: {character_info[2]}", color=int_color)
            embed.set_author(name=f'{character_info[0]}')
            embed.set_thumbnail(url=f'{character_info[14]}')
            character_log_channel = await bot.fetch_channel(character_log_channel_id[0])
            character_log_message = await character_log_channel.send(content=mentions, embed=embed,
                                                                     allowed_mentions=discord.AllowedMentions(
                                                                         users=True))
            thread = await character_log_message.create_thread(name=f'{character_info[1]}')
            await Event.log_character(self, guild_id, character_name, bio_message.id, character_log_message.id,
                                      thread.id)
            if e is None:
                await interaction.followup.send(content=f"{character_name} has been accepted into the server!")
            else:
                interaction.send(f"{character_name} has been accepted into the server!")
        else:
            if e is None:
                await interaction.followup.send(f"{character_name} could not be found in the database.", ephemeral=True)
            else:
                interaction.send(f"{character_name} has been accepted into the server!")


@admin.command()
@app_commands.autocomplete(character_name=character_select_autocompletion)
@app_commands.describe(destination="Shorthand for determining whether you are looking for a character name or nickname")
@app_commands.choices(destination=[discord.app_commands.Choice(name='Tradition', value=1),
                                   discord.app_commands.Choice(name='Template', value=2)])
@app_commands.describe(customized_name="For the name of the template or tradition")
async def customize(interaction: discord.Interaction, character_name: str, destination: discord.app_commands.Choice[int],
                    customized_name: str, link: str, essence_cost: int = 0):
    "Administrative: set a character's template or tradition!"
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = interaction.guild_id
    guild = interaction.guild
    if destination == 1:
        destination = 1
    else:
        destination = destination.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = interaction.user.name
    cursor.execute(
        "Select Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Essence, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?",
        (character_name,))
    player_info = cursor.fetchone()

    if player_info is None:
        await interaction.followup.send(f"no character with the Name or Nickname of {character_name} could be found!",
                                        ephemeral=True)
    else:
        destination_name = 'Tradition_Name' if destination == 1 else 'Template_Name'
        destination_link = 'Tradition_Link' if destination == 1 else 'Template_Link'
        destination_name_pretty = 'Tradition Name' if destination == 1 else 'Template Name'
        tradition_name = customized_name if destination == 1 else None
        tradition_link = link if destination == 1 else None
        template_name = customized_name if destination == 2 else None
        template_link = link if destination == 2 else None
        essence_remaining = player_info[16] - essence_cost
        await Event.customize_characters(self, guild_id, author, player_info[3], destination_name, destination_link,
                                         customized_name, link, essence_remaining, essence_cost)
        embed = discord.Embed(title=f"{destination_name_pretty} change for {player_info[3]}",
                              description=f"<@{player_info[1]}>'s {player_info[3]} has spent {essence_cost} essence leaving them with {player_info[16] - essence_cost} essence!",
                              colour=discord.Colour.blurple())
        embed.add_field(name=f'**{destination_name_pretty} Information:**', value=f'[{customized_name}](<{link}>)',
                        inline=False)
        cursor.execute("Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
        accepted_bio_channel = cursor.fetchone()
        cursor.execute("Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
        character_log_channel_id = cursor.fetchone()
        cursor.close()
        db.close()
        bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5],
                                    player_info[6], player_info[7], player_info[8], player_info[9], player_info[10],
                                    player_info[11], player_info[12], player_info[13], player_info[14],
                                    player_info[16] + essence_cost, player_info[17], player_info[18], player_info[19],
                                    player_info[20], player_info[21], player_info[22], player_info[23], player_info[27],
                                    player_info[28], player_info[30], player_info[31])
        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
        bio_message = await bio_channel.fetch_message(player_info[24])
        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
        source = f"changed a template or tradition for {character_name}"
        logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, None, None,
                                  None, None, player_info[16] - essence_cost, essence_cost, tradition_name, tradition_link,
                                  template_name, template_link, None, None, None, None, None, source)
        logging_thread = guild.get_thread(player_info[25])
        await logging_thread.send(embed=logging_embed)
        await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))


@admin.command()
@app_commands.describe(modify="add, remove edit, or display something in the store.")
@app_commands.choices(
    modify=[discord.app_commands.Choice(name='Display', value=1), discord.app_commands.Choice(name='Add', value=2),
            discord.app_commands.Choice(name='Edit', value=3), discord.app_commands.Choice(name='Remove', value=4)])
async def fame_store(interaction: discord.Interaction, name: str, fame_required: typing.Optional[int],
                     prestige_cost: typing.Optional[int], effect: typing.Optional[str], limit: typing.Optional[int],
                     modify: discord.app_commands.Choice[int] = 1):
    "add, edit, remove, or display something from one of the stores"
    guild_id = interaction.guild_id
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
    author = interaction.user.name
    cursor.execute("Select Fame_Required, Prestige_Cost, Effect, Use_Limit FROM Store_Fame where Name = ?", (name,))
    item_info = cursor.fetchone()
    cursor.close()
    db.close()
    if item_info is None and modify == 2:
        await Event.add_fame_store(self, guild_id, author, fame_required, prestige_cost, name, effect, limit)
        embed = discord.Embed(title=f"New Fame Store Item", description=f'{name} has been added to the fame store!',
                              colour=discord.Colour.blurple())
        embed.add_field(name=f'**Cost:**',
                        value=f'Requires {fame_required} fame, Costs: {prestige_cost} prestige, Limited to {limit}',
                        inline=False)
        embed.add_field(name=f'**Effect:**', value=f'{effect}', inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 3:
        await Event.remove_fame_store(self, guild_id, author, name)
        embed = discord.Embed(title=f"Removed Fame Store Item",
                              description=f'{name} has been removed from the fame store!',
                              colour=discord.Colour.blurple())
        await interaction.followup.send(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 4:
        await Event.edit_fame_store(self, guild_id, author, fame_required, prestige_cost, name, effect, limit)
        embed = discord.Embed(title=f"Edited Fame Store Item", description=f'{name} has been edited in the fame store!',
                              colour=discord.Colour.blurple())
        embed.add_field(name=f'**Cost:**',
                        value=f'Requires {fame_required} fame, Costs: {prestige_cost} prestige, Limited to {limit}',
                        inline=False)
        embed.add_field(name=f'**Effect:**', value=f'{effect}', inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    elif modify == 1:
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(
            "Select Fame_Required, Prestige_Cost, Name, Effect, Use_Limit FROM Store_Fame where Name = ?", (name,))
        item_info = cursor.fetchone()
        if item_info is not None:
            embed = discord.Embed(
                title=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}',
                colour=discord.Colour.blurple())
            await interaction.followup.send(embed=embed)
        else:
            buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
            cursor.execute("Select COUNT(Name) FROM Store_Fame")
            admin_count = cursor.fetchone()
            max_page = math.ceil(admin_count[0] / 20)
            current_page = 1
            low = 1 + ((current_page - 1) * 20)
            high = 20 + ((current_page - 1) * 20)
            cursor.execute(
                "Select Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}")
            pull = cursor.fetchall()
            embed = discord.Embed(title=f"Fame Store Settings Page {current_page}",
                                  description=f'This is a list of the administratively defined items',
                                  colour=discord.Colour.blurple())
            for result in pull:
                embed.add_field(name=f'**Name**: {result[1]}',
                                value=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}',
                                inline=False)
            await interaction.followup.send(embed=embed)
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
                            "Select Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}")
                        pull = cursor.fetchall()
                        embed = discord.Embed(title=f"Fame Store Settings Page {current_page}",
                                              description=f'This is a list of the administratively defined items',
                                              colour=discord.Colour.blurple())
                        for result in pull:
                            embed.add_field(name=f'**Name**: {result[1]}',
                                            value=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}',
                                            inline=False)
                        await msg.edit(embed=embed)
    else:
        await interaction.followup.send(
            f"you were trying to do the following {modify} modification in the Fame Store, but {name} was incorrect!",
            ephemeral=True)


@admin.command()
@app_commands.describe(modify="add, remove edit, or display something in the store.")
@app_commands.choices(
    modify=[discord.app_commands.Choice(name='Add', value=1), discord.app_commands.Choice(name='Remove', value=2),
            discord.app_commands.Choice(name='edit', value=3), discord.app_commands.Choice(name='Display', value=4)])
async def title_store(interaction: discord.Interaction, masculine_name: typing.Optional[str], feminine_name: typing.Optional[str],
                      fame: typing.Optional[int], effect: typing.Optional[str], ubb_id: typing.Optional[str],
                      modify: discord.app_commands.Choice[int] = 4):
    "add, edit, remove, or display something from one of the stores"
    guild_id = interaction.guild_id
    ubb_id = ubb_id.strip() if ubb_id is not None else None
    fame = 0 if fame is None else fame
    modify = 4 if modify == 4 else modify.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = interaction.user.name
    cursor.execute(
        "Select ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title where Masculine_Name = ? OR Feminine_Name = ?",
        (masculine_name, feminine_name))
    item_info = cursor.fetchone()
    cursor.close()
    db.close()
    if item_info is None and modify == 1:
        await Event.add_title_store(self, guild_id, author, ubb_id, effect, fame, masculine_name, feminine_name)
        embed = discord.Embed(title=f"New Title Store Item",
                              description=f'{masculine_name}/{feminine_name} has been added to the title store!',
                              colour=discord.Colour.blurple())
        embed.add_field(name=f'**description:**', value=f'{effect}', inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 2:
        await Event.remove_title_store(self, guild_id, author, item_info[2], item_info[3], item_info[4])
        embed = discord.Embed(title=f"Removed Title Store Item",
                              description=f'{masculine_name}/{feminine_name} has been removed from the title store!',
                              colour=discord.Colour.blurple())
        await interaction.followup.send(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 3:
        await Event.edit_title_store(self, guild_id, author, ubb_id, effect, fame, masculine_name, feminine_name)
        embed = discord.Embed(title=f"Edited Title Store Item",
                              description=f'{masculine_name}/{feminine_name} has been edited in the title store!',
                              colour=discord.Colour.blurple())
        embed.add_field(name=f'**description:**', value=f'{effect}', inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    elif modify == 4:
        if item_info is not None:
            embed = discord.Embed(title=f"Title Store Item: {item_info[3]}/{item_info[4]}",
                                  description=f'**ID**: {item_info[0]}, **Effect**: {item_info[1]}, **Rewarded Fame**: {item_info[2]}',
                                  colour=discord.Colour.blurple())
            await interaction.followup.send(embed=embed)
        else:
            db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
            cursor = db.cursor()
            buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
            cursor.execute("Select COUNT(masculine_name) FROM Store_Title")
            admin_count = cursor.fetchone()
            max_page = math.ceil(admin_count[0] / 20)
            current_page = 1
            low = 1 + ((current_page - 1) * 20)
            high = 20 + ((current_page - 1) * 20)
            cursor.execute(
                "Select ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}")
            pull = cursor.fetchall()
            embed = discord.Embed(title=f"Title Store Settings Page {current_page}",
                                  description=f'This is a list of the administratively defined items',
                                  colour=discord.Colour.blurple())
            for result in pull:
                embed.add_field(name=f"Title Store Item: {result[3]}/{result[4]}",
                                value=f'**ID**: {result[0]}, **Effect**: {result[1]}, **Rewarded Fame**: {result[2]}',
                                inline=False)
            await interaction.followup.send(embed=embed)
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
                            "Select ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}")
                        pull = cursor.fetchall()
                        embed = discord.Embed(title=f"Title Store Settings Page {current_page}",
                                              description=f'This is a list of the administratively defined items',
                                              colour=discord.Colour.blurple())
                        for result in pull:
                            embed.add_field(name=f"Title Store Item: {result[3]}/{result[4]}",
                                            value=f'**ID**: {result[0]}, **Effect**: {result[1]}, **Rewarded Fame**: {result[2]}',
                                            inline=False)
                        await msg.edit(embed=embed)
    else:
        await interaction.followup.send(
            f"you were trying to do the following {modify} modification in the title store, but {name} was incorrect!",
            ephemeral=True)


@admin.command()
async def watest(interaction: discord.Interaction):
    "This is a test command for the wa command."
    await interaction.followup.send("This is a test command for the wa command.")
    client = WaClient(
        'Pathparser',
        'https://github.com/Solfyrism/Pathparser',
        'V1.1',
        os.getenv('WORLD_ANVIL_API'),
        os.getenv('WORLD_ANVIL_USER')
    )
    authenticated_user = client.user.identity()
    print(authenticated_user)
    worlds = [world for world in client.user.worlds(authenticated_user['id'])]
    print(worlds)
    categories = [category for category in client.world.categories('f7a60480-ea15-4867-ae03-e9e0c676060a')]
    print(categories)
    articles = [article for article in
                client.world.articles('f7a60480-ea15-4867-ae03-e9e0c676060a', 'c8fd1251-1077-4bbd-a9a5-797b3dbdf356')]
    print(articles)
    world_id = 'f7a60480-ea15-4867-ae03-e9e0c676060a'
    new_page = client.article.put({
        'title': 'Test Character Page',
        'content': 'This is a test page. can you believe it?!',
        'category': {'id': 'c8fd1251-1077-4bbd-a9a5-797b3dbdf356'},
        'templateType': 'person',  # generic article template
        'state': 'public',
        'isDraft': False,
        'entityClass': 'Person',
        'world': {'id': world_id}
    })

    print(new_page)
    print(new_page['id'])


async def setup(bot):
    bot.add_command(admin)
"""


class MilestoneDisplayView(shared_functions.ShopView):
    def __init__(self, user_id, guild_id, offset, limit):
        super().__init__(user_id, guild_id, offset, limit)
        self.max_items = None  # Cache total number of items

    async def update_results(self):
        """fetch the level information."""
        statement = """
            SELECT Level, Minimum_Milestones, Milestones_to_level, easy, medium, hard, deadly, WPL, WPL_Heroic, Level_range_name, Level_Range_ID
            FROM Milestone_System WHERE  
            ORDER BY LEVEL ASC LIMIT ? OFFSET ? 
        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, (self.limit, self.offset - 1))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the levels."""
        current_page = ((self.offset - 1) // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(title=f"Milestone System",
                                   description=f"Page {current_page} of {total_pages}")
        for level in self.results:
            (level, minimum_milestones, milestones_to_level, easy, medium, hard, deadly, wpl, wpl_heroic,
             level_range_name,
             level_range_id) = level
            self.embed.add_field(name=f'**Level**: {level}',
                                 value=f'**Milestone Info**: Minimum Milestones: {minimum_milestones}, Milestones to level: {milestones_to_level}\r\n'
                                       f'**Difficulty Rewards**: Easy: {easy}, Medium: {medium}, Hard: {hard}, Deadly: {deadly}\r\n'
                                       f'**Base Wealth**: WPL: {wpl}, WPL Heroic: {wpl_heroic}\r\n'
                                       f'**Level Range**: {level_range_name} <@{level_range_id}>',
                                 inline=False)

    async def get_max_items(self):
        """Get the total number of levels."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM Milestone_System")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


# *** DUAL VIEWS ***
class SettingDisplayView(shared_functions.DualView):
    def __init__(self, user_id, guild_id, offset, limit, view_type):
        super().__init__(user_id, guild_id, offset, limit, view_type)
        self.max_items = None  # Cache total number of items
        self.view_type = view_type

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""
        statement = """SELECT Search, Type, Identifier, Description FROM Admin Limit ? OFFSET ?"""
        val = (self.limit, self.offset - 1)

        async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.execute(statement, val)
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the titles."""
        if self.view_type == 1:

            current_page = ((self.offset - 1) // self.limit) + 1
            total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
            self.embed = discord.Embed(title=f"Settings Summary",
                                       description=f"Page {current_page} of {total_pages}")
            for result in self.results:
                (search, type, identifier, description) = result
                self.embed.add_field(name=f'{type}: {identifier}', value=f'current setting: {search}\r\n{description}',
                                     inline=False)
        else:
            current_page = ((self.offset - 1) // self.limit) + 1
            total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
            for result in self.results:
                (search, type, identifier, description) = result
                self.embed = discord.Embed(title=f"Setting Details",
                                           description=f"Page {current_page} of {total_pages}")
                self.embed.add_field(name=f'{type}: {identifier}', value=f'current setting: {search}\r\n{description}',
                                     inline=False)

    async def get_max_items(self):
        """Get the total number of titles."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM Admin")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items

    async def on_view_change(self):
        self.view_type = 1 if self.view_type == 2 else 2
        if self.view_type == 1:
            self.limit = 20  # Change the limit to 20 for the summary view
        else:
            self.limit = 1  # Change the limit to 1 for the detailed view


logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='pathparser.log',  # Specify the log file name
    filemode='a'  # Append mode
)
