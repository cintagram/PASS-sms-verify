import aiohttp
import urllib.parse
import re
from bs4 import BeautifulSoup
from io import BytesIO

class PassVerify:
    global base_headers
    base_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }

    def __init__(self, ISP):
        self.ISP = ISP
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        await self.session.close()

    async def initialize(self):
        async with self.session.get('https://www.daegu.go.kr/front/customMember/joinPreTerm.do?age=up') as response:
            pass
        print("joinPreTerm")

        headers = {
            **base_headers,
            'Connection': 'keep-alive',
            'Host': 'www.daegu.go.kr',
            'Referer': 'https://www.daegu.go.kr/front/customMember/joinPreTerm.do?age=up',
        }

        async with self.session.get('https://www.daegu.go.kr/apis/kmcisSelfCheck/step2.do', headers=headers) as response:
            text = await response.text()
        print("step2")

        self.soup = BeautifulSoup(text, 'html.parser')
        form = self.soup.find('form', {'name': 'reqKMCISForm'})
        parameter = {input_tag['name']: input_tag.get('value', '') for input_tag in form.find_all('input')}
        print(parameter)
        headers = {
            **base_headers,
            'Host': 'www.kmcert.com',
            'Referer': 'https://www.daegu.go.kr/'
        }
        
        request_uri = f'https://www.kmcert.com/kmcis/web/kmcisReq.jsp?{urllib.parse.urlencode(parameter)}'
        print(request_uri)
        async with self.session.get(request_uri, headers=headers) as response:
            print(text)
            text = await response.text()
        print("parameter")


        if '당일#인증#실패#기준을#초과#하였습니다' in text:
            raise Exception('당일 인증 실패 기준을 초과하였습니다.\n관리자에게 문의해주시기 바랍니다.')

        self.soup = BeautifulSoup(text, 'html.parser')
        form = self.soup.find('form', {'name': 'KmcisFom'})
        form_data = {
            input_tag['name']: input_tag.get('value', '')
            for input_tag in form.find_all('input', {'type': 'hidden'})
        }
        print("cplogn")
        headers['Referer'] = request_uri
        headers['Origin'] = 'https://www.kmcert.com'
        request_uri = 'https://www.kmcert.com/kmcis/web_v4/kmcisHp00.jsp'
        async with self.session.post(request_uri, headers=headers, data=form_data) as response:
            text = await response.text()

        self.soup = BeautifulSoup(text, 'html.parser')
        form = self.soup.find('form', {'name': 'cplogn'})
        form_data = {
            input_tag['name']: input_tag.get('value', self.ISP)
            for input_tag in form.find_all('input', {'type': 'hidden'})
        }
        print("cplogn2")

        headers = {
            **base_headers,
            'Host': 'www.kmcert.com',
            'Referer': request_uri,
            'Origin': 'https://www.kmcert.com',
        }
        request_uri = f"https://www.kmcert.com/kmcis/web_v4/kmcisSms01.jsp"
        async with self.session.post(request_uri, data=form_data, headers=headers) as response:
            text = await response.text()
        
        print("=====INITIALIZE COMPLETE=====")
        self.soup = BeautifulSoup(text, 'html.parser')

    async def GetCaptcha(self):
        async with self.session.get('https://www.kmcert.com/KmcCaptcha.png', headers=base_headers) as response:
            content = await response.read()

        return BytesIO(content)

    async def SendSMS(self, name, jumin, phone, captcha_key):
        form = self.soup.find('form', {'name': 'cplogn'})

        form_data = {}
        for input_tag in form.find_all('input', {'type': 'hidden'}):
            form_data[input_tag['name']] = input_tag['value']

        form_data["CommId"] = self.ISP
        form_data["reqCommIdStated"] = self.ISP

        headers = {
            **base_headers,
            'Host': 'www.kmcert.com',
            'Referer': 'https://www.kmcert.com/kmcis/web_v4/kmcisHp00.jsp',
            'Origin': 'https://www.kmcert.com',
        }
        
        request_uri = "https://www.kmcert.com/kmcis/web_v4/kmcisSms01.jsp"
        async with self.session.post(request_uri, data=form_data, headers=headers) as response:
            text = await response.text()

        form = self.soup.find('form', {'name': 'cplogn'})

        form_data = {}
        for input_tag in form.find_all('input', {'type': 'hidden'}):
            form_data[input_tag['name']] = input_tag['value']
        print(form_data)

        headers = {
            **base_headers,
            'Host': 'www.kmcert.com',
            'Referer': 'https://www.kmcert.com/kmcis/web_v4/kmcisSms01.jsp',
            'Origin': 'https://www.kmcert.com',
        }

        form_data1 = {
            'reqSeq': form_data["reqSeq"],
            'No': phone,
            'CommId': self.ISP,
            'icsgCode': form_data["icsgCode"]
        }

        request_uri = "https://www.kmcert.com/kmcis/comm_v2/checkCellNo.jsp"
        async with self.session.post(request_uri, data=form_data1, headers=headers) as response:
            text = await response.text()

        print("cplogn input_tag")
        print(jumin[:6])
        print(jumin[6])
        print(urllib.parse.quote(name.encode('euc-kr')))
        
        form_data["userName"] = urllib.parse.quote(name.encode('euc-kr'))
        form_data["Birth"] = jumin[:6]
        form_data["Sex"] = jumin[6]
        form_data["No"] = phone
        form_data["securityNum"] = captcha_key

        headers = {
            **base_headers,
            'Referer': 'https://www.kmcert.com/kmcis/web_v4/kmcisSms01.jsp',
            'Origin': 'https://www.kmcert.com',
            'Host': 'www.kmcert.com'
        }
        request_uri = "https://www.kmcert.com/kmcis/web_v4/kmcisSms02.jsp"

        async with self.session.post(request_uri, data=form_data, headers=headers) as response:
            text = await response.text()
            print(text) #에러페이지

        if '보안문자를 정확히 입력해 주세요.' in text:
            return {'IsSuccess': False, 'Message': '보안문자를 정확히 입력해 주세요.'}

        self.soup = BeautifulSoup(text, 'html.parser')
        form = self.soup.find('form', {'name': 'cplogn'})
        if form is not None:
            form_data = {
                input_tag['name']: input_tag['value']
                for input_tag in form.find_all('input', {'type': 'hidden'})
            }
            if 'M' in self.ISP:
                request_uri = form.get('action')
                async with self.session.post(request_uri, data=form_data, headers=base_headers) as response:
                    response_body = await response.text()
                    self.soup = BeautifulSoup(response_body, 'html.parser')
                request_uri = form.get('action')
                form = self.soup.find('form', {'name': 'cplogn'})
                if form is not None:
                    form_data = {
                        input_tag['name']: input_tag['value']
                        for input_tag in form.find_all('input', {'type': 'hidden'})
                    }
                    request_uri = form.get('action')
                    async with self.session.post(request_uri, data=form_data, headers=base_headers) as response:
                        response_body = await response.text()
                        self.soup = BeautifulSoup(response_body, 'html.parser')
                        
            else:
                request_uri = form.get('action')
                async with self.session.post(request_uri, data=form_data, headers=base_headers) as response:
                    response_body = await response.text()
                    self.soup = BeautifulSoup(response_body, 'html.parser')

        form = self.soup.find('form', {'name': 'goPass'})
        if form is None:
            return {'IsSuccess': False, 'Message': '올바르지 않은 정보를 입력하셨습니다.'}
        self.reqInfo = form.find('input', {'name': 'reqInfo'})['value']
        self.retUrl = form.find('input', {'name': 'retUrl'})['value']
        return {'IsSuccess': True, 'Message': '인증번호가 전송되었습니다.'}

    async def CheckSMS(self, otp):
        data = {
            'otp': otp,
            'reqInfo': self.reqInfo,
            'retUrl': self.retUrl
        }
        async with self.session.post('https://pcc.siren24.com/pcc_V3/passWebV2/pcc_V3_j30_certHpTi04.jsp', data=data, headers=base_headers) as response:
            text = await response.text()

        self.soup = BeautifulSoup(text, 'html.parser')
        script_node = self.soup.find('script', {'language': 'javascript'}).string

        pattern = re.compile(r'pop_alert\("([^"]+)"\)')
        match = pattern.search(script_node)

        if match:
            message = match.group(1)
            return {'IsSuccess': message == '인증이 정상적으로 처리되었습니다.', 'Message': '인증이 정상적으로 처리되었습니다.'}
        return {'IsSuccess': False, 'Message': '인증번호가 일치하지 않습니다.'}

    async def close(self):
        await self.session.close()