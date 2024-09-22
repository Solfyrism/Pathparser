from math import floor
import sqlite3
from discord.ext import commands
import datetime
import os
from pywaclient.api import BoromirApiClient as WaClient
from google.oauth2 import service_account
from googleapiclient.discovery import build
os.chdir("C:\\pathparser")


def drive_word_document(link):
    SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
    SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=credentials)
    DOCUMENT_ID = link
    document = service.documents().get(documentId=DOCUMENT_ID).execute()
    word_blob = ""
    for element in document.get('body').get('content'):
        if 'paragraph' in element:
            for text_run in element.get('paragraph').get('elements'):
                word_blob += (text_run.get('textRun').get('content'))
    print(word_blob)
    return(word_blob)


def time_to_minutes(t):
    hours, minutes = map(int, t.split(':'))
    return hours * 60 + minutes

class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def create_kingdom(self, kingdom, password, government, alignment, economy, loyalty, stability, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = """INSERT INTO Kingdoms(Kingdom, Password, Government, Alignment, Control_DC, Build_Points, Stabilization_Points, Size, Population, Economy, Loyalty, Stability, Fame, Unrest, Consumption) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        val = (kingdom, password, government, alignment, 21, 0, 0, 1, 0, 0, economy, loyalty, stability, 0, 0)
        cursor.execute(sql, val)
        sql = """INSERT INTO Kingdoms_Custom(Kingdom, Control_DC, Economy, Loyalty, Stability, Fame, Unrest, Consumption) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        val = (kingdom, 0, 0, 0, 0, 0, 0, 0)
        cursor.execute(sql, val)
        cursor.execute(f"""SELECT Title, VPEconomy, VPLoyalty, VPStability, VPUnrest FROM AA_Leadership_Roles""")
        leadership_roles = cursor.fetchall()
        for leader in leadership_roles:
            sql = "INSERT INTO Leadership(Kingdom, Name, Title, Modifier, Economy, Loyalty, Stability, Unrest) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            val = (kingdom, 'VACANT', leader[0], 0, leader[1], leader[2], leader[3], leader[4])
            cursor.execute(sql, val)
            cursor.execute(f"""SELECT Economy, Loyalty, Stability, Unrest FROM Kingdoms WHERE Kingdom = '{kingdom}'""")
            kingdom_info = cursor.fetchone()
            sql = f"""UPDATE Kingdoms SET Economy = ?, Loyalty = ?, Stability = ?, Unrest =? WHERE Kingdom = '{kingdom}'"""
            val = (kingdom_info[0] + leader[1], kingdom_info[1] + leader[2], kingdom_info[2] + leader[3], kingdom_info[3] + leader[4])
            cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Kingdoms', f'Create {kingdom}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def destroy_kingdom(self, kingdom, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""DELETE FROM Kingdoms where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
        cursor.execute(f"""DELETE FROM Settlements where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
        cursor.execute(f"""DELETE FROM Settlements_Custom where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
        cursor.execute(f"""DELETE FROM Buildings where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
        cursor.execute(f"""DELETE FROM Kingdoms_Custom where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
        cursor.execute(f"""DELETE FROM Leadership where Kingdom = '{kingdom}'""", {'kingdom': kingdom})
        cursor.execute(f"""DELETE FROM Hexes WHERE Kingdom = '{kingdom}'""", {'kingdom': kingdom})
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Kingdoms', f'Remove {kingdom}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def modify_kingdom(self, old_kingdom, new_kingdom, new_password, new_government, new_alignment, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Government, Alignment, Economy, Loyalty, Stability FROM Kingdoms WHERE Kingdom = '{old_kingdom}'""")
        kingdom_info = cursor.fetchone()
        cursor.execute(f"""SELECT Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = '{kingdom_info[1]}'""")
        old_alignment_info = cursor.fetchone()
        cursor.execute(f"""SELECT Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = '{new_alignment}'""")
        new_alignment_info = cursor.fetchone()
        cursor.execute(f"""SELECT Corruption, Crime, Law, Lore, Productivity, Society FROM AA_Government WHERE Government = '{kingdom_info[0]}'""")
        old_government_info = cursor.fetchone()
        cursor.execute(f"""SELECT Corruption, Crime, Law, Lore, Productivity, Society FROM AA_Government WHERE Government = '{new_government}'""")
        new_government_info = cursor.fetchone()
        sql = f"""UPDATE Kingdoms SET Kingdom = ?, Password = ?, Government = ?, Alignment = ?, Economy = ?, Loyalty = ?, Stability = ?  WHERE Kingdom = '{old_kingdom}'"""
        val = (new_kingdom, new_password, new_government, new_alignment, kingdom_info[2] - old_alignment_info[0] + new_alignment_info[0], kingdom_info[3] - old_alignment_info[1] + new_alignment_info[1], kingdom_info[4] - old_alignment_info[2] + new_alignment_info[2])
        cursor.execute(sql, val)
        cursor.execute(f"""UPDATE Kingdoms_Custom SET Kingdom = '{new_kingdom}' WHERE Kingdom = '{old_kingdom}'""")
        cursor.execute(f"""SELECT Kingdom, Settlement, Corruption, Crime, Productivity, law, Lore, Society FROM Settlements WHERE Settlement = '{old_kingdom}'""")
        settlement_info = cursor.fetchall()
        for settlement in settlement_info:
            sql = f"""UPDATE Settlements SET Kingdom = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ? where Kingdom = '{old_kingdom}' AND Settlement = '{settlement[1]}'"""
            val = (new_kingdom, settlement[3] - old_government_info[0] + new_government_info[0], settlement[4] - old_government_info[1] + new_government_info[1], settlement[5] - old_government_info[2] + new_government_info[2], settlement[6] - old_government_info[3] + new_government_info[3], settlement[7] - old_government_info[4] + new_government_info[4], settlement[8] - old_government_info[5] + new_government_info[5])
            cursor.execute(sql, val)
        cursor.execute(f"""UPDATE Settlements_Custom SET Kingdom = '{new_kingdom}' where Kingdom = '{old_kingdom}'""")
        cursor.execute(f"""UPDATE Buildings SET Kingdom = '{new_kingdom}' where Kingdom = '{old_kingdom}'""")
        cursor.execute(f"""UPDATE Leadership SET Kingdom = '{new_kingdom}' where Kingdom = '{old_kingdom}'""")
        cursor.execute(f"""UPDATE Hexes SET Kingdom = '{new_kingdom}' WHERE Kingdom = '{old_kingdom}'""")
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, new_kingdom, time, 'Kingdoms', f'replace {old_kingdom} for {new_kingdom}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def customize_kingdom_modifiers(self, kingdom, control_dc, economy, loyalty, stability, fame, unrest, consumption, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT * FROM Kingdoms_Custom WHERE Kingdom = '{kingdom}'""")
        custom = cursor.fetchone()
        sql = f"""UPDATE Kingdoms_Custom SET Control_DC = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ?, Consumption = ? WHERE kingdom = '{kingdom}'"""
        val = (control_dc, economy, loyalty, stability, fame, unrest, consumption)
        cursor.execute(sql, val)
        cursor.execute(f"""SELECT Control_DC,Economy,Loyalty,Stability, Fame,Unrest,Consumption from kingdoms where kingdom = '{kingdom}'""")
        kingdoms = cursor.fetchone()
        sql = f"""UPDATE Kingdoms SET Control_DC = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ?, Consumption = ? where kingdom = '{kingdom}'"""
        val = (kingdoms[0]+control_dc - custom[1], kingdoms[1] + economy - custom[2], kingdoms[2] + loyalty - custom[3], kingdoms[3] + stability - custom[4], kingdoms[4] + fame - custom[5], kingdoms[5] + unrest - custom[6], kingdoms[6] + consumption - custom[7])
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Kingdoms_Custom', f'customize {kingdom}s custom modifiers', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def create_blueprint(self, building, build_points, lots, economy, loyalty, stability, fame, unrest, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting, supply, settlement_limit, district_limit, description, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = "INSERT INTO buildings_Blueprints(Building, Build_points, lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, defence, Base_Value, Spellcasting, Supply, Settlement_Limit, District_Limit, Description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        val = (building, build_points, lots, economy, loyalty, stability, fame, unrest, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting, supply, settlement_limit, district_limit, description)
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, building, time, 'Blueprints', f'Create {building}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def modify_blueprint(self, building, new_build_points, new_lots, new_economy, new_loyalty, new_stability, new_fame, new_unrest, new_corruption, new_crime, new_productivity, new_law, new_lore, new_society, new_danger, new_defence, new_base_value, new_spellcasting, new_supply, new_settlement_limit, new_district_limit, new_description, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT* from Buildings_Blueprints where Building = '{building}'""")
        build_info = cursor.fetchone()
        cursor.execute(f"""SELECT * from Buildings where building = '{building}'""")
        holdings = cursor.fetchall()
        for held in holdings:
            cursor.execute(f"""SELECT * FROM kingdoms where kingdom = '{held[0]}'""")
            kingdoms = cursor.fetchone()
            cursor.execute(f"""SELECT * from settlements where kingdom = '{held[0]}' AND settlement = '{held[1]}'""")
            settlements = cursor.fetchone()
            holding_bp = (build_info[1] - new_build_points) * held[3]
            holding_lots = (build_info[2] - new_lots) * held[3]
            holding_economy = (build_info[3] - new_economy) * held[3]
            holding_loyalty = (build_info[4] - new_loyalty) * held[3]
            holding_stability = (build_info[5] - new_stability) * held[3]
            holding_fame = (build_info[6] - new_fame) * held[3]
            holding_unrest = (build_info[7] - new_unrest) * held[3]
            holding_corruption = (build_info[8] - new_corruption) * held[3]
            holding_crime = (build_info[9] - new_crime) * held[3]
            holding_productivity = (build_info[10] - new_productivity) * held[3]
            holding_law = (build_info[11] - new_law) * held[3]
            holding_lore = (build_info[12] - new_lore) * held[3]
            holding_society = (build_info[13] - new_society) * held[3]
            holding_danger = (build_info[14] - new_danger) * held[3]
            holding_defence = (build_info[15] - new_defence * held[3])
            holding_bv = (build_info[16] - new_base_value) * held[3]
            holding_sc = (build_info[17] - new_spellcasting) * held[3]
            holding_supply = (build_info[18] - new_supply) * held[3]
            sql = f"""UPDATE kingdoms SET Control_DC = ?, Build_Points = ? , Stabilization_points = ? , Population = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ? WHERE Kingdom = '{held[0]}'"""
            val = (kingdoms[4] - (1/4 * holding_lots), kingdoms[5] + (holding_bp / 2), kingdoms[6] + floor((holding_bp / 2) * settlements[14]), kingdoms[8] + (holding_lots * 50), kingdoms[9] + holding_economy, kingdoms[10] + holding_loyalty, kingdoms[11] + holding_stability, kingdoms[12] + holding_fame, kingdoms[13] + holding_unrest)
            cursor.execute(sql, val)
            sql = f"""UPDATE settlements SET Size = ?, Population = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ? WHERE kingdom = '{held[0]}' AND settlement = '{held[1]}'"""
            val = (settlements[3] + (1/4 * holding_lots), settlements[4] + (holding_lots * 50), settlements[5] + holding_corruption, settlements[6] + holding_crime, settlements[7] + holding_productivity, settlements[8] + holding_law, settlements[9] + holding_lore, settlements[10] + holding_society, settlements[11] + holding_danger, settlements[12] + holding_defence, settlements[13] + holding_bv, settlements[14] + holding_sc, settlements[15] + holding_supply)
            cursor.execute(sql, val)
            sql = f"""UPDATE Buildings SET lots = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence, Base_Value = ?, Spellcasting = ?, Supply = ? WHERE kingdom = '{held[0]}' AND Settlement = '{held[1]}' AND building = '{held[2]}'"""
            val = (held[4] + holding_lots, held[5] + holding_economy, held[6] + holding_loyalty, held[7] + holding_stability, held[8] + holding_fame, held[9] + holding_unrest, held[10] + holding_corruption, held[11] + holding_crime, held[12] + holding_productivity, held[13] + holding_law, held[14] + holding_lore, held[15] + holding_society, held[16] + holding_danger, held[17] + holding_defence, held[18] + holding_bv, held[19] + holding_sc, held[20] + holding_supply)
            cursor.execute(sql, val)
        sql = f"""UPDATE Buildings_Blueprints SET Build_Points = ?, Lots = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ?, Settlement_Limit = ?, District_Limit = ?, Description = ? WHERE Building = '{building}'"""
        val = (new_build_points, new_lots, new_economy, new_loyalty, new_stability, new_fame, new_unrest, new_corruption, new_crime, new_productivity, new_law, new_lore, new_society, new_danger, new_defence, new_base_value, new_spellcasting, new_supply, new_settlement_limit, new_district_limit, new_description)
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, building, time, 'Blueprints', f'Modify {building}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def remove_blueprint(self, building, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"""SELECT * from Buildings where building  = '{building}'""")
        holdings = cursor.fetchall()
        cursor.execute(f"""SELECT * from Buildings_Blueprints where building = '{building}'""")
        building_info = cursor.fetchone()
        for held in holdings:
            cursor.execute(f"""SELECT * FROM kingdoms where kingdom = '{held[0]}'""")
            kingdoms = cursor.fetchone()
            cursor.execute(f"""SELECT * from settlements where kingdom = '{held[0]}' AND settlement = '{held[1]}'""")
            settlements = cursor.fetchone()
            sql = f"""UPDATE kingdoms SET Control_DC = ?, Build_Points = ? , Stabilization_points = ? , Population = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ? WHERE kingdom = {holdings[0]}"""
            val = (kingdoms[4] - (1/4 * held[5]), kingdoms[5] + floor((held[3] * building_info[2]) / 2), kingdoms[6] + ((held[3] * building_info[2]) / 2) * settlements[14], kingdoms[8] - (held[4] * 50), kingdoms[9] - held[5], kingdoms[10] - held[6], kingdoms[11] - held[7], kingdoms[12] - held[8], kingdoms[13] - held[9])
            cursor.execute(sql, val)
            sql = f"""UPDATE settlements SET Size = ?, Population = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ? WHERE kingdom = '{holdings[0]}' AND settlement = '{holdings[1]}'"""
            val = (settlements[3] - (1/4 * held[4]), settlements[4] - (held[4] * 50), settlements[5] - held[10], settlements[6] - held[11], settlements[7] - held[12], settlements[8] - held[13], settlements[9] - held[14], settlements[10] - held[15], settlements[11] - held[16], settlements[12] - held[17], settlements[13] - held[18], settlements[14] - held[19])
            cursor.execute(sql, val)
            sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
            val = (author, held[0], time, 'Blueprints', f'Removed {held[4]} {building}', 0, 'N/A')
            cursor.execute(sql, val)
        cursor.execute(f"""DELETE from Buildings_Blueprints where Building = '{building}'""")
        cursor.execute(f"""DELETE from Buildings where Building = '{building}'""")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, building, time, 'Blueprints', f'Remove {building}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def claim_settlement(self, kingdom, settlement, guild_id, author):
        # Sets up settlements in the settlement table - I could've coalesced this better, but didn't want it storing the password multiple times because it would've made that weird to update.
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Search from Admin where Identifier = 'Decay'""")
        decay = cursor.fetchone()
        if decay[0]:
            decay_value = 0
        else:
            decay_value = 1
        sql = "INSERT INTO Settlements(Kingdom, Settlement, Size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        val = (kingdom, settlement, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, decay_value)
        cursor.execute(sql, val)
        sql = "INSERT INTO Settlements_Custom(Kingdom, Settlement, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        val = (kingdom, settlement, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Settlements', f'Claim {settlement} in {kingdom}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def destroy_settlement(self, kingdom, settlement, guild_id, author):
        sum_sp = 0
        sum_bp = 0
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""Select Kingdom, Control_DC, Build_Points, Stabilization_Points, Population, Economy, Loyalty, Stability, Fame, Unrest FROM kingdoms WHERE kingdom = '{kingdom}'""")
        kingdoms = cursor.fetchone()
        cursor.execute(f"""SELECT Corruption FROM Settlements WHERE Kingdom = '{kingdom}' AND Settlement = '{settlement}'""")
        settlement_corruption = cursor.fetchone()
        cursor.execute(f"""SELECT Building, Constructed FROM Buildings WHERE kingdom = '{kingdom}' AND settlement = '{settlement}'""")
        blueprint_info = cursor.fetchall()
        if blueprint_info is not None:
            for blueprint in blueprint_info:
                cursor.execute(f"""SELECT Build_Points FROM Buildings_Blueprints WHERE Building = '{blueprint[0]}'""")
                cost = cursor.fetchone()
                build_points = cost[0] / 2
                stabilization_points = ((cost[0]/2)*settlement_corruption[0])
                sum_bp += build_points
                sum_sp += stabilization_points
        cursor.execute(f"""SELECT Kingdom, SUM(Lots), SUM(Economy), SUM(Loyalty), SUM(Stability), SUM(Fame), SUM(Unrest) from Buildings where kingdom = '{kingdom}' and settlement = '{settlement}'""")
        holding_sum = cursor.fetchone()
        cursor.execute(f"""DELETE from Buildings where Kingdom = '{kingdom}' AND Settlement = '{settlement}'""")
        cursor.execute(f"""DELETE from Settlements where Kingdom = '{kingdom}' AND Settlement = '{settlement}'""")
        cursor.execute(f"""DELETE from Settlements_Custom where Kingdom = '{kingdom}' AND Settlement = '{settlement}'""")
        if holding_sum[0] is not None:
            sql = f"""UPDATE kingdoms SET Control_DC = ?, build_points = ?, stabilization_points = ?, Population = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ? WHERE kingdom = '{kingdom}'"""
            val = (kingdoms[1] - (holding_sum[1] / 4), kingdoms[2] + sum_bp, kingdoms[3] + sum_sp, kingdoms[4] + (holding_sum[1] * 50), kingdoms[5] + holding_sum[2], kingdoms[6] + holding_sum[3], kingdoms[7] + holding_sum[4], kingdoms[8] + holding_sum[5], kingdoms[9] + holding_sum[6])
            cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Settlements', f'destroy {settlement} in {kingdom}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def modify_settlement(self, kingdom, old_settlement, new_settlement, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""UPDATE Settlements SET Settlement = '{new_settlement}' where Kingdom = '{kingdom}' AND Settlement = '{old_settlement}'""")
        cursor.execute(f"""UPDATE Buildings SET Settlement = '{new_settlement}' where Kingdom = '{kingdom}' AND Settlement = '{old_settlement}'""")
        cursor.execute(f"""UPDATE Settlements_Custom SET Settlement = '{new_settlement}' where Kingdom = '{kingdom}' AND Settlement = '{old_settlement}'""")
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Settlements', f'change from {old_settlement} to {new_settlement} in {kingdom}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def custom_settlement_modifiers(self, kingdom, settlement, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting, supply, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT * FROM Settlements_Custom WHERE kingdom = '{kingdom}' AND settlement = '{settlement}'""")
        custom = cursor.fetchone()
        sql = f"""UPDATE Settlements_Custom SET Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ? WHERE kingdom = '{kingdom}' AND settlement = '{settlement}'"""
        val = (corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting, supply)
        cursor.execute(sql, val)
        cursor.execute(f"""SELECT Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply FROM Settlements WHERE kingdom = '{kingdom}' AND settlement = '{settlement}'""")
        settlements = cursor.fetchone()
        sql = f"""UPDATE Settlements SET Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ? WHERE kingdom = '{kingdom}' AND settlement = '{settlement}'"""
        val = (settlements[0] + corruption - custom[2], settlements[1] + crime - custom[3], settlements[2] + productivity - custom[4], settlements[3] + law - custom[5], settlements[4] + lore - custom[6], settlements[5] + society - custom[7], settlements[6] + danger - custom[8], settlements[7] + defence - custom[9], settlements[8] + base_value - custom[10], settlements[9] + spellcasting - custom[11], settlements[10] + supply - custom[12])
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Settlement_Modifies', f'adjust the modifies of {settlement} in {kingdom}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def construct_building(self, kingdom, settlement, building, amount, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Control_DC, Build_Points, Stabilization_Points, Population, Economy, Loyalty, Stability, Fame, Unrest from kingdoms where kingdom = '{kingdom}'""")
        kingdoms = cursor.fetchone()
        cursor.execute(f"""SELECT Size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay FROM settlements WHERE kingdom = '{kingdom}' AND settlement = '{settlement}'""")
        settlements = cursor.fetchone()
        cursor.execute(f"""SELECT Constructed, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply from Buildings where kingdom = '{kingdom}' AND settlement = '{settlement}' AND building = '{building}'""")
        holdings = cursor.fetchone()
        cursor.execute(f"""SELECT Build_Points, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Settlement_Limit, District_Limit from Buildings_Blueprints where building = '{building}'""")
        blueprint = cursor.fetchone()
        build_points = blueprint[0] * amount
        lots = blueprint[1] * amount
        economy = blueprint[2] * amount
        loyalty = blueprint[3] * amount
        stability = blueprint[4] * amount
        fame = blueprint[5] * amount
        unrest = blueprint[6] * amount
        corruption = blueprint[7] * amount
        crime = blueprint[8] * amount
        productivity = blueprint[9] * amount
        law = blueprint[10] * amount
        lore = blueprint[11] * amount
        society = blueprint[12] * amount
        danger = blueprint[13] * amount
        defence = blueprint[14] * amount
        base_value = blueprint[15] * amount
        spellcasting = blueprint[16] * amount
        supply = blueprint[17] * amount
        if holdings is None:
            sql = f"""INSERT INTO Buildings(Kingdom, Settlement, Building, Constructed, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            val = (kingdom, settlement, building, amount, lots, economy, loyalty, stability, fame, unrest, corruption, crime, productivity, law, lore, society, danger, defence, base_value, spellcasting, supply)
            cursor.execute(sql, val)
        if holdings is not None:
            sql = f"""UPDATE Buildings SET Constructed = ?, Lots = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ? WHERE Kingdom = '{kingdom}' AND Settlement = '{settlement}' AND Building = '{building}'"""
            val = (holdings[0] + amount, holdings[1] + lots, holdings[2] + economy, holdings[3] + loyalty, holdings[4] + stability, holdings[5] + fame, holdings[6] + unrest, holdings[7] + corruption, holdings[8] + crime, holdings[9] + productivity, holdings[10] + law, holdings[11] + lore, holdings[12] + society, holdings[13] + danger, holdings[14] + defence, holdings[15] + base_value, holdings[16] + spellcasting, holdings[17] + supply)
            cursor.execute(sql, val)
        sql = f"""UPDATE kingdoms SET Control_DC = ?, Build_Points = ? , Stabilization_points = ? , Population = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ? WHERE kingdom = '{kingdom}'"""
        val = (kingdoms[0] + (1/4 * lots), kingdoms[1] - build_points, kingdoms[2] - (build_points * settlements[12]), kingdoms[3] + (lots * 50), kingdoms[4] + economy, kingdoms[5] + loyalty, kingdoms[6] + stability, kingdoms[7] + fame, kingdoms[8] + unrest)
        cursor.execute(sql, val)
        sql = f"""UPDATE settlements SET Size = ?, Population = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ? WHERE kingdom = '{kingdom}' AND settlement = '{settlement}'"""
        val = (settlements[0] + (1/4 * lots), settlements[1] + (lots * 50), settlements[2] + corruption, settlements[3] + crime, settlements[4] + productivity, settlements[5] + law, settlements[6] + lore, settlements[7] + society, settlements[8] + danger, settlements[9] + defence, settlements[10] + base_value, settlements[11] + spellcasting, settlements[12] + supply)
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Buildings', f'Build a {building} for {settlement} in {kingdom}', amount, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def destroy_building(self, kingdom, settlement, building, amount, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Control_DC, Build_Points, Stabilization_Points, Population, Economy, Loyalty, Stability, Fame, Unrest from kingdoms where kingdom = '{kingdom}'""")
        kingdoms = cursor.fetchone()
        cursor.execute(f"""SELECT Size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Decay FROM settlements WHERE kingdom = '{kingdom}' AND settlement = '{settlement}'""")
        settlements = cursor.fetchone()
        cursor.execute(f"""SELECT Constructed, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply from Buildings where kingdom = '{kingdom}' AND settlement = '{settlement}' AND building = '{building}'""")
        holdings = cursor.fetchone()
        cursor.execute(f"""SELECT Build_Points, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply, Settlement_Limit, District_Limit from Buildings_Blueprints where building = '{building}'""")
        blueprint = cursor.fetchone()
        build_points = blueprint[0] * amount
        lots = blueprint[1] * amount
        economy = blueprint[2] * amount
        loyalty = blueprint[3] * amount
        stability = blueprint[4] * amount
        fame = blueprint[5] * amount
        unrest = blueprint[6] * amount
        corruption = blueprint[7] * amount
        crime = blueprint[8] * amount
        productivity = blueprint[9] * amount
        law = blueprint[10] * amount
        lore = blueprint[11] * amount
        society = blueprint[12] * amount
        danger = blueprint[13] * amount
        defence = blueprint[14] * amount
        base_value = blueprint[15] * amount
        spellcasting = blueprint[16] * amount
        supply = blueprint[17] * amount
        if holdings[0] - amount == 0:
            cursor.execute(f"""DELETE FROM Buildings where Kingdom = '{kingdom}' AND Settlement = '{settlement}' AND Building = '{building}'""")
        if holdings[0] - amount > 0:
            sql = f"""UPDATE Buildings SET Constructed = ?, Lots = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ? WHERE Kingdom = '{kingdom}' AND Settlement = '{settlement}' AND Building = '{building}'"""
            val = (holdings[0] - amount, holdings[1] - lots, holdings[2] - economy, holdings[3] - loyalty, holdings[4] - stability, holdings[5] - fame, holdings[6] - unrest, holdings[7] - corruption, holdings[8] - crime, holdings[9] - productivity, holdings[10] - law, holdings[11] - lore, holdings[12] - society, holdings[13] - danger, holdings[14] - defence, holdings[15] - base_value, holdings[16] - spellcasting, holdings[17] - supply)
            cursor.execute(sql, val)
        sql = f"""UPDATE kingdoms SET Control_DC = ?, Build_Points = ? , Stabilization_points = ? , Population = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ? WHERE kingdom = '{kingdom}'"""
        val = (kingdoms[0] - (1/4 * lots), kingdoms[1] + (build_points / 2), kingdoms[2] + (build_points / 2 * settlements[12]), kingdoms[3] - (lots * 50), kingdoms[4] - economy, kingdoms[5] - loyalty, kingdoms[6] - stability, kingdoms[7] - fame, kingdoms[8] - unrest)
        cursor.execute(sql, val)
        sql = f"""UPDATE settlements SET Size = ?, Population = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ? WHERE kingdom = '{kingdom}' AND settlement = '{settlement}'"""
        val = (settlements[0] - (1/4 * lots), settlements[1] - (lots * 50), settlements[2] - corruption, settlements[3] - crime, settlements[4] - productivity, settlements[5] - law, settlements[6] - lore, settlements[7] - society, settlements[8] - danger, settlements[9] - defence, settlements[10] - base_value, settlements[11] - spellcasting, settlements[12] - supply)
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Buildings', f'Destroy a {building} for {settlement} in {kingdom}', amount, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def modify_leader(self, kingdom, leader, title, modifier, column, economy_modifier, loyalty_modifier, stability_modifier, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Economy, Loyalty, Stability, Unrest FROM leadership WHERE Kingdom = '{kingdom}' AND Title = '{title}'""")
        leader_values = cursor.fetchone()
        sql = f"""UPDATE Leadership SET Name = ?, Stat = ?, Modifier = ?, Economy = ?, Loyalty = ?, Stability = ?, Unrest = ? WHERE Kingdom = '{kingdom}' AND Title = '{title}'"""
        val = (leader, column, modifier, economy_modifier, loyalty_modifier, stability_modifier, 0)
        cursor.execute(sql, val)
        cursor.execute(f"""SELECT Economy, Loyalty, Stability, Unrest FROM kingdoms where kingdom = '{kingdom}'""")
        kingdom_values = cursor.fetchone()
        sql = f"""UPDATE kingdoms SET Economy = ?, Loyalty = ?, Stability = ?, Unrest = ? WHERE kingdom = '{kingdom}'"""
        val = (kingdom_values[0] - leader_values[0] + economy_modifier, kingdom_values[1] - leader_values[1] + loyalty_modifier, kingdom_values[2] - leader_values[2] + stability_modifier, kingdom_values[3] - leader_values[3])
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Leadership', f'Modify the {title} role for {kingdom}', 1, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def remove_leader(self, kingdom, title, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Economy, Loyalty, Stability, Unrest from Leadership WHERE Kingdom = '{kingdom}' AND Title = '{title}'""")
        leader_values = cursor.fetchone()
        cursor.execute(f"""SELECT Economy, Loyalty, Stability, Unrest FROM Kingdoms where Kingdom = '{kingdom}'""")
        kingdom_values = cursor.fetchone()
        cursor.execute(f"""SELECT VPEconomy, VPLoyalty, VPStability, VPUnrest FROM AA_Leadership_Roles WHERE Title = '{title}'""")
        role_values = cursor.fetchone()
        sql = f"""UPDATE leadership SET Name = ?, Stat = ?, Modifier = ?, Economy = ?, Loyalty = ?, Stability = ?, Unrest = ? WHERE kingdom = '{kingdom}' AND Title = '{title}'"""
        val = ("VACANT", "None", 0, role_values[0], role_values[1], role_values[2], role_values[3])
        cursor.execute(sql, val)
        economy = kingdom_values[0] + role_values[0] - leader_values[0]
        loyalty = kingdom_values[1] + role_values[1] - leader_values[1]
        stability = kingdom_values[2] + role_values[2] - leader_values[2]
        unrest = kingdom_values[3] + role_values[3] - leader_values[3]
        sql = f"""UPDATE Kingdoms SET Economy = ?, Loyalty = ?, Stability = ?, Unrest = ? WHERE Kingdom = '{kingdom}'"""
        val = (economy, loyalty, stability, unrest)
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Leadership', f'reset the {title} role for {kingdom}', 1, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def claim_hex(self, kingdom, hex_terrain, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Control_DC, Size from kingdoms WHERE kingdom = '{kingdom}'""")
        kingdom_info = cursor.fetchone()
        cursor.execute(f"""SELECT Amount FROM hexes WHERE kingdom = '{kingdom}' AND Hex_Terrain = '{hex_terrain}' AND Improvement = 'None'""")
        hex = cursor.fetchone()
        if hex is None:
            sql = f"""INSERT INTO hexes(Kingdom, Hex_Terrain, Amount, Improvement, Economy, Loyalty, Stability, Unrest, Consumption, Defence) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            val = (kingdom, hex_terrain, 1, 'None', 0, 0, 0, 0, 0, 0)
            cursor.execute(sql, val)
        if hex is not None:
            value = (hex[0] + 1)
            cursor.execute(f"""UPDATE hexes SET Amount = {value} WHERE kingdom = '{kingdom}' AND hex_terrain = '{hex_terrain}' AND Improvement = 'None'""")
        sql = f"""UPDATE Kingdoms SET Control_DC = ?, Size = ? WHERE kingdom = '{kingdom}'"""
        val = (kingdom_info[0] + 1, kingdom_info[1] + 1)
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Hexes', f'add one {hex_terrain} hex for {kingdom}', 1, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def relinquish_hex(self, kingdom, hex_terrain, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Control_DC, Size from kingdoms WHERE kingdom = '{kingdom}'""")
        kingdom_info = cursor.fetchone()
        cursor.execute(f"""SELECT Amount FROM hexes WHERE kingdom = '{kingdom}' AND Hex_Terrain = '{hex_terrain}' AND Improvement = 'None'""")
        hex = cursor.fetchone()
        if hex[0] - 1 == 0:
            cursor.execute(f"""DELETE FROM hexes  WHERE kingdom = '{kingdom}' AND hex_terrain = '{hex_terrain}' AND Improvement = 'None'""")
        if hex[0] - 1 != 0:
            cursor.execute(f"""UPDATE hexes SET Amount = ({hex[0]} - 1) WHERE kingdom = '{kingdom}' AND hex_terrain = '{hex_terrain}' AND Improvement = 'None'""")
        sql = f"""UPDATE kingdoms SET Control_DC = ?, Size = ? where kingdom = '{kingdom}'"""
        val = (kingdom_info[0] - 1, kingdom_info[1] - 1)
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Hexes', f'remove one {hex_terrain} hex for {kingdom}', 1, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def improve_hex(self, kingdom, hex_terrain, improvement, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Build_points, Economy, Loyalty, Stability, Unrest, Consumption, Defence FROM Hexes_Improvements WHERE Improvement = '{improvement}'""")
        improvement_info = cursor.fetchone()
        cursor.execute(f"""SELECT Amount FROM hexes WHERE kingdom = '{kingdom}' AND Improvement = 'None' AND Hex_Terrain = '{hex_terrain}'""")
        hex_info = cursor.fetchone()
        cursor.execute(f"""SELECT Build_Points, Economy, Loyalty, Stability, Unrest, Consumption FROM kingdoms WHERE kingdom = '{kingdom}'""")
        kingdom_info = cursor.fetchone()
        cursor.execute(f"""SELECT Amount, Economy, Loyalty, Stability, Unrest, Consumption, Defence FROM hexes WHERE kingdom = '{kingdom}' AND Hex_Terrain = '{hex_terrain}' AND Improvement = '{improvement}'""")
        total = cursor.fetchone()
        build_points = kingdom_info[0] - improvement_info[0]
        economy = kingdom_info[1] + improvement_info[1]
        loyalty = kingdom_info[2] + improvement_info[2]
        stability = kingdom_info[3] + improvement_info[3]
        unrest = kingdom_info[4] + improvement_info[4]
        consumption = kingdom_info[5] + improvement_info[5]
        sql = f"""UPDATE kingdoms SET Build_Points = ?, Economy = ?, Loyalty = ?, Stability = ?, Unrest = ?, Consumption = ? WHERE kingdom = '{kingdom}'"""
        val = (build_points, economy, loyalty, stability, unrest, consumption)
        cursor.execute(sql, val)
        if hex_info[0] - 1 == 0:
            cursor.execute(f"""DELETE from hexes WHERE kingdom = '{kingdom}' AND Hex_Terrain = '{hex_terrain}' AND Improvement = 'None'""")
        elif hex_info[0] - 1 >= 1:
            val = (hex_info[0] + -1)
            cursor.execute(f"""UPDATE hexes SET Amount = {val} WHERE Kingdom = '{kingdom}' AND Hex_Terrain = '{hex_terrain}' AND Improvement = 'None'""")
        if total is None:
            sql = f"""INSERT INTO hexes(kingdom, Hex_Terrain, Amount, Improvement, Economy, Loyalty, Stability, Unrest, Consumption, Defence) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            val = (kingdom, hex_terrain, 1, improvement, improvement_info[1], improvement_info[2], improvement_info[3], improvement_info[4], improvement_info[5], improvement_info[6])
            cursor.execute(sql, val)
        if total is not None:
            sql = f"""UPDATE hexes SET Amount = ?, Economy = ?, Loyalty = ?, Stability =?, Unrest = ?, Consumption = ?, Defence = ? WHERE kingdom = '{kingdom}' AND Hex_Terrain = '{hex_terrain}' AND Improvement = '{improvement}'"""
            val = (total[0]+1, total[1] + improvement_info[1], total[2] + improvement_info[2], total[3] + improvement_info[3], total[4] + improvement_info[4], total[5] + improvement_info[5], total[6] + improvement_info[6])
            cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Hexes', f'add one {improvement} hex improvement for {kingdom}', 1, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def diminish_hex(self, kingdom, hex_terrain, improvement, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Build_points, Economy, Loyalty, Stability, Unrest, Consumption, Defence FROM Hexes_Improvements WHERE Improvement = '{improvement}'""")
        improvement_info = cursor.fetchone()
        cursor.execute(f"""SELECT Amount, Economy, Loyalty, Stability, Unrest, Consumption, Defence FROM hexes WHERE kingdom = '{kingdom}' AND Improvement = 'None' AND Hex_Terrain = '{hex_terrain}'""")
        hex_info = cursor.fetchone()
        cursor.execute(f"""SELECT Build_Points, Economy, Loyalty, Stability, Unrest, Consumption FROM kingdoms WHERE kingdom = '{kingdom}'""")
        kingdom_info = cursor.fetchone()
        cursor.execute(f"""SELECT Amount, Economy, Loyalty, Stability, Unrest, Consumption, Defence  FROM hexes  WHERE kingdom = '{kingdom}' AND Hex_Terrain = '{hex_terrain}' AND Improvement = '{improvement}'""")
        total = cursor.fetchone()
        sql = f"""UPDATE kingdoms SET Build_Points = ?, Economy = ?, Loyalty = ?, Stability = ?, Unrest = ?, Consumption = ? WHERE kingdom = '{kingdom}'"""
        val = (kingdom_info[0] + (improvement_info[0] / 2), kingdom_info[1] - improvement_info[1], kingdom_info[2] - improvement_info[2], kingdom_info[3] - improvement_info[3], kingdom_info[4] - improvement_info[4], kingdom_info[5] - improvement_info[5])
        cursor.execute(sql, val)
        if hex_info is None:
            sql = f"""INSERT INTO hexes(kingdom, Hex_Terrain, Amount, Improvement, Economy, Loyalty, Stability, Unrest, Consumption, Defence) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            val = (kingdom, hex_terrain, 1, 'None', 0, 0, 0, 0, 0, 0)
            cursor.execute(sql, val)
        if hex_info is not None:
            val = (hex_info[0]+1)
            cursor.execute(f"""UPDATE hexes SET Amount = '{val}' WHERE kingdom = '{kingdom}' AND hex_terrain = '{hex_terrain}' AND Improvement = 'None'""")
        if total[0] - 1 == 0:
            cursor.execute(f"""DELETE FROM hexes WHERE kingdom = '{kingdom}' AND Hex_Terrain = '{hex_terrain}' AND Improvement = '{improvement}'""")
        if total[0] - 1 >= 1:
            sql = f"""UPDATE hexes SET Amount = ?, Economy = ?, Loyalty = ?, Stability =?, Unrest = ?, Consumption = ?, Defence = ? WHERE kingdom = '{kingdom}' AND Hex_Terrain = '{hex_terrain}' AND Improvement = '{improvement}'"""
            val = (total[0] - 1, total[1] - improvement_info[1], total[2] - improvement_info[2], total[3] - improvement_info[3], total[4] - improvement_info[4], total[5] - improvement_info[5], total[6] - improvement_info[6])
            cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, kingdom, time, 'Hexes', f'remove one {improvement} hex improvement for {kingdom}', 1, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def add_hex_improvements(self, improvement, build_points, road_multiplier, economy, loyalty, stability, unrest, consumption, defence, taxation, cavernous, coastline, desert, forest, hills, jungle, marsh, mountains, plains, water, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = "INSERT INTO Hexes_Improvements(Improvement,  Build_points, Road_Multiplier, Economy, Loyalty, Stability, Unrest, Consumption, Defence, taxation, Cavernous, Coastline, Desert, Forest, Hills, Jungle, Marsh, Mountains, Plains, Water) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        val = (improvement, build_points, road_multiplier, economy, loyalty, stability, unrest, consumption, defence, taxation, cavernous, coastline, desert, forest, hills, jungle, marsh, mountains, plains, water)
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, 'N/A', time, 'Hexes_Improvements', f'add the {improvement} hex improvement', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def remove_hex_improvement(self, improvement, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT kingdom, Amount, Economy, Loyalty, Stability, Unrest, Consumption, Defence FROM hexes where Improvement  = '{improvement}'""")
        hex_info = cursor.fetchall()
        cursor.execute(f"""SELECT Build_points from Hexes_Improvements where Improvement = '{improvement}'""")
        improvement_info = cursor.fetchone()
        for hex_improvements in hex_info:
            cursor.execute(f"""SELECT Control_DC, Build_Points, Size, Economy, Loyalty, Stability, Unrest, Consumption FROM kingdoms where kingdom = '{hex_improvements[0]}'""")
            kingdoms = cursor.fetchone()
            sql = f"""UPDATE kingdoms SET Control_DC = ?, Build_Points = ?, Size = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ?, Consumption = ? WHERE kingdom = '{hex_improvements[0]}'"""
            val = (kingdoms[0] - hex_improvements[1], kingdoms[1] + (improvement_info[0] * hex_improvements[1]), kingdoms[2] - hex_improvements[1], kingdoms[3] - hex_improvements[2], kingdoms[4] - hex_improvements[3], kingdoms[5] - hex_improvements[4], kingdoms[6] - hex_improvements[5], kingdoms[7] - hex_improvements[6])
            cursor.execute(sql, val)
        cursor.execute(f"""DELETE from Hexes where Improvement = '{improvement}'""")
        cursor.execute(f"""DELETE from Hexes_Improvements where Improvement = '{improvement}'""")
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, 'N/A', time, 'Hexes_Improvements', f'remove the {improvement} hex improvement', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def modify_hex_improvement(self, old_improvement, new_improvement, new_build_points, new_road_multiplier, new_economy, new_loyalty, new_stability, new_unrest, new_consumption, new_defence, new_taxation, new_cavernous, new_coastline, new_desert, new_forest, new_hills, new_jungle, new_marsh, new_mountains, new_plains, new_water, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT kingdom, Amount, Economy, Loyalty, Stability, Unrest, Consumption, Defence, new_taxation FROM hexes where Improvement  = '{old_improvement}'""")
        hex_info = cursor.fetchall()
        cursor.execute(f"""SELECT Build_points, Economy, Loyalty, Stability, Unrest, Consumption, Defence, Taxation, Cavernous, Coastline, Desert, Forest, Hills, Jungle, Marsh, Mountains, Plains, Water FROM Hexes_Improvements WHERE Improvement = '{old_improvement}'""")
        improvement_info = cursor.fetchone()
        adj_build_points = new_build_points - improvement_info[0]
        adj_economy = new_economy - improvement_info[1]
        adj_loyalty = new_loyalty - improvement_info[2]
        adj_stability = new_stability - improvement_info[3]
        adj_unrest = new_unrest - improvement_info[4]
        adj_consumption = new_consumption - improvement_info[5]
        adj_defence = new_defence - improvement_info[6]
        adj_taxation = new_taxation - improvement_info[7]
        for hex_improvements in hex_info:
            cursor.execute(f"""SELECT Build_Points, Economy, Loyalty, Stability, Unrest, Consumption FROM kingdoms where kingdom = '{hex_improvements[0]}'""")
            kingdoms = cursor.fetchone()
            sql = f"""UPDATE kingdoms SET Build_Points = ?, Economy = ?, Loyalty = ?, Stability = ?, Unrest = ?, Consumption = ? WHERE kingdom = '{hex_improvements[0]}'"""
            val = (kingdoms[0] - (adj_build_points * hex_improvements[1]), kingdoms[1] + (adj_economy * hex_improvements[1]), kingdoms[2] + (adj_loyalty * hex_improvements[1]), kingdoms[3] + (adj_stability * hex_improvements[1]), kingdoms[4] + (adj_unrest * hex_improvements[1]), kingdoms[5] + (adj_consumption * hex_improvements[1]))
            cursor.execute(sql, val)
            sql = f"""UPDATE hexes SET Improvement = ?, Economy = ?, Loyalty = ?, Stability = ?, Unrest = ?, Consumption = ?, Defence = ?, Taxation = ? WHERE kingdom = '{hex_improvements[0]}' AND Improvement = '{old_improvement}'"""
            val = (new_improvement, adj_economy * hex_improvements[1], adj_loyalty * hex_improvements[1], adj_stability * hex_improvements[1], adj_unrest * hex_improvements[1], adj_consumption * hex_improvements[1], adj_defence * hex_improvements[1], adj_taxation * hex_improvements[1])
            cursor.execute(sql, val)
        sql = f"""UPDATE hexes_improvements SET Improvement = ?, Build_points = ?, Economy = ?, Loyalty = ?, Stability = ?, Unrest = ?, Consumption = ?, Defence = ?, new_taxation = ?, Cavernous = ?, Coastline = ?, Desert =?, Forest = ?, Hills = ?, Jungle = ?, Marsh = ?, Mountains = ?, Plains = ?, Water = ?  where Improvement = '{old_improvement}'"""
        val = (new_improvement, new_build_points, new_economy, new_loyalty, new_stability, new_unrest, new_consumption, new_defence, new_taxation, new_cavernous, new_coastline, new_desert, new_forest, new_hills, new_jungle, new_marsh, new_mountains, new_plains, new_water)
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, 'N/A', time, 'Hexes_Improvements', f'Adjustment from {old_improvement} to the {new_improvement} hex improvement', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def balance_tables(self, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        """NOTE: Reset Kingdom and Recalculate leadership and alignment"""
        sql = f"""UPDATE Kingdoms SET Control_DC = ?, Size = ?, Population = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ?, Consumption = ?"""
        val = (21, 1, 0, 0, 0, 0, 0, 0, 0)
        cursor.execute(sql, val)
        cursor.execute(f"""SELECT Kingdom, Alignment, Control_DC, Economy, Loyalty, Stability, Fame, Unrest, Consumption from kingdoms""")
        kingdoms = cursor.fetchall()
        for kingdom in kingdoms:
            cursor.execute(f"""SELECT Economy, Loyalty, Stability FROM AA_Alignment WHERE Alignment = '{kingdom[1]}'""")
            alignment = cursor.fetchone()
            cursor.execute(f"""SELECT Control_DC, Economy, Loyalty, Stability, Fame, Unrest, Consumption from Kingdoms_Custom WHERE kingdom = '{kingdom[0]}'""")
            custom_info = cursor.fetchone()
            cursor.execute(f"""SELECT SUM(economy), SUM(Loyalty), SUM(Stability), SUM(Unrest) FROM leadership WHERE kingdom = '{kingdom[0]}'""")
            sum_leadership = cursor.fetchone()
            cdc = custom_info[0] + kingdom[2]
            econ = custom_info[1] + kingdom[3] + alignment[0] + sum_leadership[0]
            loy = custom_info[2] + kingdom[4] + alignment[1] + sum_leadership[1]
            stab = custom_info[3] + kingdom[5] + alignment[2] + sum_leadership[2]
            fam = custom_info[4] + kingdom[6]
            unr = custom_info[5] + kingdom[7] + sum_leadership[3]
            cons = custom_info[6] + kingdom[8]
            sql = f"""Update kingdoms SET Control_DC = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ?, Consumption = ? WHERE kingdom = '{kingdom[0]}'"""
            val = (cdc, econ, loy, stab, fam, unr, cons)
            cursor.execute(sql, val)
        """NOTE: UPDATE KINGDOM SETTLEMENTS"""
        sql = f"""UPDATE settlements SET size = ?, Population = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ?"""
        val = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        cursor.execute(sql, val)
        cursor.execute(f"""SELECT Kingdom, Settlement, Corruption, Crime, Law, Lore, Productivity, Society, Danger, Defence, Base_Value, Spellcasting, Supply FROM settlements""")
        settlement_info = cursor.fetchall()
        for settlement in settlement_info:
            cursor.execute(f"""SELECT Government FROM kingdoms WHERE kingdom = '{settlement[0]}'""")
            government = cursor.fetchone()
            cursor.execute(f"""SELECT Corruption, Crime, Law, Lore, Productivity, Society FROM AA_Government WHERE Government = '{government[0]}'""")
            government_info = cursor.fetchone()
            cursor.execute(f"""SELECT Corruption, Crime, Law, Lore, Productivity, Society, Danger, Defence, Base_Value, Spellcasting, Supply FROM Settlements_Custom WHERE Kingdom = '{settlement[0]}' AND Settlement = '{settlement[1]}'""")
            custom_info = cursor.fetchone()
            corruption = settlement[2] + government_info[0] + custom_info[0]
            crime = settlement[3] + government_info[1] + custom_info[1]
            law = settlement[4] + government_info[2] + custom_info[2]
            lore = settlement[5] + government_info[3] + custom_info[3]
            productivity = settlement[6] + government_info[4] + custom_info[4]
            society = settlement[7] + government_info[5] + custom_info[5]
            danger = settlement[8] + custom_info[6]
            defence = settlement[9] + custom_info[7]
            base_value = settlement[10] + custom_info[8]
            spellcasting = settlement[11] + custom_info[9]
            supply = settlement[12] + custom_info[10]
            sql = f"""UPDATE settlements SET Corruption = ?, Crime = ?, Law = ?, Lore = ?, Productivity = ?, Society = ?, Danger = ?, Defence = ?, Base_Value = ?, Spellcasting = ?, Supply = ? WHERE Kingdom = '{settlement[0]}' AND Settlement = '{settlement[1]}'"""
            val = (corruption, crime, law, lore, productivity, society, danger, defence, base_value, spellcasting, supply)
            cursor.execute(sql, val)
        """NOTE: UPDATE ALL Buildings FOR ALL SETTLEMENTS"""
        cursor.execute(f"""SELECT * FROM Buildings""")
        holding_info = cursor.fetchall()
        for holding in holding_info:
            cursor.execute(f"""SELECT Build_Points, Lots, Economy, Loyalty, Stability, Fame, Unrest, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_value, Spellcasting, Supply from Buildings_Blueprints where Building = '{holding[2]}'""")
            building_info = cursor.fetchone()
            sql = f"""UPDATE Buildings SET lots = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_value = ?, Spellcasting = ?, Supply = ? WHERE kingdom = '{holding[0]}' AND Settlement = '{holding[1]}' AND Building = '{holding[2]}'"""
            val = (building_info[1] * holding[3], building_info[2] * holding[3], building_info[3] * holding[3], building_info[4] * holding[3], building_info[5] * holding[3], building_info[6] * holding[3], building_info[7] * holding[3], building_info[8] * holding[3], building_info[9] * holding[3], building_info[10] * holding[3], building_info[11] * holding[3], building_info[12] * holding[3], building_info[13] * holding[3], building_info[14] * holding[3], building_info[15] * holding[3], building_info[16] * holding[3], building_info[17] * holding[3])
            cursor.execute(sql, val)
            cursor.execute(f"""SELECT Size, Population, Corruption, Crime, Productivity, Law, Lore, Society, Danger, Defence, Base_Value, Spellcasting, Supply FROM Settlements WHERE Kingdom = '{holding[0]}' AND Settlement = '{holding[1]}'""")
            settlement_info = cursor.fetchone()
            sql = f"""UPDATE settlements SET size = ?, Population = ?, Corruption = ?, Crime = ?, Productivity = ?, Law = ?, Lore = ?, Society = ?, Danger = ?, Defence = ?, Base_value = ?, Spellcasting = ?, Supply = ? WHERE Kingdom = '{holding[0]}' AND Settlement = '{holding[1]}'"""
            val = (settlement_info[0] + (holding[3] * building_info[1] / 4), settlement_info[1] + holding[3] * building_info[1] * 50, settlement_info[2] + building_info[7] * holding[3], settlement_info[3] + building_info[8] * holding[3], settlement_info[4] + building_info[9] * holding[3], settlement_info[5] + building_info[10] * holding[3], settlement_info[6] + building_info[11] * holding[3], settlement_info[7] + building_info[12] * holding[3], settlement_info[8] + building_info[13] * holding[3], settlement_info[9] + building_info[14] * holding[3], settlement_info[10] + building_info[15] * holding[3], settlement_info[11] + building_info[16] * holding[3], settlement_info[12] + building_info[17] * holding[3])
            cursor.execute(sql, val)
            cursor.execute(f"""SELECT Control_DC, Population, Economy, Loyalty, Stability, Fame, Unrest FROM kingdoms WHERE kingdom = '{holding[0]}'""")
            kingdom_info = cursor.fetchone()
            sql = f"""UPDATE kingdoms set Control_DC = ?, Population = ?, Economy = ?, Loyalty = ?, Stability = ?, Fame = ?, Unrest = ? WHERE kingdom = '{holding[0]}'"""
            val = (kingdom_info[0] + (holding[3] * building_info[1] / 4), kingdom_info[1] + holding[3] * building_info[1] * 50, kingdom_info[2] + building_info[2] * holding[3], kingdom_info[3] + building_info[3] * holding[3], kingdom_info[4] + building_info[4] * holding[3], kingdom_info[5] + building_info[5] * holding[3], kingdom_info[6] + building_info[6] * holding[3])
            cursor.execute(sql, val)
        """NOTE: UPDATE ALL KINGDOMS BASED OFF OF HEXES"""
        cursor.execute(f"""SELECT Kingdom, Amount, Improvement, Economy, Loyalty, Stability, Unrest, Consumption, Defence FROM Hexes""")
        hex_info = cursor.fetchall()
        for hexes in hex_info:
            cursor.execute(f"""SELECT Economy, Loyalty, Stability, Unrest, Consumption, Control_DC FROM kingdoms where kingdom = '{hexes[0]}'""")
            kingdom_info = cursor.fetchone()
            control_dc = kingdom_info[5] + hexes[1]
            if hexes[2] == 'None':
                cursor.execute(f"""UPDATE Kingdoms SET Control_DC = '{control_dc}' WHERE kingdom = '{hexes[0]}' """)
            if hexes[2] != 'None':
                cursor.execute(f"""SELECT Economy, Loyalty, Stability, Unrest, Consumption, Defence FROM Hexes_Improvements WHERE Improvement = '{hexes[2]}'""")
                renovation_info = cursor.fetchone()
                sql = f"""UPDATE hexes SET Economy = ?, Loyalty = ?, Stability = ?, Unrest = ?, Consumption = ?, Defence = ? WHERE kingdom = '{hexes[0]}' AND Improvement = '{hexes[2]}'"""
                val = (hexes[1] * renovation_info[0], hexes[1] * renovation_info[1], hexes[1] * renovation_info[2], hexes[1] * renovation_info[3], hexes[1] * renovation_info[4], hexes[1] * renovation_info[5])
                cursor.execute(sql, val)
                sql = f"""UPDATE kingdoms SET Control_DC = ?, Economy = ?, Loyalty = ?, Stability = ?, Unrest = ?, Consumption = ? WHERE kingdom = '{hexes[1]}'"""
                val = (control_dc, kingdom_info[0] + hexes[1] * renovation_info[0], kingdom_info[1] + hexes[1] * renovation_info[1], kingdom_info[2] + hexes[1] * renovation_info[2], kingdom_info[3] + hexes[1] * renovation_info[3], kingdom_info[4] + hexes[1] * renovation_info[4])
                cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, 'N/A', time, 'all tables', 'Massive Table rebalance', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def adjust_build_points(self, kingdom, build_points, guild_id, character_name, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Build_Points FROM Kingdoms WHERE Kingdom = '{kingdom}'""")
        bp = cursor.fetchone()
        tbp = bp[0] + build_points
        cursor.execute(f"""UPDATE Kingdoms SET Build_Points = {tbp} WHERE Kingdom = '{kingdom}'""")
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, character_name, time, 'Kingdoms', f'adjusting build points for {kingdom}', build_points, 'N/A')
        cursor.execute(sql, val)
        cursor.execute(f"""SELECT gold from Player_Characters where Character_Name = ? AND Player_Name = ?""", (character_name, author))
        gold = cursor.fetchone()
        cost = build_points * 4000
        value = gold[0] - cost
        cursor.execute(f"""UPDATE Player_Characters SET Gold = '{value}' WHERE Character_Name = ? AND Player_Name = ?""", (character_name, author))
        db.commit()
        cursor.close()
        db.close()

    async def adjust_stabilization_points(self, kingdom, stabilization_points, guild_id, author, character_name_true):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"""SELECT Stabilization_Points FROM Kingdoms WHERE Kingdom = '{kingdom}'""")
        sp = cursor.fetchone()
        tsp = sp[0] + stabilization_points
        cursor.execute(f"""UPDATE Kingdoms SET Stabilization_Points = {tsp} WHERE Kingdom = '{kingdom}'""")
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, character_name_true, time, 'Kingdoms', f'adjusting stabilization points for {kingdom}', stabilization_points, 'N/A')
        cursor.execute(sql, val)
        cursor.execute(f"""SELECT gold from Player_Characters where Character_Name = ? AND Player_Name = ?""", (character_name_true, author))
        gold = cursor.fetchone()
        cost = stabilization_points * 4000
        value = gold[0] - cost
        cursor.execute(f"""UPDATE Player_Characters SET Gold = ? WHERE ? AND Player_Name = ?""", (value, character_name_true, author))
        db.commit()
        cursor.close()
        db.close()

    async def settlement_decay_set(self, kingdom, settlement, decay, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"""UPDATE Settlements SET Decay = ? WHERE Kingdom = ? AND Settlement = ?"""
        val = (decay, kingdom, settlement)
        cursor.execute(sql, val)
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, 'N/A', time, 'Settlements', f'settlement decay for {kingdom}s {settlement}', decay, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def gold_change(self, guild_id, author_name, author_id, character_name, amount, expected_value, lifetime_value, reason, source):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        print(character_name, amount, expected_value, lifetime_value, reason, source)
        sql = f"""SELECT Character_Name, Gold, Gold_Value, Gold_Value_Max from Player_Characters WHERE Character_Name = ?"""
        val = (character_name,)
        cursor.execute(sql, val)
        character_information = cursor.fetchone()
        new_gold = character_information[1] + amount
        new_gold_value = character_information[2] + expected_value
        new_gold_value_max = character_information[3] + lifetime_value
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE Player_Characters SET gold = ?, gold_value = ?, gold_value_max = ? WHERE Character_Name = ?"
        val = (new_gold, new_gold_value, new_gold_value_max, character_name)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_Gold(Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
        val = (author_name, author_id, character_name, amount, expected_value, lifetime_value, reason, source, time)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def gold_set(self, guild_id, author_name, author_id, character_name, amount, expected_value, lifetime_value, reason, source, table):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        new_gold = amount
        new_gold_value = expected_value
        new_gold_value_max = lifetime_value
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if table == 1:
            sql = f"UPDATE Player_Characters SET gold = ?, gold_value = ?, gold_value_max = ? WHERE Character_Name = ?"
            val = (amount, expected_value, lifetime_value, character_name)
            cursor.execute(sql, val)
        else:
            sql = f"UPDATE A_STG_Player_Characters SET gold = ?, gold_value = ?, gold_value_max = ? WHERE Character_Name = ?"
            val = (amount, expected_value, lifetime_value, character_name)
            cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_Gold(Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
        val = (author_name, author_id, character_name, new_gold, new_gold_value, new_gold_value_max, reason, source, time)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def title_change(self, guild_id, author, author_id, true_character_name, title_name, total_fame, total_prestige, reason, source):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE Player_Characters SET Title = ?, Fame = ?, prestige = ? WHERE Character_Name = ?"
        val = (title_name, total_fame, total_prestige, true_character_name)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?)"
        val = (author, time, 'player_characters', source, total_fame, reason)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def proposition_open(self, guild_id, author, author_id, true_character_name, item_name, prestige_cost, reason, source):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"INSERT INTO A_Audit_Prestige(Author_ID, Character_Name, Item_Name, Prestige_Cost, IsAllowed) VALUES (?, ?, ?, ?, ?)"
        val = (author_id, true_character_name, item_name, prestige_cost, 1)
        cursor.execute(sql, val)
        sql = f"Select Prestige from Player_Characters WHERE Character_Name = ?"
        val = (true_character_name, )
        cursor.execute(sql, val)
        prestige = cursor.fetchone()
        new_prestige = prestige[0] - prestige_cost
        sql = f"UPDATE Player_Characters SET Prestige = ? WHERE Character_Name = ?"
        val = (new_prestige, true_character_name)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?)"
        val = (author, time, 'A_Audit_Prestige', source, prestige_cost, reason)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def proposition_reject(self, guild_id, author, proposition_id, reason, source):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE A_Audit_Prestige SET IsAllowed = ? WHERE Proposition_ID = ?"
        val = (0, proposition_id)
        cursor.execute(sql, val)
        sql = f"SELECT Character_Name, Item_Name, Prestige_Cost FROM A_Audit_Prestige WHERE Proposition_ID = ?"
        val = (proposition_id, )
        rejected_item = cursor.execute(sql, val)
        sql = f"SELECT Prestige FROM Player_Characters WHERE Character_Name = ?"
        val = (rejected_item[0], )
        character = cursor.execute(sql, val)
        new_prestige = character[0] + rejected_item[2]
        sql = f"UPDATE Player_Characters SET Prestige = ? WHERE Character_Name = ?"
        val = (new_prestige, rejected_item[0])
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?)"
        val = (author, time, 'A_Audit_Prestige', source, prestige_cost, reason)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def glorify(self, guild_id, author, character, fame, prestige, reason):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE Player_Characters SET Fame = ?, Prestige = ? WHERE Character_Name = ?"
        val = (fame, prestige, character)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?)"
        val = (author, time, 'Player_Characters', f'Glorifying character by changing their fame to {fame} and prestige to {prestige}', prestige, reason)
        cursor.execute(sql, val)
        sql = f"Insert into A_Audit_Prestige(Author, Character_Name, Item_Name, Prestige_Cost, IsAllowed) VALUES(?, ?, ?, ?, ?)"
        val = (author, character, 'Glorified', prestige, 1)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()



    async def stg_gold_change(self, guild_id, author_name, author_id, character_name, amount, expected_value, lifetime_value, reason, source):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"""SELECT Character_Name, Gold, Gold_Value, Gold_Value_Max from A_STG_Player_Characters WHERE Character_Name = ? and Player_Name = ?"""
        val = (character_name, author_name)
        cursor.execute(sql, val)
        character_information = cursor.fetchone()
        new_gold = character_information[1] + amount
        new_gold_value = character_information[2] + expected_value
        new_gold_value_max = character_information[3] + lifetime_value
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE A_STG_Player_Characters SET gold = ?, gold_value = ?, gold_value_max = ? WHERE Character_Name = ?"
        val = (new_gold, new_gold_value, new_gold_value_max, character_name)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_Gold(Author_Name, Author_ID, Character_Name, Gold_Value, Effective_Gold_Value, Effective_Gold_Value_Max, Reason, Source_Command, Time) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
        val = (author_name, author_id, character_name, amount, expected_value, lifetime_value, reason, source, time)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def undo_transaction(self, guild_id, transaction_id, amount, expected_value, lifetime_value, character_name, player_name):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        print(transaction_id, amount, expected_value, lifetime_value, character_name)
        sql = f"""SELECT Character_Name, Gold, Gold_Value, Gold_Value_Max from Player_Characters WHERE Character_Name = ?"""
        val = (character_name, )
        cursor.execute(sql, val)
        character_information = cursor.fetchone()
        print(character_information)
        new_gold = character_information[1] + amount
        new_gold_value = character_information[2] + expected_value
        new_gold_value_max = character_information[3] + lifetime_value
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE Player_Characters SET gold = ?, gold_value = ?, gold_value_max = ? WHERE Character_Name = ?"
        val = (new_gold, new_gold_value, new_gold_value_max, character_name)
        cursor.execute(sql, val)
        sql = f"UPDATE A_Audit_Gold SET Gold_Value = ?, Effective_Gold_Value = ?, Effective_Gold_Value_Max = ?, Reason = ?, Source_Command = ? WHERE Transaction_ID = {transaction_id}"
        val = (amount, expected_value, lifetime_value, 'Transaction Cancelled!', 'Undo Transaction')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def gold_transact(self, transaction_id, related_id, guild_id):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"UPDATE A_Audit_Gold SET Related_Transaction_ID = {related_id} WHERE Transaction_ID = {transaction_id}")
        db.commit()
        cursor.close()
        db.close()

    async def adjust_milestones(self, character_name, milestone_total, remaining, character_level, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"SELECT Player_Name, Player_ID, Character_Name, Level, Trials, Tier FROM Player_Characters where Character_Name = ?", (character_name,))
        characters = cursor.fetchone()
        cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Trials <= {characters[4]} ORDER BY Trials DESC  LIMIT 1")
        current_mythic_information = cursor.fetchone()
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Cap'")
        max_tier = cursor.fetchone()
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
        break_point = cursor.fetchone()
        if characters[3] <= int(break_point[0]):
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
            tier_rate_limit = cursor.fetchone()
        else:
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
            tier_rate_limit = cursor.fetchone()
        rate_limited_tier = floor(character_level / int(tier_rate_limit[0]))
        true_tier = int(max_tier[0]) if current_mythic_information[0] > int(max_tier[0]) else current_mythic_information[0]
        true_tier = true_tier if true_tier <= rate_limited_tier else rate_limited_tier
        print(character_level)
        if true_tier == int(max_tier[0]) or true_tier == rate_limited_tier:
            cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Tier = {true_tier}")
            current_mythic_information = cursor.fetchone()
        else:
            current_mythic_information = current_mythic_information
        trials_required = current_mythic_information[1] + current_mythic_information[2] - characters[4]
        true_tier = 0 if characters[5] == 0 else true_tier
        print(character_name)
        sql = f"UPDATE Player_Characters set Level = ?, Milestones = ?, Milestones_Required = ?, Tier = ?, Trials_Required = ? where Character_Name = ?"
        val = (character_level, milestone_total, remaining, true_tier, trials_required, character_name)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?)"
        val = (time, 'player_characters', 'milestones to level', milestone_total, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def adjust_personal_cap(self, guild_id, author, character_name, level_cap):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"SELECT Player_Name, Player_ID, Character_Name, Level, Trials, Tier, Milestones FROM Player_Characters where Player_Name = ? and Character_Name = ?", (author, character_name))
        characters = cursor.fetchone()
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Level_Cap'")
        max_level = cursor.fetchone()
        cursor.execute(f"SELECT Level, Minimum_Milestones, Milestones_To_Level FROM AA_Milestones WHERE Minimum_Milestones <= {characters[6]} ORDER BY Minimum_Milestones DESC  LIMIT 1")
        milestone_level = cursor.fetchone()
        level = milestone_level[0] if milestone_level[0] < level_cap else level_cap
        level = level if level <= int(max_level[0]) else int(max_level[0])
        cursor.execute(f"SELECT Minimum_Milestones, Milestones_To_Level FROM AA_Milestones WHERE Level = {level}")
        milestone_information = cursor.fetchone()
        cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Trials <= {characters[4]} ORDER BY Trials DESC  LIMIT 1")
        current_mythic_information = cursor.fetchone()
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Cap'")
        max_tier = cursor.fetchone()
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
        break_point = cursor.fetchone()
        if characters[3] <= int(break_point[0]):
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
            tier_rate_limit = cursor.fetchone()
        else:
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
            tier_rate_limit = cursor.fetchone()
        rate_limited_tier = floor(level / int(tier_rate_limit[0]))
        true_tier = int(max_tier[0]) if current_mythic_information[0] > int(max_tier[0]) else current_mythic_information[0]
        true_tier = true_tier if true_tier <= rate_limited_tier else rate_limited_tier
        if true_tier == int(max_tier[0]) or true_tier == rate_limited_tier:
            cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Tier = {true_tier}")
            current_mythic_information = cursor.fetchone()
        else:
            current_mythic_information = current_mythic_information
        trials_required = current_mythic_information[1] + current_mythic_information[2] - characters[4]
        true_tier = 0 if characters[5] == 0 else true_tier
        sql = f"UPDATE Player_Characters set Level = ?, Milestones = ?, Milestones_Required = ?, Tier = ?, Trials_Required = ?, Personal_Cap = ? where Character_Name = ? and Player_Name = ?"
        val = (level, characters[6], characters[6] - (milestone_information[0] + milestone_information[1]), true_tier, trials_required, level_cap, character_name, author)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?)"
        val = (time, 'player_characters', 'milestones to level', level_cap, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def adjust_trials(self, character_name, total_trials, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        print(f"MYTHIC INFO: {character_name, total_trials, author}")
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"SELECT Player_Name, Player_ID, Character_Name, Level, Trials FROM Player_Characters where Character_Name = ?", (character_name,))
        characters = cursor.fetchone()
        cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Trials <= {total_trials} ORDER BY Trials DESC  LIMIT 1")
        current_mythic_information = cursor.fetchone()
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Cap'")
        max_tier = cursor.fetchone()
        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
        break_point = cursor.fetchone()
        if characters[3] <= int(break_point[0]):
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
            tier_rate_limit = cursor.fetchone()
        else:
            cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
            tier_rate_limit = cursor.fetchone()
        rate_limited_tier = floor(characters[3] / int(tier_rate_limit[0]))
        true_tier = int(max_tier[0]) if current_mythic_information[0] > int(max_tier[0]) else current_mythic_information[0]
        true_tier = true_tier if true_tier <= rate_limited_tier else rate_limited_tier
        if true_tier == int(max_tier[0]) or true_tier == rate_limited_tier:
            cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Tier = {true_tier}")
            current_mythic_information = cursor.fetchone()
        else:
            current_mythic_information = current_mythic_information
        trials_required = current_mythic_information[1] + current_mythic_information[2] - total_trials
        sql = f"UPDATE Player_Characters set Tier = ?, Trials = ?, Trials_Required = ? where Character_Name = ?"
        val = (true_tier, total_trials, trials_required, character_name)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, character_name, time, 'player_characters', 'mythic trials', total_trials, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def retire_character(self, guild_id, character_name, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"DELETE FROM Player_Characters WHERE Character_Name = ?", (character_name,))
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, character_name, time, 'player_characters', f'deleted {character_name}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def wipe_inactive(self, player_id, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"DELETE FROM Player_Characters WHERE Player_ID = '{player_id}'")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, player_id, time, 'player_characters', f"deleted {player_id}'s characters", 0, 'N/A')
        cursor.execute(f"DELETE FROM A_Audit_Gold WHERE Author_ID = '{player_id}'")
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def wipe_unapproved(self, character_name, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"DELETE FROM A_STG_Player_Characters WHERE character_name = '{character_name}'")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, character_name, time, 'A_STG_player_characters', f"deleted {character_name}'s characters", 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def stage_character(self, true_character_name, character_name, author, author_id, guild_id, nickname, titles, description, oath_name, mythweavers, image_link, color, backstory):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"INSERT INTO A_STG_Player_Characters(Player_Name, Player_ID, True_Character_Name, Character_Name, Nickname, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_Value_Max, Mythweavers, Image_Link, Color, Flux, Created_Date, tmp_bio) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        val = (author, author_id, true_character_name, character_name, nickname, titles, description, oath_name, 3, 0, 0, 3, 0, 0, 0, 0, 0, mythweavers, image_link, color, 0, time, backstory)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, character_name, time, 'player_characters', f'staged {character_name}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def create_character(self, guild_id, author, true_character_name):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"SELECT Player_Name, Player_ID, True_Character_Name, Character_Name, Nickname, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_Value_Max, Mythweavers, Image_Link, Color, Flux FROM A_STG_Player_Characters WHERE True_Character_Name = ?", (true_character_name,))
        character_info = cursor.fetchone()
        sql = f"INSERT INTO Player_Characters(Player_Name, Player_ID, True_Character_Name, Character_Name, Nickname, Titles, Description, Oath, Level, Tier, Milestones, Milestones_Required, Trials, Trials_Required, Gold, Gold_Value, Gold_Value_Max, Mythweavers, Image_Link, Color, Flux, Fame, Prestige, Accepted_Date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        val = (character_info[0], character_info[1], character_info[2], character_info[3], character_info[4], character_info[5], character_info[6], character_info[7], character_info[8], character_info[9], character_info[10], character_info[11], character_info[12], character_info[13], character_info[14], character_info[15], character_info[16], character_info[17], character_info[18], character_info[19], character_info[20], 0 , 0, time)
        cursor.execute(sql, val)
        cursor.execute(f"DELETE FROM A_STG_Player_Characters WHERE True_Character_Name = ?", (true_character_name,))
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author[0], character_info[2], time, 'player_characters', f'accepted {character_info[2]}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def create_bio(self, guild_id, true_character_name, bio, link):
        if guild_id == 883009758179762208:
            if bio[:4] == "http":
                parts = bio.split('/')
                if len(parts) == 5:
                    link = parts[3]
                elif len(parts) == 7:
                    link = parts[5]
                else:
                    link = None
            if link is not None:
                bio = drive_word_document(link)
            else:
                bio = bio
            client = WaClient(
                'Pathparser',
                'https://github.com/Solfyrism/Pathparser',
                'V1.1',
                os.getenv('WORLD_ANVIL_API'),
                os.getenv('WORLD_ANVIL_USER')
            )
            world_id = 'f7a60480-ea15-4867-ae03-e9e0c676060a'
            new_page = None
            if 'worldanvil' in link:
                article_list = [article for article in client.world.articles('f7a60480-ea15-4867-ae03-e9e0c676060a', 'c8fd1251-1077-4bbd-a9a5-797b3dbdf356')]
                for articles in article_list:
                    if true_character_name in articles['title']:
                        new_page = articles
            else:
                new_page = client.article.put({
                    'title': f'{true_character_name}',
                    'content': f'{bio}',
                    'category': {'id': 'c8fd1251-1077-4bbd-a9a5-797b3dbdf356'},
                    'templateType': 'person',  # generic article template
                    'state': 'public',
                    'isDraft': False,
                    'entityClass': 'Person',
                    'world': {'id': world_id}
                })
            db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
            cursor = db.cursor()
            cursor.execute(f"UPDATE Player_Characters SET Article_Link = ?, Article_ID = ? WHERE True_Character_Name = ?", (new_page['url'], new_page['id'], true_character_name))
            db.commit()
            cursor.close()
            db.close()


    async def edit_bio(self, guild_id, true_character_name, bio, article_id):
        if guild_id == 883009758179762208:
            client = WaClient(
                'Pathparser',
                'https://github.com/Solfyrism/Pathparser',
                'V1.1',
                os.getenv('WORLD_ANVIL_API'),
                os.getenv('WORLD_ANVIL_USER')
            )
            world_id = 'f7a60480-ea15-4867-ae03-e9e0c676060a'
            if bio is None:
                new_page = client.article.patch(article_id, {
                    'title': f'{true_character_name}',
                    'world': {'id': world_id}
                })
            elif bio is not None:
                if bio[:4] == "http":
                    parts = bio.split('/')
                    if len(parts) == 5:
                        link = parts[3]
                    elif len(parts) == 7:
                        link = parts[5]
                    else:
                        link = None
                if link is not None:
                    bio = drive_word_document(link)
                else:
                    bio = bio
                new_page = client.article.patch(article_id, {
                    'title': f'{true_character_name}',
                    'content': f'{bio}',
                    'world': {'id': world_id}
                })
            db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
            cursor = db.cursor()
            cursor.execute(f"UPDATE Player_Characters SET Article_Link = ?, Article_ID = ? WHERE True_Character_Name = ?", (new_page['url'], new_page['id'], true_character_name))
            db.commit()
            cursor.close()
            db.close()

    async def session_report(self, guild_id,  overview, session_id, character_name, author):
            if guild_id == 883009758179762208:
                time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                client = WaClient(
                    'pathparser',
                    'https://github.com/Solfyrism/Pathparser',
                    'V1.1',
                    os.getenv('WORLD_ANVIL_API'),
                    os.getenv('WORLD_ANVIL_USER')
                )
                world_id = 'f7a60480-ea15-4867-ae03-e9e0c676060a'
                if overview[:4] == "http":
                    parts = overview.split('/')
                    if len(parts) == 5:
                        link = parts[3]
                    elif len(parts) == 7:
                        link = parts[5]
                    else:
                        link = None
                else:
                    link = None
                if link is not None:
                    overview = drive_word_document(link)
                else:
                    overview = overview
                db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
                cursor = db.cursor()
                cursor.execute(f"SELECT Article_ID from Sessions where Session_ID = ?", (session_id,))
                session_info = cursor.fetchone()
                specific_article = client.article.get(f'{session_info[0]}', granularity=str(1))
                cursor.close()
                db.close()
                new_overview = f'{specific_article["reportNotes"]} [br] [br] {character_name} - {time} [br] {overview}' if specific_article["reportNotes"] is not None else f'{character_name} - {time} [br] {overview}'
                new_page = client.article.patch(session_info[0], {
                    'reportNotes': f'{new_overview}',
                    'world': {'id': world_id}
                })

    async def plot(self, guild_id, type, plot, overview, author):
        if guild_id == 883009758179762208:
            client = WaClient(
                'pathparser',
                'https://github.com/Solfyrism/Pathparser',
                'V1.1',
                os.getenv('WORLD_ANVIL_API'),
                os.getenv('WORLD_ANVIL_USER')
            )
            world_id = 'f7a60480-ea15-4867-ae03-e9e0c676060a'
            if overview[:4] == "http":
                parts = overview.split('/')
                print(len(parts))
                if len(parts) == 5:
                    print(f"No HTTPS")
                    link = parts[3]
                elif len(parts) == 7:
                    print(f"Yes HTTPS")
                    link = parts[5]
                else:
                    link = None
                print(f"Link yelled! {link}")
            else:
                link = None
            if link is not None:
                print(f"linkie found")
                overview = drive_word_document(link)
            else:
                overview = overview
                print(f"no linkie")
            if type == 1:
                print(1)
                new_page = client.article.patch(plot, {
                    'content': f'{overview}',
                    'world': {'id': world_id}
                })
            elif type == 2:
                new_page = client.article.put({
                    'title': f'{plot}',
                    'content': f'{overview}',
                    'category': {'id': '9ad3d530-1a42-4e99-9a09-9c4dccddc70a'},
                    'templateType': 'plot',  # generic article template
                    'state': 'public',
                    'isDraft': False,
                    'entityClass': 'Plot',
                    'tags': f'{author}',
                    'world': {'id': world_id}
                })
                print(2)
            print(new_page)


    async def report(self, guild_id, request_type, plot, overview, session_id, author, significance):
        if guild_id == 883009758179762208:
            client = WaClient(
                'pathparser',
                'https://github.com/Solfyrism/Pathparser',
                'V1.1',
                os.getenv('WORLD_ANVIL_API'),
                os.getenv('WORLD_ANVIL_USER')
            )
            world_id = 'f7a60480-ea15-4867-ae03-e9e0c676060a'
            if overview[:4] == "http":
                parts = overview.split('/')
                if len(parts) == 5:
                    link = parts[3]
                elif len(parts) == 7:
                    link = parts[5]
                else:
                    link = None
            else:
                link = None
            if link is not None:
                overview = drive_word_document(link)
            else:
                overview = overview
            if request_type == 1:
                print(1)
                db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
                cursor = db.cursor()
                cursor.execute(
                    f"SELECT Article_ID, History_ID from Sessions where Session_ID = ?", (session_id,))
                session_info = cursor.fetchone()
                specific_article = client.article.get(f'{session_info[0]}', granularity=str(1))

                original_article = specific_article['content']
                cursor.execute(
                    f"SELECT Article_ID from Sessions where Session_ID = ?", (session_id,))

                session_info = cursor.fetchone()
                new_page = client.article.patch(session_info[0], {
                    'content': f'{overview}',
                    'world': {'id': world_id}
                })
                new_history = client.history.patch(session_info[0], {
                    'content': f'{overview}',
                    'world': {'id': world_id}
                })
                cursor.close()
                db.close()
            elif request_type == 2:
                db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
                cursor = db.cursor()
                cursor.execute(f"SELECT Session_Name, Completed_Time, Alt_Reward_Party, Alt_Reward_All, Overview from Sessions where Session_ID = ?", (session_id,))
                session_info = cursor.fetchone()
                cursor.execute(f"SELECT SA.Character_Name, PC.Article_Link, Article_ID FROM Sessions_Archive as SA left join Player_Characters AS PC on PC.Character_Name = SA.Character_Name WHERE SA.Session_ID = ? and SA.Player_Name != ? ", (session_id, author))
                characters = cursor.fetchall()
                print(len(characters))
                if len(characters) == 0:
                    cursor.execute(f"SELECT SA.Character_Name, PC.Article_Link, Article_ID FROM Sessions_Participants as SA left join Player_Characters AS PC on PC.Character_Name = SA.Character_Name WHERE SA.Session_ID = ? and SA.Player_Name != ? ", (session_id, author))
                    characters = cursor.fetchall()
                else:
                    characters = characters
                relatedpersonsblock = []
                counter = 0
                completed_str = session_info[1] if session_info[1] is not None else datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                completed_time = datetime.datetime.strptime(completed_str, '%Y-%m-%d %H:%M')
                day_test = datetime.datetime.strftime(completed_time, '%d')
                month_test = datetime.datetime.strftime(completed_time, '%m')

                new_report_page = client.article.put({
                    'title': f'{str(session_id).rjust(3, "0")}: {session_info[0]}',
                    'content': f'{overview}',
                    'category': {'id': 'b71f939a-f72d-413b-b4d7-4ebff1e162ca'},
                    'templateType': 'report',  # generic article template
                    'state': 'public',
                    'isDraft': False,
                    'entityClass': 'Report',
                    'tags': f'{author}',
                    'world': {'id': world_id},
                    #                  'reportDate': report_date,  # Convert the date to a string
                    'plots': [{'id': plot}]
                })
                for character in characters:
                    print(f" This is a character {character[0]} Do they have an article: {character[2]}?")
                    if character[2] is not None:
                        person = {'id': character[2]}
                        relatedpersonsblock.append(person)
                        counter += 1
                if counter == 0:
                    new_timeline_page = client.history.put({
                        'title': f'{session_info[0]}',
                        'content': f'{session_info[4]}',
                        'fullcontent': f'{overview}',
                        'timelines': [{'id': '906c8c14-2283-47e0-96e2-0fcd9f71d0d0'}],
                        'significance': significance,
                        'parsedContent': session_info[4],
                        'report': {'id': new_report_page['id']},
                        'year': 22083,
                        'month': int(month_test),
                        'day': int(day_test),
                        'endingYear': int(22083),
                        'endingMonth': int(month_test),
                        'endingDay': int(day_test),
                        'world': {'id': world_id}
                    })
                else:
                    relatedpersonsblock = relatedpersonsblock
                    print(f"this is the related person's block {relatedpersonsblock}")
                    new_timeline_page = client.history.put({
                        'title': f'{session_info[0]}',
                        'content': f'{session_info[4]}',
                        'fullcontent': f'{overview}',
                        'timelines': [{'id': '906c8c14-2283-47e0-96e2-0fcd9f71d0d0'}],
                        'significance': significance,
                        'characters': relatedpersonsblock,
                        'parsedContent': session_info[4],
                        'report': {'id': new_report_page['id']},
                        'year': 22083,
                        'month': int(month_test),
                        'day': int(day_test),
                        'endingYear': int(22083),
                        'endingMonth': int(month_test),
                        'endingDay': int(day_test),
                        'world': {'id': world_id}
                    })
                cursor.execute(f"UPDATE Sessions SET Article_Link = ?, Article_ID = ?, History_ID = ? WHERE Session_ID = ?", (new_report_page['url'], new_report_page['id'], new_timeline_page['id'], session_id))
                db.commit()
                cursor.close()
                db.close()

    async def edit_stage_bio(self, guild_id, true_character_name, bio):
        if guild_id == 883009758179762208:
            db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
            cursor = db.cursor()
            cursor.execute(f"UPDATE a_stg_player_characters SET tmp_bio = ?, WHERE True_Character_Name = ?", (bio, true_character_name))
            db.commit()
            cursor.close()
            db.close()



    async def fix_character(self, guild_id, character_name):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"Update A_STG_Player_Characters SET Image_Link = ? AND Mythweavers = ? WHERE Character_Name = ?"
        val = ("https://cdn.discordapp.com/attachments/977939245463392276/1194140952789536808/download.jpg?ex=65af456d&is=659cd06d&hm=1613025f9f1c1263823881c91a81fc4b93831ff91df9f4a84c813e9fab6467e9&", "https://cdn.discordapp.com/attachments/977939245463392276/1194141019088891984/super_saiyan_mr_bean_by_zakariajames6_defpqaz-fullview.jpg?ex=65af457d&is=659cd07d&hm=57bdefe2d376face6a842a7b7a5ed8021e854a64e798f901824242c4a939a37b&", character_name)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def clean_stg(self, guild_id, author, true_character_name):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"DELETE FROM Player_Characters WHERE True_Character_Name = ?", (true_character_name,))
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author[0], true_character_name, time, 'player_characters', f'deleted {true_character_name} from stage', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def log_character(self, guild_id, character_name, message_id, logging_id, thread_id):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"Update Player_Characters SET Message_ID = ?, Logging_ID = ?, Thread_ID = ? WHERE character_name = ?"
        val = (message_id, logging_id, thread_id, character_name)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def edit_character(self, true_name, true_character_name, new_character_name, guild_id, new_nickname, titles, description, oath_name, mythweavers, image_link, color, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.close()
        db.close()
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"UPDATE Player_Characters SET True_Character_Name = ?, Character_name = ?, Nickname = ?, Titles = ?, Description = ?, Oath = ?, Mythweavers = ?, Image_Link = ?, Color = ? WHERE True_Character_Name = ?", (true_character_name, new_character_name, new_nickname, titles, description, oath_name, mythweavers, image_link, color, true_name))
        print(true_name, true_character_name, new_character_name)
        if true_name != new_character_name:
            sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
            val = (author, true_name, time, 'player_characters', f'edited {true_name} to be {new_character_name}', 0, 'N/A')
            cursor.execute(sql, val)
            sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
            val = (author, new_character_name, time, 'player_characters', f'edited {true_name} to be {new_character_name}', 0, 'N/A')
            cursor.execute(sql, val)
            cursor.execute("UPDATE A_Audit_Gold SET Character_Name = ? WHERE Character_Name = ?",(new_character_name, true_name))
            cursor.execute("UPDATE A_Audit_Prestige SET Character_Name = ? WHERE Character_Name = ?",(new_character_name, true_name))
            cursor.execute("UPDATE A_Audit_All SET Character = ? WHERE Character = ?", (new_character_name, true_name))
            cursor.execute("UPDATE Sessions_Participants SET Character_Name = ? WHERE Character_Name = ?", (new_character_name, true_name))
            cursor.execute("UPDATE Sessions_Signups SET Character_Name = ? WHERE Character_Name = ?", (new_character_name, true_name))
            cursor.execute("UPDATE Sessions_Archive SET Character_Name = ? WHERE Character_Name = ?", (new_character_name, true_name))
        else:
            sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
            val = (author, true_name, time, 'player_characters', f"edited {true_name}'s information", 0, 'N/A')
            cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def edit_stg_character(self, true_name, true_character_name, new_character_name, guild_id, new_nickname, titles, description, oath_name, mythweavers, image_link, color, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE A_STG_Player_Characters SET True_Character_Name = ?, Character_name = ?, Nickname = ?, Titles = ?, Description = ?, Oath = ?, Mythweavers = ?, Image_Link = ?, Color = ? WHERE Character_Name = ?"
        val = (true_character_name, new_character_name, new_nickname, titles, description, oath_name, mythweavers, image_link, color, true_name)
        cursor.execute(sql, val)
        if true_name != new_character_name:
            sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
            val = (author, true_name, time, 'player_characters', f'edited {true_name} to be {new_character_name}', 0, 'N/A')
            cursor.execute(sql, val)
            sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
            val = (author, new_character_name, time, 'player_characters', f'edited {true_name} to be {new_character_name}', 0, 'N/A')
            cursor.execute(sql, val)
        else:
            sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
            val = (author, true_name, time, 'player_characters', f"edited {true_name}'s information", 0, 'N/A')
            cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def session_rewards(self, author, guild_id, character_name, level, milestone_total, remaining, flux_total, tier, trials_total, trials_required, fame_total, prestige_total, reason):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE Player_Characters set Level = ?, Milestones = ?, Milestones_Required = ?, Flux = ?, Tier = ?, Trials = ?, Trials_Required = ?, fame = ?, prestige = ? where Character_Name = ?"
        val = (level, milestone_total, remaining, flux_total, tier, trials_total, trials_required, fame_total, prestige_total, character_name)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, character_name, time, 'player_characters', f'{reason}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def session_endowment(self, author, guild_id, player_name, personal_reward, session_id, character_name):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE Sessions_Archive set Alt_Reward_Personal = ? where player_name = ? and Session_ID = ?"
        val = (personal_reward, player_name, session_id)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, character_name, time, 'player_characters', f'Session {session_id} personal reward', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def create_session(self, gm_name, session_name, session_range, session_range_id, play_location, play_time, link, guild_id, author, overview, description, player_limit, overflow, plot):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"INSERT INTO Sessions(GM_Name, Session_Name, Session_Range, session_range_ID, Play_Location, Play_Time, Game_Link, Created_Time, overview, description, Player_Limit, IsActive, overflow, Related_Plot) Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        val = (gm_name, session_name, session_range, session_range_id, play_location, play_time, link, time, overview, description, player_limit, 1, overflow, plot)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, 'N/A', time, 'Sessions', 'New Session', 0, 'creating a DND session')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def create_session_message(self, session_id, message_id, thread_id, guild_id):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"UPDATE Sessions SET Message = ?, Session_Thread = ? WHERE Session_ID = ?"
        val = (message_id, thread_id, session_id)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def delete_session(self, session_id, guild_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"Delete from Sessions WHERE Session_ID = {session_id} and IsActive = 1")
        cursor.execute(f"Delete from Sessions_Participants WHERE Session_ID = {session_id}")
        cursor.execute(f"Delete from Sessions_Signups WHERE Session_ID = {session_id}")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, 'N/A', time, 'Sessions', f'Deleted Session: {session_id}', 0, 'creating a DND session')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def edit_session(self, guild_id, author, session_id, session_name, session_range_name, session_range_id, play_location, play_time, link, overflow):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE Sessions SET Session_Name = ?, Session_Range = ?, Session_Range_ID = ?, Play_Location = ?, Play_Time = ?, Game_Link = ?, overflow = ? WHERE Session_ID = {session_id}"
        val = (session_name, session_range_name, session_range_id, play_location, play_time, link, overflow)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, 'N/A', time, 'Sessions', 'Changing the information of a session', 0, 'editing a DnD Session')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def accept_player(self, guild_id, session_name, session_id, character_name, level, gold_value, player_name, player_id, author, tier):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"INSERT Into Sessions_Participants(Session_Name, Session_ID, Player_Name, Player_ID, Character_Name, Level, Effective_Wealth, tier) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        val = (session_name, session_id, player_name, player_id, character_name, level, gold_value, tier)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, character_name, time, 'Sessions_Participants', f'{character_name} is joining session {session_id}', 0, 'Joining DND session')
        cursor.execute(f"DELETE FROM Sessions_Signups WHERE Character_Name = ? AND Session_ID = ?", (character_name,session_id))
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def remove_player(self, guild_id, session_id, player_name, author, character_name):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"DELETE FROM Sessions_Participants WHERE Session_ID = {session_id} AND Player_Name = '{player_name}'")
        db.commit()
        cursor.execute(f"DELETE FROM Sessions_Archive WHERE Session_ID = {session_id} AND Player_Name = '{player_name}'")
        db.commit()
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, character_name, time, 'Sessions_Participents', f'{player_name} is removed from session {session_id}', 0, 'Removing player from DnD Session')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def session_join(self, guild_id, session_name, session_id, player_name, player_id, character_name, level, gold_value, tier):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        print(session_id)
        sql = f"INSERT Into Sessions_Signups(Session_Name, Session_ID, Player_Name, Player_ID, Character_Name, Level, Effective_Wealth, tier) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        val = (session_name, session_id, player_name, player_id, character_name, level, gold_value, tier)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (player_name, character_name, time, 'Sessions_Signups', f'{character_name} is signing up for session {session_id}', 0, 'Joining DND session')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def session_leave(self, guild_id, session_id, player_name, true_name):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"DELETE FROM Sessions_Signups WHERE Session_ID = {session_id} AND Player_Name = '{player_name}'")
        db.commit()
        cursor.execute(f"DELETE FROM Sessions_Participants WHERE Session_ID = {session_id} AND Player_Name = '{player_name}'")
        db.commit()
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (player_name, true_name, time, 'Sessions_Participants', f'{player_name} has declined to participate in session {session_id}', 0, 'leaving DND session')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def session_cleanup(self, guild_id, session_id, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"DELETE FROM Sessions WHERE Session_ID = {session_id}' AND IsActive = 1")
        cursor.execute(f"DELETE FROM Sessions_Signups WHERE Session_ID = {session_id}'")
        cursor.execute(f"DELETE FROM Sessions_Participants WHERE Session_ID = {session_id}'")
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, 'N/A', time, 'Sessions', f'cleaning up session information from the stage tables', 0, 'session_cleaning')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def update_settings(self, guild_id, author, new_search, identifier):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = "UPDATE Admin SET Search = ? WHERE Identifier = ?"
        val = (new_search, identifier)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, 'admin', time, 'Admin', f'Updating {identifier} with new {new_search} qualifier', 0, 'administration change')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def session_log_player(self, guild_id, session_id, player_name, player_id, character_name, level, tier,  effective_gold, rewarded, trials, received_gold, received_fame, received_prestige, received_flux):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute(f"UPDATE Sessions SET IsActive = 0  WHERE Session_ID = ?", (session_id,))
        sql = f"INSERT INTO Sessions_Archive(Session_ID, Player_Name, Player_ID, Character_Name, Level, Tier,  Effective_Gold, Received_Milestones, Received_Trials, Received_Gold, Received_Fame, Received_Prestige, Received_Flux) Values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        val = (session_id, player_name, player_id, character_name, level, tier,  effective_gold, rewarded, trials, received_gold, received_fame, received_prestige, received_flux)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def session_log(self, guild_id, session_id, gold, flux, easy, medium, hard, deadly, trials, reward_all, party_reward, rewards_message, rewards_thread, fame, prestige):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE Sessions SET IsActive = ?, Completed_Time = ?, Gold = ?, Flux = ?, Easy = ?, Medium = ?, Hard = ?, Deadly = ?, Trials = ?, Alt_Reward_All = ?, Alt_Reward_Party = ?, Rewards_Message = ?, rewards_thread = ?, Fame = ?, prestige = ? WHERE Session_ID = ?"
        val = (0, time, gold, flux, easy, medium, hard, deadly, trials, reward_all, party_reward, rewards_message, rewards_thread, fame, prestige, session_id)
        cursor.execute(sql, val)
        cursor.execute(f"DELETE FROM Sessions_Participants WHERE Session_ID = ?", (session_id, ))
        db.commit()
        cursor.execute(f"DELETE FROM Sessions_Signups WHERE Session_ID = ?", (session_id,))
        db.commit()
        cursor.close()
        db.close()

    async def update_session_log(self, guild_id, session_id, gold, flux, easy, medium, hard, deadly, trials, reward_all, party_reward, rewards_message_id, rewards_thread, fame, prestige):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = f"UPDATE Sessions SET Gold = ?, Flux = ?, Easy = ?, Medium = ?, Hard = ?, Deadly = ?, Trials = ?, Alt_Reward_All = ?, Alt_Reward_Party = ?, rewards_message = ?, rewards_thread = ?, fame = ?, prestige = ?  WHERE Session_ID = ?"
        val = (gold, flux, easy, medium, hard, deadly, trials, reward_all, party_reward, rewards_message_id, rewards_thread, fame, prestige, session_id)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def update_session_log_player(self, guild_id, session_id, character_name, received_milestones, trials, received_gold, received_fame, received_prestige):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"UPDATE Sessions_Archive SET Received_Milestones = ?, Received_Trials = ?, Received_Gold = ?, Received_Fame = ?, received_prestige = ? WHERE Session_ID = ? AND Character_Name = ?"
        val = (received_milestones, trials, received_gold, session_id, character_name, received_fame, received_prestige)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def update_level_cap(self, guild_id, author, new_level):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"Update Admin SET search = {new_level} WHERE Identifier = 'Level_Cap'")
        cursor.execute(f"SELECT Minimum_Milestones, Milestones_to_level FROM AA_Milestones where Level = {new_level}")
        level_info = cursor.fetchone()
        minimum_milestones = level_info[0]
        cursor.execute(f"SELECT Player_Name, Player_ID, Character_Name, Trials, Milestones, Personal_Cap FROM Player_Characters WHERE Milestones >= {minimum_milestones}")
        characters_info = cursor.fetchall()
        if characters_info is not None:
            for characters in characters_info:
                personal_cap = 20 if characters[5] is None else characters[5]
                if personal_cap >= characters[4]:
                    sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
                    val = (author, 'admin', time, 'Player_Characters', f'Updating {characters[2]} with new level cap of {new_level}', 0, 'administration change')
                    cursor.execute(sql, val)
                    cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Trials <= {characters[3]} ORDER BY Trials DESC  LIMIT 1")
                    current_mythic_information = cursor.fetchone()
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Cap'")
                    max_tier = cursor.fetchone()
                    cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_Breakpoint'")
                    break_point = cursor.fetchone()
                    if new_level <= int(break_point[0]):
                        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_1'")
                        tier_rate_limit = cursor.fetchone()
                    else:
                        cursor.execute(f"SELECT Search from Admin WHERE Identifier = 'Tier_Rate_Limit_2'")
                        tier_rate_limit = cursor.fetchone()
                    rate_limited_tier = floor(new_level / int(tier_rate_limit[0]))
                    print(current_mythic_information[0])
                    true_tier = current_mythic_information[0] if current_mythic_information[0] < int(max_tier[0]) else int(max_tier[0])
                    print(true_tier)
                    true_tier = true_tier if true_tier <= rate_limited_tier else rate_limited_tier
                    print(true_tier)
                    if true_tier == int(max_tier[0]) or true_tier == rate_limited_tier:
                        cursor.execute(f"SELECT Tier, Trials, Trials_Required from AA_Trials  WHERE Tier = {true_tier}")
                        current_mythic_information = cursor.fetchone()
                    else:
                        current_mythic_information = current_mythic_information
                    trials_required = current_mythic_information[1] + current_mythic_information[2] - characters[3]
                    sql = f"UPDATE Player_Characters SET Level = ?, Milestones_Required = ?, Tier = ?, Trials_Required = ? WHERE Character_Name = ?"
                    val = (new_level, level_info[0] + level_info[1] - characters[4], true_tier, trials_required, characters[2])
                    cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def update_tier_cap(self, guild_id, author, new_tier, minimum_level):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"SELECT Trials, Trials_Required FROM AA_Trials where Tier = {new_tier}")
        level_info = cursor.fetchone()
        cursor.execute(f"UPDATE Admin SET search = {new_tier} WHERE Identifier = 'Tier_Cap'")
        minimum_milestones = level_info[0]
        cursor.execute(f"SELECT Player_Name, Player_ID, Character_Name, Trials FROM Player_Characters WHERE Trials >= {minimum_milestones} AND Level >= {minimum_level}")
        characters_info = cursor.fetchall()
        if characters_info is not None:
            for characters in characters_info:
                sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
                val = (author, 'admin', time, 'Player_Characters', f'Updating {characters[2]} with new tier cap of {new_tier}', 0, 'administration change')
                cursor.execute(sql, val)
                sql = f"UPDATE Player_Characters SET Tier = ?, Trials_Required = ? WHERE Character_Name = ?"
                val = (new_tier, level_info[0] + level_info[1] - characters[3], characters[2])
                cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def flux(self, guild_id, true_name, amount, new_flux, author):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"UPDATE Player_Characters SET flux = ? WHERE Character_Name = ?"
        val = (new_flux, true_name)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, f'{true_name}', time, 'Player_Characters', f'adjusting flux by {amount} to be {new_flux}', amount, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def set_range(self, guild_id, author, range_name, range_id, minimum, maximum):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"UPDATE Level_Range SET Role_Name = ?, Role_ID = ? WHERE level >= ? AND level <= ?"
        val = (range_name, range_id, minimum, maximum)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, f'N/A', time, 'Level_Range', f'Numbers {minimum}-{maximum} have been changed to be {range_name}', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def customize_characters(self, guild_id, author, character_name, destination_name, destination_link, customized_name, link, flux_remaining, flux_cost):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"UPDATE Player_characters SET {destination_name} = ?, {destination_link} = ?, flux = ? WHERE character_name = ?"
        val = (customized_name, link, flux_remaining, character_name)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, f'{character_name}', time, 'Player_Characters', f'{character_name} has been given {destination_name} of {customized_name} leaving them with {flux_remaining} flux', flux_cost, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def add_fame_store(self, guild_id, author, fame_required, prestige_cost, name, effect, limit):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"INSERT INTO Store_Fame(Fame_Required, Prestige_Cost, Name, Effect, Use_Limit) VALUES (?, ?, ?, ?, ?)"
        val = (fame_required, prestige_cost, name, effect, limit)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, f'{name}', time, 'Store_Fame', f'added {name} with effect {effect} requiring {fame_required} fame and {prestige_cost} prestige', 0, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()


    async def remove_fame_store(self, guild_id, author, name):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, f'{name}', time, 'Store_Fame', f'deleted {name}', 0, 'N/A')
        cursor.execute(sql, val)
        cursor.execute(f"DELETE FROM Store_Fame WHERE Item = ?", (name,))
        db.commit()
        cursor.close()
        db.close()


    async def update_fame_store(self, guild_id, author, fame_required, prestige_cost, name, effect, limit):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"UPDATE Store_Fame SET Fame_Required = ?, Prestige_Cost = ?, Effect = ?, Use_Limit = ? WHERE Item = ?"
        val = (fame_required, prestige_cost, effect, limit, name)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, f'{name}', time, 'Store_Fame', f'updated {name} with effect {effect}', cost, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def add_title_store(self, guild_id, author, ubb_id, effect, fame, masculine_name, feminine_name):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"INSERT INTO Store_Title(ID, Masculine_Name, Feminine_Name, Fame, Effect) VALUES (?, ?, ?, ?, ?)"
        val = (ubb_id, masculine_name, feminine_name, fame, effect)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, f'{masculine_name} / {feminine_name}', time, 'Store_Title', f'added {masculine_name} / {feminine_name} with effect {effect}', fame, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def remove_title_store(self, guild_id, author, fame, masculine_name, feminine_name):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"select fame, Character_Name from Player_Characters where Title = ? or Title = ?", (masculine_name, feminine_name))
        characters = cursor.fetchall()
        if characters is not None:
            for character in characters:
                cursor.execute(f"UPDATE Player_Characters SET fame = ?, Title WHERE Character_Name = ?", (character[0] - fame, None, character[1]))
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, f'{name}', time, 'Store_Title', f'deleted {name}', 0, 'N/A')
        cursor.execute(sql, val)
        cursor.execute(f"DELETE FROM Store_Title WHERE Masculine_Name = ?", (masculine_name,))
        db.commit()
        cursor.close()
        db.close()

    async def update_title_store(self, guild_id, author, ubb_id, effect, fame, masculine_name, feminine_name):
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        sql = f"UPDATE Store_Title SET Cost = ?, Effect = ? WHERE Item = ?"
        val = (cost, effect, name)
        cursor.execute(sql, val)
        sql = "INSERT INTO A_Audit_All(Author, Character, Timestamp, Database_Changed, Modification, Amount, Reason) VALUES(?, ?, ?, ?, ?, ?, ?)"
        val = (author, f'{name}', time, 'Store_Title', f'updated {name} with effect {effect}', cost, 'N/A')
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()

    async def timesheet(self, guild_id, author, utc_offset, start_day, start_hours, start_minutes, end_day, end_hours, end_minutes, change):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        time_columns = [
            "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30",
            "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30",
            "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
            "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
            "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30",
            "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30"
        ]
        columns_to_nullify = []
        start_minutes = start_hours * 60 + start_minutes + utc_offset * 60
        end_minutes = end_hours * 60 + end_minutes + utc_offset * 60
        cursor.execute(f"select count(player_name) from Player_Timecard where player_name = ?", (author,))
        player_exists = cursor.fetchone()
        if player_exists[0] != 7:
            print(player_exists[0])
            if player_exists[0] > 0:
                cursor.execute(f"DELETE from Player_Timecard where Player_Name = ?", (author,))

                db.commit()
                cursor.close()
                db.close()
                db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
                cursor = db.cursor()
            x = 1
            while x < 8:
                cursor.execute(f"INSERT INTO Player_Timecard(Player_Name, Day) VALUES(?, ?)", (author, x))
                x += 1
        if change == 1:
            print("adding")
            if start_day == end_day:
                for col in time_columns:
                    col_minutes = time_to_minutes(col)
                    if col_minutes >= start_minutes or col_minutes <= end_minutes:
                        columns_to_nullify.append(f'"{col}" = 1')
                # Build the SQL query dynamically
                set_clause = ', '.join(columns_to_nullify)
                print(set_clause)
                query = f"""
                    UPDATE Player_Timecard
                    SET {set_clause}
                    WHERE Player_Name = ? AND Day = ?;
                """
                # Execute the query
                cursor.execute(query, (author, start_day))
                print(f"ran query")
                db.commit()
                cursor.execute(f"UPDATE Player_Timecard SET utc_offset = ? WHERE Player_Name = ?", (utc_offset, author))
            else:
                for col in time_columns:
                    col_minutes = time_to_minutes(col)
                    if col_minutes >= start_minutes or col_minutes <= 1440:
                        columns_to_nullify.append(f'"{col}" = 1')
                # Build the SQL query dynamically
                set_clause = ', '.join(columns_to_nullify)
                print(set_clause)
                query = f"""
                    UPDATE Player_Timecard
                    SET {set_clause}
                    WHERE Player_Name = ? AND Day = ?;
                """
                cursor.execute(query, (author, start_day))
                columns_to_nullify = []
                for col in time_columns:
                    col_minutes = time_to_minutes(col)
                    if col_minutes >= 0 or col_minutes <= end_minutes:
                        columns_to_nullify.append(f'"{col}" = 1')
                # Build the SQL query dynamically
                set_clause = ', '.join(columns_to_nullify)
                query = f"""
                    UPDATE Player_Timecard
                    SET {set_clause}
                    WHERE Player_Name = ? AND Day = ?;
                """
                print(set_clause)
                cursor.execute(query, (author, end_day))
        else:
            if start_day == end_day:
                for col in time_columns:
                    col_minutes = time_to_minutes(col)
                    if col_minutes >= start_minutes or col_minutes <= end_minutes:
                        columns_to_nullify.append(f'"{col}" = NULL')
                # Build the SQL query dynamically
                set_clause = ', '.join(columns_to_nullify)
                query = f"""
                    UPDATE Player_Timecard
                    SET {set_clause}
                    WHERE Player_Name = ? AND Day = ?;
                """
                # Execute the query
                cursor.execute(query, (author, start_day))
            else:
                print(f"I did else.")
                for col in time_columns:
                    col_minutes = time_to_minutes(col)
                    if col_minutes >= start_minutes or col_minutes <= 1440:
                        columns_to_nullify.append(f'"{col}" = NULL')
                # Build the SQL query dynamically
                set_clause = ', '.join(columns_to_nullify)
                query = f"""
                    UPDATE Player_Timecard
                    SET {set_clause}
                    WHERE Player_Name = ? AND Day = ?;
                """
                cursor.execute(query, (author, start_day))
                columns_to_nullify = []
                for col in time_columns:
                    col_minutes = time_to_minutes(col)
                    if col_minutes >= 0 or col_minutes <= end_minutes:
                        columns_to_nullify.append(f'"{col}" = NULL')
                # Build the SQL query dynamically
                set_clause = ', '.join(columns_to_nullify)
                query = f"""
                    UPDATE Player_Timecard
                    SET {set_clause}
                    WHERE Player_Name = ? AND Day = ?;
                """
                cursor.execute(query, (author, end_day))
        db.commit()
        cursor.close()
        db.close()

    async def clear_timesheet(self, guild_id, change, day, author):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        if change == 4:
            cursor.execute(f"DELETE FROM Timesheet WHERE player_name = ?", (author,))
        else:
            time_columns = [
                "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30",
                "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30",
                "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
                "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30",
                "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30"
            ]
            columns_to_nullify = []
            cursor.execute(f"SELECT UTC_Offset FROM player_Timecard WHERE player_name = ? and UTC_Offset is not Null", (day,))
            utc_offset_info = cursor.fetchone()
            utc_offset = 0 if utc_offset_info is None else utc_offset_info[0]
            if utc_offset == 0:
                hour_clear_window_start = "0:00"
                hour_clear_window_end = "24:00"
                start_minutes = time_to_minutes(hour_clear_window_start)
                end_minutes = time_to_minutes(hour_clear_window_end)
                columns_to_nullify = []
                for col in time_columns:
                    col_minutes = time_to_minutes(col)
                    if col_minutes >= start_minutes or col_minutes <= end_minutes:
                        columns_to_nullify.append(f'"{col}" = NULL')
                # Build the SQL query dynamically
                set_clause = ', '.join(columns_to_nullify)
                query = f"""
                    UPDATE Player_Timecard
                    SET {set_clause}
                    WHERE Player_Name = ? AND Day = ?;
                """
                # Execute the query
                cursor.execute(query, (author, day))
            elif utc_offset > 0:
                hour_clear_window_start = utc_offset
                hour_clear_window_end = utc_offset
                start_minutes = time_to_minutes(hour_clear_window_start)
                end_minutes = time_to_minutes(hour_clear_window_end)
                day_clear_window_start = day
                day_clear_window_end = day+1 if day < 7 else 1
                columns_to_nullify = []
                for col in time_columns:
                    col_minutes = time_to_minutes(col)
                    if col_minutes >= start_minutes or col_minutes <= 1440:
                        columns_to_nullify.append(f'"{col}" = NULL')
                # Build the SQL query dynamically
                set_clause = ', '.join(columns_to_nullify)
                query = f"""
                    UPDATE Player_Timecard
                    SET {set_clause}
                    WHERE Player_Name = ? AND Day = ?;
                """
                cursor.execute(query, (author, day_clear_window_start))
                columns_to_nullify = []
                for col in time_columns:
                    col_minutes = time_to_minutes(col)
                    if col_minutes >= 0 or col_minutes <= end_minutes:
                        columns_to_nullify.append(f'"{col}" = NULL')
                # Build the SQL query dynamically
                set_clause = ', '.join(columns_to_nullify)
                query = f"""
                    UPDATE Player_Timecard
                    SET {set_clause}
                    WHERE Player_Name = ? AND Day = ?;
                """
                cursor.execute(query, (author, day_clear_window_end))

            else:
                hour_clear_window_start = 24 + utc_offset
                hour_clear_window_end = 24 + utc_offset
                day_clear_window_start = day-1 if day > 1 else 7
                day_clear_window_end = day
                start_minutes = time_to_minutes(hour_clear_window_start)
                end_minutes = time_to_minutes(hour_clear_window_end)
                columns_to_nullify = []
                for col in time_columns:
                    col_minutes = time_to_minutes(col)
                    if start_minutes >= hour_clear_window_start or col_minutes <= 1440:
                        columns_to_nullify.append(f'"{col}" = NULL')
                # Build the SQL query dynamically
                set_clause = ', '.join(columns_to_nullify)
                query = f"""
                                    UPDATE Player_Timecard
                                    SET {set_clause}
                                    WHERE Player_Name = ? AND Day = ?;
                                """
                cursor.execute(query, (author, day_clear_window_start))
                columns_to_nullify = []
                for col in time_columns:
                    col_minutes = time_to_minutes(col)
                    if col_minutes >= 0 or col_minutes <= end_minutes:
                        columns_to_nullify.append(f'"{col}" = NULL')
                # Build the SQL query dynamically
                set_clause = ', '.join(columns_to_nullify)
                query = f"""
                                    UPDATE Player_Timecard
                                    SET {set_clause}
                                    WHERE Player_Name = ? AND Day = ?;
                                """
                cursor.execute(query, (author, day_clear_window_end))

        db.commit()
        cursor.close()
        db.close()

    async def group_request(self, guild_id, author, character_name, group_name, choice):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        if choice == 1:
            cursor.execute(f"INSERT INTO Sessions_Group(Group_Name, Player_Name, Created_date) VALUES (?, ?, ?)", (group_name, author, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            db.commit()
            cursor.execute(f"SELECT Group_ID from Sessions_Group where Player_Name = ?", (author,))
            group_info = cursor.fetchone()
            cursor.execute(f"INSERT INTO Sessions_Presign(Group_ID, Player_name, Character_Name) VALUES (?, ?)", (group_info[0], author, character_name))
        else:
            cursor.execute(f"SELECT Group_ID from sessions_group where host = ?", (author,))
            group_info = cursor.fetchone()
            cursor.execute(f"DELETE FROM Sessions_Group WHERE host = ?", (author))
            db.commit()
            cursor.execute(f"Delete from Sessions_Presign where group_id = ?", (group_info[0],))
            db.commit()
        db.commit()
        cursor.close()
        db.close()

    async def group_join(self, guild_id, group_id, author, character_name, choice):
        db = sqlite3.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        if choice == 1:
            cursor.execute(f"INSERT INTO Sessions_Presign(Group_ID, player_name, Character_Name) VALUES (?, ?)", (group_id, author, character_name))
        else:
            cursor.execute(f"Delete from Sessions_Presign where group_id = ? and character_name = ?", (group_id, character_name))
        db.commit()
        cursor.close()
        db.close()

    async def clear_group(self, guild_id, group_id):
        db = sqlite.connect(f"Pathparser_{guild_id}.sqlite")
        cursor = db.cursor()
        cursor.execute(f"DELETE FROM Sessions_Group WHERE Group_ID = ?", (group_id,))
        cursor.execute(f"DELETE FROM Sessions_Presign WHERE Group_ID = ?", (group_id,))
        db.commit()
        cursor.close()
        db.close()