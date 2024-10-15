import discord
from discord.ext import commands

class TestCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Top-level group
    event_group = discord.app_commands.Group(
        name='event',
        description='Commands related to events'
    )

    # Nested group
    settings_group = discord.app_commands.Group(
        name='settings',
        description='Event settings commands',
        parent=event_group
    )

    # Command within the nested group
    @settings_group.command(name='fix_dst', description='Fix DST settings for a guild')
    async def fix_dst(self, interaction: discord.Interaction, guild_id: int):
        """Fixes DST settings for a guild."""
        # Command implementation
        await interaction.response.send_message(f'DST fixed for guild ID: {guild_id}')