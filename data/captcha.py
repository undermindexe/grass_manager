import asyncio
import captchatools


CAPTCHA_PARAMS = {
    "captcha_type": "v2",
    "invisible_captcha": False,
    "sitekey": "6LeeT-0pAAAAAFJ5JnCpNcbYCBcAerNHlkK4nm6y",
    "captcha_url": "https://app.grass.io"
}


class CaptchaService:
    def __init__(self, service: str, api_key: str):
        self.service = self._validate_service(service)
        self.api_key = self._validate_api_key(api_key)

    def _validate_service(self, service):
        if not isinstance(service, str):
            raise TypeError('Setup not valid type data in service name')
        if not service in ['capmonster', 'anticaptcha', '2captcha', 'capsolver', 'captchaai']:
            raise ValueError('Unknown captcha service')
        return service
    
    def _validate_api_key(self, api_key):
        if not isinstance(api_key, str):
            raise TypeError('Setup not valid type data in captcha api key')
        if not api_key:
            raise ValueError('Captcha api key is missing')
        return api_key

    def get_captcha_token(self):
        solver = captchatools.new_harvester(solving_site = self.service, api_key = self.api_key, **CAPTCHA_PARAMS)
        return solver.get_token()
        
    async def get_captcha_token_async(self):
        return await asyncio.to_thread(self.get_captcha_token)
