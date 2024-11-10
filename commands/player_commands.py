import typing

import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import List, Optional
import aiosqlite
import pytz
import datetime
from zoneinfo import ZoneInfo
import logging
from dateutil import parser
import os

os.chdir("C:\\pathparser")

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize the timezone cache
timezone_cache = sorted(pytz.all_timezones)

# Define regions
regions = {
    'Africa', 'America', 'Antarctica', 'Asia', 'Atlantic',
    'Australia', 'Europe', 'Indian', 'Pacific', 'Etc'
}

# Create a mapping of regions to their respective timezones
region_timezones = {region: [tz for tz in timezone_cache if tz.startswith(f"{region}/")] for region in regions}


# Utility functions
def get_next_weekday(weekday: int) -> datetime.date:
    """Return the date of the next specified weekday (0=Monday, 6=Sunday)."""
    today = datetime.datetime.now().date()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)


def parse_time_input(time_str: str) -> Optional[datetime.time]:
    """Parse time input in various formats and return a time object."""
    try:
        dt = parser.parse(time_str, fuzzy=True)
        return dt.time()
    except (parser.ParserError, ValueError):
        return None


# Custom Select Menus
class ContinentSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Africa'),
            discord.SelectOption(label='America'),
            discord.SelectOption(label='Antarctica'),
            discord.SelectOption(label='Asia'),
            discord.SelectOption(label='Atlantic'),
            discord.SelectOption(label='Australia'),
            discord.SelectOption(label='Europe'),
            discord.SelectOption(label='Indian'),
            discord.SelectOption(label='Pacific'),
            discord.SelectOption(label='Etc'),
        ]
        super().__init__(placeholder="Select your region...", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            self.view.region = self.values[0]
            await self.view.update_timezone_select(interaction)
        except Exception as e:
            logging.exception("Error in ContinentSelect callback")
            await interaction.response.send_message(
                "An error occurred while selecting your region.", ephemeral=True
            )
            self.view.stop()


class TimezoneSelect(discord.ui.Select):
    def __init__(self, options: List[discord.SelectOption]):
        super().__init__(placeholder="Select your timezone...", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            selected_timezone = self.values[0]
            if selected_timezone == "more":
                # Prompt user to enter their timezone manually
                await interaction.response.send_message(
                    "Please enter your timezone manually using the `/timesheet` command with your timezone.",
                    ephemeral=True
                )
                self.view.stop()
                return

            self.view.timezone = selected_timezone
            await self.view.update_day_select(interaction)
        except Exception as e:
            logging.exception("Error in TimezoneSelect callback")
            await interaction.response.send_message(
                "An error occurred while selecting your timezone.", ephemeral=True
            )
            self.view.stop()


class DaySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Monday', value='Monday'),
            discord.SelectOption(label='Tuesday', value='Tuesday'),
            discord.SelectOption(label='Wednesday', value='Wednesday'),
            discord.SelectOption(label='Thursday', value='Thursday'),
            discord.SelectOption(label='Friday', value='Friday'),
            discord.SelectOption(label='Saturday', value='Saturday'),
            discord.SelectOption(label='Sunday', value='Sunday'),
        ]
        super().__init__(placeholder='Select a day...', options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            self.view.day = self.values[0]
            await self.view.update_time_select(interaction, time_type="start")
        except Exception as e:
            logging.exception("Error in DaySelect callback")
            await interaction.response.send_message(
                "An error occurred while selecting the day.", ephemeral=True
            )
            self.view.stop()


class TimeSelect(discord.ui.Select):
    def __init__(self, label: str, time_type: str):
        self.time_type = time_type
        options = [
                      discord.SelectOption(label=f"{hour:02d}:00", value=f"{hour:02d}:00") for hour in range(0, 24)
                  ] + [
                      discord.SelectOption(label=f"{hour:02d}:30", value=f"{hour:02d}:30") for hour in range(0, 24)
                  ]
        super().__init__(placeholder=label, options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            selected_time = self.values[0]
            if self.time_type == "start":
                self.view.start_time = selected_time
                await self.view.update_time_select(interaction, time_type="end")
            elif self.time_type == "end":
                self.view.end_time = selected_time
                await self.view.process_availability(interaction)
        except Exception as e:
            logging.exception("Error in TimeSelect callback")
            await interaction.response.send_message(
                "An error occurred while selecting the time.", ephemeral=True
            )
            self.view.stop()


# Custom Buttons for Adding Multiple Time Slots
class AddAnotherSlotButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Add Another Time Slot", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        try:
            # Reset the view to allow adding another time slot
            self.view.clear_items()
            self.view.add_item(DaySelect())
            self.view.add_item(TimeSelect(label="Select Start Time", time_type="start"))
            await interaction.response.edit_message(content="Select the day of the week for the new time slot:",
                                                    view=self.view)
        except Exception as e:
            logging.exception("Error in AddAnotherSlotButton callback")
            await interaction.response.send_message(
                "An error occurred while adding another time slot.", ephemeral=True
            )
            self.view.stop()


class FinishButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Finish", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        try:
            await self.view.process_all_availability(interaction)
        except Exception as e:
            logging.exception("Error in FinishButton callback")
            await interaction.response.send_message(
                "An error occurred while finalizing your availability.", ephemeral=True
            )
            self.view.stop()


# Enhanced AvailabilityView with Multiple Time Slots
class AvailabilityView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)  # Extended timeout for multiple entries
        self.region: Optional[str] = None
        self.timezone: Optional[str] = None
        self.day: Optional[str] = None
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.guild_id: Optional[int] = None
        self.user_id: Optional[int] = None
        self.time_slots: List[dict] = []

        # Start with continent selection
        self.add_item(ContinentSelect())

    async def on_timeout(self):
        """Disable all components when the view times out."""
        for item in self.children:
            item.disabled = True
        # Optionally, edit the message to inform the user
        if self.message:
            await self.message.edit(content="This interaction has timed out.", view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the initiating user can interact with the view."""
        if self.user_id and interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You cannot interact with this view.", ephemeral=True
            )
            return False
        return True

    async def update_timezone_select(self, interaction: discord.Interaction):
        try:
            # Remove the continent select menu
            self.clear_items()
            # Get filtered timezones from the cached mapping
            filtered_timezones = region_timezones.get(self.region, [])
            if not filtered_timezones:
                await interaction.response.send_message("No timezones found for the selected region.", ephemeral=True)
                self.stop()
                return

            # Limit to 24 options and add "More..." as the 25th option
            display_timezones = filtered_timezones[:24]
            options = [discord.SelectOption(label=tz, value=tz) for tz in display_timezones]
            if len(filtered_timezones) > 24:
                options.append(discord.SelectOption(label="More...", value="more"))

            self.add_item(TimezoneSelect(options=options))
            await interaction.response.edit_message(content="Select your timezone:", view=self)
        except Exception as e:
            logging.exception("Error in update_timezone_select")
            await interaction.response.send_message(
                "An error occurred while updating timezone selection.", ephemeral=True
            )
            self.stop()

    async def update_day_select(self, interaction: discord.Interaction):
        try:
            # Remove the timezone select menu
            self.clear_items()
            # Add the day select menu
            self.add_item(DaySelect())
            await interaction.response.edit_message(content="Select the day of the week:", view=self)
        except Exception as e:
            logging.exception("Error in update_day_select")
            await interaction.response.send_message(
                "An error occurred while updating day selection.", ephemeral=True
            )
            self.stop()

    async def update_time_select(self, interaction: discord.Interaction, time_type: str):
        try:
            # Remove previous time select menus
            self.clear_items()
            # Add time select menus based on time_type
            if time_type == "start":
                self.add_item(TimeSelect(label="Select Start Time", time_type="start"))
                await interaction.response.edit_message(content="Select your start time:", view=self)
            elif time_type == "end":
                self.add_item(TimeSelect(label="Select End Time", time_type="end"))
                # Add Finish button after selecting end time
                self.add_item(FinishButton())
                await interaction.response.edit_message(content="Select your end time:", view=self)
        except Exception as e:
            logging.exception("Error in update_time_select")
            await interaction.response.send_message(
                "An error occurred while updating time selection.", ephemeral=True
            )
            self.stop()

    async def process_availability(self, interaction: discord.Interaction):
        try:
            # All selections have been made, process the data
            if not all([self.timezone, self.day, self.start_time, self.end_time]):
                await interaction.response.send_message(
                    "Incomplete availability information.", ephemeral=True
                )
                return

            # Convert day string to integer
            days = {
                'Monday': 1, 'Tuesday': 2, 'Wednesday': 3,
                'Thursday': 4, 'Friday': 5, 'Saturday': 6,
                'Sunday': 7
            }
            day_value = days.get(self.day)
            if not day_value:
                await interaction.response.send_message(
                    f"Invalid day: {self.day}", ephemeral=True
                )
                return

            # Parse times
            start_time_parsed = parse_time_input(self.start_time)
            end_time_parsed = parse_time_input(self.end_time)
            if not start_time_parsed or not end_time_parsed:
                await interaction.response.send_message(
                    "Invalid start or end time format.", ephemeral=True
                )
                return

            # Get the next occurrence of the selected day
            next_date = get_next_weekday(day_value - 1)  # Adjust for Python's weekday (0=Monday)

            # Create datetime objects with timezone
            try:
                tzinfo = ZoneInfo(self.timezone)
            except Exception:
                await interaction.response.send_message(
                    "Invalid timezone selected.", ephemeral=True
                )
                return

            start_datetime = datetime.datetime.combine(next_date, start_time_parsed, tzinfo=tzinfo)
            end_datetime = datetime.datetime.combine(next_date, end_time_parsed, tzinfo=tzinfo)

            # Adjust end time if it's before start time
            if end_datetime <= start_datetime:
                end_datetime += datetime.timedelta(days=1)

            # Convert to UTC
            start_datetime_utc = start_datetime.astimezone(datetime.timezone.utc)
            end_datetime_utc = end_datetime.astimezone(datetime.timezone.utc)

            # Extract hours and minutes for storage
            start_hours = start_datetime_utc.hour
            start_minutes = start_datetime_utc.minute
            end_hours = end_datetime_utc.hour
            end_minutes = end_datetime_utc.minute

            # Add the time slot to the list
            self.time_slots.append({
                'day': self.day,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'timezone': self.timezone
            })

            # Reset selections for another entry
            self.day = None
            self.start_time = None
            self.end_time = None
            self.timezone = None

            # Ask if the user wants to add another time slot
            self.clear_items()
            self.add_item(AddAnotherSlotButton())
            self.add_item(FinishButton())
            await interaction.response.edit_message(
                content="Time slot added! Would you like to add another time slot or finish?",
                view=self
            )
        except Exception as e:
            logging.exception("Error in process_availability")
            await interaction.response.send_message(
                "An unexpected error occurred while processing your availability.", ephemeral=True
            )
            self.stop()

    async def process_all_availability(self, interaction: discord.Interaction):
        try:
            if not self.time_slots:
                await interaction.response.send_message(
                    "No availability entries to save.", ephemeral=True
                )
                return

            async with aiosqlite.connect(f"Pathparser_{self.guild_id}.sqlite") as db:
                for slot in self.time_slots:
                    user_name = interaction.user.name
                    day_value = {
                        'Monday': 1, 'Tuesday': 2, 'Wednesday': 3,
                        'Thursday': 4, 'Friday': 5, 'Saturday': 6,
                        'Sunday': 7
                    }.get(slot['day'])

                    # Parse times
                    start_time_parsed = parse_time_input(slot['start_time'])
                    end_time_parsed = parse_time_input(slot['end_time'])
                    if not start_time_parsed or not end_time_parsed:
                        await interaction.response.send_message(
                            f"Invalid time format for {slot['day']}. Skipping.", ephemeral=True
                        )
                        continue

                    # Get the next occurrence of the selected day
                    next_date = get_next_weekday(day_value - 1)  # Adjust for Python's weekday (0=Monday)

                    # Create datetime objects with timezone
                    try:
                        tzinfo = ZoneInfo(slot['timezone'])
                    except Exception:
                        await interaction.response.send_message(
                            f"Invalid timezone {slot['timezone']} for {slot['day']}. Skipping.", ephemeral=True
                        )
                        continue

                    start_datetime = datetime.datetime.combine(next_date, start_time_parsed, tzinfo=tzinfo)
                    end_datetime = datetime.datetime.combine(next_date, end_time_parsed, tzinfo=tzinfo)

                    # Adjust end time if it's before start time
                    if end_datetime <= start_datetime:
                        end_datetime += datetime.timedelta(days=1)

                    # Convert to UTC
                    start_datetime_utc = start_datetime.astimezone(datetime.timezone.utc)
                    end_datetime_utc = end_datetime.astimezone(datetime.timezone.utc)

                    # Extract hours and minutes for storage
                    start_hours = start_datetime_utc.hour
                    start_minutes = start_datetime_utc.minute
                    end_hours = end_datetime_utc.hour
                    end_minutes = end_datetime_utc.minute

                    # Insert or update availability
                    await db.execute(
                        """
                        INSERT INTO Player_Availability
                        (player_name, day, start_hour, start_minute, end_hour, end_minute, timezone)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(player_name, day) DO UPDATE SET
                            start_hour=excluded.start_hour,
                            start_minute=excluded.start_minute,
                            end_hour=excluded.end_hour,
                            end_minute=excluded.end_minute,
                            timezone=excluded.timezone
                        """,
                        (user_name, day_value, start_hours, start_minutes, end_hours, end_minutes, slot['timezone'])
                    )
                await db.commit()

            # Inform the user
            embed = discord.Embed(
                title="Availability Updated",
                description=f"Your availability has been successfully updated.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            self.stop()
        except Exception as e:
            logging.exception("Error in process_all_availability")
            await interaction.response.send_message(
                "An unexpected error occurred while finalizing your availability.", ephemeral=True
            )
            self.stop()


async def player_signup(guild: discord.Guild, thread_id: int, session_name: str, session_id: int, player_id: int, character_name: str, warning_duration: typing.Optional[int]) -> bool:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild.id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute("Select True_Character_Name, title, level, tier, gold, gold_value, tradition_name, tradition_link, template_name, template_link, mythweavers, image_link, color, description from Player_Characters where Player_ID = ? and Character_Name = ?", (player_id, character_name))
            character_info = await cursor.fetchone()
            if character_info:
                (character_name, level, tier, gold, gold_value, tradition_name, tradition_link, template_name, template_link, mythweavers, image_link, color, description, titles, flux, oath) = character_info
                await cursor.execute(
                    """INSERT INTO Sessions_Signups (Session_ID, Session_Name, Player_Name, Player_ID, Character_Name, Level, Gold_Value, Tier, Notification_Warning) Values (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (session_id, session_name, player_id, character_name, level, gold_value, tier, warning_duration)
                )
                await db.commit()
                thread = guild.get_thread(thread_id)
                if not thread:
                    thread = await guild.fetch_channel(thread_id)
                if thread:
                    embed = signup_embed(character_name, titles, level, tier, gold, gold_value, tradition_name, tradition_link, template_name, template_link, mythweavers, image_link, color, description)
                    await thread.send(embed=embed, content=f"<@{player_id}>", allowed_mentions=discord.AllowedMentions(users=True))
                    return True
                else:
                    raise ValueError(f"Thread {thread_id} not found in guild {guild.id}")
            else:
                raise ValueError(f"Character {character_name} not found for player {player_id}")
    except (aiosqlite.Error, TypeError) as e:
        logging.exception(f"Failed to sign up player <@{player_id}> for session {session_name} ({session_id})")



def signup_embed(character_name: str, title: str, level: int, tier: int, gold: int, gold_value: int, tradition_name: str,
                 tradition_link: str, template_name: str, template_link: str, mythweavers: str, image_link: str,
                 color: str, description: str) -> discord.Embed:
    try:
        title_field = f"{character_name} would like to participate" if title is None else f"{title} {character_name} would like to participate"
        embed = discord.Embed(title=title_field, color=int(color[1:], 16),url=mythweavers)
        embed.set_thumbnail(url=image_link)
        embed.add_field(name="Information", value=f"**Level**: {level}, **Mythic Tier**: {tier}", inline=True)
        embed.add_field(name="illiquid Wealth", value=f"**GP**: {round(gold_value - gold, 2)}", inline=True)
        additional_info = f"**Tradition**: [{tradition_name}]({tradition_link})" if tradition_name else ""
        additional_info += '\r\n' if tradition_name and template_name else ""
        additional_info += f"**Template**: [{template_name}]({template_link})" if template_name else ""
        if tradition_name or template_name:
            embed.add_field(name="Additional Info", value=additional_info, inline=False)
        embed.set_footer(text=description)
        return embed
    except ValueError as e:
        logging.exception(f"Failed to create signup embed for character {character_name}")



async def player_leave_session(guild_id, session_id, player_name) -> bool:
    try:
        async with aiosqlite.connect(f"Pathparser_{guild_id}.sqlite") as db:
            cursor = await db.cursor()
            await cursor.execute(
                "DELETE FROM Sessions_Signups WHERE Session_ID = ? AND Player_Name = ?",
                (session_id, player_name)
            )
            await db.commit()
            await cursor.execute(
                "DELETE FROM Sessions_Participants WHERE Session_ID = ? AND Player_Name = ?",
                (session_id, player_name)
            )
            await db.commit()
            return True
    except aiosqlite.Error as e:
        logging.exception(f"Failed to remove player {player_name} from session {session_id}")


"""@player.command()
@app_commands.autocomplete(character_name=own_character_select_autocompletion)
async def join(interaction: discord.Interaction, session_id: int, character_name: str):
    "PLAYER: Offer your Participation in a session."
    guild_id = interaction.guild_id
    author = interaction.user.name
    author_id = interaction.user.id
    user = interaction.user
    guild = interaction.guild
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    await interaction.response.defer(thinking=True, ephemeral=True)
    cursor.execute("SELECT Session_Name, Play_location, Play_Time, game_link, Session_Range_ID, Session_Range, Session_Thread, overflow FROM Sessions WHERE Session_ID = '{session_id}' AND IsActive = 1")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.followup.send(f"No active session with Session ID: {session_id} can be found!")
    else:
        quest_thread = guild.get_thread(session_info[6])
        role = interaction.guild.get_role(session_info[4])
        if role in user.roles or session_info[7] == 4 or session_info[7] == 3 or session_info[7] == 2:
            sql = "SELECT Character_Name, Level, Gold_Value, Tier from Player_Characters where Player_Name = ? and Character_Name = ? OR Nickname = ?"
            val = (author, character_name, character_name)
            cursor.execute(sql, val)
            character_info = cursor.fetchone()
            if character_info is None:
                await interaction.followup.send(f"Falsehoods! the Character of {character_name} either doesn't exist or belong to {author}!")
            if character_info is not None:
                cursor.execute("SELECT Level, Role_Name from Level_Range WHERE Role_ID = {session_info[4]}")
                level_range_info = cursor.fetchone()
                print(session_info[7])
                if level_range_info is None or session_info[7] == 4:
                    cursor.execute("SELECT Character_Name from Sessions_Participants where Player_name = '{author}' and Session_ID = {session_id}")
                    participation = cursor.fetchone()
                    cursor.execute("SELECT Character_Name from Sessions_Signups where Player_name = '{author}' AND Session_ID = {session_id}")
                    signups = cursor.fetchone()
                    if participation is None and signups is None:
                        await Event.session_join(self, guild_id, session_info[0], session_id, author, author_id, character_info[0], character_info[1], character_info[2], character_info[3])
                        sql = "SELECT Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Gold_Value, Oath from Player_characters WHERE Character_Name = ? OR Nickname = ?"
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
                        cursor.execute("SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_ID = {session_info[4]}")
                        new_level_range_info = cursor.fetchone()
                        cursor.execute("SELECT Role_Name from Level_Range WHERE level = {new_level_range_info[0]-1}")
                        overflow_level_role = cursor.fetchone()
                        overflow_level_role = overflow_level_role if overflow_level_role is not None else new_level_range_info
                        cursor.execute("SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_Name = ?", (overflow_level_role[0],))
                        overflow_level_range_info = cursor.fetchone()
                        overflow_level_range_info = overflow_level_range_info if overflow_level_range_info[0] is not None else new_level_range_info
                        level_range_validation = 1 if overflow_level_range_info is not None and overflow_level_range_info[0] <= character_info[1] <= new_level_range_info[1] else 0
                    elif session_info[7] == 2:
                        cursor.execute("SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_ID = {session_info[4]}")
                        new_level_range_info = cursor.fetchone()
                        cursor.execute("SELECT Role_Name from Level_Range WHERE level = {new_level_range_info[1] + 1}")
                        overflow_level_role = cursor.fetchone()
                        overflow_level_role = overflow_level_role if overflow_level_role is not None else new_level_range_info
                        cursor.execute("SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_Name = ?", (overflow_level_role[0],))
                        overflow_level_range_info = cursor.fetchone()
                        overflow_level_range_info = overflow_level_range_info if overflow_level_range_info[0] is not None else new_level_range_info
                        level_range_validation = 1 if overflow_level_range_info is not None and new_level_range_info[0] <= character_info[1] <= overflow_level_range_info[1] else 0
                    else:
                        cursor.execute("SELECT min(level), max(level) Role_Name from Level_Range WHERE Role_ID = {session_info[4]} AND Level = {character_info[1]}")
                        new_level_range_info = cursor.fetchone()
                        level_range_validation = 1 if new_level_range_info is not None else 0
                    if level_range_validation != 1:
                        await interaction.followup.send(f"{character_info[0]} is level {character_info[1]} which is not inside the level range of {level_range_info[1]}!", ephemeral=True)
                    else:
                        cursor.execute("SELECT Character_Name from Sessions_Participants where Player_name = '{author}' and Session_ID = {session_id}")
                        participation = cursor.fetchone()
                        cursor.execute("SELECT Character_Name from Sessions_Signups where Player_name = '{author}' and Session_ID = {session_id}")
                        signups = cursor.fetchone()
                        if participation is None and signups is None:
                            await Event.session_join(self, guild_id, session_info[0], session_id, author, author_id, character_info[0], character_info[1], character_info[2], character_info[3])
                            sql = "SELECT True_Character_Name, Nickname, Titles, Description, Level, Tier, Milestones, Milestones_Required, Trials, Trials_required, Gold, Color, Mythweavers, Image_Link, Flux, Tradition_Name, Tradition_Link, Template_Name, Template_Link, Gold_Value, Oath from Player_characters WHERE Character_Name = ? OR Nickname = ?"
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
    "PLAYER: Rescind your Participation in a session."
    guild_id = interaction.guild_id
    author = interaction.user.name
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    cursor.execute("SELECT Session_Name, Play_location, Play_Time, Game_Link FROM Sessions WHERE Session_ID = '{session_id}'")
    session_info = cursor.fetchone()
    if session_info is None:
        await interaction.response.send_message(f"No active session with {session_id} can be found!")
    if session_info is not None:
        cursor.execute("SELECT Character_Name, Level, Effective_Wealth from Sessions_Signups where Player_Name = '{author}'")
        character_info = cursor.fetchone()
        if character_info is None:
            cursor.execute("SELECT Character_Name, Level, Effective_Wealth from Sessions_Participants where Player_Name = '{author}'")
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
    "ALL: THIS COMMAND DISPLAYS SESSION INFORMATION"
    guild_id = ctx.guild.id
    db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
    cursor = db.cursor()
    if group == 1:
        group = 1
    else:
        group = group.value
    cursor.execute("SELECT GM_Name, Session_Name, Session_Range, Play_location, Play_Time, Overview, Description, Message, IsActive FROM Sessions WHERE Session_ID = {session_id}")
    session_info = cursor.fetchone()
    if session_info is not None:
        cursor.execute("SELECT Search FROM Admin WHERE Identifier = 'Sessions_Channel'")
        sessions_channel = cursor.fetchone()
        session_channel = await bot.fetch_channel(sessions_channel[0])
        msg = await session_channel.fetch_message(session_info[7])
        embed = discord.Embed(title=f"{session_info[1]}", description=f'[Session overview](<{msg.jump_url}>)!',colour=discord.Colour.blurple())
        if session_info[8] == 1:
            embed.add_field(name=f"Active Session Info", value=f"**GM**: {session_info[0]}, **Session Range**: {session_info[2]}, **Play_Location**: {session_info[3]}, **Play_Time**: <t:{session_info[4]}:D>", inline=False)
            x = 0
            print(group)
            if group == 1 or group == 2:
                cursor.execute("SELECT COUNT(Player_Name) FROM Sessions_Participants WHERE Session_ID = {session_id}")
                total_participants = cursor.fetchone()
                cursor.execute("SELECT Player_Name, Character_Name, Level, Effective_Wealth, Tier, Player_ID FROM Sessions_Participants WHERE Session_ID = {session_id}")
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
                cursor.execute("SELECT COUNT(Player_Name) FROM Sessions_Signups WHERE Session_ID = {session_id}")
                total_participants = cursor.fetchone()
                x = 0 + player_total
                cursor.execute("SELECT Player_Name, Character_Name, Level, Effective_Wealth, Tier, Player_ID FROM Sessions_Signups WHERE Session_ID = {session_id}")
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
            cursor.execute("SELECT Gold, Flux, Easy, Medium, Hard, Deadly, Trials FROM Sessions WHERE Session_ID = {session_id}")
            session_reward_info = cursor.fetchone()
            embed.add_field(name=f"Inactive Session Info", value=f"**GM**: {session_info[0]}, **Session Range**: {session_info[2]}, **Play_Location**: {session_info[3]}, **Play_Time**: <t:{session_info[4]}:D>", inline=False)
            embed.add_field(name=f"Milestone Rewards", value=f"**Easy Jobs**: {session_reward_info[2]}, **Medium Jobs**: {session_reward_info[3]}, **Hard_jobs**: {session_reward_info[4]}, **Deadly_Jobs**: {session_reward_info[5]}, **Trials**: {session_reward_info[6]}", inline=False)
            embed.add_field(name=f"Currency Rewards", value=f"**Gold**: {session_reward_info[0]}, **Flux**: {session_reward_info[1]}", inline=False)
            x = 0
            cursor.execute("SELECT COUNT(Player_Name) FROM Sessions_Archive WHERE Session_ID = {session_id}")
            total_participants = cursor.fetchone()
            cursor.execute("SELECT Player_Name, Character_Name, Level, Effective_Gold, Tier, Received_Milestones, Received_Gold, Player_ID FROM Sessions_Archive WHERE Session_ID = {session_id}")
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
