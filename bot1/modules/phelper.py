import pandas as pd
import os
import json
import random
from datetime import datetime
import pytz
import csv
from datetime import timedelta
from . import config
from .PassVerify_siren import PassVerify
import asyncio
import discord
from discord import app_commands
from typing import Any
import requests

gmfile = os.path.join(config.DB_Path, "guild_manager.csv")
lsfile = os.path.join(config.DB_Path, "license.csv")
spffile = os.path.join(config.DB_Path, "whitelist.json")
bmfile = os.path.join(config.DB_Path, "srvbl.json")

def LoadGMFile():
    df = pd.read_csv(gmfile, sep=",")
    return df

def SaveGMFile(df: pd.DataFrame):
    df.to_csv(gmfile, index=None)

def LoadLSFile():
    df = pd.read_csv(lsfile, sep=",")
    return df

def SaveLSFile(df: pd.DataFrame):
    df.to_csv(lsfile, index=None)

def GetMFileValue(df: pd.DataFrame, column_name: str, row_name: str, column_standard_value: Any):
    # column_standard_value를 문자열로 처리하여 비교
    filtered_df = df.loc[df[column_name].astype(str) == str(column_standard_value), row_name]
    
    value = filtered_df.values[0]
    return value

def RB_IfMValueExists(df: pd.DataFrame, column_name: str, value: any):
    return df[column_name].eq(value).any()

def EditMFile(df: pd.DataFrame, column_name: str, row_name: str, column_standard_value: any, new_value: any):
    df.loc[df[column_name] == column_standard_value, row_name] = new_value
    return df

def GenRandomStr(length):
    characters = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ"
    return "".join(random.choice(characters) for _ in range(length))

def GetCurrentKST():
    today = datetime.now(pytz.timezone('Asia/Seoul'))
    return str(today).split(".")[0].replace(" ", "_")

def ProcessLicense(licensekey: str, srvid: str):
    df = LoadLSFile()
    df = EditMFile(df, "LicenseKey", "AssignedGuildID", licensekey, int(srvid))
    day = df.loc[df["LicenseKey"] == licensekey, "LicenseDay"].values[0]
    valid_until = (datetime.now() + timedelta(days=int(day))).strftime("%Y-%m-%d %H:%M:%S")
    df = EditMFile(df, "LicenseKey", "ValidUntil", licensekey, valid_until)
    SaveLSFile(df)
    return valid_until

def LicenseKeyCheck(licensekey: str):
    df = LoadLSFile()
    license_row = df[df["LicenseKey"] == licensekey]
    
    if license_row.empty:
        return False
    
    assigned_guild_id = license_row["AssignedGuildID"].iloc[0]    
    is_available = pd.isna(assigned_guild_id) or assigned_guild_id == "undefined" 
    return is_available

def RB_GetGuild(srvid: str):
    df = LoadGMFile()
    guild_row = df[df['GuildID'] == srvid]
    if not guild_row.empty:
        return guild_row.iloc[0]
    else:
        return None

def RB_AddRole(guildid: int, userid: str, roleid: int):
    url = f"https://discordapp.com/api/v9/guilds/{guildid}/members/{userid}/roles/{roleid}"
    botToken = config.BotToken
    headers = {
        "Authorization" : f"Bot {botToken}",
        'Content-Type': 'application/json'
    }
    requests.put(url=url, headers=headers)
    return True

def RB_AddGuild(srvid: str, licensekey: str):
    if LicenseKeyCheck(licensekey) == False:
        return "NL"
    result = ProcessLicense(licensekey, srvid)
    if result is None:
        return "ERROR"
    with open(os.path.join(config.DB_Path, "guild_manager.csv"), "a", newline='', encoding="utf-8") as gmcsv:
        appender = csv.writer(gmcsv)
        appender.writerow([srvid, True, "undefined", licensekey, "undefined", "undefined", False])
    return result

def RB_GetGuildInfo(srvid: str):
    url = f'https://discord.com/api/v10/guilds/{srvid}?with_counts=true'
    headers = {
        'Authorization': f'Bot {config.BotToken}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        guild_data = response.json()
        guild_name = guild_data.get('name', None)
        icon_hash = guild_data.get('icon')
        ownerid = guild_data.get('owner_id')
        all_member_count = guild_data.get('approximate_member_count')
        onlinemem_count = guild_data.get('approximate_presence_count')
        if icon_hash:
            icon_url = f'https://cdn.discordapp.com/icons/{srvid}/{icon_hash}.png'
        else:
            icon_url = None
        return {"name": guild_name, "icon": icon_url, "owner_id": ownerid, "allmem_count": all_member_count, "onlinemem_count": onlinemem_count}
    else:
        return False

def RB_AddLicense(license_day: int):
    licensekey = GenRandomStr(16)
    valid_until = "undefined"
    assigned_guild_id = "undefined"
    with open(lsfile, "a", newline='', encoding="utf-8") as lscsv:
        appender = csv.writer(lscsv)
        appender.writerow([licensekey, license_day, valid_until, assigned_guild_id])
    return licensekey

def RB_UpdateGuildPermission(srvid: str, permission: bool):
    df = LoadGMFile()
    df.loc[df['GuildID'] == srvid, 'Permitted'] = permission
    SaveGMFile(df)


async def BeginPassVerify(name: str, birth:str, phone:str, captcha: str, verify):
    result = verify.SendSMS(name, birth, phone, captcha)
    print(result)
    if not result['IsSuccess']:
        return False
    else:
        return True

async def CheckSMS(otp: str, verify):
    result = verify.CheckSMS(otp)
    # verify.close()
    return result

async def CaptchaManager(telecom: str, user_id: str):
        verify = PassVerify(telecom)
        verify.initialize()
        captcha = verify.GetCaptcha()
        
        filep = os.path.join(os.path.join(config.DB_Path, "captchas"), f"{user_id}_captcha.png")
        with open(filep, "wb") as f:
            f.write(captcha.getbuffer())
        return verify
#asyncio.run(Verify(telecom, name, birth, phone))

def check_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        # admin_users = RB_GetAdmins()
        return interaction.user.guild_permissions.administrator if interaction.guild else False
    return app_commands.check(predicate)

def RB_ExtendLicense(srvid: str, licensekey: str):
    df = LoadLSFile()
    server_row = df[df['AssignedGuildID'] == srvid]
    if server_row.empty:
        return "NR"

    new_license_row = df[df['LicenseKey'] == licensekey]
    if new_license_row.empty:
        return "NL"

    if pd.notna(new_license_row['AssignedGuildID'].values[0]):
        return "UL"

    current_valid_until = pd.to_datetime(server_row['ValidUntil'].values[0])
    new_days = int(new_license_row['LicenseDay'].values[0])
    new_valid_until = current_valid_until + pd.Timedelta(days=new_days)

    df.loc[df['AssignedGuildID'] == srvid, 'ValidUntil'] = new_valid_until
    df = df[df['LicenseKey'] != licensekey]
    df.loc[df['AssignedGuildID'] == srvid, 'LicenseKey'] = licensekey

    SaveLSFile(df)

    gm_df = LoadGMFile()
    gm_df.loc[gm_df['GuildID'] == srvid, 'Permitted'] = True
    SaveGMFile(gm_df)

    return str(new_valid_until)

def RB_AddBlacklist_Srv(srvid: str):
    try:
        with open(bmfile, "r", encoding="utf-8") as file:
            wmlist = json.load(file)
    except FileNotFoundError:
        wmlist = {}
    except json.JSONDecodeError:
        wmlist = {}

    if srvid not in wmlist:
        wmlist[srvid] = {"userid": [], "name": [], "phone": []}
    else:
        return False

    with open(bmfile, "w", encoding="utf-8") as file:
        json.dump(wmlist, file, ensure_ascii=False, indent=4)

    return True

def RB_DeleteBlacklist_Srv(srvid: str):
    try:
        with open(bmfile, "r", encoding="utf-8") as file:
            wmlist = json.load(file)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

    if srvid in wmlist:
        del wmlist[srvid]
    else:
        return False

    with open(bmfile, "w", encoding="utf-8") as file:
        json.dump(wmlist, file, ensure_ascii=False, indent=4)

    return True

def RB_CheckBlacklist_Srv(target: str, srvid: str, isid: bool, isname: bool, isphone: bool) -> bool:
    with open(bmfile, "r", encoding="utf-8") as file:
        wmlist = json.load(file)

    if srvid not in wmlist:
        return None

    if isid and not isname and not isphone:
        return str(target) in wmlist[srvid].get("userid", [])
    elif isname and not isid and not isphone:
        return str(target) in wmlist[srvid].get("name", [])
    elif not isname and not isid and isphone:
        return str(target) in wmlist[srvid].get("phone", [])

def RB_AddBlacklist_Srv_User(target: str, srvid: str, isid: bool, isname: bool, isphone: bool) -> str:
    if RB_CheckBlacklist_Srv(target, srvid, isid, isname, isphone) is None:
        result = RB_AddBlacklist_Srv(str(srvid))
        if result == False:
            return False
    
    if RB_CheckBlacklist_Srv(target, srvid, isid, isname, isphone):
        return False

    with open(bmfile, "r", encoding="utf-8") as file:
        wmlist = json.load(file)

    if isid and not isname and not isphone:
        wmlist[srvid]["userid"].append(str(target))
    elif isname and not isid and not isphone:
        wmlist[srvid]["name"].append(str(target))
    elif not isname and not isid and isphone:
        wmlist[srvid]["phone"].append(str(target))

    with open(bmfile, "w", encoding="utf-8") as file:
        json.dump(wmlist, file)

    return True

def RB_DeleteBlacklist_Srv_User(target: str, srvid: str, isid: bool, isname: bool, isphone: bool) -> str:
    if RB_CheckBlacklist_Srv(target, srvid, isid, isname, isphone) is None:
        return None
    
    if not RB_CheckBlacklist_Srv(target, srvid, isid, isname, isphone):
        return False

    with open(bmfile, "r", encoding="utf-8") as file:
        wmlist = json.load(file)

    if srvid in wmlist:
        if isid and not isname and not isphone:
            wmlist[srvid]["userid"].remove(str(target))
        elif isname and not isid and not isphone:
            wmlist[srvid]["name"].remove(str(target))
        elif not isname and not isid and isphone:
            wmlist[srvid]["phone"].remove(str(target))

    with open(bmfile, "w", encoding="utf-8") as file:
        json.dump(wmlist, file)

    return True

def AddWhitelist(userid: str):
    with open(spffile, "r", encoding="utf-8") as file:
        wmlist = json.load(file)
    
    if not userid in wmlist["userid"]:
        wmlist["userid"].append(userid)
        with open(spffile, "w", encoding="utf-8") as file:
            json.dump(wmlist, file)
        return True
    elif userid in wmlist["userid"]:
        return False
    
def RmWhitelist(userid: str):
    with open(spffile, "r", encoding="utf-8") as file:
        wmlist = json.load(file)
    
    if userid in wmlist["userid"]:
        wmlist["userid"].remove(userid)
        with open(spffile, "w", encoding="utf-8") as file:
            json.dump(wmlist, file)
        return True
    elif not userid in wmlist["userid"]:
        return False
    
def ChkWhitelist(userid: str):
    with open(spffile, "r", encoding="utf-8") as file:
        wmlist = json.load(file)
    
    if userid in wmlist["userid"]:
        return True
    elif not userid in wmlist["userid"]:
        return False