import asyncio
from baseorder import BaseOrder, log

async def main():
	sdk = BaseOrder.create_dexible_sdk()
	r = await sdk.contact.get_all()
	log.info(f"Contact API response: {r}")

if __name__ == '__main__':
    asyncio.run(main())
