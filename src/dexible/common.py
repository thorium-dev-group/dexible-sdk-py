from decimal import Decimal
from .exceptions import DexibleException


def chain_to_name(network, chain_id):
    if network != 'ethereum':
        raise DexibleException("Only support ethereum right now")

    if chain_id == 1:
        return "mainnet"
    elif chain_id == 3:
        return "ropsten"
    elif chain_id == 4:
        return "rinkeby"
    elif chain_id == 42:
        return "kovan"
    else:
        raise DexibleException(
            "Only mainnet and kovan are supported right now")


CHAIN_CONFIG = {
    1: {
        "Multicall": "0xeefBa1e63905eF1D7ACbA5a8513c70307C1cE441",
        "Settlement": "0xad84693a21E0a1dB73ae6c6e5aceb041A6C8B6b3"
    },
    3: {
        "Settlement": "0x18b534C7D9261C2af0D65418309BA2ABfc4b682d",
        "Multicall": "0x53c43764255c17bd724f74c4ef150724ac50a3ed"
    },
    42: {
        "Settlement": "0x147bFD9cEffcd58A2B2594932963F52B16d528b1",
        "Multicall": "0x2cc8688c5f75e365aaeeb4ea8d6a480405a48d2a"
    }
}


class Token:
    address: str
    decimals: int
    symbol: str
    balance: int
    allowance: int

    def __init__(self, address, decimals, symbol, balance, allowance):
        self.address = address
        self.decimals = decimals
        self.symbol = symbol
        self.balance = balance
        self.allowance = allowance

    def __str__(self):
        return f"<Token {self.symbol} {self.address}" \
            f" decimals: {self.decimals}," \
            f" balance: {self.balance}, " \
            f"allowance: {self.allowance}>"
    __repr__ = __str__


class Contact:
    api_client = None

    def __init__(self, api_client):
        self.api_client = api_client

    async def add(self, email):
        return await self.api_client.post("contact-method/create", data={
            "identifier": email,
            "contact_method": "email"})

    async def get_all(self):
        return await self.api_client.get("contact-method")

    async def toggle(self, id):
        return await self.api_client.post(
            f"contact-method/toggle/{id}", data={"id": id})


class Reports:
    api_client = None

    def __init__(self, api_client):
        self.api_client = api_client

    async def get_summary(self, start, end):
        return await self.api_client.post("report/order_summary/csv", data={
            "startDate": start.total_seconds(),
            "endDate": end.total_seconds()})

    async def get_all(self):
        return await self.api_client.get("contact-method")

    async def toggle(self, id):
        return await self.api_client.post(
            f"contact-method/toggle/{id}", data={"id": id})


def as_units(numberish, unit="ether"):
    """
    Similar to ethers.utils.parseUnits( value [ , unit = "ether" ] ) ⇒ BigNumber, but pythonic

    Takes a numberish and optionally a unit and returns an integer (wei) representation of the Decimal
    """
    if unit == "ether":
        unit = 18
    return int(Decimal(numberish) * 10 ** unit)


def as_decs(numberish, unit="ether"):
    """
    Similar to ethers.utils.formatUnits( value [ , unit = "ether" ] ) ⇒ string, but pythonic

    Takes a numberish (in wei) and optionally a unit and returns a Decimal representation of the value
    """
    if unit == "ether":
        unit = 18
    return Decimal(numberish) / 10**unit


class Price:
    @staticmethod
    def units_to_price(in_token, out_token, in_units, out_units):
        return Price(in_token,
                     out_token,
                     as_units(round(in_units, in_token.decimals)),
                     as_units(round(out_units, out_token.decimals)))

    def __init__(self, in_token, out_token, in_amount, out_amount):
        self.in_token = in_token
        self.out_token = out_token
        self.in_amount = in_amount
        self.out_amount = out_amount

        in_units = +as_decs(self.in_amount, self.in_token.decimals)
        out_units = +as_decs(self.out_amount, self.out_token.decimals)
        self.rate = out_units / in_units

    def inverse(self):
        return Price(self.out_token,
                     self.in_token,
                     self.out_amount,
                     self.in_amount)

    def to_fixed(self, digits):
        return round(self.rate, digits)

    def to_string(self):
        return round(self.rate,
                     min(self.in_token.decimals, self.out_token.decimals))

    def toJSON(self):
        return {
            "inToken": {"address": self.in_token.address,
                        "symbol": self.in_token.symbol,
                        "decimals": self.in_token.decimals},
            "outToken": {"address": self.out_token.address,
                         "symbol": self.out_token.symbol,
                         "decimals": self.out_token.decimals},
            "inAmount": str(self.in_amount),
            "outAmount": str(self.out_amount)
        }

    def __str__(self):
        return f"<Price token in: {self.in_token}, " \
            f"token out: {self.out_token}, in amount: {self.in_amount}, " \
            f"out amount: {self.out_amount}, (rate: {self.rate})>"
    __repr__ = __str__
