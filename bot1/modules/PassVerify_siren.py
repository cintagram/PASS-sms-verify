import requests
import urllib.parse
import re
import random
from bs4 import BeautifulSoup
from io import BytesIO
import traceback


class PassVerify:
    global base_headers
    base_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }

    def __init__(self, ISP):
        self.ISP = ISP
        line1 = '23e99bd9dddd4634f8f0__cr.ru:7b880945d6a187c5@gw.dataimpulse.com:823'
        self.proxies = {"https": "https://" + line1}

        self.session = requests.Session()

    def initialize(self):
        try:
            response = self.session.get(
                'https://www.changwon.go.kr/cwportal/10783/10919.web?amode=rn%5Ename%5Eins&rurl=https%3A%2F%2Fwww.changwon.go.kr%2Fcwportal%2Fportal.web',
                headers=base_headers,
                proxies=self.proxies
            )

            headers = {
                **base_headers,
                'Connection': 'keep-alive',
                'Host': 'www.changwon.go.kr',
                'Referer': 'https://www.changwon.go.kr/cwportal/10783/10919.web?amode=rn%5Ename%5Eins&rurl=https%3A%2F%2Fwww.changwon.go.kr%2Fcwportal%2Fportal.web',
            }

            response = self.session.get(
                'https://www.changwon.go.kr/cwportal/realname/bizsiren/auth.do?rn_url=https%3A%2F%2Fwww.changwon.go.kr%2Fcwportal%2Fportal.web',
                headers=headers,
                proxies=self.proxies
            )
            text = response.text

            self.soup = BeautifulSoup(text, 'html.parser')
            form = self.soup.find('form', {'name': 'reqPCCForm'})
            parameter = {input_tag['name']: input_tag.get('value', '') for input_tag in form.find_all('input')}

            headers = {
                **base_headers,
                'Host': 'pcc.siren24.com',
                'Referer': 'https://www.changwon.go.kr/'
            }

            request_uri = f'https://pcc.siren24.com/pcc_V3/jsp/pcc_V3_j10_v2.jsp?{urllib.parse.urlencode(parameter)}'
            response = self.session.get(request_uri, headers=headers, proxies=self.proxies)
            text = response.text

            if '당일#인증#실패#기준을#초과#하였습니다' in text:
                raise Exception('당일 인증 실패 기준을 초과하였습니다.\n관리자에게 문의해주시기 바랍니다.')

            self.soup = BeautifulSoup(text, 'html.parser')
            form = self.soup.find('form', {'name': 'Pcc_V3Form'})
            form_data = {
                input_tag['name']: input_tag.get('value', '')
                for input_tag in form.find_all('input', {'type': 'hidden'})
            }
            headers['Referer'] = request_uri
            headers['Origin'] = 'https://pcc.siren24.com'
            request_uri = 'https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j10.jsp'
            response = self.session.post(request_uri, headers=headers, data=form_data, proxies=self.proxies)
            text = response.text

            self.soup = BeautifulSoup(text, 'html.parser')
            form = self.soup.find('form', {'name': 'cplogn'})
            form_data = {
                input_tag['name']: input_tag.get('value', self.ISP)
                for input_tag in form.find_all('input', {'type': 'hidden'})
            }

            headers = {
                **base_headers,
                'Host': 'pcc.siren24.com',
                'Referer': request_uri,
                'Origin': 'https://pcc.siren24.com',
            }
            request_uri = f"https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j30_certHp{'Mvno' if 'M' in self.ISP else ''}Ti01.jsp"
            response = self.session.post(request_uri, data=form_data, headers=headers, proxies=self.proxies)
            self.soup = BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException:
            print(traceback.format_exc())

    def GetCaptcha(self):
        try:
            response = self.session.get(
                'https://pcc.siren24.com/pcc_V3/Captcha/simpleCaptchaImg.jsp',
                headers=base_headers,
                proxies=self.proxies
            )
            return BytesIO(response.content)
        except requests.RequestException:
            print(traceback.format_exc())

    def SendSMS(self, name, jumin, phone, captcha_key):
        try:
            form = self.soup.find('form', {'name': 'goPass'})

            form_data = {}
            for input_tag in form.find_all('input', {'type': 'hidden'}):
                form_data[input_tag['name']] = input_tag['value']

            form_data["userName"] = name
            form_data["birthDay1"] = jumin[:6]
            form_data["birthDay2"] = jumin[6]
            form_data["No"] = phone
            form_data["captchaInput"] = captcha_key

            defaultUrl = form.get('action', '')
            request_uri = defaultUrl if defaultUrl else f"https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j30_certHp{'Mvno' if 'M' in self.ISP else ''}Ti02.jsp"

            response = self.session.post(request_uri, data=form_data, headers=base_headers, proxies=self.proxies)
            text = response.text

            if '보안문자를 정확히 입력해 주세요.' in text:
                return {'IsSuccess': False, 'Message': '보안문자를 정확히 입력해 주세요.'}

            self.soup = BeautifulSoup(text, 'html.parser')
            form = self.soup.find('form', {'name': 'goForm'})
            if form is not None:
                form_data = {
                    input_tag['name']: input_tag['value']
                    for input_tag in form.find_all('input', {'type': 'hidden'})
                }
                if 'M' in self.ISP:
                    request_uri = form.get('action')
                    response = self.session.post(request_uri, data=form_data, headers=base_headers, proxies=self.proxies)
                    self.soup = BeautifulSoup(response.text, 'html.parser')
                    form = self.soup.find('form', {'name': 'goForm'})
                    if form is not None:
                        form_data = {
                            input_tag['name']: input_tag['value']
                            for input_tag in form.find_all('input', {'type': 'hidden'})
                        }
                        request_uri = form.get('action')
                        response = self.session.post(request_uri, data=form_data, headers=base_headers, proxies=self.proxies)
                        self.soup = BeautifulSoup(response.text, 'html.parser')
                else:
                    request_uri = form.get('action')
                    response = self.session.post(request_uri, data=form_data, headers=base_headers, proxies=self.proxies)
                    self.soup = BeautifulSoup(response.text, 'html.parser')

            form = self.soup.find('form', {'name': 'goPass'})
            if form is None:
                return {'IsSuccess': False, 'Message': '올바르지 않은 정보를 입력하셨습니다.'}
            self.reqInfo = form.find('input', {'name': 'reqInfo'})['value']
            self.retUrl = form.find('input', {'name': 'retUrl'})['value']
            return {'IsSuccess': True, 'Message': '인증번호가 전송되었습니다.'}
        except requests.RequestException:
            print(traceback.format_exc())
            return {'IsSuccess': False, 'Message': '연결실패'}

    def CheckSMS(self, otp):
        try:
            data = {
                'otp': otp,
                'reqInfo': self.reqInfo,
                'retUrl': self.retUrl
            }
            response = self.session.post(
                'https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j30_certHpTi04.jsp',
                data=data,
                headers=base_headers,
                proxies=self.proxies
            )
            text = response.text

            self.soup = BeautifulSoup(text, 'html.parser')
            script_node = self.soup.find('script', {'language': 'javascript'}).string

            pattern = re.compile(r'pop_alert\("([^"]+)"\)')
            match = pattern.search(script_node)

            if match:
                message = match.group(1)
                if '인증에 성공' in message:
                    return {'IsSuccess': True, 'Message': message}
                else:
                    return {'IsSuccess': False, 'Message': message}

            return {'IsSuccess': False, 'Message': '인증 실패'}
        except requests.RequestException:
            print(traceback.format_exc())
            return {'IsSuccess': False, 'Message': '연결실패'}
