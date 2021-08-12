import asyncio
import sys
from baseorder import BaseOrder, log
from tokens import WETH_KOVAN, DAI_KOVAN
from dexible.common import as_units


async def main():
    sdk = BaseOrder.create_dexible_sdk()

    token_out = await sdk.token.lookup(DAI_KOVAN)
    token_in = await sdk.token.lookup(WETH_KOVAN)

    r = await sdk.quote.get_quote(token_in=token_in,
                                  token_out=token_out,
                                  amount_in=as_units(600),
                                  slippage_percent=0.5)

    log.info(f"Quote: {r}")

if __name__ == '__main__':
    asyncio.run(main())
