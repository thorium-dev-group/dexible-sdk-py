from tokens import *
from baseorder import BaseOrder, log
from dexible.common import Price, as_units
from dexible.exceptions import *
import asyncio

TOKEN_IN = DAI_KOVAN
TOKEN_OUT = WETH_KOVAN
IN_AMT = as_units(500, 18)

async def main():
    sdk = BaseOrder.create_dexible_sdk()
    token_in = await sdk.token.lookup(TOKEN_IN)
    token_out = await sdk.token.lookup(TOKEN_OUT)

    twap = BaseOrder(
        sdk=sdk,
        token_in=TOKEN_IN,
        token_out=TOKEN_OUT,
        amount_in=IN_AMT,
        algo_details={
            "type": "TWAP",
            "params": {
                "time_window": {"minutes": 7},
                "price_range": {
                    "base_price": Price.units_to_price(in_token=token_in,
                                                       out_token=token_out,
                                                       in_units=1,
                                                       out_units=.00133),
                    "lower_bound_percent": 1,
                    "upper_bound_percent": 1},
                "gas_policy": {
                    "type": "relative",
                    "deviation": 0
                },
                "slippage_percent": 5
            }
        })

    try:
        order = await twap.create_order()
        log.info("Submitting order...")
        result = await order.submit()

        log.info(f"Order result: {result}")
    except InvalidOrderException as e:
        log.error(f"Probem with order: {e}")
    except QuoteMissingException as e:
        log.error(f"Could not generate quote: {e}")
    except DexibleException as e:
        log.error(f"Generic problem: {e}")

if __name__ == '__main__':
    asyncio.run(main())


