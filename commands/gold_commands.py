from math import floor
import sqlite3
from discord.ext import commands
import datetime
import os
from pywaclient.api import BoromirApiClient as WaClient
os.chdir("C:\\pathparser")


@gold.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Gold Help", description=f'This is a list of Gold management commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Claim**', value=f'Claim gold that should be received through downtime!', inline=False)
    embed.add_field(name=f'**Buy**', value=f'Buy items, or send your gold out into the open wide world.', inline=False)
    embed.add_field(name=f'**Send**', value=f'Send gold to another player', inline=False)
    await ctx.response.send_message(embed=embed)


@gold.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def claim(ctx: commands.Context, character_name: str, amount: float, reason: str):
    """Claim gold based on downtime activities, or through other interactions with NPCs"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    reason = str.replace(reason, ";", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount <= 0:
        await ctx.response.send_message(f"Little comrade! Please give yourself some credit! {amount} is too small to claim!")
    elif amount > 0:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Nickname = ?", (author, character_name, character_name))
        player_info = cursor.fetchone()
        if player_info is None:
            await ctx.response.send_message(f"{author} does not have a character named {character_name}")
        else:
            gold_info = gold_calculation(player_info[7], player_info[6], player_info[13], player_info[14], player_info[15], amount)
            await Event.gold_change(self, guild_id, author, author_id, character_name, gold_info[3], gold_info[3], amount, reason, 'Gold_Claim')
            cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
            transaction_id = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + gold_info[3], player_info[14] + gold_info[3], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"Character has increased their wealth by {gold_info[3]} GP using a gold pouch from the shop, transaction_id: {transaction_id[0]}!"
            logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, player_info[13] + gold_info[3], gold_info[3], player_info[14] + gold_info[3], transaction_id[0], None, None, None, None, None, None, None, None, None, None, None, source)
            logging_thread = guild.get_thread(player_info[25])
            cursor.close()
            db.close()
            await logging_thread.send(embed=logging_embed)
            await ctx.response.send_message(f"{player_info[2]} has claimed {amount} gold, receiving {gold_info[3]} gold and now has {gold_info[0]} gold!.")



@gold.command()
@app_commands.describe(market_value="market value of the item regardless of crafting. Items crafted for other players have an expected value of 0.")
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def buy(ctx: commands.Context, character_name: str, expenditure: float, market_value: float, reason: str):
    """Buy items from NPCs for non-player trades and crafts. Expected Value is the MARKET price of what you are buying, not the price you are paying."""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    reason = str.replace(reason, ";", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if expenditure <= 0:
        await ctx.response.send_message(f"Little comrade! Please buy something of actual value! {expenditure} is too small to purchase anything with!")
    elif market_value < 0:
        await ctx.response.send_message(f"Little comrade! You cannot have an expected value of: {market_value}, it is too little gold to work with!")
    elif expenditure > 0:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Nickname = ?", (author, character_name, character_name))
        player_info = cursor.fetchone()
        if player_info[0] is None:
            await ctx.response.send_message(f"{ctx.user.name} does not have a character named {character_name}")
        else:
            expenditure = -abs(expenditure)
            print(player_info[13])
            print(abs(expenditure))
            if player_info[13] >= abs(expenditure):
                market_value_adjusted = market_value + expenditure
                remaining = round(expenditure + player_info[13], 2)
                gold_value = player_info[14] + market_value_adjusted
                if player_info[6] == 'Poverty':
                    max_wealth = 80 * (player_info[7] ** 2)
                    if gold_value > max_wealth:
                        await ctx.response.send_message(f"{player_info[2]} has too much money and needs to give some to charitable causes by using the 'buy' command where they receive nothing in return!")
                        return
                elif player_info[6] == 'Absolute':
                    max_wealth = 5 * player_info[7]
                    if gold_value > max_wealth:
                        await ctx.response.send_message(f"{player_info[2]} has too much money and needs to give some to charitable causes by using the 'buy' command where they receive nothing in return!")
                        return
                expenditure = round(expenditure, 2)
                market_value_adjusted = round(market_value_adjusted, 2)
                await Event.gold_change(self, guild_id, author, author_id, character_name, expenditure, market_value_adjusted, market_value_adjusted, reason, 'Gold_Buy')
                cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                transaction_id = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + expenditure, player_info[14] + market_value_adjusted, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"Character of {character_name} has spent {expenditure} GP in return for {market_value} GP using the buy command, transaction_id: {transaction_id[0]}!"
                print(f"THIS IS {player_info[13] + expenditure} PLAYER INFO AND EXPENDITURE")
                print(f"this is the raw {expenditure}")
                logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, player_info[13] + expenditure, expenditure, round(player_info[14] + market_value_adjusted,2), transaction_id[0], None, None, None, None, None, None, None, None, None, None, None, source)
                logging_thread = guild.get_thread(player_info[25])
                print(expenditure)
                await logging_thread.send(embed=logging_embed)
                await ctx.response.send_message(f"{player_info[2]} has spent {abs(expenditure)} gold and has received {market_value_adjusted} in expected value return. Leaving them with {remaining} gold.")
            else:
                await ctx.response.send_message(f"{player_info[2]} does not have enough gold to make this purchase!")
    cursor.close()
    db.close()


@gold.command()
@app_commands.autocomplete(character_from=own_character_select_autocompletion)
@app_commands.autocomplete(character_to=character_select_autocompletion)
async def send(ctx: commands.Context, character_from: str, character_to: str, amount: float, expected_value: float, reason: str):
    """Send gold to a crafter or other players for the purposes of their transactions. Expected Value is the MARKET price of what they will give you in return."""
    character_from = str.replace(str.title(character_from), ";", "")
    character_to = str.replace(str.title(character_to), ";", "")
    reason = str.replace(reason, ";", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount <= 0:
        await ctx.response.send_message(f"Little comrade! Please SEND something of actual value! {amount} is too small to claim!")
    elif expected_value < 0:
        await ctx.response.send_message(f"Expected Value cannot be less than 0!")
    elif expected_value < amount:
        await ctx.response.send_message(f"If they're charging you higher than the market value, go buy it from an NPC...")
    else:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Player_Name = ? AND Nickname = ?", (author, character_from, author, character_from))
        player_info = cursor.fetchone()
        if player_info[0] is None:
            await ctx.response.send_message(f"{author} does not have a character named or nicknamed {character_from}")
        else:
            if player_info[13] < amount:
                await ctx.response.send_message(f"Unlike America, you can't go into debt to resolve your debt. {player_info[1] - amount} leaves you too in debt.")
            else:
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? or Nickname = ? ", (character_to, character_to))
                send_info = cursor.fetchone()
                if send_info is None:
                    await ctx.response.send_message(f"Could not find a character named {character_to}!")
                else:
                    buttons = ["✅", "❌"]  # checkmark X symbol
                    embed = discord.Embed(title=f"Are you sure you want {character_from} to send {amount} GP to {character_to}?", description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
                    await ctx.response.send_message(embed=embed)
                    msg = await ctx.original_response()
                    for button in buttons:
                        await msg.add_reaction(button)
                    while True:
                        try:
                            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
                        except asyncio.TimeoutError:
                            embed.set_footer(text="Request has timed out.")
                            await msg.edit(embed=embed)
                            await msg.clear_reactions()
                            return print("timed out")
                        else:
                            if reaction.emoji == u"\u264C":
                                embed = discord.Embed(title=f"You have thought better of freely giving your money", description=f"Savings!", colour=discord.Colour.blurple())
                                await msg.edit(embed=embed)
                                await msg.clear_reactions()
                            if reaction.emoji == u"\u2705":
                                embed = discord.Embed(title=f"{character_from} has given {amount} in GP to {character_to}", description=f"Hope it was worth it.", colour=discord.Colour.red())
                                await msg.clear_reactions()
                                expected_value_adjusted = expected_value + -abs(amount)
                                print(-abs(amount))
                                print(type(-abs(amount)))
                                expected_value_adjusted = round(expected_value_adjusted, 2)
                                amount = round(amount, 2)
                                await Event.gold_change(self, guild_id, author, author_id, character_from, -abs(amount), expected_value_adjusted, expected_value_adjusted, reason, 'gold send')
                                cursor.execute(f"Select MAX(Transaction_ID) from A_Audit_Gold order by Transaction_ID desc limit 1")
                                transaction_id_from = cursor.fetchone()
                                await Event.gold_change(self, guild_id, send_info[0], send_info[1], send_info[2], amount, amount, amount, reason, 'Gold_Buy')
                                cursor.execute(f"Select MAX(Transaction_ID) from A_Audit_Gold order by Transaction_ID desc limit 1")
                                transaction_id_to = cursor.fetchone()
                                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                accepted_bio_channel = cursor.fetchone()
                                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + -abs(amount), player_info[14] + expected_value_adjusted, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                                bio_message = await bio_channel.fetch_message(player_info[24])
                                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                source = f"Character of {character_from} has spent {amount} GP in return for {expected_value_adjusted} using the send command, transaction_id: {transaction_id_from[0]}!"
                                logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, player_info[13] + -abs(amount), -abs(amount), player_info[14] + expected_value_adjusted, transaction_id_from[0], None, None, None, None, None, None, None, None, None, None, None, source)
                                logging_thread = guild.get_thread(player_info[25])
                                await logging_thread.send(embed=logging_embed)
                                to_bio_embed = character_embed(send_info[0], send_info[1], send_info[2], send_info[4], send_info[5], send_info[6], send_info[7], send_info[8], send_info[9], send_info[10], send_info[11], send_info[12], send_info[13] + amount, send_info[14] + expected_value_adjusted, send_info[16], send_info[17], send_info[18], send_info[19], send_info[20], send_info[21], send_info[22], send_info[23], send_info[27], send_info[28], send_info[30], send_info[31])
                                to_bio_message = await bio_channel.fetch_message(send_info[24])
                                await to_bio_message.edit(content=to_bio_embed[1], embed=to_bio_embed[0])
                                to_source = f"Character of {character_to} has received {amount} GP in return for services of {expected_value_adjusted} using the send command, transaction_id: {transaction_id_to[0]}!"
                                to_logging_embed = log_embed(send_info[0], author, None, None, None, None, None, None, None, None, send_info[13] + amount, amount, send_info[14] + amount, transaction_id_to[0], None, None, None, None, None, None, None, None, None, None, None, to_source)
                                to_logging_thread = guild.get_thread(send_info[25])
                                await to_logging_thread.send(embed=to_logging_embed)
                                await Event.gold_transact(self, transaction_id_from[0], transaction_id_to[0], guild_id)
                                await Event.gold_transact(self, transaction_id_to[0], transaction_id_from[0], guild_id)
                                embed.set_footer(text=f"Transaction ID was {transaction_id_from[0]}")
                                await msg.edit(embed=embed)
                                break
    cursor.close()
    db.close()


@gold.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def history(ctx: commands.Context, character_name: str, current_page: int = 1):
    """This command displays gold audit history."""
    character = str.replace(str.title(character_name), ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    sql = f"""SELECT COUNT(Character_Name) FROM A_Audit_Gold where Character_Name = ?"""
    val = [character]
    cursor.execute(sql, val)
    leaders = cursor.fetchone()
    max_page = math.ceil(leaders[0] / 8)
    if current_page >= max_page:
        current_page = max_page
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    low = 0 + (8 * (current_page-1))
    offset = 8
    cursor.execute(f"""Select Transaction_ID, Author_Name, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time from A_Audit_Gold WHERE Character_Name = ? LIMIT {low}, {offset}""", (character,))
    pull = cursor.fetchall()
    embed = discord.Embed(title=f"{character} character page {current_page}", description=f"This is list of {character}'s transactions", colour=discord.Colour.red())
    for result in pull:
        embed.add_field(name=f'Transaction Information', value=f'**Date**: {result[8]}, **Source**: {result[7]}', inline=False)
        embed.add_field(name=f'Changes:', value=f'{result[3]} Liquid GP {result[4]} Effective GP, {result[5]} Life Time GP')
        embed.add_field(name=f'Transaction:', value=f'Transaction_ID: {result[0]}, Reason: {result[6]}', inline=False)
    await ctx.response.send_message(embed=embed)
    msg = await ctx.original_response()
    for button in buttons:
        await msg.add_reaction(button)
    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user.id == ctx.user.id and reaction.emoji in buttons, timeout=60.0)
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
                low = 0 + (8 * (current_page - 1))
                offset = 8
            elif reaction.emoji == u"\u2B05" and current_page > 1:
                current_page -= 1
                low = 0 + (8 * (current_page - 1))
                offset = 8
            elif reaction.emoji == u"\u27A1" and current_page < max_page:
                current_page += 1
                low = 0 + (8 * (current_page - 1))
                offset = 8
            elif reaction.emoji == u"\u23E9":
                current_page = max_page
                low = 0 + (8 * (current_page - 1))
                offset = 8
            for button in buttons:
                await msg.remove_reaction(button, ctx.user)
            if current_page != previous_page:
                cursor.execute(f"""Select Transaction_ID, Author_Name, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time from A_Audit_Gold WHERE Character_Name = ? LIMIT {low}, {offset}""", (character,))
                pull = cursor.fetchall()
                embed = discord.Embed(title=f"{character} character page {current_page}", description=f"This is list of {character}'s transactions", colour=discord.Colour.red())
                for result in pull:
                    embed.add_field(name=f'Transaction Information', value=f'**Date**: {result[8]}, **Source**: {result[7]}', inline=False)
                    embed.add_field(name=f'Changes:', value=f'{result[3]} Liquid GP {result[4]} Effective GP, {result[5]} Life Time GP')
                    embed.add_field(name=f'Transaction:', value=f'Transaction_ID: {result[0]}, Reason: {result[6]}', inline=False)
                await msg.edit(embed=embed)

