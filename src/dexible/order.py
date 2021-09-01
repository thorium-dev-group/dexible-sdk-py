import logging
from .common import Token
from .quote import get_quote
from .algo import DexibleBaseAlgorithm
from .exceptions import (InvalidOrderException,
                         OrderIncompleteException,
                         QuoteMissingException)

log = logging.getLogger('DexOrder')


class DexOrder:
    api_client = None
    token_in = None
    token_out = None
    amount_in = None
    algo = None
    max_rounds = None
    tags = []
    fee = 0
    quote = None

    def __init__(self, api_client, token_in, token_out, amount_in,
                 algo, max_rounds, tags=[], quote_id=0):
        self.api_client = api_client
        self.token_in = token_in
        self.token_out = token_out
        self.amount_in = amount_in
        self.algo = algo
        self.max_rounds = max_rounds
        self.tags = tags
        self.quote_id = quote_id

    def serialize(self):
        if self.quote_id == 0:
            raise OrderIncompleteException("No quote found to serialize order")

        algo_serialized = self.algo.serialize()

        return {
            "tokenIn": self.token_in.address,
            "tokenOut": self.token_out.address,
            "quoteId": self.quote_id,
            "amountIn": str(self.amount_in),
            "networkId": self.api_client.chain_id,
            "policies": algo_serialized["policies"],
            "algorithm": algo_serialized["algorithm"],
            "tags": self.tags
        }

    def verify(self):
        if self.algo is None:
            return "Order is missing algo"

        # make sure all algos are good
        log.debug("Verifying algorithm properties...")
        err = self.algo.verify()
        if err is not None:
            log.error(f"Problem with algo: {err}")
            return err

        if self.quote_id in [None, 0]:
            log.error("Missing quote id")
            return "Must prepare order before submitting"

        if not self.token_in.balance:
            log.error("Input token has no balance")
            return "Input token is missing a balance"

        if not self.token_in.allowance:
            log.error("Input token has no allowance")
            return "Input token is missing allowance"

        if self.token_in.balance < self.amount_in:
            log.error("In token balance will not cover trade")
            return "Insufficient token balance for trade"

        if self.token_in.allowance < self.amount_in:
            log.error("Token allowance will not cover trade")
            return "Insufficient token allowance for trade"

        log.debug("Surface-level order verification looks ok")

        return None

    async def prepare(self):
        log.debug("Preparing order for submission")
        slippage = self.algo.get_slippage()
        if not slippage:
            raise InvalidOrderException("Missing slippage amount",
                                        json_response=slippage)
        if not self.quote:
            if not self.quote_id:
                await self._generate_quote(slippage)
            else:
                await self._get_quote()

        err = self.verify()

        if err is not None:
            raise InvalidOrderException(err, json_response=err)
        return self

    async def _get_quote(self):
        try:
            self.quote = await self.api_client.get(f"quotes/{self.quote_id}")
        except Exception as e:
            log.error(f"Could not get quote by id: {e}")
            raise

    async def _generate_quote(self, slippage_percent):
        log.debug("Generating a default quote...")
        min_per_round = self.amount_in * 30 // 100
        if self.max_rounds:
            min_per_round = self.amount_in // self.max_rounds

        quotes = await get_quote(self.api_client,
                                 self.token_in,
                                 self.token_out,
                                 self.amount_in,
                                 slippage_percent,
                                 max_rounds=self.max_rounds,
                                 min_order_size=min_per_round)

        if quotes and type(quotes) == list and len(quotes) > 0:
            log.debug("Have quote result")
            # quotes array should have single-round and recommended quotes
            single = quotes[0]
            best = None

            if len(quotes) > 1:
                best = quotes[1]
            else:
                best = single

            if best is None:
                raise QuoteMissingException(
                    "Could not generate a quote for order",
                    json_response=quotes)

            # pick the recommended
            self.quote_id = best["id"]
            self.quote = best

        else:
            log.error(f"No quote returned from server: {quotes}")
            raise QuoteMissingException(
                f"Could not generate quote for order: {quotes}",
                json_response=quotes)
        return quotes

    async def submit(self):
        log.debug("Verifying order...")
        err = self.verify()
        if err:
            log.error("Problem found during verification", err)
            raise InvalidOrderException(err, json_response=err)

        serialized = self.serialize()
        log.debug(f"Sending raw order details: {serialized}")
        return await self.api_client.post("orders", serialized)

    def toJSON(self):
        return {
            "tokenIn": self.token_in,
            "tokenOut": self.token_out,
            "amountIn": self.amount_in,
            "algo": self.algo,
            "quoteId": self.quote_id,
            "quote": self.quote,
            "maxRounds": self.max_rounds,
            "tags": self.tags
        }

    def __str__(self):
        has_quote = self.quote_id > 0
        quote_str = "No quote"
        if has_quote:
            quote_str = f"{self.quote}"
        return f"<Order in: {self.amount_in} {self.token_in}, " \
            f"out: {self.token_out}, max_rounds: {self.max_rounds}, " \
            f"algo: {self.algo}, tags: {self.tags}, quote: {quote_str}>"
    __repr__ = __str__


class OrderWrapper:
    api_client = None

    def __init__(self, api_client):
        self.api_client = api_client

    async def prepare(self,
                      token_in: Token,
                      token_out: Token,
                      amount_in: int,
                      algo: DexibleBaseAlgorithm,
                      tags: list):
        order = DexOrder(api_client=self.api_client,
                         token_in=token_in,
                         token_out=token_out,
                         amount_in=amount_in,
                         algo=algo,
                         max_rounds=algo.max_rounds,
                         tags=tags)
        return await order.prepare()

    async def get_all(self, limit=100, offset=0, state="all"):
        assert(state in ["all", "active"])
        return await self.api_client.get(
            f"orders?limit={limit}&offset={offset}&state={state}")

    async def get_one(self, id):
        return await self.api_client.get(f"orders/{id}")

    async def cancel(self, id):
        return await self.api_client.post(f"orders/{id}/actions/cancel",
                                          {"orderId": id})

    async def pause(self, id):
        return await self.api_client.post(f"orders/{id}/actions/pause",
                                          {"orderId": id})

    async def resume(self, id):
        return await self.api_client.post(f"orders/{id}/actions/resume",
                                          {"orderId": id})
