import logging
from math import floor
import sqlite3
from discord.ext import commands
import datetime
import os
from pywaclient.api import BoromirApiClient as WaClient

os.chdir("C:\\pathparser")
import shared_functions
from discord.ext import commands
import aiosqlite


# *** DATABASE FUNCTIONS *** #
async def level_calculation(guild_id, character_name, personal_cap, level, base, easy, medium, hard, deadly, misc):
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as cursor:
        try:
            await cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
            max_level = await cursor.fetchone()
            await cursor.execute(f"SELECT easy, medium, hard, deadly from AA_Milestones WHERE level = ?"), (level,)
            milestone_information = await cursor.fetchone()
            easy_milestones = milestone_information[0] * easy if milestone_information[0] is not None else 0
            medium_milestones = milestone_information[1] * medium if milestone_information[1] is not None else 0
            hard_milestones = milestone_information[2] * hard if milestone_information[2] is not None else 0
            deadly_milestones = milestone_information[3] * deadly if milestone_information[3] is not None else 0
            new_milestone_total = easy_milestones + medium_milestones + hard_milestones + deadly_milestones + misc
            maximum_level = int(max_level[0]) if int(max_level[0]) <= personal_cap else personal_cap
            await cursor.execute(
                f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= ? AND Level <= ? ORDER BY Minimum_Milestones DESC  LIMIT 1",
                (base + new_milestone_total, maximum_level))
            new_level_information = await cursor.fetchone()
            if new_milestone_total != 0:
                await cursor.execute(
                    f"UPDATE Player_Characters SET Level = ?, Milestones = ?, Milestones_Required = ? WHERE Character_Name = ?",
                    (new_level_information[0], base + new_milestone_total,
                     base + new_level_information[1] + new_level_information[2] - new_milestone_total, character_name))
                await cursor.commit()
            return_value = (new_level_information[0], new_level_information[1], new_level_information[2],
                            new_level_information[1] + new_level_information[2] - new_milestone_total)
        except:
            logging.exception(f"Error in level calculation for {character_name}")
            return_value = -1
        finally:
            await cursor.close()
            return return_value


async def mythic_calculation(guild_id, character_name, level, trials, trial_change):
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as cursor:
        try:
            # Call limiters and restrictions.
            await cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Mythic_Cap'")
            max_mythic = await cursor.fetchone()
            await cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_limit_1'")
            tier_rate_limit_1 = await cursor.fetchone()
            await cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_limit_2'")
            tier_rate_limit_2 = await cursor.fetchone()
            await cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_limit_Breakpoint'")
            tier_rate_limit_breakpoint = await cursor.fetchone()
            tier_rate_limit_modifier = tier_rate_limit_1[0] if level < tier_rate_limit_breakpoint[0] else tier_rate_limit_2[0]
            tier_max = floor(trials / tier_rate_limit_modifier) if floor(trials / tier_rate_limit_modifier) <= max_mythic[0] else max_mythic[0]
            # Call the mythic tier information.
            await cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Mythic  WHERE Trials <= ? AND Tier <= ? ORDER BY Trials DESC  LIMIT 1",
                                (trials + trial_change, tier_max))
            new_mythic_information = await cursor.fetchone()
            # Update Mythic tier if you changed the trial amount.
            if trial_change != 0:
                await cursor.execute(
                    f"UPDATE Player_Characters SET Tier = ?, Trials = ?, Trials_Required = ? WHERE Character_Name = ?",
                    (new_mythic_information[0], trials + trial_change, new_mythic_information[1] + new_mythic_information[2] - trials + trial_change, character_name))
                await cursor.commit()
            # return mythic tier, trials, and mythic trials remaining.
            return_value = (new_mythic_information[0], trials + trial_change, new_mythic_information[1] + new_mythic_information[2] - trial_change - trials)
        except:
            logging.exception(f"Error in level calculation for {character_name}")
            return_value = -1
        finally:
            await cursor.close()
            return return_value


async def gold_calculation(guild_id, character_name, level, oath, gold, gold_value, gold_value_max, gold_change):
    async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as cursor:
        try:
            if gold_change > 0:
                if oath == 'Offerings':
                    difference = gold_change * .5
                    gold_total = gold + difference
                    gold_value_total = gold_value + difference
                elif oath == 'Poverty':
                    max_gold = 80 * level * level
                    if gold_value > max_gold and gold_change > 0:
                        difference = 0
                        gold_total = gold
                        gold_value_total = gold_value
                    elif gold_value > max_gold and gold_change < 0:
                        difference = gold_change
                        gold_total = gold + difference
                        gold_value_total = gold_value + difference
                    elif gold_value + gold_change > max_gold:
                        difference = max_gold - gold_value
                        gold_total = gold + difference
                        gold_value_total = gold_value + difference
                    else:
                        difference = gold_change
                        gold_total = gold + difference
                        gold_value_total = gold_value + difference
                elif oath == 'Absolute':
                    max_gold = level * 5
                    if gold_value > max_gold and gold_change > 0:
                        difference = 0
                        gold_total = gold + difference
                        gold_value_total = gold_value + difference
                    elif gold_value > max_gold and gold_change < 0:
                        difference = gold_change
                        gold_total = gold + difference
                        gold_value_total = gold_value + difference
                    elif gold_value + gold_change > max_gold:
                        difference = max_gold - gold_value
                        gold_total = gold + difference
                        gold_value_total = gold_value + difference
                    else:
                        difference = gold_change
                        gold_total = gold + difference
                        gold_value_total = gold_value + difference
                else:
                    gold_total = gold + gold_change
                    gold_value_total = gold_value + gold_change
                    difference = gold_change
            else:
                gold_total = gold + gold_change
                gold_value_total = gold_value + gold_change
                difference = gold_change
            if gold_change != 0
                await cursor.execute(
                    f"UPDATE Player_Characters SET Gold = ?, Gold_Value = ?, Gold_Value_Max = ? WHERE Character_Name = ?",
                    (gold_total, gold_value_total, gold_value_max + gold_change, character_name))
                await cursor.commit()
            return_value = (gold_total, gold_value_total, gold_value_max + gold_change)
        except:
            logging.exception(f"Error in level calculation for {character_name}")
            return_value = -1
        finally:
            await cursor.close()
            return return_value




async def flux_calculation(guild_id, character_name, flux, flux_change):
    ...


@character.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Character Help", description=f'This is a list of Character commands',
                          colour=discord.Colour.blurple())
    embed.add_field(name=f'**Register**', value=f'Register your character!', inline=False)
    embed.add_field(name=f'**Retire**', value=f'Retire a registered character!', inline=False)
    embed.add_field(name=f'**levelup**', value=f'Use Medium Jobs from the unbelievaboat shop.', inline=False)
    embed.add_field(name=f'**trialup**', value=f'Use Trial Catch Ups from the unbelievaboat shop', inline=False)
    embed.add_field(name=f'**Pouch**', value=f'Use Gold Pouches from the unbelievaboat shop.', inline=False)
    embed.add_field(name=f'**Display**', value=f'View information about a character.', inline=False)
    embed.add_field(name=f'**List**', value=f'View information about characters in a level range.', inline=False)
    embed.add_field(name=f'**Edit**',
                    value=f'Change the Character Name, Mythweavers, Image, Nickname, Titles, Description, Oath of your character, or color of your embed.',
                    inline=False)
    embed.add_field(name=f'**Entitle**',
                    value=f'Use an approved title item from the unbelievaboat Store. NOTE: Your most famous title is the one that will be used.',
                    inline=False)
    embed.add_field(name=f'**Proposition**', value=f'Use your prestigious status to proposition an act.', inline=False)
    embed.add_field(name=f'**Cap**', value=f'Stop yourself from leveling! For reasons only you understand.',
                    inline=False)
    embed.add_field(name=f'**Backstory**', value=f'Give your character a backstory if they do not already have one.',
                    inline=False)
    await ctx.response.send_message(embed=embed)


@character.command()
@app_commands.describe(oath="Determining future gold gain from sessions and gold claims.")
@app_commands.choices(oath=[discord.app_commands.Choice(name='No Oath', value=1),
                            discord.app_commands.Choice(name='Oath of Offerings', value=2),
                            discord.app_commands.Choice(name='Oath of Poverty', value=3),
                            discord.app_commands.Choice(name='Oath of Absolute Poverty', value=4)])
@app_commands.describe(nickname='a shorthand way to look for your character in displays')
async def register(ctx: commands.Context, character_name: str, mythweavers: str, image_link: str, nickname: str = None,
                   titles: str = None, description: str = None, oath: discord.app_commands.Choice[int] = 1,
                   color: str = '#5865F2', backstory: str = None):
    """Register your character"""
    if character_name is not None:
        true_character_name = str.replace(
            str.replace(str.replace(str.replace(str.replace(str.title(character_name), ";", ""), "(", ""), ")", ""),
                        "[", ""), "]", "")
        character_name = unidecode(true_character_name)
    else:
        await ctx.response.send_message(f"Character Name is required")
        return
    if nickname is not None:
        nickname = str.replace(str.replace(str.title(nickname), ";", ""), ")", "")
    if titles is not None:
        titles = str.replace(titles, ";", "")
    if description is not None:
        description = str.replace(description, ";", "")
    if mythweavers is not None:
        mythweavers = str.replace(str.replace(str.lower(mythweavers), ";", ""), ")", "")
        mythweavers_valid = str.lower(mythweavers[0:5])
        if mythweavers_valid != 'https':
            await ctx.response.send_message(f"Mythweavers link is missing HTTPS:", ephemeral=True)
            return
    else:
        await ctx.response.send_message(f"Mythweavers link is required", ephemeral=True)
        return
    if image_link is not None:
        image_link = str.replace(str.replace(image_link, ";", ""), ")", "")
        image_link_valid = str.lower(image_link[0:5])
        if image_link_valid != 'https':
            await ctx.response.send_message(f"Image link is missing HTTPS:")
            return
    else:
        await ctx.response.send_message(f"image link is required", ephemeral=True)
        return
    if oath == 1:
        oath = 1
    else:
        oath = oath.value
    if oath == 2:
        oath_name = 'Offerings'
        starting_gold = 1500
    elif oath == 3:
        oath_name = 'Poverty'
        starting_gold = 720
    elif oath == 4:
        oath_name = 'Absolute'
        starting_gold = 15
    else:
        oath_name = 'No Oath'
        starting_gold = 3000
    regex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
    match = re.search(regex, color)
    if len(color) == 7 and match:
        guild_id = ctx.guild_id
        author = ctx.user.name
        author_id = ctx.user.id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Player_Name, Character_Name from Player_Characters where Character_Name = ?""",
                       (character_name,))
        results = cursor.fetchone()
        cursor.execute(f"""SELECT Player_Name, Character_Name from A_STG_Player_Characters where Character_Name = ?""",
                       (character_name,))
        results2 = cursor.fetchone()
        cursor.close()
        db.close()
        print(results, results2)
        if results is None and results2 is None:
            int_color = int(color[1:], 16)
            await EventCommand.stage_character(self, true_character_name, character_name, author, author_id, guild_id,
                                               nickname, titles, description, oath_name, mythweavers, image_link, color,
                                               backstory)
            await EventCommand.stg_gold_change(self, guild_id, author, author_id, character_name, starting_gold,
                                               starting_gold, 3000, 'Character Creation', 'Character Create')
            embed = discord.Embed(title=f"{character_name}", url=f'{mythweavers}', description=f"Other Names: {titles}",
                                  color=int_color)
            embed.set_author(name=f'{author}')
            embed.set_thumbnail(url=f'{image_link}')
            embed.add_field(name="Information", value=f'**Level**: 3, **Mythic Tier**: 0', inline=False)
            embed.add_field(name="Experience", value=f'**Milestones**: 0, **Remaining**: 3')
            embed.add_field(name="Mythic", value=f'**Trials**: 0, **Remaining**: 0')
            embed.add_field(name="Current Wealth", value=f'**GP**: {starting_gold}', inline=False)
            embed.add_field(name="Current Flux", value=f'**Flux**: 0')
            if oath_name == 'Offerings':
                embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
            elif oath_name == 'Poverty':
                embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
            elif oath_name == 'Absolute':
                embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
            else:
                embed.set_footer(text=f'{description}')
            try:
                await ctx.response.send_message(embed=embed)
            except discord.errors.HTTPException:
                embed = discord.Embed(title=f"{character_name}",
                                      url=f'https://cdn.discordapp.com/attachments/977939245463392276/1194141019088891984/super_saiyan_mr_bean_by_zakariajames6_defpqaz-fullview.jpg?ex=65af457d&is=659cd07d&hm=57bdefe2d376face6a842a7b7a5ed8021e854a64e798f901824242c4a939a37b&',
                                      description=f"Other Names: {titles}", color=int_color)
                embed.set_author(name=f'{author}')
                embed.set_thumbnail(
                    url=f'https://cdn.discordapp.com/attachments/977939245463392276/1194140952789536808/download.jpg?ex=65af456d&is=659cd06d&hm=1613025f9f1c1263823881c91a81fc4b93831ff91df9f4a84c813e9fab6467e9&')
                embed.add_field(name="Information", value=f'**Level**: 3, **Mythic Tier**: 0', inline=False)
                embed.add_field(name="Experience", value=f'**Milestones**: 0, **Remaining**: 3')
                embed.add_field(name="Mythic", value=f'**Trials**: 0, **Remaining**: 0')
                embed.add_field(name="Current Wealth", value=f'**GP**: {starting_gold}', inline=False)
                embed.add_field(name="Current Flux", value=f'**Flux**: 0')
                embed.set_footer(text=f'Oops! You used a bad URL, please fix it.')
                await ctx.response.send_message(embed=embed)
                await EventCommand.fix_character(self, guild_id, character_name)
        else:
            await ctx.response.send_message(f"{character_name} has already been registered by {author}", ephemeral=True)
    else:
        await ctx.response.send_message(f"Invalid Hex Color Code!", ephemeral=True)


@character.command()
@app_commands.autocomplete(name=own_character_select_autocompletion)
@app_commands.describe(oath="Determining future gold gain from sessions and gold claims.")
@app_commands.choices(oath=[discord.app_commands.Choice(name='No Oath', value=1),
                            discord.app_commands.Choice(name='Oath of Offerings', value=2),
                            discord.app_commands.Choice(name='Oath of Poverty', value=3),
                            discord.app_commands.Choice(name='Oath of Absolute Poverty', value=4),
                            discord.app_commands.Choice(name='No Change', value=5)])
@app_commands.describe(new_nickname='a shorthand way to look for your character in displays')
async def edit(ctx: commands.Context, name: str, new_character_name: str = None, mythweavers: str = None,
               image_link: str = None, new_nickname: str = None, titles: str = None, description: str = None,
               oath: discord.app_commands.Choice[int] = 5, color: int = None):
    """Register your character"""
    name = str.replace(
        str.replace(str.replace(str.replace(str.replace(str.title(name), ";", ""), "(", ""), ")", ""), "[", ""), "]",
        "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    if oath == 5:
        oath = 5
    else:
        oath = oath.value
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    sql = f"""Select True_Character_Name, Nickname, Titles, Description, Mythweavers, Image_Link, Oath, Color, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Gold_Value, Gold_Value_Max, Flux, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? OR Player_Name = ? AND  Nickname = ?"""
    val = (author, name, author, name)
    cursor.execute(sql, val)
    results = cursor.fetchone()
    await ctx.response.defer(thinking=True, ephemeral=True)
    if results is None:
        sql = f"""Select True_Character_Name, Nickname, Titles, Description, Mythweavers, Image_Link, Oath, Color, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Gold_Value, Gold_Value_Max, Flux, Character_Name from A_STG_Player_Characters where Player_Name = ? AND Character_Name = ? OR  Player_Name = ? AND Nickname = ?"""
        val = (author, name, author, name)
        cursor.execute(sql, val)
        results = cursor.fetchone()
        if results is None:
            await ctx.response.send_message(
                f"Cannot find any {name} owned by {author} with the supplied name or nickname.")
        else:
            if new_character_name is not None:
                new_character_name = str.replace(str.replace(
                    str.replace(str.replace(str.replace(str.title(new_character_name), ";", ""), ")", ""), "("), "["),
                                                 "]")
                true_character_name = unidecode(new_character_name)
            else:
                true_character_name = results[0]
                new_character_name = results[18]
            if new_nickname is not None:
                new_nickname = str.replace(str.replace(str.title(new_nickname), ";", ""), ")", "")
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
            print(f"test")
            print(mythweavers)
            if mythweavers is not None:
                print(mythweavers)
                mythweavers = str.replace(str.replace(str.lower(mythweavers), ";", ""), ")", "")
                mythweavers_valid = str.lower(mythweavers[0:5])
                print(mythweavers_valid)
                if mythweavers_valid != 'https':
                    await ctx.response.send_message(f"Mythweavers link is missing HTTPS:")
                    return
            else:
                mythweavers = results[4]
            if image_link is not None:
                image_link = str.replace(str.replace(image_link, ";", ""), ")", "")
                image_link_valid = str.lower(image_link[0:5])
                print(image_link_valid)
                if image_link_valid != 'https':
                    await ctx.response.send_message(f"Image link is missing HTTPS:")
                    return
            else:
                image_link = results[5]
            if oath == 1:
                oath_name = 'No Oath'
                gold = 3000
            elif oath == 2:
                oath_name = 'Offerings'
                gold = 1500
            elif oath == 3:
                oath_name = 'Poverty'
                gold = 720
            elif oath == 4:
                oath_name = 'Absolute'
                gold = 15
            else:
                oath_name = results[6]
            if color is not None:
                regex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
                match = re.search(regex, color)
            else:
                color = results[7]
                regex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
                match = re.search(regex, color)
            if len(color) == 7 and match:
                cursor.close()
                db.close()
                if results is not None:
                    int_color = int(color[1:], 16)
                    true_name = results[0]
                    if oath_name != results[6]:
                        await EventCommand.gold_set(self, guild_id, author, author_id, name, gold, gold, gold,
                                                    'Oath Change', 'Character Edit', 2)
                    await EventCommand.edit_stg_character(self, true_name, true_character_name, new_character_name,
                                                          guild_id, new_nickname, titles, description, oath_name,
                                                          mythweavers, image_link, color, author)
                    embed = discord.Embed(title=f"Edited Character: {new_character_name}", url=f'{mythweavers}',
                                          description=f"Other Names: {titles}", color=int_color)
                    embed.set_author(name=f'{author}')
                    embed.set_thumbnail(url=f'{image_link}')
                    embed.add_field(name="Information", value=f'**Level**: {results[8]}, **Mythic Tier**: {results[9]}',
                                    inline=False)
                    embed.add_field(name="Experience",
                                    value=f'**Milestones**: {results[10]}, **Remaining**: {results[11]}')
                    embed.add_field(name="Mythic", value=f'**Trials**: {results[12]}, **Remaining**: {results[13]}')
                    embed.add_field(name="Current Wealth",
                                    value=f'**Current gold**: {results[14]} GP, **Effective Gold**: {results[15]} GP, **Lifetime Wealth**: {results[16]} GP',
                                    inline=False)
                    embed.add_field(name="Current Flux", value=f'**Flux**: {results[17]}', inline=False)
                    if oath_name == 'Offerings':
                        embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
                    elif oath_name == 'Poverty':
                        embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
                    elif oath_name == 'Absolute':
                        embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
                    else:
                        embed.set_footer(text=f'{description}')
                    await ctx.response.send_message(embed=embed)
            else:
                await ctx.response.send_message(f"Invalid Hex Color Code!")
    else:
        if new_character_name is not None:
            new_character_name = str.replace(str.replace(str.title(new_character_name), ";", ""), ")", "")
            true_character_name = unidecode(new_character_name)
        else:
            new_character_name = unidecode(results[0])
            true_character_name = results[0]
        if new_nickname is not None:
            new_nickname = str.replace(str.replace(str.title(new_nickname), ";", ""), ")", "")
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
            mythweavers = str.replace(str.replace(mythweavers, ";", ""), ")", "")
            mythweavers_valid = str.lower(mythweavers[0:5])
            if mythweavers_valid != 'https':
                await ctx.followup.send(f"Mythweavers link is missing HTTPS:")
                return
        else:
            mythweavers = results[4]
        if image_link is not None:
            image_link = str.replace(str.replace(image_link, ";", ""), ")", "")
            image_link_valid = str.lower(image_link[0:5])
            if image_link_valid != 'https':
                await ctx.followup.send(f"Image link is missing HTTPS:")
                return
        else:
            image_link = results[5]
        if oath == 1:
            oath_name = 'No Oath'
        elif oath == 2:
            oath_name = 'Offerings'
        elif oath == 3:
            oath_name = 'Poverty'
        elif oath == 4:
            oath_name = 'Absolute'
        else:
            oath_name = results[6]
            print(f"printing {oath_name} as Absolute")
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
                true_name = results[0]
                if oath_name != results[6] and results[8] < 7:
                    if oath == 2:
                        await EventCommand.gold_set(self, guild_id, author, author_id, name, results[14] / 2,
                                                    results[15] - results[14] / 2, results[15], 'Oath Change',
                                                    'Character Edit', 1)
                    else:
                        await EventCommand.gold_set(self, guild_id, author, author_id, name, results[14], results[15],
                                                    results[15], 'Oath Change', 'Character Edit', 1)
                print(f"printing {oath_name}")
                await EventCommand.edit_character(self, true_name, true_character_name, new_character_name, guild_id,
                                                  new_nickname, titles, description, oath_name, mythweavers, image_link,
                                                  color, author)
                if results[23] is not None:
                    await EventCommand.edit_bio(self, guild_id, new_character_name, None, results[22])
                cursor.execute(
                    f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link, Article_ID FROM Player_Characters where Character_Name = ? or Nickname = ?",
                    (new_character_name, new_nickname))
                player_info = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
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
                embed = discord.Embed(title=f"Edited Character: {new_character_name}", url=f'{mythweavers}',
                                      description=f"Other Names: {titles}", color=int_color)
                embed.set_author(name=f'{author}')
                embed.set_thumbnail(url=f'{image_link}')
                embed.add_field(name="Information",
                                value=f'**Level**: {player_info[7]}, **Mythic Tier**: {player_info[8]}', inline=False)
                embed.add_field(name="Experience",
                                value=f'**Milestones**: {player_info[9]}, **Remaining**: {player_info[10]}')
                embed.add_field(name="Mythic", value=f'**Trials**: {player_info[11]}, **Remaining**: {player_info[12]}')
                embed.add_field(name="Current Wealth",
                                value=f'**Current gold**: {player_info[13]} GP, **Effective Gold**: {player_info[14]} GP, **Lifetime Wealth**: {player_info[15]} GP',
                                inline=False)
                embed.add_field(name="Current Flux", value=f'**Flux**: {player_info[16]}', inline=False)
                if player_info[6] == 'Offerings':
                    embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/dSuLyJd.png')
                elif player_info[6] == 'Poverty':
                    embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/4Fr9ZnZ.png')
                elif player_info[6] == 'Absolute':
                    embed.set_footer(text=f'{description}', icon_url=f'https://i.imgur.com/ibE5vSY.png')
                else:
                    embed.set_footer(text=f'{description}')
                cursor.close()
                db.close()
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
                await ctx.followup.send(embed=embed)
        else:
            await ctx.followup.send(f"Invalid Hex Color Code!")


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def retire(ctx: commands.Context, character_name: str):
    """Retires your character"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = ctx.user.name
    sql = f"""SELECT True_Character_Name, Thread_ID from Player_Characters where  Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND  Nickname = ?"""
    val = (author, character_name, author, character_name)
    cursor.execute(sql, val)
    results = cursor.fetchone()
    cursor.close()
    db.close()
    if results is None:
        await ctx.response.send_message(
            f"there is no character registered by character name or nickname as {character_name} owned by {ctx.user.name} to unregister.",
            ephemeral=True)
    if results is not None:
        true_character_name = results[0]
        buttons = ["✅", "❌"]  # checkmark X symbol
        embed = discord.Embed(title=f"Are you sure you want to retire {true_character_name}?",
                              description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction,
                                                                                 user: user.id == ctx.user.id and reaction.emoji in buttons,
                                                    timeout=60.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Request has timed out.")
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                return print("timed out")
            else:
                if reaction.emoji == u"\u274C":
                    embed = discord.Embed(title=f"You have thought better of retirement",
                                          description=f"Carpe Diem my lad!", colour=discord.Colour.blurple())
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                if reaction.emoji == u"\u2705":
                    embed = discord.Embed(title=f"{true_character_name} has retired",
                                          description=f"Have a pleasant retirement.", colour=discord.Colour.red())
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                    await EventCommand.retire_character(self, guild_id, true_character_name, author)
                    source = f"Character has retired!"
                    logging_embed = log_embed(results[0], author, None, None, None, None, None, None, None, None, None,
                                              None, None, None, None, None, None, None, None, None, None, None, None,
                                              None, None, source)
                    logging_thread = guild.get_thread(results[1])
                    await logging_thread.send(embed=logging_embed)


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def levelup(interaction: discord.Interaction, character_name: str, amount: int):
    """Level up by using medium jobs from the unbelievaboat shop."""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild = interaction.guild
    guild_id = interaction.guild_id
    author = interaction.user.name
    user = interaction.user
    client = Client(os.getenv('UBB_TOKEN'))
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount >= 1:
        cursor.execute(f"SELECT Search from Admin Where Identifier = 'UBB_Medium_Job'")
        item_id = cursor.fetchone()
        try:
            inventory = await client.get_inventory_item(guild_id, author_id, item_id[0])
            if 0 < amount <= inventory.quantity:
                cursor.execute(
                    f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?",
                    (author, character_name, author, character_name))
                player_info = cursor.fetchone()
                if player_info is not None:
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
                    max_level = cursor.fetchone()
                    true_character_name = player_info[3]
                    personal_cap = int(max_level[0]) if player_info[29] is None else player_info[29]
                    character_level = player_info[7]
                    if player_info[7] >= int(max_level[0]) or player_info[7] > personal_cap:
                        await interaction.response.send_message(
                            f"you are currently at the level cap {max_level[0]} for the server or your personal level cap of {personal_cap}.")
                    else:
                        milestone_total = player_info[9]
                        milestones_earned = 0
                        int_max_level = int(max_level[0])
                        used = 0
                        for x in range(amount):
                            if character_level < int_max_level:
                                used = used + 1
                                new = inventory.quantity - 1
                                cursor.execute(f"SELECT Medium from AA_Milestones where level = {character_level}")
                                milestone_info = cursor.fetchone()
                                milestone_total += milestone_info[0]
                                milestones_earned += milestone_info[0]
                                cursor.execute(
                                    f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
                                current_level = cursor.fetchone()
                                remaining = current_level[1] + current_level[2] - milestone_total
                                character_level = current_level[0]
                                if x + 1 == amount or character_level == int_max_level or character_level == personal_cap:
                                    await EventCommand.adjust_milestones(self, true_character_name, milestone_total,
                                                                         remaining, character_level, guild_id, author)
                                    await client.delete_inventory_item(guild_id, author_id, item_id[0], used)
                                    mythic_information = mythic_calculation(guild_id, character_level, player_info[11],
                                                                            0)
                                    tier = 0 if player_info[8] == 0 else mythic_information[0]
                                    cursor.execute(
                                        f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                    accepted_bio_channel = cursor.fetchone()
                                    cursor.execute(
                                        f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                                    character_log_channel_id = cursor.fetchone()
                                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2],
                                                                player_info[4], player_info[5], player_info[6],
                                                                character_level, tier, milestone_total, remaining,
                                                                player_info[11], mythic_information[1], player_info[13],
                                                                player_info[14], player_info[16], player_info[17],
                                                                player_info[18], player_info[19], player_info[20],
                                                                player_info[21], player_info[22], player_info[23],
                                                                player_info[27], player_info[28], player_info[30],
                                                                player_info[31])
                                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                    bio_message = await bio_channel.fetch_message(player_info[24])
                                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                    source = f"{player_info[2]} has leveled up to level {character_level}! using {used} medium jobs from the shop."
                                    logging_embed = log_embed(player_info[2], author, character_level,
                                                              milestones_earned, milestone_total, remaining, tier, 0,
                                                              player_info[11], mythic_information[1], None, None, None,
                                                              None, None, None, None, None, None, None, None, None,
                                                              None, None, None, source)
                                    logging_thread = guild.get_thread(player_info[25])
                                    await logging_thread.send(embed=logging_embed)
                                    if player_info[1] != current_level[0]:
                                        cursor.execute(
                                            f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {current_level[0]}")
                                        level_range = cursor.fetchone()
                                        cursor.execute(
                                            f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Desc")
                                        level_range_max = cursor.fetchone()
                                        cursor.execute(
                                            f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Asc")
                                        level_range_min = cursor.fetchone()
                                        cursor.execute(
                                            f"SELECT True_Character_Name from Player_Characters WHERE Player_Name = '{author}' AND level >= {level_range_min[0]} AND level <= {level_range_max[0]}")
                                        level_range_characters = cursor.fetchone()
                                        member = await guild.fetch_member(interaction.user.id)
                                        if level_range_characters is None:
                                            cursor.execute(
                                                f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {character_level}")
                                            new_level_range = cursor.fetdchone()
                                            role1 = guild.get_role(level_range[2])
                                            role2 = guild.get_role(new_level_range[2])
                                            await member.remove_roles(role1)
                                            await member.add_roles(role2)
                                        else:
                                            cursor.execute(
                                                f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {character_level}")
                                            new_level_range = cursor.fetchone()
                                            role2 = guild.get_role(new_level_range[2])
                                            await member.add_roles(role2)
                                        color = player_info[17]
                                        int_color = int(color[1:], 16)
                                        embed = discord.Embed(title="Mythweavers Sheet", url=f'{player_info[18]}',
                                                              description=f"Other Names: {player_info[4]}",
                                                              color=int_color)
                                        embed.set_author(name=f'{player_info[2]} Level Up Report')
                                        embed.set_thumbnail(url=f'{player_info[19]}')
                                        embed.add_field(name="Information", value=f'**New Level**:{character_level}',
                                                        inline=False)
                                        embed.add_field(name="Experience",
                                                        value=f'**Milestones**: {milestone_total}, **Remaining to next level**: {remaining}')
                                        embed.set_footer(
                                            text=f'You have spent {used} medium jobs from the store with {new} medium jobs remaining increasing your milestones by {milestones_earned}.')
                                        await interaction.response.send_message(embed=embed)
                                        break
                                    elif player_info[1] == current_level[0]:
                                        color = player_info[17]
                                        int_color = int(color[1:], 16)
                                        embed = discord.Embed(title="Mythweavers Sheet", url=f'{player_info[18]}',
                                                              description=f"Other Names: {player_info[4]}",
                                                              color=int_color)
                                        embed.set_author(name=f'{player_info[2]} Milestone Report')
                                        embed.set_thumbnail(url=f'{player_info[19]}')
                                        embed.add_field(name="Information", value=f'**Level**: {player_info[1]}',
                                                        inline=False)
                                        embed.add_field(name="Experience",
                                                        value=f'**Milestones**: {milestone_total}, **Remaining**: {remaining}')
                                        embed.set_footer(
                                            text=f'You have spent {used} medium jobs from the store with {new} medium jobs remaining increasing your milestones by {milestones_earned}.')
                                        await interaction.response.send_message(embed=embed)
                                        break
                else:
                    await interaction.response.send_message(
                        f"{author} does not have a {character_name} registered under this Nickname or Character Name.")
            else:  # if no item is found
                await interaction.response.send_message(
                    f"{author} only has {inventory.quantity} jobs in his inventory and cannot spend {amount}.")
        except unbelievaboat.errors.HTTPError:
            await interaction.response.send_message(f"{author} does not have any medium jobs in their inventory.")
    else:
        await interaction.response.send_message(
            f"Sweet brother in christ, I'm not an MMO bot, please stop trying to overflow me!")
    cursor.close()
    db.close()
    await client.close()


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def trialup(interaction: discord.Interaction, character_name: str, amount: int):
    """Tier up by using mythic trial catchups from the unbelievaboat shop. WARNING: do not use more medium jobs than you require to level up as you will LOSE milestones this way."""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = interaction.guild_id
    guild = interaction.guild
    author = interaction.user.name
    author_id = interaction.user.id
    client = Client(os.getenv('UBB_TOKEN'))
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount >= 1:
        cursor.execute(f"SELECT Search from Admin Where Identifier = 'UBB_Mythic_Trial'")
        item_id = cursor.fetchone()
        item = int(item_id[0])
        inventory = await client.get_inventory_item(guild_id, author_id, item)
        inventory_remaining = inventory.quantity
        if 0 < amount <= inventory.quantity:
            cursor.execute(
                f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?",
                (author, character_name, author, character_name))
            player_info = cursor.fetchone()
            if player_info is not None:
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Cap'")
                max_tier = cursor.fetchone()
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
                break_point = cursor.fetchone()
                if player_info[1] <= int(break_point[0]):
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
                    tier_rate_limit = cursor.fetchone()
                else:
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
                    tier_rate_limit = cursor.fetchone()
                rate_limited_tier = floor(player_info[7] / int(tier_rate_limit[0]))
                tier_max = rate_limited_tier if rate_limited_tier <= max_tier[0] else max_tier[0]
                true_character_name = player_info[3]
                tier = player_info[8]
                print(tier)
                trial_total = player_info[11]
                used = 0
                if tier != 0:
                    if tier < tier_max:
                        for x in range(amount):
                            if tier < tier_max:
                                used = used + 1
                                trial_total = trial_total + 1
                                cursor.execute(
                                    f"SELECT Tier, Trials, Trials_Required from AA_Trials WHERE Trials <= '{trial_total}' ORDER BY Trials DESC  LIMIT 1")
                                current_level = cursor.fetchone()
                                tier = current_level[0]
                                if x + 1 == amount or tier == tier_max:
                                    inventory_remaining = inventory_remaining - used
                                    trials_required = current_level[1] + current_level[2] - trial_total
                                    await EventCommand.adjust_trials(self, character_name, trial_total, guild_id,
                                                                     author)
                                    await client.delete_inventory_item(guild_id, author_id, item_id[0], used)
                                    cursor.execute(
                                        f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                                    accepted_bio_channel = cursor.fetchone()
                                    cursor.execute(
                                        f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                                    character_log_channel_id = cursor.fetchone()
                                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2],
                                                                player_info[4], player_info[5], player_info[6],
                                                                player_info[7], tier, player_info[9], player_info[10],
                                                                player_info[11] + used, trials_required,
                                                                player_info[13], player_info[14], player_info[16],
                                                                player_info[17], player_info[18], player_info[19],
                                                                player_info[20], player_info[21], player_info[22],
                                                                player_info[23], player_info[27], player_info[28],
                                                                player_info[30], player_info[31])
                                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                                    bio_message = await bio_channel.fetch_message(player_info[24])
                                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                                    source = f"{author} has increased their tier to tier {tier}! using {used} Trial catch-ups from the shop."
                                    logging_embed = log_embed(player_info[2], author, None, None, None, None, tier,
                                                              used, player_info[11] + used, trials_required, None, None,
                                                              None, None, None, None, None, None, None, None, None,
                                                              None, None, None, None, source)
                                    logging_thread = guild.get_thread(player_info[25])
                                    await logging_thread.send(embed=logging_embed)
                                    if player_info[8] != current_level[0]:
                                        await interaction.response.send_message(
                                            content=f"you have leveled up to tier {tier} using {used} mythic trial catch ups from the shop.")
                                    if player_info[2] == current_level[0]:
                                        await interaction.response.send_message(
                                            content=f"you used {used} mythic trial catch ups from the shop!")
                                    break
                    else:
                        await interaction.response.send_message(
                            f"{true_character_name} is already at his tier cap of {tier_max}.")
                else:
                    await interaction.response.send_message(
                        f"{true_character_name} is unable to rank his mythic tier up before his first session.")
            else:
                await interaction.response.send_message(
                    f"{author} does not have a {character_name} registered under this nickname or character name.")
        elif inventory is None:
            await interaction.response.send_message(f"{author} does not have any trial catch ups in their inventory.")
        else:  # if no item is found
            await interaction.response.send_message(
                f"{author} only has {inventory.quantity} trial catch ups in his inventory and cannot spend {amount}.")
    else:
        await interaction.response.send_message(
            f"Sweet brother in christ, I'm not an MMO bot, please stop trying to overflow me!")
    cursor.close()
    db.close()
    await client.close()


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def pouch(interaction: discord.Interaction, character_name: str):
    """increase your wealth by using a gold pouch to WPL"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = interaction.guild_id
    author = interaction.user.name
    guild = interaction.guild
    client = Client(os.getenv('UBB_TOKEN'))
    author_id = interaction.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Search from Admin Where Identifier = 'UBB_Gold_Pouch'")
    item_id = cursor.fetchone()
    try:
        inventory = await client.get_inventory_item(guild_id, author_id, item_id[0])
        if inventory is not None:
            cursor.execute(
                f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or  Player_Name = ? AND Nickname = ?",
                (author, character_name, author, character_name))
            player_info = cursor.fetchone()
            if player_info is not None:
                true_character_name = player_info[3]
                new = inventory.quantity - 1
                character_level = player_info[7]
                cursor.execute(f"SELECT WPL from AA_Milestones where level = {character_level}")
                wpl_info = cursor.fetchone()
                if wpl_info[0] <= player_info[15]:
                    await interaction.response.send_message(
                        f'You are too wealthy for the gold pouch, go rob an orphanage. Your lifetime wealth is {player_info[15]} GP against a WPL of {wpl_info[0]} GP')
                else:
                    gold = wpl_info[0] - player_info[15]
                    gold_info = gold_calculation(player_info[7], player_info[6], player_info[13], player_info[14],
                                                 player_info[15], gold)
                    await EventCommand.gold_change(self, guild_id, author, author_id, true_character_name, gold_info[3],
                                                   gold_info[3], gold, 'Used Unbelievaboat Pouch',
                                                   'Used Unbelievaboat Pouch')
                    cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                    transaction_id = cursor.fetchone()
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    accepted_bio_channel = cursor.fetchone()
                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4],
                                                player_info[5], player_info[6], player_info[7], player_info[8],
                                                player_info[9], player_info[10], player_info[11], player_info[12],
                                                player_info[13] + gold_info[3], player_info[14] + gold_info[3],
                                                player_info[16], player_info[17], player_info[18], player_info[19],
                                                player_info[20], player_info[21], player_info[22], player_info[23],
                                                player_info[27], player_info[28], player_info[30], player_info[31])
                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                    bio_message = await bio_channel.fetch_message(player_info[24])
                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                    source = f"Character has increased their wealth by {gold_info[3]} GP using a gold pouch from the shop, transaction_id: {transaction_id[0]}!"
                    logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None,
                                              player_info[13] + gold_info[3], gold_info[3],
                                              player_info[14] + gold_info[3], transaction_id[0], None, None, None, None,
                                              None, None, None, None, None, None, None, source)
                    logging_thread = guild.get_thread(player_info[25])
                    await logging_thread.send(embed=logging_embed)
                    await interaction.response.send_message(
                        content=f"you have increased your wealth by {gold_info[3]} GP using a gold pouch from the shop for the character named {character_name}.")
                    await client.delete_inventory_item(guild_id, author_id, item_id[0], 1)
            else:
                await interaction.response.send_message(
                    f"{author} does not have a {character_name} registered under this character name or nickname.")
    except unbelievaboat.errors.HTTPError:
        await interaction.response.send_message(f"{author} does not have any gold pouches in their inventory.")
    cursor.close()
    db.close()
    await client.close()


@character.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
@app_commands.autocomplete(title=title_lookup)
@app_commands.choices(usage=[discord.app_commands.Choice(name='Display', value=1),
                             discord.app_commands.Choice(name='Apply Masculine Title', value=2),
                             discord.app_commands.Choice(name='Apply Feminine Title', value=3),
                             discord.app_commands.Choice(name='Change Gender', value=4)])
async def entitle(ctx: commands.Context, character_name: str, title: str, usage: discord.app_commands.Choice[int]):
    """Apply a title to yourself! This defaults to display the available titles."""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    guild = ctx.guild
    usage = 1 if usage == 1 else usage.value
    client = Client(os.getenv('UBB_TOKEN'))
    author_id = ctx.user.id
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
                        await ctx.response.send_message(
                            f'Unlike a repo-man, you do not need to collect titles. You already have the title {title_information[1]}')
                    else:
                        title_fame = item_id[1] - title_fame
                        await EventCommand.title_change(self, guild_id, author, author_id, true_character_name,
                                                        title_name, player_info[27] + title_fame,
                                                        player_info[30] + title_fame,
                                                        f'Became the title of {title_name}', 'Used entitle!')
                        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
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
                        await ctx.response.send_message(
                            content=f"you have changed your title to {title_name} and increased your fame by {title_fame} by using an item from shop for the character named {character_name}.",
                            ephemeral=True)
                        await client.delete_inventory_item(guild_id, author_id, item_id[0], 1)
                else:
                    await ctx.response.send_message(
                        f"{author} does not have a {character_name} registered under this character name or nickname.")
        except unbelievaboat.errors.HTTPError:
            await ctx.response.send_message(f"{author} does not have any {title_name} in their inventory.")
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
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
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
                await ctx.response.send_message(
                    content=f"you have changed your title to {title_name} for {character_name}.", ephemeral=True)
            else:
                await ctx.response.send_message(
                    f"{author} does not have a title registered under this character name or nickname.")
        else:
            await ctx.response.send_message(
                f"{author} does not have a {character_name} registered under this character name or nickname.")
    else:
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        cursor.execute(f"""SELECT COUNT(masculine_name) FROM Store_Title""")
        admin_count = cursor.fetchone()
        max_page = math.ceil(admin_count[0] / 20)
        current_page = 1
        low = 1 + ((current_page - 1) * 20)
        high = 20 + ((current_page - 1) * 20)
        cursor.execute(
            f"""SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"Title Store Settings Page {current_page}",
                              description=f'This is a list of available titles', colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f"Title Store Item: {result[3]}/{result[4]}",
                            value=f'**Effect**: {result[1]}, **Rewarded Fame**: {result[2]}', inline=False)
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction,
                                                                                 user: user.id == ctx.user.id and reaction.emoji in buttons,
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
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(
                        f"""SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}""")
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
async def proposition(ctx: commands.Context, character_name: typing.Optional[str], name: typing.Optional[str],
                      approver: typing.Optional[discord.Member], modify: discord.app_commands.Choice[int] = 1):
    """Proposition NPCs for Favors using your prestige!."""
    character_name = None if character_name is None else str.replace(
        str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    guild = ctx.guild
    modify = 1 if modify == 1 else modify.value
    character_name = character_name if character_name is not None else "N/A"
    name = name if name is not None else "N/A"
    approver = approver if approver is not None else "N/A"
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame Where name = ?",
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
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select MAX(Transaction_ID) FROM A_Audit_Prestige WHERE Character_Name = ?",
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
                await ctx.response.send_message(
                    content=f"<@{approver.id}>, {player_info[2]} is attempting to proposition for {name}, with ID of {proposition_id[0]} do you accept? \r\n use the /Gamemaster Proposition command to reject or deny this request using the Proposition ID!",
                    allowed_mentions=discord.AllowedMentions(users=True))
            elif title_information[0] >= item_id[4]:
                await ctx.response.send_message(f"{author} has met the limit for usage of this proposition.")
            elif player_info[27] < item_id[0]:
                await ctx.response.send_message(f"{author} does not have enough fame to use this proposition.")
            else:
                await ctx.response.send_message(f"{author} does not have enough prestige to use this proposition.")
        else:
            await ctx.response.send_message(
                f"{author} does not have a {character_name} registered under this character name or nickname.")
    elif modify == 2 and approver != "N/A" and item_id is None:
        await ctx.response.send_message(f"{name} is not an available proposition.")
    elif modify == 2 and approver == "N/A":
        await ctx.response.send_message(f"Please mention the approver of this proposition.")
    else:
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        cursor.execute(f"""SELECT COUNT(Name) FROM Store_Fame""")
        admin_count = cursor.fetchone()
        max_page = math.ceil(admin_count[0] / 20)
        current_page = 1
        low = 1 + ((current_page - 1) * 20)
        high = 20 + ((current_page - 1) * 20)
        cursor.execute(
            f"""SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"Fame Store Settings Page {current_page}",
                              description=f'This is a list of the administratively defined items',
                              colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f'**Name**: {result[2]}',
                            value=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}',
                            inline=False)
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction,
                                                                                 user: user.id == ctx.user.id and reaction.emoji in buttons,
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
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(
                        f"""SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}""")
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
async def cap(ctx: commands.Context, character_name: str, level_cap: int):
    """THIS COMMAND DISPLAYS CHARACTER INFORMATION"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    author = ctx.user.name
    guild_id = ctx.guild_id
    guild = ctx.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(
        f"""SELECT Character_Name FROM Player_Characters where Player_Name = ? and Character_Name = ? or  Player_Name = ? AND Nickname = ?""",
        (author, character_name, author, character_name))
    character_info = cursor.fetchone()
    if character_info is not None:
        await EventCommand.adjust_personal_cap(self, guild_id, author, character_name, level_cap)
        await ctx.response.send_message(f"{author} has adjusted the personal cap of {character_name} to {level_cap}.",
                                        ephemeral=True)
        cursor.execute(
            f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Player_Name = ? AND Character_Name = ? or Nickname = ?",
            (author, character_name, character_name))
        player_info = cursor.fetchone()
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
        accepted_bio_channel = cursor.fetchone()
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
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
        await ctx.response.send_message(
            f"{author} does not have a {character_name} registered under this character name or nickname.")
    cursor.close()
    db.close()


@character.command()
@app_commands.autocomplete(character_name=character_select_autocompletion)
async def display(ctx: commands.Context, player_name: typing.Optional[discord.Member], character_name: str = 'All',
                  current_page: int = 1):
    """THIS COMMAND DISPLAYS CHARACTER INFORMATION"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    if player_name is not None:
        player_name = player_name.name
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if player_name == 'NA':
        player_name = ctx.user.name
    if character_name == 'All':
        cursor.execute(f"""SELECT COUNT(Character_Name) FROM Player_Characters where Player_Name = '{player_name}'""")
        character_count = cursor.fetchone()
        if character_count is None:
            cursor.close()
            db.close()
            ctx.response.send_message(f"{player_name} was not a valid player to obtain the characters of!")
            return
        max_page = math.ceil(character_count[0] / 5)
        if current_page >= max_page:
            current_page = max_page
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        low = 0 + (5 * (current_page - 1))
        offset = 5
        cursor.execute(
            f"""Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Mythweavers from Player_characters WHERE player_name = '{player_name}' LIMIT {low}, {offset}""")
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
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction,
                                                                                 user: user.id == ctx.user.id and reaction.emoji in buttons,
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
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(
                        f"""Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Mythweavers from Player_characters WHERE player = '{player_name}' LIMIT {low}, {offset}""")
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
                    await ctx.response.send_message(embed=embed)
                    await msg.edit(embed=embed)
    elif character_name != 'All':
        sql = f"""Select True_Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Gold_Value, Oath, Fame, Prestige, Title, Article_Link from Player_characters WHERE Character_Name = ? or Nickname = ?"""
        val = (character_name, character_name)
        cursor.execute(sql, val)
        result = cursor.fetchone()
        if result is None:
            await ctx.response.send_message(f"{character_name} is not a valid Nickname or Character Name.")
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
            await ctx.response.send_message(embed=embed)
    cursor.close()
    db.close()


@character.command()
@app_commands.describe(
    level_range="the level range of the characters you are looking for. Keep in mind, this applies only to the preset low/med/high/max ranges your admin has set")
async def list(ctx: commands.Context, level_range: discord.Role, current_page: int = 1):
    """THIS COMMAND DISPLAYS CHARACTER INFORMATION"""
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Level FROM Level_Range WHERE Role_ID = {level_range.id} order by Level asc limit 1""")
    level_range_min = cursor.fetchone()
    cursor.execute(f"""SELECT Level FROM Level_Range WHERE Role_ID = {level_range.id} order by Level desc limit 1""")
    level_range_max = cursor.fetchone()
    if level_range_min is None:
        cursor.close()
        db.close()
        ctx.response.send_message(f"{level_range.name} was not a valid role to select", ephemeral=True)
        return
    cursor.execute(
        f"""SELECT COUNT(Character_Name) FROM Player_Characters where level >= {level_range_min[0]} and level <= {level_range_max[0]}""")
    character_count = cursor.fetchone()
    if character_count[0] != 0:
        max_page = math.ceil(character_count[0] / 5)
        if current_page >= max_page:
            current_page = max_page
        buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
        low = 0 + (5 * (current_page - 1))
        offset = 5
        cursor.execute(
            f"""Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link from Player_characters WHERE level >= {level_range_min[0]} and level <= {level_range_max[0]} LIMIT {low}, {offset}""")
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
        await ctx.response.send_message(embed=embed)
        msg = await ctx.original_response()
        for button in buttons:
            await msg.add_reaction(button)
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=lambda reaction,
                                                                                 user: user.id == ctx.user.id and reaction.emoji in buttons,
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
                    await msg.remove_reaction(button, ctx.user)
                if current_page != previous_page:
                    cursor.execute(
                        f"""Select True_Character_Name, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link from Player_characters WHERE level >= {level_range_min[0]} and level <= {level_range_max[0]} LIMIT {low}, {offset}""")
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
        await ctx.response.send_message(f"{level_range.name} does not have any characters within this level range.",
                                        ephemeral=True)


@character.command()
@app_commands.choices(
    modify=[discord.app_commands.Choice(name='Create', value=1), discord.app_commands.Choice(name='Edit', value=2)])
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def backstory(ctx: commands.Context, character_name: str, backstory: str,
                    modify: discord.app_commands.Choice[int] = 1):
    """THIS COMMAND CREATES OR CHANGES THE BACKSTORY ASSOCIATED WITH YOUR CHARACTER"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    author = ctx.user.name
    guild_id = ctx.guild_id
    guild = ctx.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(
        f"""SELECT Character_Name, Article_ID, Mythweavers FROM Player_Characters where Player_Name = ? and Character_Name = ? or  Player_Name = ? AND Nickname = ?""",
        (author, character_name, author, character_name))
    character_info = cursor.fetchone()
    if character_info is not None:
        if modify == 1:
            if character_info[1] is not None:
                await ctx.response.send_message(
                    f"{author} already has a backstory associated with {character_name}. If you wish to edit it, use the Edit Option of this command",
                    ephemeral=True)
            else:
                await EventCommand.create_bio(self, guild_id, character_info[0], backstory, character_info[2])
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
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
                await ctx.response.send_message(f"{author} has created a backstory for {character_name}.",
                                                ephemeral=True)
        else:
            if character_info[1] is None:
                await ctx.response.send_message(
                    f"{author} does not have a backstory associated with {character_name}. If you wish to create one, use the Create Option of this command",
                    ephemeral=True)
            else:
                await EventCommand.edit_bio(self, guild_id, character_info[0], backstory, character_info[1])
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
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
                await ctx.response.send_message(f"{author} has edited the backstory for {character_name}.",
                                                ephemeral=True)
    else:
        cursor.execute(
            f"""SELECT Character_Name FROM A_STG_Player_Characters where Player_Name = ? and Character_Name = ? or  Player_Name = ? AND Nickname = ?""",
            (author, character_name, author, character_name))
        character_info = cursor.fetchone()
        if character_info is not None:
            await EventCommand.edit_stage_bio(self, guild_id, character_info[0], backstory)
        else:
            await ctx.response.send_message(
                f"{author} does not have a {character_name} registered under this character name or nickname.",
                ephemeral=True)

    cursor.close()
    db.close()
