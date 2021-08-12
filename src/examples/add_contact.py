import asyncio
from baseorder import BaseOrder, log


async def main():
    sdk = BaseOrder.create_dexible_sdk()
    r = await sdk.contact.add("dexible-gene@shouldnt-resolve-876591234.com")
    log.info(f"Contact API response: {r}")

if __name__ == '__main__':
    asyncio.run(main())
