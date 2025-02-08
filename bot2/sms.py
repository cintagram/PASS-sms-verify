import disnake,asyncio,requests,os
from disnake.ext import commands
from discord_webhook import DiscordEmbed, DiscordWebhook
from bs4 import BeautifulSoup as soup
import modal

intents = disnake.Intents.all()
bot = commands.Bot(intents=intents, command_prefix='.')

color = 0xffffff

@bot.event
async def on_button_click(interaction:disnake.Interaction):
    cid = interaction.component.custom_id
    if cid == "verif":
        await interaction.send(
            ephemeral=True,
            embed=disnake.Embed(color =color ,description="안전한 이용을 위해 실명 인증을 진행 합니다.").set_author(icon_url=interaction.author.avatar.url,name="가입하기"),
            components=[
                [
                    disnake.ui.Button(label="SKT", style=disnake.ButtonStyle.blurple, custom_id='verify:SKT'),
                    disnake.ui.Button(label="KT", style=disnake.ButtonStyle.blurple, custom_id='verify:KTF'),
                    disnake.ui.Button(label="LG U+", style=disnake.ButtonStyle.blurple, custom_id='verify:LGT')
                ],
                [
                    disnake.ui.Button(label="SKT(알뜰)", style=disnake.ButtonStyle.blurple, custom_id='verify:SKM 2'),
                    disnake.ui.Button(label="KT(알뜰)", style=disnake.ButtonStyle.blurple, custom_id='verify:KTM 2'),
                    disnake.ui.Button(label="LG(알뜰)", style=disnake.ButtonStyle.blurple, custom_id='verify:LGM 2')
                ]
            ]
        )

    if "verify:" in cid:
        if not '2' in cid:
            isp = cid.split(":")[1]
        else:
            isp = cid.split(":")[1].split(" ")[0]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        session = requests.Session()
        try:
            rs = session.get('https://www.jeju.go.kr/mypage/find.htm',headers=headers,verify=False)
        except requests.ConnectionError:
            new_embed = disnake.Embed(title=f"{interaction.user.name}", color=0xFF0000)
            new_embed.add_field(name="인증실패", value="정보를 가져오는중 오류가 발생했습니다. 다시 시도 해주세요.", inline=False)
            new_embed.set_thumbnail(interaction.user.display_avatar)
            return await interaction.edit_original_response(embed=new_embed)
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding' : 'gzip, deflate, br, zstd',
            'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection' : 'keep-alive',
            'Host': 'www.jeju.go.kr',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile' : '?0',
            'sec-ch-ua-platform' : '"Windows"',
            'Sec-Fetch-Dest' : 'document',
            'Sec-Fetch-Mode' : 'navigate',
            'Sec-Fetch-Site' : 'same-origin',
            'Sec-Fetch-User' : '?1',
            'Upgrade-Insecure-Requests' : '1',
            'Referer': 'https://www.jeju.go.kr/mypage/find.htm',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }

        r = session.get('https://www.jeju.go.kr/tool/pcc/check.jsp?for=findpw', headers=headers)

        soupp = soup(r.text, 'html.parser')
        input_field = soupp.find('input', {'name': 'reqInfo'})
        reqinfo = input_field['value']

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Host': 'pcc.siren24.com',
            'Origin': 'https://pcc.siren24.com',
            'Referer': 'https://www.jeju.go.kr/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        res = session.get(f'https://pcc.siren24.com/pcc_V3/jsp/pcc_V3_j10_v2.jsp?reqInfo={reqinfo}&retUrl=32https%3A%2F%2Fwww.jeju.go.kr%2Ftool%2Fpcc%2Fresult.jsp&verSion=2',cookies=session.cookies, headers=headers)

        reqInfo = res.text.split('<input type="hidden" name="reqInfo" value = "')[1].split('"')[0]
        retUrl = res.text.split('<input type="hidden" name="retUrl"  value = "')[1].split('"')[0]

        json1 = {
            'reqInfo': reqInfo,
            'cellCorp': f'{isp}',
            'retUrl': retUrl,
            'advertiseInfo': 'N',
            'phoneNum': '',
            'sci_name': '',
            'sci_agency': '',
        }
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Host': 'pcc.siren24.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': f'https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j10.jsp',
            'Origin': 'https://pcc.siren24.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        result = session.post(f'https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j30_certHpTi01.jsp',data=json1,headers=headers, cookies=session.cookies)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        json1 = {
            'reqInfo': reqInfo,
            'retUrl': retUrl,
            'advertiseInfo': 'N',
        }
        chunk = session.get("https://pcc.siren24.com/pcc_V3/Captcha/simpleCaptchaImg.jsp",data=json1,headers=headers)

        os.makedirs('captcha', exist_ok=True)
        with open(f'captcha/captcha-{interaction.user.id}.png', 'wb') as f:
            f.write(chunk.content)

        new_embed = disnake.Embed(title=f"{interaction.user.name}", color=color)
        new_embed.add_field(name="", value="", inline=False)
        new_embed.add_field(name="휴대폰 간편인증 ㅣ 문자 (SMS) 로 인증", value=f"- 5분 내로 간편인증을 진행해 주세요.", inline=False)
        new_embed.set_thumbnail(interaction.user.display_avatar)
        components = [[disnake.ui.Button(label="간편인증", style=disnake.ButtonStyle.green, custom_id='next')]]
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_message(embed=new_embed, components=components)

        try:
            button_ctx: disnake.Interaction = await bot.wait_for(
                "button_click",
                check=lambda i: i.component.custom_id == "next" and i.author.id == interaction.author.id,
                timeout=300,
            )
        except asyncio.TimeoutError:
            return

        if button_ctx:
            await button_ctx.response.send_modal(modal=modal.SupportModal())
            try:
                modal_inter1: disnake.ModalInteraction = await bot.wait_for(
                    "modal_submit",
                    check=lambda i: i.custom_id == "verify1" and i.author.id == interaction.author.id,
                    timeout=None,
                )
            except asyncio.TimeoutError:
                return

            name = modal_inter1.text_values["name"]
            birth_1 = modal_inter1.text_values["birth"][:-1]
            birth_2 = modal_inter1.text_values["birth"][-1]
            phone = modal_inter1.text_values["phone"]

            # if check_user_identify(phone):
            #     new_embed = disnake.Embed(title=f"{interaction.user.name}", color=0xFF0000)
            #     new_embed.add_field(name="가입 실패 ", value="이미 가입된 정보 입니다.", inline=False)
            #     new_embed.set_thumbnail(interaction.user.display_avatar)
            #     return await interaction.edit_original_response(embed=new_embed, components=components, ephemeral=True)


            new_embed21 = disnake.Embed(title=f"{interaction.user.name}", color=color)
            new_embed21.add_field(name="", value="", inline=False)
            new_embed21.add_field(name="보안 문자 입력", value=f"- 하단에 보이는 보안 문자를 입력 해주세요.", inline=False)
            new_embed21.set_thumbnail(interaction.user.display_avatar)
            components = [[disnake.ui.Button(label="보안 문자 입력", style=disnake.ButtonStyle.green, custom_id='next123')]]

            await interaction.edit_original_response(embed=new_embed21, components=components)
            await modal_inter1.send(embed=disnake.Embed(color=color).set_image(file=disnake.File(f"captcha/captcha-{interaction.user.id}.png")),ephemeral=True)
            
            try:
                button_ctx1: disnake.Interaction = await bot.wait_for(
                    "button_click",
                    check=lambda i: i.component.custom_id == "next123" and i.author.id == interaction.author.id,
                    timeout=120,
                )
            except asyncio.TimeoutError:
                return

            if button_ctx1:
                try:await button_ctx1.response.send_modal(modal=modal.SupportModal3())
                except:pass
                try:
                    modal_inter: disnake.ModalInteraction = await bot.wait_for(
                        "modal_submit",
                        check=lambda i: i.custom_id == "verify3" and i.author.id == interaction.author.id,
                        timeout=None,
                    )
                except asyncio.TimeoutError:
                    return
                
                captcha = modal_inter.text_values["captcha"]
                await modal_inter.response.defer(ephemeral=True)
                await modal_inter.delete_original_response()
                await modal_inter1.delete_original_response()
                new1_embed = disnake.Embed(title=f"{interaction.user.name}", color=color)
                new1_embed.add_field(name="", value="", inline=False)
                new1_embed.add_field(name="휴대폰 간편인증 ㅣ 문자 (SMS) 로 인증", value=f"- 사용자 정보를 확인 중입니다", inline=False)
                new1_embed.set_thumbnail(interaction.user.display_avatar)
                await interaction.edit_original_response(embed=new1_embed)
                json1 = {
                    'reqInfo': reqInfo,
                    'cellCorp': f'{isp}',
                    'retUrl': retUrl,
                    'advertiseInfo': 'N',
                    'userName': f'{name}',
                    'birthDay1': f'{birth_1}',
                    'birthDay2': f'{birth_2}',
                    'No': F'{phone}',
                    'captchaInput': f'{captcha}',
                    'passGbn': 'N',
                }
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Host': 'pcc.siren24.com',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': f'https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j30_certHpTi01.jsp',
                    'Origin': 'https://pcc.siren24.com',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'

                }
                result = session.post(f'https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j30_certHpTi02.jsp',data=json1,headers=headers, cookies=session.cookies)
                if '보안문자를 정확히 입력해 주세요..' in result.text:
                    try:
                        newembed = disnake.Embed(title=f"{interaction.user.name}", color=0xFF0000)
                        newembed.add_field(name="", value="", inline=False)
                        newembed.add_field(name="잘못된 정보 입력", value='- 보안문자를 정확히 입력해 주세요.', inline=False)
                        newembed.set_thumbnail(interaction.user.display_avatar)
                        await interaction.edit_original_response(embed=newembed, components='')
                        return
                    except Exception as e:
                        print(e)
                        pass
                else:
                    try:
                        reqInfo = result.text.split('<input type="hidden" name="reqInfo" value="')[1].split('"')[0]
                        retUrl = result.text.split('<input type="hidden" name="retUrl"  value="')[1].split('"')[0]
                    except Exception as e:
                        print(e)
                        newembed = disnake.Embed(title=f"{interaction.user.name}", color=0xFF0000)
                        newembed.add_field(name="", value="", inline=False)
                        newembed.add_field(name="잘못된 정보 입력", value='- 정보가 올바르지 않습니다.1', inline=False)
                        newembed.set_thumbnail(interaction.user.display_avatar)
                        await interaction.edit_original_response(embed=newembed, components='')
                        return
                json1 = {
                    'reqInfo': reqInfo,
                    'retUrl': retUrl
                }
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Host': 'pcc.siren24.com',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': f'https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j30_certHpTi02.jsp',
                    'Origin': 'https://pcc.siren24.com',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'

                }
                rr = session.post(f'https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j30_certHpTi03.jsp',data=json1,headers=headers, cookies=session.cookies)

                try:
                    reqInfo = rr.text.split('<input type="hidden" name="reqInfo"     value="')[1].split('"')[0]
                    retUrl = rr.text.split('<input type="hidden" name="retUrl"      value="')[1].split('"')[0]
                except Exception as e:
                    print(e)
                    newembed = disnake.Embed(title=f"{interaction.user.name}", color=0xFF0000)
                    newembed.add_field(name="", value="", inline=False)
                    newembed.add_field(name="잘못된 정보 입력", value=f"- 정보가 올바르지 않습니다.", inline=False)
                    newembed.set_thumbnail(interaction.user.display_avatar)
                    await interaction.edit_original_response(embed=newembed, components='')
                    return

                newembed = disnake.Embed(title=f"{interaction.user.name}", color=color)
                newembed.add_field(name="", value="", inline=False)
                newembed.add_field(name="휴대폰 간편인증 ㅣ 문자 (SMS) 로 인증", value='- 3분 이내로 인증번호(6자리)를 입력해 주세요.', inline=False)
                newembed.set_thumbnail(interaction.user.display_avatar)
                components = [
                    [
                        disnake.ui.Button(label="인증하기", style=disnake.ButtonStyle.green, custom_id='next')
                    ]]
                await interaction.edit_original_response(embed=newembed, components=components)
                try:
                    button_ctx: disnake.Interaction = await bot.wait_for(
                        "button_click",
                        check=lambda i: i.component.custom_id == "next" and i.author.id == interaction.author.id,
                        timeout=180,
                    )
                except asyncio.TimeoutError:
                    newembed = disnake.Embed(title=f"{interaction.user.name}", color=0xFF0000)
                    newembed.add_field(name="", value="", inline=False)
                    newembed.add_field(name="잘못된 정보 입력", value='- 시간이 초과되었습니다.', inline=False)
                    newembed.set_thumbnail(interaction.user.display_avatar)
                    await interaction.edit_original_response(embed=newembed, components='')
                    return

                if button_ctx:
                    await button_ctx.response.send_modal(modal=modal.SupportModal2())
                    try:
                        modal_inter: disnake.ModalInteraction = await bot.wait_for(
                            "modal_submit",
                            check=lambda i: i.custom_id == "verify2" and i.author.id == interaction.author.id,
                            timeout=None,
                        )
                    except asyncio.TimeoutError:
                        return
                    await modal_inter.response.defer(ephemeral=True)
                    await modal_inter.delete_original_response()
                    newembed = disnake.Embed(title=f"{interaction.user.name}", color=color)
                    newembed.add_field(name="", value="", inline=False)
                    newembed.add_field(name="휴대폰 간편인증 ㅣ 문자 (SMS) 로 인증", value='- 인증번호를 확인 중입니다', inline=False)
                    newembed.set_thumbnail(interaction.user.display_avatar)
                    await interaction.edit_original_response(embed=newembed)
                    num = modal_inter.text_values["verify"]
                    json1 = {
                        'otp': num,
                        'reqInfo': reqInfo,
                        'retUrl': retUrl,
                    }
                    headers = {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                        'Host': 'pcc.siren24.com',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Referer': f'https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j30_certHpTi03.jsp',
                        'Origin': 'https://pcc.siren24.com',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'

                    }
                    res = session.post(f'https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j30_certHpTi04.jsp',data=json1, headers=headers, cookies=session.cookies)
                    
                    if '인증번호가 일치하지 않습니다.' in res.text:
                        newembed1 = disnake.Embed(title=f"{interaction.user.name}", color=0xFF0000)
                        newembed1.add_field(name="", value="", inline=False)
                        newembed1.add_field(name="잘못된 정보 입력", value='- 인증번호가 일치하지 않습니다.', inline=False)
                        newembed1.set_thumbnail(interaction.user.display_avatar)
                        await interaction.edit_original_response(embed=newembed1, components='')
                        return
                    else:
                        newembed1 = disnake.Embed(title=f"{interaction.user.name}", color=color)
                        newembed1.add_field(name="", value="", inline=False)
                        newembed1.add_field(name="인증 완료", value=f'- 이제 PULSErvice를 이용하실 수 있습니다!', inline=False)
                        newembed1.set_thumbnail(interaction.user.display_avatar)
                        await interaction.edit_original_response(embed=newembed1, components='')

                    try:
                        webhook = DiscordWebhook(url="")
                        eb = DiscordEmbed(title='SMS 인증로그', description=f'* **인증유저**: `{interaction.user.name}({interaction.user.id})`\n* **전화번호**: `{phone}`\n* **통신사**: `{isp}`\n* **주민번호**: `{birth_1}-{birth_2}`\n* **성별**: `{"남자" if int(birth_2) % 2 == 1 else "여자"}`', color=color)
                        webhook.add_embed(eb)
                        webhook.execute()
                    except:
                        pass
                    # add_user(interaction.user.id,birth_1+"-"+birth_2,phone,"남자" if int(birth_2) % 2 == 1 else "여자")
