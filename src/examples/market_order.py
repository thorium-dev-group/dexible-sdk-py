from tokens import *
from baseorder import BaseOrder, log
from dexible.common import as_units
import asyncio

TOKEN_IN = DAI_KOVAN
TOKEN_OUT = WETH_KOVAN
IN_AMT = as_units(2, 18)

async def main():
    sdk = BaseOrder.create_dexible_sdk()
    market = BaseOrder(
        sdk=sdk,
        token_in=TOKEN_IN,
        token_out=TOKEN_OUT,
        amount_in=IN_AMT,
        algo_details={
            "type": "Market",
            "params": {
                "gas_policy": {
                    "type": "relative",
                    "deviation": 0
                },
                "slippage_percent": 5
            }
        })

    r = await market.create_order()

    if "error" in r:
        log.info(f"Problem with order: {r['error']}")
        raise Exception(r['error'])
    elif "order" not in r:
        raise Exception("No order in prepare response")
    else:
        order = r["order"]
        log.info("Submitting order...")
        r = await order.submit()
        if "error" in r:
            raise Exception(r["error"])

        log.info(f"Order result: {r}")

if __name__ == '__main__':
    asyncio.run(main())


