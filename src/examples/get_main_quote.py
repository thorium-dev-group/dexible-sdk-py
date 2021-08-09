import asyncio
import logging
from baseorder import BaseOrder, log
from tokens import *
from dexible.common import as_units

async def main():
	logging.basicConfig(level=logging.INFO)
	inputs = [WETH_KOVAN, USDC_KOVAN, WETH_KOVAN, WETH_KOVAN]
	outputs = [WBTC_KOVAN, WETH_KOVAN, DAI_KOVAN, USDC_KOVAN]
	amounts = [as_units(300, 18), as_units(300000, 6), as_units(300, 18), as_units(300, 18)]
	sdk = BaseOrder.create_dexible_sdk()
	calls = []

	for i in range(0, len(inputs)):
		token_in = await sdk.token.lookup(inputs[i])
		token_out = await sdk.token.lookup(outputs[i])
		calls.append(sdk.quote.get_quote(token_in=token_in,
										 token_out=token_out,
										 amount_in=amounts[i],
										 slippage_percent=.5))

	r = await asyncio.gather(*calls)
	log.info(f"Quotes: {r}")

if __name__ == '__main__':
    asyncio.run(main())
