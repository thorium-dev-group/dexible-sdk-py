import asyncio
import sys
from baseorder import BaseOrder, log

async def main():
	if len(sys.argv) < 2:
		log.error(f"Usage: {sys.argv[0]} <order_id>")
		sys.exit(0)

	sdk = BaseOrder.create_dexible_sdk()
	r = await sdk.order.resume(int(sys.argv[1]))
	log.info(f"Order resume result: {r}")

if __name__ == '__main__':
    asyncio.run(main())
