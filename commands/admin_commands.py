import logging
import shutil
import typing
from math import ceil
from typing import Union
import discord
import unbelievaboat
from discord.app_commands import checks
from discord.ext import commands
from discord import app_commands
import datetime
import os
from pywaclient.api import BoromirApiClient as WaClient
import aiosqlite
import shared_functions
from decimal import Decimal

from commands import gamemaster_commands
from shared_functions import name_fix
import commands.character_commands as character_commands

# *** GLOBAL VARIABLES *** #
os.chdir("C:\\pathparser")


async def transaction_reverse(cursor: aiosqlite.Cursor, transaction_id: int, author_id: int, author_name: str,
                              reason: str) -> (
        Union[tuple[int, int, str, int, float, float, float, float], str]):
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
                new_gold_total = gold_total - gold
                new_effective_gold_total = gold_value_total - effective_gold
                new_max_effective_gold_total = gold_value_max_total - max_effective_gold
                return_value = (
                    new_transaction_id, related_transaction_id, character_name, thread_id, -abs(gold), new_gold_total,
                    new_effective_gold_total, new_max_effective_gold_total)
                return return_value
    except (aiosqlite.Error, TypeError, ValueError) as e:
        logging.exception(
            f"an error occurred for {author_name} whilst undoing transaction with id {transaction_id}': {e}")
        return_value = f"an error occurred for {author_name} whilst undoing transaction with id {transaction_id} Error: {e}."
        return return_value


def safe_add(a, b):
    # Treat None as zero
    a = a if a is not None else 0
    b = b if b is not None else 0

    # If either value is a Decimal, convert both to Decimal
    if isinstance(a, float) or isinstance(b, float):
        a = float(a)
        b = float(b)

    return a + b

def create_progress_bar(current, total, bar_length=20):
    progress = int(bar_length * (current / total))
    return f"[{'█' * progress}{'-' * (bar_length - progress)}] {current}/{total}"



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
                            value=f'**/admin Store_Fame**: Add, edit, or remove items from the fame store.\r\n' +
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

    @character_group.command(name="essence",
                             description="commands for adding or removing essence from a character")
    @app_commands.autocomplete(character_name=shared_functions.character_select_autocompletion)
    async def essence(self, interaction: discord.Interaction, character_name: str, amount: int):
        """Adjust the essence a PC has"""
        _, unidecode_name = name_fix(character_name)
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
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
                                                        content=f"Essence changes for {character_name} have been made: {essence_change}.")
            except (aiosqlite.Error, TypeError, ValueError, character_commands.CalculationAidFunctionError) as e:
                logging.exception(
                    f"an error occurred for {interaction.user.name} whilst adjusting essence for {character_name}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst adjusting essence for '{character_name}' Error: {e}.", ephemeral=True)

    @character_group.command(name="fame",
                             description="commands for adding or removing fame from a character")
    @app_commands.autocomplete(character_name=shared_functions.character_select_autocompletion)
    async def fame(self, interaction: discord.Interaction, character_name: str, fame: int, prestige: int):
        """Adjust the essence a PC has"""
        _, unidecode_name = name_fix(character_name)
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute(
                    "Select True_Character_Name, Character_Name, Fame, Prestige, Thread_ID FROM Player_Characters where Character_Name = ? OR Nickname = ?",
                    (unidecode_name, unidecode_name))
                player_info = await cursor.fetchone()
                if fame == 0 and prestige == 0:
                    await interaction.followup.send(f"No changes to fame or prestige required.")
                else:
                    if not player_info:
                        await interaction.followup.send(
                            f"there is no {character_name} registered.")
                    else:
                        (info_true_character_name, info_character_name, info_fame, info_prestige,
                         info_thread_id) = player_info
                        fame_calculation = await character_commands.calculate_fame(
                            character_name=character_name,
                            fame=info_fame,
                            fame_change=fame,
                            prestige=info_prestige,
                            prestige_change=prestige
                        )
                        (Fame, fame_change, prestige, prestige_change) = fame_calculation
                        character_updates = shared_functions.UpdateCharacterData(
                            character_name=character_name,
                            fame_package=(Fame, prestige))
                        await shared_functions.update_character(
                            guild_id=guild.id,
                            change=character_updates)
                        character_changes = shared_functions.CharacterChange(
                            character_name=character_name,
                            author=interaction.user.name,
                            fame=fame,
                            fame_change=fame_change,
                            prestige=prestige,
                            prestige_change=prestige_change,
                            source=f"admin adjusted fame by {fame_change} and prestige by {prestige_change} for {character_name}")
                        character_log = await shared_functions.log_embed(change=character_changes, guild=guild,
                                                                         thread=info_thread_id, bot=self.bot)
                        await shared_functions.character_embed(
                            character_name=character_name,
                            guild=guild)
                        await interaction.followup.send(embed=character_log,
                                                        content=f"Fame changes for {character_name} have been made fame has been changed by {fame_change} and prestige by {prestige_change}.")
            except (aiosqlite.Error, TypeError, ValueError, character_commands.CalculationAidFunctionError) as e:
                logging.exception(
                    f"an error occurred for {interaction.user.name} whilst adjusting essence for {character_name}': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst adjusting essence for '{character_name}' Error: {e}.", ephemeral=True)

    gold_group = discord.app_commands.Group(
        name='gold',
        description='gold commands',
        parent=admin_group
    )

    @gold_group.command(name="adjust",
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

        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
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
                    gold_value=new_effective_gold,
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

    @gold_group.command(name="undo_transaction",
                        description="commands for undoing a transaction")
    async def undo_transaction(self, interaction: discord.Interaction, reason: str,
                               transaction_id: int):
        guild_id = interaction.guild_id
        guild = interaction.guild

        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                transaction_undo = await transaction_reverse(
                    cursor=cursor, transaction_id=transaction_id,
                    author_id=interaction.user.id, author_name=interaction.user.name, reason=reason)
                if isinstance(transaction_undo, str):
                    await interaction.followup.send(transaction_undo, ephemeral=True)
                else:
                    (new_transaction_id, related_transaction_id, character_name, thread_id, amount, gold_total,
                     gold_value_total,
                     gold_value_max_total) = transaction_undo
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
                    content = f"undid transaction {transaction_id} for {character_name} with a new transaction id of {new_transaction_id}."
                    if related_transaction_id:
                        related_transaction_undo = await transaction_reverse(
                            cursor=cursor, transaction_id=transaction_id,
                            author_id=interaction.user.id, author_name=interaction.user.name, reason=reason)
                        if isinstance(related_transaction_undo, str):
                            content += f"\r\n {related_transaction_undo}"
                        else:
                            (new_transaction_id, _, character_name, thread_id, amount, gold_total, gold_value_total,
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
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
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
                    base_session_info = gamemaster_commands.RewardSessionBaseInfo(
                        session_name=session_name,
                        rewarded_gold=rewarded_gold,
                        rewarded_essence=rewarded_essence,
                        rewarded_easy=rewarded_easy,
                        rewarded_medium=rewarded_medium,
                        rewarded_hard=rewarded_hard,
                        rewarded_deadly=rewarded_deadly,
                        rewarded_trials=rewarded_trials,
                        rewarded_alt_reward_all=rewarded_reward_all,
                        rewarded_alt_reward_party=rewarded_reward_party,
                        rewarded_fame=rewarded_fame,
                        rewarded_prestige=rewarded_prestige,
                        rewarded_session_thread=session_rewards_thread,
                        rewarded_message=session_rewards_message,
                        gm_name=gm_name
                    )

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
                                    remove_rewards = await gamemaster_commands.session_reward_reversal(
                                        interaction=interaction,
                                        session_id=session_id,
                                        character_name=character_name,
                                        author_name=gm_name,
                                        session_info=player,
                                        session_gold=received_gold,
                                        source="Session Reward")
                                    if isinstance(remove_rewards, str):
                                        field += "failed to remove rewards, skipping adjustment. \r\n "
                                    else:
                                        (reversal_dataclass, reversal_thread_id) = remove_rewards
                                        add_rewards = await gamemaster_commands.session_reward_calculation(
                                            interaction=interaction,
                                            session_id=session_id,
                                            character_name=character_name,
                                            author_name=gm_name,
                                            pre_session_level=level,
                                            pre_session_tier=tier,
                                            pre_session_gold=effective_gold,
                                            source="Session Adjustment",
                                            session_base_info=base_session_info
                                        )
                                        if isinstance(add_rewards, str):
                                            field += "failed to calculate rewards, skipping adjustment. \r\n "
                                        else:
                                            numeric_fields = ['milestone_change', 'milestones_total',
                                                              'milestones_remaining',
                                                              'trial_change', 'trials', 'trials_remaining',
                                                              'gold_change',
                                                              'essence_change', 'fame_change', 'prestige_change']
                                            for field in numeric_fields:
                                                a_value = getattr(add_rewards, field)
                                                r_value = getattr(reversal_dataclass, field)
                                                new_value = safe_add(a_value, r_value)
                                                setattr(add_rewards, field, new_value)
                                            await shared_functions.log_embed(change=add_rewards[0], guild=guild,
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
            except (aiosqlite.Error, TypeError, ValueError) as e:
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
        await interaction.response.defer(thinking=True)
        try:
            shop = await client.get_inventory_items_all(guild_id, player.id)
            if shop is not None:
                embed = discord.Embed(title=f"UBB Inventory", description=f'UBB inventory',
                                      colour=discord.Colour.blurple())
                print(shop)
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
            async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
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
                        offset = results.index(results[0]) + 1
                else:
                    view_type = 1

                # Set up pagination variables
                page_number = min(max(page_number, 1), ceil(item_count / 20))
                items_per_page = 20 if view_type == 1 else 1
                offset = (page_number - 1) * items_per_page if view_type == 1 else offset

                # Create and send the view with the results
                view = SettingDisplayView(
                    user_id=interaction.user.id,
                    guild_id=guild_id,
                    limit=items_per_page,
                    offset=offset,
                    view_type=view_type,
                    interaction=interaction
                )
                await view.send_initial_message()
        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(
                f"An error occurred whilst fetching data! input values of setting: {setting}, page_number: {page_number}': {e}"
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
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await interaction.response.defer(thinking=True)
                if not setting:
                    await interaction.followup.send(f"cannot replace a search key with None")
                elif not revision:
                    await interaction.followup.send(f"Yeah... that would break shit, no")
                else:
                    await cursor.execute(
                        "Select Search, Type, Identifier, Description FROM Admin where Identifier = ?", (setting,))
                    information = await cursor.fetchone()
                    if information:
                        if information[1] == 'Channel':
                            revision = int(revision)
                            channel = interaction.guild.get_channel(revision)
                            if not channel:
                                channel = await interaction.guild.fetch_channel(revision)
                            if not channel:
                                await interaction.followup.send("Error: Could not find the requested channel.")
                                return
                        elif information[1] == 'Level':
                            await cursor.execute("SELECT Max(Level), Min(Level) from Milestone_System")
                            max_level = await cursor.fetchone()
                            if int(revision) > max_level[0]:
                                await interaction.followup.send(
                                    f"Your server does not have a milestone system for above level {max_level[0]}")
                                return
                            elif int(revision) < max_level[1]:
                                await interaction.followup.send(
                                    f"Your server does not have a milestone system for below level {max_level[1]}")
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
                            try:
                                item = await client.get_store_item(guild_id, int(revision))
                                if not item:
                                    await interaction.followup.send("Error: Could not find the requested item.")
                                    return
                            except unbelievaboat.HTTPError as e:
                                await interaction.followup.send(f"Error: Could not find the requested item. {e}")
                                logging.error(f"Error: Could not find the requested item. {e}")
                                return
                        await cursor.execute("Update Admin set Search = ? WHERE identifier = ?", (revision, setting))
                        await conn.commit()
                        await interaction.followup.send(f"Updated {setting} to {revision}")

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

    @settings_group.command()
    @app_commands.describe(certainty="is life short?")
    @app_commands.choices(
        certainty=[discord.app_commands.Choice(name='YOLO', value=1), discord.app_commands.Choice(name='No', value=2)])
    async def reset(self, interaction: discord.Interaction, certainty: discord.app_commands.Choice[int]):
        """Perform a database reset, remember to reassign role ranges and server settings!"""
        certainty_value = certainty.value
        interaction.response.defer(thinking=True)
        if certainty_value == 1:
            # Create and send the PropositionView
            content = "You gotta be like so sure about this. Super Sure. Super Duper Sure."
            view = ResetDatabaseView(content=content, interaction=interaction)
            await view.create_embed()

            await interaction.followup.send(
                content=content,
                embed=view.embed,
                view=view
            )

        else:
            await interaction.followup.send(f"I'M FIRING MY LAS--- What?")

    @settings_group.command(name='fame', description='Administrative commands for the fame store.')
    @app_commands.describe(modify="add, remove, or edit something in the store.")
    @app_commands.autocomplete(name=shared_functions.fame_autocomplete)
    @app_commands.choices(
        modify=[discord.app_commands.Choice(name='Add/Edit', value=1),
                discord.app_commands.Choice(name='Remove', value=2)])
    async def store_fame(self, interaction: discord.Interaction, name: str, fame_required: typing.Optional[int],
                         prestige_cost: typing.Optional[int], effect: typing.Optional[str], limit: typing.Optional[int],
                         modify: discord.app_commands.Choice[int]):
        """Add, edit, or remove items from the fame store."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute(
                    "Select Name, Fame_Required, Prestige_Cost, Use_limit, effect from Store_Fame where Name = ?",
                    (name,))
                fame_item = await cursor.fetchone()
                if modify.value == 1 and not fame_item:
                    if not fame_required or not prestige_cost or not effect or not limit:
                        await interaction.followup.send(
                            f"Please provide all required information for adding a new item to the fame store. \r\n "
                            f"You provided: Name: {name}, Fame required: {fame_required}, Prestige Cost: {prestige_cost}, Limit: {limit} \r\n"
                            f"EFFECT: {effect}.")
                        return
                    else:
                        await cursor.execute(
                            "Insert into Store_Fame (Name, Fame_Required, Prestige_Cost, Effect, Use_Limit) VALUES (?, ?, ?, ?, ?)",
                            (name, fame_required, prestige_cost, effect, limit))
                        await conn.commit()
                        embed = discord.Embed(title="Fame Store Adjustment",
                                              description=f"adding new fame option",
                                              color=discord.Color.blue())
                        embed.add_field(name=name,
                                        value=f"Fame Required: {fame_required}, Prestige Cost: {prestige_cost}, Limit: {limit} \r\n"
                                              f"Effect: {effect}")
                        await interaction.followup.send(embed=embed)
                elif modify.value == 1 and fame_item:
                    (info_name, info_fame_required, info_prestige_cost, info_limit, info_effect) = fame_item
                    updated_fame_requirement = fame_required if fame_required else info_fame_required
                    updated_prestige_cost = prestige_cost if prestige_cost else info_prestige_cost
                    updated_limit = limit if limit else info_limit
                    updated_effect = effect if effect else info_effect
                    await cursor.execute(
                        "Update Store_Fame set Name = ?, Fame_Required = ?, Prestige_Cost = ?, Effect = ?, Use_Limit = ? WHERE Name = ?",
                        (name, updated_fame_requirement, updated_prestige_cost, updated_effect, updated_limit, name))
                    embed = discord.Embed(title="Fame Store Adjustment",
                                          description=f"changing fame option",
                                          color=discord.Color.blue())
                    embed.add_field(name=name,
                                    value=f"Fame Required: {fame_required}, Prestige Cost: {prestige_cost}, Limit: {limit} \r\n"
                                          f"Effect: {effect}")
                    await interaction.followup.send(embed=embed)
                elif modify.value == 2 and fame_item:
                    await cursor.execute("DELETE FROM Store_Fame WHERE Name = ?",
                                         (name,))
                    await conn.commit()
                    await interaction.followup.send(f"Removed {name} from the fame store.")
                else:
                    await interaction.followup.send(
                        f"An error occurred whilst adjusting the fame store. Please ensure that the item exists and that all required fields are filled out")
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"an error occurred for {interaction.user.name} whilst adjusting fame store': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst adjusting fame store. Error: {e}.", ephemeral=True)

    @settings_group.command(name='titles', description='Administrative commands for the title store.')
    @app_commands.describe(modify="add, remove, or edit something in the store.")
    @app_commands.choices(
        modify=[discord.app_commands.Choice(name='Add/Edit', value=1),
                discord.app_commands.Choice(name='Remove', value=2)])
    async def title_store(self, interaction: discord.Interaction, masculine_name: typing.Optional[str],
                          feminine_name: typing.Optional[str],
                          fame: typing.Optional[int], effect: typing.Optional[str], ubb_id: typing.Optional[str],
                          modify: discord.app_commands.Choice[int] = 4):
        """Add, edit, or remove items from the fame store."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute(
                    "Select ID, Masculine_Name, Feminine_Name, Fame, Effect from Store_Title where Masculine_Name = ? or Feminine_Name = ?",
                    (masculine_name, feminine_name))
                fame_item = await cursor.fetchone()
                if modify.value == 1 and not fame_item:
                    if not fame or not ubb_id or not effect or not masculine_name or not feminine_name:
                        await interaction.followup.send(
                            f"Please provide all required information for adding a new item to the fame store. \r\n "
                            f"You provided: Name: {masculine_name}/{feminine_name}, Fame bestowed: {fame}, UBB_ID: {ubb_id}"
                            f"EFFECT: {effect}.")
                        return
                    else:
                        ubb_evaluation = await character_commands.ubb_inventory_check(
                            guild_id=guild_id,
                            item_id=ubb_id,
                            author_id=interaction.user.id,
                            amount=1
                        )
                        if ubb_evaluation > 0:
                            await cursor.execute(
                                "Insert into Store_Title (ID, Masculine_Name, Feminine_Name, fame, Effect) VALUES (?, ?, ?, ?, ?)",
                                (ubb_id, masculine_name, feminine_name, fame, effect))
                            await conn.commit()
                            embed = discord.Embed(title="Title Store Adjustment",
                                                  description=f"Title Store Adjustment",
                                                  color=discord.Color.blue())
                            embed.add_field(name="Titles:", value=f"Updated Name: {masculine_name}/{feminine_name}")
                            embed.add_field(name="Fame:", value=f"Fame bestowed: {fame}")
                            embed.add_field(name="UBB_ID:", value=f"UBB_ID: {ubb_id}")
                            await interaction.followup.send(embed=embed)
                        else:
                            await interaction.followup.send(f"UBB_ID: {ubb_id} not found in the UBB inventory.")
                elif modify.value == 1 and fame_item:
                    (info_id, info_masculine_name, info_feminine_name, info_fame, info_effect) = fame_item
                    updated_fame = fame if fame else info_fame
                    updated_ubb_id = ubb_id if ubb_id else info_id
                    updated_effect = effect if effect else info_effect
                    updated_masculine_name = masculine_name if masculine_name else info_masculine_name
                    updated_feminine_name = feminine_name if feminine_name else info_feminine_name
                    ubb_evaluation = await character_commands.ubb_inventory_check(
                        guild_id=guild_id,
                        item_id=updated_ubb_id,
                        author_id=interaction.user.id,
                        amount=1
                    )
                    if ubb_evaluation > 0:
                        await cursor.execute(
                            "Update Store_Title set ID = ?, Masculine_Name = ?, Feminine_Name = ?, Fame = ?, Effect = ? WHERE ID = ?",
                            (
                                updated_ubb_id, updated_masculine_name, updated_feminine_name, updated_fame,
                                updated_effect,
                                info_id))
                        await conn.commit()
                        embed = discord.Embed(
                            title="Title Store Adjustment",
                            description=f"Title Store Adjustment",
                            color=discord.Color.blue())
                        embed.add_field(name="Titles:", value=f"Updated Name: {masculine_name}/{feminine_name}")
                        embed.add_field(name="Fame:", value=f"Fame bestowed: {fame}")
                        embed.add_field(name="UBB_ID:", value=f"UBB_ID: {ubb_id}")
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"UBB_ID: {ubb_id} not found in the UBB inventory.")
                elif modify.value == 2 and fame_item:
                    (info_id, info_masculine_name, info_feminine_name, info_fame, info_effect) = fame_item
                    await cursor.execute("DELETE FROM Store_Title WHERE Masculine_Name = ?",
                                         (info_masculine_name,))
                    await conn.commit()
                    await interaction.followup.send(
                        f"Removed {info_masculine_name}/{info_feminine_name} from the fame store.")
                else:
                    await interaction.followup.send(
                        f"An error occurred whilst adjusting the title store. Please ensure that the item exists and that all required fields are filled out")
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"an error occurred for {interaction.user.name} whilst adjusting title store': {e}")
                await interaction.followup.send(
                    f"An error occurred whilst adjusting title store. Error: {e}.", ephemeral=True)

    level_group = discord.app_commands.Group(
        name='level',
        description='Update the level, WPL, and other information in the milestone system',
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
    async def adjust_milestones(self, interaction: discord.Interaction, character_name: str, amount: int,
                                job: discord.app_commands.Choice[int], level: typing.Optional[int],
                                misc_milestones: int = 0):
        """Adjusts the milestone number a PC has."""
        _, unidecode_name = name_fix(character_name)
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
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
                            trial_change=0,
                            tier=tier)
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

    @level_group.command(name='cap', description='command for adjusting the level cap of the server')
    async def level_cap(self, interaction: discord.Interaction, new_level: int):
        """This allows the admin to adjust the server wide level cap"""
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
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
                            "SELECT True_Character_Name, Character_Name, Level, Milestones, Tier, Trials, personal_cap, Thread_ID FROM Player_Characters WHERE Milestones >= ?",
                            (minimum_milestones,))
                        characters_to_adjust = await cursor.fetchall()
                        if characters_to_adjust:
                            cap_embed = discord.Embed(title=f"Level Cap Adjustment",
                                                      description=f'{interaction.user.name} Adjusting the level cap to {new_level}')
                            for idx, character in enumerate(characters_to_adjust):
                                try:
                                    (true_character_name, character_name, character_level, milestones, tier, trials,
                                     personal_cap, thread_id) = character
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
                                        trial_change=0,
                                        tier=tier)
                                    (new_tier, total_trials, trials_required, trial_change) = mythic_adjustment
                                    character_updates = shared_functions.UpdateCharacterData(
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

    @level_group.command(name='milestones',
                         description='command for adjusting the milestone floor of a level among other things.')
    @app_commands.describe(
        level="The level you wish to adjust the milestone floor for or to add a new level into the range.")
    @app_commands.describe(
        minimum_milestones="The minimum number of milestones required to reach the level. Set as -1 to delete the level.")
    async def define_milestone(self, interaction: discord.Interaction, level: int, minimum_milestones: int):
        """This allows the admin to adjust the milestone floor of a level among other things."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute("SELECT MIN(LEVEL), MAX(LEVEL) from Milestone_System")
                level_minmax = await cursor.fetchone()
                if level < level_minmax[0] - 1:
                    await interaction.followup.send(
                        f"Your minimum server level was {level_minmax[0]} You cannot add levels which break the sequence!")
                    return
                elif level > level_minmax[1] + 1:
                    await interaction.followup.send(
                        f"Your maximum server level was {level_minmax[1]}! You cannot add numbers which break the sequence!")
                    return

                await cursor.execute(
                    "SELECT level, minimum_milestones, wpl, wpl_heroic FROM Milestone_System WHERE Level = ?",
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
                        await conn.commit()
                        if level > 0:
                            await cursor.execute("UPDATE Milestones_System SET level = level - 1 where level > ?",
                                                 (level,))
                        else:
                            await cursor.execute("UPDATE Milestones_System SET level = level + 1 where level < ?",
                                                 (level,))
                        await conn.commit()

                        await interaction.followup.send(f"Level of {level} removed from milestone system.")
                    else:
                        await cursor.execute("UPDATE Milestone_System SET milestones_required = ? WHERE Level = ?",
                                             (center_milestones_required, level))
                        await interaction.followup.send(f"Level of {level} updated in milestone system.")
                else:
                    wpl = 0 if not lower_level_info else lower_level_info[2]
                    wpl_heroic = 0 if not lower_level_info else lower_level_info[3]
                    await cursor.execute(
                        "INSERT INTO Milestone_System (Level, Milestones_Required, WPL, WPL_Heroic) VALUES (?, ?, ?, ?)",
                        (level, center_milestones_required, wpl, wpl_heroic))
                    await interaction.followup.send(
                        f"Level of {level} added to milestone system. PLEASE REMEMBER TO UPDATE WPL VALUES.")
                await conn.commit()
                center_milestones_range = minimum_milestones if minimum_milestones != -1 else center_level_info[1]
                upper_milestone_range = 99999 if not higher_level_info else higher_level_info[1]
                await cursor.execute(
                    "Select character_name, level, milestones, trials, personal_cap, Tier, Thread_ID FROM Player_Characters WHERE Minimum_Milestones (? AND ?)",
                    (center_milestones_range, upper_milestone_range))
                characters_to_adjust = await cursor.fetchall()
                for character in characters_to_adjust:
                    (character_name, level, milestones, trials, personal_cap, tier, thread_id) = character
                    level_adjustment = await character_commands.level_calculation(
                        character_name=character_name,
                        level=level,
                        guild=interaction.guild,
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
                        trial_change=0,
                        tier=tier)
                    (new_tier, total_trials, trials_required, trial_change) = mythic_adjustment
                    character_updates = shared_functions.UpdateCharacterData(
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
                        guild=interaction.guild,
                        thread=thread_id, bot=self.bot)
                    await shared_functions.character_embed(
                        character_name=character_name,
                        guild=interaction.guild)

            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"An error occurred whilst milestones! input values of: level: {level}, minimum_milestones{minimum_milestones} in server {interaction.guild.id} by {interaction.user.name}': {e}"
                )
                await interaction.followup.send(
                    f"An error occurred whilst fetching data. Please try again later.",
                    ephemeral=True
                )

    @level_group.command(name='wpl',
                         description='command for adjusting the wealth per level and heroic WPL of a level.')
    async def define_wpl(self, interaction: discord.Interaction, level: int, wpl: int, wpl_heroic: int):
        """This allows the admin to adjust the milestone floor of a level among other things."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
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
                    f"An error occurred whilst milestones! input values of: level: {level}, WPL: {wpl}, WPL_Heroic {wpl_heroic} in server {interaction.guild.id} by {interaction.user.name}': {e}"
                )
                await interaction.followup.send(
                    f"An error occurred whilst fetching data. Please try again later.",
                    ephemeral=True
                )

    @level_group.command(name='jobs', description='command for adjusting the job rewards for a session.')
    async def define_jobs(self, interaction: discord.Interaction, level: int, easy: typing.Optional[int],
                          medium: typing.Optional[int], hard: typing.Optional[int], deadly: typing.Optional[int]):
        """This allows the admin to adjust the milestone floor of a level among other things."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
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
                        await conn.commit()
                        await interaction.followup.send(
                            f"Successfully updated level: {level} to have the following rewards \r\n Easy: {new_easy}, Medium: {new_medium}, Hard: {new_hard}, Deadly: {new_deadly}")
                else:
                    await interaction.followup.send(f"Your server does not have a milestone system for level {level}")
            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"An error occurred whilst milestones! input values of: level: {level}, easy: {easy}, medium: {medium}, hard: {hard}, deadly: {deadly} in server {interaction.guild.id} by {interaction.user.name}': {e}"
                )
                await interaction.followup.send(
                    f"An error occurred whilst fetching data. Please try again later.",
                    ephemeral=True
                )

    @level_group.command(
        name='level_range',
        description='Adjust the stored level ranges of levels in the server.'
    )
#    @checks.has_permissions(administrator=True)
    async def level_range(
            self,
            interaction: discord.Interaction,
            min_level: int,
            max_level: int,
            role: discord.Role
    ):
        """Allows the admin to adjust the associated levels with a role."""
        await interaction.response.defer(thinking=True)
        try:
            async with aiosqlite.connect(f"Pathparser_{interaction.guild_id}_test.sqlite") as conn:
                cursor = await conn.cursor()
                await cursor.execute("SELECT MIN(level), MAX(level) FROM Milestone_System")
                level_minmax = await cursor.fetchone()
                if min_level < level_minmax[0] or max_level > level_minmax[1]:
                    await interaction.followup.send(
                        f"Your server does not support levels below {level_minmax[0]} or above {level_minmax[1]}.",
                        ephemeral=True
                    )
                    return

                # Fetch existing level ranges that overlap with the new range
                await cursor.execute(
                    "SELECT DISTINCT Level_Range_ID FROM Milestone_System WHERE Level BETWEEN ? AND ?",
                    (min_level, max_level)
                )
                level_ranges = await cursor.fetchall()

                # Prepare progress message
                progress_message = await interaction.followup.send(
                    "Processing level range adjustments...",
                    ephemeral=True
                )

                # Remove roles from players who no longer qualify
                if level_ranges:
                    for level_range in level_ranges:
                        level_range_id = level_range[0]
                        await cursor.execute(
                            "SELECT MIN(Level), MAX(Level) FROM Milestone_System WHERE Level_Range_ID = ?",
                            (level_range_id,)
                        )
                        range_level = await cursor.fetchone()
                        if range_level[0] < min_level or range_level[1] > max_level:
                            # Fetch players to remove the role from
                            await cursor.execute(
                                """
                                SELECT DISTINCT Player_ID
                                FROM player_characters
                                WHERE Level BETWEEN ? AND ?
                                AND Level NOT BETWEEN ? AND ?
                                """,
                                (range_level[0], range_level[1], min_level, max_level)
                            )
                            players_to_remove = await cursor.fetchall()
                            players_to_remove_list = [player[0] for player in players_to_remove]

                            total_players = len(players_to_remove_list)
                            processed_count = 0

                            for player_id in players_to_remove_list:
                                remove_role = interaction.guild.get_role(level_range_id)
                                if not remove_role:
                                    logging.warning(
                                        f"Role with ID {level_range_id} not found in guild {interaction.guild.id}")
                                    continue

                                member = interaction.guild.get_member(player_id)
                                if not member:
                                    logging.warning(
                                        f"Member with ID {player_id} not found in guild {interaction.guild.id}")
                                    continue

                                try:
                                    await member.remove_roles(remove_role)
                                except discord.DiscordException as e:
                                    logging.error(f"Failed to remove role {remove_role.name} from {member.name}: {e}")

                                processed_count += 1
                                if processed_count % 10 == 0 or processed_count == total_players:
                                    progress_bar = create_progress_bar(processed_count, total_players)
                                    await progress_message.edit(content=f"Removing roles...\n{progress_bar}")

                # Update the Milestone_System table with the new range
                await cursor.execute(
                    "UPDATE Milestone_System SET Level_Range_Name = ?, Level_Range_ID = ? WHERE Level BETWEEN ? AND ?",
                    (role.name, role.id, min_level, max_level)
                )

                await conn.commit()

                # Assign the role to players who now meet the new requirements
                await cursor.execute(
                    "SELECT DISTINCT Player_ID FROM player_characters WHERE Level BETWEEN ? AND ?",
                    (min_level, max_level)
                )
                players = await cursor.fetchall()
                players_to_add_list = [player[0] for player in players]

                total_players = len(players_to_add_list)
                processed_count = 0

                for player_id in players_to_add_list:
                    member = interaction.guild.get_member(player_id)
                    if not member:
                        logging.warning(f"Member with ID {player_id} not found in guild {interaction.guild.id}")
                        continue

                    try:
                        await member.add_roles(role)
                    except discord.DiscordException as e:
                        logging.error(f"Failed to add role {role.name} to {member.name}: {e}")

                    processed_count += 1
                    if processed_count % 10 == 0 or processed_count == total_players:
                        progress_bar = create_progress_bar(processed_count, total_players)
                        await progress_message.edit(content=f"Assigning roles...\n{progress_bar}")

                # Final update
                await progress_message.edit(content="Level range adjustments complete.")

                await interaction.followup.send(
                    f"Successfully updated role: {role.name} with level range {min_level}-{max_level}.",
                    ephemeral=True
                )

        except Exception as e:
            logging.exception(
                f"An error occurred while adjusting level ranges: {e}"
            )
            await interaction.followup.send(
                "An error occurred while adjusting level ranges. Please try again later.",
                ephemeral=True
            )

    @level_range.error
    async def level_range_error(interaction: discord.Interaction, error):
        if isinstance(error, checks.MissingPermissions):
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
        else:
            logging.exception(f"An error occurred in level_range command: {error}")
            await interaction.response.send_message(
                "An unexpected error occurred. Please contact the administrator.",
                ephemeral=True
            )
    @level_group.command(name='display',
                         description='Display milestone settings')
    async def display_milestones(self, interaction: discord.Interaction, page_number: int = 1):
        """Display Milestone Information and further context about levels."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)

        try:
            async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
                cursor = await conn.cursor()

                # Decide which query to execute based on whether 'name' is provided
                await cursor.execute("SELECT COUNT(level) FROM Milestone_System")
                item_count = await cursor.fetchone()
                item_count = item_count[0]

                # Set up pagination variables
                page_number = min(max(page_number, 1), ceil(item_count / 20))
                items_per_page = 20
                offset = (page_number - 1) * items_per_page

                # Create and send the view with the results
                view = MilestoneDisplayView(
                    user_id=interaction.user.id,
                    guild_id=guild_id,
                    limit=items_per_page,
                    offset=offset,
                    interaction=interaction
                )
                await view.update_results()
                await view.create_embed()
                await interaction.followup.send(embed=view.embed, view=view)

        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(
                f"an error occurred displaying milestones: {e}"
            )
            await interaction.followup.send(
                f"An error occurred whilst fetching data. Please try again later.",
                ephemeral=True
            )

    mythic_group = discord.app_commands.Group(
        name='mythic',
        description='Update the Mythic Trials required and other information in the mythic system',
        parent=admin_group
    )

    @character_group.command(name="trials",
                             description="commands for adding or removing mythic trials from a character")
    @app_commands.autocomplete(character_name=shared_functions.character_select_autocompletion)
    async def trial_adjustment(self, interaction: discord.Interaction, character_name: str, amount: int):
        """Adjust the number of Mythic Trials a character possesses"""
        _, unidecode_name = name_fix(character_name)
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute(
                    "Select True_Character_Name, Character_Name, Level, Tier, Trials, Thread_ID  FROM Player_Characters where Character_Name = ? OR Nickname = ?",
                    (character_name, character_name))
                player_info = cursor.fetchone()
                if amount == 0:
                    await interaction.followup.send(f"No changes to trial total required.")
                else:
                    if not player_info:
                        await interaction.followup.send(
                            f"there is no {character_name} registered.")
                    else:
                        (true_character_name, character_name, character_level, tier, trials, thread_id) = player_info
                        mythic_adjustment = await character_commands.mythic_calculation(
                            character_name=character_name,
                            level=character_level,
                            trials=trials,
                            trial_change=amount,
                            guild_id=guild_id,
                            tier=tier
                        )
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

    @mythic_group.command(name='cap', description='command for adjusting the tier cap of the server')
    async def tier_cap(self, interaction: discord.Interaction, new_tier: int):
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute("SELECT MIN(tier), MAX(tier) from AA_Trials")
                tier_minmax = await cursor.fetchone()
                if new_tier < tier_minmax[0]:
                    await interaction.followup.send(
                        f"Your server does not have a trial system for below tier {tier_minmax[0]}")
                elif new_tier > tier_minmax[1]:
                    await interaction.followup.send(
                        f"Your server does not have a trial system for above tier {tier_minmax[1]}")
                else:
                    await cursor.execute("Select Trials FROM AA_Trials where Tier = ?", (tier_minmax,))
                    new_tier_info = await cursor.fetchone()
                    if new_tier_info:
                        minimum_milestones = new_tier_info[0]
                        await cursor.execute(
                            "SELECT True_Character_Name, Character_Name, Level, Tier, Trials, Thread_ID FROM Player_Characters WHERE Trials >= ?",
                            (minimum_milestones,))
                        characters_to_adjust = await cursor.fetchall()
                        if characters_to_adjust:
                            cap_embed = discord.Embed(title=f"Tier Cap Adjustment",
                                                      description=f'{interaction.user.name} Adjusting the tier cap to {new_tier}')
                            for idx, character in enumerate(characters_to_adjust):
                                (true_character_name, character_name, character_level, tier, trials,
                                 thread_id) = character
                                mythic_adjustment = await character_commands.mythic_calculation(
                                    guild_id=guild_id,
                                    character_name=character_name,
                                    level=character_level,
                                    trials=trials,
                                    trial_change=0,
                                    tier=tier)
                                (new_tier, total_trials, trials_required, trial_change) = mythic_adjustment
                                character_updates = shared_functions.UpdateCharacterData(
                                    character_name=character_name,
                                    mythic_package=(new_tier, total_trials, trials_required)
                                )
                                character_changes = shared_functions.CharacterChange(
                                    character_name=character_name,
                                    author=interaction.user.name,
                                    tier=new_tier,
                                    trials=total_trials,
                                    trials_remaining=trials_required,
                                    trial_change=0,
                                    source=f"admin adjusted tier cap to {new_tier}")
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
                                                        value=f"{true_character_name} has been leveled up to {new_tier}.",
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

    @mythic_group.command(name='define', description='command for defining the trials required for a tier')
    async def define_tier(self, interaction: discord.Interaction, tier: int, trials: int):
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute("SELECT MIN(Tier), MAX(Tier) from AA_Trials")
                tier_minmax = await cursor.fetchone()
                if tier < tier_minmax[0] - 1:
                    await interaction.followup.send(
                        f"Your server does not have a trial system for below tier {tier_minmax[0]}")
                    return
                elif tier > tier_minmax[1] + 1:
                    await interaction.followup.send(
                        f"Your server does not have a trial system for above tier {tier_minmax[1]}")
                    return
                await cursor.execute("SELECT Trials FROM AA_Trials WHERE Tier = ?", (tier - 1,))
                low_tier_info = await cursor.fetchone()
                await cursor.execute("SELECT Trials FROM AA_Trials WHERE Tier = ?", (tier,))
                center_tier_info = await cursor.fetchone()
                await cursor.execute("SELECT Trials FROM AA_Trials WHERE Tier = ?", (tier + 1,))
                high_tier_info = await cursor.fetchone()
                center_trials_required = 999 if not high_tier_info else high_tier_info[0] - trials
                if low_tier_info:
                    if trials == -1:
                        low_trials_required = 999 if not high_tier_info else high_tier_info[0] - low_tier_info[0]
                    else:
                        low_trials_required = trials - low_tier_info[0]
                        if low_trials_required < 0:
                            await interaction.followup.send(
                                f"Your input of tier: {tier} trials: {trials} cannot be less than tier: {tier - 1} trials: {low_tier_info[0]}.")
                            return
                    await cursor.execute("UPDATE AA_Trials SET Trials_Required = ? WHERE Tier = ?",
                                         (low_trials_required, low_tier_info[0]))
                    await conn.commit()
                if high_tier_info:
                    if trials > high_tier_info[0]:
                        await interaction.followup.send(
                            f"Your input of tier: {tier} trials: {trials} cannot be more than tier: {tier + 1} trials: {high_tier_info[0]}.")
                        return
                    else:
                        await cursor.execute(
                            "SELECT Character_Name, level, Trials, thread_id FROM Player_Characters WHERE Trials BETWEEN ? AND ?",
                            (trials, high_tier_info[0]))
                        characters_to_adjust = await cursor.fetchall()
                        for character in characters_to_adjust:
                            (character_name, character_level, trials, thread_id) = character
                            mythic_adjustment = await character_commands.mythic_calculation(
                                character_name=character_name,
                                level=character_level,
                                trials=trials,
                                trial_change=0,
                                guild_id=guild_id,
                                tier=tier
                            )
                            (new_tier, total_trials, trials_required, trial_change) = mythic_adjustment
                            character_updates = shared_functions.UpdateCharacterData(
                                character_name=character_name,
                                mythic_package=(new_tier, total_trials, trials_required)
                            )
                            character_changes = shared_functions.CharacterChange(
                                character_name=character_name,
                                author=interaction.user.name,
                                tier=new_tier,
                                trials=total_trials,
                                trials_remaining=trials_required,
                                trial_change=0,
                                source=f"admin added new Tier of {tier}")
                            await shared_functions.update_character(
                                guild_id=guild_id,
                                change=character_updates
                            )
                            await shared_functions.log_embed(
                                change=character_changes,
                                guild=interaction.guild,
                                thread=thread_id,
                                bot=self.bot)
                            await shared_functions.character_embed(
                                character_name=character_name,
                                guild=interaction.guild)

                if center_tier_info:
                    if trials == -1:
                        await cursor.execute("DELETE FROM AA_Trials WHERE Tier = ?", (tier,))
                        await conn.commit()
                        if tier > 0:
                            await cursor.execute("UPDATE AA_Trials SET Tier = Tier - 1 where Tier > ?", (tier,))
                        else:
                            await cursor.execute("UPDATE AA_Trials SET Tier = Tier + 1 where Tier < ?",
                                                 (tier,))
                        await interaction.followup.send(f"Tier of {tier} removed from trial system.")
                    else:
                        await cursor.execute("UPDATE AA_Trials SET Trials = ?, Trials_Required = ? WHERE Tier = ?",
                                             (trials, center_trials_required, tier))
                        await interaction.followup.send(
                            f"Tier of {tier} updated in trial system. Now requires {trials} trials.")
                else:
                    await cursor.execute("INSERT INTO AA_Trials (Tier, Trials, Trials_Required) VALUES (?, ?, ?)",
                                         (tier, trials, center_trials_required))
                    await interaction.followup.send(
                        f"Tier of {tier} added to trial system. It requires {trials} trials.")
                await conn.commit()

            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"An error occurred whilst updating tier cap! input values of: {tier}, {trials} in server {interaction.guild.id} by {interaction.user.name}': {e}"
                )
                await interaction.followup.send(
                    f"An error occurred whilst fetching data. Please try again later.",
                    ephemeral=True
                )

    test_group = discord.app_commands.Group(
        name='test',
        description='Test commands for the bot for testing certain features.',
        parent=admin_group
    )

    @test_group.command(name='worldanvil', description='Test command for the worldanvil API')
    async def worldanvil(self, interaction: discord.Interaction):
        """This is a test command for the wa command."""
        await interaction.followup.defer(thinking=True)
        client = WaClient(
            'Pathparser',
            'https://github.com/Solfyrism/Pathparser',
            'V1.1',
            os.getenv('WORLD_ANVIL_API'),  # This is the token for the bot
            os.getenv(f'WORLD_ANVIL_{interaction.guild_id}')  # This is the token for the guild
        )
        try:
            authenticated_user = client.user.identity()
            worlds = [world for world in client.user.worlds(authenticated_user['id'])]
            # categories = [category for category in client.world.categories('f7a60480-ea15-4867-ae03-e9e0c676060a')]
            await interaction.followup.send(
                f"Authenticated User Connection Successful: {authenticated_user}\r\nWorlds: {worlds}")
        except Exception as e:
            # If the user is not authenticated, the bot will raise an exception. I don't know the intended exceptions. but this is to tell the user it failed
            await interaction.followup.send(f"An error occurred: {e}")
            logging.exception("An error occurred whilst testing the WorldAnvil API")

    archive = discord.app_commands.Group(
        name='archive',
        description='display players from the archive, and archive inactive players',
        parent=admin_group
    )

    @archive.command(name='display', description='Display players from the archive')
    async def display_archive(self, interaction: discord.Interaction, player_name: typing.Optional[discord.Member],
                              character_name: typing.Optional[str],
                              page_number: int = 1):
        """Display character information.
                Display A specific view when a specific character is provided,
                refine the list of characters when a specific player is provided."""
        guild_id = interaction.guild_id
        await interaction.response.defer(thinking=True)

        try:
            async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
                cursor = await conn.cursor()

                # Decide which query to execute based on whether 'name' is provided
                if not player_name:
                    await cursor.execute("SELECT COUNT(Character_Name) FROM Archive_Player_Characters")
                else:
                    await cursor.execute(
                        "SELECT COUNT(Character_Name) FROM Archive_Player_Characters WHERE Player_Name = ?",
                        (player_name.name,))
                character_count = await cursor.fetchone()
                (character_count,) = character_count
                if character_name:
                    view_type = 2
                    await cursor.execute(
                        "SELECT character_name from Archive_Player_Characters where Character_Name = ?",
                        (character_name,))
                    character = await cursor.fetchone()
                    if not character:
                        await interaction.followup.send(
                            f"Character '{character_name}' not found.",
                            ephemeral=True
                        )
                        return
                    else:
                        if player_name:
                            await cursor.execute(
                                "SELECT character_name from Archive_Player_Characters WHERE Player_Name = ? ORDER BY True_Character_Name asc",
                                (player_name.name,))
                        else:
                            await cursor.execute(
                                "SELECT character_name from Archive_Player_Characters ORDER BY True_Character_Name asc")
                        results = await cursor.fetchall()
                        offset = results.index(character[0]) + 1
                else:
                    view_type = 1

                # Set up pagination variables
                page_number = min(max(page_number, 1), ceil(character_count / 20))
                items_per_page = 5 if view_type == 1 else 1
                offset = (page_number - 1) * items_per_page if view_type == 1 else offset

                # Create and send the view with the results
                view = ArchiveDisplayView(
                    user_id=interaction.user.id,
                    guild_id=guild_id,
                    player_name=player_name.name,
                    character_name=character_name,
                    limit=items_per_page,
                    offset=offset,
                    view_type=view_type,
                    interaction=interaction
                )
                await view.update_results()
                await view.create_embed()
                await interaction.followup.send(embed=view.embed, view=view)

        except (aiosqlite.Error, TypeError, ValueError) as e:
            logging.exception(
                f"An error occurred whilst fetching data and creating views! {e}"
            )
            await interaction.followup.send(
                f"An error occurred whilst fetching data. Please try again later.",
                ephemeral=True
            )

    @archive.command(name='inactive', description='Archive inactive players')
    @app_commands.describe(confirmation="if yes, remove all inactive players!")
    @app_commands.choices(
        confirmation=[discord.app_commands.Choice(name='No!', value=1),
                      discord.app_commands.Choice(name='Yes!', value=2)])
    async def archive_inactive(self, interaction: discord.Interaction, player_name: typing.Optional[str],
                               character_name: typing.Optional[str],
                               confirmation: discord.app_commands.Choice[int]):
        """Archive inactive players."""
        guild_id = interaction.guild_id
        guild = interaction.guild
        await interaction.response.defer(thinking=True)
        async with aiosqlite.connect(f"Pathparser_{guild_id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                if confirmation == 1:
                    await interaction.followup.send(
                        f"Archive Inactive Players has been cancelled.",
                        ephemeral=True
                    )
                    return
                else:
                    if character_name:
                        await cursor.execute(
                            "SELECT player_id, player_name, character_name FROM Player_Characters WHERE Character_Name = ?",
                            (character_name,))
                        player_info = await cursor.fetchone()
                        retirement_type = 2
                        if not player_info:
                            await interaction.followup.send("No character found with that name to archive.")
                            return

                    elif player_name:
                        await cursor.execute(
                            "SELECT player_id, player_name, character_name FROM Player_Characters WHERE Player_Name = ?",
                            (player_name,))
                        player_info = await cursor.fetchone()
                        retirement_type = 1
                        if not player_info:
                            await interaction.followup.send("No player found with that name to archive.")
                            return
                    else:
                        retirement_type = 3
                    await cursor.execute("SELECT Search From Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    bio_channel = await cursor.fetchone()
                    accepted_bio_channel = bio_channel[0]
                    if not accepted_bio_channel:
                        await interaction.followup.send(
                            "No accepted bio channel found. Please set an accepted bio channel to continue.")
                        return
                    content = "These player characters will be moved to an Archived table and their Character Bios cleared from the server."
                    view = ArchiveCharactersView(retirement_type=retirement_type, player_name=player_name,
                                                 character_name=character_name, guild=guild,
                                                 accepted_bio_channel=accepted_bio_channel,
                                                 content=content, interaction=interaction)
                    await view.send_initial_message()

            except (aiosqlite.Error, TypeError, ValueError) as e:
                logging.exception(
                    f"An error occurred whilst archiving inactive players! input values of player_name: {player_name}, character_name: {character_name}': {e}"
                )
                await interaction.followup.send(
                    f"An error occurred whilst archiving inactive players. Please try again later.",
                    ephemeral=True
                )


class MilestoneDisplayView(shared_functions.ShopView):
    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int, interaction: discord.Interaction):
        super().__init__(user_id, guild_id, offset, limit, content="", interaction=interaction)
        self.max_items = None  # Cache total number of items

    async def update_results(self):
        """fetch the level information."""
        statement = """
            SELECT Level, Minimum_Milestones, Milestones_to_level, easy, medium, hard, deadly, WPL, WPL_Heroic, Level_range_name, Level_Range_ID
            FROM Milestone_System   
            ORDER BY Tier ASC LIMIT ? OFFSET ? 
        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}_test.sqlite") as db:
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
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}_test.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM Milestone_System")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class MythicDisplayView(shared_functions.ShopView):
    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int, interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, content="",
                         interaction=interaction)
        self.max_items = None  # Cache total number of items

    async def update_results(self):
        """fetch the level information."""
        statement = """
            SELECT Tier, Trials, Trials_Required
            FROM AA_Trials   
            ORDER BY LEVEL ASC LIMIT ? OFFSET ? 
        """
        async with aiosqlite.connect(f"Pathparser_{self.guild_id}_test.sqlite") as db:
            cursor = await db.execute(statement, (self.limit, self.offset - 1))
            self.results = await cursor.fetchall()

    async def create_embed(self):
        """Create the embed for the levels."""
        current_page = ((self.offset - 1) // self.limit) + 1
        total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
        self.embed = discord.Embed(title=f"Mythic System",
                                   description=f"Page {current_page} of {total_pages}")
        for tier in self.results:
            (tier, trials, trials_required) = tier
            self.embed.add_field(name=f'**Mythic Tier**: {tier}',
                                 value=f'**Minimum Trials:**: {trials}, Milestones to increase tier: {trials_required}',
                                 inline=False)

    async def get_max_items(self):
        """Get the total number of levels."""
        if self.max_items is None:
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}_test.sqlite") as db:
                cursor = await db.execute("SELECT COUNT(*) FROM AA_Trials")
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items


class ArchiveDisplayView(shared_functions.DualView):
    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int, player_name: str, character_name: str,
                 view_type: int, interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, view_type=view_type,
                         content="", interaction=interaction)
        self.max_items = None  # Cache total number of items
        self.character_name = character_name
        self.view_type = view_type
        self.player_name = player_name

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""
        try:
            if not self.player_name:
                statement = """SELECT player_name, player_id, True_Character_Name, Title, Titles, Description, Oath, Level, 
                                Milestones, Tier, Trials, Gold, Gold_Value, Gold_Value_Max,
                                Essence, Fame, Prestige, Mythweavers, Image_Link, Tradition_Name, 
                                Tradition_Link, Template_Name, Template_Link, Article_Link
                                FROM Archive_Player_Characters ORDER BY True_Character_Name ASC LIMIT ? OFFSET ?"""
                val = (self.limit, self.offset - 1)

            else:
                statement = """SELECT player_name, player_id, True_Character_Name, Title, Titles, Description, Oath, Level, 
                                Milestones, Tier, Trials, Gold, Gold_Value, Gold_Value_Max,
                                Essence, Fame, Prestige, Mythweavers, Image_Link, Tradition_Name, 
                                Tradition_Link, Template_Name, Template_Link, Article_Link
                                FROM Archive_Player_Characters WHERE Player_Name = ? ORDER BY True_Character_Name ASC LIMIT ? OFFSET ? """
                val = (self.player_name, self.limit, self.offset - 1)
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}_test.sqlite") as db:
                cursor = await db.execute(statement, val)
                self.results = await cursor.fetchall()
        except aiosqlite.Error as e:
            logging.exception(
                f"An error occurred whilst fetching data for the archive! input values of player_name: {self.player_name}, character_name: {self.character_name}': {e}"
            )

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
                (player_name, player_id, true_character_name, title, titles, description, oath, level,
                 milestones, tier, trials, gold, gold_value, gold_value_max,
                 essence, fame, prestige, mythweavers, image_link, tradition_name,
                 tradition_link, template_name, template_link, article_link) = result
                self.embed.add_field(name=f'Character Name', value=f'**Name**:{true_character_name}')
                self.embed.add_field(name=f'Information',
                                     value=f'**Level**: {level}, **Mythic Tier**: {tier}')
                self.embed.add_field(name=f'Total Experience',
                                     value=f'**Milestones**: {milestones}, **Trials**: {trials}')
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
                (player_name, player_id, true_character_name, title, titles, description, oath, level,
                 milestones, tier, trials, gold, gold_value, gold_value_max,
                 essence, fame, prestige, mythweavers, image_link, tradition_name,
                 tradition_link, template_name, template_link, article_link) = result
                self.embed = discord.Embed(title=f"Detailed view for {true_character_name}",
                                           description=f"Page {current_page} of {total_pages}")
                self.embed.set_author(name=f'{player_name}')
                self.embed.set_thumbnail(url=f'{image_link}')
                self.embed.add_field(name=f'Character Name', value=f'**Name**:{true_character_name}')
                self.embed.add_field(name=f'Information',
                                     value=f'**Level**: {level}, **Mythic Tier**: {tier}')
                self.embed.add_field(name=f'Total Experience',
                                     value=f'**Milestones**: {milestones}, **Trials**: {trials},')
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
            async with aiosqlite.connect(f"Pathparser_{self.guild_id}_test.sqlite") as db:
                if not self.player_name:
                    cursor = await db.execute("SELECT COUNT(*) FROM Archive_Player_Characters")
                else:
                    cursor = await db.execute("SELECT COUNT(*) FROM Archive_Player_Characters WHERE Player_Name = ?",
                                              (self.player_name,))
                count = await cursor.fetchone()
                self.max_items = count[0]
        return self.max_items

    async def on_view_change(self):
        self.view_type = 1 if self.view_type == 2 else 2
        if self.view_type == 1:
            self.limit = 5  # Change the limit to 5 for the summary view
        else:
            self.limit = 1  # Change the limit to 1 for the detailed view


# *** DUAL VIEWS ***
class SettingDisplayView(shared_functions.DualView):
    def __init__(self, user_id: int, guild_id: int, offset: int, limit: int, view_type: int,
                 interaction: discord.Interaction):
        super().__init__(user_id=user_id, guild_id=guild_id, offset=offset, limit=limit, view_type=view_type,
                         content="", interaction=interaction)
        self.max_items = None  # Cache total number of items
        self.view_type = view_type

    async def update_results(self):
        """Fetch the history of prestige request  for the current page."""
        try:
            statement = """SELECT Search, Type, Identifier, Description FROM Admin Limit ? OFFSET ?"""
            val = (self.limit, self.offset - 1)

            async with aiosqlite.connect(f"Pathparser_{self.guild_id}_test.sqlite") as db:
                cursor = await db.execute(statement, val)
                self.results = await cursor.fetchall()
        except Exception as e:
            logging.exception(
                f"An error occurred whilst fetching data and creating views! {e}"
            )

    async def create_embed(self):
        """Create the embed for the titles."""
        try:
            if self.view_type == 1:

                current_page = ((self.offset - 1) // self.limit) + 1
                total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
                self.embed = discord.Embed(title=f"Settings Summary",
                                           description=f"Page {current_page} of {total_pages}")
                for result in self.results:
                    (search, data_type, identifier, description) = result
                    self.embed.add_field(name=f'{data_type}: {identifier}',
                                         value=f'current setting: {search}\r\n{description}',
                                         inline=False)
            else:
                current_page = ((self.offset - 1) // self.limit) + 1
                total_pages = ((await self.get_max_items() - 1) // self.limit) + 1
                for result in self.results:
                    (search, data_type, identifier, description) = result
                    self.embed = discord.Embed(title=f"Setting Details",
                                               description=f"Page {current_page} of {total_pages}")
                    self.embed.add_field(name=f'{data_type}: {identifier}',
                                         value=f'current setting: {search}\r\n{description}',
                                         inline=False)
        except Exception as e:
            logging.exception(
                f"An error occurred whilst fetching data and creating views! {e}"
            )

    async def get_max_items(self):
        """Get the total number of titles."""
        try:
            if self.max_items is None:
                async with aiosqlite.connect(f"Pathparser_{self.guild_id}_test.sqlite") as db:
                    cursor = await db.execute("SELECT COUNT(*) FROM Admin")
                    count = await cursor.fetchone()
                    self.max_items = count[0]
            return self.max_items
        except Exception as e:
            logging.exception(
                f"An error occurred whilst fetching data and creating views! {e}"
            )

    async def on_view_change(self):
        try:
            self.view_type = 1 if self.view_type == 2 else 2
            if self.view_type == 1:
                self.limit = 20  # Change the limit to 20 for the summary view
            else:
                self.limit = 1  # Change the limit to 1 for the detailed view
        except Exception as e:
            logging.exception(
                f"An error occurred whilst fetching data and creating views! {e}"
            )

        # *** ACKNOWLEDGEMENT VIEWS ***


class ResetDatabaseView(shared_functions.SelfAcknowledgementView):
    def __init__(self, content: str, interaction: discord.Interaction):
        super().__init__(content=content, interaction=interaction)
        self.embed = None

    async def accepted(self, interaction: discord.Interaction):
        """Handle the approval logic."""
        # Update the database to mark the proposition as accepted
        # Adjust prestige, log the transaction, notify the requester, etc.
        self.embed = discord.Embed(
            title="Database Reset Successful",
            description=f"{interaction.user.name} actually wanted me gone. :'(",
            color=discord.Color.green()
        )
        time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        shutil.copyfile(f"C:/pathparser/pathparser_{interaction.guild.id}_test.sqlite",
                        f"C:/pathparser/pathparser_{interaction.guild.id}_{time}_test.sqlite")
        shutil.copyfile(f"C:/pathparser/pathparser_test.sqlite",
                        f"C:/pathparser/pathparser_{interaction.guild.id}_test.sqlite")

        # Additional logic such as notifying the requester

    async def rejected(self, interaction: discord.Interaction):
        """Handle the rejection logic."""
        # Update the database to mark the proposition as rejected
        self.embed = discord.Embed(
            title="Database Reset Rejected",
            description=f"{interaction.user.name} has decided to keep me around. :)",
            color=discord.Color.red()
        )
        # Additional logic such as notifying the requester

    async def create_embed(self):
        """Create the initial embed for the proposition."""
        self.embed = discord.Embed(
            title="Database Reset",
            description="Are you sure you want to reset the database? This action is inconvenient to reverse and may result in data inconsistency.",
            color=discord.Color.blue()
        )


class ArchiveCharactersView(shared_functions.SelfAcknowledgementView):
    def __init__(self, retirement_type, player_name: typing.Optional[str], character_name: typing.Optional[str],
                 guild: discord.Guild, accepted_bio_channel: int, content: str, interaction: discord.Interaction):
        super().__init__(content=content, interaction=interaction)
        self.embed = None
        self.retirement_type = retirement_type
        self.player_name = player_name
        self.character_name = character_name
        self.guild = guild
        self.accepted_bio_channel = accepted_bio_channel
        self.items_to_be_archived = []
        self.items_to_be_deleted = []
        self.results = None

    async def accepted(self, interaction: discord.Interaction):
        """Handle the approval logic."""
        # Update the database to mark the proposition as accepted
        # Adjust prestige, log the transaction, notify the requester, etc.
        self.embed = discord.Embed(
            title="Archive Attempt",
            description=f"{interaction.user.name} has successfully archived the following characters.",
            color=discord.Color.green()
        )
        self.embed.add_field(name=f'Characters Archived', value=f'{self.items_to_be_archived}')
        async with aiosqlite.connect(f"Pathparser_{self.guild.id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            placeholders = ', '.join(
                '?' for _ in self.items_to_be_archived)  # Create the correct number of placeholders
            query = (f"""INSERT INTO Archive_Player_Characters (Player_ID, Player_Name, True_Character_Name, Character_Name, Title, Titles, Description, Oath, Level, Milestones, Tier, Trials, Gold, Gold_Value, Gold_Value_Max, Essence, Fame, Prestige, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Article_Link)
                        SELECT Player_ID, Player_Name, True_Character_Name, Character_Name, Title, Titles, Description, Oath, Level, Milestones, Tier, Trials, Gold, Gold_Value, Gold_Value_Max, Essence, Fame, Prestige, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Article_Link
                        FROM Player_Characters WHERE Character_Name IN ({placeholders})""")
            await cursor.execute(query, self.items_to_be_archived)
            await conn.commit()
            bio_channel = self.guild.get_channel(self.accepted_bio_channel)
            if not bio_channel:
                bio_channel = await self.guild.fetch_channel(self.accepted_bio_channel)
            for item in self.items_to_be_deleted:
                message = await bio_channel.fetch_message(item[0])
                await message.delete()
                logging_thread = self.guild.get_channel(item[1])
                if not logging_thread:
                    logging_thread = await self.guild.fetch_channel(item[1])
                await logging_thread.send("Character has been archived.")
        # Additional logic such as notifying the requester

    async def rejected(self, interaction: discord.Interaction):
        """Handle the rejection logic."""
        # Update the database to mark the proposition as rejected
        self.embed = discord.Embed(
            title="Database Reset Rejected",
            description=f"{interaction.user.name} has decided to keep me around. :)",
            color=discord.Color.red()
        )
        # Additional logic such as notifying the requester

    async def create_embed(self):
        """Create the initial embed for the proposition."""
        self.embed = discord.Embed(
            title="Character Archive",
            description="Are you sure you want to Archive the following characters?",
            color=discord.Color.blue()
        )
        async with aiosqlite.connect(f"Pathparser_{self.guild.id}_test.sqlite") as conn:
            cursor = await conn.cursor()
            try:
                if self.retirement_type == 1:
                    await cursor.execute(
                        "SELECT True_Character_Name, Message_ID, Thread_ID  FROM Player_Characters WHERE Player_Name = ?",
                        (self.player_name,))
                    results = await cursor.fetchall()
                    for result in results:
                        self.items_to_be_archived.append(result[0])
                        self.items_to_be_deleted.append((result[1], result[2]))
                        self.embed.add_field(name=f'{result[0]}', value=f'**Player**: {self.player_name}')
                elif self.retirement_type == 2:
                    await cursor.execute(
                        "SELECT True_Character_Name, Message_ID, Thread_ID  FROM Player_Characters WHERE Character_Name = ?",
                        (self.character_name,))
                    results = await cursor.fetchone()
                    self.items_to_be_archived.append(results[0])
                    self.items_to_be_deleted.append((results[1], results[2]))
                    self.embed.add_field(name=f'{results[0]}', value=f'**Player**: {self.player_name}')
                else:
                    await cursor.execute("SELECT DISTINCT(Player_ID)  FROM Player_Characters")
                    player_ids = await cursor.fetchall()
                    for player_id in player_ids:
                        find_player = await self.guild.fetch_member(player_id[0])
                        if not find_player:
                            character_list = ''
                            await cursor.execute(
                                "SELECT True_Character_Name, Message_ID, Thread_ID  FROM Player_Characters WHERE Player_ID = ?",
                                (player_id[0],))
                            results = await cursor.fetchall()
                            for result in results:
                                self.items_to_be_archived.append(result[0])
                                self.items_to_be_deleted.append((result[1], result[2]))
                                character_list += f'{result[0]}\r\n'
                            self.embed.add_field(name=f'**Player**: {find_player.name}', value=character_list)
            except (aiosqlite.Error, TypeError, ValueError, NameError) as e:
                logging.exception(
                    f"An error occurred whilst archiving characters! ViewType: {self.retirement_type} input values of player_name: {self.player_name}, character_name: {self.character_name}': {e}"
                )
                self.embed = discord.Embed(
                    title='Error',
                    description=f"An error occurred whilst archiving characters. Please try again later.",
                )


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='pathparser.log',  # Specify the log file name
    filemode='a'  # Append mode
)
