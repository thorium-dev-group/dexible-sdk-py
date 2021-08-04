from tokens import *
from baseorder import BaseOrder, log
from dexible.common import Price, as_units
import asyncio

# TOKEN_IN = "0xa36085f69e2889c224210f603d836748e7dc0088" # Chainlink Kovan
TOKEN_IN = DAI_KOVAN
TOKEN_OUT = WETH_KOVAN
IN_AMT = as_units(5, 18)

async def main():
    sdk = BaseOrder.create_dexible_sdk()
    token_in = await sdk.token.lookup(TOKEN_IN)
    token_out = await sdk.token.lookup(TOKEN_OUT)

    limit = BaseOrder(
        sdk=sdk,
        token_in=TOKEN_IN,
        token_out=TOKEN_OUT,
        amount_in=IN_AMT,
        algo_details={
            "type": "Limit",
            "params": {
                "price": Price.units_to_price(in_token=token_in,
                                              out_token=token_out,
                                              in_units=1,
                                              out_units=.00133),
                "gas_policy": {
                    "type": "relative",
                    "deviation": 0
                },
                "slippage_percent": 5
            }
        })

    r = await limit.create_order()

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


