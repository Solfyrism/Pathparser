import datetime
import re
import shutil
import typing
import discord
import sqlite3
import os
from discord import app_commands
from discord.ext import commands
from Event_List import Event
from unbelievaboat import Client
import unbelievaboat
import asyncio
import math
import random
from math import floor
from dotenv import load_dotenv; load_dotenv()
from unidecode import unidecode
from pywaclient.api import BoromirApiClient as WaClient
os.chdir("C:\\pathparser")




@player.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def join(interaction: discord.Interaction, session_id: int, character_name: str):
    """PLAYER: Offer your Participation in a session."""
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    user = interaction.user
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    await interaction.response.defer(thinking=True, ephemeral=True)
    cursor.execute(f"SELECT Session_Name, Play_location, Play_Time, game_link, Session_Range_ID, Session_Range, Session_Thread, overflow FROM Sessions WHERE Session_ID = '{session_id}' AND IsActive = 1")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.followup.send(f"No active session with Session ID: {session_id} can be found!")
    else:
        quest_thread = guild.get_thread(session_info[6])
        role = interaction.guild.get_role(session_info[4])
        if role in user.roles or session_info[7] == 4 or session_info[7] == 3 or session_info[7] == 2:
            sql = f"""Select Character_Name, Level, Gold_Value, Tier from Player_Characters where Player_Name = ? and Character_Name = ? OR Nickname = ?"""
            val = (author, character_name, character_name)
            cursor.execute(sql, val)
            character_info = cursor.fetchone()
            if character_info is None:
                await interaction.followup.send(f"Falsehoods! the Character of {character_name} either doesn't exist or belong to {author}!")
            if character_info is not None:
                cursor.execute(f"SELECT Level, Role_Name from Level_Range WHERE Role_ID = {session_info[4]}")
                level_range_info = cursor.fetchone()
                print(session_info[7])
                if level_range_info is None or session_info[7] == 4:
                    cursor.execute(f"""Select Character_Name from Sessions_Participants where Player_name = '{author}' and Session_ID = {session_id}""")
                    participation = cursor.fetchone()
                    cursor.execute(f"""Select Character_Name from Sessions_Signups where Player_name = '{author}' AND Session_ID = {session_id}""")
                    signups = cursor.fetchone()
                    if participation is None and signups is None:
                        await Event.session_join(self, guild_id, session_info[0], session_id, author, author_id, character_info[0], character_info[1], character_info[2], character_info[3])
                        sql = f"""Select Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Gold_Value, Oath from Player_characters WHERE Character_Name = ? OR Nickname = ?"""
                        val = (character_name, character_name)
                        cursor.execute(sql, val)
                        result = cursor.fetchone()
                        if result is None:
                            await interaction.followup.send(f"{character_name} is not a valid Character name or Nickname.")
                            cursor.close()
                            db.close()
                            return
                        else:
                            color = result[11]
                            int_color = int(color[1:], 16)
                            embed = discord.Embed(title="Mythweavers Sheet", url=f'{result[12]}', description=f"Other Names: {result[2]}", color=int_color, timestamp=datetime.datetime.utcnow())
                            embed.set_author(name=f'{result[0]} would like to participate')
                            embed.set_thumbnail(url=f'{result[13]}')
                            embed.add_field(name="Information", value=f'**Level**: {result[4]}, **Mythic Tier**: {result[5]}', inline=True)
                            embed.add_field(name="illiquid Wealth", value=f'**GP**: {round(result[19] - result[10],2)}', inline=True)
                            linkage = f""
                            if result[15] is not None:
                                linkage += f"**Tradition**: [{result[15]}]({result[16]})"
                            if result[17] is not None:
                                if result[15] is not None:
                                    linkage += " "
                                linkage += f"**Template**: [{result[17]}]({result[18]})"
                            if result[15] is not None or result[17] is not None:
                                embed.add_field(name=f'Additional Info', value=linkage, inline=False)
                            if result[20] == 'Offerings':
                                embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
                            elif result[20] == 'Poverty':
                                embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
                            elif result[20] == 'Absolute':
                                embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
                            else:
                                embed.set_footer(text=f'{result[3]}')
                            await quest_thread.send(embed=embed, content=f"{interaction.user.mention}", allowed_mentions=discord.AllowedMentions(users=True))
                            await interaction.followup.send(content=f"You have submitted your request! Please wait for the GM to accept or deny your request!", ephemeral=True)
                    elif participation is not None:
                        await interaction.followup.send(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
                    elif signups is not None:
                        await interaction.followup.send(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
                else:
                    if session_info[7] == 3:
                        cursor.execute(f"SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_ID = {session_info[4]}")
                        new_level_range_info = cursor.fetchone()
                        cursor.execute(f"SELECT Role_Name from Level_Range WHERE level = {new_level_range_info[0]-1}")
                        overflow_level_role = cursor.fetchone()
                        overflow_level_role = overflow_level_role if overflow_level_role is not None else new_level_range_info
                        cursor.execute(f"SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_Name = ?", (overflow_level_role[0],))
                        overflow_level_range_info = cursor.fetchone()
                        overflow_level_range_info = overflow_level_range_info if overflow_level_range_info[0] is not None else new_level_range_info
                        level_range_validation = 1 if overflow_level_range_info is not None and overflow_level_range_info[0] <= character_info[1] <= new_level_range_info[1] else 0
                    elif session_info[7] == 2:
                        cursor.execute(f"SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_ID = {session_info[4]}")
                        new_level_range_info = cursor.fetchone()
                        cursor.execute(f"SELECT Role_Name from Level_Range WHERE level = {new_level_range_info[1] + 1}")
                        overflow_level_role = cursor.fetchone()
                        overflow_level_role = overflow_level_role if overflow_level_role is not None else new_level_range_info
                        cursor.execute(f"SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_Name = ?", (overflow_level_role[0],))
                        overflow_level_range_info = cursor.fetchone()
                        overflow_level_range_info = overflow_level_range_info if overflow_level_range_info[0] is not None else new_level_range_info
                        level_range_validation = 1 if overflow_level_range_info is not None and new_level_range_info[0] <= character_info[1] <= overflow_level_range_info[1] else 0
                    else:
                        cursor.execute(f"SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_ID = {session_info[4]} AND Level = {character_info[1]}")
                        new_level_range_info = cursor.fetchone()
                        level_range_validation = 1 if new_level_range_info is not None else 0
                    if level_range_validation != 1:
                        await interaction.followup.send(f"{character_info[0]} is level {character_info[1]} which is not inside the level range of {level_range_info[1]}!", ephemeral=True)
                    else:
                        cursor.execute(f"""Select Character_Name from Sessions_Participants where Player_name = '{author}' and Session_ID = {session_id}""")
                        participation = cursor.fetchone()
                        cursor.execute(f"""Select Character_Name from Sessions_Signups where Player_name = '{author}' and Session_ID = {session_id}""")
                        signups = cursor.fetchone()
                        if participation is None and signups is None:
                            await Event.session_join(self, guild_id, session_info[0], session_id, author, author_id, character_info[0], character_info[1], character_info[2], character_info[3])
                            sql = f"""Select True_Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Gold_Value, Oath from Player_characters WHERE Character_Name = ? OR Nickname = ?"""
                            val = (character_name, character_name)
                            cursor.execute(sql, val)
                            result = cursor.fetchone()
                            if result is None:
                                await interaction.followup.send(f"{character_name} is not a valid Character Name or Nickname.")
                                cursor.close()
                                db.close()
                                return
                            else:
                                color = result[11]
                                int_color = int(color[1:], 16)
                                embed = discord.Embed(title="Mythweavers Sheet", url=f'{result[12]}',
                                                      description=f"Other Names: {result[2]}", color=int_color)
                                embed.set_author(name=f'{result[0]} would like to participate!')
                                embed.set_thumbnail(url=f'{result[13]}')
                                embed.add_field(name="Information", value=f'**Level**: {result[4]}, **Mythic Tier**: {result[5]}', inline=True)
                                embed.add_field(name="illiquid Wealth", value=f'**GP**: {round(result[19] - result[10],2)}', inline=True)
                                linkage = f""
                                print(result[15], result[17])
                                if result[15] is not None:
                                    linkage += f"**Tradition**: [{result[15]}]({result[16]})"
                                if result[17] is not None:
                                    if result[15] is not None:
                                        linkage += " "
                                    linkage += f"**Template**: [{result[17]}]({result[18]})"
                                if result[15] is not None or result[17] is not None:
                                    print(linkage)
                                    embed.add_field(name=f'Additional Info', value=linkage, inline=False)
                                if result[20] == 'Offerings':
                                    embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
                                elif result[20] == 'Poverty':
                                    embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
                                elif result[20] == 'Absolute':
                                    embed.set_footer(text=f'{result[3]}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
                                else:
                                    embed.set_footer(text=f'{result[3]}')
                                await quest_thread.send(embed=embed, content=f"{interaction.user.mention}", allowed_mentions=discord.AllowedMentions(users=True))
                                await interaction.followup.send(content=f"You have submitted your request! Please wait for the GM to accept or deny your request!")
                        elif participation is not None:
                            await interaction.followup.send(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
                        elif signups is not None:
                            await interaction.followup.send(f"{author} is already participating in {session_info[0]} with session ID: {session_id}")
        else:
            await interaction.followup.send(f"User does not have role: {session_info[5]}! If you wish to join, obtain this role! Ensure you have a character in the correct level bracket.", ephemeral=True)

@player.command()
async def leave(interaction: discord.Interaction, session_id: int):
    """PLAYER: Rescind your Participation in a session."""
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Session_Name, Play_location, Play_Time, Game_Link FROM Sessions WHERE Session_ID = '{session_id}'")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.response.send_message(f"No active session with {session_id} can be found!")
    if session_info is not None:
        cursor.execute(f"""Select Character_Name, Level, Effective_Wealth from Sessions_Signups where Player_Name = '{author}'""")
        character_info = cursor.fetchone()
        if character_info is None:
            cursor.execute(f"""Select Character_Name, Level, Effective_Wealth from Sessions_Participants where Player_Name = '{author}'""")
            character_info = cursor.fetchone()
            if character_info is None:
                await interaction.response.send_message(f"{author} has no active character in this session!")
            if character_info is not None:
                true_name = character_info[0]
                cursor.close()
                db.close()
                await Event.session_leave(self, guild_id, session_id, author, true_name)
                await interaction.response.send_message(f"{author}'s {true_name} has decided against participating in the session of '{session_info[0]}!'")
        elif character_info is not None:
            true_name = character_info[0]
            cursor.close()
            db.close()
            await Event.session_leave(self, guild_id, session_id, author, true_name)
            await interaction.response.send_message(f"{author}'s {true_name} has decided against participating in the session of '{session_info[0]}!'")


@player.command()
@app_commands.describe(group="Displaying All Participants & Signups, Active Participants Only, or Potential Sign-ups Only for a session")
@app_commands.choices(group=[discord.app_commands.Choice(name='All', value=1), discord.app_commands.Choice(name='Participants', value=2), discord.app_commands.Choice(name='Sign-ups', value=3)])
async def display(ctx: commands.Context, session_id: int, group: discord.app_commands.Choice[int] = 1):
    """ALL: THIS COMMAND DISPLAYS SESSION INFORMATION"""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if group == 1:
        group = 1
    else:
        group = group.value
    cursor.execute(f"SELECT GM_Name, Session_Name, Session_Range, Play_location, Play_Time, Overview, Description, Message, IsActive FROM Sessions WHERE Session_ID = {session_id}")
    session_info = cursor.fetchone()
    if session_info is not None:
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        sessions_channel = cursor.fetchone()
        session_channel = await bot.fetch_channel(sessions_channel[0])
        msg = await session_channel.fetch_message(session_info[7])
        embed = discord.Embed(title=f"{session_info[1]}", description=f'[Session overview](<{msg.jump_url}>)!',colour=discord.Colour.blurple())
        if session_info[8] == 1:
            embed.add_field(name=f"Active Session Info", value=f"**GM**: {session_info[0]}, **Session Range**: {session_info[2]}, **Play_Location**: {session_info[3]}, **Play_Time**: <t:{session_info[4]}:D>", inline=False)
            x = 0
            print(group)
            if group == 1 or group == 2:
                cursor.execute(f"SELECT COUNT(Player_Name) FROM Sessions_Participants WHERE Session_ID = {session_id}")
                total_participants = cursor.fetchone()
                cursor.execute(f"SELECT Player_Name, Character_Name, Level, Effective_Wealth, Tier, Player_ID FROM Sessions_Participants WHERE Session_ID = {session_id}")
                participants = cursor.fetchall()
                player_total = total_participants[0]
                embed.add_field(name=f"Participant List: {player_total} players", value=" ")
                for player in participants:
                    embed.add_field(name=f'**Character**: {player[1]}', value=f"**Player**: <@{player[5]}> \n **Level**: {player[2]}, **Tier** {player[4]} \n **Effective_Wealth**: {player[3]} GP", inline=False)
                    x += 1
                    if x >= 20:
                        embed.add_field(name=f"Field Limit reached", value=f'{total_participants[0] - 20} remaining Participants', inline=False)
                        break
            else:
                player_total = 0
            if group == 1 or group == 3:
                cursor.execute(f"SELECT COUNT(Player_Name) FROM Sessions_Signups WHERE Session_ID = {session_id}")
                total_participants = cursor.fetchone()
                x = 0 + player_total
                cursor.execute(f"SELECT Player_Name, Character_Name, Level, Effective_Wealth, Tier, Player_ID FROM Sessions_Signups WHERE Session_ID = {session_id}")
                participants = cursor.fetchall()
                player_total += total_participants[0]
                embed.add_field(name=f"Sign Up List: {total_participants[0]} players", value=' ', inline=False)
                for player in participants:
                    embed.add_field(name=f'**Character**: {player[1]}', value=f"Player: <@{player[5]}>, Level: {player[2]}, Tier: {player[4]}, Effective_Wealth: {player[3]}!", inline=False)
                    x += 1
                    if x >= 20:
                        embed.add_field(name=f"Field Limit reached", value=f'{total_participants[0] - 20} remaining Sign-ups')
                        break
                embed.set_footer(text=f"Session ID: {session_id}")
            await ctx.response.send_message(embed=embed)
        else:
            cursor.execute(f"SELECT Gold, Flux, Easy, Medium, Hard, Deadly, Trials FROM Sessions WHERE Session_ID = {session_id}")
            session_reward_info = cursor.fetchone()
            embed.add_field(name=f"Inactive Session Info", value=f"**GM**: {session_info[0]}, **Session Range**: {session_info[2]}, **Play_Location**: {session_info[3]}, **Play_Time**: <t:{session_info[4]}:D>", inline=False)
            embed.add_field(name=f"Milestone Rewards", value=f"**Easy Jobs**: {session_reward_info[2]}, **Medium Jobs**: {session_reward_info[3]}, **Hard_jobs**: {session_reward_info[4]}, **Deadly_Jobs**: {session_reward_info[5]}, **Trials**: {session_reward_info[6]}", inline=False)
            embed.add_field(name=f"Currency Rewards", value=f"**Gold**: {session_reward_info[0]}, **Flux**: {session_reward_info[1]}", inline=False)
            x = 0
            cursor.execute(f"SELECT COUNT(Player_Name) FROM Sessions_Archive WHERE Session_ID = {session_id}")
            total_participants = cursor.fetchone()
            cursor.execute(f"SELECT Player_Name, Character_Name, Level, Effective_Gold, Tier, Received_Milestones, Received_Gold, Player_ID FROM Sessions_Archive WHERE Session_ID = {session_id}")
            participants = cursor.fetchall()
            player_total = total_participants[0]
            embed.add_field(name=f"Participant List: {player_total} players", value=' ', inline=False)
            for player in participants:
                embed.add_field(name=f'**Character**: {player[1]}', value=f"**Player**: <@{player[7]}> \n **Level**: {player[2]}, **Tier** {player[4]}, \n **Received Milestones**: {player[5]}, **Received Trials**: {session_info[12]} \n  **Session Effective Gold**: {player[3]}, **Received Gold**: {player[6]}", inline=False)
                x += 1
                if x >= 20:
                    embed.add_field(name=f"Field Limit reached",
                                    value=f'{total_participants[0] - 20} remaining Participants')
                    break
            embed.set_footer(text=f"Session ID: {session_id}")
            await ctx.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title=f"Display Command Failed", description=f'{session_id} could not be found in current or archived sessions!', colour=discord.Colour.red())
        await ctx.response.send_message(embed=embed)
    cursor.close()
    db.close()
