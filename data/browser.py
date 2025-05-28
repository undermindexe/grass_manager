import asyncio
from aiohttp import ClientSession, TCPConnector

from fake_useragent import UserAgent


class Browser:
    def __init__(self, user_agent: str, proxy: str = None):
        self.session = ClientSession(trust_env=True, connector=TCPConnector(ssl=False))
        self.ip = None
        self.username = None
        self.proxy = None

        self.url = {
            'register': 'https://api.grass.io/register',
            'login': 'https://api.grass.io/login',
            'retrieveUser': 'https://api.grass.io/retrieveUser',
            'sendEmailVerification': 'https://api.grass.io/sendEmailVerification',
            'confirmEmail': 'https://api.grass.io/confirmEmail', 
            'verifySignedMessage': 'https://api.grass.io/verifySignedMessage',
            'sendWalletAddressEmailVerification': 'https://api.grass.io/sendWalletAddressEmailVerification',
            'confirmWalletAddress': 'https://api.grass.io/confirmWalletAddress',
            'sendOtp': 'https://api.grass.io/sendOtp',
            'verifyOtp': 'https://api.grass.io/verifyOtp',
            'setPassword': 'https://api.grass.io/setPassword',
            'resetPassword': 'https://api.grass.io/resetPassword',
            'claimReward': 'https://api.grass.io/claimReward'
        }
        self.user_agent = user_agent
        self.proxy = proxy
        self.sec_ch_ua = '"Google Chrome";v="136", "Chromium";v="136", "Not.A/Brand";v="99"'


        self.headers_registration = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'text/plain;charset=UTF-8',
            'Origin': 'https://app.grass.io',
            'Priority': 'u=1, i',
            'Referer': 'https://app.grass.io/',
            'Sec-Ch-Ua': self.sec_ch_ua,
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.user_agent,
        }

        self.headers_retrive_user = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-language': 'en-US,en;q=0.9',
            'Authorization': None,
            'Origin': 'https://app.grass.io',
            'Priority': 'u=1, i',
            'Referer': 'https://app.grass.io/',
            'Sec-Ch-Ua': self.sec_ch_ua, 
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.user_agent,
        }

        self.options_headers = [
            ('Accept','*/*'),
            ('Accept-language','en-US,en;q=0.9'),
            ('Access-Control-Request-','authorization'),
            ('Headers',''),
            ('Access-Control-Request-','POST'),
            ('Method',''),
            ('Origin','https://app.grass.io/'),
            ('Priority','u=1, i'),
            ('Referer','https://app.grass.io/'),
            ('Sec-Fetch-Dest','empty'),
            ('Sec-Fetch-Mode','cors'),
            ('Sec-Fetch-Site','same-site'),
            ('User-Agent', self.user_agent)
        ]

    async def get_ua_version(self):
        ls = self.user_agent.split()
        for i in ls:
            if 'Chrome/' in i:
                v = i.lstrip('Chrome/')
                v = v.split('.')[0]
                return v
        raise ValueError('Не определена версия user-agent')

    async def update_headers(self):
        ver = await self.get_ua_version()
        self.headers_registration['Sec-Ch-Ua'] = f'"Google Chrome";v="{ver}", "Not.A/Brand";v="99", "Chromium";v="{ver}"'
        self.headers_retrive_user['Sec-Ch-Ua'] = f'"Google Chrome";v="{ver}", "Not.A/Brand";v="99", "Chromium";v="{ver}"'

    async def open_session(self):
        if self.session.closed:
            self.session = ClientSession(trust_env=True, connector=TCPConnector(ssl=False))

