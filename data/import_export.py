import asyncio
from logger import logger
import pandas


ALWAYS_PARAM ={'email', 'password'}
ALLOW_PARAM = {'email', 'password', 'email_password', 'imap_domain', 'username', 'user_agent', 'referal_code', 'wallet', 'private_key', 'seed'}


async def validate_params(dict_keys: set, line):
    if len(dict_keys) == len(line):
        if ALWAYS_PARAM.issubset(dict_keys) and dict_keys.issubset(ALLOW_PARAM):
            return True
    return False
        
async def import_acc(file_name: str = 'import.txt', separator: str = ':', form: str = 'email:password'):
    list_accounts = []
    dict_keys = set(form.split(separator))
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            account = {}
            line = line.strip().split(separator)
            if await validate_params(dict_keys, line):
                for k,v in zip(form.split(separator), line):
                    account[k] = v
                list_accounts.append(account)
                logger.debug(f'{account}')
    if len(list_accounts) > 0:
        return list_accounts
    else:
        logger.error(f'Error in the parameters, separator or fromat not equal import data\nALWAYS PARAMETERS: {ALWAYS_PARAM}\nALLOW_PARAMETERS: {ALLOW_PARAM}')

async def export_acc(database, file_name: str, export_type: str = 'excel', form: str = 'email:password', separator: str = ':'):

    if export_type == 'excel':
        database = database()
        db = await database.connect()
        res = await db.execute('''
        SELECT * FROM Accounts
        ''')
        columns = [desc[0] for desc in res.description]
        rows = await res.fetchall()
        df = pandas.DataFrame(rows, columns=columns)
        df.to_excel(f'{file_name}.xlsx', index=False, engine='openpyxl')

    if export_type == 'txt':
        
        keys = form.split(separator)

        database = database()
        db = await database.connect()
        db.row_factory = database._row
        cursor = await db.execute('SELECT * FROM Accounts')
        rows = await cursor.fetchall()
        list_accs = [dict(row) for row in rows]
        list_string = []
        for acc in list_accs:
            data = [acc.get(key, '') if acc.get(key, '') != None else 'None' for key in keys]
            if len(data) > 1:
                string = separator.join(data)
            else:
                string = data[0]
            string += '\n'
            list_string.append(string)

        with open(f'{file_name}.txt', 'a', encoding='utf-8') as file:
            file.writelines(list_string)