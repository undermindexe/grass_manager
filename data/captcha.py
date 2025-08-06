import asyncio
from playwright.async_api import async_playwright
from .custom_logger import logger
import subprocess
import ctypes
import random
import os
import json
import tempfile
import shutil
import socket
from pathlib import Path
from .proxy import Proxy

SW_MINIMIZE = 7


class CaptchaService:
    def __init__(self, proxy: Proxy, cookies: str = None, storage_state: str = None):
        self.port = self.get_free_port()
        self.proxy = self.set_proxy_data(proxy)
        self.cookies = cookies if cookies else None
        self.storage_state = storage_state

    def set_proxy_data(self, proxy: Proxy) -> dict:
        return {
            "server": f"http://{proxy.host}:{proxy.port}",
            "username": f"{proxy.login}",
            "password": f"{proxy.password}",
        }

    def get_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    async def solve_turnstile(self) -> dict:
        chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
        profile_dir = tempfile.mkdtemp(prefix="temp_profile_")
        debug_port = self.port

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = SW_MINIMIZE  # Свернуто при запуске

        chrome_proc = subprocess.Popen(
            [
                chrome_path,
                f"--user-data-dir={profile_dir}",
                f"--remote-debugging-port={debug_port}",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            startupinfo=startupinfo,
        )

        try:
            endpoint = f"http://localhost:{debug_port}"
            playwright = await async_playwright().start()
            browser = await playwright.chromium.connect_over_cdp(endpoint)
            context = await browser.new_context(
                proxy=self.proxy,
                locale="en-US",
                storage_state=(
                    json.loads(self.storage_state)
                    if isinstance(self.storage_state, str)
                    else self.storage_state
                ),
            )
            if self.cookies:
                await context.add_cookies(cookies=self.cookies)
            self.page = await context.new_page()

            await self.page.goto("https://app.grass.io/register", timeout=60000)
            await self.click_button(
                selector='button:has-text("ACCEPT ALL")', timeout=5000
            )
            await self.wait_cloudflare_frame()
            await self.page.wait_for_function(
                "document.querySelector('[name=cf-turnstile-response]')?.value?.length > 0",
                timeout=12000,
            )

            token = await self.solve_captcha()
            cookies = await context.cookies()
            user_agent = await self.page.evaluate("navigator.userAgent")
            storage_state = await context.storage_state()

            await browser.close()
            await playwright.stop()
            return {
                "token": token,
                "cookies": cookies,
                "user_agent": user_agent,
                "storage_state": storage_state,
            }

        finally:
            chrome_proc.terminate()
            chrome_proc.wait(timeout=5)
            await asyncio.sleep(1)
            if Path(profile_dir).exists():
                shutil.rmtree(profile_dir, ignore_errors=True)

    async def wait_cloudflare_frame(self):
        await self.page.wait_for_timeout(10000)
        element = await self.page.query_selector("#g-recaptcha-signup-el")
        box = await element.bounding_box()
        if box:
            await self.page.mouse.click(
                box["x"] + box["width"] / 8, box["y"] + box["height"] / 2
            )

    async def solve_captcha(self) -> str:
        token = await self.page.eval_on_selector(
            "[name=cf-turnstile-response]", "el => el.value"
        )
        return token

    async def click_button(self, selector: str, timeout: int):
        try:
            await self.page.wait_for_selector(selector=selector, timeout=timeout)
            await self.page.click(selector=selector)
        except:
            pass
