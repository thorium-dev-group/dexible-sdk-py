import os
import logging
import requests
import json
from .common import chain_to_name
from .dexible_http import DexibleHttpSignatureAuth

log = logging.getLogger('APIClient')

DEFAULT_BASE_ENDPOINT = "api.dexible.io/v1";

class APIClient:
    def __init__(self, signer, chain_id, network='ethereum', *args, **kwargs):
        self.signer = signer
        self.adapter = None
        self.network = network
        self.chain_id = chain_id
        self.chain_name = chain_to_name(self.network, self.chain_id)
        self.base_url = self._build_base_url()
        log.debug(f"Created api client for chain {self.chain_name} on network {self.network}")


    async def get(self, endpoint):
        url = f"{self.base_url}/{endpoint}"
        log.debug(f"GET call to {url}")
        try:
            if self.adapter is None:
                self.adapter = DexibleHttpSignatureAuth(self.signer)

            r = requests.get(url, auth=self.adapter)

            if not r.content:
                raise Exception("Missing result in GET request")

            return json.loads(r.content)
            # return r.content
        except Exception as e:
            log.error("Problem in APIClient GET request ", e)
            raise

    async def post(self, endpoint, data=None):
        url = f"{self.base_url}/{endpoint}"
        log.debug(f"POST call to {url}")
        try:
            if self.adapter is None:
                self.adapter = DexibleHttpSignatureAuth(self.signer)

            if type(data) in [dict, list]:
                post_data = json.dumps(data)
            else:
                post_data = data
            log.debug(f"Posting data: {post_data}")
            
            r = requests.post(url, data=post_data, auth=self.adapter)

            if not r.content:
                raise Exception("Missing result in POST request")

            return json.loads(r.content)
        except Exception as e:
            log.error("Problem in APIClient POST request ", e)
            raise

    def _build_base_url(self):
        base = os.getenv("API_BASE_URL") or f"https://{self.network}.{self.chain_name}.{DEFAULT_BASE_ENDPOINT}"
        return base