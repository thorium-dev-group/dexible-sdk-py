import os
import logging
import json
import aiohttp
import base64
import hashlib
from urllib.parse import urlparse
from datetime import datetime
from eth_account.messages import encode_defunct
from eth_utils.curried import to_bytes
from .common import chain_to_name
from .exceptions import DexibleException

log = logging.getLogger('APIClient')
DEFAULT_BASE_ENDPOINT = "api.dexible.io/v1";


class APIClient:
    SIGNATURE_PREFIX = "Signature "

    def __init__(self, signer, chain_id, network='ethereum', *args, **kwargs):
        self.signer = signer
        self.network = network
        self.chain_id = chain_id
        self.chain_name = chain_to_name(self.network, self.chain_id)
        self.base_url = self._build_base_url()
        log.debug(f"Created API client for chain {self.chain_name} on network {self.network}")

    def make_headers(self, url, method, data=None):
        headers = {}
        timestamp = datetime.utcnow()

        # Always replace Date, making sure signed timestamp is correct
        headers['Date'] = timestamp.isoformat()[:-3]+"Z" # Simulate JavaScript
        required_header_fields = ['Date']

        # Add content-type
        headers['Accept'] = 'application/json, text/plain, */*'
        headers['User-Agent'] = 'dexible-sdk-py'
        headers["Content-Type"] = "application/json"

        if data is not None:
            shadigest = base64.b64encode(
                hashlib.sha256(
                    to_bytes(text=data))
                .digest()).decode()
            headers['Digest'] = f"SHA-256={shadigest}"
            required_header_fields.append('Digest')

        headers['Authorization'] = self.SIGNATURE_PREFIX + \
            self.create_signature_string(url, headers, method, timestamp, required_header_fields)
        return headers

    def create_signature_string(self, url, headers, method, created_timestamp, required_header_fields):
        # expires_timestamp = None
        # if self.expires_in is not None:
        #     expires_timestamp = created_timestamp + self.expires_in.total_seconds()

        # public key
        key_id = self.signer.address

        # signature payload is assembled form of all headers being signed
        signing_string = self.build_signing_string(url, headers, method, required_header_fields)

        # It's common practice to wrap message signatures with a common
        # prefix to prevent users from accidentally pre-signing transactions
        # wrapped_signing_string = create_signable_message_geth(text=signing_string)
        # Workaround for js double wrapping:
        wrapped_signing_string = encode_defunct(self.double_wrap_as_in_upstream(text=signing_string))

        signature = self.signer.sign_message(wrapped_signing_string)

        # build the fully formed signature string
        signature_data = {
            "keyId": key_id,
            "algorithm": "keccak-256",
            "headers": " ".join(required_header_fields),
            "signature": signature.signature.hex()
        }
        
        # assemble signature value that will be embedded in Authorization header
        signature_line = self.build_signature_line(signature_data)
        
        return signature_line;

    @classmethod
    def build_signature_line(cls, params):
        # TODO: verify required params exist...
        return ",".join([f"{k}=\"{v}\"" for k, v in params.items()])

    @classmethod
    def build_signing_string(cls, url, headers, method, required_header_fields):
        urlparsed = urlparse(url)
        tohost = urlparsed.path
        if urlparsed.query:
            tohost += "?" + urlparsed.query

        to_sign = "(request-target): " + method.lower() + " " + tohost
        for header in required_header_fields:
            to_sign += "\n" + header.lower() + ": " + cls.get_header_value(headers, header)
        return to_sign

    @classmethod
    def get_header_value(cls, headers, header):
        if header in headers:
            return headers[header]
        elif header.lower() in headers:
            return headers[header.lower()]
        else:
            raise DexibleException(f"Header expected to exist and have value set: {header}")

    @staticmethod
    def double_wrap_as_in_upstream(primitive: bytes = None, *, hexstr: str = None, text: str = None):
        """
            This is essentially a compatibility layer to achieve the same behavior as with the js sdk.

            The original sdk prewraps the message with this string, before passing it to signMessage.
            signMessage additionally wraps the message in a simliar fashion: (quote from doc)
            
                signer.signMessage( message ) ⇒ Promise< string< RawSignature > >
                This returns a Promise which resolves to the Raw Signature of message.

                A signed message is prefixd with "\x19Ethereum signed message:\n" and the length of the
                message, using the hashMessage method, so that it is EIP-191 compliant. If recovering
                the address in Solidity, this prefix will be required to create a matching hash.

            This makes it important to double-wrap.

        """
        message_bytes = to_bytes(primitive, hexstr=hexstr, text=text)
        msg_length = str(len(message_bytes)).encode('utf-8')

        return b'\x19Ethereum Signed Message:\n' + msg_length + message_bytes

    async def get(self, endpoint):
        url = f"{self.base_url}/{endpoint}"
        log.debug(f"GET call to {url}")
        try:
            async with aiohttp.ClientSession(headers=self.make_headers(url, "get")) as session:
                async with session.get(url) as r:
                    json_body = await r.json()
                    if not json_body:
                        raise DexibleException("Missing result in GET request")
                    return json_body
        except Exception as e:
            log.error("Problem in APIClient GET request ", e)
            raise

    async def post(self, endpoint, data=None):
        url = f"{self.base_url}/{endpoint}"
        log.debug(f"POST call to {url}")
        try:
            if type(data) in [dict, list]:
                post_data = json.dumps(data)
            else:
                post_data = data
            log.debug(f"Posting data: {post_data}")

            async with aiohttp.ClientSession(headers=self.make_headers(url, "post", data=post_data)) as session:
                async with session.post(url, data=post_data) as r:
                    json_body = await r.json()
                    if not json_body:
                        raise DexibleException("Missing result in POST request")
                    return json_body
        except Exception as e:
            log.error("Problem in APIClient POST request ", e)
            raise

    def _build_base_url(self):
        base = os.getenv("API_BASE_URL") or f"https://{self.network}.{self.chain_name}.{DEFAULT_BASE_ENDPOINT}"
        return base;