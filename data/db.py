import asyncio
import aiosqlite

class DataBase:

    def __init__(self, path: str = 'database.db'):
        self.path = path

        self.cursor = None
        self.connection = None
        self._row = aiosqlite.Row




    async def connect(self):
        self.connection = await aiosqlite.connect(self.path)
        self.cursor = await self.connection.cursor()
        await self.validate_table()
        return self.connection

    async def validate_table(self):
        await self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Accounts(
        id INTEGER PRIMARY KEY,
        email TEXT NOT NULL,
        email_password TEXT,
        imap_domain TEXT,
        username TEXT,
        password TEXT NOT NULL,
        access_token TEXT,
        refresh_token TEXT,
        access_token_create_time DATETIME,
        user_agent TEXT,
        ref_reg TEXT,
        userid TEXT,
        userrole TEXT,
        referal_code TEXT,
        entity TEXT,
        created DATETIME,
        verified BOOLEAN,
        wallet_verified BOOLEAN,
        reward_claimed TEXT,
        modified TEXT,
        refferals INTEGER,
        qualified_refferals INTEGER,
        totalpoints INTEGER,
        tokens INTEGER,
        parent_referrals TEXT,
        wallet TEXT,
        private_key TEXT,
        seed TEXT
        )
        ''')

        await self.connection.commit()

    async def close(self):
        if self.connection._connection != None:
            await self.cursor.close()
            await self.connection.close()
