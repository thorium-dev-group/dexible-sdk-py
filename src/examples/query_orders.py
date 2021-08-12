import asyncio
import sys
from baseorder import BaseOrder, log


async def main():
    sdk = BaseOrder.create_dexible_sdk()
    r = await sdk.order.get_all()
    log.info(f"Orders: {r}")

if __name__ == '__main__':
    asyncio.run(main())
