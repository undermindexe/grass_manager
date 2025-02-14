import asyncio
from datetime import datetime

class Proxy:
    def __init__(self, proxy: str):
        self.link = proxy
        self.status = False
        self.last_ip = None
        self.last_touch = None
        self.errors = 0


class ProxyManager:
    def __init__(self, proxies: list, rotation: int):
        self.proxies = [Proxy(i) for i in proxies]
        self.rotation_time = rotation
    
    async def get(self):
        try:
            for i in self.proxies:
                if i.status == False and (i.last_touch == None or await ProxyManager.check_time(i.last_touch, self.rotation_time)) and i.errors <= 3:
                    proxy = i
                    proxy.status = True
                    return proxy
                else:
                    None
            return Proxy('not_available_proxy:1111')
        except Exception as e:
            print(f'{e}')
            raise e

    
    async def swap(self, proxy):
        proxy.status = False
        proxy.last_touch = datetime.now()
        proxy.errors += 1
        return await self.get()

    async def drop(self, proxy):
        proxy.status = False
        proxy.last_touch = datetime.now()
        self.proxies.remove(proxy)
        self.proxies.append(proxy)

    async def drop_not_use(self, proxy):
        proxy.status = False

    @staticmethod
    async def check_time(last_touch: datetime, rotate: int):
        actual_time = datetime.now()
        result = actual_time - last_touch
        if result.seconds >= rotate:
            return True
        return False


def get_proxies():
    proxy = []
    with open('proxy.txt', 'r', encoding='utf-8') as file:
        for i in file.readlines():
            proxy.append(i.strip())
    return proxy

async def main():
    proxy = ProxyManager(get_proxies(), 12)
    for _ in range(250):
        my_proxy = await proxy.get()
        print(my_proxy.link)
        await proxy.swap(my_proxy)

if __name__ == '__main__':
    asyncio.run(main())
