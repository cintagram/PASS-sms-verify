import requests
import base64
import json
from . import config
def thecheat_login(email, passwd):
    jsonObject = {
        "phone_app_version": "3.0.5",
        "phone_app_lang": "ko",
        "phone_ios_version": "17.4.1",
        "phone_nation": "ko",
        "phone_model": "iPhone15,4",
        "pw": passwd,
        "unique_p_uid": "90B91F56-B42F-45DA-9E8E-9043DE3322D5",
        "phone_provider": "",
        "phone_uuid": "90B91F56-B42F-45DA-9E8E-9043DE3322D5",
        "phone_number": "",
        "id": email,
        "phone_email": ""
    }

    jsonString = json.dumps(jsonObject)
    base64data = base64.b64encode(jsonString.encode('utf-8')).decode('utf-8')

    headers = {
        "appversion": "3.0.5",
        "User-Agent": "corp/3.0.5 (kr.thecheat.corp; build:21; iOS 17.4.1) Alamofire/5.9.1",
        "Content-Type": "multipart/form-data; boundary=alamofire.boundary.a92307a4f9eb86e5"
    }

    data = f"--alamofire.boundary.a92307a4f9eb86e5\nContent-Disposition: form-data; name=\"contents\"\n\n{base64data}\n--alamofire.boundary.a92307a4f9eb86e5--"

    try:
        res = requests.post("https://thecheat.co.kr/thecheat/app/MemberCheck.php", data=data, headers=headers)
        res_data = res.json()

        if 'content' in res_data:
            decoded_content = decode64(res_data['content'])
            hexArray = [hex_val.strip() for hex_val in decoded_content.split(',')]
            decodedString = ''.join([chr(int(hex_val, 16)) for hex_val in hexArray])
            data = json.loads(decodedString)
            return data
        else:
            return {"msg": decode64(res_data.get("msg", ""))}
    except Exception as e:
        print("Error occurred during request:", e)

def check_two_number(phone_number, token):
    jsonObject = {
        "keyword": phone_number,
        "ad_view_bit": "1",
        "premium_request_type": "two_number",
        "fraud_result_enc": "eKEoW7GjtXNq1znxiuLgZn2227bZ%2BjfJrx1Y4pUAUXx9k6k8UbHpTeeoRE%2Fm5CgQwXzR%2FOnEVfGWMaBcQqQKD02KmmFfrUNB96S5DSEUmrcV2HEtr%2FZ6I5cEBZuUMw0GyiNClkUq%2BKxRaQHMAAyFInlbemWUSh3xmjUD1oJsYd6P6j9TuK1otlsicNkD8JkPwYuXJAtx1kSSmy8h1pu2iZLZXw9QbyjCIsACaPB72wQGjH7iwHvZ1NgCLpBKxw1CLBv%2FCGCQC7oHtGlrrbIdxWihsWFXpOTplzGYXa6pmyduBdVDaHIhLixhtngMyd8bQr4Nv0924uu79qoMAUDZrsO0UJmfShalRooXYuaxziAX9Rz297319VEJ6mre2bV7QvtByMXoofNFgn5nuzZpbFe5SfIxd5bBCtvsW71ijqIVgcvuXmAPYW2%2FAXjr0tf%2BtTOwfZX7dFgR%2B2U2lfWLqolM2ejQM5%2BZ7j8CguPXgIO65hasKx%2FRffKWIqFRttT6DAsf7wXm9vhZSPdsrh9WtihuZJ%2F4xH64At5bDPzgla6D8MiGPvNNv%2Bi42WnC38WdET6HTnxZBVoz2392BbAI6ZpiQMkovNPV62jxbLgRUxX56XATuB0p7X%2B8c8qyaYKaXOJeR74F0QHsCaeAjoVV3ftZSo%2BxQZ4kcX4Ch2laHee67cZfn2bH%2FHpVvqFWp86CySkvUets3BKf3n5ueKXi79Wzxo9xnPbQ%2FNSPTtpGR7MNsx%2BKFGKlqoAFnxyK5MDJq2yXd89TqpHBkXSQukvGvFRGdEYi9gHqTHmqEm7KpCRx18D0HnrUs9HmT6%2B66rnI%2B7M0Ge5LRDI6OiOaKOtwVzvw"
    }

    jsonString = json.dumps(jsonObject)
    base64data = base64.b64encode(jsonString.encode('utf-8')).decode('utf-8')

    headers = {
        "Authorization": token,
        "appversion": "3.0.5",
        "User-Agent": "corp/3.0.5 (kr.thecheat.corp; build:21; iOS 17.4.1) Alamofire/5.9.1",
        "Content-Type": "multipart/form-data; boundary=alamofire.boundary.a92307a4f9eb86e5"
    }

    data = f"--alamofire.boundary.a92307a4f9eb86e5\nContent-Disposition: form-data; name=\"contents\"\n\n{base64data}\n--alamofire.boundary.a92307a4f9eb86e5--"

    try:
        res = requests.post("https://thecheat.co.kr/thecheat/app/FraudSearchV4.php", data=data, headers=headers)
        res_data = res.json()

        if 'content' in res_data:
            decoded_content = decode64(res_data['content'])
            hexArray = [hex_val.strip() for hex_val in decoded_content.split(',')]
            decodedString = ''.join([chr(int(hex_val, 16)) for hex_val in hexArray])
            data = json.loads(decodedString)
            return {
                "msg": data[0]["two_number_info"]["msg"],
                "two_number": data[0]["two_number_info"]["bool"]
            }
        else:
            print(res_data)
    except Exception as e:
        print("Error occurred during request:", e)

def decode64(base64String):
    return base64.b64decode(base64String).decode('utf-8')

def StartTNConfirm(pnumber: str):
    login_data = thecheat_login(config.TC_ID, config.TC_PW)
    if login_data and "member_key" in login_data[0]:
        result = check_two_number(pnumber, login_data[0]["member_key"])
        return result
