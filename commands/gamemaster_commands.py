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







"""@gamemaster.command()
async def help(ctx: commands.Context):
    "Help commands for the associated tree"
    embed = discord.Embed(title=f"Gamemaster Help", description=f'This is a list of GM administrative commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Create**', value=f'**GAMEMASTER**: Create a session and post an announcement!', inline=False)
    embed.add_field(name=f'**Edit**', value=f'**GAMEMASTER**: Edit the session information!', inline=False)
    embed.add_field(name=f'**Accept**', value=f'**GAMEMASTER**: Accept a character into your session group!', inline=False)
    embed.add_field(name=f'**Remove**', value=f'**GAMEMASTER**: Remove a character from your session group!', inline=False)
    embed.add_field(name=f'**Display**', value=f'**GAMEMASTER**: Display the players on your quest!',inline=False)
    embed.add_field(name=f'**Reward**', value=f'**GAMEMASTER**: Send session rewards to involved characters!', inline=False)
    embed.add_field(name=f'**Endow**', value=f'**GAMEMASTER**: Endow individual players with rewards!', inline=False)
    embed.add_field(name=f'**Notify**', value=f'**GAMEMASTER**: Notify Players of a quest!', inline=False)
    embed.add_field(name=f'**Proposition**', value=f'**GAMEMASTER**: Accept or Reject A Proposition based on the ID!', inline=False)
    embed.add_field(name=f'**Glorify**', value=f'**GAMEMASTER**: Increase or decrease characters fame and prestige!', inline=False)
    await ctx.response.send_message(embed=embed)

@player.command()
async def help(ctx: commands.Context):
    "Help commands for the associated tree"
    embed = discord.Embed(title=f"Player Help", description=f'This is a list of Playerside commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Join**', value=f'**PLAYER**: join a session using one your characters!', inline=False)
    embed.add_field(name=f'**Leave**', value=f'**PLAYER**: Leave a session that you have joined!', inline=False)
    embed.add_field(name=f'**Display**', value=f'**ALL**: Display the details of a session.', inline=False)
    await ctx.response.send_message(embed=embed)


@gamemaster.command()
@app_commands.choices(acceptance=[discord.app_commands.Choice(name='accept', value=1), discord.app_commands.Choice(name='rejectance', value=2)])
async def proposition(ctx: commands.Context, proposition_id: int, reason: typing.Optional[str], acceptance: discord.app_commands.Choice[int] = 1):
    "Accept or reject a proposition!"
    guild_id = ctx.guild_id
    author = ctx.user.name
    guild = ctx.guild
    acceptance = 1 if acceptance == 1 else acceptance.value
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Character_Name from A_Audit_Prestige Where Proposition_ID = ?", (proposition_id, ))
    item_id = cursor.fetchone()
    reason = "N/A" if reason is None else reason
    if item_id is not None:
        if acceptance == 1:
            cursor.execute(f"Select Thread_ID from Player_Characters where Character_Name = ?", (item_id[0],))
            player_info = cursor.fetchone()
            logging_embed = discord.Embed(title=f"{author} has accepted the proposition!", description=f"Proposition ID: {proposition_id}", color=discord.Colour.red())
            embed.add_field(name=f'Reason:', value=f'{reason}', inline=False)
            logging_thread = guild.get_thread(player_info[0])
            await logging_thread.send(embed=logging_embed)
        else:
            cursor.execute(f"Select Thread_ID from Player_Characters where Character_Name = ?", (item_id[0],))
            player_info = cursor.fetchone()
            logging_embed = discord.Embed(title=f"{author} has rejected the proposition!", description=f"Proposition ID: {proposition_id}", color=discord.Colour.red())
            embed.add_field(name=f'Reason:', value=f'{reason}', inline=False)
            logging_thread = guild.get_thread(player_info[0])
            await logging_thread.send(embed=logging_embed)
            await Event.proposition_reject(self, guild_id, author, proposition_id, reason, source)
    cursor.close()
    db.close()


@gamemaster.command()
@app_commands.autocomplete(character=character_select_autocompletion)
async def glorify(ctx: commands.Context, character: str, fame: int, prestige: int, reason: typing.Optional[str]):
    "Add or remove from a player's fame and prestige!"
    guild_id = ctx.guild_id
    author = ctx.user.name
    guild = ctx.guild
    acceptance = 1 if acceptance == 1 else acceptance.value
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Character_Name from A_Audit_Prestige Where Proposition_ID = ?", (proposition_id, ))
    item_id = cursor.fetchone()
    reason = "N/A" if reason is None else reason
    cursor.execute(f"Select Thread_ID, Fame, Prestige from Player_Characters where Character_Name = ?", (item_id[0],))
    player_info = cursor.fetchone()
    if player_info is not None:
        logging_embed = discord.Embed(title=f"{author} has adjusted your fame or prestige!", description=f"**changed fame**: {fame} **changed prestige**: {prestige}", color=discord.Colour.red())
        embed.add_field(name=f'New Totals:', value=f'**fame**: {fame + player_info[1]}, **prestige**: {prestige + player_info[2]} ', inline=False)
        logging_thread = guild.get_thread(player_info[0])
        await logging_thread.send(embed=logging_embed)
        await Event.glorify(self, guild_id, author, character, fame + player_info[1], prestige + player_info[2], reason)
    else:
        await ctx.response.send_message(f"Character {character} does not exist!")
    cursor.close()
    db.close()



@gamemaster.command()
@app_commands.describe(hammer_time="Please use the plain code hammer time provides that appears like </>, ")
@app_commands.describe(overflow="Allow for adjust role ranges!")
@app_commands.choices(overflow=[discord.app_commands.Choice(name='current range only!', value=1), discord.app_commands.Choice(name='include next level bracket!', value=2), discord.app_commands.Choice(name='include lower level bracket!', value=3),discord.app_commands.Choice(name='ignore role requirements!', value=4)])
async def create(interaction: discord.Interaction, session_name: str, session_range: discord.Role, player_limit: int, play_location: str, game_link: typing.Optional[str], hammer_time: str, overview: str, description: str, overflow: discord.app_commands.Choice[int] = 1):
    "Create a new session."
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    overflow = 1 if overflow == 1 else overflow.value
    session_range_name = session_range.name
    session_range_id = session_range.id
    if game_link is not None:
        game_link_valid = str.lower(game_link[0:4])
        if game_link_valid == 'http':
            embed = discord.Embed(title=f"{session_name}", url=f'{game_link}', description=f"Play Location: {play_location}", color=discord.Colour.red())
        else:
            game_link = 'HTTPS://' + game_link
            embed = discord.Embed(title=f"{session_name}", url=f'{game_link}', description=f"Play Location: {play_location}", color=discord.Colour.red())
    else:
        embed = discord.Embed(title=f"{session_name}", description=f"Session Range: {session_range}", color=discord.Colour.red())

    hammer_timing = hammer_time[0:3]
    if hammer_timing == "<t:":
        timing = hammer_time[3:13]
        date = "<t:" + timing + ":D>"
        hour = "<t:" + timing + ":t>"
        arrival = "<t:" + timing + ":R>"
    else:
        timing = hammer_time
        date = "<t:" + timing + ":D>"
        hour = "<t:" + timing + ":t>"
        arrival = "<t:" + timing + ":R>"
    await Event.create_session(self, author, session_name, session_range_name, session_range_id, play_location, timing, game_link, guild_id, author, overview, description, player_limit, overflow)
    sql = f"SELECT Session_ID from Sessions WHERE Session_Name = ? AND GM_Name = ? ORDER BY Session_ID Desc Limit 1"
    val = (session_name, author)
    cursor.execute(sql, val)
    info = cursor.fetchone()
    print(overflow)
    if overflow == 1:
        footer_text = f'Session ID: {info[0]}.'
        session_ranges = f'<@&{session_range_id}>'
    elif overflow == 2:
        cursor.execute(f"SELECT min(level), max(level) FROM Level_Range WHERE Role_ID = ?", (session_range_id,))
        session_range_info = cursor.fetchone()
        footer_text = f'Session ID: {info[0]}.'
        if session_range_info is not None and session_range_info[1] + 1 < 20:
            cursor.execute(f"SELECT Role_ID FROM Level_Range WHERE level = ?", (session_range_info[1] + 1, ))
            overflow_range_id = cursor.fetchone()
            session_ranges = f'<@&{session_range_id}> AND <@&{overflow_range_id[0]}>'
        else:
            session_ranges = f'<@&{session_range_id}>'
    elif overflow == 3:
        footer_text = f'Session ID: {info[0]}.'
        cursor.execute(f"SELECT min(level), max(level) FROM Level_Range WHERE Role_ID = ?", (session_range_id,))
        session_range_info = cursor.fetchone()
        if session_range_info is not None and session_range_info[0] - 1 > 3:
            cursor.execute(f"SELECT Role_ID FROM Level_Range WHERE level = ?", (session_range_info[0] - 1,))
            overflow_range_id = cursor.fetchone()
            session_ranges = f'<@&{session_range_id}> AND <@&{overflow_range_id[0]}>'
        else:
            session_ranges = f'<@&{session_range_id}>'
    else:
        session_ranges = f'<@&{session_range_id}>'
        footer_text = f'Session ID: {info[0]}. Any level can join.'
    try:
        embed.set_author(name=f'{author}')
        embed.add_field(name="Session Range", value=session_ranges)
        embed.add_field(name="Player Limit", value=f'{player_limit}')
        embed.add_field(name="Date & Time:", value=f'{date} at {hour} which is {arrival}', inline=False)
        embed.add_field(name="Overview:", value=f'{overview}', inline=False)
        embed.add_field(name="Description:", value=f'{description}', inline=False)
        embed.set_footer(text=footer_text)
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        sessions_channel = cursor.fetchone()
        session_channel = await bot.fetch_channel(sessions_channel[0])
        session_text = f'<@{interaction.user.id}> is running a session.\r\n{session_ranges}'
        msg = await session_channel.send(content=session_text, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        message = msg.id
        thread = await msg.create_thread(name=f"{info[0]}: {session_name}", auto_archive_duration=60, reason=f"{description}")
        await Event.create_session_message(self, info[0], message, thread.id, guild_id)
        await interaction.response.send_message(f"Session created! Session ID: {info[0]}.", ephemeral=True)
        cursor.close()
        db.close()
    except discord.app_commands.errors.CommandInvokeError:
        embed = discord.Embed(title=f"{session_name}", description=f"Session Range: {session_range}", color=discord.Colour.red())
        embed.set_author(name=f'{author}')
        embed.add_field(name="Play Location", value=f'{play_location}')
        embed.add_field(name="Player Limit", value=f'{player_limit}')
        embed.add_field(name="Date & Time:", value=f'{date} at {hour} which is {arrival}', inline=False)
        embed.add_field(name="Overview:", value=f'{overview}', inline=False)
        embed.add_field(name="Description:", value=f'{description}', inline=False)
        embed.set_footer(text=footer_text)
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        sessions_channel = cursor.fetchone()
        session_channel = await bot.fetch_channel(sessions_channel[0])
        session_text = f'<@{interaction.user.id}> is running a session.\r\n{session_ranges}'
        msg = await session_channel.send(content=session_text, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        thread = await msg.create_thread(name=f"Session name: {session_name} Session ID: {info[0]}", auto_archive_duration=60, reason=f"{description}")
        message = msg.id
        await interaction.response.send_message(f"Session created! Session ID: {info[0]}.", ephemeral=True)
        await Event.create_session_message(self, {info[0]}, message, thread.id, guild_id)
        cursor.close()
        db.close()


@gamemaster.command()
@app_commands.describe(overflow="Allow for adjust role ranges!")
@app_commands.choices(overflow=[discord.app_commands.Choice(name='current range only!', value=1), discord.app_commands.Choice(name='include next level bracket!', value=2),discord.app_commands.Choice(name='include lower level bracket!', value=3),discord.app_commands.Choice(name='ignore role requirements!', value=4)])
async def edit(interaction: discord.Interaction, session_id: int, session_range: typing.Optional[discord.Role], session_name: typing.Optional[str], player_limit: typing.Optional[int], play_location: typing.Optional[str], game_link: typing.Optional[str], hammer_time: typing.Optional[str], overview: typing.Optional[str], description: typing.Optional[str], overflow: typing.Optional[discord.app_commands.Choice[int]]):
    "GM: Edit an Active Session."
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    sql = f"SELECT Message, Session_Name, Session_Range_ID, Play_Location, Play_Time, game_link, Overview, Description, Player_Limit, Session_Range, overflow from Sessions WHERE Session_ID = ? AND GM_Name = ? AND IsActive = ? ORDER BY Created_Time Desc Limit 1"
    val = (session_id, author, 1)
    cursor.execute(sql, val)
    info = cursor.fetchone()
    if info is not None:
        overflow = info[10] if overflow is None else overflow.value
        if session_range is not None:
            session_range = session_range
            session_range_name = session_range.name
            session_range_id = session_range.id
        else:
            session_range = info[2]
            session_range_id = info[2]
            session_range_name = info[9]
        if session_name is not None:
            session_name = session_name
        else:
            session_name = info[1]
        if player_limit is not None:
            player_limit = player_limit
        else:
            player_limit = info[8]
        if play_location is not None:
            play_location = play_location
        else:
            play_location = info[3]
        if game_link is not None:
            game_link_valid = game_link[0:4]
            if str.lower(game_link_valid) == 'http':
                embed = discord.Embed(title=f"{session_name}", url=f'{game_link}', description=f"Play Location: {play_location}", color=discord.Colour.blue())
            else:
                game_link = 'HTTPS://' + game_link
                embed = discord.Embed(title=f"{session_name}", url=f'{game_link}', description=f"Play Location: {play_location}", color=discord.Colour.blue())
        elif game_link is None and info[5] is not None:
            game_link = info[5]
            embed = discord.Embed(title=f"{session_name}", url=f'{game_link}', description=f"Play Location: {play_location}", color=discord.Colour.blue())
        else:
            embed = discord.Embed(title=f"{session_name}", description=f"Play Location: {play_location}", color=discord.Colour.blue())
        if hammer_time is not None:
            hammer_timing = hammer_time[0:3]
            if hammer_timing == "<t:":
                timing = hammer_time[3:13]
                date = "<t:" + timing + ":D>"
                hour = "<t:" + timing + ":t>"
                arrival = "<t:" + timing + ":R>"
            else:
                timing = hammer_time
                date = "<t:" + timing + ":D>"
                hour = "<t:" + timing + ":t>"
                arrival = "<t:" + timing + ":R>"
        else:
            timing = info[4]
            date = "<t:" + timing + ":D>"
            hour = "<t:" + timing + ":t>"
            arrival = "<t:" + timing + ":R>"
        if overview is not None:
            overview = overview
        else:
            overview = info[6]
        if description is not None:
            description = description
        else:
            description = info[7]
        print(overflow)
        print(session_id)
        if overflow == 1:
            footer_text = f'Session ID: {session_id}.'
            session_ranges = f'<@&{session_range_id}>'
        elif overflow == 2:
            footer_text = f'Session ID: {session_id}.'
            cursor.execute(f"SELECT min(level), max(level) FROM Level_Range WHERE Role_ID = ?", (session_range_id,))
            session_range_info = cursor.fetchone()
            if session_range_info is not None and session_range_info[1] + 1 < 20:
                cursor.execute(f"SELECT Role_ID FROM Level_Range WHERE level = ?", (session_range_info[1] + 1,))
                overflow_range_id = cursor.fetchone()
                session_ranges = f'<@&{session_range_id}> AND <@&{overflow_range_id[0]}>'
            else:
                session_ranges = f'<@&{session_range_id}>'
        elif overflow == 3:
            footer_text = f'Session ID: {session_id}.'
            cursor.execute(f"SELECT min(level), max(level) FROM Level_Range WHERE Role_ID = ?", (session_range_id,))
            session_range_info = cursor.fetchone()
            print(session_range_info)
            if session_range_info is not None and session_range_info[0] - 1 > 3:
                cursor.execute(f"SELECT Role_ID FROM Level_Range WHERE level = ?", (session_range_info[0] - 1,))
                overflow_range_id = cursor.fetchone()
                session_ranges = f'<@&{session_range_id}> AND <@&{overflow_range_id[0]}>'
            else:
                session_ranges = f'<@&{session_range_id}>'
        else:
            session_ranges = f'<@&{session_range_id}>'
            footer_text = f'Session ID: {session_id}. Any level can join.'
        print(footer_text)
        await Event.edit_session(self, guild_id, author, session_id, session_name, session_range_name, session_range_id, play_location, timing, game_link, overflow)
        embed.set_author(name=f'{author}')
        embed.add_field(name="Session Range", value=session_ranges)
        embed.add_field(name="Play Location", value=f'{play_location}')
        embed.add_field(name="Player Limit", value=f'{player_limit}')
        embed.add_field(name="Date & Time:", value=f'{date} at {hour} which is {arrival}', inline=False)
        embed.add_field(name="Overview:", value=f'{overview}', inline=False)
        embed.add_field(name="Description:", value=f'{description}', inline=False)
        embed.set_footer(text=footer_text)
        print(info)
        session_content = f'<@{interaction.user.id}> is running a session.\r\n{session_ranges}'
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        session_channel_info = cursor.fetchone()
        session_channel = await bot.fetch_channel(session_channel_info[0])
        msg = await session_channel.fetch_message(info[0])
        role = guild.get_role(session_range_id)
        await msg.edit(embed=embed, content=session_content)
        await interaction.response.send_message(content=f"The following session of {session_name} located at {msg.jump_url} has been updated.", allowed_mentions=discord.AllowedMentions(roles=True,))
    if info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id} associated with host {author}")
    cursor.close()
    db.close()


@gamemaster.command()
async def delete(interaction: discord.Interaction, session_id: int):
    "Delete an ACTIVE Session."
    guild_id = interaction.guild_id
    guild = interaction.guild
    author = interaction.user.name
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    sql = f"SELECT Message, Session_Thread, Session_Name from Sessions WHERE Session_ID = ? AND GM_Name = ? AND IsActive = ? ORDER BY Created_Time Desc Limit 1"
    val = (session_id, author, 1)
    cursor.execute(sql, val)
    info = cursor.fetchone()
    if info is not None:
        embed = discord.Embed(title=f"{info[1]}", description=f"This session has been cancelled.", color=discord.Colour.red())
        await Event.delete_session(self, session_id, guild_id, author)
        embed.set_author(name=f'{author}')
        embed.set_footer(text=f'Session ID: {session_id}.')
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        session_channel_info = cursor.fetchone()
        session_channel = await bot.fetch_channel(session_channel_info[0])
        msg = await session_channel.fetch_message(info[0])
        await msg.edit(embed=embed)
        await interaction.response.send_message(content=f"the following session of {info[2]} located at {msg.jump_url} has been cancelled.", ephemeral=True)
        thread = guild.get_thread(info[1])
        await thread.delete()
    if info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id} associated with host {author}")
    cursor.close()
    db.close()


# noinspection PyUnresolvedReferences
@gamemaster.command()
@app_commands.autocomplete(specific_character=character_select_autocompletion)
@app_commands.describe(randomizer="for the purposes of picking a number of randomized players")
@app_commands.describe(specific_character="Picking a specific player's character. You will have to use their CHARACTER Name for this.")
async def accept(interaction: discord.Interaction, session_id: int, player_1: typing.Optional[discord.Member], player_2: typing.Optional[discord.Member], player_3: typing.Optional[discord.Member], player_4: typing.Optional[discord.Member], player_5: typing.Optional[discord.Member], player_6: typing.Optional[discord.Member], specific_character: typing.Optional[str], randomizer: int = 0):
    "GM: Accept player Sign-ups into your session for participation"
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Session_Name, Play_location, Play_Time, game_link FROM Sessions WHERE Session_ID = '{session_id}' AND GM_Name = '{author}'")
    session_info = cursor.fetchone()
    accepted_characters = 0
    if session_info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id} associated with host {author}")
    elif randomizer < 0:
        await interaction.response.send_message(f"Cannot have a negative number of randomized players! {randomizer} is not acceptable!")
    else:
        cursor.execute(f"SELECT count(character_name) FROM Sessions_Participants WHERE Session_ID = {session_id}")
        accepted_players = cursor.fetchone()
        if accepted_players[0] < 20:
            accepted_characters += accepted_players[0]
            cursor.execute(f"SELECT count(character_name) FROM Sessions_Signups WHERE Session_ID = {session_id}")
            players = cursor.fetchone()
            print(players)
            print(accepted_characters)
            if players[0] > 0:
                timing = session_info[2]
                date = "<t:" + timing + ":D>"
                hour = "<t:" + timing + ":t>"
                arrival = "<t:" + timing + ":R>"
                mentions = f"the following players: "
                if session_info[3] is not None:
                    embed = discord.Embed(title=f"{session_info[0]}", url=f'{session_info[3]}', description=f"Date & Time: {date} at {hour} which is {arrival}", color=discord.Colour.green())
                else:
                    embed = discord.Embed(title=f"{session_info[0]}", description=f"Date & Time: {date} at {hour} which is {arrival}", color=discord.Colour.green())
                embed.set_author(name=f'{author}')
                if randomizer == 0 and player_1 is None and player_2 is None and player_3 is None and player_4 and player_5 is None and player_6 is None and specific_character is None:
                    await interaction.response.send_message(f"a session without players is like a drought with rain.")
                else:
                    if player_1 is not None:
                        player_name = player_1.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_1.id}> '
                        if player_info is None and signups_information is None:
                            embed.add_field(name=f'**Not Accepted!**:', value=f"<@{player_1.id}> had no characters signed up for this session!")
                        elif signups_information is not None:
                            embed.add_field(name=f'**No Duplicates!**:', value=f" <@{player_1.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_1.name, player_1.id, author, player_info[3])
                            embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with Player: <@{player_1.id}>!")
                    if player_2 is not None and player_2 != player_1:
                        player_name = player_2.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_2.id}> '
                        if player_info is None and signups_information is None:
                            embed.add_field(name=f'**Not Accepted!**:', value=f"<@{player_2.id}> had no characters signed up for this session!")
                        elif signups_information is not None:
                            embed.add_field(name=f'**No Duplicates!**:', value=f" <@{player_2.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_2.name, player_2.id, author, player_info[3])
                            embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with Player: <@{player_2.id}>!")
                    if player_3 is not None and player_3 != player_1 and player_3 != player_2:
                        player_name = player_3.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_3.id}> '
                        if player_info is None:
                            embed.add_field(name=f'**Not Accepted!**:', value=f"<@{player_3.id}> had no characters signed up for this session!")
                        elif signups_information is not None and signups_information is None:
                            embed.add_field(name=f'**No Duplicates!**:', value=f" <@{player_3.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_3.name, player_3.id, author, player_info[3])
                            embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with Player: <@{player_3.id}>!")
                    if player_4 is not None and player_4 != player_1 and player_4 != player_2 and player_4 != player_3:
                        player_name = player_4.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_4.id}> '
                        if player_info is None:
                            embed.add_field(name=f'**Not Accepted!**:',
                                            value=f" <@{player_4.id}> had no characters signed up for this session!")
                        elif signups_information is not None:
                            embed.add_field(name=f'**No Duplicates!**:',
                                            value=f" <@{player_4.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0],
                                                      player_info[1], player_info[2], player_4.name, player_4.id, author,
                                                      player_info[3])
                            embed.add_field(name=f'{player_info[0]}',
                                            value=f"has been accepted with Player: <@{player_4.id}>!")
                    if player_5 is not None and player_5 != player_1 and player_5 != player_2 and player_5 != player_3 and player_5 != player_4:
                        player_name = player_5.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_5.id}> '
                        if player_info is None:
                            embed.add_field(name=f'**Not Accepted!**:',
                                            value=f" <@{player_5.id}> had no characters signed up for this session!")
                        elif signups_information is not None:
                            embed.add_field(name=f'**No Duplicates!**:',
                                            value=f" <@{player_5.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0],
                                                      player_info[1], player_info[2], player_5.name, player_5.id, author,
                                                      player_info[3])
                            embed.add_field(name=f'{player_info[0]}',
                                            value=f"has been accepted with Player: <@{player_5.id}>!")
                    if player_6 is not None and player_6 != player_1 and player_6 != player_2 and player_6 != player_3 and player_6 != player_4 and player_6 != player_5:
                        player_name = player_6.name
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Signups WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        sql = f"Select Character_Name, Level, Effective_Wealth, Tier FROM Sessions_Participants WHERE Player_Name = ? AND Session_ID = ?"
                        val = (player_name, session_id)
                        cursor.execute(sql, val)
                        signups_information = cursor.fetchone()
                        mentions += f'<@{player_6.id}> '
                        if player_info is None:
                            embed.add_field(name=f'**Not Accepted!**:',
                                            value=f" <@{player_6.id}> had no characters signed up for this session!")
                        elif signups_information is not None:
                            embed.add_field(name=f'**No Duplicates!**:',
                                            value=f" <@{player_6.id}> already has {signups_information[0]} signed up!")
                        else:
                            accepted_characters += 1
                            await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0],
                                                      player_info[1], player_info[2], player_6.name, player_6.id, author,
                                                      player_info[3])
                            embed.add_field(name=f'{player_info[0]}',
                                            value=f"has been accepted with Player: <@{player_6.id}>!")
                    if specific_character is not None:
                        sql = f"Select Character_Name, Level, Gold_value, Player_Name, Player_ID, Tier FROM Player_Characters WHERE Character_Name = ?"
                        val = (specific_character,)
                        cursor.execute(sql, val)
                        player_info = cursor.fetchone()
                        if player_info is not None:
                            accepted_characters += 1
                            await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_info[3], player_info[4], author, player_info[5])
                            embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with player: @{player_info[4]}!")
                            mentions += f'<@{player_info[4]}> '
                    if randomizer > 0:
                        characters_total = players[0] - accepted_characters
                        randomizer = players[0] if randomizer > characters_total else randomizer
                        for x in range(randomizer):
                            random_number = random.randint(1, characters_total)
                            random_number -= 1
                            characters_total -= 1
                            accepted_characters += 1
                            cursor.execute(f"Select Character_Name, Level, Effective_Wealth, Player_Name, Player_ID, Tier FROM Sessions_Signups WHERE Session_ID = '{session_id}' LIMIT 1 OFFSET {random_number}")
                            player_info = cursor.fetchone()
                            print(x, player_info)
                            if accepted_characters <= 20:
                                await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_info[3], player_info[4], author, player_info[5])
                                embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with player: @{player_info[3]}!")
                                mentions += f'<@{player_info[4]}> '
                            else:
                                break
                    mentions += f"have been accepted!"
                    embed.set_footer(text=f"Session ID: {session_id}")
                    await interaction.response.send_message(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            else:
                print(session_info[3])
                if specific_character is not None:
                    sql = f"Select Character_Name, Level, Gold_value, Player_Name, Player_ID, Tier FROM Player_Characters WHERE Character_Name = ?"
                    val = (specific_character,)
                    cursor.execute(sql, val)
                    player_info = cursor.fetchone()
                    if player_info is not None:
                        timing = session_info[2]
                        date = "<t:" + timing + ":D>"
                        hour = "<t:" + timing + ":t>"
                        arrival = "<t:" + timing + ":R>"
                        mentions = f"the following players: "
                        if session_info[3] is not None:
                            embed = discord.Embed(title=f"{session_info[0]}", url=f'{session_info[3]}',
                                                  description=f"Date & Time: {date} at {hour} which is {arrival}",
                                                  color=discord.Colour.green())
                        else:
                            embed = discord.Embed(title=f"{session_info[0]}",
                                                  description=f"Date & Time: {date} at {hour} which is {arrival}",
                                                  color=discord.Colour.green())
                        embed.set_author(name=f'{author}')
                        accepted_characters += 1
                        await Event.accept_player(self, guild_id, session_info[0], session_id, player_info[0], player_info[1], player_info[2], player_info[3], player_info[4], author, player_info[5])
                        embed.add_field(name=f'{player_info[0]}', value=f"has been accepted with player: @{player_info[4]}!")
                        mentions += f'<@{player_info[4]}> '
                        embed.set_footer(text=f"Session ID: {session_id}")

                    else:
                        embed = discord.Embed(title=f"{session_info[0]} signups failed!", description=f"This character was not found.", color=discord.Colour.green())
                if session_info[3] is not None:
                    embed = discord.Embed(title=f"{session_info[0]} signups failed!", url=f'{session_info[3]}', description=f"there are no players signed up for this session", color=discord.Colour.green())
                else:
                    embed = discord.Embed(title=f"{session_info[0]} signups failed!", description=f"there are no players signed up for this session", color=discord.Colour.green())
                embed.set_author(name=f'{author}')
                print(embed)
                if mentions is not None:
                    await interaction.response.send_message(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
                else:
                    await interaction.response.send_message(embed=embed)
        else:
            if session_info[3] is not None:
                embed = discord.Embed(title=f"{session_info[0]} signups failed!", url=f'{session_info[3]}', description=f"20 IS THE HARD CAP. GO MAKE A SEPARATE SESSION FOR HANDLING REWARDS.", color=discord.Colour.green())
            else:
                embed = discord.Embed(title=f"{session_info[0]} signups failed!", description=f"20 IS THE HARD CAP. GO MAKE A SEPARATE SESSION FOR HANDLING REWARDS.", color=discord.Colour.green())
            embed.set_author(name=f'{author}')
            await interaction.response.send_message(embed=embed)
    cursor.close()
    db.close()


@gamemaster.command()
async def remove(interaction: discord.Interaction, session_id: int, player: discord.Member):
    "GM: Kick a player out of your session or remove them from rewards"
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    guild = interaction.guild
    cursor.execute(f"SELECT Session_Name, Play_location, Play_Time, game_link, IsActive, Gold, Flux, Alt_Reward_All FROM Sessions WHERE Session_ID = '{session_id}'")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id}")
    else:
        if session_info[4] == 1:
            cursor.execute(f"SELECT Player_Name, Character_Name FROM Sessions_Participants WHERE Session_ID = '{session_id}' and Player_Name = '{player.name}'")
            player_info = cursor.fetchone()
            if player_info is None:
                await interaction.response.send_message(f"{player.name} does not appear to be participating in the session of {session_info[0]} with session ID: {session_id}")
            else:
                player_name = player.name
                character_name = player_info[1]
                await Event.remove_player(self, guild_id, session_id, player_name, character_name, author)
                await interaction.response.send_message(f"{player.name} has been removed from Session {session_info[0]} with ID: {session_id}")
        else:
            cursor.execute(f"SELECT Player_Name, Character_Name, Level, Effective_Gold, Received_Milestones, Received_Trials, Received_Gold, Alt_Reward_Personal, Received_Fame FROM Sessions_Archive WHERE Session_ID = '{session_id}' and Player_Name = '{player.name}'")
            reward_info = cursor.fetchone()
            if reward_info is None:
                await interaction.response.send_message(
                    f"{player.name} does not appear to have participated in the session of {session_info[0]} with session ID: {session_id}")
            else:
                buttons = ["✅", "❌"]  # checkmark X symbol
                embed = discord.Embed(title=f"are you sure you want to revoke rewards from {reward_info[1]}?", description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
                await interaction.response.send_message(embed=embed)
                msg = await interaction.original_response()
                for button in buttons:
                    await msg.add_reaction(button)
                while True:
                    try:
                        reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == interaction.user.id and reaction.emoji in buttons, timeout=60.0)
                    except asyncio.TimeoutError:
                        embed.set_footer(text="Request has timed out.")
                        await msg.edit(embed=embed)
                        await msg.clear_reactions()
                        return print("timed out")
                    else:
                        if reaction.emoji == u"\u264C":
                            embed = discord.Embed(title=f"You have thought better of revoking rewards from {reward_info[1]}", description=f"Savings!", colour=discord.Colour.blurple())
                            await msg.edit(embed=embed)
                            await msg.clear_reactions()
                        if reaction.emoji == u"\u2705":
                            embed = discord.Embed(title=f"Reward Change has occurred!", description=f"Rewards Revoked from {reward_info[1]}.", colour=discord.Colour.red())
                            await msg.clear_reactions()
                            await msg.edit(embed=embed)
                            character_name = reward_info[1]
                            cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name, character_name))
                            player_info = cursor.fetchone()
                            cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                            transaction_id = cursor.fetchone()
                            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                            accepted_bio_channel = cursor.fetchone()
                            milestone_total = player_info[9] - reward_info[4]
                            level_information = level_calculation(guild_id, player_info[9], -abs(reward_info[4]), player_info[29])
                            mythic_information = mythic_calculation(guild_id, player_info[7], player_info[11], -abs(reward_info[5]))
                            await Event.session_rewards(self, author, guild_id, player_info[2], level_information[0], milestone_total, level_information[1], player_info[16] - session_info[6], mythic_information[0], player_info[11] - reward_info[5], mythic_information[1], player_info[28] - reward_info[8], session_id)
                            await Event.gold_change(self, guild_id, player_info[0], player_info[1], player_info[2], reward_info[6] * -1, reward_info[6] * -1, session_info[5] * -1, 'Session removing session_reward', 'removing session_reward')
                            bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], level_information[0], mythic_information[0], player_info[9] + -abs(reward_info[4]), level_information[1], player_info[11] + -abs(reward_info[5]), mythic_information[1], player_info[13] - reward_info[6], player_info[14] - reward_info[6], player_info[16] - session_info[6], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                            bio_message = await bio_channel.fetch_message(player_info[24])
                            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                            source = f"Session Reward removed with Session ID: {session_id}"
                            reward_all = None if session_info[7] is None else f"Removed the following: {session_info[7]}"
                            logging_embed = log_embed(player_info[2], author, level_information[0], -abs(reward_info[4]), player_info[9] + -abs(reward_info[4]), level_information[1], mythic_information[0], reward_info[5], player_info[11] + -abs(reward_info[5]), mythic_information[1], player_info[13] - reward_info[6], reward_info[5], player_info[14] - reward_info[6], transaction_id[0], player_info[16] - session_info[6], -abs(session_info[6]), None, None, None, None, reward_all, None, None, None, None, source)
                            logging_thread = guild.get_thread(player_info[25])
                            await logging_thread.send(embed=logging_embed)
                            cursor.close()
                            db.close()
                            await Event.remove_player(self, guild_id, session_id, reward_info[0], reward_info[1], author)
    cursor.close()
    db.close()


@gamemaster.command()
@app_commands.describe(reward_all="A reward for each individual member of the party")
@app_commands.describe(party_reward="A reward for the party to divy up amongst themselves, or not. Link a google doc if reward exceeds character limit.")
async def reward(interaction: discord.Interaction, session_id: int, gold: float, easy: int = 0, medium: int = 0, hard: int = 0, deadly: int = 0, trials: int = 0, reward_all: str = None, fame: int = 2, prestige: int = 2, party_reward: str = None):
    "GM: Reward Players for Participating in your session."
    awarded_flux = 10
    if gold < 0 or easy < 0 or medium < 0 or hard < 0 or deadly < 0 or flux < 0 or trials < 0:
        await interaction.response.send_message(f"Your players might not judge you out loud for trying to give them a negative award, but I do...")
    elif gold == 0 and easy == 0 and medium == 0 and hard == 0 and deadly == 0 and flux == 0 and trials == 0 and reward_all is None and party_reward is None:
        await interaction.response.send_message(f"Your players have been rewarded wi-- wait a minute, what the fuck? No Rewards?! No! At least give them a silver or a milestone!")
    guild_id = interaction.guild_id
    guild = interaction.guild

    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT GM_Name, Session_Name, Session_Range, Play_Location, Play_Time, Message, Session_Thread, IsActive FROM Sessions WHERE Session_ID = {session_id} LIMIT 1")
    session_info = cursor.fetchone()
    if session_info is not None:
        if session_info[7] == 1:
            mentions = f"Session Rewards for {session_info[1]}: "
            cursor.execute(f"SELECT Player_Name, Player_ID, Character_Name, Level, Tier, Effective_Wealth  FROM Sessions_Participants WHERE Session_ID = {session_id}")
            session_players = cursor.fetchall()
            if session_players == []:
                await interaction.response.send_message(f"No players could be found participating in session with {session_id} can be found!")
            elif session_players is not None:
                await interaction.response.defer(thinking=True, ephemeral=True)
                embed = discord.Embed(title=f"{session_info[1]}", description=f"Reward Display", color=discord.Colour.green())
                embed.set_footer(text=f"Session ID is {session_id}")
                for player in session_players:
                    mentions += f"<@{player[1]}> "
                    character_name = player[2]
    #                Setting Job Rewards
                    cursor.execute(f"SELECT Easy, Medium, Hard, Deadly from AA_Milestones WHERE level = {player[3]}")
                    job_info = cursor.fetchone()
                    easy_jobs = easy * job_info[0]
                    medium_jobs = medium * job_info[1]
                    hard_jobs = hard * job_info[2]
                    deadly_jobs = deadly * job_info[3]
                    rewarded = easy_jobs + medium_jobs + hard_jobs + deadly_jobs
    #                Done Setting Job Rewards
    #                Obtaining Character Information
                    print(f"CHARACTER NAME IS {character_name}")
                    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link, Accepted_Date FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name, character_name))
                    player_info = cursor.fetchone()
                    # The specific date you want to compare
                    end_date = datetime.datetime.strptime(player_info[32], '%Y-%m-%d %H:%M')
                    # Current date and time
                    current_date = datetime.datetime.now()
                    # Calculate the difference between dates
                    difference = current_date - end_date
                    # Get the difference in days
                    if player_info[7] >= 7:
                        if 90 <= difference.days < 120:
                            flux_multiplier = 2
                        elif difference.days >= 120:
                            flux_multiplier = 2 + math.floor((difference.days-90) / 30)
                            flux_multiplier = flux_multiplier if flux_multiplier <= 4 else 4
                        else:
                            flux_multiplier = 1
                    else:
                        flux_multiplier = 1
                    awarded_flux = 10 * flux_multiplier
                    print(f"Player flux info is {player_info[16]}")
                    flux_total = player_info[16] + flux  #Setting the Flux
                    level_info = level_calculation(guild_id, player_info[9], rewarded, player_info[29])
                    gold_info = gold_calculation(level_info[0], player_info[6], player_info[13], player_info[14], player_info[15], gold)
                    mythic_info = mythic_calculation(guild_id, level_info[0], player_info[11], trials)
                    # Building Player Reward
                    response = f"Player: <@{player[1]}>'s character has received:"
                    if gold != 0:
                        response += f" {gold_info[3]} gold with a new total of {gold_info[0]} GP!"
                    else:
                        response = response
                    if rewarded != 0:
                        response += f" {rewarded} milestones!"
                    else:
                        response = response
                    if player[3] != level_info[0]:
                        response += f" and has leveled up to {level_info[0]}!"
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {player[3]}")
                        level_range = cursor.fetchone()
                        cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Desc")
                        level_range_max = cursor.fetchone()
                        cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Asc")
                        level_range_min = cursor.fetchone()
                        sql = f"Select True_Character_Name from Player_Characters WHERE Player_Name = ? AND level >= ? AND level <= ?"
                        val = (player[0], level_range_min[0], level_range_max[0])
                        cursor.execute(sql, val)
                        level_range_characters = cursor.fetchone()
                        # user = await bot.fetch_user(player[1])
                        member = await guild.fetch_member(player[1])
                        if level_range_characters is None:
                            cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {level_info[0]}")
                            new_level_range = cursor.fetchone()
                            role1 = guild.get_role(level_range[2])
                            role2 = guild.get_role(new_level_range[2])
                            await member.remove_roles(role1)
                            await member.add_roles(role2)
                        else:
                            cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {level_info[0]}")
                            new_level_range = cursor.fetchone()
                            role2 = guild.get_role(new_level_range[2])
                            await member.add_roles(role2)
                    prestige = prestige if player_info[30] + prestige <= player_info[27] + fame else player_info[27] + fame - player_info[30]
                    if trials != 0:
                        response += f" {trials} Mythic Trials!"
                    if player[4] != mythic_info[0]:
                        response += f" and has reached a new mythic tier of {mythic_info[0]}!"
                    if fame != 0:
                        response += f" also receiving {fame} fame for a total of {player_info[27] + fame}!"
                    if prestige != 0:
                        response += f" and {prestige} prestige for a total of {player_info[30] + prestige}!"
                    if flux != 0:
                        response += f" and {flux} flux for a total of {flux_total}!"
                    embed.add_field(name=f'**Character**: {player[2]}', value=response)
                    await Event.session_rewards(self, author, guild_id, player[2], level_info[0], player_info[9] + rewarded, level_info[1], flux_total, mythic_info[0], player_info[11] + trials, mythic_info[1], player_info[27] + fame, player_info[30] + prestige, f"Session {session_id} reward")
                    await Event.gold_change(self, guild_id, player[0], player[1], player[2], gold_info[3], gold_info[3], gold, 'Session Reward', 'Session Reward')
                    await Event.session_log_player(self, guild_id, session_id, player_info[0], player_info[1], player_info[2], player[3], player[4], player[5], rewarded, trials, gold_info[3], fame, prestige, flux)
                    cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                    transaction_id = cursor.fetchone()
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    accepted_bio_channel = cursor.fetchone()

                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], level_info[0], mythic_info[0], player_info[9] + rewarded, level_info[1], player_info[11] + trials, mythic_info[1], player_info[13] + gold_info[3], player_info[14] + gold_info[3], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27] + fame, player_info[28], player_info[30]+prestige, player_info[31])
                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                    bio_message = await bio_channel.fetch_message(player_info[24])
                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                    source = f"Session Reward with Session ID: {session_id} and transaction ID: {transaction_id[0]}"
                    logging_embed = log_embed(player_info[2], author, level_info[0], rewarded, player_info[9] + rewarded, level_info[1], mythic_info[0], trials, player_info[11] + trials, mythic_info[1], player_info[13] + gold_info[3], gold_info[3], player_info[14] + gold_info[3], transaction_id[0], flux_total, flux, None, None, None, None, reward_all, player_info[27] + fame, fame, player_info[30] + prestige, prestige, source)
                    logging_thread = guild.get_thread(player_info[25])
                    print(f"logging thread is {logging_thread} \r\nplayer thread is {player_info[25]}")
                    try:
                        print(f"attempt 1 sending to logging thread ")
                        await logging_thread.send(embed=logging_embed)
                    except AttributeError as e:
                        try:
                            print(f"attempt 2 sending to logging thread")
                            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                            eventlog_channel = cursor.fetchone()
                            event_channel = bot.get_channel(eventlog_channel[0])
                            print(f"this is the event Channel {event_channel}")
                            logging_thread = event_channel.get_thread(player_info[25])
                            print(f"this is the {logging_thread} pulled hopefully from server not memory")
                            if logging_thread is not None:
                                logging_thread.archived = False;
                            await logging_thread.send(embed=logging_embed)
                        except AttributeError as e:
                            print(f"passing")
                            mentions += f"Note! Thread is archived!"
                            pass

                await interaction.followup.send(content=f"You have successfully run this command!", ephemeral=True)
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Quest_Rewards_Channel'")
                rewards_channel = cursor.fetchone()
                reward_channel = await bot.fetch_channel(rewards_channel[0])
                reward_msg = await reward_channel.send(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
                if party_reward is not None:
                    reward_thread = await reward_msg.create_thread(name=f"Session name: {session_info[1]} Party Rewards, Session ID: {session_id}", auto_archive_duration=60, reason=f"{party_reward}")
                    reward_thread_id = reward_thread.id
                    party_reward_embed = discord.Embed(title=f"{session_info[1]}", description=f"Party Reward Display", color=discord.Colour.green())
                    party_reward_embed.set_footer(text=f"Session ID is {session_id}")
                    party_reward_embed.add_field(name=f'**Party Reward**: ', value=f"{party_reward}")
                    await reward_thread.send(embed=party_reward_embed)
                else:
                    reward_thread_id = None
                await Event.session_log(self, guild_id, session_id, gold, flux, easy, medium, hard, deadly, trials, reward_all, party_reward, reward_msg.id, reward_thread_id, fame, prestige)
                cursor.close()
                db.close()
        else:
            await interaction.response.send_message(f"Session found with {session_id} but it is archived! Please submit a request to your admin to address!")
    if session_info is None:
        await interaction.response.send_message(f"No active session with {session_id} can be found!")

@gamemaster.command()
async def endow(interaction: discord.Interaction, session_id: int, player_1: typing.Optional[discord.Member], player_1_reward: typing.Optional[str], player_2: typing.Optional[discord.Member], player_2_reward: typing.Optional[str], player_3: typing.Optional[discord.Member], player_3_reward: typing.Optional[str], player_4: typing.Optional[discord.Member], player_4_reward: typing.Optional[str], player_5: typing.Optional[discord.Member], player_5_reward: typing.Optional[str], player_6: typing.Optional[discord.Member], player_6_reward: typing.Optional[str]):
    "GM: Reward Players for Participating in your session."
    guild_id = interaction.guild_id
    guild = interaction.guild
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT GM_Name, Session_Name, Session_Range, Play_Location, Play_Time, Message FROM Sessions WHERE Session_ID = {session_id} LIMIT 1")
    session_info = cursor.fetchone()
    await interaction.response.defer(thinking=True)
    if session_info is not None:
        embed = discord.Embed(title=f"{session_info[1]}", description=f"Personal Reward Display", color=discord.Colour.green())
        embed.set_footer(text=f"Session ID is {session_id}")
        if player_1 is not None and player_1_reward is not None:
            cursor.execute(f"SELECT Character_Name FROM Sessions_Archive WHERE Player_Name = '{player_1.name}' AND Session_ID = {session_id}")
            session_player_info = cursor.fetchone()
            response = f"<@{player_1.id}> "
            if session_player_info is not None:
                cursor.execute(f"SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?", (session_player_info[0],))
                character_info = cursor.fetchone()
                await Event.session_endowment(self, author, guild_id, session_id, player_1.name, player_1_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_1_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_1_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_1.name}', value=response, inline=False)
        if player_2 is not None and player_2_reward is not None:
            cursor.execute(f"SELECT Character_Name FROM Sessions_Archive WHERE Player_Name = '{player_2.name}' AND Session_ID = {session_id}")
            session_player_info = cursor.fetchone()
            response = f"<@{player_2.id}> "
            if session_player_info is not None:
                cursor.execute(f"SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?",(session_player_info[0],))
                character_info = cursor.fetchone()
                await Event.session_endowment(self, author, guild_id, session_id, player_2.name, player_2_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_2_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_2_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_2.name}', value=response, inline=False)
        if player_3 is not None and player_3_reward is not None:
            cursor.execute(f"SELECT Character_Name FROM Sessions_Archive WHERE Player_Name = '{player_3.name}' AND Session_ID = {session_id}")
            session_player_info = cursor.fetchone()
            response = f"<@{player_3.id}> "
            if session_player_info is not None:
                cursor.execute(f"SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?",(session_player_info[0],))
                character_info = cursor.fetchone()
                await Event.session_endowment(self, author, guild_id, session_id, player_3.name, player_3_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_3_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_3_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_3.name}', value=response, inline=False)
        if player_4 is not None and player_4_reward is not None:
            cursor.execute(f"SELECT Character_Name FROM Sessions_Archive WHERE Player_Name = '{player_4.name}' AND Session_ID = {session_id}")
            session_player_info = cursor.fetchone()
            response = f"<@{player_4.id}> "
            if session_player_info is not None:
                cursor.execute(f"SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?",(session_player_info[0],))
                character_info = cursor.fetchone()
                await Event.session_endowment(self, author, guild_id, session_id, player_4.name, player_4_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_4_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_4_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_4.name}', value=response, inline=False)
        if player_5 is not None and player_5_reward is not None:
            cursor.execute(f"SELECT Character_Name FROM Sessions_Archive WHERE Player_Name = '{player_5.name}' AND Session_ID = {session_id}")
            session_player_info = cursor.fetchone()
            response = f"<@{player_5.id}> "
            if session_player_info is not None:
                cursor.execute(f"SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?", (session_player_info[0],))
                character_info = cursor.fetchone()
                await Event.session_endowment(self, author, guild_id, session_id, player_5.name, player_5_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_5_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_5_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_5.name}', value=response, inline=False)
        if player_6 is not None and player_6_reward is not None:
            cursor.execute(f"SELECT Character_Name, Thread_ID FROM Sessions_Archive WHERE Player_Name = '{player_6.name}' AND Session_ID = {session_id}")
            session_player_info = cursor.fetchone()
            response = f"<@{player_6.id}> "
            if session_player_info is not None:
                cursor.execute(f"SELECT Character_Name, Thread_ID FROM Player_Characters WHERE Character_Name = ?", (session_player_info[0],))
                character_info = cursor.fetchone()
                await Event.session_endowment(self, author, guild_id, session_id, player_6.name, player_6_reward, character_info[0])
                source = f"Personal reward for Session ID: {session_id}"
                logging_embed = log_embed(session_player_info[0], author, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, player_6_reward, None, None, None, None, source)
                logging_thread = guild.get_thread(character_info[1])
                await logging_thread.send(embed=logging_embed)
                response += f"has been rewarded with {player_6_reward}!"
            else:
                response += f"has not participated in this session or could not be found!"
            embed.add_field(name=f'**Player**: {player_6.name}', value=response, inline=False)
        await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=False))
    cursor.close()
    db.close()
    if session_info is None:
        await interaction.followup.send(f"No active session with {session_id} can be found!")



@gamemaster.command()
@app_commands.describe(forego="Accept only part of a session reward!")
@app_commands.choices(forego=[discord.app_commands.Choice(name='all!', value=1), discord.app_commands.Choice(name='Forego Milestones!', value=2), discord.app_commands.Choice(name='Foregold!', value=3)])
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def claim(interaction: discord.Interaction, session_id: int, character_name: str, forego: discord.app_commands.Choice[int] = 1):
    guild_id = interaction.guild_id
    guild = interaction.guild
    author = interaction.user.name
    author_id = interaction.user.id
    user = interaction.user
    if forego == 1:
        forego = 1
    else:
        forego = forego.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    print(interaction.user.name)
    print(interaction.channel.id)
    cursor.execute(f"SELECT IsActive, GM_Name, Session_Name, Gold, Flux, Easy, Medium, Hard, Deadly, Trials, Fame, Prestige FROM Sessions WHERE Session_ID = '{session_id}' limit 1")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.response.send_message(f"No session with {session_id} can be found!")
    elif session_info[0] == 1:
        await interaction.response.send_message(f"The Session of {session_info[2]} is still active! !")
    else:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link, Accepted_Date FROM Player_Characters WHERE Player_Name = ? AND Character_Name = ? OR Nickname =?", (author, character_name, character_name))
        validate_recipient = cursor.fetchone()
        if validate_recipient is not None:
            cursor.execute(f"SELECT Player_Name, Character_Name, Received_Milestones, Received_Trials, Received_Gold, Forego  FROM Sessions_Archive WHERE Session_ID = ? AND Player_Name = ?", (session_id, author))
            previous_rewards = cursor.fetchone()
            if previous_rewards is not None:
                print(previous_rewards[1])
                print(character_name)
                if previous_rewards[1] == character_name:
                    await interaction.response.send_message(f"you cannot claim for the same character of {character_name} when you already have claimed for them!!")
                else:
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    accepted_bio_channel = cursor.fetchone()
                    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters WHERE Character_Name = ?", (previous_rewards[1],))
                    previous_recipient = cursor.fetchone()
                    buttons = ["✅", "❌"]  # checkmark X symbol
                    embed = discord.Embed(title=f"are you sure you want to revoke rewards from {previous_recipient[2]} and claim them for {validate_recipient[2]}?", description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
                    await interaction.response.send_message(embed=embed)
                    msg = await interaction.original_response()
                    for button in buttons:
                        await msg.add_reaction(button)
                    while True:
                        try:
                            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == interaction.user.id and reaction.emoji in buttons, timeout=60.0)
                        except asyncio.TimeoutError:
                            embed.set_footer(text="Request has timed out.")
                            await msg.edit(embed=embed)
                            await msg.clear_reactions()
                            return print("timed out")
                        else:
                            if reaction.emoji == u"\u264C":
                                embed = discord.Embed(title=f"You have thought better of swapping the rewards", description=f"Savings!", colour=discord.Colour.blurple())
                                await msg.edit(embed=embed)
                                await msg.clear_reactions()
                            if reaction.emoji == u"\u2705":
                                embed = discord.Embed(title=f"Reward Change has occurred!", description=f"Rewards Revoked from {previous_recipient[2]} and claimed for {validate_recipient[2]}.",colour=discord.Colour.red())
                                await msg.clear_reactions()
                                await msg.edit(embed=embed)
                                character_name = reward_info[1]
                                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name, character_name))
                                player_info = cursor.fetchone()
                                cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                                transaction_id = cursor.fetchone()
                                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                accepted_bio_channel = cursor.fetchone()
                                milestone_total = player_info[9] - reward_info[4]
                                level_information = level_calculation(guild_id, player_info[9], -abs(reward_info[4]), player_info[29])
                                mythic_information = mythic_calculation(guild_id, player_info[7], player_info[11], -abs(reward_info[5]))
                                await Event.session_rewards(self, author, guild_id, player_info[2], level_information[0], milestone_total, level_information[1], player_info[16] - session_info[6], mythic_information[0], player_info[11] - reward_info[5], mythic_information[1], player_info[28] - reward_info[8], session_id)
                                await Event.gold_change(self, guild_id, player_info[0], player_info[1], player_info[2],reward_info[6] * -1, reward_info[6] * -1, session_info[5] * -1, 'Session removing session_reward', 'removing session_reward')
                                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], level_information[0], mythic_information[0], player_info[9] + -abs(reward_info[4]), level_information[1], player_info[11] + -abs(reward_info[5]), mythic_information[1], player_info[13] - reward_info[6], player_info[14] - reward_info[6], player_info[16] - session_info[6], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                bio_message = await bio_channel.fetch_message(player_info[24])
                                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                source = f"Session Reward removed with Session ID: {session_id}"
                                reward_all = None if session_info[7] is None else f"Removed the following: {session_info[7]}"
                                logging_embed = log_embed(player_info[2], author, level_information[0], -abs(reward_info[4]), player_info[9] + -abs(reward_info[4]), level_information[1], mythic_information[0], reward_info[5], player_info[11] + -abs(reward_info[5]), mythic_information[1], player_info[13] - reward_info[6], reward_info[5], player_info[14] - reward_info[6], transaction_id[0], player_info[16] - session_info[6], -abs(session_info[6]), None, None, None, None, reward_all, None, None, None, None, source)
                                logging_thread = guild.get_thread(player_info[25])
                                await logging_thread.send(embed=logging_embed)
                                cursor.close()
                                db.close()
                                await Event.remove_player(self, guild_id, session_id, reward_info[0], reward_info[1], author)
                                db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
                                cursor = db.cursor()
                                cursor.execute(f"SELECT Easy, Medium, Hard, Deadly from AA_Milestones WHERE level = {validate_recipient[6]}")
                                job_info = cursor.fetchone()
                                easy_jobs = session_info[5] * job_info[0]
                                medium_jobs = session_info[6] * job_info[1]
                                hard_jobs = session_info[7] * job_info[2]
                                deadly_jobs = session_info[8] * job_info[3]
                                rewarded = easy_jobs + medium_jobs + hard_jobs + deadly_jobs
                                rewarded = 0 if forego == 2 else rewarded
                                new_milestones = validate_recipient[8] + rewarded
                                level_information = level_calculation(guild_id, validate_recipient[8], rewarded, player_info[29])
                                print(level_information[0], validate_recipient[10], session_info[9], player_info[29])
                                mythic_information = mythic_calculation(guild_id, level_information[0], validate_recipient[10], session_info[9])
                                print(mythic_information)
                                gold_information = gold_calculation(level_information[0], validate_recipient[5], validate_recipient[12], validate_recipient[13], validate_recipient[14], session_info[3])
                                gold_received = 0 if forego == 3 else gold_information[3]
                                gold_rewarded = 0 if forego == 3 else session_info[3]
                                await Event.session_rewards(self, validate_recipient[0], guild_id, character_name, level_information[0], new_milestones, level_information[1], validate_recipient[15] + session_info[4], mythic_information[0], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[26] + session_info[10],  session_id)
                                await Event.gold_change(self, guild_id, validate_recipient[0], validate_recipient[1], character_name, gold_received, gold_received, gold_rewarded, 'Session Added new Claim', 'Session Claim')
                                cursor.execute(f"Select MAX(transaction_id) from A_Audit_Gold")
                                gold_transaction_id = cursor.fetchone()
                                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                accepted_bio_channel = cursor.fetchone()
                                cursor.close()
                                db.close()
                                await Event.session_log_player(self, guild_id, session_id, validate_recipient[0], validate_recipient[1], validate_recipient[2], validate_recipient[6], validate_recipient[7], validate_recipient[13], rewarded, session_info[9], gold_received, session_info[10])
                                bio_embed = character_embed(validate_recipient[0], validate_recipient[1], validate_recipient[2], validate_recipient[3], validate_recipient[4], validate_recipient[5], level_information[0], mythic_information[0], new_milestones, level_information[1], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[12] + gold_received, validate_recipient[13] + gold_received, validate_recipient[15] + session_info[4], validate_recipient[16], validate_recipient[17], validate_recipient[18], validate_recipient[19], validate_recipient[20], validate_recipient[21], validate_recipient[22], validate_recipient[26] + session_info[10], validate_recipient[27], )
                                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                bio_message = await bio_channel.fetch_message(validate_recipient[23])
                                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                session_name = session_info[2]
                                embed_log = log_embed(validate_recipient[2], author, level_information[0], rewarded, new_milestones, level_information[1], mythic_information[0], session_info[9], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[12] + gold_received, gold_received, validate_recipient[13] + gold_received, gold_transaction_id[0], validate_recipient[15] + session_info[4], session_info[4], None, None, None, None, None, validate_recipient[26] + session_info[10], session_info[10], None, None, f"Session {session_name} with ID: {session_id} claimed")
                                logging_thread = guild.get_thread(validate_recipient[25])
                                await logging_thread.send(embed=embed_log)
                                await interaction.response.send_message(f"Rewards have been claimed for {character_name}!")
            else:
                cursor.execute(f"SELECT Easy, Medium, Hard, Deadly from AA_Milestones WHERE level = {validate_recipient[6]}")
                job_info = cursor.fetchone()
                easy_jobs = session_info[5] * job_info[0]
                medium_jobs = session_info[6] * job_info[1]
                hard_jobs = session_info[7] * job_info[2]
                deadly_jobs = session_info[8] * job_info[3]
                rewarded = easy_jobs + medium_jobs + hard_jobs + deadly_jobs
                rewarded = 0 if forego == 2 else rewarded
                new_milestones = validate_recipient[8] + rewarded
                level_information = level_calculation(guild_id, validate_recipient[8], rewarded, validate_recipient[28])
                print(level_information[0], validate_recipient[10], session_info[9], validate_recipient[28])
                mythic_information = mythic_calculation(guild_id, level_information[0], validate_recipient[10], session_info[9])
                print(mythic_information)
                gold_information = gold_calculation(level_information[0], validate_recipient[5], validate_recipient[12], validate_recipient[13], validate_recipient[14], session_info[3])
                gold_received = 0 if forego == 3 else gold_information[3]
                gold_rewarded = 0 if forego == 3 else session_info[3]
                prestige = session_info[11]
                prestige = prestige if validate_recipient[29] + prestige <= validate_recipient[26] + session_info[10] else validate_recipient[26] + session_info[10] - validate_recipient[29]
                # The specific date you want to compare
                end_date = datetime.datetime.strptime(validate_recipient[31], '%Y-%m-%d %H:%M')
                # Current date and time
                current_date = datetime.datetime.now()
                # Calculate the difference between dates
                difference =  current_date - end_date
                # Get the difference in days
                if validate_player[6] >= 7:
                    if 90 <= difference.days < 120:
                        flux_multiplier = 2
                    elif difference.days >= 120:
                        flux_multiplier = 2 + math.floor((difference.days - 90) / 30)
                        flux_multiplier = flux_multiplier if flux_multiplier <= 4 else 4
                    else:
                        flux_multiplier = 1
                else:
                    flux_multiplier = 1
                awarded_flux = session_info[4] * flux_multiplier
                await Event.session_rewards(self, validate_recipient[0], guild_id, character_name, level_information[0], new_milestones, level_information[1], validate_recipient[15] + awarded_flux, mythic_information[0], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[26] + session_info[10], validate_recipient[29] +prestige, session_id)
                await Event.gold_change(self, guild_id, validate_recipient[0], validate_recipient[1], character_name, gold_received, gold_received, gold_rewarded, 'Session Added new Claim', 'Session Claim')
                cursor.execute(f"Select MAX(transaction_id) from A_Audit_Gold")
                gold_transaction_id = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.close()
                db.close()
                await Event.session_log_player(self, guild_id, session_id, validate_recipient[0], validate_recipient[1], validate_recipient[2], validate_recipient[6], validate_recipient[7], validate_recipient[13], rewarded, session_info[9], gold_received, session_info[10], prestige, awarded_flux)
                bio_embed = character_embed(validate_recipient[0], validate_recipient[1], validate_recipient[2], validate_recipient[3], validate_recipient[4], validate_recipient[5], level_information[0], mythic_information[0], new_milestones, level_information[1], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[12]+gold_received, validate_recipient[13]+gold_received, validate_recipient[15] + awarded_flux, validate_recipient[16], validate_recipient[17], validate_recipient[18], validate_recipient[19], validate_recipient[20], validate_recipient[21], validate_recipient[22], validate_recipient[26] + session_info[10], validate_recipient[27], validate_recipient[29] + prestige, validate_recipient[30])
                # cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters WHERE Player_Name = ? AND Character_Name = ? OR Nickname =?", (author, character_name, character_name))
                # (player_name, player_id, character_name, titles, description, oath, level, tier, milestones, milestones_required, trials, trials_required, gold, effective_gold, flux, color, mythweavers, image_link, tradition_name, tradition_link, template_name, template_link, fame, title, prestige):
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(validate_recipient[23])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                session_name = session_info[2]
                embed_log = log_embed(validate_recipient[2], author, level_information[0], rewarded, new_milestones, level_information[1], mythic_information[0], session_info[9], validate_recipient[10] + session_info[9], mythic_information[1], validate_recipient[12]+gold_received, gold_received, validate_recipient[13]+gold_received, gold_transaction_id[0], validate_recipient[15] + awarded_flux, awarded_flux, None, None, None, None, None, validate_recipient[26] + session_info[10], session_info[10], validate_recipient[29] + prestige, prestige, f"Session {session_name} with ID: {session_id} claimed")
                logging_thread = guild.get_thread(validate_recipient[25])
                await logging_thread.send(embed=embed_log)
                await interaction.response.send_message(f"Rewards have been claimed for {character_name}!")
        else:
            await interaction.response.send_message(f"{character_name} is not a valid Character name or Nickname.")

@gamemaster.command()
async def notify(interaction: discord.Interaction, session_id: int, message: str = "Session Notice!"):
    "Notify players about an ACTIVE Session."
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    guild = interaction.guild
    sql = f"SELECT Message, Session_Name, Session_Thread, Play_Time from Sessions WHERE Session_ID = ? AND IsActive = ? AND GM_Name = ? ORDER BY Created_Time Desc Limit 1"
    val = (session_id, 1, author)
    cursor.execute(sql, val)
    info = cursor.fetchone()
    if info is not None:
        cursor.execute(f"SELECT Player_ID FROM Sessions_Participants WHERE Session_ID = ?", (session_id,))
        participants = cursor.fetchall()
        ping_list = f"NOTICE:"
        for player in participants:
            ping_list += f"<@{player[0]}> "
        if message == "Session Notice!":
            message == f"Session Notice! Session is in <t:{info[3]}:R>"
        ping_list = ping_list + f"your GM {interaction.user.name} has the following message for you! \r\n {message}"
        quest_thread = guild.get_thread(info[2])
        await quest_thread.send(content=ping_list, allowed_mentions=discord.AllowedMentions(users=True))
    if info is None:
        await interaction.response.send_message(f"Invalid Session ID of {session_id} associated with host {author}")
    cursor.close()
    db.close()



@gamemaster.command()
@app_commands.describe(group="Displaying All Participants & Signups, Active Participants Only, or Potential Sign-ups Only for a session")
@app_commands.choices(group=[discord.app_commands.Choice(name='All', value=1), discord.app_commands.Choice(name='Participants', value=2), discord.app_commands.Choice(name='Sign-ups', value=3)])
async def display(ctx: commands.Context, session_id: int, group: discord.app_commands.Choice[int] = 1):
    "ALL: THIS COMMAND DISPLAYS SESSION INFORMATION"
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT GM_Name, Session_Name, Session_Range, Play_location, Play_Time, Overview, Description, Message, IsActive FROM Sessions WHERE Session_ID = {session_id}")
    session_info = cursor.fetchone()
    if group == 1:
        group = 1
    else:
        group = group.value
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
"""