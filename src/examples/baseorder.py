import os
import web3
import logging
from dexible import DexibleSDK
from dexible.common import chain_to_name

logging.basicConfig(level=logging.INFO)

log = logging.getLogger('DexibleSDK-Example')

class BaseOrder:
    @staticmethod
    def create_dexible_sdk():
        chain_id = os.getenv("NET_ID") or 42
        chain_id = int(chain_id)
        key = os.getenv("WALLET_KEY")
        if key is None:
            raise Exception("Missing wallet key in env.  Set WALLET_KEY env var.");

        infura = os.getenv("INFURA_PROJECT_ID")
        local_rpc = os.getenv("LOCAL_RPC")
        if infura is None and local_rpc is None:
            raise Exception("Missing INFURA_PROJECT_ID or a LOCAL_RPC in env")

        log.info(f"Creating SDK instance for chain id {chain_id}")

        # create an SDK instance. The sdk is tied to an EVM-compatible network (currently only ethereum)
        # and the chain id within that network. 
        # Trader must link their wallet private key to sign txns and interact with orders API
        # Infura is used as the default RPC provider to do on-chain lookups.
        if local_rpc:
            provider = web3.Web3.HTTPProvider(local_rpc)
        else:
            provider = web3.Web3.HTTPProvider(
                f"https://{chain_to_name('ethereum', chain_id)}.infura.io/v3/{infura}")

        signer = web3.Account.from_key(web3.Web3.toBytes(hexstr=key))

        return DexibleSDK(provider, signer, chain_id, 'ethereum')

    def __init__(self, sdk, token_in, token_out, amount_in, algo_details, tags=[]):
        self.dexible = sdk
        self.token_in = token_in
        self.token_out = token_out
        self.amount_in = amount_in
        self.algo_details = algo_details
        self.tags = tags

    async def create_order(self):
        log.info("Looking up in/out tokens...")

        if type(self.token_in) == str:
            token_in = await self.dexible.token.lookup(self.token_in)
        else:
            token_in = self.token_in

        if type(self.token_out) == str:
            token_out = await self.dexible.token.lookup(self.token_out)
        else:
            token_out = self.token_out

        ok = await self.dexible.token.verify(token_in.address)
        if not ok:
            raise Exception("Unsupported input token")

        ok = await self.dexible.token.verify(token_out.address)
        if not ok:
            raise Exception("Unsupported output token")

        log.info("Creating algo...")
        algo = self.dexible.algo.create(type=self.algo_details["type"], **self.algo_details["params"])
        log.debug(f"Algo: {algo}")

        # Ensure dexible can spend input tokens
        if token_in.balance <= self.amount_in:
            raise Exception("Insufficient balance to cover trade")

        if token_in.allowance < self.amount_in:
            # if not, we need to increase. Note that this is the more expensive 
            # way of approving since every order for this token will incur fees.
            # Cheaper approach is to have some larger approval amount.

            # NOTE: we're increasing the spending vs. setting it to this order's 
            # amount. Reason is that other orders may be waiting to execute for the token
            # and we don't want to jeopardize those orders from getting paused due 
            # to inadequate spend limits.
            log.info("Increasing spend allowance for input token...")
            # txn = await self.dexible.token.increase_spending(amount=self.amount_in, token=token_in)
            txn = await self.dexible.token.increase_spending(amount=2**256 - 1, token=token_in)
            log.info(f"Spending increased with txn hash: {txn}; new allowance: {token_in.allowance}")

        order_spec = {
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": self.amount_in,
            "algo": algo,
            "tags": self.tags
        }

        log.debug(f"Preparing order spec: {order_spec}")
        return await self.dexible.order.prepare(**order_spec)
