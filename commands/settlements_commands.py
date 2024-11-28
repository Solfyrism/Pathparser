
@settlement.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Settlement Help", description=f'This is a list of Settlement help commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Claim**', value=f'The command for a player to claim a new settlement.', inline=False)
    embed.add_field(name=f'**Destroy**', value=f'The command for a player to release their settlement.', inline=False)
    embed.add_field(name=f'**Modify**', value=f'The command for a player to modify the properties of a settlement.', inline=False)
    embed.add_field(name=f'**Detail**', value=f'The detailed display of the buildings in a settlement.', inline=False)
    embed.add_field(name=f'**DisplayOne**', value=f'The kingdom display of a settlement.', inline=False)
    embed.add_field(name=f'**DisplayAll**', value=f'Displays all settlements owned by the kingdom.', inline=False)
    await ctx.response.send_message(embed=embed)


@settlement.command()
async def claim(ctx: commands.Context, kingdom: str, password: str, settlement: str):
    """This allows the kingdom to claim a new settlement."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Settlement FROM Settlements WHERE Settlement = '{settlement}' AND Kingdom = '{kingdom}'""", {'settlement': settlement, 'kingdom': kingdom})
    settlement_result = cursor.fetchone()
    cursor.execute(f"""SELECT kingdom, password FROM kingdoms WHERE Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_result = cursor.fetchone()
    cursor.close()
    db.close()
    if kingdom_result is None:
        await ctx.response.send_message(f'{kingdom} does not exist!')
    if kingdom_result[1] != password:
        await ctx.response.send_message(f'The password you used was incorrect for the kingdom of {kingdom}!')
    if settlement_result is not None:
        status = f"You cannot claim the same settlement of {settlement} a second time for your kingdom of {kingdom}"
        await ctx.response.send_message(status)
    if settlement_result is None and kingdom_result[1] == password:
        status = f"You have claimed {settlement} for your kingdom of {kingdom}"
        await ctx.response.send_message(status)
        await Event.claim_settlement(self, kingdom, settlement, guild_id, author)


@settlement.command()
async def destroy(ctx: commands.Context, kingdom: str, password: str, settlement: str):
    """This allows a kingdom to remove its claim to a settlement and void its holdings."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Settlement FROM Settlements WHERE Settlement = '{settlement}' AND Kingdom = '{kingdom}'""", {'Kingdom': kingdom, 'Settlement': settlement})
    settlement_result = cursor.fetchone()
    cursor.execute(f"""SELECT Kingdom, Password FROM kingdoms WHERE Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_result = cursor.fetchone()
    cursor.close()
    db.close()
    if kingdom_result is None:
        await ctx.response.send_message(f'{kingdom} is not a valid kingdom.')
    elif kingdom_result[1] != password:
        await ctx.response.send_message(f'you have submitted an invalid password for {kingdom}')
    elif settlement_result is not None and kingdom_result[1] == password:
        status = f"Your kingdom of {kingdom} has let their control over the settlement of {settlement} lapse."
        await Event.destroy_settlement(self, kingdom, settlement, guild_id, author)
        await ctx.response.send_message(status)
    elif settlement_result is None:
        status = f"You cannot have {kingdom} make a war crime out of {settlement} if it doesn't exist!"
        await ctx.response.send_message(status)


@settlement.command()
async def modify(ctx: commands.Context, kingdom: str, password: str, old_settlement: str, new_settlement: str):
    """This will modify the name of a settlement by the kingdom owner."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    old_settlement = str.replace(str.title(old_settlement), ";", "")
    new_settlement = str.replace(str.title(new_settlement), ";", "")
    password = str.replace(str.title(password), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Settlement FROM Settlements WHERE Settlement = '{old_settlement}' AND Kingdom = '{kingdom}'""", {'Settlement': old_settlement, 'Kingdom': kingdom})
    result = cursor.fetchone()
    cursor.execute(f"""SELECT Kingdom, Password FROM kingdoms WHERE Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_result = cursor.fetchone()
    cursor.close()
    db.close()
    if kingdom_result is None:
        await ctx.response.send_message(f'{kingdom} is not a valid kingdom.')
    elif kingdom_result[1] != password:
        await ctx.response.send_message(f'you have submitted an invalid password for {kingdom}')
    if result is None:
        status = f"You cannot modify a settlement which doesn't exist!"
        await ctx.response.send_message(status)
    if result is not None and password == kingdom_result[1]:
        status = f"Congratulations you have changed the settlement from {old_settlement} to {new_settlement}"
        await ctx.response.send_message(status)
        await Event.modify_settlement(self, kingdom, old_settlement, new_settlement, guild_id, author)


@settlement.command()
async def detail(ctx: commands.Context, kingdom: str, settlement: str, current_page: int = 1):
    """This will offer the detailed view of a settlement and it's buildings"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    cursor.execute(f"""SELECT COUNT(building) FROM Buildings WHERE Kingdom = '{kingdom}' AND Settlement = '{settlement}'""", {'Kingdom': kingdom, 'Settlement': settlement})
    blueprint_count = cursor.fetchone()
    max_page = math.ceil(blueprint_count[0] / 5)
    if current_page >= max_page:
        current_page = max_page
    low = 1 + ((current_page-1) * 5)
    high = 5 + ((current_page-1) * 5)
    cursor.execute(f"""SELECT Building, Constructed, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_value, Spellcasting, Supply from Buildings WHERE Kingdom = '{kingdom}' AND Settlement = '{settlement}' AND ROWID BETWEEN {low} and {high}""", {'Kingdom': kingdom, 'Settlement': settlement})
    pull = cursor.fetchall()
    embed = discord.Embed(title=f"Buildings page {current_page}", description=f'This is list of constructed buildings in the settlement of {settlement} in kingdom of {kingdom}', colour=discord.Colour.blurple())
    for result in pull:
        embed.add_field(name=f'Buildings Info', value=f'***__Building__***: {result[0]}, **Constructed**: {result[1]}, **Lots occupied**: {result[2]}, **Supply**: {result[18]}', inline=False)
        embed.add_field(name=f'Kingdom Benefits', value=f'**Economy**: {result [3]}, **Loyalty**: {result[4]}, **Stability**: {result[5]}, **Fame:**: {result[6]}, **Unrest**: {result[7]}', inline=False)
        embed.add_field(name=f'Settlement Benefits', value=f'**Corruption:**: {result[8]}, **Crime**: {result[9]}, **Productivity**: {result[10]}, **Law**: {result[11]}, **Lore**: {result[12]}, **Society**: {result[13]}', inline=False)
        embed.add_field(name=f'Settlement Risks', value=f'**Danger**: {result[14]} **Defence**: {result[15]}')
        embed.add_field(name=f'Settlement Economy', value=f'**Base Value**: {result[16]}, **Spellcasting**: {result[17]}')
        embed.add_field(name=f'Settlement Limitation', value=f'**Settlement Limit**: {result[19]}, **District Limit**: {result[20]}')
        embed.add_field(name=f'Blueprint Description', value=f'{result[21]}', inline=False)
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
                high = 5
            elif reaction.emoji == u"\u2B05" and current_page > 1:
                low -= 5
                high -= 5
                current_page -= 1
            elif reaction.emoji == u"\u27A1" and current_page < max_page:
                low += 5
                high += 5
                current_page += 1
            elif reaction.emoji == u"\u23E9":
                current_page = max_page
                low = ((5 * max_page) - 4)
                high = (5 * max_page)
            for button in buttons:
                await msg.remove_reaction(button, ctx.user)
            if current_page != previous_page:
                cursor.execute(f"""SELECT Building, Build_Points, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence Base_value, Spellcasting, Supply, Settlement_limit, District_Limit, Description from Buildings WHERE Kingdom = '{kingdom}' AND Settlement = '{settlement}' AND ROWID BETWEEN {low} and {high}""", {'Kingdom': kingdom, 'Settlement': settlement})
                edit_pull = cursor.fetchall()
                embed = discord.Embed(title=f"Buildings page {current_page}", description=f'This is list of constructed buildings in the settlement of {settlement} in kingdom of {kingdom}', colour=discord.Colour.blurple())
                for result in edit_pull:
                    embed.add_field(name=f'Buildings Info', value=f'***__Building__***: {result[0]}, **Constructed**: {result[1]}, **Lots occupied**: {result[2]}, **Supply**: {result[18]}', inline=False)
                    embed.add_field(name=f'Kingdom Benefits', value=f'**Economy**: {result[3]}, **Loyalty**: {result[4]}, **Stability**: {result[5]}, **Fame:**: {result[6]}, **Unrest**: {result[7]}', inline=False)
                    embed.add_field(name=f'Settlement Benefits', value=f'**Corruption:**: {result[8]}, **Crime**: {result[9]}, **Productivity**: {result[10]}, **Law**: {result[11]}, **Lore**: {result[12]}, **Society**: {result[13]}', inline=False)
                    embed.add_field(name=f'Settlement Risks', value=f'**Danger**: {result[14]} **Defence**: {result[15]}')
                    embed.add_field(name=f'Settlement Economy', value=f'**Base Value**: {result[16]}, **Spellcasting**: {result[17]}')
                    embed.add_field(name=f'Settlement Limitation', value=f'**Settlement Limit**: {result[19]}, **District Limit**: {result[20]}')
                    embed.add_field(name=f'Blueprint Description', value=f'{result[21]}', inline=False)
                await msg.edit(embed=embed)

"""This calls all buildings in a settlement"""


@settlement.command()
async def displayall(ctx: commands.Context, kingdom: str, settlement: str, current_page: int = 1):
    """This will display all settlements associated to a kingdom."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT COUNT(Settlement) FROM Settlements WHERE Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
    settlement_count = cursor.fetchone()
    max_page = math.ceil(settlement_count[0] / 5)
    if current_page >= max_page:
        current_page = max_page
    low = 1 + ((current_page-1) * 5)
    high = 5 + ((current_page-1) * 5)
    cursor.execute(f"""SELECT Settlement, size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay FROM Settlements WHERE Kingdom = '{kingdom}' AND ROWID BETWEEN {low} and {high}""", {'Kingdom': kingdom})
    pull = cursor.fetchall()
    embed = discord.Embed(title=f"Settlements page {current_page}", description=f'This is list of settlements in {kingdom}', colour=discord.Colour.blurple())
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    decay = cursor.fetchone()
    if decay[0]:  # IF THE SERVER HAS DECAY ON
        for result in pull:
            embed.add_field(name=f'Settlement info', value=f'**Settlement**: {result[0]}, **Districts**: {result[1]} **Population**: {result[2]}, **Supply**: {result[13]}, **Decay**: {result[14]}', inline=False)
            embed.add_field(name=f'Settlement Benefits', value=f'**Corruption**: {result[3]}, **Crime**: {result[4]}, **Productivity**: {result[5]}, **Law**: {result[6]}, **Lore**: {result[7]}, **Society**: {result[8]}', inline=False)
            embed.add_field(name=f'Settlement Misc', value=f'**Danger**: {result[9]}, **Defence**: {result[10]} **Base_Value**: {result[11]} **Spellcasting**: {result[12]}, ', inline=False)
    else:
        for result in pull:
            embed.add_field(name=f'Settlement info', value=f'**Settlement**: {result[0]}, **Districts**: {result[1]} **Population**: {result[2]}, **Supply**: {result[13]}', inline=False)
            embed.add_field(name=f'Settlement Benefits', value=f'**Corruption**: {result[3]}, **Crime**: {result[4]}, **Productivity**: {result[5]}, **Law**: {result[6]}, **Lore**: {result[7]}, **Society**: {result[8]}', inline=False)
            embed.add_field(name=f'Settlement Misc', value=f'**Danger**: {result[9]}, **Defence**: {result[10]} **Base_Value**: {result[11]} **Spellcasting**: {result[12]}, ', inline=False)
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
                high = 5
            elif reaction.emoji == u"\u2B05" and current_page > 1:
                low -= 5
                high -= 5
                current_page -= 1
            elif reaction.emoji == u"\u27A1" and current_page < max_page:
                low += 5
                high += 5
                current_page += 1
            elif reaction.emoji == u"\u23E9":
                current_page = max_page
                low = ((5 * max_page) - 4)
                high = (5 * max_page)
            for button in buttons:
                await msg.remove_reaction(button, ctx.user)
            if current_page != previous_page:
                cursor.execute(f"""SELECT Settlement, size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay FROM Settlements WHERE Kingdom = '{kingdom}' AND ROWID BETWEEN {low} and {high}""", {'Kingdom': kingdom})
                edit_pull = cursor.fetchall()
                embed = discord.Embed(title=f"Settlements page {current_page}", description=f'This is list of settlements in {kingdom}', colour=discord.Colour.blurple())
                if decay[0]:  # IF THE SERVER HAS DECAY ON
                    for result in pull:
                        embed.add_field(name=f'Settlement info', value=f'**Settlement**: {result[0]}, **Districts**: {result[1]} **Population**: {result[2]}, **Supply**: {result[13]}, **Decay**: {result[14]}', inline=False)
                        embed.add_field(name=f'Settlement Benefits', value=f'**Corruption**: {result[3]}, **Crime**: {result[4]}, **Productivity**: {result[5]}, **Law**: {result[6]}, **Lore**: {result[7]}, **Society**: {result[8]}', inline=False)
                        embed.add_field(name=f'Settlement Misc', value=f'**Danger**: {result[9]}, **Defence**: {result[10]} **Base_Value**: {result[11]} **Spellcasting**: {result[12]}, ', inline=False)
                else:
                    for result in pull:
                        embed.add_field(name=f'Settlement info', value=f'**Settlement**: {result[0]}, **Districts**: {result[1]} **Population**: {result[2]}, **Supply**: {result[13]}', inline=False)
                        embed.add_field(name=f'Settlement Benefits', value=f'**Corruption**: {result[3]}, **Crime**: {result[4]}, **Productivity**: {result[5]}, **Law**: {result[6]}, **Lore**: {result[7]}, **Society**: {result[8]}', inline=False)
                        embed.add_field(name=f'Settlement Misc', value=f'**Danger**: {result[9]}, **Defence**: {result[10]} **Base_Value**: {result[11]} **Spellcasting**: {result[12]}, ', inline=False)
                await msg.edit(embed=embed)
"""This is a Settlement shop"""


@settlement.command()
async def displayone(ctx: commands.Context, kingdom: str, settlement: str, custom_stats: bool = False):
    """This will display a singular settlement, and it's basic information"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    decay = cursor.fetchone()
    if custom_stats is False:
        cursor.execute(f"""SELECT Size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay from Settlements where Kingdom = '{kingdom}' and Settlement = '{settlement}'""", {'Kingdom': kingdom, 'Settlement': settlement})
        settlement_info = cursor.fetchone()
        cursor.execute(f"""SELECT Government, Alignment from Kingdoms where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
        kingdom_info = cursor.fetchone()
        if kingdom_info is None:
            await ctx.response.send_message(f'The kingdom of {kingdom} could not be found.')
        if settlement_info is None:
            await ctx.response.send_message(f'The settlement of {settlement} could not be found underneath the kingdom of {kingdom}.')
        if kingdom_info is not None and settlement_info is not None:
            embed = discord.Embed(title=f"Settlement {Settlement} of kingdom {kingdom}", description=f'Here is the full view of this Settlement', colour=discord.Colour.blurple())
            embed.add_field(name=f'Government', value=f'{kingdom_info[0]}')
            embed.add_field(name=f'Alignment', value=f'{kingdom_info[1]}')
            embed.add_field(name=f'Size', value=f'{settlement_info[0]}', inline=False)
            embed.add_field(name=f'Population', value=f'{settlement_info[1]}')
            embed.add_field(name=f'Corruption', value=f'{settlement_info[2]}')
            embed.add_field(name=f'Crime', value=f'{settlement_info[3]}')
            embed.add_field(name=f'Productivity', value=f'{settlement_info[4]}')
            embed.add_field(name=f'Law', value=f'{settlement_info[5]}')
            embed.add_field(name=f'Lore', value=f'{settlement_info[6]}')
            embed.add_field(name=f'Society', value=f'{settlement_info[7]}')
            embed.add_field(name=f'Danger', value=f'{settlement_info[8]}')
            embed.add_field(name=f'Defence', value=f'{settlement_info[9]}')
            embed.add_field(name=f'Base_Value', value=f'{settlement_info[10]}')
            embed.add_field(name=f'Spellcasting', value=f'{settlement_info[11]}')
            embed.add_field(name=f'Supply', value=f'{settlement_info[12]}')
            if decay[0]:  # IF THE SERVER HAS DECAY ON
                embed.add_field(name=f'Decay', value=f'{settlement_info[15]}')
            await ctx.response.send_message(embed=embed)
    if custom_stats is True:
        cursor.execute(f"""SELECT Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply from Settlements_Custom where Kingdom = '{kingdom}' and Settlement = '{settlement}'""", {'Kingdom': kingdom, 'Settlement': settlement})
        kingdom_info = cursor.fetchone()
        if kingdom_info is None:
            await ctx.response.send_message(f'The settlement of {settlement} underneath kingdom of {kingdom_info} could not be found.')
        if kingdom_info is not None:
            embed = discord.Embed(title=f"Settlement of {settlement} underneath kingdom of {kingdom}", description=f'Here is the full view of this Custom Information for this Settlement', colour=discord.Colour.blurple())
            embed.add_field(name=f'Corruption', value=f'{kingdom_info[0]}')
            embed.add_field(name=f'Crime', value=f'{kingdom_info[1]}')
            embed.add_field(name=f'Productivity', value=f'{kingdom_info[2]}')
            embed.add_field(name=f'Law', value=f'{kingdom_info[3]}')
            embed.add_field(name=f'Lore', value=f'{kingdom_info[4]}')
            embed.add_field(name=f'Society', value=f'{kingdom_info[5]}')
            embed.add_field(name=f'Danger', value=f'{kingdom_info[6]}')
            embed.add_field(name=f'Defence', value=f'{kingdom_info[7]}')
            embed.add_field(name=f'Base_Value', value=f'{kingdom_info[8]}')
            embed.add_field(name=f'Spellcasting', value=f'{kingdom_info[9]}')
            await ctx.response.send_message(embed=embed)
    cursor.close()
    db.close()
"""This calls a specific settlement or custom info"""
