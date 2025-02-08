import disnake

### 본인인증 ###
class SupportModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="이름",
                placeholder="성함을 입력해 주세요.",
                custom_id="name",
                style=disnake.TextInputStyle.short,
                min_length=2,
                max_length=4,
            ),
            disnake.ui.TextInput(
                label="생년월일/성별",
                placeholder="[주민등록7자리]ex) 0601013",
                custom_id="birth",
                style=disnake.TextInputStyle.short,
                min_length=6,
                max_length=7,
            ),
            disnake.ui.TextInput(
                label="휴대폰번호",
                placeholder="숫자만 입력해주세요.",
                custom_id="phone",
                style=disnake.TextInputStyle.short,
                min_length=10,
                max_length=11,
            )
        ]
        super().__init__(
            title="문자(SMS) 휴대폰본인확인",
            custom_id="verify1",
            components=components,
        )

class SupportModal3(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="캡챠",
                placeholder="캡챠를 입력해 주세요.",
                custom_id="captcha",
                style=disnake.TextInputStyle.short,
                min_length=6,
                max_length=6,
            )
        ]
        super().__init__(
            title="문자(SMS) 휴대폰본인확인",
            custom_id="verify3",
            components=components,
        ) 

class SupportModal2(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="인증번호",
                placeholder="문자로온 숫자 6자리를 입력해 주세요.",
                custom_id="verify",
                style=disnake.TextInputStyle.short,
                min_length=1,
                max_length=99,
            ),
        ]
        super().__init__(
            title="문자(SMS) 휴대폰본인확인",
            custom_id="verify2",
            components=components,
        )