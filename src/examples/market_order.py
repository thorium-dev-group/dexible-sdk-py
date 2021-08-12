from tokens import *
from baseorder import BaseOrder, log
from dexible.common import as_units
from dexible.exceptions import *
import asyncio

TOKEN_IN = DAI_KOVAN

TOKEN_OUT = WETH_KOVAN
IN_AMT = as_units(2000, 18)

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

    try:
        order = await market.create_order()
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


