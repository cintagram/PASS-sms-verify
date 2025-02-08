import discord
from discord.ext import commands
from discord.ui import Button, TextInput
from discord import app_commands, Interaction, ui, ButtonStyle, SelectOption, SyncWebhook, TextChannel
import os
import traceback
import sqlite3
import pytz
from datetime import datetime
from . import phelper, config

class SMGModal(ui.Modal):
    titleb = ui.TextInput(
        label="제목",
        style=discord.TextStyle.short,
        placeholder="제목 입력",
        default=""
    )
    contentb = ui.TextInput(
        label="내용",
        style=discord.TextStyle.long,
        placeholder="내용 입력",
        default=""
    )
    def __init__(self, botpfpurl):
        self.botpfpurl = botpfpurl
        super().__init__(title="Embed 입력")
            
    async def on_submit(self, interaction: Interaction):
        #보낼 임베드 세팅
        embed = discord.Embed(
            title=self.titleb.value,
            description=self.contentb.value,
            color=discord.Color.blurple(),
            timestamp=datetime.now(pytz.timezone("Asia/Seoul"))
        )
        embed.set_footer(text=f"Sent by {interaction.user.name}")
        await interaction.response.send_message(content="등록된 모든 서버에 메시지를 보내고 있습니다.")
        
        #순서대로 보내기
        df = phelper.LoadGMFile()
        rdf = df[df["WebhookLink"] != "undefined"]
        for index, row in rdf.iterrows():
            wlink = row['WebhookLink']
            try:
                webhookobj = SyncWebhook.from_url(wlink)
                guild_info = phelper.RB_GetGuildInfo(srvid=int(row["GuildID"]))
                webhookobj.send(content=f"<@{guild_info['owner_id']}>", embed=embed, username="PS Restore Announcement", avatar_url=self.botpfpurl)
            except Exception as e:
                print(f"{row['GuildID']}에 메시지를 보내지 못했습니다.\n{traceback.format_exc()}")
                continue

class CEDModal(ui.Modal):
    titleb = ui.TextInput(
        label="제목",
        style=discord.TextStyle.short,
        placeholder="제목 입력",
        default=""
    )
    contentb = ui.TextInput(
        label="내용",
        style=discord.TextStyle.long,
        placeholder="내용 입력",
        default=""
    )
    def __init__(self, username1: str, chnl: TextChannel, botpfpurl: str):
        self.botpfpurl = botpfpurl
        self.username1 = username1
        self.chnl = chnl
        super().__init__(title="Embed 입력")
            
    async def on_submit(self, interaction: Interaction):
        #보낼 임베드 세팅
        embed = discord.Embed(
            title=self.titleb.value,
            description=self.contentb.value,
            color=discord.Color.blurple(),
            timestamp=datetime.now(pytz.timezone("Asia/Seoul"))
        )
        embed.set_footer(text=f"Sent by {interaction.user.name}")
        await interaction.response.send_message(content="메시지가 곧 전송됩니다.", ephemeral=True)
        webhook = await self.chnl.create_webhook(name="ps sms verify", reason="ced webhook")
        webhookurl = webhook.url
        webhookobj = SyncWebhook.from_url(webhookurl)
        webhookobj.send(embed=embed, username=self.username1, avatar_url=self.botpfpurl)
        webhookobj.delete()