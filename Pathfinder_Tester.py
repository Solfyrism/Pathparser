import discord
from discord.ext import commands
from dotenv import load_dotenv; load_dotenv()
import os
from test_functions import TestCommands
from commands.character_commands import CharacterCommands
from commands.admin_commands import AdminCommands
import logging
import shared_functions
intents = discord.Intents.default()
intents.typing = True
intents.message_content = True
intents.members = True
os.chdir("C:\\pathparser")
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    print(f"Logged in as {bot.user.name}")
    await bot.add_cog(TestCommands(bot))
    await bot.add_cog(CharacterCommands(bot))
    await bot.add_cog(AdminCommands(bot))

    await bot.tree.sync()




@bot.event
async def on_disconnect():
    print("Bot is disconnecting.")

bot.run(os.getenv("DISCORD_TOKEN_V2"))
bot.loop.create_task(shared_functions.clear_autocomplete_cache())


logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='pathparser.log',  # Specify the log file name
    filemode='a'  # Append mode
)