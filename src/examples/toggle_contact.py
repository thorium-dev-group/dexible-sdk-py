import asyncio
import sys
from baseorder import BaseOrder, log

async def main():
	if len(sys.argv) < 2:
		log.error(f"Usage: {sys.argv[0]} <contact_id>")
		sys.exit(0)

	sdk = BaseOrder.create_dexible_sdk()
	r = await sdk.contact.toggle(int(sys.argv[1]))
	log.info(f"Contact toggle result: {r}")

if __name__ == '__main__':
    asyncio.run(main())
