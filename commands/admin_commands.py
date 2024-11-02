from discord.ext import commands
from discord import app_commands
import discord


@commands.group()
async def admin(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"no {ctx.invoked_subcommand} exists")

@admin.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Admin Help", description=f'This is a list of Admin help commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Character Commands**', value=f'**/Character_Milestones**: Modifies the milestones associated with a character. \r\n' +
                    f'**/admin character_trials**: Modifies the trials associated with a character. \r\n' +
                    f'**/admin gold_adjust**: Modifies the gold that a character has. \r\n ' +
                    f'**/admin Flux_Adjust**: Modifies the flux that a character has. \r\n ' +
                    f'**/admin customize**: Apply a Tradition or Template for a character \r\n' +
                    f'**/admin manage**: Accept or reject a player registration attempt, or clean out historical ones. \r\n ' +
                    f'**/admin undo_transaction**: undo a player transaction',inline=False)
    embed.add_field(name=f'**Database Commands**', value=f'**/settings_display**: Display the various Administrative Defined Settings\r\n' +
                    f'**/admin settings_define**: Define an Administrative Setting.\r\n' +
                    f'**/admin level_cap**: Set a new level cap and set all player characters levels as appropriate.\r\n' +
                    f'**/admin Tier_cap**: Set a new tier cap and set all player characters levels as appropriate.\r\n' +
                    f'**/admin level_range**: Define a role and range for a level range.\r\n' +
                    f'**/admin reset_database**: Reset the Server Database to Defaults.\r\n' +
                    f'**/admin clean_playerbase**: Clean out a or all inactive player characters from player characters and gold history and session history.', inline=False)
    embed.add_field(name=f"**Utility Commands**", value=f'**/admin session_adjust**: alter the reward from a session.\r\n' +
                    f'**/admin ubb_inventory**: Display the inventory of a user in order to find information.', inline=False)
    embed.add_field(name=f"**Fame Commands**", value=f'**/admin fame_store**: Add, edit, or remove items from the fame store.\r\n' +
                    f'**/admin title_store**: Add, edit, or remove items from the title store.\r\n', inline=False)
    await ctx.response.send_message(embed=embed)


@admin.command(name="character_milestones", description="commands for adding or removing milestones")
@app_commands.autocomplete(character_name=character_select_autocompletion)
@app_commands.describe(job='What kind of job you are adding')
@app_commands.choices(job=[discord.app_commands.Choice(name='Easy', value=1), discord.app_commands.Choice(name='Medium', value=2), discord.app_commands.Choice(name='Hard', value=3), discord.app_commands.Choice(name='Deadly', value=4), discord.app_commands.Choice(name='None', value=5)])
@app_commands.describe(level="The character level for the adjustment: Default at 0 to use current level.")
async def character_milestones(ctx: commands.Context, character_name: str, amount: int, job: discord.app_commands.Choice[int], level: typing.Optional[int], misc_milestones: int = 0):
    """Adjusts the milestone number a PC has."""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    if job == 1:
        job = 1
    else:
        job = job.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if job == 1:
        job_name = 'Easy'
    elif job == 2:
        job_name = 'Medium'
    elif job == 3:
        job_name = 'Hard'
    elif job == 4:
        job_name = 'Deadly'
    else:
        job_name = 'None'
    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name,character_name))
    player_info = cursor.fetchone()
    if player_info is None:
        await ctx.response.send_message(f"{author} does not have {character_name} registered to their account.")
    if player_info is not None:
        if amount == 0 and misc_milestones == 0:
            await ctx.response.send_message("No Change in Milestones!", ephemeral=True)
        if job_name == 'None' and misc_milestones == 0:
            await ctx.response.send_message("No Change in Milestones!", ephemeral=True)

        else:
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
            max_level = cursor.fetchone()
            int_max_level = int(max_level[0])
            if player_info[29] is not None:
                int_max_level = player_info[29] if player_info[29] < int_max_level else int_max_level
            if job_name != 'None':
                character_level = player_info[7] if level is None else level
                cursor.execute(f"SELECT {job_name} from AA_Milestones where level = {character_level}")
                milestone_info = cursor.fetchone()
                milestone_total = (milestone_info[0] * amount) + misc_milestones + player_info[9]
                adjust_milestones = (milestone_info[0] * amount) + misc_milestones
            else:
                milestone_total = player_info[9] + misc_milestones
                adjust_milestones = misc_milestones
            cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
            current_level = cursor.fetchone()

            if current_level[0] < int_max_level:
                character_level = current_level[0]
                remaining = current_level[1] + current_level[2] - milestone_total
            else:
                character_level = int_max_level
                cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE level = '{character_level}'")
                current_level = cursor.fetchone()
                remaining = current_level[1] + current_level[2] - milestone_total
            if current_level is None:
                await ctx.response.send_message(f"Comrade, one cannot degrade this character: {character_name} past level 3, please train them to  best level up in the future!")
            else:
                await Event.adjust_milestones(self, character_name, milestone_total, remaining, character_level, guild_id, author)
                if character_level != player_info[1]:
                    cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = '{player_info[7]}'")
                    level_range = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Desc")
                    level_range_max = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Asc")
                    level_range_min = cursor.fetchone()
                    cursor.execute(f"Select True_Character_Name from Player_Characters WHERE Player_Name = '{player_info[0]}' AND level >= {level_range_min[0]} AND level <= {level_range_max[0]}")
                    level_range_characters = cursor.fetchone()
                    member = await guild.fetch_member(player_info[1])
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                    accepted_bio_channel = cursor.fetchone()
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                    character_log_channel_id = cursor.fetchone()
                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], character_level, player_info[8], milestone_total, remaining, player_info[11], player_info[12], player_info[13], player_info[14], player_info[16] , player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                    bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                    bio_message = await bio_channel.fetch_message(player_info[24])
                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                    source = f"admin adjusted milestones by {adjust_milestones} for {character_name}"
                    logging_embed = log_embed(player_info[2], author, character_level, adjust_milestones, milestone_total, remaining, None, None, None, None, None, None, None, None, None, None, None, None,None, None, None, None, None, None, None, source)
                    logging_thread = guild.get_thread(player_info[25])
                    await logging_thread.send(embed=logging_embed)
                    if level_range_characters is None:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {character_level}")
                        new_level_range = cursor.fetchone()
                        role1 = guild.get_role(level_range[2])
                        role2 = guild.get_role(new_level_range[2])
                        await member.remove_roles(role1)
                        await member.add_roles(role2)
                    else:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {character_level}")
                        new_level_range = cursor.fetchone()
                        role2 = guild.get_role(new_level_range[2])
                        await member.add_roles(role2)
                    await ctx.response.send_message(f"{ctx.user.name} has adjusted {character_name}'s milestones by {adjust_milestones}, they are now level {current_level[0]} and require {remaining} milestones to reach their next level up!")
                if player_info[1] == current_level[0]:
                    await ctx.response.send_message(f"{ctx.user.name} has adjusted {character_name}'s milestones by {adjust_milestones}, they require {remaining} milestones to level up!")
    cursor.close()
    db.close()


@admin.command(name="character_trials", description="commands for adding or removing trials")
@app_commands.autocomplete(character_name=character_select_autocompletion)
async def character_trials(ctx: commands.Context, character_name: str, amount: int):
    """Adjust the number of Mythic Trials a character possesses"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    guild = ctx.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name,character_name))
    player_info = cursor.fetchone()
    if amount == 0:
        await ctx.response.send_message(f"No changes to trial total required.")
    else:
        if player_info is None:
            await ctx.response.send_message(f"{ctx.user.name} does not have {character_name} registered to their account.")
        else:
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Cap'")
            max_tier = cursor.fetchone()
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
            break_point = cursor.fetchone()
            if player_info[7] <= int(break_point[0]):
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
                tier_rate_limit = cursor.fetchone()
            else:
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
                tier_rate_limit = cursor.fetchone()
            rate_limited_tier = floor(player_info[7] / int(tier_rate_limit[0]))
            tier_max = rate_limited_tier if rate_limited_tier <= max_tier[0] else max_tier[0]
            total_trials = player_info[11] + amount
            cursor.execute(f"SELECT Tier, Trials, Trials_Required FROM AA_Trials where Trials <= {total_trials} ORDER BY Trials Desc LIMIT 1")
            trial_info = cursor.fetchone()
            if trial_info is None:
                await ctx.response.send_message(f"{character_name} cannot be made any more menial! Please comrade, encourage them to elevate themselves in the future!")
            elif trial_info[0] <= tier_max or amount < 0:
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16] , player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"admin adjusted trials by {amount} for {character_name}"
                logging_embed = log_embed(player_info[2], author, None, None, None, None, trial_info[0], amount, total_trials, trial_info[1] + trial_info[2] - total_trials, None, None, None, None, None, None, None, None,None, None, None, None, None, None, None, source)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
                await Event.adjust_trials(self, character_name, total_trials, guild_id, author)
                if player_info[8] != trial_info[0]:
                    remaining = trial_info[1] + trial_info[2] - total_trials
                    await ctx.response.send_message(f"{ctx.user.name} has adjusted {character_name}'s trials by {amount}, reaching a tier of {trial_info[0]} with {remaining} trials to increase their tier.")
                if player_info[8] == trial_info[0]:
                    remaining = trial_info[1] + trial_info[2] - total_trials
                    await ctx.response.send_message(f"{ctx.user.name} has adjusted {character_name}'s trials by {amount} with {remaining} trials to increase their tier")
            else:
                await ctx.response.send_message(f"{character_name} is at the max tier cap for the server or his level!")
        cursor.close()
        db.close()


@admin.command()
@app_commands.autocomplete(character_name=character_select_autocompletion)
async def gold_adjust(ctx: commands.Context, character_name: str, amount: typing.Optional[float], effective_gold: typing.Optional[float], lifetime_gold: typing.Optional[float], reason: str):
    """Adjust the gold a PC has"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    reason = str.replace(reason, ";", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    author_id = ctx.user.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount is None and effective_gold is None and lifetime_gold is None:
        await ctx.response.send_message(f"BRUH, if you don't intend to change anything why change at all?", ephemeral=True)
    else:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR Nickname = ?",(character_name, character_name))
        player_info = cursor.fetchone()
        print(player_info[4])
        if player_info is None:
            await ctx.response.send_message(f"There is no character with the name or nickname of {character_name}.")
        else:
            amount = 0 if amount is None else amount
            gold_info = gold_calculation(player_info[7], player_info[6], player_info[13], player_info[14], player_info[15], amount)
            lifetime_gold_change = lifetime_gold if lifetime_gold is not None else amount
            effective_gold_change = effective_gold if effective_gold is not None else gold_info[3]
            await Event.gold_change(self, guild_id, author, author_id, player_info[3], gold_info[3], effective_gold_change, lifetime_gold_change, reason, 'Admin Gold Adjust')
            cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
            transaction_id = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + gold_info[3], player_info[14] + effective_gold_change, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"admin adjusted gold by {amount} for {character_name}"
            logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, player_info[13] + gold_info[3], gold_info[3], player_info[14] + effective_gold_change, transaction_id[0], None, None, None, None, None, None, None, None, None, None, None, source)
            logging_thread = guild.get_thread(player_info[25])
            await logging_thread.send(embed=logging_embed)
            embed = discord.Embed(title=f"Admin Gold Change", description=f'Gold Adjustment Transaction', colour=discord.Colour.blurple())
            embed.add_field(name=f'**Adjustments**', value=f'Gold change: {gold_info[3]}, Effective Gold Change: {effective_gold_change}, Lifetime Wealth Change: {lifetime_gold_change}', inline=False)
            embed.add_field(name=f"**Totals**", value=f"Gold Total: {player_info[13] + gold_info[3]}, Effective Gold Total: {player_info[14] + effective_gold_change}, Lifetime Wealth Total: {player_info[15] + lifetime_gold_change}", inline=False)
            embed.set_footer(text=f"Transaction ID: {transaction_id[0]}")
            await ctx.response.send_message(embed=embed, ephemeral=True)
    cursor.close()
    db.close()


@admin.command()
async def undo_transaction(ctx: commands.Context, transaction_id: int):
    """Undo a transaction performed by a PC"""
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    guild = ctx.guild
    author = ctx.user.name
    cursor.execute(f"Select Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_value_max FROM A_Audit_Gold WHERE Transaction_ID = {transaction_id}")
    transaction_info = cursor.fetchone()
    if transaction_info is not None:
        embed = discord.Embed(title=f"Undoing Transaction: {transaction_id}", description=f'Undoing a transaction', colour=discord.Colour.red())
        """Help commands for the associated tree"""
        mentions = f"The Below Transaction has been cancelled for {transaction_info[2]}, <@{transaction_info[1]}>"
        gold = transaction_info[3] * -1
        effective_gold = transaction_info[4] * -1
        max_effective_gold = transaction_info[5] * -1
        embed.add_field(name=f"**{transaction_info[2]}'s Transaction Info:**", value=f'**Gold:** {transaction_info[3]} GP, **Effective Gold**: {transaction_info[4]} GP, **Lifetime Gold**: {transaction_info[5]}.', inline=False)
        cursor.execute(f"Select Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_value_max, Transaction_ID FROM A_Audit_Gold WHERE Related_Transaction_ID = {transaction_id}")
        related_transaction_info = cursor.fetchone()
        await Event.undo_transaction(self, guild_id, transaction_id, gold, effective_gold, max_effective_gold, transaction_info[2], transaction_info[0])
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
        accepted_bio_channel = cursor.fetchone()
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
        character_log_channel_id = cursor.fetchone()
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?",(transaction_info[2],))
        player_info = cursor.fetchone()
        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
        bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13] + gold, player_info[14] + effective_gold, player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
        bio_message = await bio_channel.fetch_message(player_info[24])
        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
        source = f"admin undid transaction {transaction_id}"
        logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, player_info[13] + gold, gold, player_info[14] + effective_gold, transaction_id, None, None, None, None, None, None, None, None, None, None, None, source)
        logging_thread = guild.get_thread(player_info[25])
        await logging_thread.send(embed=logging_embed)
        if related_transaction_info is not None:
            mentions = f"and for {transaction_info[2]}, <@{transaction_info[1]}>!"
            """Help commands for the associated tree"""
            gold = related_transaction_info[3] * -1
            effective_gold = related_transaction_info[4] * -1
            max_effective_gold = related_transaction_info[5] * -1
            cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?",(related_transaction_info[2],))
            player_info = cursor.fetchone()
            embed.add_field(name=f"**{related_transaction_info[2]}'s Transaction Info:**", value=f'**Gold:** {related_transaction_info[3]} GP, **Effective Gold**: {related_transaction_info[4]} GP, **Lifetime Gold**: {related_transaction_info[5]}.', inline=False)
            await Event.undo_transaction(self, guild_id, related_transaction_info[6], gold, effective_gold, max_effective_gold, related_transaction_info[0], related_transaction_info[2])
            bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11],player_info[12], player_info[13] + gold, player_info[14] + effective_gold,player_info[16], player_info[17], player_info[18], player_info[19],player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"admin undid transaction {transaction_id}"
            logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None,player_info[13] + gold, gold, player_info[14] + effective_gold, transaction_id,None, None, None, None, None, None, None, None, None, None, None, source)
            logging_thread = guild.get_thread(player_info[25])
            await logging_thread.send(embed=logging_embed)
    else:
        mentions = f"This Transaction was not a valid transaction to undo!!"
        embed = discord.Embed(title=f"Command Failed! Undo Transaction: {transaction_id}", description=f'This Command Failed', colour=discord.Colour.red())
    await ctx.response.send_message(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
    cursor.close()
    db.close()


@admin.command()
async def session_management(interaction: discord.Interaction, session_id: int, gold: typing.Optional[int], easy: typing.Optional[int], medium: typing.Optional[int], hard: typing.Optional[int], deadly: typing.Optional[int], flux: typing.Optional[int], trials: typing.Optional[int], reward_all: typing.Optional[str], party_reward: typing.Optional[str], fame: typing.Optional[int], prestige: typing.Optional[int]):
    """Update Session Information and alter the rewards received by the players"""
    guild_id = interaction.guild_id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT GM_Name, Session_Name, Play_Time, Session_Range, Gold, Flux, Easy, Medium, Hard, Deadly, Trials, Alt_Reward_All, Alt_Reward_Party, Session_Thread, Message, Rewards_Message, Rewards_Thread, Fame, Prestige FROM Sessions WHERE Session_ID = {session_id} and IsActive = 0 LIMIT 1""")
    session_simple = cursor.fetchone()
    cursor.execute(f"""SELECT Player_Name, Character_Name, Level, Received_Milestones, Effective_Gold, Received_Gold, Player_ID, Received_Fame, Forego, Received_Prestige FROM Sessions_Archive WHERE Session_ID = {session_id}""")
    session_complex = cursor.fetchall()
    if session_simple is None:
        await interaction.response.send_message(f'invalid session ID of {session_id}')
    else:
        if gold is not None and gold < 0 or easy is not None and easy < 0 or medium is not None and medium < 0 or hard is not None and hard < 0 or deadly is not None and deadly < 0 or flux is not None and flux < 0 or trials is not None and trials < 0:
            await interaction.response.send_message(f"Minimum Session Rewards may only be 0, if a player receives a lesser reward, have them claim the transaction.")
        elif gold is None and easy is None and medium is None and hard is None and deadly is None and flux is None and trials is None and fame is None and reward_all is None and party_reward is None:
            embed = discord.Embed(title="Session Report", description=f"a report of the session: {session_simple[1]}", color=discord.Color.blue())
            embed.set_author(name=f'{session_simple[0]}')
            embed.add_field(name="Session Info", value=f'**GM:** {session_simple[0]} \n **Level Range**: {session_simple[3]}, **Gold**: {session_simple[4]}, **Trials**: {session_simple[10]}, **Fame**: {session_simple[17]} **Flux**:{session_simple[5]}', inline=False)
            embed.add_field(name="Job Info", value=f'**Easy**: {session_simple[6]}, **Medium**:{session_simple[7]}, **Hard**: {session_simple[8]}, **Deadly**: {session_simple[9]}', inline=False)
            for player in session_complex:
                embed.add_field(name="Character Info", value=f'Player: {player[0]} Character:{player[1]} \r\n **Level**: {player[2]} \r\n **Milestones Received**: {player[3]} **Gold Received**: {player[5]} \r\n ***Fame Received***: {player[[7]]}', inline=False)
            embed.set_footer(text=f'Session occurred on: {session_simple[2]}.')
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.defer(thinking=True)
            gold = session_simple[4] if gold is None else gold
            flux = session_simple[5] if flux is None else flux
            easy = session_simple[6] if easy is None else easy
            medium = session_simple[7] if medium is None else medium
            hard = session_simple[8] if hard is None else hard
            deadly = session_simple[9] if deadly is None else deadly
            trials = session_simple[10] if trials is None else trials
            reward_all = session_simple[11] if reward_all is None else reward_all
            fame = session_simple[17] if fame is None else fame
            prestige = session_simple[18] if prestige is None else prestige
            embed = discord.Embed(title="Session Report", description=f"a report of the session: {session_simple[1]}", color=discord.Color.blue())
            embed.set_author(name=f'{session_simple[0]}')
            embed.add_field(name="Session Info", value=f'**GM:** {session_simple[0]} \n **Level Range**: {session_simple[3]}, **Gold**: {gold}, **Trials**: {trials}, **Fame**: {fame}, **Flux**:{flux}', inline=False)
            embed.add_field(name="Job Info", value=f'**Easy**: {easy}, **Medium**:{medium}, **Hard**: {hard}, **Deadly**: {deadly}', inline=False)
            x = 0
            if party_reward is not None:
                party_reward_embed = discord.Embed(title="Party Reward", description=f"Party Reward for {session_simple[1]}", color=discord.Color.blue())
                party_reward_embed.set_author(name=f'{session_simple[0]}')
                party_reward_embed.add_field(name="Reward Info", value=f'{party_reward}', inline=False)
                if session_simple[16] is None:
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
                    rewards_channel = cursor.fetchone()
                    reward_channel = await bot.fetch_channel(rewards_channel[0])
                    reward_msg = await reward_channel.fetch_message(session_simple[16])
                    reward_thread = await reward_msg.create_thread(name=f"Session name: {session_name} Party Rewards, Session ID: {info[0]}", auto_archive_duration=60, reason=f"{description}")
                    reward_thread_id = reward_thread.id
                    reward_message_id = reward_msg.id
                    await reward_thread.send(embed=party_reward_embed)
                else:
                    thread = guild.get_thread(session_simple[16])
                    await thread.send(embed=party_reward_embed)
                    reward_message_id = session_simple[15]
                    reward_thread_id = session_simple[16]
            else:
                reward_message_id = session_simple[15]
                reward_thread_id = session_simple[16]
            for player in session_complex:
                x += 1
                cursor.execute(f"""SELECT Easy, Medium, Hard, Deadly from AA_Milestones WHERE level = {player[2]}""")
                job_info = cursor.fetchone()
                easy_jobs = (easy - session_simple[6]) * job_info[0]
                medium_jobs = (medium - session_simple[7]) * job_info[1]
                hard_jobs = (hard - session_simple[8]) * job_info[2]
                deadly_jobs = (deadly - session_simple[9]) * job_info[3]
                if player[8] == 2:
                    rewarded = 0
                else:
                    rewarded = easy_jobs + medium_jobs + hard_jobs + deadly_jobs
                new_milestones = player[3] + rewarded
                # SETTING WHAT THE LEVEL WILL BE.
                cursor.execute(f"SELECT Milestones, Tier, Trials, Gold, Gold_Value, Gold_Value_Max, Flux, Oath FROM Player_Characters WHERE Character_Name = ?", (player[1],))
                current_info = cursor.fetchone()
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?",(player[1],))
                player_info = cursor.fetchone()
                new_milestone_total = player_info[9] + rewarded
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
                max_level = cursor.fetchone()
                int_max_level = int(max_level[0])
                cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{new_milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
                current_level = cursor.fetchone()
                if int_max_level < current_level[0]:
                    int_max_level = player_info[29] if player_info[29] is not None and  int_max_level > player_info[29] else int_max_level
                    cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Level = {int_max_level} ORDER BY Minimum_Milestones DESC  LIMIT 1")
                    current_level = cursor.fetchone()
                    true_level = int(max_level[0])
                else:
                    cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_to_level from AA_Milestones  WHERE Minimum_Milestones <= '{new_milestone_total}' ORDER BY Minimum_Milestones DESC  LIMIT 1")
                    current_level = cursor.fetchone()
                    true_level = current_level[0]
                remaining = current_level[1] + current_level[2] - new_milestone_total
                if true_level != player[2]:
                    cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {player[2]}")
                    level_range = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Desc")
                    level_range_max = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Asc")
                    level_range_min = cursor.fetchone()
                    cursor.execute(f"Select True_Character_Name from Player_Characters WHERE Player_Name = '{player[0]}' AND level >= {level_range_min[0]} AND level <= {level_range_max[0]}")
                    level_range_characters = cursor.fetchone()
                    member = await guild.fetch_member(player_info[1])
                    if level_range_characters is None:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {true_level}")
                        new_level_range = cursor.fetchone()
                        role1 = guild.get_role(level_range[2])
                        role2 = guild.get_role(new_level_range[2])
                        await member.remove_roles(role1)
                        await member.add_roles(role2)
                    else:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {true_level}")
                        new_level_range = cursor.fetchone()
                        role2 = guild.get_role(new_level_range[2])
                        await member.add_roles(role2)
#                    DONE SETTING THE LEVEL
#                    SETTING THE MYTHIC TIER, REQUIRES LEVEL TO BE SET BEFOREHAND.
                trials_total = player_info[11] + trials - session_simple[10]
                cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Trials <= {trials_total} ORDER BY Trials DESC  LIMIT 1")
                current_mythic_information = cursor.fetchone()
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Cap'")
                max_tier = cursor.fetchone()
                cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
                break_point = cursor.fetchone()
                if true_level <= int(break_point[0]):
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
                    tier_rate_limit = cursor.fetchone()
                else:
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
                    tier_rate_limit = cursor.fetchone()
                rate_limited_tier = floor(true_level / int(tier_rate_limit[0]))
                true_tier = int(max_tier[0]) if current_mythic_information[0] > int(max_tier[0]) else current_mythic_information[0]
                true_tier = true_tier if true_tier <= rate_limited_tier else rate_limited_tier
                if true_tier == rate_limited_tier or true_tier == max_tier:
                    cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Tier = {true_tier} LIMIT 1")
                    current_mythic_information = cursor.fetchone()
                    trials_required = current_mythic_information[1] + current_mythic_information[2] - trials_total
                else:
                    trials_required = current_mythic_information[1] + current_mythic_information[2] - trials_total
#                   Done Creating the Tier Variables
                flux_total = player_info[16] + (flux - session_simple[5])
                fame_total = player_info[27] + fame - player[7]
                prestige_total = player_info[30] + prestige - player[9]
#                CREATING THE GOLD VARIABLES (REQUIRES LEVEL TO BE ALREADY SET)
                if player[8] == 3:
                    difference = 0
                    gold_difference = 0
                    effective_gold_total = player_info[14]
                    gold = 0
                else:
                    gold_difference = gold - session_simple[4]
                    effective_gold_total = player_info[14] + gold_difference
                    if current_info[6] == 'Offerings':
                        difference = gold_difference * .5
                    elif current_info[6] == 'Poverty':
                        max_gold = 80 * true_level * true_level
                        if current_info[4] > max_gold:
                            difference = 0
                        elif effective_gold_total > max_gold:
                            difference = effective_gold_total - max_gold
                            effective_gold_total -= difference
                        else:
                            difference = gold_difference
                    elif current_info[7] == 'Absolute':
                        max_gold = true_level * 5
                        if current_info[4] > max_gold:
                            difference = 0
                        elif effective_gold_total > max_gold:
                            difference = effective_gold_total - max_gold
                            effective_gold_total -= difference
                        else:
                            difference = gold_difference
                    else:
                        difference = gold_difference
#                    DONE WITH GOLD
                difference = round(difference, 2)
                await Event.session_rewards(self, player[0], guild_id, player[1], true_level, new_milestone_total, remaining, flux_total, true_tier, trials_total, trials_required, fame_total, prestige_total, f"Adjusting Session {session_id} reward")
                await Event.gold_change(self, guild_id, player[0], player[6], player[1], difference, difference, gold, 'Session Reward', 'Session Reward')
                await Event.update_session_log_player(self, guild_id, session_id, player[1], rewarded, trials, difference, fame, prestige)
                embed.add_field(name="Character Info", value=f'Player: {player[0]} Character:{player[1]} \n **Level**: {true_level} \n **Milestone change**: {rewarded} **Gold change**: {difference}', inline=False)
                cursor.execute(f'SELECT MAX(Transaction_ID) FROM A_Audit_Gold Order By Transaction_ID DESC LIMIT 1')
                transaction_id = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
                accepted_bio_channel = cursor.fetchone()
                cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                character_log_channel_id = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], true_level, true_tier, new_milestone_total, remaining, trials_total, trials_required, player_info[13] + difference, player_info[14] + difference, flux_total, player_info[17], player_info[18], player_info[19], player_info[20], player_info[21],player_info[22], player_info[23], player_info[27], fame_total, prestige_total, player_info[31])
                bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"admin adjusted session {session_id}"
                logging_embed = log_embed(player_info[2], player_info[2], true_level, rewarded, new_milestone_total, remaining, true_tier, trials - session_simple[10], trials_total, trials_required, player_info[13] + difference, difference, player_info[14] + difference, transaction_id[0], flux_total, flux - session_simple[5], None, None, None, None, reward_all, fame_total, fame, prestige_total, prestige, source)
                logging_thread = guild.get_thread(player_info[25])
                await logging_thread.send(embed=logging_embed)
            await Event.update_session_log(self, guild_id, session_id, gold, flux, easy, medium, hard, deadly, trials, reward_all, party_reward, reward_message_id, reward_thread_id, fame, prestige)
            await interaction.followup.send(embed=embed)
            cursor.close()
            db.close()


@admin.command()
async def ubb_inventory(interaction: discord.Interaction, player: discord.Member):
    """Display a player's inventory to identify their owned items and set the serverside items for pouches, milestones, and other"""
    guild_id = interaction.guild_id
    client = Client(os.getenv('UBB_TOKEN'))
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    shop = await client.get_inventory_items_all(guild_id, player.id)  # get the inventory
    if shop is not None:
        embed = discord.Embed(title=f"UBB Inventory", description=f'UBB inventory', colour=discord.Colour.blurple())
        embed.add_field(name=f'**new item**', value=f'{shop}', inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"This player does not have any items in their inventory.")
    cursor.close()
    db.close()
    await client.close()


@admin.command()
async def settings_display(ctx: commands.Context, current_page: int = 1):
    """Serverside Settings detailed view"""
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    cursor.execute(f"""SELECT COUNT(Identifier) FROM Admin""")
    admin_count = cursor.fetchone()
    max_page = math.ceil(admin_count[0] / 20)
    if current_page >= max_page:
        current_page = max_page
    low = 1 + ((current_page-1) * 20)
    high = 20 + ((current_page-1) * 20)
    cursor.execute(f"""SELECT Search, Type, Identifier, Description from Admin WHERE ROWID BETWEEN {low} and {high}""")
    pull = cursor.fetchall()
    embed = discord.Embed(title=f"Admin Settings Page {current_page}", description=f'This is a list of the administrative defined settings', colour=discord.Colour.blurple())
    for result in pull:
        embed.add_field(name=f'Identifier: {result[2]}', value=f'**Search Key**: {result[0]}, **Data Type**: {result[1]}, \n **Description**:{result[3]}', inline=False)
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
                cursor.execute(f"""SELECT Search, Type, Identifier, Description from Admin WHERE ROWID BETWEEN {low} and {high}""")
                pull = cursor.fetchall()
                embed = discord.Embed(title=f"Admin Settings Page {current_page}", description=f'This is a list of the administrative defined settings', colour=discord.Colour.blurple())
                for result in pull:
                    embed.add_field(name=f'Search key: {result[2]}', value=f'**Identifier**: {result[0]}, **Type**: {result[1]}, \n **Description**:{result[3]}', inline=False)
                await msg.edit(embed=embed)


@admin.command()
@app_commands.describe(new_search='Enter the corresponding search-key for the Identifier')
@app_commands.describe(identifier='Key phrase to be updated')
async def settings_define(interaction: discord.Interaction, identifier: str, new_search: str):
    """This allows the admin to adjust a serverside setting"""
    guild_id = interaction.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = interaction.user.name
    if new_search is None:
        await interaction.response.send_message(f"cannot replace a search key with None")
    elif identifier is None:
        await interaction.response.send_message(f"Yeah... that would break shit, no.")
    else:
        cursor.execute(f"""SELECT Search, Type, Identifier, Description FROM Admin where Identifier = '{identifier}'""")
        information = cursor.fetchone()
        if information is None:
            await interaction.response.send_message('The identifier you have supplied is incorrect.')
        if information is not None:
            await Event.update_settings(self, guild_id, author, new_search, identifier)
            await interaction.response.send_message(f'The identifier of {identifier} is now looking for {new_search}.')
    cursor.close()
    db.close()


@admin.command()
async def level_cap(interaction: discord.Interaction, new_level: int):
    """This allows the admin to adjust the server wide level cap"""
    guild_id = interaction.guild_id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = interaction.user.name
    if new_level < 3:
        await interaction.response.send_message(f"Your server does not have a milestone system for below level 3")
    if new_level > 20:
        await interaction.response.send_message(f"Your server does not have a milestone system for above level 20")
    else:
        await interaction.response.defer(thinking=True)
        await Event.update_level_cap(self, guild_id, author, new_level)
        cursor.execute(f"SELECT Minimum_Milestones FROM AA_Milestones where Level = {new_level}")
        level_info = cursor.fetchone()
        minimum_milestones = level_info[0]
        cursor.execute(f"SELECT COUNT(Character_Name) FROM Player_Characters WHERE Milestones >= {minimum_milestones}")
        count_of_characters = cursor.fetchone()
        cursor.execute(f"SELECT Player_Name, Player_ID, Character_Name, Level, Personal_Cap FROM Player_Characters WHERE Milestones >= {minimum_milestones} LIMIT 20")
        characters_info = cursor.fetchall()
        embed = discord.Embed(title=f"New Level Cap", description=f'The Server level cap has been adjusted', colour=discord.Colour.blurple())
        if count_of_characters is not None:
            x = 0
            character_count = count_of_characters[0]
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            for characters in characters_info:
                personal_cap = 20 if characters[4] is None else characters[4]
                if personal_cap >= new_level:
                    x += 1
                    cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {characters[3]}")
                    level_range = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Desc")
                    level_range_max = cursor.fetchone()
                    cursor.execute(f"SELECT Level from LEVEL_Range WHERE Role_ID = {level_range[2]} Order by Level Asc")
                    level_range_min = cursor.fetchone()
                    cursor.execute(f"Select True_Character_Name from Player_Characters WHERE Player_Name = '{characters[2]}' AND level >= {level_range_min[0]} AND level <= {level_range_max[0]}")
                    level_range_characters = cursor.fetchone()
                    member = await guild.fetch_member(characters[1])
                    cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
                    character_log_channel_id = cursor.fetchone()
                    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?", (characters[2],))
                    player_info = cursor.fetchone()
                    bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], new_level, player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21],player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                    bio_message = await bio_channel.fetch_message(player_info[24])
                    await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                    source = f"admin adjusted adjusted level cap to {new_level}"
                    logging_embed = log_embed(player_info[2], author, new_level, 0, player_info[9], player_info[10], player_info[8], 0, player_info[11], player_info[12], None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, source)
                    logging_thread = guild.get_thread(player_info[25])
                    logging_thread_mention = f"<@{player_info[1]}>"
                    await logging_thread.send(embed=logging_embed, content=logging_thread_mention, allowed_mentions=discord.AllowedMentions(users=True))
                    if level_range_characters is None:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {new_level}")
                        new_level_range = cursor.fetchone()
                        role1 = guild.get_role(level_range[2])
                        role2 = guild.get_role(new_level_range[2])
                        await member.remove_roles(role1)
                        await member.add_roles(role2)
                    else:
                        cursor.execute(f"SELECT Level, Role_name, Role_ID FROM Level_Range WHERE level = {new_level}")
                        new_level_range = cursor.fetchone()
                        role2 = guild.get_role(new_level_range[2])
                        await member.add_roles(role2)
                    if x <= 20:
                        embed.add_field(name=f"**{characters[2]}**", value=f"<@{characters[1]}>'s character {characters[2]} has been leveled up to {new_level}.", inline=False)
                if character_count <= 20:
                    if character_count == 0:
                        embed.set_footer(text="There were no characters to be adjusted.")
                    else:
                        embed.set_footer(text="Are all the characters who have been adjusted to a new level.")
            else:
                character_count -= 20
                embed.set_footer(text=f"And {character_count[0]} more have obtained a new level")
        if count_of_characters is None:
            embed.add_field(name=f"**No Characters Changed:**", value=f"The server cap is now {new_level} but no characters meet the minimum milestones.", inline=False)
        await interaction.followup.send(embed=embed)
    cursor.close()
    db.close()


@admin.command()
async def tier_cap(interaction: discord.Interaction, new_tier: int):
    """This allows the admin to adjust the max serverside tier"""
    guild_id = interaction.guild_id
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = interaction.user.name
    await interaction.response.defer(thinking=True, ephemeral=True)
    if new_tier < 1:
        await interaction.followup.send(f"Negative Mythic Tiers? More like... Negative Brain Cells AMIRITE? {new_tier} is not valid")
    elif new_tier > 10:
        await interaction.followup.send(f"Just make them gods already damnit?! {new_tier} is too high!")
    else:
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
        break_point = cursor.fetchone()
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
        tier_rate_limit = cursor.fetchone()
        minimum_level = new_tier * int(tier_rate_limit[0])
        if int(minimum_level) <= int(break_point[0]):
            minimum_level = minimum_level
        else:
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
            tier_rate_limit = cursor.fetchone()
            minimum_level = new_tier * int(tier_rate_limit[0])
        cursor.execute(f"SELECT Trials FROM AA_Trials where Tier = {new_tier}")
        level_info = cursor.fetchone()
        minimum_milestones = level_info[0]
        cursor.execute(f"SELECT COUNT(Character_Name) FROM Player_Characters Trials WHERE level >= {minimum_milestones} and level >= {minimum_level}")
        count_of_characters = cursor.fetchone()
        cursor.execute(f"SELECT Player_Name, Player_ID, Character_Name FROM Player_Characters WHERE Trials >= {minimum_milestones} LIMIT 20")
        characters_info = cursor.fetchall()
        await Event.update_tier_cap(self, guild_id, author, new_tier, minimum_level)
        embed = discord.Embed(title=f"New Trial Cap", description=f'The Server Trial cap has been adjusted', colour=discord.Colour.blurple())
        if count_of_characters is not None:
            x = 0
            character_count = count_of_characters[0]
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            for characters in characters_info:
                x += 1
                embed.add_field(name=f"**{characters[2]}**", value=f"<@{characters[1]}>'s character {characters[2]} has attained a new tier of {new_tier}.", inline=False)
                cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?",(characters[2],))
                player_info = cursor.fetchone()
                bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16], player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
                bio_message = await bio_channel.fetch_message(player_info[24])
                await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
                source = f"admin adjusted adjusted tier cap to {new_tier}"
                logging_embed = log_embed(player_info[2], author, None, None, None,None, new_tier, 0, player_info[11], player_info[12], None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, source)
                logging_thread = guild.get_thread(player_info[25])
                try:
                    await logging_thread.send(embed=logging_embed)
                except:
                    pass
            if character_count <= 20:
                embed.set_footer(text=f"Are all the characters who have been adjusted to a new new_tier.")
            else:
                character_count -= 20
                embed.set_footer(text="And {character_count[0]} more have obtained a new tier")
        if count_of_characters is None:
            embed.add_field(name=f"**No Characters Changed:**", value=f"The server cap is now {new_tier} but no characters meet the minimum milestones.", inline=False)
        await interaction.followup.send(embed=embed)
    cursor.close()
    db.close()


@admin.command()
@app_commands.autocomplete(character_name=character_select_autocompletion)
async def flux_adjust(ctx: commands.Context, character_name: str, amount: int):
    """Adjust the flux a PC has"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if amount == 0:
        ctx.response.send_message(f"BRUH, 0 flux change? SRSLY?")
    elif amount != 0:
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ? OR Nickname = ?", (character_name, character_name))
        player_info = cursor.fetchone()
        if player_info is None:
            await ctx.response.send_message(f"There is no character named {character_name} that can be found by their name or nickname")
        elif player_info is not None:
            true_name = player_info[2]
            new_flux = player_info[16] + amount
            await Event.flux(self, guild_id, true_name, amount, new_flux, author)
            response = f"{character_name}'s Flux has changed by {amount} to become {new_flux}."
            await ctx.response.send_message(response, ephemeral=True)
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16] + amount, player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
            bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
            bio_message = await bio_channel.fetch_message(player_info[24])
            await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
            source = f"admin adjusted gold by {amount} for {character_name}"
            logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, None, None, None, None, new_flux, amount, None, None, None, None, None, None, None, None, None, source)
            logging_thread = guild.get_thread(player_info[25])
            await logging_thread.send(embed=logging_embed)
    cursor.close()
    db.close()


@admin.command()
async def level_range(ctx: commands.Context, range: discord.Role, minimum_level: int, maximum_level: int):
    """Adjust the role associated with a level range in the server"""
    if maximum_level < minimum_level:
        await ctx.response.send_message("Your Minimum Level Exceeded your maximum level!", ephemeral=True)
    elif maximum_level < 3 or maximum_level > 20:
        await ctx.response.send_message(f"Your maximum level of {maximum_level} is either below 3 or above 20!", ephemeral=True)
    elif minimum_level < 3 or minimum_level > 20:
        await ctx.response.send_message(f"Your minimum level of {minimum_level} is either below 3 or above 20!", ephemeral=True)
    else:
        guild_id = ctx.guild_id
        author = ctx.user.name
        role_name = range.name
        role_id = range.id
        await Event.set_range(self, guild_id, author, role_name, role_id, minimum_level, maximum_level)
        embed = discord.Embed(title=f"Range Update", description=f'a new role name and role ID has been applied', colour=discord.Colour.green())
        embed.add_field(name=f'**Role**', value=f'{role_name} with ID: {role_id}.', inline=False)
        embed.add_field(name=f'**Range**', value=f'{minimum_level} level to {maximum_level} level have been updated', inline=False)
        await ctx.response.send_message(embed=embed)


@admin.command()
@app_commands.describe(certainty="is life short?")
@app_commands.choices(certainty=[discord.app_commands.Choice(name='YOLO', value=1), discord.app_commands.Choice(name='No', value=2)])
async def reset_database(ctx: commands.Context, certainty: discord.app_commands.Choice[int]):
    """Perform a database reset, remember to reassign role ranges and server settings!"""
    if certainty == 1:
        certainty = 1
    else:
        certainty = certainty.value
    if certainty.value == 1:
        guild_id = ctx.guild_id
        buttons = ["✅", "❌"]  # checkmark X symbol
        embed = discord.Embed(title=f"Are you sure you want to reset the server database??", description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
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
                    embed = discord.Embed(title=f"Database Reset has occurred!", description=f"Say Farewell to a world you used to know.", colour=discord.Colour.red())
                    await msg.clear_reactions()
                    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    shutil.copyfile(f"C:/pathparser/pathparser_{guild_id}.sqlite", f"C:/pathparser/pathparser_{guild_id}_{time}.sqlite")
                    shutil.copyfile(f"C:/pathparser/pathparser.sqlite", f"C:/pathparser/pathparser_{guild_id}.sqlite")
                    await msg.edit(embed=embed)
    else:
        await ctx.response.send_message(f"I'M FIRING MY LAS--- What?")


@admin.command()
@app_commands.describe(player_wipe="if yes, remove all inactive players!")
@app_commands.choices(player_wipe=[discord.app_commands.Choice(name='No!', value=1), discord.app_commands.Choice(name='Yes!', value=2)])
async def clean_playerbase(ctx: commands.Context, player: typing.Optional[discord.Member], player_id: typing.Optional[int], player_wipe: discord.app_commands.Choice[int] = 1):
    """Clean out the entire playerbase or clean out a specific player's character by mentioning them or using their role!"""
    if player_wipe == 1:
        player_wipe = 1
    else:
        player_wipe = player_wipe.value
    if player_wipe == 1 and player_id is None and player is None:
        await ctx.response.send_message(f"Pick Something that lets me end someone! Please?", ephemeral=True)
    else:
        guild_id = ctx.guild_id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = ctx.user.name
        overall_wipe_list = []
        embed = discord.Embed(title=f"The Following Players will have their characters removed:",
                              description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
        if player_id is not None:
            cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from Player_Characters where Player_ID = {player_id}")
            player_id_info = cursor.fetchone()
            if player_id_info is not None:
                overall_wipe_list.append(player_id)
                embed.add_field(name=f"{player_id_info[0]}'s characters will be removed", value=f"this player had {player_id_info[1]} characters!")
            else:
                embed.add_field(name=f"{player_id} could not be found in the database.", value=f"This ID had no characters associated with it..")
        if player is not None:
            cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from Player_Characters where Player_ID = {player.id}")
            player_id_info = cursor.fetchone()
            if player_id_info is not None:
                embed.add_field(name=f"{player_id_info}'s characters will be removed", value=f"This player had {player_id_info[2]} characters who will be removed.")
                overall_wipe_list.append(player.id)
            else:
                embed.add_field(name=f"{player.name} could not be found in the database.", value=f"This user had no characters associated with it..")
        if player_wipe == 2:
            guild = ctx.guild
            cursor.execute(f"Select distinct(Player_ID), count(Character_Name) from Player_Characters")
            player_id_info = cursor.fetchall()
            wipe_tuple = None
            x = 0
            for inactive_player in player_id_info:
                member = guild.get_member(inactive_player[0])
                if member is None:
                    x += 1
                    overall_wipe_list.append(inactive_player[0])
                    if x <= 20:
                        embed.add_field(name=f"{player_id_info[0]}'s characters will be removed", value=f"this player had {player_id_info[1]} characters!")
                else:
                    x = x
                    wipe_tuple = wipe_tuple
            embed.set_footer(text=f"{x} Total Players were inactive and are being removed!")
        else:
            embed.add_field(name=f"No Player Characters could be found in the database.", value=f"This ID had no characters associated with it..")
        guild_id = ctx.guild_id
        buttons = ["✅", "❌"]  # checkmark X symbol
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
                if reaction.emoji == u"\u264C":
                    embed = discord.Embed(title=f"You have thought better of freely giving your money", description=f"Savings!", colour=discord.Colour.blurple())
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                if reaction.emoji == u"\u2705":
                    embed = discord.Embed(title=f"Database Reset has occurred!", description=f"Say Farewell to a world you used to know.", colour=discord.Colour.red())
                    await msg.clear_reactions()
                    await msg.edit(embed=embed)
                    for wiped in overall_wipe_list:
                        await Event.wipe_unapproved(self, wiped[0], guild_id, author)



@admin.command()
@app_commands.autocomplete(character_name=stg_character_select_autocompletion)
@app_commands.describe(cleanse="Optional: supply a number ending with D or W to remove users who have not been accepted within that period!")
@app_commands.describe(status="Accepted players are moved into active and posted underneath!")
@app_commands.choices(status=[discord.app_commands.Choice(name='Accepted!', value=1), discord.app_commands.Choice(name='Rejected!', value=2)])
async def manage(ctx: commands.Context, character_name: str, player_id: typing.Optional[int], status: discord.app_commands.Choice[int] = 1, cleanse: str = None):
    """accept a player into your accepted bios, or clean out the stage tables!"""
    guild = ctx.guild
    guild_id = ctx.guild_id
    if status == 1:
        status = 1
    else:
        status = status.value
    if character_name is None and cleanse is None:
        await ctx.response.send_message(f"NOTHING COMPLETED, RUN DURATION: 1 BAJILLION Eternities?", ephemeral=True)
    elif cleanse is not None or character_name is not None and status == 2 or player_id is not None and status == 2:
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = ctx.user.name
        if status == 2:
            overall_wipe_list = []
            character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
            embed = discord.Embed(title=f"The Following Players will have their staged characters removed:",
                                  description=f"hit the checkmark to confirm", colour=discord.Colour.blurple())
            if character_name is not None:
                cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where character_name = ?", (character_name,))
                player_id_info = cursor.fetchone()
                if player_id_info is not None:
                    overall_wipe_list.append(character_name)
                    embed.add_field(name=f"{player_id_info[0]}'s character will be removed from stage", value=f"The character of {character_name} will be removed!")
                else:
                    embed.add_field(name=f"{character_name} could not be found in the database.", value=f"This character name had no characters associated with it.")
            if cleanse is not None:
                if cleanse.endswith('D'):
                    cleanse = cleanse.replace('D', '')
                    cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where Created_Date <= date('now', '-{cleanse} days')")
                    player_id_info = cursor.fetchall()
                    x = 0
                    for inactive_player in player_id_info:
                        x += 1
                        overall_wipe_list.append(inactive_player[0])
                        if x <= 20:
                            embed.add_field(name=f"{player_id_info[0]}'s characters will be removed", value=f"this player had {player_id_info[1]} characters!")
                    embed.set_footer(text=f"{x} Total Players were inactive and are being removed!")
                elif cleanse.endswith('W'):
                    cleanse = cleanse.replace('W', '')
                    cursor.execute(f"Select distinct(Player_Name), count(Character_Name) from A_STG_Player_Characters where Created_Date <= date('now', '-{cleanse} weeks')")
                    player_id_info = cursor.fetchall()
                    x = 0
                    for inactive_player in player_id_info:
                        x += 1
                        overall_wipe_list.append(inactive_player[0])
                        if x <= 20:
                            embed.add_field(name=f"{player_id_info[0]}'s characters will be removed", value=f"this player had {player_id_info[1]} characters!")
                    embed.set_footer(text=f"{x} Total Players were inactive and are being removed!")
                else:
                    embed.add_field(name=f"Invalid Duration", value=f"Please use a number ending in D for days or W for weeks.")
            buttons = ["✅", "❌"]  # checkmark X symbol
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
                    if reaction.emoji == "❌":
                        embed = discord.Embed(title=f"you have reconsidered wiping a character", description=f"life is a kindness, do not waste it!", colour=discord.Colour.blurple())
                        await msg.edit(embed=embed)
                        await msg.clear_reactions()
                    if reaction.emoji == u"\u2705":
                        embed = discord.Embed(title=f"Character wipe has been approved!", description=f"Getting rid of outdated characters.", colour=discord.Colour.red())
                        await msg.clear_reactions()
                        await msg.edit(embed=embed)
                        print(overall_wipe_list)
                        print(type(overall_wipe_list))
                        for wiped in overall_wipe_list:
                            await Event.wipe_unapproved(self, wiped, guild_id, author)
    else:
        e = None
        try:
            await ctx.response.defer(thinking=True, ephemeral=True)
        except Exception as e:
            print(e)
            pass
        guild_id = ctx.guild_id
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        author = ctx.user.name
        character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
        cursor.execute(f"Select True_Character_Name, tmp_bio from A_STG_Player_Characters where character_name = ?", (character_name,))
        player_id_info = cursor.fetchone()
        if player_id_info is not None:
            try:
                e = None
                await Event.create_bio(self, guild_id, player_id_info[0], player_id_info[1])
            except Exception as e:
                print(e)
                pass
            await Event.create_character(self, guild_id, author, player_id_info[0])
            cursor.execute(f"SELECT Search FROM Admin WHERE Identifier = 'Approved_Character'")
            approved_character = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
            accepted_bio_channel = cursor.fetchone()
            cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
            character_log_channel_id = cursor.fetchone()
            cursor.execute(f"SELECT Player_Name, True_Character_Name, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_Value_Max, Mythweavers, Image_Link, Color, Flux, Player_ID, Oath, Article_Link FROM Player_Characters WHERE Character_Name = ?", (character_name,))
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
            embed = discord.Embed(title=f"{character_info[1]}", url=f'{character_info[13]}', description=f"{description_field}", color=int_color)
            embed.set_author(name=f'{character_info[0]}')
            embed.set_thumbnail(url=f'{character_info[14]}')
            embed.add_field(name="Information", value=f'**Level**: 3, **Mythic Tier**: 0, **Fame**: 0', inline=False)
            embed.add_field(name="Experience", value=f'**Milestones**: 0, **Remaining**: 3')
            embed.add_field(name="Mythic", value=f'**Trials**: 0, **Remaining**: 0')
            embed.add_field(name="Current Wealth", value=f'**GP**: {character_info[10]}', inline=False)
            embed.add_field(name="Current Flux", value=f'**Flux**: 0')
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
            bio_message = await bio_channel.send(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            embed = discord.Embed(title=f"{character_info[1]}", url=f'{character_info[13]}', description=f"Other Names: {character_info[2]}", color=int_color)
            embed.set_author(name=f'{character_info[0]}')
            embed.set_thumbnail(url=f'{character_info[14]}')
            character_log_channel = await bot.fetch_channel(character_log_channel_id[0])
            character_log_message = await character_log_channel.send(content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
            thread = await character_log_message.create_thread(name=f'{character_info[1]}')
            await Event.log_character(self, guild_id, character_name, bio_message.id, character_log_message.id, thread.id)
            if e is None:
                await ctx.followup.send(content=f"{character_name} has been accepted into the server!")
            else:
                ctx.send(f"{character_name} has been accepted into the server!")
        else:
            if e is None:
                await ctx.followup.send(f"{character_name} could not be found in the database.", ephemeral=True)
            else:
                ctx.send(f"{character_name} has been accepted into the server!")


@admin.command()
@app_commands.autocomplete(character_name=character_select_autocompletion)
@app_commands.describe(destination="Shorthand for determining whether you are looking for a character name or nickname")
@app_commands.choices(destination=[discord.app_commands.Choice(name='Tradition', value=1), discord.app_commands.Choice(name='Template', value=2)])
@app_commands.describe(customized_name="For the name of the template or tradition")
async def customize(ctx: commands.Context, character_name: str, destination: discord.app_commands.Choice[int], customized_name: str, link: str, flux_cost: int = 0):
    """Administrative: set a character's template or tradition!"""
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = ctx.guild_id
    guild = ctx.guild
    if destination == 1:
        destination = 1
    else:
        destination = destination.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = ctx.user.name
    cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_value_Max, Flux, Color, Mythweavers, Image_Link, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Message_ID, Logging_ID, Thread_ID, Fame, Title, Personal_Cap, Prestige, Article_Link FROM Player_Characters where Character_Name = ?", (character_name, ))
    player_info = cursor.fetchone()

    if player_info is None:
        await ctx.response.send_message(f"no character with the Name or Nickname of {character_name} could be found!", ephemeral=True)
    else:
        destination_name = 'Tradition_Name' if destination == 1 else 'Template_Name'
        destination_link = 'Tradition_Link' if destination == 1 else 'Template_Link'
        destination_name_pretty = 'Tradition Name' if destination == 1 else 'Template Name'
        tradition_name = customized_name if destination == 1 else None
        tradition_link = link if destination == 1 else None
        template_name = customized_name if destination == 2 else None
        template_link = link if destination == 2 else None
        flux_remaining = player_info[16] - flux_cost
        await Event.customize_characters(self, guild_id, author, player_info[3], destination_name, destination_link, customized_name, link, flux_remaining, flux_cost)
        embed = discord.Embed(title=f"{destination_name_pretty} change for {player_info[3]}", description=f"<@{player_info[1]}>'s {player_info[3]} has spent {flux_cost} flux leaving them with {player_info[16] - flux_cost} flux!", colour=discord.Colour.blurple())
        embed.add_field(name=f'**{destination_name_pretty} Information:**', value=f'[{customized_name}](<{link}>)', inline=False)
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Accepted_Bio_Channel'")
        accepted_bio_channel = cursor.fetchone()
        cursor.execute(f"Select Search FROM Admin WHERE Identifier = 'Char_Eventlog_Channel'")
        character_log_channel_id = cursor.fetchone()
        cursor.close()
        db.close()
        bio_embed = character_embed(player_info[0], player_info[1], player_info[2], player_info[4], player_info[5], player_info[6], player_info[7], player_info[8], player_info[9], player_info[10], player_info[11], player_info[12], player_info[13], player_info[14], player_info[16] + flux_cost, player_info[17], player_info[18], player_info[19], player_info[20], player_info[21], player_info[22], player_info[23], player_info[27], player_info[28], player_info[30], player_info[31])
        bio_channel = await bot.fetch_channel(accepted_bio_channel[0])
        bio_message = await bio_channel.fetch_message(player_info[24])
        await bio_message.edit(content=bio_embed[1], embed=bio_embed[0])
        source = f"changed a template or tradition for {character_name}"
        logging_embed = log_embed(player_info[2], author, None, None, None, None, None, None, None, None, None, None, None, None, player_info[16] - flux_cost, flux_cost, tradition_name, tradition_link, template_name, template_link, None, None, None, None, None, source)
        logging_thread = guild.get_thread(player_info[25])
        await logging_thread.send(embed=logging_embed)
        await ctx.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))


@admin.command()
@app_commands.describe(modify="add, remove edit, or display something in the store.")
@app_commands.choices(modify=[discord.app_commands.Choice(name='Display', value=1), discord.app_commands.Choice(name='Add', value=2), discord.app_commands.Choice(name='Edit', value=3), discord.app_commands.Choice(name='Remove', value=4)])
async def fame_store(ctx: commands.Context, name: str, fame_required: typing.Optional[int], prestige_cost: typing.Optional[int], effect: typing.Optional[str], limit: typing.Optional[int], modify: discord.app_commands.Choice[int] = 1):
    """add, edit, remove, or display something from one of the stores"""
    guild_id = ctx.guild_id
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
    author = ctx.user.name
    cursor.execute(f"SELECT Fame_Required, Prestige_Cost, Effect, Use_Limit FROM Store_Fame where Name = ?", (name,))
    item_info = cursor.fetchone()
    cursor.close()
    db.close()
    if item_info is None and modify == 2:
        await Event.add_fame_store(self, guild_id, author, fame_required, prestige_cost, name, effect, limit)
        embed = discord.Embed(title=f"New Fame Store Item", description=f'{name} has been added to the fame store!', colour=discord.Colour.blurple())
        embed.add_field(name=f'**Cost:**', value=f'Requires {fame_required} fame, Costs: {prestige_cost} prestige, Limited to {limit}', inline=False)
        embed.add_field(name=f'**Effect:**', value=f'{effect}', inline=False)
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 3:
        await Event.remove_fame_store(self, guild_id, author, name)
        embed = discord.Embed(title=f"Removed Fame Store Item", description=f'{name} has been removed from the fame store!', colour=discord.Colour.blurple())
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 4:
        await Event.edit_fame_store(self, guild_id, author, fame_required, prestige_cost, name, effect, limit)
        embed = discord.Embed(title=f"Edited Fame Store Item", description=f'{name} has been edited in the fame store!', colour=discord.Colour.blurple())
        embed.add_field(name=f'**Cost:**', value=f'Requires {fame_required} fame, Costs: {prestige_cost} prestige, Limited to {limit}', inline=False)
        embed.add_field(name=f'**Effect:**', value=f'{effect}', inline=False)
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif modify == 1:
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit FROM Store_Fame where Name = ?""", (name,))
        item_info = cursor.fetchone()
        if item_info is not None:
            embed = discord.Embed(title=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}', colour=discord.Colour.blurple())
            await ctx.response.send_message(embed=embed)
        else:
            buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
            cursor.execute(f"""SELECT COUNT(Name) FROM Store_Fame""")
            admin_count = cursor.fetchone()
            max_page = math.ceil(admin_count[0] / 20)
            current_page = 1
            low = 1 + ((current_page - 1) * 20)
            high = 20 + ((current_page - 1) * 20)
            cursor.execute(f"""SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}""")
            pull = cursor.fetchall()
            embed = discord.Embed(title=f"Fame Store Settings Page {current_page}", description=f'This is a list of the administratively defined items', colour=discord.Colour.blurple())
            for result in pull:
                embed.add_field(name=f'**Name**: {result[1]}', value=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}', inline=False)
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
                        cursor.execute(f"""SELECT Fame_Required, Prestige_Cost, Name, Effect, Use_Limit from Store_Fame WHERE ROWID BETWEEN {low} and {high}""")
                        pull = cursor.fetchall()
                        embed = discord.Embed(title=f"Fame Store Settings Page {current_page}", description=f'This is a list of the administratively defined items', colour=discord.Colour.blurple())
                        for result in pull:
                            embed.add_field(name=f'**Name**: {result[1]}', value=f'**Fame Required**: {result[0]} **Prestige Cost**: {result[1]}, **Limit**: {result[4]} \r\n **Effect**: {result[3]}', inline=False)
                        await msg.edit(embed=embed)
    else:
        await ctx.response.send_message(f"you were trying to do the following {modify} modification in the Fame Store, but {name} was incorrect!", ephemeral=True)

@admin.command()
@app_commands.describe(modify="add, remove edit, or display something in the store.")
@app_commands.choices(modify=[discord.app_commands.Choice(name='Add', value=1), discord.app_commands.Choice(name='Remove', value=2), discord.app_commands.Choice(name='edit', value=3), discord.app_commands.Choice(name='Display', value=4)])
async def title_store(ctx: commands.Context, masculine_name: typing.Optional[str], feminine_name: typing.Optional[str], fame: typing.Optional[int], effect: typing.Optional[str], ubb_id: typing.Optional[str], modify: discord.app_commands.Choice[int] = 4):
    """add, edit, remove, or display something from one of the stores"""
    guild_id = ctx.guild_id
    ubb_id = ubb_id.strip() if ubb_id is not None else None
    fame = 0 if fame is None else fame
    modify = 4 if modify == 4 else modify.value
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    author = ctx.user.name
    cursor.execute(f"SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title where Masculine_Name = ? OR Feminine_Name = ?", (masculine_name, feminine_name))
    item_info = cursor.fetchone()
    cursor.close()
    db.close()
    if item_info is None and modify == 1:
        await Event.add_title_store(self, guild_id, author, ubb_id, effect, fame, masculine_name, feminine_name)
        embed = discord.Embed(title=f"New Title Store Item", description=f'{masculine_name}/{feminine_name} has been added to the title store!', colour=discord.Colour.blurple())
        embed.add_field(name=f'**description:**', value=f'{effect}', inline=False)
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 2:
        await Event.remove_title_store(self, guild_id, author, item_info[2], item_info[3], item_info[4])
        embed = discord.Embed(title=f"Removed Title Store Item", description=f'{masculine_name}/{feminine_name} has been removed from the title store!', colour=discord.Colour.blurple())
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif item_info is not None and modify == 3:
        await Event.edit_title_store(self, guild_id, author, ubb_id, effect, fame, masculine_name, feminine_name)
        embed = discord.Embed(title=f"Edited Title Store Item", description=f'{masculine_name}/{feminine_name} has been edited in the title store!', colour=discord.Colour.blurple())
        embed.add_field(name=f'**description:**', value=f'{effect}', inline=False)
        await ctx.response.send_message(embed=embed, ephemeral=True)
    elif modify == 4:
        if item_info is not None:
            embed = discord.Embed(title=f"Title Store Item: {item_info[3]}/{item_info[4]}", description=f'**ID**: {item_info[0]}, **Effect**: {item_info[1]}, **Rewarded Fame**: {item_info[2]}', colour=discord.Colour.blurple())
            await ctx.response.send_message(embed=embed)
        else:
            db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
            cursor = db.cursor()
            buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
            cursor.execute(f"""SELECT COUNT(masculine_name) FROM Store_Title""")
            admin_count = cursor.fetchone()
            max_page = math.ceil(admin_count[0] / 20)
            current_page = 1
            low = 1 + ((current_page - 1) * 20)
            high = 20 + ((current_page - 1) * 20)
            cursor.execute(f"""SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}""")
            pull = cursor.fetchall()
            embed = discord.Embed(title=f"Title Store Settings Page {current_page}", description=f'This is a list of the administratively defined items', colour=discord.Colour.blurple())
            for result in pull:
                embed.add_field(name=f"Title Store Item: {result[3]}/{result[4]}", value=f'**ID**: {result[0]}, **Effect**: {result[1]}, **Rewarded Fame**: {result[2]}', inline=False)
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
                        cursor.execute(f"""SELECT ID, Effect, Fame, Masculine_Name, Feminine_Name FROM Store_Title WHERE ROWID BETWEEN {low} and {high}""")
                        pull = cursor.fetchall()
                        embed = discord.Embed(title=f"Title Store Settings Page {current_page}", description=f'This is a list of the administratively defined items', colour=discord.Colour.blurple())
                        for result in pull:
                            embed.add_field(name=f"Title Store Item: {result[3]}/{result[4]}", value=f'**ID**: {result[0]}, **Effect**: {result[1]}, **Rewarded Fame**: {result[2]}', inline=False)
                        await msg.edit(embed=embed)
    else:
        await ctx.response.send_message(f"you were trying to do the following {modify} modification in the title store, but {name} was incorrect!", ephemeral=True)


@admin.command()
async def watest(ctx: commands.Context):
    """This is a test command for the wa command."""
    await ctx.response.send_message("This is a test command for the wa command.")
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
    articles = [article for article in client.world.articles('f7a60480-ea15-4867-ae03-e9e0c676060a', 'c8fd1251-1077-4bbd-a9a5-797b3dbdf356')]
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