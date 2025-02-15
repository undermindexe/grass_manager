import asyncio
import json
import random
from datetime import datetime, timezone
from logger import logger

from data.account import Account
from data.proxy import ProxyManager
from data.db import DataBase
from data.wallet import Wallet
from data.browser import Browser
from data.captcha import CaptchaService
from data.imap import search_mail

from data.service import *
from data.exception import *
from data.arg import get_args, update_args
from data.import_export import import_acc, export_acc

from aiosqlite import Error as DatabaseError
from tenacity import retry, stop_after_attempt, wait_random, retry_if_exception_type, RetryError

from data.ui import MyInterface

args = get_args()
semaphore = asyncio.Semaphore(args.threads)


class Grass(Browser, Account, Wallet):
    def __init__(self, email: str = None, 
                 username: str = None, 
                 password: str = None, 
                 email_password: str = None, 
                 imap_domain: str = None, 
                 proxymanager: ProxyManager = None,
                 ref_reg: str = None
                 ):
        Browser.__init__(self, user_agent = get_user_agent())
        Account.__init__(self, ref_reg = ref_reg)
        Wallet.__init__(self)
        self.db = DataBase('database.db')
        self.email = email
        self.username = username
        self.password = password
        self.email_password = email_password
        self.imap_domain = imap_domain
        self.proxymanager = proxymanager
        self.proxy = 'https://proxy'
        self.error = 0

    @retry(
            stop = stop_after_attempt(6),
            retry = (retry_if_exception_type(RegistrationError)),
            wait = wait_random(5,7)
    )
    async def register(self):
        try:
            await self.open_session()
            logger.info(f'{self.email} | Start create account. Password: {self.password}, Proxy: {self.proxy.link}')
            captcha = CaptchaService(args.captcha_service, args.captcha_key)
            json_data = {
                "email": self.email,
                "password": self.password,
                "role": "USER",
                "referralCode":self.ref_reg,
                "username": self.username,
                "marketingEmailConsent": random.choice([True, False]),
                "recaptchaToken": await captcha.get_captcha_token_async(),
                "listIds": [
                    15,
                ],
            }
            async with self.session.post(url = self.url['register'], headers= self.headers_registration, data = json.dumps(json_data), proxy = f"http://{self.proxy.link}") as response:
                if response.status == 200:
                    logger.info(f'{self.email} | Account has been created')
                    return True
                else:
                    logger.info(f'{self.email} | Account not created | Status: {response.status}')
                    raise RegistrationError()
        except RetryError:
            logger.error(f'{self.email} | Registration | Retry Error')
            return False
        except Exception as e:
            if not self.session.closed:
                await self.session.close()
            logger.error(f'{self.email} | Error registration | {e}')
            self.error += 1
            if self.error > 2:
                self.proxy = await self.swap_proxy()
                self.error = 0
            raise RegistrationError()
        finally:
            await self.session.close()

    @retry(
            stop = stop_after_attempt(5),
            retry = (retry_if_exception_type(LoginError)),
            wait = wait_random(5,7)
    )
    async def login(self):
        try:
            logger.debug(f'{self.email} | Start Login')
            await self.open_session()
            json_data = {
                    'password': self.password,
                    'username': self.email
            }
            async with self.session.post(url = self.url['login'], headers= self.headers_registration, data = json.dumps(json_data), proxy = f"http://{self.proxy.link}") as response:
                if response.status == 200:
                    logger.info(f'{self.email} | Account login...')
                    login_response = await response.json()
                    self.access_token = login_response['result']['data']['accessToken']
                    self.access_token_create_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                    self.refresh_token = login_response['result']['data']['refreshToken']
                    self.userid = login_response['result']['data']['userId']
                    self.userrole = login_response['result']['data']['userRole']
                    self.headers_retrive_user['Authorization'] = self.access_token
                    await self.update_headers()
                    if await self.save_session():
                        return True
                else:
                    raise LoginError('Login error')
        except Exception as e:
            if not self.session.closed:
                await self.session.close()
            logger.error(f'{self.email} | Error login | {e}')
            self.error += 1
            if self.error > 3:
                self.proxy = await self.swap_proxy()
                logger.info(f'{self.email} | New proxy: {self.proxy.link}') 
                self.error = 0
            raise LoginError('Login error')
        finally:
            await self.session.close()

    @retry(
            stop = stop_after_attempt(5),
            retry = (retry_if_exception_type(DatabaseError)),
            wait = wait_random(5,15)
    )
    async def save_session(self):
        try:
            db = await self.db.connect()
            await db.execute('''
            UPDATE Accounts 
            SET access_token = ?, access_token_create_time = ?, refresh_token = ?, user_agent = ?,
            userid = ?, userrole = ?
            WHERE email = ?
            ''', (self.access_token, self.access_token_create_time, self.refresh_token, self.user_agent, self.userid, self.userrole, self.email))
            await db.commit()
            logger.info(f'{self.email} | Session has been saved in database')
            return True
        except DatabaseError as e:
            logger.error(f'{self.email} | Database Error')
            raise e
        finally:
            await self.db.close()

    @retry(
            stop = stop_after_attempt(15),
            retry = (retry_if_exception_type(UpdateError)),
            wait = wait_random(5,7)
    )
    async def update_info(self):
        try:
            await self.open_session()
            async with self.session.get(url = self.url['retrieveUser'], headers= self.headers_retrive_user, proxy = f"http://{self.proxy.link}") as response:
                if response.status == 200:
                    retrieveUser = await response.json()
                    self.referal_code = retrieveUser['result']['data']['referralCode']
                    self.entity = retrieveUser['result']['data']['entity']
                    self.created = retrieveUser['result']['data']['created']
                    self.verified = retrieveUser['result']['data']['isVerified']
                    self.wallet_verified = retrieveUser['result']['data']['isWalletAddressVerified']
                    self.reward_claimed = retrieveUser['result']['data']['lastRewardClaimed']
                    self.modified = retrieveUser['result']['data']['modified']
                    self.refferals = retrieveUser['result']['data']['referralCount']
                    self.qualified_refferals = retrieveUser['result']['data']['qualifiedReferrals']
                    self.userid = retrieveUser['result']['data']['userId']
                    self.userrole = retrieveUser['result']['data']['userRole']
                    self.totalpoints = retrieveUser['result']['data']['totalPoints']
                    self.parent_referrals = ','.join(retrieveUser['result']['data']['parentReferrals'])

                    await self.save_info()
                    return True
                else:
                    logger.error(f'{self.email} | Update_info: {response.status}')
                    return False
        except Exception as e:
            if not self.session.closed:
                await self.session.close()
            logger.error(f'{self.email} | Error update info | {e}')
            self.error += 1
            if self.error > 3:
                self.proxy = await self.swap_proxy()
                self.error = 0
            raise UpdateError('Update info error')
        finally:
            await self.session.close()

    async def save_wallet(self):
        try:
            db = await self.db.connect()
            await db.execute('''
            UPDATE Accounts 
            SET wallet = ?, private_key = ?, seed = ?
            WHERE email = ?
            ''', (self.wallet, self.private_key, self.seed, self.email))
            await db.commit()
            logger.info(f'{self.email} | Account wallet has been saved in database')
            return True
        finally:
            await self.db.close()  

    async def save_info(self):
        try:
            db = await self.db.connect()
            await db.execute('''
            UPDATE Accounts 
            SET referal_code = ?, entity = ?, created = ?, verified = ?, wallet_verified = ?, reward_claimed = ?,
            modified = ?, refferals = ?, qualified_refferals = ?, userid = ?, userrole = ?, totalpoints = ?, parent_referrals = ?,
            wallet = ?, private_key = ?, seed = ?
            WHERE email = ?
            ''', (self.referal_code, self.entity, self.created, self.verified, self.wallet_verified, self.reward_claimed,
                  self.modified, self.refferals, self.qualified_refferals, self.userid, self.userrole, self.totalpoints, self.parent_referrals,
                  self.wallet, self.private_key, self.seed,
                  self.email))
            await db.commit()
            logger.info(f'{self.email} | Info account has been saved in database')
            return True
        finally:
            await self.db.close()
            if not self.session.closed:
                await self.session.close()

    async def save_account(self):
        try:
            db = await self.db.connect()
            logger.debug(f'{self.email} | Save in db')
            await db.execute('''
            INSERT INTO Accounts (email, password, ref_reg, username) VALUES (?, ?, ?, ?)
            ''', (self.email, self.password, self.ref_reg, self.username))
            if self.email_password:
                await db.execute('''
                UPDATE Accounts SET email_password = ? WHERE email = ?
                ''', (self.email_password, self.email))
            if self.imap_domain:
                await db.execute('''
                UPDATE Accounts SET imap_domain = ? WHERE email = ?
                ''', (self.imap_domain, self.email))
            await db.commit()
            logger.info(f'{self.email} | Account has been saved in database')
        finally:
            await self.db.close()
            if not self.session.closed:
                await self.session.close()

    async def validate_session(self):
        try:
            db = await self.db.connect()
            self.cursor = await db.execute('SELECT access_token, access_token_create_time, user_agent, password\
                                            FROM Accounts WHERE email = ?', (self.email,))
            row = await self.cursor.fetchone()
            if not (bool(row[0]) and bool(row[1])):
                logger.info(f'{self.email} | No active session. Login...')
                self.password = row[3]
                if await self.login():
                    return True
            else:
                logger.info(f'{self.email} | An active session is in use')
                self.access_token = row[0]
                self.user_agent = row[2]
                self.password = row[3]
                self.headers_retrive_user['Authorization'] = self.access_token
                await self.update_headers()
                return True
        finally:
            await self.db.close()

    async def error_stat(self):
        self.error += 1
        if self.error > 3:
            self.proxy = await self.swap_proxy()
            self.error = 0

    @retry(
            stop = stop_after_attempt(5),
            retry = (retry_if_exception_type(VarificationError)),
            wait = wait_random(5,7)
    )
    async def send_email_verification(self):
        try:
            await self.open_session()
            logger.info(f'{self.email} | Start email verification')
            response = await self.session.post(url=self.url['sendEmailVerification'], headers= self.headers_retrive_user, proxy = f"http://{self.proxy.link}")
            if response.status == 200:
                logger.info(f'{self.email} | Sent verification message: {response.status}')
                await asyncio.sleep(15)
                return True
            else:
                logger.error(f'{self.email} | Error send mail: {response.status}')
                raise VarificationError
        except Exception as e:
            if not self.session.closed:
                await self.session.close()
            logger.error(f'{self.email} | Error send email verification {e}')
            await self.error_stat()
            raise VarificationError()
        finally:
            await self.session.close()

    @retry(
            stop = stop_after_attempt(5),
            retry = (retry_if_exception_type(VarificationError)),
            wait = wait_random(5,7)
    )
    async def click_email_verification(self, token):
        try:
            await self.open_session()
            logger.info(f'{self.email} | Attempt verified email')
            self.headers_retrive_user['Authorization'] = token
            response = await self.session.post(url=self.url['confirmEmail'], headers= self.headers_retrive_user, proxy = f"http://{self.proxy.link}")
            if response.status == 200:
                logger.info(f'{self.email} | Success response from verification email: {response.status}')
                return True
            else:
                logger.error(f'{self.email} | Error response from verification email: {response.status}')
                raise VarificationError
        except Exception as e:
            if not self.session.closed:
                await self.session.close()
            logger.error(f'{self.email} | Error verification {e}')
            await self.error_stat()
            raise VarificationError()
        finally:
            await self.session.close()

    @retry(
            stop = stop_after_attempt(5),
            retry = (retry_if_exception_type(VarificationError)),
            wait = wait_random(5,7)
    )
    async def click_wallet_verification(self, token):
        try:
            await self.open_session()
            logger.info(f'{self.email} | Attempt verified wallet')
            response = await self.session.options(url=self.url['confirmWalletAddress'], headers= self.options_headers, proxy = f"http://{self.proxy.link}")
            if response.status == 204:
                self.headers_retrive_user['Authorization'] = token
                response = await self.session.post(url=self.url['confirmWalletAddress'], headers= self.headers_retrive_user, proxy = f"http://{self.proxy.link}")
                if response.status == 200:
                    logger.info(f'{self.email} | Success response from verification wallet: {response.status}')
                    return True
                else:
                    logger.error(f'{self.email} | Error response from verification wallet: {response.status}')
                    raise VarificationError
        except Exception as e:
            if not self.session.closed:
                await self.session.close()
            logger.error(f'{self.email} | Error verification {e}')
            await self.error_stat()
            raise VarificationError()
        finally:
            await self.session.close()

    @retry(
            stop = stop_after_attempt(5),
            retry = (retry_if_exception_type(ConnectWallet)),
            wait = wait_random(5,7)
    )
    async def verifySignedMessage(self, sign, timestamp):
        try:
            await self.open_session()
            logger.info(f'{self.email} | Connect wallet')
            self.headers_retrive_user['Authorization'] = self.access_token
            json_data = {
                'signedMessage': sign,
                'publicKey': self.public_key,
                'walletAddress': self.wallet,
                'timestamp': timestamp,
                'isLedger': False,
                'isAfterCountdown': True
            }
            response = await self.session.post(url=self.url['verifySignedMessage'], headers= self.headers_retrive_user, proxy = f"http://{self.proxy.link}", json=json_data)
            if response.status == 200:
                logger.info(f'{self.email} | Success connect wallet: {self.wallet}')
                return True
            else:
                logger.error(f'{self.email} | Error connect wallet. Status: {response.status}')
                raise ConnectWallet()
        except Exception as e:
            if not self.session.closed:
                await self.session.close()
            logger.error(f'{self.email} | Error connect wallet {e}')
            await self.error_stat()
            raise ConnectWallet()
        finally:
            await self.session.close()


    @retry(
            stop = stop_after_attempt(5),
            retry = (retry_if_exception_type(ConnectWallet)),
            wait = wait_random(5,7)
    )
    async def send_wallet_verification(self):
        try:
            await self.open_session()
            logger.info(f'{self.email} | Attempt send email verification wallet')
            self.headers_retrive_user['Authorization'] = self.access_token
            response = await self.session.options(url=self.url['sendWalletAddressEmailVerification'], headers= self.options_headers, proxy = f"http://{self.proxy.link}")
            if response.status == 204:
                logger.info(f'{self.email} | Success OPTIONS request: {response.status}')
                response = await self.session.post(url=self.url['sendWalletAddressEmailVerification'], headers= self.headers_retrive_user, proxy = f"http://{self.proxy.link}")
                if response.status == 200:
                    logger.info(f'{self.email} | Send wallet verification email: {response.status}')
                    await asyncio.sleep(15)
                else:
                    logger.error(f'{self.email} | Send wallet verification email: {response.status}')
                    raise ConnectWallet
                return True
            else:
                logger.error(f'{self.email} | Error Options: {response.status}')
                raise ConnectWallet
        except Exception as e:
            if not self.session.closed:
                await self.session.close()
            logger.error(f'{self.email} | Error: {e}')
            await self.error_stat()
            raise ConnectWallet()
        finally:
            await self.session.close()


    async def get_email(self, request): 
        email = await asyncio.to_thread(search_mail, request=request, email=self.email, password=self.email_password, imap_server=self.imap_domain, proxy=self.proxy.link, imap_proxy = args.imap_proxy)
        return email

    async def email_verification(self, subject):
        try:
            if subject == '"Verify Your Email for Grass"':
                await self.send_email_verification()
                email = await self.get_email(f'FROM "no-reply@grassfoundation.io" SUBJECT {subject}')
                token = email.split('token=')[1].split('/')[0]
                logger.debug(f'{self.email} | Token verified email: {token}')
                if await self.click_email_verification(token):
                    self.verified = True
                    return True
                else:
                    return False
            elif subject == '"Verify Your Wallet Address for Grass"':
                email = await self.get_email(f'FROM "no-reply@grassfoundation.io" SUBJECT {subject}')
                token = email.split('token=')[1].split('/')[0]
                logger.debug(f'{self.email} | Token verified wallet: {token}')
                return token


        except Exception as e:
            logger.error(f'{self.email} | Error verification {e}')
            raise e

    async def get_proxy(self):  # Обернуть get в логику get proxy
        while True:
            proxy = await self.proxymanager.get()
            if proxy.link != 'not_available_proxy:1111':
                self.proxy = proxy
                break
            else:
                logger.info(f'{self.email} | No available proxies. Sleep 20 second')
                await asyncio.sleep(20)

    async def swap_proxy(self):
        self.proxy.status = False
        self.proxy.last_touch = datetime.now()
        return await self.get_proxy()

    async def wallet_verification(self):
        try:
            logger.info(f'{self.email} | Start wallet verification')
            if self.wallet_verified == True:
                logger.info(f'{self.email} | Wallet already linked and verified')
            elif self.wallet_verified == False:
                if self.seed != None:
                    #sign, timestamp = self.gen_wallet(self.seed)
                    await self.send_wallet_verification()
                    token = await self.email_verification(subject='"Verify Your Wallet Address for Grass"')
                    await self.click_wallet_verification(token)
                else:
                    sign, timestamp = self.gen_wallet()
                    if await self.verifySignedMessage(sign, timestamp):
                        await self.save_wallet()
                        await self.send_wallet_verification()
                        token = await self.email_verification(subject='"Verify Your Wallet Address for Grass"')
                        await self.click_wallet_verification(token)
        except Exception as e:
            logger.error(f'{self.email} | Error verification {e}')
            raise e

def get_accounts(reflist: list, proxy: ProxyManager, accounts: str = 'accounts.txt'):
    list_accounts = []
    with open(accounts, 'r', encoding= 'utf-8') as file:
        for string in file.readlines():
            string = string.strip()
            if ':' in string:
                string = tuple(string.split(':'))
                if validate_email(string[0]) and len(string) == 2:
                    account = Grass(email = string[0], password = generate_pass(), email_password=string[1], username = get_nickname(), ref_reg = random.choice(reflist), proxymanager=proxy)  # email:email_pass
                    logger.info(f'Select mode email:email_pass | {string}')
                    list_accounts.append(account)
                elif validate_email(string[0]) and len(string) == 3:
                    account = Grass(email = string[0], password = generate_pass(), email_password=string[1], imap_domain=string[2], username = get_nickname(), ref_reg = random.choice(reflist), proxymanager=proxy)  # email:email_pass:imap_domain
                    logger.info(f'Select mode email:email_pass:imap_domain | {string}')
                    list_accounts.append(account)
                else:
                    logger.error(f'Error parsing account | {string}')
            else:
                if validate_email(string):
                    password = generate_pass()
                    logger.info(f'Select mode no email_pass | {string} {password}')
                    list_accounts.append(Grass(email = string, password = password, username = get_nickname(), ref_reg = random.choice(reflist), proxymanager=proxy))
                else:
                    logger.error(f'Error parsing account | {string}')
    return list_accounts

async def import_acc_from_db(proxy: ProxyManager):
    accounts = []
    database = DataBase('database.db')
    db = await database.connect()
    logger.info(f'Import account from db')
    db.row_factory = database._row
    cursor = await db.execute('SELECT * FROM Accounts')
    rows = await cursor.fetchall()
    result = [dict(row) for row in rows]
    for i in result:
        acc = Grass(proxymanager=proxy)
        acc.__dict__.update(i)
        if acc.user_agent == None:
            acc.user_agent = get_user_agent()
        accounts.append(acc)
        logger.info(f'{acc.email} | Get in DB')
    return accounts

async def search_acc_db(account: Grass):
    database = DataBase('database.db')
    db = await database.connect()
    logger.info(f'{account.email} | Search in db')
    db.row_factory = database._row
    cursor = await db.execute('SELECT * FROM Accounts WHERE email = ?', (account.email,))
    result = await cursor.fetchone()
    if result:
        account.__dict__.update(result)
        logger.info(f'{account.email} | Account was found in db | Password: {account.password}')
        await database.close()
        return True
    else:
        await database.close()
        return False

async def worker_reg(account: Grass):
    try:
        async with semaphore:
            if await search_acc_db(account):
                logger.info(f'{account.email} | Account in the database | SKIP')
            else:
                await account.get_proxy()
                logger.info(f'{account.email} | Proxy: {account.proxy.link} Password: {account.password}')
                if await account.register():
                    await account.save_account()
                    if await account.validate_session():
                        await account.update_info()
                else:
                    logger.error(f'{account.email} | Account maybe registered')
                await account.proxymanager.drop(account.proxy)
            if not account.session.closed:
                await account.session.close()  
    except RetryError:
        logger.error(f'{account.email} | Registration | Retry Error')
    finally:
        await account.db.close()
        if not account.session.closed:
            await account.session.close()
            
async def worker_update(account: Grass):
    try:
        async with semaphore:
            await account.get_proxy()
            logger.info(f'{account.email} | Proxy: {account.proxy.link} Password: {account.password}')
            if await account.validate_session():
                await account.update_info()
            await account.proxymanager.drop(account.proxy)
    except RetryError:
        logger.error(f'{account.email} | Update | Retry Error')
    finally:
        await account.db.close()
        if not account.session.closed:
            await account.session.close()

async def worker_verif(account: Grass):
    try:
        async with semaphore:
            await account.get_proxy()
            logger.info(f'{account.email} | Proxy: {account.proxy.link} Password: {account.password}')
            if await account.validate_session():
                await account.update_info()
                if account.verified == False:
                    await account.email_verification(subject='"Verify Your Email for Grass"')
                if account.verified == True and account.wallet_verified == False:
                    await account.wallet_verification()
                await account.update_info()
            await account.proxymanager.drop(account.proxy)
    except RetryError:
        logger.error(f'{account.email} | Verification | Retry Error')
    finally:
        await account.db.close()
        if not account.session.closed:
            await account.session.close()

async def worker_import(account: Grass):
    try:
        async with semaphore:
            if await search_acc_db(account):
                return
            await account.save_account()
            await account.save_info()
            await account.save_session()
    except Exception as e:
        logger.error(f'{account.email} {e}')
        raise e


async def ui():
    app = MyInterface()
    new_args = await app.run_async()
    print(new_args)
    return new_args

async def main(new_args = None):
    try:
        if new_args:
            logger.debug(f'{new_args}')
            global args, semaphore
            args = update_args(args, new_args)
            semaphore = asyncio.Semaphore(args.threads)

        if args.action in ['registration', 'update', 'verification']:
            get_user_agent()

        if args.action == 'registration':
            proxy = ProxyManager(get_proxies(args.proxy), args.rotate)
            reflist = get_ref(args.ref)
            #generate_random_email(50, args.accounts) #DEBUG create accs
            accounts = get_accounts(reflist, proxy, accounts = args.accounts)
            tasks = [worker_reg(a) for a in accounts]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f'END Registration')

        elif args.action == 'imap':
            await add_email_pass(DataBase(), args.imap , args.accounts)

        elif args.action == 'import':
            list_dicts = await import_acc(file_name = args.file_name, separator = args.separator, form = args.format)
            list_accs = [Grass() for _ in list_dicts]
            for num, acc in enumerate(list_accs):
                acc.__dict__.update(list_dicts[num])
            tasks = [worker_import(acc) for acc in list_accs]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f'END import accounts')

        elif args.action == 'export':
            await export_acc(DataBase, file_name = args.file_name, export_type=args.export_type, separator = args.separator, form = args.format)
            logger.info(f'END export accounts')

        elif args.action == 'update':
            proxy = ProxyManager(get_proxies(args.proxy), args.rotate)
            accounts = await import_acc_from_db(proxy)
            tasks = [worker_update(a) for a in accounts]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f'END update info')

        elif args.action == 'verification':
            proxy = ProxyManager(get_proxies(args.proxy), args.rotate)
            accounts = await import_acc_from_db(proxy)
            tasks = [worker_verif(a) for a in accounts]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f'END Verification')
        else:
            logger.error(f'Incorrect --action argument')  


    except Exception as e:
        print(e)

if __name__ =='__main__':
    try:
        print('Grass Faker Autoreger v1.0')
        if args.action == None:
            new_args = asyncio.run(ui())
            asyncio.run(main(new_args))
            raise SystemExit
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Forces Stop')
    except Exception as e:
        print(e)
