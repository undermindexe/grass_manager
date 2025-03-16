import asyncio
from logger import logger
import pandas


ALWAYS_PARAM =('email', 'email_password', 'imap_domain')
ALLOW_PARAM = ('email', 'password', 'email_password', 'imap_domain', 'username', 'user_agent', 'referal_code', 'wallet', 'private_key', 'seed')


async def validate_params(keys: set, line):
    if len(keys) == len(line):
        if set(ALWAYS_PARAM).issubset(keys) and keys.issubset(set(ALLOW_PARAM)):
            return True
    return False

async def validate_filename(file_name: str):
    if not any(ch in file_name for ch in ['/', '\\', '"', '\'']):
        if '.txt' in file_name:
            return file_name
        else:
            return f'{file_name}.txt'
    else:
        return file_name.strip('"\'')



async def import_acc(file_name: str = 'import', separator: str = ':', form: str = 'email:password'):
    file_name = await validate_filename(file_name)
    list_accounts = []
    keys = form.split(separator)
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    for line in lines:
        account = []
        line = line.strip().split(separator)
        line = [None if item == "None" else item for item in line]
        if await validate_params(set(keys), line):
            account = tuple([line[keys.index(i)] if i in keys else None for i in ALLOW_PARAM])
            list_accounts.append(account)
            logger.debug(f'{account}')
    if len(list_accounts) > 0:
        return list_accounts
    else:
        logger.error(f'Error in the parameters, separator or fromat not equal import data\nALWAYS PARAMETERS: {ALWAYS_PARAM}\nALLOW_PARAMETERS: {ALLOW_PARAM}')

async def export_acc(db, file_name: str, export_type: str = 'excel', form: str = 'email:password', separator: str = ':'):
    file_name = await validate_filename(file_name)
    if export_type == 'excel':
        rows, description = await db.query('''
        SELECT * FROM Accounts
        ''', description = True)
        columns = [desc[0] for desc in description]
        df = pandas.DataFrame(rows, columns=columns)
        df.to_excel(f'{file_name.rstrip('.txt')}.xlsx', index=False, engine='openpyxl')

    if export_type == 'txt':
        
        keys = form.split(separator)

        rows = await db.query_custom_row('SELECT * FROM Accounts')
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

        with open(f'{file_name}', 'a', encoding='utf-8') as file:
            file.writelines(list_string)