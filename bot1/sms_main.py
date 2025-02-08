import discord
from discord.ext import commands
from enum import Enum
import base64
import os
import sys
import json
import pandas as pd
from discord.ext import tasks, commands
from discord.ui import Button, TextInput
from discord import app_commands, Interaction, ui, ButtonStyle, SelectOption, SyncWebhook, Attachment, TextChannel
from modules import *
from typing import Optional, Literal, Any
import datetime
import asyncio
import pytz
import pytz
import csv
from datetime import timedelta, datetime
import logging
import traceback

lc = os.path.join(config.DB_Path, "license.csv")
gm = os.path.join(config.DB_Path, "guild_manager.csv")

class AddDel(Enum):
    추가="Add"
    삭제="Delete"

class Bot(commands.AutoShardedBot):
    async def setup_hook(self):
        self.loop.set_exception_handler(handle_exception)
        self.loop.create_task(check_licenses())

    async def on_ready(self):
        await self.wait_until_ready()
        await self.tree.sync()
        print(f"Logged in as {self.user} !")
    

intents = discord.Intents.default()
intents.members = True
client = Bot(intents=intents, command_prefix="!") #, shard_count=100)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

@client.event
async def on_interaction(interaction: Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get('custom_id')
        if custom_id == "verifybtn":
            await on_button2_click(interaction)
        elif custom_id == "selectedtel":
            await on_tel_click(interaction)

def handle_exception(loop, context):
    # 예외 정보 추출
    exception = context.get('exception')
    if exception:
        print(f"Unhandled exception: {exception}", file=sys.stderr)
        print(f"Exception details:\n{''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))}", file=sys.stderr)
    else:
        print(f"Unhandled exception: {context['message']}", file=sys.stderr)

async def check_licenses():
    while True:
        now = datetime.now()
        expired_guilds = []

        with open(lc, 'r', newline='', encoding='utf-8') as license_file:
            license_reader = csv.DictReader(license_file)
            for row in license_reader:
                if not row["ValidUntil"] == "undefined":
                    try:
                        valid_until = datetime.strptime(row['ValidUntil'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            valid_until = datetime.strptime(row['ValidUntil'], '%Y-%m-%d')
                        except ValueError:
                            print(f"Invalid date format in ValidUntil: {row['ValidUntil']}")
                            continue

                    if valid_until < now:
                        expired_guilds.append(row['AssignedGuildID'])

        if expired_guilds:
            temp_file = gm + '.tmp'
            with open(gm, 'r', newline='', encoding='utf-8') as guild_file, \
                open(temp_file, 'w', newline='', encoding='utf-8') as temp_guild_file:
                guild_reader = csv.DictReader(guild_file)
                fieldnames = guild_reader.fieldnames
                guild_writer = csv.DictWriter(temp_guild_file, fieldnames=fieldnames)
                
                guild_writer.writeheader()
                for row in guild_reader:
                    if row['GuildID'] in expired_guilds:
                        row['Permitted'] = 'False'
                    guild_writer.writerow(row)

            os.replace(temp_file, gm)

        await asyncio.sleep(30)

async def on_button2_click(interaction: Interaction):
    #라센 유효한지 체크
    df = phelper.LoadGMFile()
    ispermitted = phelper.GetMFileValue(
        df=df,
        column_name="GuildID",
        row_name="Permitted",
        column_standard_value=str(interaction.guild_id)
    )
    if ispermitted == False:
        embed = discord.Embed(title="FAILED", description="라이센스가 만료되어 인증이 불가합니다.\n서버관리자에게 문의해 주세요.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
        
    #화리 - userid
    iswh = phelper.ChkWhitelist(userid=str(interaction.user.id))
    if iswh == True:
        embed_log = discord.Embed(title=f"<@{interaction.user.id}>님이 인증을 완료하였습니다.", description=f"```성명: [REDACTED]\n생년월일: [REDACTED]\n전화번호: [REDACTED]```", color=discord.Color.green())
        roleid = phelper.GetMFileValue(df=phelper.LoadGMFile(), column_name="GuildID", row_name="RoleID", column_standard_value=int(interaction.guild_id))
        if roleid == "undefined":
            embed = discord.Embed(title="인증 설정오류", description="부여될 역할이 설정되지 않았습니다.\n서버 관리자에게 문의해주세요.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        webhooklink = phelper.GetMFileValue(df=phelper.LoadGMFile(), column_name="GuildID", row_name="WebhookLink", column_standard_value=int(interaction.guild_id))
        phelper.RB_AddRole(guildid=int(interaction.guild.id), userid=str(interaction.user.id), roleid=int(roleid))
        if not webhooklink == "undefined":
            webhookobj = SyncWebhook.from_url(webhooklink)
            webhookobj.send(embed=embed_log, username="PSMS Verify Log", avatar_url=config.DefaultPfp)
        embed = discord.Embed(title="인증 완료", description="인증이 완료되었습니다.\n역할이 부여되지 않았을 경우, 서버관리자에게 문의해주세요.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    embed = discord.Embed(title="SMS 인증 시작", description="PASS를 이용하여 인증을 진행합니다.\n통신사를 선택해주세요.", color=discord.Color.blue())
    select = ui.Select(placeholder="통신사를 선택하세요", custom_id="selectedtel")
    select.add_option(label="KT", value="KT", description="일반 KT")
    select.add_option(label="SKT", value="SKT", description="일반 SKT")
    select.add_option(label="LG", value="LGT", description="일반 LG")
    select.add_option(label="알뜰폰 KT", value="KTM", description="알뜰폰 KT")
    select.add_option(label="알뜰폰 SKT", value="SKM", description="알뜰폰 SKT")
    select.add_option(label="알뜰폰 LG", value="LGM", description="알뜰폰 LG")
    view = ui.View(timeout=None)
    view.add_item(select)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def on_tel_click(interaction: Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        selected_value = interaction.data.get('values', [None])[0]
        print(selected_value)
        if selected_value:
            await interaction.edit_original_response(content="정보를 받는 중입니다. 잠시만 기다려 주세요...", embed=None, view=None)
            selected_value = str(selected_value)
            verify = await phelper.CaptchaManager(selected_value, str(interaction.user.id))
            with open(os.path.join(config.DB_Path, "captchas", f"{interaction.user.id}_captcha.png"), "rb") as impf:
                dimg = discord.File(impf, filename="captcha.png")
            embed = discord.Embed(
                title=f"{selected_value} 전화번호 인증", description="캡챠를 기억하신 후 아래 버튼을 눌러주세요.", color=discord.Color.blue())
            embed.set_image(url="attachment://captcha.png")
            await interaction.edit_original_response(content=None, embed=embed, view=AuthView(verify, interaction, selected_value), attachments=[dimg])
        else:
            await interaction.followup.send("통신사를 선택하지 않았습니다.", ephemeral=True, delete_after=5.0)
    except Exception as e:
        await interaction.followup.send(content=f"오류가 발생했습니다: {e}", ephemeral=True)

@client.tree.command(name="생성", description="[BotAdmin] 라이센스를 생성합니다.")
async def create_license(interaction: Interaction, 일수: int, 갯수: int):
    if interaction.user.id not in config.BotAdmin:
        embed = discord.Embed(title="ERROR", description="권한이 없습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if 갯수 > 50:
        embed = discord.Embed(title="ERROR", description="갯수는 50개 이하로 입력해주세요. DB 더러워 진다 씨발년아 테러하면 죽여버리겠노무현", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if 갯수 <= 0:
        embed = discord.Embed(title="ERROR", description="갯수는 1개 이상으로 입력해주세요.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if 일수 <= 0:
        embed = discord.Embed(title="ERROR", description="일수는 1일 이상으로 입력해주세요.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    licenses = []  
    for _ in range(갯수):
        licenses.append(phelper.RB_AddLicense(일수))
    
    embed = discord.Embed(title="SUCCESS", description="생성된 라이센스는 다음과 같습니다.", color=discord.Color.green())
    embed.add_field(name="라이센스", value="```\n" + "\n".join(licenses) + "\n```", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="임베드보내기", description="지정한 프사, 이름으로 임베드메시지를 특정채널에 보냅니다.")
@phelper.check_admin()
async def sendced(interaction: Interaction, 이름: Optional[str] = None, 프사: Optional[Attachment] = None, 채널: Optional[TextChannel] = None):
    if 이름 == None:
        이름 = interaction.guild.name
    if 프사 == None:
        프사 = interaction.guild.icon.url
    if 채널 == None:
        채널 = interaction.channel
    await interaction.response.send_modal(modalclass.CEDModal(username1=이름, chnl=채널, botpfpurl=프사))

@client.tree.command(name="sendglobalmsg", description="[BotAdmin] 모든 서버에 메시지를 보냅니다.")
async def sendmsgg(interaction: Interaction):
    if (interaction.user.id in config.BotAdmin):
        await interaction.response.send_modal(modalclass.SMGModal(botpfpurl=client.user.display_avatar.url))
    else:
        embed = discord.Embed(
            title="실행 불가",
            description="이 명령어를 실행할 권한이 없습니다.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
@client.tree.command(name="고급인증설정", description="인증에 고급기능들을 추가합니다.")
@phelper.check_admin()
async def advset(interaction: Interaction, 기능: Literal["투넘버차단"], 설정: Literal["활성화", "비활성화"]):
    feature = 기능
    optset = 설정
    
    try:
        if feature == "투넘버차단":
            if optset == "활성화":
                cvalue = True
            else:
                cvalue = False
            df = phelper.EditMFile(df=phelper.LoadGMFile(), column_name="GuildID", row_name="BTN", column_standard_value=int(interaction.guild.id), new_value=cvalue)
            phelper.SaveGMFile(df=df)
            embed = discord.Embed(
                title="설정 성공",
                description=f"`투넘버차단`기능이 {optset} 되었습니다.",
                color=discord.Color.blue(),
                timestamp=datetime.now(pytz.timezone("Asia/Seoul"))
            )
    except Exception:
        embed = discord.Embed(
            title="오류 발생",
            description=f"**처리실패**\n```{traceback.format_exc()}```",
            color=discord.Color.red(),
            timestamp=datetime.now(pytz.timezone("Asia/Seoul"))
        )
    finally:
        await interaction.response.send_message(embed=embed)
        

@client.tree.command(name="서버등록정보", description="서버 등록정보를 표시합니다.")
@phelper.check_admin()
async def serverinfo(interaction: Interaction):
    if phelper.RB_GetGuild(interaction.guild.id) is None:
        embed = discord.Embed(title="FAILED", description="서버가 등록되어있지 않습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    try:
        liskey = phelper.GetMFileValue(df=phelper.LoadGMFile(), column_name="GuildID", row_name="LicenseKey", column_standard_value=int(interaction.guild.id))
        validuntil = phelper.GetMFileValue(df=phelper.LoadLSFile(), column_name="LicenseKey", row_name="ValidUntil", column_standard_value=liskey)
        guildinfo = phelper.RB_GetGuildInfo(srvid=interaction.guild_id)
        verifyrole = phelper.GetMFileValue(
            df=phelper.LoadGMFile(),
            column_name="GuildID",
            row_name="RoleID",
            column_standard_value=interaction.guild_id
        )
        if verifyrole == "undefined":
            verifyrole_cover = "`설정되지않음`"
        else:
            verifyrole_cover = f"<@&{verifyrole}>"
        whchnlid = phelper.GetMFileValue(
            df=phelper.LoadGMFile(),
            column_name="GuildID",
            row_name="LogChnlID",
            column_standard_value=interaction.guild_id
        )
        if whchnlid == "undefined":
            whchnlid_cover = "`설정되지않음`"
        else:
            whchnlid_cover = f"<#{whchnlid}>"
        embed = discord.Embed(
            title="서버 정보",
            description=f"서버ID: `{interaction.guild_id}`\n서버이름: `{interaction.guild.name}`\n라이센스 유효기간: `{validuntil}`\n인증역할: {verifyrole_cover}\n인증로그: {whchnlid_cover}",
            color=discord.Color.blue(),
            timestamp=datetime.now(pytz.timezone("Asia/Seoul"))
        )
        embed.set_thumbnail(url=guildinfo['icon'])
    except Exception as e:
        embed = discord.Embed(
            title="오류 발생",
            description=f"**처리실패**\n```{traceback.format_exc()}```",
            color=discord.Color.red(),
            timestamp=datetime.now(pytz.timezone("Asia/Seoul"))
        )
    finally:
        await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="인증역할설정", description="인증시 부여할 역할을 설정합니다.")
@phelper.check_admin()
async def rileset(interaction: Interaction, 역할: discord.Role):
    if phelper.RB_GetGuild(interaction.guild.id) is None:
        embed = discord.Embed(title="FAILED", description="서버가 등록되어있지 않습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    vrole = 역할
    df = phelper.EditMFile(df=phelper.LoadGMFile(), column_name="GuildID", row_name="RoleID", column_standard_value=int(interaction.guild_id), new_value=vrole.id)
    phelper.SaveGMFile(df=df)
    embed = discord.Embed(
        title="인증역할 설정완료",
        description=f"<@&{vrole.id}>로 인증역할을 설정하였습니다.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@client.tree.command(name="인증로그설정", description="인증로그를 설정합니다.")
@phelper.check_admin()
async def vlogset(interaction: Interaction, 채널: TextChannel):
    if phelper.RB_GetGuild(interaction.guild.id) is None:
        embed = discord.Embed(title="FAILED", description="서버가 등록되어있지 않습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    try:
        chnl = 채널
        webhook = await chnl.create_webhook(name="Pulservice SMS Log", reason="t")
        webhookurl = webhook.url
        webhookobj = SyncWebhook.from_url(webhookurl)
        webhookobj.send(content="PSMS 인증로그 테스트 메시지\n이 메시지가 보인다면, 설정이 완료되었습니다.", username="인증로그TEST", avatar_url=config.DefaultPfp)
        df = phelper.EditMFile(df=phelper.LoadGMFile(), column_name="GuildID", row_name="WebhookLink", column_standard_value=int(interaction.guild_id), new_value=webhookurl)
        df = phelper.EditMFile(df=df, column_name="GuildID", row_name="LogChnlID", column_standard_value=int(interaction.guild_id), new_value=int(chnl.id))
        phelper.SaveGMFile(df=df)
        embed = discord.Embed(
        title="인증로그 설정완료",
        description=f"채널 <#{chnl.id}>로 인증로그를 설정하였습니다.",
        color=discord.Color.green()
    )
    except Exception as e:
        embed = discord.Embed(title="ERROR", description="인증로그 설정 중 오류가 발생했습니다.", color=discord.Color.red())
        embed.add_field(name="오류내용", value=f"```{e}```", inline=False)
    finally:
        await interaction.response.send_message(embed=embed)

@client.tree.command(name="서버등록", description="발급받은 라이센스로 서버를 등록합니다.")
@phelper.check_admin()
async def enrollsrv(interaction: Interaction, 라이센스: str):
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(title="ERROR", description=f"{interaction.user.name} 님은 관리자가 아닙니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if phelper.RB_GetGuild(interaction.guild.id) is not None:
        embed = discord.Embed(title="ERROR", description="이미 등록된 서버입니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    result = phelper.RB_AddGuild(interaction.guild.id, 라이센스)

    if result == "NL":
        embed = discord.Embed(title="FAILED", description="유효하지 않은 라이센스 입니다.", color=discord.Color.red())
    elif result == "ERROR":
        embed = discord.Embed(title="FAILED", description="서버 등록 중 오류가 발생했습니다.", color=discord.Color.red())
    else:
        embed = discord.Embed(title="SUCCESS", description="서버 등록이 완료되었습니다.", color=discord.Color.green())
        embed.add_field(name="유효기간", value=f"```{result}```", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="연장", description="서버의 라이센스를 연장합니다.")
@phelper.check_admin()
async def extend_license(interaction: Interaction, 라이센스: str):
    if phelper.RB_GetGuild(interaction.guild.id) is None:
        embed = discord.Embed(title="FAILED", description="서버가 등록되어있지 않습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    result = phelper.RB_ExtendLicense(interaction.guild.id, 라이센스)
    
    if result == "NL":
        embed = discord.Embed(title="FAILED", description="유효하지 않은 라이센스 입니다.", color=discord.Color.red())
    elif result == "NR": # impossible
        embed = discord.Embed(title="FAILED", description="서버가 등록되어있지 않습니다.", color=discord.Color.red())
    elif result == "UL":
        embed = discord.Embed(title="FAILED", description="사용된 라이센스입니다.", color=discord.Color.red())
    else:
        embed = discord.Embed(title="SUCCESS", description="서버 라이센스가 연장되었습니다.", color=discord.Color.green())
        embed.add_field(name="유효기간", value=f"```{result}```", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

class AuthView(ui.View):
    def __init__(self, verify, original_interaction, selected_value):
        super().__init__()
        self.verify = verify
        self.original_interaction = original_interaction
        self.selected_value = selected_value
    
    @ui.button(label="정보 입력하기", style=discord.ButtonStyle.success)
    async def auth(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(AuthModal(self.verify, self.original_interaction, self.selected_value))

class OtpView(ui.View):
    def __init__(self, verify, original_interaction, name, birth, phone, selected_value):
        super().__init__()
        self.verify = verify
        self.name = name
        self.birth = birth
        self.phone = phone
        self.original_interaction = original_interaction
        self.selected_value = selected_value
    
    @ui.button(label="인증번호 입력", style=discord.ButtonStyle.success)
    async def otp(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(OtpModal(self.verify, self.original_interaction, self.name, self.birth, self.phone, self.selected_value))

class AuthModal(ui.Modal, title="인증"):
    def __init__(self, verify, original_interaction, selected_value):
        super().__init__()
        self.verify = verify
        self.original_interaction = original_interaction
        self.selected_value = selected_value

        self.name = ui.TextInput(label="이름", placeholder="이름을 입력해주세요.")
        self.birth = ui.TextInput(label="생년월일 & 성별", placeholder="2000년생 1월 1일 남자: 0001013")
        self.phone = ui.TextInput(label="전화번호", placeholder="전화번호를 숫자만 입력해주세요.")
        self.otp = ui.TextInput(label="캡챠", placeholder="캡챠를 입력해주세요.")

        self.add_item(self.name)
        self.add_item(self.birth)
        self.add_item(self.phone)
        self.add_item(self.otp)

    async def on_submit(self, interaction: Interaction):
        try:
            await interaction.response.defer()
            embed1 = discord.Embed(title="정보 검증 중", description="정보를 검증 중입니다. 잠시만 기다려 주세요...", color=discord.Color.yellow())
            is_guild_use_btn = phelper.GetMFileValue(df=phelper.LoadGMFile(), column_name="GuildID", row_name="BTN", column_standard_value=int(interaction.guild.id))
            if is_guild_use_btn:
                is_tn_json = TwoNumber.StartTNConfirm(pnumber=self.phone)
                if is_tn_json["two_number"] == True:
                    embed = discord.Embed(title="FAILED", description="이 서버에서는 투넘버 사용이 제한되었습니다.", color=discord.Color.red())
                    await original_message.edit(content=None, embed=embed, attachments=[], view=None)
                    return
            await self.original_interaction.edit_original_response(embed=embed1, attachments=[], view=None)
            result = await phelper.BeginPassVerify(self.name.value, self.birth.value, self.phone.value, self.otp.value, self.verify)
            original_message = await self.original_interaction.original_response()
            print(result)
            if not result:
                embed = discord.Embed(title="FAILED", description="올바르지 않은 정보를 입력하셨습니다.", color=discord.Color.red())
                await original_message.edit(content=None, embed=embed, attachments=[], view=None)
            else:
                embed = discord.Embed(title="인증번호 입력", description="발송된 인증번호를 입력해주세요.", color=discord.Color.blue())
                await original_message.edit(content=None, embed=embed, view=OtpView(self.verify, self.original_interaction, self.name, self.birth, self.phone, self.selected_value), attachments=[])

        except Exception as e:
            embed = discord.Embed(title="ERROR", description="인증번호 처리 중 오류가 발생했습니다.", color=discord.Color.red())
            embed.add_field(name="오류내용", value=f"```{e}```", inline=False)
            await self.original_interaction.edit_original_response(content=None, embed=embed, attachments=[], view=None)


class OtpModal(ui.Modal, title="인증번호 입력"):
    def __init__(self, verify, original_interaction, name, birth, phone, selected_value):
        super().__init__()
        self.verify = verify
        self.name = name
        self.birth = birth
        self.phone = phone
        self.original_interaction = original_interaction
        self.selected_value = selected_value
        self.otp = ui.TextInput(label="인증번호", placeholder="인증번호를 입력해주세요.", max_length=6, min_length=6)
        self.add_item(self.otp)
    
    async def on_submit(self, interaction: Interaction):
        try:
            await interaction.response.defer()
            await self.original_interaction.edit_original_response(content="인증번호 검증 중입니다. 잠시만 기다려 주세요...", embed=None, view=None)
            result = await phelper.CheckSMS(self.otp.value, self.verify)
            original_message = await self.original_interaction.original_response()
            print(result)
            if result['Message'] == "인증이 정상적으로 처리되었습니다.":
                embed_log = discord.Embed(title=f"<@{interaction.user.id}>님이 인증을 완료하였습니다.", description=f"```성명: {self.name.value}\n생년월일: {self.birth.value[:6]}-{self.birth.value[6]}\n전화번호: {self.phone.value}\n통신사: {self.selected_value}```", color=discord.Color.green())
                roleid = phelper.GetMFileValue(df=phelper.LoadGMFile(), column_name="GuildID", row_name="RoleID", column_standard_value=int(interaction.guild_id))
                if roleid == "undefined":
                    embed = discord.Embed(title="인증 설정오류", description="부여될 역할이 설정되지 않았습니다.\n서버 관리자에게 문의해주세요.", color=discord.Color.red())
                    await original_message.edit(content=None, embed=embed, attachments=[], view=None)
                    return
                webhooklink = phelper.GetMFileValue(df=phelper.LoadGMFile(), column_name="GuildID", row_name="WebhookLink", column_standard_value=int(interaction.guild_id))
                if webhooklink != "undefined":
                    webhookobj = SyncWebhook.from_url(webhooklink)
                    webhookobj.send(embed=embed_log, username="PSMS Verify Log", avatar_url=config.DefaultPfp)
                phelper.RB_AddRole(guildid=int(interaction.guild.id), userid=str(interaction.user.id), roleid=int(roleid))
                embed = discord.Embed(title="인증 완료", description="인증이 완료되었습니다.\n역할이 부여되지 않았을 경우, 서버관리자에게 문의해주세요.", color=discord.Color.green())
                
            else:
                
                embed = discord.Embed(title="인증 실패", description="인증에 실패하였습니다.", color=discord.Color.red())
        except Exception as e:
            embed = discord.Embed(title="ERROR", description="인증번호 처리 중 오류가 발생했습니다.", color=discord.Color.red())
            embed.add_field(name="오류내용", value=f"```{e}```", inline=False)
            await self.original_interaction.edit_original_response(content=None, embed=embed, attachments=[], view=None)
            
            return
        
        # 이미지와 버튼 모두 제거
        await self.original_interaction.edit_original_response(content=None, embed=embed, attachments=[], view=None)

@client.tree.command(name="whitelist", description="[BotAdmin] 화이트리스트관리")
async def enwh(interaction: Interaction, opt: AddDel, 유저: str):
    embed = None
    try:
        if (interaction.user.id in config.BotAdmin):
            user_id = str(유저)
            유저 = await client.fetch_user(user_id)
            if opt.value == "Add":
                result = phelper.AddWhitelist(userid=str(유저.id))
                action = "추가"
            elif opt.value == "Delete":
                result = phelper.RmWhitelist(userid=str(유저.id))
                action = "삭제"
                

            if result:
                embed = discord.Embed(
                    title=f"화이트리스트 {action} 성공",
                    description=f"**{action} 성공**\n\n`{유저.name}`님을 화이트리스트에 {action}했습니다.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(pytz.timezone("Asia/Seoul"))
                )
            else:
                embed = discord.Embed(
                    title="오류 발생",
                    description=f"**등록 실패**\n\n`{유저.name}`님은 이미 있거나(추가 시) 없습니다(삭제 시).",
                    color=discord.Color.red(),
                    timestamp=datetime.now(pytz.timezone("Asia/Seoul"))
                )
        else:
            embed = discord.Embed(
                title="권한 부족",
                description="이 기능을 사용하려면 봇관리자 권한이 필요합니다.",
                color=discord.Color.red(),
                timestamp=datetime.now(pytz.timezone("Asia/Seoul"))
            )
    except Exception as e:
        embed = discord.Embed(
            title="오류 발생",
            description=f"**등록 실패**\n```{traceback.format_exc()}```",
            color=discord.Color.red(),
            timestamp=datetime.now(pytz.timezone("Asia/Seoul"))
        )
    finally:
        if embed is not None:
            await interaction.response.send_message(embed=embed)

@client.tree.command(name="인증메시지", description="인증메시지를 전송합니다.")
@phelper.check_admin()
async def auth(interaction: Interaction):
    if phelper.RB_GetGuild(interaction.guild.id) is None:
        embed = discord.Embed(title="FAILED", description="서버가 등록되어있지 않습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    df = phelper.LoadGMFile()
    ispermitted = phelper.GetMFileValue(
        df=df,
        column_name="GuildID",
        row_name="Permitted",
        column_standard_value=str(interaction.guild_id)
    )
    if ispermitted == False:
        embed = discord.Embed(title="FAILED", description="라이센스가 만료되어 인증이 불가합니다.\라이센스를 연장해주세요.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    view = ui.View(timeout=None)
    button = ui.Button(style=ButtonStyle.green, label="인증하기", disabled=False, custom_id="verifybtn")
    view.add_item(button)
    embed = discord.Embed(title="SMS 인증하기", description="아래 버튼을 눌러 인증을 진행해주세요.\n(알뜰폰도 가능)", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=view)
    

#NoUse, 참고용
async def 존못씹게이소추펄스화이팅(interaction: Interaction):
    df = phelper.LoadGMFile()
    ispermitted = phelper.GetMFileValue(
        df=df,
        column_name="GuildID",
        row_name="Permitted",
        column_standard_value=str(interaction.guild_id)
    )
    if ispermitted == False:
        embed = discord.Embed(title="FAILED", description="라이센스가 만료되어 인증이 불가합니다.\n서버관리자에게 문의해 주세요.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    verify = await phelper.CaptchaManager("SKT", str(interaction.user.id)) #임시하드코딩
    embed = discord.Embed(title="전화번호 인증", description="캡챠를 기억하신후 아래 버튼을 눌러주세요.", color=discord.Color.blue())
    embed.set_image(url=f"attachment://{str(interaction.user.id)}_captcha.png") #file 첨부로 바꾸기
    await interaction.response.send_message(embed=embed, view=AuthView(verify), ephemeral=True)
    original_interaction = await interaction.original_response()
    view = AuthView(verify)
    view.auth.callback = lambda i: i.response.send_modal(AuthModal(verify, original_interaction))
    await original_interaction.edit(view=view)

async def RunBot():
    async with client:
        await client.start(config.BotToken)
if __name__ == "__main__":
    setupsystem.bootup()
    asyncio.run(RunBot())
