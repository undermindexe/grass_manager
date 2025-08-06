import random
import quopri
import time
import re

from .custom_logger import logger
from .imap import SocksIMAP4SSL


class IMAPRepository:

    @staticmethod
    def get_mailbox(
        email: str, password: str, imap_server: str, proxy: str, imap_proxy: str = None
    ):
        """
        Get mailbox from IMAP server
        """
        if imap_proxy:
            with open(imap_proxy, "r", encoding="utf-8") as file:
                proxies = file.readlines()
                proxy = parse_proxy(random.choice(proxies).strip())
        else:
            proxy = parse_proxy(proxy)
        proxy_username, proxy_password, proxy_addr, proxy_port = (
            proxy[0],
            proxy[1],
            proxy[2],
            int(proxy[3]),
        )
        mailbox = SocksIMAP4SSL(
            host=imap_server,
            port=993,
            proxy_addr=proxy_addr,
            proxy_port=proxy_port,
            proxy_type="socks5",
            username=proxy_username,
            password=proxy_password,
        )
        mailbox.login(email, password)
        return mailbox

    @staticmethod
    def search_mail(
        request: str,
        email: str,
        password: str,
        imap_server: str,
        proxy: str,
        imap_proxy: str = None,
    ):
        """
        Search mail in IMAP server
        """

        error = 0
        while error <= 5:
            try:
                logger.debug(f"{email} | {password} | {imap_server} | {proxy}")

                mailbox = IMAPRepository.get_mailbox(
                    email=email,
                    password=password,
                    imap_server=imap_server,
                    proxy=proxy,
                    imap_proxy=imap_proxy,
                )

                typ, data = mailbox.list()
                folders = reversed(
                    [
                        re.search(rb'["|/] (.+)', folder).group(1).decode("utf-8")
                        for folder in data
                    ]
                )

                attempt = 0
                while attempt < 6:
                    for i in folders:
                        logger.debug(f'{email} | Search mail in folder "{i}"')
                        mailbox.select(i)
                        status, search = mailbox.search("utf-8", request)
                        if status == "OK" and search != [None]:
                            # logger.debug(search)
                            last_mail = get_last_mail(mailbox, msgs=search[0].split())
                            # logger.debug(last_mail)
                            logger.info(f"{email} | Found message")
                            if "Your One Time Password for Grass is" in request:
                                status, data = mailbox.fetch(
                                    last_mail, "(BODY[HEADER.FIELDS (SUBJECT)])"
                                )
                                result = quopri.decodestring(data[0][1]).decode("utf-8")
                                result = result.strip()[-6:]
                            else:
                                status, data = mailbox.fetch(last_mail, "(BODY[TEXT])")
                                result = quopri.decodestring(data[0][1]).decode("utf-8")
                            mailbox.store(last_mail, "+FLAGS", "\\Deleted")
                            mailbox.expunge()
                            check_trash_grass(mailbox)
                            return result
                    attempt += 1
                    time.sleep(10)
            except Exception as e:
                error += 1
                if error <= 5:
                    logger.error(f"{email} | {e}")
                    time.sleep(15)


def check_trash_grass(mailbox: SocksIMAP4SSL):
    """
    Check and delete Grass Foundation emails if there are more than 50 in a folder
    """
    try:
        typ, data = mailbox.list()
        folders = [
            re.search(rb'["|/] (.+)', folder).group(1).decode("utf-8")
            for folder in data
        ]

        for folder in folders:
            logger.debug(f"Checking folder: {folder}")
            mailbox.select(folder)

            status, search = mailbox.search("utf-8", 'FROM "Grass Foundation"')

            if status == "OK" and search[0]:
                msg_ids = search[0].split()
                if len(msg_ids) > 20:
                    logger.info(
                        f'Found {len(msg_ids)} "Grass Foundation" emails in {folder}, deleting...'
                    )

                    for msg_id in msg_ids:
                        mailbox.store(msg_id, "+FLAGS", "\\Deleted")
                    mailbox.expunge()
                    logger.info(
                        f"Successfully deleted Grass Foundation emails from {folder}"
                    )
    except Exception as e:
        logger.error(f"Error while checking trash mail: {e}")


def get_last_mail(mailbox: SocksIMAP4SSL, msgs: list):
    """
    Get last mail from IMAP server
    """
    msg_dates = []
    for msg_id in msgs:
        status, date_data = mailbox.fetch(msg_id, "(INTERNALDATE)")
        if status != "OK":
            continue
        match = re.search(r'"(.+?)"', date_data[0].decode())
        if match:
            msg_date = time.strptime(match.group(1), "%d-%b-%Y %H:%M:%S %z")
            msg_dates.append((msg_id, msg_date))
    sorted_mails = sorted(msg_dates, key=lambda x: x[1], reverse=True)
    if len(sorted_mails) > 20:
        for msg, _ in sorted_mails:
            mailbox.store(str(msg), "+FLAGS", "\\Deleted")
        mailbox.expunge()
    return sorted_mails[0][0]


def parse_proxy(proxy: str):
    result = re.split(r"[:,@]", proxy)
    return result
