from enum import Enum
from .common import Contact
from .token import TokenSupport
from .order import OrderWrapper
from .quote import QuoteWrapper
from .algo import AlgoWrapper


class DexibleSDK:
    class GasPolicyTypes(Enum):
        RELATIVE = "relative"
        FIXED = "fixed"

    def __init__(self, provider, signer, chain_id, network='ethereum', aio=True, *args, **kwargs):
        self.signer = signer
        self.provider = provider
        self.chain_id = chain_id

        if aio:
            from .apiclient_aio import APIClient
        else:
            from .apiclient import APIClient

        self.api_client = APIClient(chain_id=chain_id, network=network, signer=signer)

        self.algo = AlgoWrapper()
        self.token = TokenSupport(provider=provider, signer=signer, api_client=self.api_client, chain_id=chain_id)
        self.order = OrderWrapper(self.api_client)
        self.quote = QuoteWrapper(self.api_client)
        self.contact = Contact(self.api_client)

        super(DexibleSDK, self).__init__(*args, **kwargs)
