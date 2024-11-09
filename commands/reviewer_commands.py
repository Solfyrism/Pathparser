import logging
import shutil
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


async def register_character_embed(character_name: str, guild: discord.Guild) -> Union[
    Tuple[discord.Embed, str, int, int], str]:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild.id}.sqlite") as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.cursor()

            # Fetch channel ID
            await cursor.execute("SELECT Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            channel_id_row = await cursor.fetchone()
            if not channel_id_row:
                return f"No channel found with Identifier 'Accepted_Bio_Channel' in Admin table."
            channel_id = channel_id_row['Search']

            # Fetch character info
            await cursor.execute(
                "
                SELECT player_name, player_id, True_Character_Name, Title, Titles, Description, Oath, Level,
                       Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value,
                       Essence, Fame, Prestige, Color, Mythweavers, Image_Link, Tradition_Name,
                       Tradition_Link, Template_Name, Template_Link, Article_Link, Message_ID
                FROM Player_Characters WHERE Character_Name = ?
                ", (character_name,))
            character_info = await cursor.fetchone()
            if not character_info:
                return f"No character found with Character_Name '{character_name}'."

        # Unpack character_info using column names
        player_name = character_info['player_name']
        player_id = character_info['player_id']
        true_character_name = character_info['True_Character_Name']
        title = character_info['Title']
        titles = character_info['Titles']
        description = character_info['Description']
        oath = character_info['Oath']
        level = character_info['Level']
        tier = character_info['Tier']
        milestones = character_info['Milestones']
        milestones_required = character_info['Milestones_Required']
        trials = character_info['Trials']
        trials_required = character_info['Trials_Required']
        gold = character_info['Gold']
        gold_value = character_info['Gold_Value']
        essence = character_info['Essence']
        fame = character_info['Fame']
        prestige = character_info['Prestige']
        color = character_info['Color']
        mythweavers = character_info['Mythweavers']
        image_link = character_info['Image_Link']
        tradition_name = character_info['Tradition_Name']
        tradition_link = character_info['Tradition_Link']
        template_name = character_info['Template_Name']
        template_link = character_info['Template_Link']
        article_link = character_info['Article_Link']
        message_id = character_info['Message_ID']

        # Convert color to integer
        try:
            int_color = int(color.lstrip('#'), 16)
        except ValueError:
            int_color = 0x000000  # Default color if invalid

        # Build embed description
        description_field = ""
        if titles:
            description_field += f"**Other Names**: {titles}\n"
        if article_link:
            description_field += f"[**Backstory**]({article_link})"

        titled_character_name = true_character_name if not title else f"{title} {true_character_name}"

        embed = discord.Embed(
            title=titled_character_name,
            url=mythweavers,
            description=description_field,
            color=int_color
        )
        embed.set_author(name=player_name)
        embed.set_thumbnail(url=image_link)
        embed.add_field(
            name="Information",
            value=f'**Level**: {level}, **Mythic Tier**: {tier}\n**Fame**: {fame}, **Prestige**: {prestige}',
            inline=False
        )
        embed.add_field(
            name="Experience",
            value=f'**Milestones**: {milestones}, **Remaining**: {milestones_required}'
        )
        embed.add_field(
            name="Mythic",
            value=f'**Trials**: {trials}, **Remaining**: {trials_required}'
        )
        embed.add_field(
            name="Current Wealth",
            value=f'**GP**: {Decimal(gold)}, **Effective**: {Decimal(gold_value)} GP',
            inline=False
        )
        embed.add_field(
            name="Current Essence",
            value=f'**Essence**: {essence}'
        )

        # Additional Info
        linkage = ""
        if tradition_name:
            linkage += f"**Tradition**: [{tradition_name}]({tradition_link})"
        if template_name:
            if tradition_name:
                linkage += " "
            linkage += f"**Template**: [{template_name}]({template_link})"
        if linkage:
            embed.add_field(name='Additional Info', value=linkage, inline=False)

        # Footer with Oath
        oath_icons = {
            'Offerings': 'https://i.imgur.com/dSuLyJd.png',
            'Poverty': 'https://i.imgur.com/4Fr9ZnZ.png',
            'Absolute': 'https://i.imgur.com/ibE5vSY.png'
        }
        icon_url = oath_icons.get(oath)
        embed.set_footer(text=description, icon_url=icon_url)

        message_content = f"<@{player_id}>"

        # Fetch the bio channel
        bio_channel = guild.get_channel(channel_id)
        if bio_channel is None:
            bio_channel = await guild.fetch_channel(channel_id)
        if bio_channel is None:
            return f"Channel with ID {channel_id} not found."

        # Fetch and edit the message
        try:
            bio_message = await bio_channel.send(content=message_content, embed=embed,
                                                 allowed_mentions=discord.AllowedMentions(users=True))
        except discord.Forbidden:
            return "Bot lacks permissions to send the message."
        except discord.HTTPException as e:
            logging.exception(f"Discord error while sending message: {e}")
            return "An error occurred while sending the message."

        return embed, message_content, channel_id, bio_message.id

    except aiosqlite.Error as e:
        logging.exception(f"Database error: {e}")
        return f"An error occurred with the database."
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        return f"An unexpected error occurred while building character embed for '{character_name}'."


class ReviewerCommands(commands.Cog, name='Reviewer'):
    def __init__(self, bot):
        self.bot = bot

    reviewer_group = discord.app_commands.Group(
        name='reviewer',
        description='Reviewer Roots commands.'
    )

    registration_group = discord.app_commands.Group(
        name='registration',
        description='Commands related to registration.',
        parent=reviewer_group
    )

    @registration_group.command()
    @app_commands.describe(player_wipe="if yes, remove all inactive players!")
    @app_commands.choices(
        remove=[discord.app_commands.Choice(name='No!', value=1),
                discord.app_commands.Choice(name='Yes!', value=2)])
    async def wipe(self, interaction: discord.Interaction, cleanse: str, remove: discord.app_commands.Choice[int]):
        "Clean out the entire stging base or clean out a specific player's character by mentioning them or using their role!"
        await interaction.followup.defer(thinking=True)
        try:
            if cleanse.endswith('D'):
                cleanse = cleanse.replace('D', '')
                cleanse_in_days = int(cleanse)
            elif cleanse.endswith('W'):
                cleanse = cleanse.replace('W', '')
                cleanse_in_days = int(cleanse) * 7
            else:
                cleanse_in_days = int(cleanse)
            guild_id = interaction.guild_id
            # Create and send the view with the results
            view = CleanOldRegistrationView(
                days=cleanse_in_days,
                guild_id=guild_id,
            )
            await view.create_embed()
            await interaction.followup.send(embed=view.embed, view=view)


        except (AttributeError, TypeError) as e:
            logging.exception(f"Error in cleanse. {cleanse} was not valid. {e}")
            await interaction.followup.send(f"Error in cleanse. {cleanse} was not valid.", ephemeral=True)

    @registration_group.command()
    @app_commands.autocomplete(character_name=shared_functions.stg_character_select_autocompletion)
    @app_commands.describe(status="Accepted players are moved into active and posted underneath!")
    @app_commands.choices(status=[discord.app_commands.Choice(name='Accepted!', value=1),
                                  discord.app_commands.Choice(name='Rejected!', value=2)])
    async def manage(self, interaction: discord.Interaction, character_name: str,
                     status: discord.app_commands.Choice[int]):
        "accept a player into your accepted bios, or Remove them."
        guild = interaction.guild
        guild_id = interaction.guild_id
        async with aiosqlite.connect(f"C:/pathparser/pathparser_{guild_id}.sqlite") as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.cursor()
            _, character_name = name_fix(character_name)
            await cursor.execute(
                "Select Player_Name, Player_ID, True_Character_Name, Character_Name, Nickname, Titles, Description,
                Oath, Tier, Trials, Trials_Required,
                 Essence, Color, Mythweavers, Image_Link, tmp_bio
                 FROM A_STG_Player_Characters where Character_Name = ?",
                (character_name,))
            player_info = await cursor.fetchone()
            if not player_info:
                await interaction.followup.send(
                    f"no character with the Name or Nickname of {character_name} could be found!",
                    ephemeral=True)
            else:
                if status.value == 2:
                    await cursor.execute("DELETE FROM A_STG_Player_Characters WHERE Character_Name = ?",
                                         (character_name,))
                    await db.commit()
                    await interaction.followup.send(f"{character_name} has been removed from the STG database.",
                                                    ephemeral=True)
                else:
                    info_player_name = player_info['player_name']
                    info_player_id = player_info['player_id']
                    info_true_character_name = player_info['True_Character_Name']
                    info_character_name = player_info['character_name']
                    info_nickname = player_info['nickname']
                    info_titles = player_info['titles']
                    info_description = player_info['description']
                    info_oath = player_info['oath']
                    info_tier = player_info['tier']
                    info_trials = player_info['trials']
                    info_trials_required = player_info['trials_required']
                    info_essence = player_info['essence']
                    info_color = player_info['color']
                    info_mythweavers = player_info['mythweavers']
                    info_image_link = player_info['image_link']
                    info_tmp_bio = player_info['tmp_bio']
                    await cursor.execute("Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                    character_log_channel_id = await cursor.fetchone()
                    await cursor.execute("SELECT search from admin where identifier = 'WA_Backstory_Category'")
                    backstory_category = await cursor.fetchone()
                    await cursor.execute("SELECT search from admin where identifier = 'Starting_Level'")
                    starting_level = await cursor.fetchone()
                    await cursor.execute(
                        "SELECT Minimum_Milestones, Milestones_to_level, WPL FROM Milestone_System where level = ?",
                        (starting_level[0],))
                    starting_level_info = await cursor.fetchone()
                    if not starting_level_info:
                        await interaction.followup.send(
                            f"Starting Level not found! Ask your Admin to check server settings!",
                            ephemeral=True)
                    else:
                        (info_minimum_milestones, info_milestones_to_level, info_wpl) = starting_level_info
                        gold_calculation = character_commands.gold_calculation(
                            guild_id=guild_id,
                            level=starting_level[0],
                            author_name=interaction.user.name,
                            author_id=interaction.user.id,
                            character_name=info_character_name,
                            oath=info_oath,
                            gold=Decimal(0),
                            gold_value=Decimal(0),
                            gold_value_max=Decimal(0),
                            gold_change=Decimal(3000),
                            gold_value_change=Decimal(0),
                            gold_value_max_change=Decimal(0),
                            reason="Character Registration",
                            source="Character Registration")
                    if isinstance(gold_calculation, tuple):
                        (gold_difference, gold_total, gold_value_total, gold_value_max_total,
                         transaction_id) = gold_calculation
                    await cursor.execute(
                        "INSERT INTO Player_Characters (Player_Name, Player_ID, True_Character_Name, Character_Name,
                        Nickname, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required,
                        Gold, Gold_Value, Gold_value_Max, Essence, Color, Mythweavers, Image_Link, Fame) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (info_player_name, info_player_id, info_true_character_name, info_character_name,
                         info_nickname, info_titles, info_description, info_oath, starting_level[0], info_tier,
                         info_minimum_milestones, info_milestones_to_level, info_trials, info_trials_required,
                         gold_total, gold_value_total, gold_value_max_total, info_essence, info_color, info_mythweavers,
                         info_image_link, 0))
                    await db.commit()
                    await cursor.execute("DELETE FROM A_STG_Player_Characters WHERE Character_Name = ?",
                                         (character_name,))
                    await db.commit()

                    character_embed_info = await register_character_embed(character_name, guild)
                    embed = discord.Embed(title=f"{info_character_name}", url=f'{info_mythweavers}',
                                          description=f"Other Names: {info_titles}", color=int(info_color[1:], 16))
                    embed.set_author(name=f'{info_player_name}')
                    embed.set_thumbnail(url=f'{info_image_link}')
                    character_log_channel = await interaction.guild.get_channel(character_log_channel_id[0])
                    if not character_log_channel:
                        character_log_channel = await self.bot.fetch_channel(character_log_channel_id[0])
                    character_log_message = await character_log_channel.send(content=f'<@{info_player_id}>',
                                                                             embed=embed,
                                                                             allowed_mentions=discord.AllowedMentions(
                                                                                 users=True))
                    thread = await character_log_message.create_thread(name=f'{info_true_character_name}')
                    article = await shared_functions.put_wa_article(guild_id=interaction.guild.id, template='Person',
                                                                    title=info_true_character_name,
                                                                    category=backstory_category[0],
                                                                    overview=info_tmp_bio)
                    await cursor.execute(
                        "UPDATE Player_Characters SET Article_Link = ?, Article_ID = ?, Message_ID = ?, Logging_ID, Thread_ID = ? WHERE Character_Name = ?",
                        (
                            article['url'], article['id'], character_embed_info[3], character_log_message.id, thread.id,
                            info_character_name))
                    await db.commit()
                    await interaction.followup.send(f"{character_name} has been moved to the accepted bios.",
                                                    ephemeral=True)

    customize_group = discord.app_commands.Group(
        name='customize',
        description='Commands related to costumizing a character.',
        parent=reviewer_group
    )

    customize_group.command()

    @app_commands.autocomplete(character_name=shared_functions.character_select_autocompletion)
    @app_commands.describe(
        destination="Shorthand for determining whether you are looking for a character name or nickname")
    @app_commands.describe(customized_name="For the name of the template or tradition")
    async def apply_tradition(self, interaction: discord.Interaction, character_name: str,
                              tradition_name: str, link: str, essence_cost: int):
        "Administrative: set a character's tradition!"
        character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
        guild_id = interaction.guild_id
        guild = interaction.guild
        shared_functions.extract_document_id(link)
        if not shared_functions:
            await interaction.followup.send("Invalid link provided!", ephemeral=True)
            return

        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            author = interaction.user.name
            await cursor.execute(
                "Select Character_Name, Essence, Thread_ID, FROM Player_Characters where Character_Name = ?",
                (character_name,))
            player_info = await cursor.fetchone()

            if player_info is None:
                await interaction.followup.send(
                    f"no character with the Name of {character_name} could be found!",
                    ephemeral=True)
            else:
                (character_name, essence, logging_thread) = player_info
                essence_calculation = character_commands.calculate_essence(
                    character_name=character_name,
                    essence=essence,
                    essence_change=-abs(essence_cost),
                    accepted_date=None
                )  # Calculate the new essence
                if isinstance(essence_calculation, tuple):
                    (essence_total, essence_change) = essence_calculation
                    character_updates = shared_functions.UpdateCharacterData(
                        character_name=character_name,
                        essence=essence_total)
                    await cursor.execute(
                        "UPDATE Player_Characters SET Essence = ?, Tradition_Name, Tradition_Link WHERE Character_Name = ?",
                        (essence_total, tradition_name, link, character_name))
                    await db.commit()
                    log_character = shared_functions.CharacterChange(
                        character_name=character_name,
                        author=author,
                        essence_change=essence_change,
                        tradition_name=tradition_name,
                        tradition_link=link,
                        source="Apply Tradition"
                    )
                    log_embed = shared_functions.log_embed(
                        change=log_character,
                        guild=guild,
                        thread=logging_thread,
                        bot=self.bot
                    )
                    await shared_functions.character_embed(character_name=character_name, guild=guild)
                    await interaction.followup.send(embed=log_embed)
                else:
                    await interaction.followup.send(essence_calculation, ephemeral=True)
                    return

    @app_commands.autocomplete(character_name=shared_functions.character_select_autocompletion)
    @app_commands.describe(
        destination="Shorthand for determining whether you are looking for a character name or nickname")
    @app_commands.describe(customized_name="For the name of the template or tradition")
    async def apply_template(self, interaction: discord.Interaction, character_name: str,
                             template_name: str, link: str, essence_cost: int):
        "Administrative: set a character's tradition!"
        character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
        guild_id = interaction.guild_id
        guild = interaction.guild
        shared_functions.extract_document_id(link)
        if not shared_functions:
            await interaction.followup.send("Invalid link provided!", ephemeral=True)
            return

        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            author = interaction.user.name
            await cursor.execute(
                "Select Character_Name, Essence, Thread_ID, FROM Player_Characters where Character_Name = ?",
                (character_name,))
            player_info = await cursor.fetchone()

            if player_info is None:
                await interaction.followup.send(
                    f"no character with the Name of {character_name} could be found!",
                    ephemeral=True)
            else:
                (character_name, essence, logging_thread) = player_info
                essence_calculation = character_commands.calculate_essence(
                    character_name=character_name,
                    essence=essence,
                    essence_change=-abs(essence_cost),
                    accepted_date=None
                )  # Calculate the new essence
                if isinstance(essence_calculation, tuple):
                    (essence_total, essence_change) = essence_calculation
                    character_updates = shared_functions.UpdateCharacterData(
                        character_name=character_name,
                        essence=essence_total)
                    await cursor.execute(
                        "UPDATE Player_Characters SET Essence = ?, template_name, template_Link WHERE Character_Name = ?",
                        (essence_total, template_name, link, character_name))
                    await db.commit()
                    log_character = shared_functions.CharacterChange(
                        character_name=character_name,
                        author=author,
                        essence_change=essence_change,
                        template_name=template_name,
                        template_link=link,
                        source="Apply Tradition"
                    )
                    log_embed = shared_functions.log_embed(
                        change=log_character,
                        guild=guild,
                        thread=logging_thread,
                        bot=self.bot
                    )
                    await shared_functions.character_embed(character_name=character_name, guild=guild)
                    await interaction.followup.send(embed=log_embed)
                else:
                    await interaction.followup.send(essence_calculation, ephemeral=True)
                    return


class CleanOldRegistrationView(shared_functions.SelfAcknowledgementView):
    def __init__(self, guild_id: int, days: int):
        super().__init__()
        self.embed = None
        self.guild_id = guild_id
        self.days = days
        self.remove_character = []

    async def accepted(self, interaction: discord.Interaction):
        "Handle the approval logic."

        self.embed = discord.Embed(
            title="Cleanse of dated characters Successful",
            description=f"{interaction.user.name} has cleaned house.",
            color=discord.Color.green()
        )
        async with aiosqlite.connect(f"C:/pathparser/pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.cursor()
            for player in self.remove_character:
                await cursor.execute("DELETE FROM A_STG_Player_Characters WHERE True_Character_Name = ?", (player,))
                await db.commit()

        # Additional logic such as notifying the requester

    async def rejected(self, interaction: discord.Interaction):
        "Handle the rejection logic."
        # Update the database to mark the proposition as rejected
        await self.update_proposition_status(is_allowed=-1)
        self.embed = discord.Embed(
            title="Database Reset Rejected",
            description=f"{interaction.user.name} has decided to keep me around. :)",
            color=discord.Color.red()
        )
        # Additional logic such as notifying the requester

    async def create_embed(self):
        "Create the initial embed for the cleanse."
        async with aiosqlite.connect(f"C:/pathparser/pathparser_{self.guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "SELECT Player_Name, True_Character_Name, Created_Date FROM A_STG_Player_Characters where Created_Date <= date('now', '-? days')",
                (self.days,))
            players = await cursor.fetchall()
            for player in players:
                self.embed.add_field(name=player[0], value=f"{player[1]} Registered on {player[2]}", inline=False)
                self.remove_character.append(player[1])


logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='application.log',  # Log to a file
    filemode='a'  # Append to the file
)
