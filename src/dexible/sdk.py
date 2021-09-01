from enum import Enum
from .common import Contact, Reports
from .token import TokenSupport
from .order import OrderWrapper
from .quote import QuoteWrapper
from .algo import AlgoWrapper


class DexibleSDK:
    class GasPolicyTypes(Enum):
        RELATIVE = "relative"
        FIXED = "fixed"

    def __init__(self, provider, account, chain_id,
                 network='ethereum', aio=True, *args, **kwargs):
        self.account = account
        self.provider = provider
        self.chain_id = chain_id

        if aio:
            from .apiclient_aio import APIClient
        else:
            from .apiclient import APIClient

        self.api_client = APIClient(chain_id=chain_id,
                                    network=network,
                                    account=account)
        self.algo = AlgoWrapper()
        self.token = TokenSupport(provider=provider,
                                  account=account,
                                  api_client=self.api_client,
                                  chain_id=chain_id)
        self.order = OrderWrapper(self.api_client)
        self.quote = QuoteWrapper(self.api_client)
        self.contact = Contact(self.api_client)
        self.reports = Reports(self.api_client)

        super(DexibleSDK, self).__init__(*args, **kwargs)

    @staticmethod
    async def create(web3_object):
        account = web3_object.eth.account
        provider = web3_object.provider
        chain_id = web3_object.eth.chain_id
        return DexibleSDK(provider, account, chain_id)


class Dexible:
    @staticmethod
    async def connect(web3_object=None, wallet_key=None, account=None, provider=None):
        if web3_object is None:
            if provider is None:
                provider = web3.providers.AutoProvider()
            if account is None:
                if wallet_key is None:
                    raise Exception("If not providing an Account implementation, must supply a wallet key")
                account = web3.Account.from_key(web3.Web3.toBytes(hexstr=key))
            web3_object = web3.Web3(provider)
            web3_object.middleware_onion.add(
                construct_sign_and_send_raw_middleware(account))
            web3_object.eth.default_account = account.address

        sdk = await DexibleSDK.create(web3_object)
        return Dexible(sdk)

    def __init__(self, sdk):
        self.sdk = sdk
        self.get_quote = sdk.quote.get_quote

    async def resolve_tokens(self, token_address_in, token_address_out):
        t1 = await self.sdk.token.lookup(token_address_in)
        t2 = await self.sdk.token.lookup(token_address_out)
        return {"token_in": t1,
                "token_out": t2}

    async def approve(self, token, amount=None, infinite=None):
        if amount is None:
            if infinite is None:
                raise Exception("Must either provide a fixed spend allowance set the infinite flag for infinite approval")
            amount = 2 ** 256 - 1
        return await self.sdk.token.increase_spending(token=token, amount=amount)

    async def limit(self, *args, **kwargs):
        return await Order.create(type=AlgoWrapper.types.Limit,
                            sdk=self.sdk,
                            *args,
                            **kwargs)

    async def market(self, *args, **kwargs):
        return await Order.create(type=AlgoWrapper.types.Market,
                            sdk=self.sdk,
                            *args,
                            **kwargs)

    async def stop_loss(self, *args, **kwargs):
        return await Order.create(type=AlgoWrapper.types.StopLoss,
                            sdk=self.sdk,
                            *args,
                            **kwargs)

    async def twap(self, *args, **kwargs):
        return await Order.create(type=AlgoWrapper.types.TWAP,
                            sdk=self.sdk,
                            *args,
                            **kwargs)

class Order:
    order = None

    @staticmethod
    async def create(*args, **kwargs):
        o = Order(*args, **kwargs)
        await o._prepare()
        return o.order

    def __init__(self, *args, **kwargs):
        try:
            _type = kwargs.pop("type")
            self.sdk = kwargs.pop("sdk")
        except KeyError:
            raise Exception("'sdk' and 'type' parameters required")
        self.tags = kwargs.get("tags", [])
        self.max_rounds = kwargs.get("max_rounds")

        try:
            self.token_in = kwargs.pop("token_in")
        except:
            raise Exception("'token_in' parameter required")

        try:
            self.token_out = kwargs.pop("token_out")
        except:
            raise Exception("'token_out' parameter required")

        try:
            self.amount_in = kwargs.pop("amount_in")
        except:
            raise Exception("'amount_in' parameter required")

        if 'gas_policy' not in kwargs:
            raise Exception("'gas_policy' parameter required")

        if 'slippage_percent' not in kwargs:
            raise Exception("'slippage_percent' parameter required")

        self.algo_wrapper = AlgoWrapper()
        self._build_base_polices = self.algo_wrapper._build_base_polices

        if _type in [self.sdk.algo.types.Limit,
                     self.sdk.algo.types.Limit.value]:
            self.algo = self.algo_wrapper.create_limit(*args, **kwargs)
        elif _type in [self.sdk.algo.types.Market,
                     self.sdk.algo.types.Market.value]:
            self.algo = self.algo_wrapper.create_market(*args, **kwargs)
        elif _type in [self.sdk.algo.types.StopLoss,
                     self.sdk.algo.types.StopLoss.value]:
            self.algo = self.algo_wrapper.create_stop_loss(*args, **kwargs)
        elif _type in [self.sdk.algo.types.TWAP,
                     self.sdk.algo.types.TWAP.value]:
            self.algo = self.algo_wrapper.create_twap(*args, **kwargs)
        else:
            raise DexibleAlgoException(f"Unsupported algorithm type: {_type}")

    async def submit(self):
        if not self.order:
            await self._prepare()
        return self.order.submit()

    async def _prepare(self):
        if not self.algo:
            raise Exception("No algo in order")
        r = await self.sdk.order.prepare(
            algo=self.algo,
            amount_in=self.amount_in,
            token_in=self.token_in,
            token_out=self.token_out,
            tags=self.tags)
        self.order = r;
