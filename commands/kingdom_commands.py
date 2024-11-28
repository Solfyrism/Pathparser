
@kingdom.command()
async def help(ctx: commands.Context):
    """an extremely simple help request for Kingdoms"""
    embed = discord.Embed(title=f"Kingdoms Help", description=f'This is a list of kingdom help commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**Create Kingdom**', value=f'This command allows a player to take the first step of kingdom management, creating their kingdom and allowing them to interact with it. NOTE: There is NO encryption. When creating a password do NOT use a personalized password.', inline=False)
    embed.add_field(name=f'**Destroy Kingdom**', value=f'This command will delete all properties of kingdom management, deleting it from the database.', inline=False)
    embed.add_field(name=f'**Modify Kingdom**', value=f'This command allows the kingdom leaders to modify the name of the kingdom.', inline=False)
    embed.add_field(name=f'**Display Kingdom**', value=f'This command displays all kingdoms along with some basic information about them.', inline=False)
    embed.add_field(name=f'**Detail Kingdoms**', value=f'This displays the detailed view of a singular kingdom.', inline=False)
    embed.add_field(name=f'**BP**', value=f'Modifies the build points allocated to a kingdom by a negative or positive value', inline=False)
    embed.add_field(name=f'**SP**', value=f'Modifies the [stabilization points](https://docs.google.com/document/d/1c_W0d-fDgQukteeX8fwNXv3egKD41b6FXtuSPurUoLg/edit?usp=sharing) allocated to a kingdom by a negative or positive value', inline=False)
    embed.add_field(name=f'**Reference Links**', value=f'[Government](https://www.aonprd.com/Rules.aspx?Name=Forms%20of%20Government&Category=Optional%20Kingdom%20Rules),[Build Points](https://www.d20pfsrd.com/gamemastering/other-rules/kingdom-building#TOC-Build-Points), [Decay](https://docs.google.com/document/d/1c_W0d-fDgQukteeX8fwNXv3egKD41b6FXtuSPurUoLg/edit?usp=sharing)')
    await ctx.response.send_message(embed=embed)


@kingdom.command()
async def create(ctx: commands.Context, kingdom: str, password: str, government: str, alignment: str):
    """This creates allows a player to create a new kingdom"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    government = str.replace(str.title(government), ";", "")
    password = str.replace(password, ";", "")
    alignment = str.replace(str.upper(alignment), ";", "")
    guild_id = ctx.guild.id
    author = ctx.user.name
    db = sqlite3.connect(f"pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    kingdom_validity = cursor.fetchone()
    cursor.execute(f"""SELECT Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = '{alignment}'""", {'Alignment': alignment})
    alignment_validity = cursor.fetchone()
    cursor.execute(f"""SELECT Government FROM AA_Government WHERE Government = '{government}'""", {'Government': government})
    government_validity = cursor.fetchone()
    if alignment_validity is None:
        await ctx.response.send_message(content=f"You have offered an invalid alignment of {alignment}.")
        cursor.close()
        db.close()
        return
    if kingdom_validity is not None:
        status = f"the kingdom of **{kingdom}** Already Exists."
        await ctx.response.send_message(content=status)
        cursor.close()
        db.close()
        return
    if government_validity is None:
        await ctx.response.send_message(content=f"{government} government type does not exist.")
        cursor.close()
        db.close()
        return
    if alignment_validity is not None and kingdom_validity is None and government_validity is not None:
        economy = alignment_validity[1]
        loyalty = alignment_validity[2]
        stability = alignment_validity[3]
        status = f"Congratulations you have made the kingdom of **{kingdom}** a reality"
        await Event.create_kingdom(self, kingdom, password, government, alignment, economy, loyalty, stability, guild_id, author)
        await ctx.response.send_message(content=status)
    cursor.close()
    db.close()


@kingdom.command()
async def destroy(ctx: commands.Context, kingdom: str, password: str):
    """This is a player command to remove a kingdom THEY OWN from play"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    password = str.replace(password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"the kingdom which you have elected to make a war crime out of couldn't be found."
        await ctx.response.send_message(content=status)
    if result is not None and result[1] == password:
        status = f"The Kingdom of {kingdom} can no longer be found, whether it be settlements, political figures, or Buildings"
        await Event.destroy_kingdom(self, kingdom, guild_id, author)
        await ctx.response.send_message(content=status)
    else:
        status = f"You have entered an invalid password for this kingdom."
        await ctx.response.send_message(content=status)


@kingdom.command()
async def modify(ctx: commands.Context, old_kingdom: str, new_kingdom: str, old_password: str, new_password: str, new_government: str, new_alignment: str):
    """This is a player command to modify a kingdom THEY OWN."""
    new_kingdom = str.replace(str.title(new_kingdom), ";", "")
    old_kingdom = str.replace(str.title(old_kingdom), ";", "")
    new_government = str.replace(str.title(new_government), ";", "")
    new_alignment = str.replace(str.upper(new_alignment), ";", "")
    new_password = str.replace(new_password, ";", "")
    old_password = str.replace(old_password, ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{old_kingdom}'""", {'Kingdom': old_kingdom})
    result = cursor.fetchone()
    cursor.execute(f"""SELECT Alignment, Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = '{new_alignment}'""", {'Alignment': new_alignment})
    alignment_validity = cursor.fetchone()
    cursor.execute(f"""SELECT Government FROM AA_Government WHERE Government = '{new_government}'""", {'Government': new_government})
    government_validity = cursor.fetchone()
    cursor.close()
    db.close()
    if alignment_validity is None:
        await ctx.response.send_message(content=f"{new_alignment} is not a invalid alignment.")
        return
    if government_validity is None:
        await ctx.response.send_message(content=f"Government type of {new_government} does not exist.")
        return
    if result is None:
        status = f"The kingdom of {old_kingdom} which you have attempted to modify was doesn't exist."
        await ctx.response.send_message(status)
    elif old_password != result[1]:
        status = f"H-Have you lied to me slash commander-kun? That password wasn't correct for the kingdom of {kingdom}!"
        await ctx.response.send_message(status)
    elif result is not None and result[1] == old_password:
        await Event.modify_kingdom(self, old_kingdom, new_kingdom, new_password, new_government, new_alignment, guild_id, author)
        status = f"the specified kingdom of {old_kingdom} has been modified with the relevant changes to make it into {new_kingdom}"
        await ctx.response.send_message(status)


@kingdom.command()
async def display(ctx: commands.Context, current_page: int = 1):
    """This displays all kingdoms stored in the database"""
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    buttons = ["⏪", "⬅", "➡", "⏩"]  # skip to start, left, right, skip to end
    cursor.execute(f"SELECT COUNT(Kingdom) FROM Kingdoms")
    kingdom_count = cursor.fetchone()
    max_page = math.ceil(kingdom_count[0] / 5)
    if current_page >= max_page:
        current_page = max_page
    low = 1 + ((current_page-1) * 5)
    high = 5 + ((current_page-1) * 5)
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    decay = cursor.fetchone()
    if decay[0]:  # IF THE SERVER HAS DECAY ON
        cursor.execute(f"""SELECT Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"Kingdoms page {current_page}", description=f'This is list of kingdoms', colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f'Kingdom info', value=f'**Kingdom**: {result[0]}, **Govt**: {result[1]} **Alignment**: {result[2]}', inline=False)
            embed.add_field(name=f'Kingdom Control', value=f'**Control DC**: {result[3]}, **BP**: {result[4]}')
            embed.add_field(name=f'Kingdom Stats', value=f'**Hex**: {result[6]} **Pop**: {result[7]} **Cons**: {result[13]}')
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
                    cursor.execute(f"SELECT Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}")
                    edit_pull = cursor.fetchall()
                    embed = discord.Embed(title=f"Kingdoms page {current_page}", description=f'This is list of kingdoms', colour=discord.Colour.blurple())
                    for result in edit_pull:
                        embed.add_field(name=f'Kingdom info',
                                        value=f'**Kingdom**: {result[0]}, **Govt**: {result[1]} **Alignment**: {result[2]}',
                                        inline=False)
                        embed.add_field(name=f'Kingdom Control',
                                        value=f'**Control DC**: {result[3]}, **BP**: {result[4]}',
                                        inline=True)
                        embed.add_field(name=f'Kingdom Stats',
                                        value=f'**Hex**: {result[6]} **Pop**: {result[7]} **Cons**: {result[13]}',
                                        inline=True)
                    await msg.edit(embed=embed)
    if not decay[0]:  # IF THE SERVER HAS DECAY OFF
        cursor.execute(f"""SELECT Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}""")
        pull = cursor.fetchall()
        embed = discord.Embed(title=f"Kingdoms page {current_page}", description=f'This is list of kingdoms', colour=discord.Colour.blurple())
        for result in pull:
            embed.add_field(name=f'Kingdom info', value=f'**Kingdom**: {result[0]}, **Govt**: {result[1]} **Alignment**: {result[2]}', inline=False)
            embed.add_field(name=f'Kingdom Control', value=f'**Control DC**: {result[3]}, **BP**: {result[4]}, **SP**: {result[5]}')
            embed.add_field(name=f'Kingdom Stats', value=f'**Hex**: {result[6]} **Pop**: {result[7]} **Cons**: {result[13]}')
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
                    cursor.execute(f"SELECT Kingdom, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms WHERE ROWID BETWEEN {low} and {high}")
                    edit_pull = cursor.fetchall()
                    embed = discord.Embed(title=f"Kingdoms page {current_page}", description=f'This is list of kingdoms', colour=discord.Colour.blurple())
                    for result in edit_pull:
                        embed.add_field(name=f'Kingdom info',
                                        value=f'**Kingdom**: {result[0]}, **Govt**: {result[1]} **Alignment**: {result[2]}',
                                        inline=False)
                        embed.add_field(name=f'Kingdom Control',
                                        value=f'**Control DC**: {result[3]}, **BP**: {result[4]}, **SP**: {result[5]}',
                                        inline=True)
                        embed.add_field(name=f'Kingdom Stats',
                                        value=f'**Hex**: {result[6]} **Pop**: {result[7]} **Cons**: {result[13]}',
                                        inline=True)
                    await msg.edit(embed=embed)
"""This is a shop"""


@kingdom.command()
async def detail(ctx: commands.Context, kingdom: str, custom_stats: bool = False):
    """This displays the detailed information of a specific kingdom"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    guild_id = ctx.guild_id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if custom_stats:
        cursor.execute(
            f"SELECT Control_DC, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms_Custom where Kingdom = '{kingdom}'")
        kingdom_info = cursor.fetchone()
        if kingdom_info is None:
            await ctx.response.send_message(f'The kingdom of {kingdom_info} could not be found.')
        if kingdom_info is not None:
            embed = discord.Embed(title=f"Kingdom of {kingdom}", description=f'Here is the full view of this Custom Information for this kingdom', colour=discord.Colour.blurple())
            embed.add_field(name=f'Control_DC', value=f'{kingdom_info[0]}')
            embed.add_field(name=f'Economy', value=f'{kingdom_info[1]}')
            embed.add_field(name=f'Loyalty', value=f'{kingdom_info[2]}')
            embed.add_field(name=f'Stability', value=f'{kingdom_info[3]}')
            embed.add_field(name=f'Fame', value=f'{kingdom_info[4]}')
            embed.add_field(name=f'Unrest', value=f'{kingdom_info[5]}')
            embed.add_field(name=f'Consumption', value=f'{kingdom_info[6]}')
            await ctx.response.send_message(embed=embed)
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    decay = cursor.fetchone()
    if decay[0]:
        if not custom_stats:
            cursor.execute(f"""SELECT Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
            kingdom_info = cursor.fetchone()
            if kingdom_info is None:
                await ctx.response.send_message(f'The kingdom of {kingdom} could not be found.')
            if kingdom_info is not None:
                embed = discord.Embed(title=f"Kingdom of {kingdom}", description=f'Here is the full view of this kingdom', colour=discord.Colour.blurple())
                embed.add_field(name=f'Government', value=f'{kingdom_info[0]}')
                embed.add_field(name=f'Alignment', value=f'{kingdom_info[1]}')
                embed.add_field(name=f'Control_DC', value=f'{kingdom_info[2]}')
                embed.add_field(name=f'Build_Points', value=f'{kingdom_info[3]}')
                embed.add_field(name=f'Stabilization_Points', value=f'{kingdom_info[4]}')
                embed.add_field(name=f'Size', value=f'{kingdom_info[5]}', inline=False)
                embed.add_field(name=f'Population', value=f'{kingdom_info[6]}')
                embed.add_field(name=f'Economy', value=f'{kingdom_info[7]}')
                embed.add_field(name=f'Loyalty', value=f'{kingdom_info[8]}')
                embed.add_field(name=f'Stability', value=f'{kingdom_info[9]}')
                embed.add_field(name=f'Fame', value=f'{kingdom_info[10]}')
                embed.add_field(name=f'Unrest', value=f'{kingdom_info[11]}')
                embed.add_field(name=f'Consumption', value=f'{kingdom_info[12]}')
                await ctx.response.send_message(embed=embed)
    if not decay[0]:
        if not custom_stats:
            cursor.execute(f"""SELECT Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
            kingdom_info = cursor.fetchone()
            if kingdom_info is None:
                await ctx.response.send_message(f'The kingdom of {kingdom} could not be found.')
            if kingdom_info is not None:
                embed = discord.Embed(title=f"Kingdom of {kingdom}", description=f'Here is the full view of this kingdom', colour=discord.Colour.blurple())
                embed.add_field(name=f'Government', value=f'{kingdom_info[0]}')
                embed.add_field(name=f'Alignment', value=f'{kingdom_info[1]}')
                embed.add_field(name=f'Control_DC', value=f'{kingdom_info[2]}')
                embed.add_field(name=f'Build_Points', value=f'{kingdom_info[3]}')
                embed.add_field(name=f'Size', value=f'{kingdom_info[5]}', inline=False)
                embed.add_field(name=f'Population', value=f'{kingdom_info[6]}')
                embed.add_field(name=f'Economy', value=f'{kingdom_info[7]}')
                embed.add_field(name=f'Loyalty', value=f'{kingdom_info[8]}')
                embed.add_field(name=f'Stability', value=f'{kingdom_info[9]}')
                embed.add_field(name=f'Fame', value=f'{kingdom_info[10]}')
                embed.add_field(name=f'Unrest', value=f'{kingdom_info[11]}')
                embed.add_field(name=f'Consumption', value=f'{kingdom_info[12]}')
                await ctx.response.send_message(embed=embed)

    cursor.close()
    db.close()
"""THIS CALLS FOR A SINGULAR KINGDOM OR IT'S CUSTOM INFORMATION"""


@kingdom.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def bp(interaction: discord.Interaction, kingdom: str, password: str, character_name: str, amount: int):
    """This modifies the number of build points in a kingdom"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    password = str.replace(password, ";", "")
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom, Password, Build_Points FROM Kingdoms where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
    result = cursor.fetchone()
    sql = f"""Select True_Character_Name, Gold from Player_Characters where Player_Name = ? and Character_Name = ? OR Nickname = ?"""
    val = (author, character_name, character_name)
    cursor.execute(sql, val)
    character_info = cursor.fetchone()
    if character_info is None:
        await interaction.response.send_message(f"Falsehoods! the Character of {character_name} either doesn't exist or belong to {author}!")
    elif character_info is not None:
        cost = amount * 4000
        gold_value = character_info[1] - cost
        if gold_value < 0:
            await interaction.response.send_message(f"Sell yourself into slavery if you want to buy these points! We don't accept debt at this shop!")
        if gold_value >= 0:
            if result is None:
                await interaction.response.send_message(f"Bollocks! The kingdom of {kingdom} was not a valid kingdom to give building points to!")
                return
            if result[1] != password:
                await interaction.response.send_message(f"The password provided for the kingdom of {kingdom} was inaccurate!!")
            if result is not None and result[1] == password:
                build_points = result[2] + amount
                if build_points < 0:
                    await interaction.response.send_message(f"Impossible! the kingdom of {kingdom} would have {build_points} remaining build points and go into anarchy!!")
                if build_points >= 0:
                    await Event.adjust_build_points(self, kingdom, amount, guild_id, character_info[0], author)
                    await interaction.response.send_message(f"the kingdom of {kingdom} has been adjusted by {amount} build points and has a new value of {build_points}! {character_info[0]} has been charged {cost} GP leaving {gold_value} remaining!")
"""We can make this ALL settlements for that kingdom, or a specific settlement"""


@kingdom.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def sp(interaction: discord.Interaction, kingdom: str, password: str, character_name: str, amount: int):
    """This modifies the Stability Points for a kingdom"""
    kingdom = str.replace(str.title(kingdom), ";", "")
    password = str.replace(password, ";", "")
    character_name = str.replace(str.replace(unidecode(str.title(character_name)), ";", ""), ")", "")
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    decay = cursor.fetchone()
    if decay[0]:  # IF THE SERVER HAS DECAY ON
        cursor.execute(f"""SELECT Kingdom, Password, Stabilization_Points FROM Kingdoms where Kingdom = '{kingdom}'""", {'Kingdom': kingdom})
        result = cursor.fetchone()
        sql = f"""Select True_Character_Name, Gold from Player_Characters where Character_Name = ? or Nickname = ?"""
        val = (character_name, character_name)
        cursor.execute(sql, val)
        character_info = cursor.fetchone()
        cost = amount * 4000
        gold_value = character_info[1] - cost
        if character_info is None:
            await interaction.response.send_message(f"Falsehoods! the Character of {character_name} either doesn't exist or belong to {author}!")
        elif character_info is not None:
            if gold_value < 0:
                await interaction.response.send_message(f"Sell yourself into slavery if you want to buy these points! We don't accept debt at this shop!")
            elif gold_value >= 0:
                if result is None:
                    await interaction.response.send_message(f"You fool! The kingdom of {kingdom} a valid kingdom to give building points to!")
                    return
                if result[1] != password:
                    await interaction.response.send_message(f"The password provided for the kingdom of {kingdom} was inaccurate!!")
                if result is not None and result[1] == password:
                    stabilization_points = result[2] + amount
                    if stabilization_points < 0:
                        await interaction.response.send_message(f"Impossible! the kingdom of {kingdom} would have {stabilization_points} remaining stabilization_points and go into anarchy!!")
                    if stabilization_points >= 0:
                        await Event.adjust_stabilization_points(self, kingdom, amount, guild_id, author, character_info[0])
                        await interaction.response.send_message(f"The kingdom of {kingdom} has been adjusted by {amount} Stabilization Points and has a new value of {stabilization_points}! {character_info[0]} has been charged {cost} GP leaving {gold_value} remaining!")
        if not decay[0]:
            await interaction.response.send_message(f"this server does not have decay enabled!")
"""We can make this ALL settlements for that kingdom, or a specific settlement"""

