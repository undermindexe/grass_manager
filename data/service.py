import asyncio
import re
import random
from random_words import RandomNicknames, RandomEmails
import string
from logger import logger
from fake_useragent import UserAgent

USER_AGENTS = []


def validate_email(email: str):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email)

def generate_pass():
    symbols = "%@$"
    password = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice(symbols),
    ]

    remaining_length = random.randint(4, 10)
    password += random.choices(string.ascii_letters + string.digits + symbols, k=remaining_length)
    random.shuffle(password) 
    return ''.join(password)

def get_user_agent():
    if USER_AGENTS:
        return random.choice(USER_AGENTS)
    else:
        logger.info(f'Generate user-agent list')
        for _ in range(150):
            USER_AGENTS.append(UserAgent('Chrome', 'Windows', 131.0, 0.0, 'desktop').random)
            print(USER_AGENTS[-1])
        return random.choice(USER_AGENTS)

def get_random_mail(n):
    list_acc = []
    for _ in range(n):
        length_local = random.randint(7,12)
        length_domain = random.randint(7,12)
        domain_list = ["gmail.com"]
        local_part = ''.join(random.choices(string.ascii_letters + string.digits, k=length_local))

        if domain_list:
            domain_part = random.choice(domain_list)
        else:
            domain_part = ''.join(random.choices(string.ascii_lowercase, k=length_domain)) + ".com"
        list_acc.append(f"{local_part}@{domain_part}:password:imap.gmail.com\n")
    return list_acc

def get_proxies(proxy_path: str = 'proxy.txt'):
    proxy = []
    with open(proxy_path, 'r', encoding='utf-8') as file:
        for i in file.readlines():
            proxy.append(i.strip())
    return proxy

def get_ref(path_ref: str = 'referral.txt'):
    ref = []
    with open(path_ref, 'r', encoding='utf-8') as file:
        ref = [i.strip() for i in file.readlines()]
        if len(ref) == 0:
            ref = ['GRASS', 'GRASS']
    print(ref)
    return ref

def get_nickname():
    nickname = RandomNicknames().random_nick(gender='m').lower() + \
                ''.join(random.choice(string.ascii_lowercase) for _ in range(random.randint(1,3)) ) + \
                random.choice(['',RandomNicknames().random_nick(gender='m').lower(), str(random.randint(0,99))])
    if len(nickname) < 10:
        nickname += ''.join(random.choice(string.ascii_lowercase) for _ in range(1,4))
    return nickname

def generate_random_email(num, path):
    list_emails = get_random_mail(num)
    with open(path, 'w+', encoding='utf-8') as file:
        file.writelines(list_emails)

async def add_email_pass(db, fixed_imap: str = None, path: str = 'accounts.txt'):
    try:
        batch_size = 1000
        updates = []
        with open(path, 'r', encoding='utf-8') as file:
            for string in file.readlines():
                string = string.strip()
                if ':' in string:
                    string = tuple(string.split(':'))
                    if validate_email(string[0]) and (len(string) == 2 or len(string) == 3):
                        email = string[0]
                        email_pass = string[1]
                        imap_domain = string[2] if len(string) == 3 else fixed_imap if fixed_imap else None
                        updates.append((email_pass, imap_domain, email))
                        logger.info(f'{email} | Add {email_pass} and {imap_domain}')

                        if len(updates) >= batch_size:
                            logger.info(f'Writing {len(updates)} to the database')
                            await db.executemany('''
                            UPDATE Accounts
                            SET email_password = ?, imap_domain = ?
                            WHERE email = ?
                            ''', updates)
                            updates.clear()
        if updates:
            logger.info(f'Writing {len(updates)} to the database')
            await db.executemany('''
            UPDATE Accounts
            SET email_password = ?, imap_domain = ?
            WHERE email = ?
            ''', updates)
            updates.clear()

    except Exception as e:
        print(e)



