import base64
import hashlib
from datetime import datetime
from urllib.parse import urlparse
from requests.auth import AuthBase
from eth_account.messages import encode_defunct
from eth_utils.curried import to_bytes
from .exceptions import DexibleException


class DexibleHttpSignatureAuth(AuthBase):
    SIGNATURE_PREFIX = "Signature "

    def __init__(self, account, expires_in=None):
        self.account = account
        if expires_in is not None:
            raise DexibleException("expires_in is currently unsupported")

    def __call__(self, r):
        timestamp = datetime.utcnow()

        # Always replace Date, making sure signed timestamp is correct
        # Simulate typical JavaScript behavior
        r.headers['Date'] = timestamp.isoformat()[:-3] + "Z"
        required_header_fields = ['Date']

        # Add content-type
        r.headers['Accept'] = 'application/json, text/plain, */*'
        r.headers['User-Agent'] = 'dexible-sdk-py'
        r.headers["Content-Type"] = "application/json"

        if r.body is not None:
            shadigest256 = base64.b64encode(
                hashlib.sha256(to_bytes(text=r.body)).digest()).decode()
            r.headers['Digest'] = f"SHA-256={shadigest256}"
            required_header_fields.append('Digest')

            # log.debug("DIGEST: " + r.headers['Digest'])

        r.headers['Authorization'] = self.SIGNATURE_PREFIX + \
            self.create_signature_string(r, timestamp, required_header_fields)

        return r

    def create_signature_string(self,
                                r,
                                created_timestamp,
                                required_header_fields):
        # expires_timestamp = None
        # if self.expires_in is not None:
        #     expires_timestamp = created_timestamp + self.expires_in.total_seconds()

        # public key
        key_id = self.account.address

        # signature payload is assembled form of all headers being signed
        signing_string = self.build_signing_string(r, required_header_fields)

        # It's common practice to wrap message signatures with a common
        # prefix to prevent users from accidentally pre-signing transactions
        # wrapped_signing_string = create_signable_message_geth(text=signing_string)
        # Workaround for js double wrapping:
        wrapped_signing_string = encode_defunct(
            self.double_wrap_as_in_upstream(text=signing_string))

        signature = self.account.sign_message(wrapped_signing_string)

        # build the fully formed signature string
        signature_data = {
            "keyId": key_id,
            "algorithm": "keccak-256",
            "headers": " ".join(required_header_fields),
            "signature": signature.signature.hex()
        }

        # assemble signature value that will be embedded in the
        # Authorization header
        signature_line = self.build_signature_line(signature_data)

        return signature_line

    @classmethod
    def build_signature_line(cls, params):
        # TODO: verify required params exist...
        return ",".join([f"{k}=\"{v}\"" for k, v in params.items()])

    @classmethod
    def build_signing_string(cls, request, required_header_fields):
        urlparsed = urlparse(request.url)
        tohost = urlparsed.path
        if urlparsed.query:
            tohost += "?" + urlparsed.query

        to_sign = "(request-target): " + request.method.lower() + " " + tohost
        for header in required_header_fields:
            to_sign += "\n" + header.lower() + \
                ": " + cls.get_header_value(request, header)
        return to_sign

    @classmethod
    def get_header_value(cls, request, header):
        if header in request.headers:
            return request.headers[header]
        elif header.lower() in request.headers:
            return request.headers[header.lower()]
        else:
            raise DexibleException(
                f"Header expected to exist and have value set: {header}")

    @staticmethod
    def double_wrap_as_in_upstream(primitive: bytes = None,
                                   *,
                                   hexstr: str = None,
                                   text: str = None):
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
