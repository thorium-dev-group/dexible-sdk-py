import web3
import time
import eth_abi.exceptions
from web3.middleware import construct_sign_and_send_raw_middleware
from .abi import ERC20_ABI, MULTICALL_ABI
from .common import CHAIN_CONFIG, Token
from .exceptions import *

class TokenException(Exception):
    pass


class TokenHelper:
    cache = {}

    async def find(self, provider, chain_id, address, owner=None):
        if address.lower() in self.cache:
            return self.cache[address.lower()]
        try:
            info = await self.get_info(provider,
                                       chain_id,
                                       address,
                                       owner=owner)
        except eth_abi.exceptions.InsufficientDataBytes:
            raise TokenException(f"Can't resolve token at {address}")

        token = Token(address=address, **info)
        self.cache[address.lower()] = token
        return token

    async def get_info(self, provider, chain_id, address, owner=None):
        w3 = web3.Web3(provider)
        erc20 = w3.eth.contract(abi=ERC20_ABI)  # Generic ERC20 Contract
        # Multicall contract address
        mc_adddress = CHAIN_CONFIG[chain_id]["Multicall"]
        # Settlement contract address
        settlement_address = CHAIN_CONFIG[chain_id]["Settlement"]
        # Multicall contract on chain
        multicall = w3.eth.contract(abi=MULTICALL_ABI,
                                    address=w3.toChecksumAddress(mc_adddress))

        calls = [{"abi": ERC20_ABI,
                  "contract": erc20,
                  "address": address,
                  "method": "decimals",
                  "args": [],
                  "target": "decimals"},
                 {"abi": ERC20_ABI,
                  "contract": erc20,
                  "address": address,
                  "method": "symbol",
                  "args": [],
                  "target": "symbol"}]
        if owner:
            calls.append(
                {"abi": ERC20_ABI,
                 "contract": erc20,
                 "address": address,
                 "method": "balanceOf",
                 "args": [owner],
                 "target": "balance"})
            calls.append(
                {"abi": ERC20_ABI,
                 "contract": erc20,
                 "address": address,
                 "method": "allowance",
                 "args": [owner, settlement_address],
                 "target": "allowance"})

        results = multicall.functions.aggregate(
            [[w3.toChecksumAddress(c["address"]),
              c["contract"].encodeABI(fn_name=c["method"],
                                      args=c["args"])]
             for c in calls]
        ).call()

        callnr = 0
        returndict = {}
        for call in calls:
            fn_abi = web3._utils.contracts.find_matching_fn_abi(
                call["abi"], w3.codec, call["method"], call["args"])
            output_types = web3._utils.abi.get_abi_output_types(fn_abi)
            decoded = w3.codec.decode_abi(output_types, results[1][callnr])

            call["result"] = decoded
            returndict[call["target"]] = call["result"][0]
            callnr += 1

        return returndict

    async def increase_spending(self, provider, chain_id,
                                account, token, amount):
        w3 = web3.Web3(provider)
        w3.middleware_onion.add(
            construct_sign_and_send_raw_middleware(account))
        w3.eth.default_account = account.address
        token_contract = w3.eth.contract(
            abi=ERC20_ABI,
            address=w3.toChecksumAddress(token.address))
        # Settlement contract address
        settlement_address = CHAIN_CONFIG[chain_id]["Settlement"]
        return web3.eth.to_hex(
            token_contract.functions.approve(
                settlement_address, amount).transact())

    def invalidate_cache_for(self, address):
        if address.lower() in self.cache:
            del self.cache[address.lower()]


class TokenSupport:
    address = None

    def __init__(self, account, provider, api_client, chain_id):
        self.account = account
        self.provider = provider
        self.api_client = api_client
        self.chain_id = chain_id
        self.tokenhelper = TokenHelper()

    async def lookup(self, address):
        try:
            r = await self.verify(address)
            if not r:
                raise DexibleException(f"Bad status code: {r}")
        except:
            raise DexibleException("Unsupported token address: " + address)

        if self.address is None:
            self.address = self.account.address

        return await self.tokenhelper.find(provider=self.provider,
                                           chain_id=self.chain_id,
                                           address=address,
                                           owner=self.address)

    async def increase_spending(self, token, amount):
        tx_id = await self.tokenhelper.increase_spending(
            provider=self.provider,
            chain_id=self.chain_id,
            account=self.account,
            token=token,
            amount=amount)
        w3 = web3.Web3(self.provider)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_id)
        if not tx_receipt.status:
            raise Exception("Allowance transaction failed.")
        # Wait for 30s to allow network to propagate, as with original sdk
        time.sleep(30)
        token.allowance = amount
        self.tokenhelper.invalidate_cache_for(token.address)
        return tx_id

    async def verify(self, address):
        return await self.api_client.get(
            f"token/verify/{self.chain_id}/{address}")
