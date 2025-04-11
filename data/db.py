import asyncio
import aiosqlite
from .migrations import MIGRATIONS

class DataBase:
    _connection = None
    _lock = asyncio.Lock()

    @classmethod
    async def migration(cls):
        async with cls._lock:
            conn = await cls.get_connection()

            async with conn.execute("SELECT name FROM schema_migrations") as cursor:
                applied = {row[0] async for row in cursor}

            for name, sql in MIGRATIONS:
                if name not in applied:
                    try:
                        print(f"Applying migration: {name}")
                        await conn.execute(sql)
                        await conn.execute("INSERT INTO schema_migrations (name) VALUES (?)", (name,))
                        await conn.commit()
                        print("All migrations applied.")
                    except Exception as e:
                        print(f"Error applying migration {name}: {e}")

    @classmethod
    async def get_connection(cls):
        if cls._connection is None:
            cls._connection = await aiosqlite.connect('database.db')
        await cls._connection.execute('PRAGMA journal_mode=WAL;')
        await cls._connection.commit()

        await cls._connection.execute('''
            CREATE TABLE IF NOT EXISTS Accounts(
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL,
            email_password TEXT,
            imap_domain TEXT,
            username TEXT,
            password TEXT,
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
        await cls._connection.commit()

        await cls._connection.execute('''
            CREATE INDEX IF NOT EXISTS idx_email ON Accounts(email)
        ''')
        await cls._connection.commit()

        await cls._connection.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY
            )
        ''')
        await cls._connection.commit()
        return cls._connection

    @classmethod
    async def execute(cls, query, params = ()):
        async with cls._lock:
            conn = await cls.get_connection()
            await conn.execute(query, params)
            await conn.commit()

    @classmethod
    async def executemany(cls, query, params = ()):
        async with cls._lock:
            conn = await cls.get_connection()
            await conn.executemany(query, params)
            await conn.commit()

    @classmethod
    async def query(cls, query, params = (), description = False):
        async with cls._lock:
            conn = await cls.get_connection()
            async with conn.execute(query, params) as cursor:
                result = await cursor.fetchall()
                if description:
                    return result, cursor.description
        return result
    
    @classmethod
    async def query_custom_row(cls, query, params = (), one = False):
        async with cls._lock:
            conn = await cls.get_connection()
            default_row_factory = conn.row_factory
            conn.row_factory = aiosqlite.Row
            if one:
                async with conn.execute(query, params) as cursor:
                    result = await cursor.fetchone()
            else:
                async with conn.execute(query, params) as cursor:
                    result = await cursor.fetchall()
            conn.row_factory = default_row_factory
        return result


    @classmethod
    async def close_connection(cls):
        if cls._connection:
            await cls._connection.close()
            cls._connection = None
