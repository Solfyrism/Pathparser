

@overseer.command()
async def help(ctx: commands.Context):
    """Help commands for the associated tree"""
    embed = discord.Embed(title=f"Overseer Help", description=f'This is a list of Overseer help commands', colour=discord.Colour.blurple())
    embed.add_field(name=f'**blueprint_add**', value=f'The command for an overseer to create a new blueprint for players to use..', inline=False)
    embed.add_field(name=f'**blueprint_remove**', value=f'This command removes blueprints from player usage.', inline=False)
    embed.add_field(name=f'**blueprint_modify**', value=f'This command modifies a blueprint that is already in use.', inline=False)
    embed.add_field(name=f'**kingdom_modifiers**', value=f'This command adjusts the custom modifiers associated with a kingdom.', inline=False)
    embed.add_field(name=f'**settlement_modifiers**', value=f'This command adjusts the custom modifiers associated with a settlement.', inline=False)
    embed.add_field(name=f'**settlement_decay**', value=f'This command modifies the multiplier for stabilization points a settlement requires in order to build.', inline=False)
    embed.add_field(name=f'**improvement_add**', value=f'This command adds a new hex improvement for players to build', inline=False)
    embed.add_field(name=f'**improvement_remove**', value=f'This command removes hex improvements from options players can build.', inline=False)
    embed.add_field(name=f'**improvement_modify**', value=f'This command modifies hex improvements that are available to build, or have been built', inline=False)
    embed.add_field(name=f'**kingdom_tables_rebalance**', value=f'Forced the kingdom and settlement tables to rebalance.', inline=False)
    await ctx.response.send_message(embed=embed)


@overseer.command()
async def blueprint_add(ctx: commands.Context, building: str, build_points: int, lots: int, economy: int, loyalty: int, stability: int, fame: int, unrest: int, corruption: int, crime: int, productivity: int, law: int, lore: int, society: int, danger: int, defence: int, base_value: int, spell_casting: int, supply: int, settlement_limit: int, district_limit: int, description: str):
    """This adds a new blueprint for players to build with"""
    building = str.replace(str.title(building), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT building FROM Buildings_Blueprints where building = '{building}' LIMIT 1;""", {'building': building})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"Congratulations you have allowed the construction of **{building}**"
        await Event.create_blueprint(self, building, build_points, lots, economy, loyalty, stability, fame, unrest, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spell_casting, supply, settlement_limit, district_limit, description, guild_id, author)
        await ctx.response.send_message(status)
    if result is not None:
        status = f"you have already allowed the construction of **{building}**"
        await ctx.response.send_message(status)


@overseer.command()
async def blueprint_remove(ctx: commands.Context, building: str):
    """This removes a blueprint from play and refunds some build points used."""
    building = str.replace(str.title(building), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Building FROM Buildings_Blueprints WHERE Building = '{building}'""", {'building': building})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"You have removed the possibility of constructing {building} for all future kingdoms."
        await ctx.response.send_message(status)
    if result is not None:
        status = f"You have done the YEETETH of this particular building which is {building}."
        await Event.remove_blueprint(self, building, guild_id, author)
        await ctx.response.send_message(status)


@overseer.command()
async def blueprint_modify(ctx: commands.Context, building: str, build_points: int, lots: int, economy: int, loyalty: int, stability: int, fame: int, unrest: int, corruption: int, crime: int, productivity: int, law: int, lore: int, society: int, danger: int, defence: int, base_value: int, spellcasting: int, supply: int, settlement_limit: int, district_limit: int, description: str):
    """this modifies a blueprint that is currently in play"""
    building = str.replace(str.title(building), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Building FROM Buildings_Blueprints WHERE Building = '{building}'""", {'Building': building})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"You, like a false god have falsely instructed me to modify this nonexistent {building}."
        await ctx.response.send_message(status)
    if result is not None:
        status = f"The blueprint of {building} has been modified for all times built, and in the records!"
        await Event.modify_blueprint(self, building, build_points, lots, economy, loyalty, stability, fame, unrest, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting, supply, settlement_limit, district_limit, description, guild_id, author)
        await ctx.response.send_message(status)


@overseer.command()
async def kingdom_modifiers(ctx: commands.Context, kingdom: str, control_dc: int, economy: int, loyalty: int, stability: int, fame: int, unrest: int, consumption: int):
    """This will set the custom kingdom values as a new value. it does NOT handle addition or subtraction."""
    kingdom = str.title(kingdom)
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Kingdom, Password FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"the kingdom of {kingdom} which you have attempted to set new modifiers for couldn't be found."
        await ctx.response.send_message(status)
    if result is not None:
        status = f"The kingdom of {kingdom} which you have set new modifiers for has been adjusted"
        await Event.customize_kingdom_modifiers(self, kingdom, control_dc, economy, loyalty, stability, fame, unrest, consumption, guild_id, author)
        await ctx.response.send_message(status)


@overseer.command()
async def settlement_modifiers(ctx: commands.Context, kingdom: str, settlement: str, corruption: int, crime: int, productivity: int, law: int, lore: int, society: int, danger: int, defence: int, base_value: int, spellcasting: int, supply: int):
    """Sets new values for a settlement."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Settlement FROM Settlements WHERE Settlement = '{settlement}' AND Kingdom = '{kingdom}'""")
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        status = f"you cannot apply custom modifiers if the settlement of {settlement} doesn't exist for the kingdom of {kingdom}!"
        await ctx.response.send_message(status)
    if result is not None:
        status = f"You have modified the settlement of {settlement} congratulations!"
        await ctx.response.send_message(status)
        await Event.custom_settlement_modifiers(self, kingdom, settlement, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting, supply, guild_id, author)


@overseer.command()
async def settlement_decay(ctx: commands.Context, kingdom: str, settlement: str, decay: int):
    """This will set the custom decay of a settlement."""
    kingdom = str.replace(str.title(kingdom), ";", "")
    settlement = str.replace(str.title(settlement), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"SELECT Search from Admin where identifier = 'Decay'")
    server_decay = cursor.fetchone()
    if server_decay[0]:  # IF THE SERVER HAS DECAY ON
        cursor = db.cursor()
        cursor.execute(f"""SELECT Kingdom FROM Settlements where Kingdom = '{kingdom}' AND Settlement = '{settlement}'""", {'Kingdom': kingdom, 'Settlement': settlement})
        result = cursor.fetchone()
        if result is None:
            await ctx.response.send_message(f"You have failed to specify a valid settlement to adjust the decay!!")
            return
        if result is not None:
            await Event.settlement_decay_set(self, kingdom, settlement, decay, guild_id, author)
            await ctx.response.send_message(f"The settlement of {settlement} within the kingdom of {kingdom} has had it's decay set to {decay}!")
    if not server_decay[0]:
        await ctx.response.send_message(f"Decay is not enabled in this server!")


@overseer.command()
async def improvement_add(ctx: commands.Context, improvement: str, build_points: int, road_multiplier: int, economy: int, loyalty: int, stability: int, unrest: int, consumption: int, defence: int, taxation: int, cavernous: bool, coastline: bool, desert: bool, forest: bool, hills: bool, jungle: bool, marsh: bool, mountain: bool, plains: bool, water: bool):
    """This will add a new custom improvement for the players to build for hexes"""
    improvement = str.replace(str.title(improvement), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Improvement from Hexes_Improvements where Improvement = '{improvement}'""", {'Improvement': improvement})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is None:
        await Event.add_hex_improvements(self, improvement, build_points, road_multiplier, economy, loyalty, stability, unrest, consumption, defence, taxation, cavernous, coastline, desert, forest, hills, jungle, marsh, mountain, plains, water, guild_id, author)
        status = f"You have allowed the creation the new hex improvement: {improvement}!"
        await ctx.response.send_message(status)
    if result is not None:
        status = f"You cannot add a improvement with the same name of {improvement}!"
        await ctx.response.send_message(status)


@overseer.command()
async def improvement_remove(ctx: commands.Context, improvement: str):
    """This will remove a custom improvement from play for players and delete historical instances of it."""
    improvement = str.replace(str.title(improvement), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Improvement from Hexes_Improvements where Improvement = '{improvement}'""", {'Improvement': improvement})
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result is not None:
        await Event.remove_hex_improvement(self, improvement, guild_id, author)
        status = f"You have removed {improvement} from the list of available improvements."
        await ctx.response.send_message(status)
    if result is None:
        status = f"You cannot remove a thing which doesn't exist!!! or can you? {improvement} was not found."
        await ctx.response.send_message(status)


@overseer.command()
async def improvement_modify(ctx: commands.Context, old_improvement: str, new_improvement: str, new_build_points: int, new_road_multiplier: int, new_economy: int, new_loyalty: int, new_stability: int, new_unrest: int, new_consumption: bool, new_defence: int, new_taxation: int, new_cavernous: bool, new_coastline: bool, new_desert: bool, new_forest: bool, new_hills: bool, new_jungle: bool, new_marsh: bool, new_mountains: bool, new_plains: bool, new_water: bool):
    """This is an overseer command that modifies an existing improvement."""
    new_improvement = str.replace(str.title(new_improvement), ";", "")
    old_improvement = str.replace(str.title(old_improvement), ";", "")
    guild_id = ctx.guild_id
    author = ctx.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute(f"""SELECT Improvement from Hexes_Improvements where Improvement = '{new_improvement}'""", {'Improvement': new_improvement})
    result1 = cursor.fetchone()
    cursor.execute(f"""SELECT Improvement from Hexes_Improvements where Improvement = '{old_improvement}'""", {'Improvement': old_improvement})
    result2 = cursor.fetchone()
    cursor.close()
    db.close()
    if result1 is None:
        status = f"My master, You cannot alter that which doesn't exist. {old_improvement} doesn't exist."
        await ctx.response.send_message(status)
    if result1 is not None:
        if result2 is None:
            status = f"You have made this improvement into something new... something different. {new_improvement} has been altered for all settlements."
            await ctx.response.send_message(status)
            await Event.modify_hex_improvement(self, old_improvement, new_improvement, new_build_points, new_road_multiplier, new_economy, new_loyalty, new_stability, new_unrest, new_consumption, new_defence, new_taxation, new_cavernous, new_coastline, new_desert, new_forest, new_hills, new_jungle, new_marsh, new_mountains, new_plains, new_water, guild_id, author)
        elif result1[0] == result2[0]:
            await Event.modify_hex_improvement(self, old_improvement, new_improvement, new_build_points, new_road_multiplier, new_economy, new_loyalty, new_stability, new_unrest, new_consumption, new_defence, new_taxation, new_cavernous, new_coastline, new_desert, new_forest, new_hills, new_jungle, new_marsh, new_mountains, new_plains, new_water, guild_id, author)
            status = f"You have kept the name the same for this building. The stats of {new_improvement} have been altered.."
            await ctx.response.send_message(status)
        elif result2 is not None:
            status = f"for shame! {new_improvement} already exists! You cannot change something to be the same as another! (no seriously, it breaks shit)"
            await ctx.response.send_message(status)


@overseer.command()
async def kingdom_tables_rebalance(ctx: commands.Context):
    """This will rebalance the existing tables"""
    guild_id = ctx.guild_id
    author = ctx.user.name
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    shutil.copyfile(f"C:/pathparser/pathparser_{guild_id}.sqlite", f"C:/pathparser/pathparser_{guild_id}_{time}.sqlite")
    await Event.balance_tables(self, guild_id, author)
    status = f"TABLE UPDATE HAS BEEN COMPLETED"
    await ctx.response.send_message(status)

