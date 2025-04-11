import ssl
import quopri

from socks import create_connection
from socks import PROXY_TYPE_SOCKS4
from socks import PROXY_TYPE_SOCKS5
from socks import PROXY_TYPE_HTTP

from imaplib import IMAP4
from imaplib import IMAP4_PORT
from imaplib import IMAP4_SSL_PORT

import re

from logger import logger

import time
import random

class SocksIMAP4(IMAP4):

    PROXY_TYPES = {"socks4": PROXY_TYPE_SOCKS4,
                   "socks5": PROXY_TYPE_SOCKS5,
                   "http": PROXY_TYPE_HTTP}

    def __init__(self, host, port=IMAP4_PORT, proxy_addr=None, proxy_port=None,
                 rdns=True, username=None, password=None, proxy_type="socks5", timeout=None):

        self.proxy_addr = proxy_addr
        self.proxy_port = proxy_port
        self.rdns = rdns
        self.username = username
        self.password = password
        self.proxy_type = SocksIMAP4.PROXY_TYPES[proxy_type.lower()]

        IMAP4.__init__(self, host, port, timeout)

    def _create_socket(self):
        return create_connection((self.host, self.port), proxy_type=self.proxy_type, proxy_addr=self.proxy_addr,
                                 proxy_port=self.proxy_port, proxy_rdns=self.rdns, proxy_username=self.username,
                                 proxy_password=self.password)


class SocksIMAP4SSL(SocksIMAP4):

    def __init__(self, host='', port=993, keyfile=None, certfile=None, ssl_context=None, proxy_addr=None,
                 proxy_port=None, rdns=True, username=None, password=None, proxy_type="socks5", timeout=None):

        if ssl_context is not None and keyfile is not None:
                raise ValueError("ssl_context and keyfile arguments are mutually "
                                 "exclusive")
        if ssl_context is not None and certfile is not None:
            raise ValueError("ssl_context and certfile arguments are mutually "
                             "exclusive")

        self.keyfile = keyfile
        self.certfile = certfile
        if ssl_context is None:
            ssl_context = ssl._create_stdlib_context(certfile=certfile,
                                                     keyfile=keyfile)
        self.ssl_context = ssl_context

        SocksIMAP4.__init__(self, host, port, proxy_addr=proxy_addr, proxy_port=proxy_port,
                            rdns=rdns, username=username, password=password, proxy_type=proxy_type, timeout=None)

    def _create_socket(self, timeout = None):
        sock = SocksIMAP4._create_socket(self)
        server_hostname = self.host if ssl.HAS_SNI else None
        return self.ssl_context.wrap_socket(sock, server_hostname=server_hostname)
        
    def open(self, host='', port=IMAP4_PORT, timeout=None):
        SocksIMAP4.open(self, host, port, timeout)

def search_mail(request,
                email,
                password,
                imap_server,
                proxy,
                imap_proxy = None):
    if imap_proxy:
        with open(imap_proxy, 'r', encoding='utf-8') as file:
            proxies = file.readlines()
            proxy = parse_proxy(random.choice(proxies).strip())
    else:
        proxy = parse_proxy(proxy)
    proxy_username, proxy_password, proxy_addr, proxy_port = proxy[0], proxy[1], proxy[2], int(proxy[3])
    error = 0
    while error <= 5:
        try:
            logger.debug(f'{email} | {password} | {imap_server} | {proxy}')

            mailbox = SocksIMAP4SSL(host=imap_server, port=993,
                                    proxy_addr=proxy_addr, proxy_port=proxy_port, 
                                    proxy_type="socks5", username=proxy_username, 
                                    password=proxy_password)
            mailbox.login(email, password)

            typ, data = mailbox.list()
            logger.debug(data)
            folders = reversed([re.search(br'["|/] (.+)', folder).group(1).decode('utf-8') for folder in data])
            attempt = 0
            while attempt < 6:
                for i in folders:
                    logger.debug(f'{email} | Search mail in folder "{i}"')
                    mailbox.select(i)
                    status, search = mailbox.search('utf-8', request)
                    if status == 'OK' and search != [None]:
                        logger.debug(search)
                        mails = latest_sort(mailbox, msgs=search[0].split())
                        sorted_mails = sorted(mails, key=lambda x: x[1], reverse=True)
                        logger.debug(mails)
                        for msg, _ in sorted_mails:
                            logger.info(f'{email} | Found message')
                            if 'Your One Time Password for Grass is' in request:
                                status, data = mailbox.fetch(msg, '(BODY[HEADER.FIELDS (SUBJECT)])')
                                result = quopri.decodestring(data[0][1]).decode('utf-8')
                                result = result.strip()[-6:]
                            else:
                                status, data = mailbox.fetch(msg, '(BODY[TEXT])')
                                result = quopri.decodestring(data[0][1]).decode('utf-8')
                            return result
                attempt += 1
                time.sleep(10)
        except Exception as e:
            error += 1
            if error <= 5:
                logger.error(f'{email} | {e}')
                time.sleep(15)

def latest_sort(mailbox, msgs):
    msg_dates = []
    for msg_id in msgs:
        status, date_data = mailbox.fetch(msg_id, '(INTERNALDATE)')
        if status != 'OK':
            continue
        match = re.search(r'"(.+?)"', date_data[0].decode())
        if match:
            msg_date = time.strptime(match.group(1), "%d-%b-%Y %H:%M:%S %z")
            msg_dates.append((msg_id, msg_date))
    return msg_dates

def parse_proxy(proxy: str):
    result = re.split(r'[:,@]', proxy)
    return result