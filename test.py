import asyncio

from lcu import lcu


async def main():
    await lcu.start()


asyncio.run(main())
