import asyncio
import json
import random
import warnings

from datetime import datetime, timezone

from data.account import Account
from data.proxy import ProxyManager
from data.db import DataBase
from data.wallet import Wallet
from data.browser import Browser
from data.captcha import CaptchaService
from data.imap_repository import IMAPRepository
from data.custom_logger import logger

from data.service import *
from data.exception import *
from data.arg import get_args, update_args
from data.import_export import import_acc, export_acc

from aiosqlite import Error as DatabaseError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random,
    retry_if_exception_type,
    RetryError,
)

from data.ui import run_ui

from curl_cffi import AsyncSession

args = get_args()
semaphore = asyncio.Semaphore(args.threads)

warnings.filterwarnings("ignore", category=ResourceWarning)


class Grass(Browser, Account, Wallet):
    def __init__(
        self,
        email: str = None,
        forward_email: str = None,
        password: str = None,
        email_password: str = None,
        imap_domain: str = None,
        proxymanager: ProxyManager = None,
        ref_reg: str = None,
    ):
        Browser.__init__(self, user_agent=get_user_agent())
        Account.__init__(self, ref_reg=ref_reg)
        Wallet.__init__(self)
        self.email = email
        self.password = password
        self.forward_email = forward_email
        self.email_password = email_password
        self.imap_domain = imap_domain
        self.proxymanager = proxymanager
        self.proxy = "https://proxy"
        self.error = 0

    @retry(
        stop=stop_after_attempt(3),
        retry=(retry_if_exception_type(RegistrationError)),
        wait=wait_random(5, 7),
    )
    async def send_otp(self, action: str):
        try:
            await self.update_headers()

            logger.info(
                f"{self.email} | Send OTP {action} mail\nPassword: {self.password}\nProxy: {self.proxy.link}\nRef_code: {self.ref_reg if self.ref_reg else None}\n"
            )

            logger.info(f"{self.email} | ⏳ Solve captcha")
            captcha = CaptchaService(
                proxy=self.proxy, cookies=self.cookies, storage_state=self.storage_state
            )
            cloudflare = await captcha.solve_turnstile()

            self.cookies = cloudflare["cookies"]
            self.user_agent = cloudflare["user_agent"]
            self.captcha_token = cloudflare["token"]
            self.storage_state = cloudflare["storage_state"]

            await self.update_headers()

            json_data = self.build_json_data(action=action, token=self.captcha_token)

            async with AsyncSession() as s:
                response = await s.post(
                    url=self.url["sendOtp"],
                    headers=self.headers_registration,
                    data=json.dumps(json_data),
                    cookies=self.get_cookies(),
                    proxy=f"http://{self.proxy.link}",
                    impersonate="chrome",
                )

                status = response.status_code
                if status == 200:
                    logger.info(
                        f"{self.email} | Success send OTP massage for {self.email}"
                    )
                    await asyncio.sleep(20)
                    return True
                if status == 429:
                    logger.info(
                        f"{self.email} | Too Many Requests SendOTP {self.email}"
                    )
                    return False
                else:
                    logger.info(
                        f"{self.email} | Error send OTP massage for {self.email} | Status: {status}"
                    )
                    raise RegistrationError()

        except RetryError:
            logger.error(f"{self.email} | Send OTP | Retry Error")
            return False

        except Exception as e:
            logger.error(f"{self.email} | Unexpected error: {e}")
            self.error += 1
            if self.error > 2:
                await self.swap_proxy()
                self.error = 0
            raise RegistrationError()

    @retry(
        stop=stop_after_attempt(5),
        retry=(retry_if_exception_type(LoginError)),
        wait=wait_random(5, 7),
    )
    async def login(self):
        try:
            logger.debug(f"{self.email} | Account login...")
            await self.update_headers()
            logger.info(f"{self.email} | ⏳ Solve captcha")
            captcha = CaptchaService(
                proxy=self.proxy, cookies=self.cookies, storage_state=self.storage_state
            )
            cloudflare = await captcha.solve_turnstile()

            self.cookies = cloudflare["cookies"]
            self.user_agent = cloudflare["user_agent"]
            self.captcha_token = cloudflare["token"]
            self.storage_state = cloudflare["storage_state"]

            json_data = {
                "username": self.email,
                "password": self.password,
                "recaptchaToken": self.captcha_token,
            }

            async with AsyncSession() as s:
                response = await s.post(
                    url=self.url["login"],
                    headers=self.headers_registration,
                    data=json.dumps(json_data),
                    cookies=self.get_cookies(),
                    proxy=f"http://{self.proxy.link}",
                    impersonate="chrome",
                )
                status = response.status_code
                if status == 200:
                    logger.info(f"{self.email} | Login Success")
                    login_response = response.json()
                    self.access_token = login_response["result"]["data"]["accessToken"]
                    self.access_token_create_time = (
                        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                        + "Z"
                    )
                    self.refresh_token = login_response["result"]["data"][
                        "refreshToken"
                    ]
                    self.userid = login_response["result"]["data"]["userId"]
                    self.userrole = login_response["result"]["data"]["userRole"]
                    self.headers_retrive_user["Authorization"] = self.access_token
                    if await self.save_session():
                        return True
                else:
                    logger.error(f"{self.email} | {response.text}")
                    raise LoginError()
        except Exception as e:
            logger.error(f"{self.email} | Error login | {e}")
            self.error += 1
            if self.error > 3:
                await self.swap_proxy()
                logger.info(f"{self.email} | New proxy: {self.proxy.link}")
                self.error = 0
            raise LoginError("Login error")

    @retry(
        stop=stop_after_attempt(5),
        retry=(retry_if_exception_type(LoginError)),
        wait=wait_random(5, 7),
    )
    async def verify_otp(self, otp_code):
        try:
            logger.debug(f"{self.email} | Verify OTP Code...")
            await self.update_headers()

            json_data = {"email": self.email, "otp": otp_code}
            async with AsyncSession() as s:
                response = await s.post(
                    url=self.url["verifyOtp"],
                    headers=self.headers_registration,
                    data=json.dumps(json_data),
                    proxy=f"http://{self.proxy.link}",
                    impersonate="chrome",
                )
                status = response.status_code
                if status == 200:
                    logger.info(f"{self.email} | Success Verify OTP Code")
                    login_response = response.json()
                    self.access_token = login_response["result"]["data"]["accessToken"]
                    self.access_token_create_time = (
                        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                        + "Z"
                    )
                    self.refresh_token = login_response["result"]["data"][
                        "refreshToken"
                    ]
                    self.userid = login_response["result"]["data"]["userId"]
                    self.userrole = login_response["result"]["data"]["userRole"]
                    self.headers_retrive_user["Authorization"] = self.access_token
                    await self.save_session()
                    return True
                else:
                    raise LoginError()
        except Exception as e:
            logger.error(f"{self.email} | Error Verify OTP | {e}")
            self.error += 1
            if self.error > 3:
                await self.swap_proxy()
                logger.info(f"{self.email} | New proxy: {self.proxy.link}")
                self.error = 0
            raise LoginError("Verify OTP error")

    @retry(
        stop=stop_after_attempt(5),
        retry=(retry_if_exception_type(LoginError)),
        wait=wait_random(5, 7),
    )
    async def set_password(self):
        try:
            logger.debug(f"{self.email} | Send setup password link")
            await self.update_headers()
            self.headers_retrive_user["Authorization"] = self.access_token
            logger.info(f"{self.email} | ⏳ Solve captcha")
            captcha = CaptchaService(
                proxy=self.proxy, cookies=self.cookies, storage_state=self.storage_state
            )
            cloudflare = await captcha.solve_turnstile()

            self.cookies = cloudflare["cookies"]
            self.user_agent = cloudflare["user_agent"]
            self.captcha_token = cloudflare["token"]
            self.storage_state = cloudflare["storage_state"]

            json_data = {"email": self.email, "recaptchaToken": self.captcha_token}

            async with AsyncSession() as s:
                response = await s.post(
                    url=self.url["setPassword"],
                    headers=self.headers_retrive_user,
                    data=json.dumps(json_data),
                    cookies=self.get_cookies(),
                    proxy=f"http://{self.proxy.link}",
                    impersonate="chrome",
                )

                status = response.status_code
                if status == 200:
                    logger.info(
                        f"{self.email} | Success send setup password link for email"
                    )
                    await asyncio.sleep(20)
                    return True
                else:
                    raise LoginError("Send setup password link error")

        except Exception as e:
            logger.error(f"{self.email} | Setup password link error | {e}")
            self.error += 1
            if self.error > 3:
                await self.swap_proxy()
                logger.info(f"{self.email} | New proxy: {self.proxy.link}")
                self.error = 0
            raise LoginError("Setup password link error")

    @retry(
        stop=stop_after_attempt(5),
        retry=(retry_if_exception_type(DatabaseError)),
        wait=wait_random(5, 15),
    )
    async def save_session(self):
        await DataBase.execute(
            """
        UPDATE Accounts
        SET access_token = ?, access_token_create_time = ?, refresh_token = ?, user_agent = ?,
        userid = ?, userrole = ?
        WHERE email = ?
        """,
            (
                self.access_token,
                self.access_token_create_time,
                self.refresh_token,
                self.user_agent,
                self.userid,
                self.userrole,
                self.email,
            ),
        )

        if self.cookies:
            cookies = json.dumps(self.cookies)
            await DataBase.execute(
                """
                UPDATE Accounts
                SET cookies = ?
                WHERE email = ?
                """,
                (cookies, self.email),
            )

        if self.storage_state:
            storage_state = json.dumps(self.storage_state)
            await DataBase.execute(
                """
                UPDATE Accounts
                SET storage_state = ?
                WHERE email = ?            
                """,
                (storage_state, self.email),
            )
        logger.info(f"{self.email} | Session has been saved in database")
        return True

    @retry(
        stop=stop_after_attempt(6),
        retry=(retry_if_exception_type(UpdateError)),
        wait=wait_random(5, 7),
    )
    async def update_info(self) -> bool:
        try:
            logger.info(f"{self.email} | Start update info")
            await self.update_headers()

            if self.headers_retrive_user["Authorization"] == None:
                logger.error(
                    f"{self.email} | Error update account info. Enought Authorization token"
                )
                return False

            async with AsyncSession() as s:
                response = await s.get(
                    url=self.url["retrieveUser"],
                    headers=self.headers_retrive_user,
                    proxy=f"http://{self.proxy.link}",
                    impersonate="chrome",
                )

                status = response.status_code
                if status == 200:
                    retrieveUser = response.json()
                    self.referal_code = retrieveUser["result"]["data"]["referralCode"]
                    self.entity = retrieveUser["result"]["data"]["entity"]
                    self.username = retrieveUser["result"]["data"]["username"]
                    self.created = retrieveUser["result"]["data"]["created"]
                    self.verified = retrieveUser["result"]["data"]["isVerified"]
                    self.wallet_verified = retrieveUser["result"]["data"][
                        "isWalletAddressVerified"
                    ]
                    self.reward_claimed = retrieveUser["result"]["data"][
                        "lastRewardClaimed"
                    ]
                    self.modified = retrieveUser["result"]["data"]["modified"]
                    self.refferals = retrieveUser["result"]["data"]["referralCount"]
                    self.qualified_refferals = retrieveUser["result"]["data"][
                        "qualifiedReferrals"
                    ]
                    self.userid = retrieveUser["result"]["data"]["userId"]
                    self.userrole = retrieveUser["result"]["data"]["userRole"]
                    self.totalpoints = retrieveUser["result"]["data"]["totalPoints"]
                    self.parent_referrals = ",".join(
                        retrieveUser["result"]["data"]["parentReferrals"]
                    )
                    logger.info(f"{self.email} | Success get user info")
                    await self.reward_claim()
                    await self.save_info()
                    return True
                else:
                    logger.error(f"{self.email} | Update_info: {status}")
                    return False
        except Exception as e:
            logger.error(f"{self.email} | Error update info | {e}")
            self.error += 1
            if self.error > 2:
                await self.swap_proxy()
                self.error = 0
            raise UpdateError("Update info error")

    async def reward_claim(self):
        try:
            logger.info(f"{self.email} | Check reward claim")
            await self.update_headers()

            if self.headers_retrive_user["Authorization"] == None:
                logger.error(
                    f"{self.email} | Error reward claim. Enought Authorization token"
                )
                return False

            REWARD_CLAIM_LIST = {
                "0001": 373,
                "0002": 373,
                "0003": 2595,
                "0004": 11351,
                "0005": 36351,
                "0006": 118247,
                "0007": 375443,
                "0008": 2767564,
                "0009": 7394899,
                "0010": 49616938,
            }

            logger.info(
                f"{self.email} | Total points: {self.totalpoints}, Reward claimed: {self.reward_claimed}"
            )
            if (
                self.totalpoints > 373
                and self.totalpoints > REWARD_CLAIM_LIST[self.reward_claimed]
            ):
                logger.debug("Need to claim reward")
                start_tier = 0
                last_tier = 0
                for index, tier in enumerate(REWARD_CLAIM_LIST.items(), start=1):
                    if self.reward_claimed == tier[0]:
                        start_tier = index
                    if self.totalpoints > tier[1]:
                        last_tier = index
                        continue
                    else:
                        break
                logger.debug(f"Need to claim {last_tier} - {start_tier}")
                if last_tier - start_tier >= 1:
                    available_tiers = last_tier - start_tier
                    logger.info(
                        f"{self.email} | Reward claim available: {available_tiers}"
                    )

                    for i in range(1, available_tiers + 1):
                        logger.debug(f"{self.email} | Claim reward: {i}")

                        async with AsyncSession() as s:
                            response = await s.post(
                                url=self.url["claimReward"],
                                headers=self.headers_retrive_user,
                                proxy=f"http://{self.proxy.link}",
                                impersonate="chrome",
                            )

                            status = response.status_code
                            if status == 200:
                                logger.info(f"{self.email} | Reward claim success: {i}")
                            else:
                                logger.error(
                                    f"{self.email} | Reward claim error: {status}\n{response.text}"
                                )
                            await asyncio.sleep(5)
                    await self.update_info()
        except Exception as e:
            logger.error(f"{self.email} | Error Reward claim | {e}")
            self.error += 1
            if self.error > 2:
                await self.swap_proxy()
                self.error = 0
            raise UpdateError("Reward claim error")

    async def save_wallet(self):
        try:
            await DataBase.execute(
                """
            UPDATE Accounts 
            SET wallet = ?, private_key = ?, seed = ?
            WHERE email = ?
            """,
                (self.wallet, self.private_key, self.seed, self.email),
            )
            logger.info(f"{self.email} | Account wallet has been saved in database")
            return True
        finally:
            pass

    async def save_info(self):
        try:
            await DataBase.execute(
                """
                UPDATE Accounts 
                SET referal_code = ?, entity = ?, username = ?, created = ?, verified = ?, wallet_verified = ?, reward_claimed = ?,
                modified = ?, refferals = ?, qualified_refferals = ?, userid = ?, userrole = ?, totalpoints = ?, parent_referrals = ?,
                wallet = ?
                WHERE email = ?
                """,
                (
                    self.referal_code,
                    self.entity,
                    self.username,
                    self.created,
                    self.verified,
                    self.wallet_verified,
                    self.reward_claimed,
                    self.modified,
                    self.refferals,
                    self.qualified_refferals,
                    self.userid,
                    self.userrole,
                    self.totalpoints,
                    self.parent_referrals,
                    self.wallet,
                    self.email,
                ),
            )

            if self.private_key or self.seed:
                await DataBase.execute(
                    """
                    UPDATE Accounts 
                    SET private_key = ?, seed = ?
                    WHERE email = ?
                    """,
                    (self.private_key, self.seed, self.email),
                )

            logger.info(f"{self.email} | Info account has been saved in database")
            return True
        except Exception as e:
            logger.error(f"{self.email} <---\n{e}")

    async def save_account(self):
        try:
            logger.debug(f"{self.email} | Save in db")
            await DataBase.execute(
                """
            INSERT INTO Accounts (email, ref_reg, username, email_password, imap_domain, forward_email) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    self.email,
                    self.ref_reg,
                    self.username,
                    self.email_password,
                    self.imap_domain,
                    self.forward_email,
                ),
            )

            logger.info(f"{self.email} | Account has been saved in database")
        except Exception as e:
            logger.error(f"{self.email} <---\n{e}")

    async def save_password(self):
        try:
            logger.debug(f"{self.email} | Save password in db")
            await DataBase.execute(
                """
            UPDATE Accounts
            SET password = ?
            WHERE email = ?
            """,
                (self.password, self.email),
            )
            logger.info(f"{self.email} | Password has been saved in database")
        except Exception as e:
            logger.error(f"{self.email} <---\n{e}")

    async def validate_session(self):
        try:
            await self.update_headers()
            row = await DataBase.query_custom_row(
                """SELECT access_token, access_token_create_time, user_agent, password\
                                  FROM Accounts WHERE email = ?""",
                (self.email,),
                one=True,
            )
            if not (bool(row[0]) and bool(row[1])):
                logger.info(f"{self.email} | No active session. Login...")
                self.password = row[3]
                logger.info(f"{self.email} | Send OTP code")
                if await self.send_otp(action="login"):
                    if self.password != None:
                        logger.info(f"{self.email} | Login via password")
                        if await self.login():
                            return True
                    otp_code = await self.get_email(
                        'Your One Time Password for Grass is'
                    )
                    if not isinstance(otp_code, str):
                        logger.error(f"{self.email} | Error get OTP Code: {otp_code}")
                        return False
                    logger.info(f"{self.email} | Success get OTP Code: {otp_code}")
                    if await self.verify_otp(otp_code):
                        return True
            else:
                logger.info(f"{self.email} | An active session is in use")
                self.access_token = row[0]
                self.user_agent = row[2]
                self.password = row[3]
                self.headers_retrive_user["Authorization"] = self.access_token
                return True
        finally:
            pass

    async def error_stat(self):
        self.error += 1
        if self.error > 3:
            await self.swap_proxy()
            self.error = 0

    @retry(
        stop=stop_after_attempt(2),
        retry=(retry_if_exception_type(VarificationError)),
        wait=wait_random(180, 300),
    )
    async def send_email_verification(self):
        try:
            logger.info(f"{self.email} | Start email verification")
            async with AsyncSession() as s:
                response = await s.post(
                    url=self.url["sendEmailVerification"],
                    headers=self.headers_retrive_user,
                    proxy=f"http://{self.proxy.link}",
                    impersonate="chrome",
                )

                status = response.status_code
                if status == 200:
                    logger.info(f"{self.email} | Sent verification message: {status}")
                    await asyncio.sleep(15)
                    return True
                else:
                    logger.error(f"{self.email} | Error send mail: {status}")
                    raise VarificationError
        except Exception as e:
            logger.error(f"{self.email} | Error send email verification \n{e}")
            await self.error_stat()
            raise VarificationError()

    @retry(
        stop=stop_after_attempt(5),
        retry=(retry_if_exception_type(VarificationError)),
        wait=wait_random(5, 7),
    )
    async def click_email_verification(self, token):
        try:
            logger.info(f"{self.email} | Attempt verified email")
            self.headers_retrive_user["Authorization"] = token

            async with AsyncSession() as s:
                response = await s.post(
                    url=self.url["confirmEmail"],
                    headers=self.headers_retrive_user,
                    proxy=f"http://{self.proxy.link}",
                    impersonate="chrome",
                )

                status = response.status_code
                if status == 200:
                    logger.info(
                        f"{self.email} | Success response from verification email: {status}"
                    )
                    return True
                else:
                    logger.error(
                        f"{self.email} | Error response from verification email: {status}"
                    )
                    raise VarificationError
        except Exception as e:
            logger.error(f"{self.email} | Error verification \n{e}")
            await self.error_stat()
            raise VarificationError()

    async def reset_password(self, token):
        try:
            logger.info(f"{self.email} | Attempt setup/reset password")
            self.headers_retrive_user["Authorization"] = token
            self.password = generate_pass() if self.password == None else self.password

            json_data = {"password": self.password}

            async with AsyncSession() as s:
                response = await s.post(
                    url=self.url["resetPassword"],
                    headers=self.headers_retrive_user,
                    data=json.dumps(json_data),
                    proxy=f"http://{self.proxy.link}",
                    impersonate="chrome",
                )

                status = response.status_code
                if status == 200:
                    logger.info(
                        f"{self.email} | Success setup password: {self.password}"
                    )
                    return True
                else:
                    logger.error(
                        f"{self.email} | Error setup password: Status {status}"
                    )
                    raise VarificationError

        except Exception as e:
            logger.error(f"{self.email} | Error setup password \n{e}")
            await self.error_stat()
            raise VarificationError()

    @retry(
        stop=stop_after_attempt(5),
        retry=(retry_if_exception_type(VarificationError)),
        wait=wait_random(5, 7),
    )
    async def click_wallet_verification(self, token):
        try:
            logger.info(f"{self.email} | Attempt verified wallet")
            async with AsyncSession() as s:
                response = await s.options(
                    url=self.url["confirmWalletAddress"],
                    headers=self.options_headers,
                    proxy=f"http://{self.proxy.link}",
                    impersonate="chrome",
                )

                status = response.status_code
                if status == 204:
                    self.headers_retrive_user["Authorization"] = token
                    response = await s.post(
                        url=self.url["confirmWalletAddress"],
                        headers=self.headers_retrive_user,
                        proxy=f"http://{self.proxy.link}",
                        impersonate="chrome",
                    )

                    status = response.status_code
                    if status == 200:
                        logger.info(
                            f"{self.email} | Success response from verification wallet: {status}"
                        )
                        return True
                    else:
                        logger.error(
                            f"{self.email} | Error response from verification wallet: {status}"
                        )
                        raise VarificationError

        except Exception as e:
            logger.error(f"{self.email} | Error verification {e}")
            await self.error_stat()
            raise VarificationError()

    @retry(
        stop=stop_after_attempt(5),
        retry=(retry_if_exception_type(ConnectWallet)),
        wait=wait_random(5, 7),
    )
    async def verifySignedMessage(self, sign, timestamp):
        try:
            logger.info(f"{self.email} | Connect wallet")
            self.headers_retrive_user["Authorization"] = self.access_token

            json_data = {
                "signedMessage": sign,
                "publicKey": self.public_key,
                "walletAddress": self.wallet,
                "timestamp": timestamp,
                "isLedger": False,
                "isAfterCountdown": True,
            }

            async with AsyncSession() as s:
                response = await s.post(
                    url=self.url["verifySignedMessage"],
                    headers=self.headers_retrive_user,
                    data=json.dumps(json_data),
                    proxy=f"http://{self.proxy.link}",
                    impersonate="chrome",
                )

                status = response.status_code
                if status == 200:
                    logger.info(f"{self.email} | Success connect wallet: {self.wallet}")
                    return True
                else:
                    logger.error(
                        f"{self.email} | Error connect wallet. Status: {status}"
                    )
                    raise ConnectWallet()

        except Exception as e:
            logger.error(f"{self.email} | Error connect wallet {e}")
            await self.error_stat()
            raise ConnectWallet()

    @retry(
        stop=stop_after_attempt(5),
        retry=(retry_if_exception_type(ConnectWallet)),
        wait=wait_random(5, 7),
    )
    async def send_wallet_verification(self):
        try:
            if (
                self.access_token == None
                and self.headers_retrive_user["Authorization"] == None
            ):
                logger.error(f"{self.email} | No authorization token")
                raise ConnectWallet
            self.headers_retrive_user["Authorization"] = self.access_token
            logger.info(f"{self.email} | Attempt send email verification wallet")

            async with AsyncSession() as s:
                response = await s.options(
                    url=self.url["sendWalletAddressEmailVerification"],
                    headers=self.options_headers,
                    proxy=f"http://{self.proxy.link}",
                    impersonate="chrome",
                )

                status = response.status_code
                if status == 204:
                    logger.info(f"{self.email} | Success OPTIONS request: {status}")

                    response = await s.post(
                        url=self.url["sendWalletAddressEmailVerification"],
                        headers=self.headers_retrive_user,
                        proxy=f"http://{self.proxy.link}",
                        impersonate="chrome",
                    )

                    status = response.status_code
                    if status == 200:
                        logger.info(
                            f"{self.email} | Send wallet verification email: {status}"
                        )
                        await asyncio.sleep(20)
                    else:
                        logger.error(
                            f"{self.email} | Send wallet verification email: {status}"
                        )
                        raise ConnectWallet
                    return True
                else:
                    logger.error(f"{self.email} | Error Options: {status}")
                    raise ConnectWallet

        except Exception as e:
            logger.error(f"{self.email} | Error: {e}")
            await self.error_stat()
            raise ConnectWallet()

    async def get_email(self, request) -> str:
        if self.forward_email:
            email = await asyncio.to_thread(
                IMAPRepository.search_mail,
                request=request,
                email=self.forward_email,
                password=self.email_password,
                imap_server=self.imap_domain,
                proxy=self.proxy.link,
                imap_proxy=args.imap_proxy,
            )
        else:
            email = await asyncio.to_thread(
                IMAPRepository.search_mail,
                request=request,
                email=self.email,
                password=self.email_password,
                imap_server=self.imap_domain,
                proxy=self.proxy.link,
                imap_proxy=args.imap_proxy,
            )
        return email

    async def email_verification(self, request):
        try:
            if request == 'Verify Your Email for Grass':
                await self.send_email_verification()
                email = await self.get_email(request)
                token = email.split("token=")[1].split("/")[0]
                #logger.debug(f"{self.email} | Token verified email: {token}")
                if token and await self.click_email_verification(token):
                    self.verified = True
                    return True
                else:
                    return False
            elif request == 'Verify Your Wallet Address':
                email = await self.get_email(request)
                if email:
                    token = email.split("token=")[1].split("/")[0]
                    #logger.debug(f"{self.email} | Token verified wallet: {token}")
                    return token
                else:
                    logger.error(f"{self.email} | Not found email")
                    raise TypeError

            elif request == 'Set Password':
                email = await self.get_email(request)
                token = email.split("token=")[1].split("/")[0]
                #logger.debug(f"{self.email} | Token setup password: {token}")
                return token
        except Exception as e:
            logger.error(f"{self.email} | Error verification {e}")
            raise e

    async def get_proxy(self):
        while True:
            proxy = await self.proxymanager.get()
            if proxy.link != "not_available_proxy:1111":
                self.proxy = proxy
                break
            else:
                logger.info(f"{self.email} | No available proxies. Sleep 20 second")
                await asyncio.sleep(20)

    async def swap_proxy(self):
        self.proxy.status = False
        self.proxy.last_touch = datetime.now()
        return await self.get_proxy()

    async def wallet_verification(self):
        try:
            logger.info(f"{self.email} | Start wallet verification")
            if self.wallet_verified == True:
                logger.info(f"{self.email} | Wallet already linked and verified")
            elif self.wallet_verified == False:
                if self.seed != None:
                    await self.send_wallet_verification()
                    token = await self.email_verification(
                        request='Verify Your Wallet Address for Grass'
                    )
                    await self.click_wallet_verification(token)
                else:
                    sign, timestamp = self.gen_wallet()
                    if await self.verifySignedMessage(sign, timestamp):
                        await self.save_wallet()
                        await self.send_wallet_verification()
                        token = await self.email_verification(
                            request='Verify Your Wallet Address for Grass'
                        )
                        await self.click_wallet_verification(token)
        except Exception as e:
            logger.error(f"{self.email} | Error verification {e}")
            raise e


def get_accounts(
    reflist: list,
    proxy: ProxyManager,
    accounts: str = "accounts.txt",
    domain: str = "",
    forward_mode: bool = False,
):
    list_accounts = []
    with open(accounts, "r", encoding="utf-8") as file:
        for string in file.readlines():
            string = string.strip()
            if ":" in string:
                string = tuple(string.split(":"))
                if forward_mode:
                    if validate_email(string[0]) and len(string) == 3 and domain:
                        account = Grass(
                            email=string[0],
                            password=generate_pass(),
                            forward_email=string[1],
                            email_password=string[2],
                            imap_domain=domain,
                            ref_reg=random.choice(reflist),
                            proxymanager=proxy,
                        )  # email:forward_email:email_pass
                        logger.info(
                            f"Select mode email:forward_email:email_pass | {string}"
                        )
                        list_accounts.append(account)
                    elif validate_email(string[0]) and len(string) == 4:
                        account = Grass(
                            email=string[0],
                            password=generate_pass(),
                            forward_email=string[1],
                            email_password=string[2],
                            imap_domain=string[3],
                            ref_reg=random.choice(reflist),
                            proxymanager=proxy,
                        )  # email:forward_email:email_pass:imap_domain
                        logger.info(
                            f"Select mode email:forward_email:email_pass:imap_domain | {string}"
                        )
                        list_accounts.append(account)
                else:
                    if validate_email(string[0]) and len(string) == 2 and domain:
                        account = Grass(
                            email=string[0],
                            password=generate_pass(),
                            email_password=string[1],
                            imap_domain=domain,
                            ref_reg=random.choice(reflist),
                            proxymanager=proxy,
                        )  # email:email_pass
                        logger.info(f"Select mode email:email_pass | {string}")
                        list_accounts.append(account)
                    elif validate_email(string[0]) and len(string) == 3:
                        account = Grass(
                            email=string[0],
                            password=generate_pass(),
                            email_password=string[1],
                            imap_domain=string[2],
                            ref_reg=random.choice(reflist),
                            proxymanager=proxy,
                        )  # email:email_pass:imap_domain
                        logger.info(
                            f"Select mode email:email_pass:imap_domain | {string}"
                        )
                        list_accounts.append(account)
            else:
                logger.error(f"Error parsing account | {string}")
    return list_accounts


async def import_acc_from_db(proxy: ProxyManager):
    logger.info(f"Import account from db")
    accounts = []
    result = [
        dict(row) for row in await DataBase.query_custom_row("SELECT * FROM Accounts")
    ]
    for i in result:
        acc = Grass(proxymanager=proxy)
        acc.__dict__.update(i)
        acc.cookies = json.loads(i["cookies"]) if i["cookies"] else None
        if acc.user_agent == None:
            acc.user_agent = get_user_agent()
        accounts.append(acc)
        logger.info(f"{acc.email} | Get in DB")
    return accounts


async def search_acc_db(account: Grass):
    logger.info(f"{account.email} | Search in db")
    result = await DataBase.query_custom_row(
        "SELECT * FROM Accounts WHERE email = ?", (account.email,), one=True
    )
    if result:
        account.__dict__.update(result)
        logger.info(
            f"{account.email} | Account was found in db | Password: {account.password}"
        )
        return True


async def worker_reg(account: Grass):
    try:
        async with semaphore:
            if await search_acc_db(account):
                logger.info(f"{account.email} | Account in the database | SKIP")
            else:
                await account.get_proxy()

                if await account.send_otp(action="register"):
                    otp_code = await account.get_email(
                        'Your One Time Password for Grass is'
                    )
                    logger.info(f"{account.email} | Success get OTP Code: {otp_code}")

                    if otp_code is None:
                        logger.error(f"{account.email} | Error getting OTP Code, skip account")
                        await account.proxymanager.drop(account.proxy)
                        return False

                    if await account.verify_otp(otp_code):
                        await account.save_account()
                        await account.save_session()
                        if await account.set_password():
                            token = await account.email_verification(
                                request='Set Password'
                            )
                            if await account.reset_password(token):
                                await account.save_password()
                            await account.update_info()
                else:
                    logger.error(f"{account.email} | Account maybe registered")
                await account.proxymanager.drop(account.proxy)
    except RetryError:
        logger.error(f"{account.email} | Registration | Retry Error")
    except Exception as e:
        print(f"{e}")



async def worker_update(account: Grass):
    try:
        async with semaphore:
            await account.get_proxy()
            logger.info(
                f"{account.email} | Proxy: {account.proxy.link} Password: {account.password}"
            )
            if await account.validate_session():
                await account.update_info()
            await account.proxymanager.drop(account.proxy)
    except RetryError:
        logger.error(f"{account.email} | Update | Retry Error")


async def worker_verif(account: Grass):
    try:
        async with semaphore:
            logger.debug(
                f"{account.email} | Mail Verified: {account.verified} | Wallet Verified: {account.wallet_verified} | Password: {account.password}"
            )
            if (
                account.verified == True
                and account.wallet_verified == True
                and account.password != None
            ):
                logger.info(
                    f"{account.email} | Account already verified and has a password | SKIP"
                )
            else:
                await account.get_proxy()
                logger.info(
                    f"{account.email} | Proxy: {account.proxy.link} Password: {account.password}"
                )
                if await account.validate_session():
                    await account.update_info()
                    if account.password == None:
                        logger.info(f"{account.email} | Start setup password")
                        if await account.set_password():
                            token = await account.email_verification(
                                request='Set Password'
                            )
                            if await account.reset_password(token):
                                await account.save_password()
                            await account.update_info()
                    if account.verified == False:
                        await account.email_verification(
                            request='Verify Your Email for Grass'
                        )
                    if account.verified == True and account.wallet_verified == False:
                        await account.wallet_verification()
                        await account.update_info()
                await account.proxymanager.drop(account.proxy)
    except RetryError:
        logger.error(f"{account.email} | Verification | Retry Error")


async def worker_import(account: Grass):
    try:
        async with semaphore:
            if await search_acc_db(account):
                return
            await account.save_account()
    except Exception as e:
        logger.error(f"{account.email} {e}")
        raise e


async def ui():
    args = run_ui()
    if args is None:
        raise SystemExit("No arguments provided")
    return args


async def main(new_args=None):
    try:
        await DataBase.migration()

        if new_args:
            logger.debug(f"{new_args}")
            global args, semaphore
            args = update_args(args, new_args)
            semaphore = asyncio.Semaphore(args.threads)

        if args.action in ["registration", "update", "verification"]:
            get_user_agent()

        if args.action == "registration":
            proxy = ProxyManager(get_proxies(args.proxy), args.rotate)
            reflist = get_ref(args.ref)
            accounts = get_accounts(
                reflist,
                proxy,
                accounts=args.accounts,
                domain=args.imap,
                forward_mode=args.forward_mode,
            )
            tasks = [worker_reg(a) for a in accounts]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"END Registration")

        elif args.action == "imap":
            await add_email_pass(DataBase, args.imap, args.accounts)
            logger.info(f"All imap info added")

        elif args.action == "import":
            import_accounts = await import_acc(
                file_name=args.file_name, separator=args.separator, form=args.format
            )
            database_accs = set(
                row[0] for row in await DataBase.query("""SELECT email FROM Accounts""")
            )
            import_accounts = [
                acc for acc in import_accounts if acc[0] not in database_accs
            ]
            await DataBase.executemany(
                """
                INSERT INTO Accounts (email, password, email_password, imap_domain, username, user_agent, referal_code, wallet, private_key, seed, forward_email) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                import_accounts,
            )
            logger.info(f"END import accounts")

        elif args.action == "export":
            await export_acc(
                DataBase,
                file_name=args.file_name,
                export_type=args.export_type,
                separator=args.separator,
                form=args.format,
            )
            logger.info(f"END export accounts")

        elif args.action == "update":
            proxy = ProxyManager(get_proxies(args.proxy), args.rotate)
            accounts = await import_acc_from_db(proxy)
            tasks = [worker_update(a) for a in accounts]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"END update info")

        elif args.action == "verification":
            proxy = ProxyManager(get_proxies(args.proxy), args.rotate)
            accounts = await import_acc_from_db(proxy)
            tasks = [worker_verif(a) for a in accounts]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"END Verification")
        else:
            logger.error(f"Incorrect --action argument")
    except Exception as e:
        print(e)
    finally:
        if DataBase._connection:
            await DataBase.close_connection()


if __name__ == "__main__":
    try:
        if args.action == None:
            new_args = asyncio.run(ui())
            asyncio.run(main(new_args))
            raise SystemExit
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Forces Stop")
    except Exception as e:
        raise e
