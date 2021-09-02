import sys
import web3
import asyncio
from dexible import DexibleSDK, as_units
import dexible.algo

from importlib import import_module
from dexible.common import chain_to_name

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    print("Note: python-dotenv is not installed, .env won't be imported")
from config import CONFIG

async def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <order-template-name>")
        sys.exit(1)

    template = sys.argv[1]
    if 'infura_id' not in CONFIG:
        CONFIG['infura_id'] = None
    if 'rpc' not in CONFIG:
        CONFIG['rpc'] = None

    if CONFIG['infura_id'] is None and CONFIG['rpc'] is None:
        print("Must provide an infura id or rpc endpoint for web3 provider in setup config (see setup.py)");
        sys.exit(1)

    if 'chain_id' not in CONFIG or CONFIG['chain_id'] is None:
        CONFIG['chain_id'] = 1 

    if 'wallet' not in CONFIG or CONFIG['wallet'] is None:
        print("Must provide a wallet in sdk setup config")
        sys.exit(1)

    if CONFIG['infura_id'] is not None:
        chainname = chain_to_name('ethereum', CONFIG['chain_id'])
        provider = web3.Web3.HTTPProvider(
            f"https://{chainname}.infura.io/v3/{CONFIG['infura_id']}")
    else:
        provider = web3.Web3.HTTPProvider(CONFIG['rpc'])

    account = web3.Account.from_key(web3.Web3.toBytes(hexstr=CONFIG['wallet']))

    sdk = DexibleSDK(provider, account, CONFIG['chain_id'], 'ethereum')

    module = import_module(template)

    await module.init(sdk, order_factory)

async def order_factory(sdk, config):
    token_in = config['token_in']
    token_out = config['token_out']
    if not token_in or not token_out:
        print("Must supply input and output token instances")
        sys.exit(1)
    if not token_in.decimals or not token_out.decimals:
        print("Must use tokens that were looked up using the sdk instance")
        sys.exit(1)
    if 'algo' not in config or 'type' not in config['algo']:
        print("Missing algo or algo['type'] properties in config")
        sys.exit(1)

    amount_in = as_units(config['amount_in'], token_in.decimals)
    algo_type = config['algo'].pop('type')
    if algo_type == dexible.algo.AlgoWrapper.types.Limit:
        algo_class = dexible.algo.Limit
    elif algo_type == dexible.algo.AlgoWrapper.types.Market:
        algo_class = dexible.algo.Market
    elif algo_type == dexible.algo.AlgoWrapper.types.StopLoss:
        algo_class = dexible.algo.StopLoss
    elif algo_type == dexible.algo.AlgoWrapper.types.TWAP:
        algo_class = dexible.algo.TWAP
    else:
        print(f"Unsupported algo type {algo_type}")
        sys.exit(1)

    algo = algo_class(**config['algo'])
    bal = token_in.balance or 0
    allow = token_in.allowance or 0

    print("Checking single-order token balance...")
    if bal < amount_in:
        raise Exception("Insufficient token balance to trade")
    else:
        print("Token balance looks good")

    print("Checking single-order spend allowance...")
    if allow < amount_in:
        if CONFIG['automatic_spend_approval']:
            print("Approving infinite spend on input token...")
            if CONFIG['use_infinite_spend_approval']:
                await sdk.token.increase_spending(
                    token=token_in,
                    amount=2**256-1)
            else:
                await sdk.token.increase_spending(
                    token=token_in,
                    amount=amount_in)
        else:
            raise Exception("Insufficient spend allowance for input token, and automatic_spend_approval not set in config")
    else:
        print("Single-order spend allowance good")
        print("Preparing and validating order....")
        order = await sdk.order.prepare(
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            algo=algo,
            tags=config['order_tags'])
        return order

if __name__ == '__main__':
    asyncio.run(main())