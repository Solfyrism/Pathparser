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


class ReviewerCommands(commands.Cog, name='Reviewer'):
    def __init__(self, bot):
        self.bot = bot

    registration_group = discord.app_commands.Group(
        name='registration',
        description='Commands related to accepting or rejecting registrations for new characters.'
    )

    @registration_group.command()
    @app_commands.describe(player_wipe="if yes, remove all inactive players!")
    @app_commands.choices(
        player_wipe=[discord.app_commands.Choice(name='No!', value=1),
                     discord.app_commands.Choice(name='Yes!', value=2)])
    async def wipe(interaction: discord.Interaction, player: typing.Optional[discord.Member],
                               player_id: typing.Optional[int], player_wipe: discord.app_commands.Choice[int] = 1):
        """Clean out the entire playerbase or clean out a specific player's character by mentioning them or using their role!"""
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

    @registration_group.command()
    @app_commands.autocomplete(character_name=stg_character_select_autocompletion)
    @app_commands.describe(
        cleanse="Optional: supply a number ending with D or W to remove users who have not been accepted within that period!")
    @app_commands.describe(status="Accepted players are moved into active and posted underneath!")
    @app_commands.choices(status=[discord.app_commands.Choice(name='Accepted!', value=1),
                                  discord.app_commands.Choice(name='Rejected!', value=2)])
    async def manage(self, interaction: discord.Interaction, character_name: str, player_id: typing.Optional[int],
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
                embed.add_field(name="Information", value=f'**Level**: 3, **Mythic Tier**: 0, **Fame**: 0',
                                inline=False)
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
                    await interaction.followup.send(f"{character_name} could not be found in the database.",
                                                    ephemeral=True)
                else:
                    interaction.send(f"{character_name} has been accepted into the server!")

    @registration_group.command()
    @app_commands.autocomplete(character_name=character_select_autocompletion)
    @app_commands.describe(
        destination="Shorthand for determining whether you are looking for a character name or nickname")
    @app_commands.choices(destination=[discord.app_commands.Choice(name='Tradition', value=1),
                                       discord.app_commands.Choice(name='Template', value=2)])
    @app_commands.describe(customized_name="For the name of the template or tradition")
    async def customize(interaction: discord.Interaction, character_name: str,
                        destination: discord.app_commands.Choice[int],
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
            await interaction.followup.send(
                f"no character with the Name or Nickname of {character_name} could be found!",
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
                                        player_info[16] + essence_cost, player_info[17], player_info[18],
                                        player_info[19],
                                        player_info[20], player_info[21], player_info[22], player_info[23],
                                        player_info[27],
                                        player_info[28], player_info[30], player_info[31])
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"changed a template or tradition for {character_name}"
            logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, None,
                                      None,
                                      None, None, player_info[16] - essence_cost, essence_cost, tradition_name,
                                      tradition_link,
                                      template_name, template_link, None, None, None, None, None, source)
            logging_thread = guild.get_thread(player_info[25])
            await logging_thread.send(embed=logging_embed)
            await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))


logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='application.log',  # Log to a file
    filemode='a'  # Append to the file
)
