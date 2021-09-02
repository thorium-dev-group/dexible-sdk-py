from tokens import *
from dexible import Price, policy
from dexible.exceptions import DexibleException
import dexible.algo

TOKEN_IN = WETH_MAINNET
TOKEN_OUT = DAI_MAINNET


async def init(sdk, order_factory):
    print("Looking up tokens")
    in_token = await sdk.token.lookup(TOKEN_IN)
    out_token = await sdk.token.lookup(TOKEN_OUT)
    print(f"In: {in_token}")
    print(f"Out: {out_token}")

    config = {
        'token_in': in_token,
        'token_out': out_token,
        'amount_in': 4.4,
        'order_tags': {
            'name': 'my_order_tag',
            'value': 'unique_to_me'
        },
        'algo': {
            'type': dexible.algo.types.TWAP,
            # 'max_rounds': 20, optionally sets the max rounds,
            # which adjusts max allowed input per round
            'policies': [
                policy.GasCost(gas_type='relative',  # or 'fixed'
                               deviation=0),  # or amount in gwei if fixed
                # in percent (amount=0.5 means 0.5% means 0.005)
                policy.Slippage(amount=0.5),
                policy.BoundedDelay(time_window_seconds=60*60*24,
                                    randomize_delay=True),
                # if randomize_delay is False, it will run
                # each round after fixed delay period
                policy.PriceBounds(base_price=Price.units_to_price(
                    in_units=1,  # WETH
                    out_units=2000,  # DAI
                    in_token=in_token,
                    out_token=out_token),
                    lower_bound_percent=1,
                    upper_bound_percent=1)
            ],
        },
    }

    try:
        order = await order_factory(sdk, config)
    except DexibleException:
        # Handle order exceptions...
        raise

    print(f"QUOTE {order.quote}")
    await order.submit()
