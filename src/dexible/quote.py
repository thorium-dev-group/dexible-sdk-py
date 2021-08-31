class QuoteWrapper:
    api_client = None

    def __init__(self, api_client):
        self.api_client = api_client

    async def get_quote(self, token_in, token_out, amount_in, slippage_percent,
                        max_rounds=None, max_fixed_gas=None, fixed_price=None):
        return await get_quote(api_client=self.api_client,
                               token_in=token_in,
                               token_out=token_out,
                               amount_in=amount_in,
                               slippage_percent=slippage_percent,
                               max_rounds=max_rounds,
                               max_fixed_gas=max_fixed_gas,
                               fixed_price=fixed_price)


async def get_quote(api_client, token_in, token_out, amount_in,
                    slippage_percent, max_rounds=None, min_order_size=-1,
                    max_fixed_gas=None, fixed_price=None):
    if max_rounds:
        min_order_size //= max_rounds
        if min_order_size < 1:
            min_order_size = amount_in * 30 // 100

    quote_body = {
        "amountIn": str(amount_in),
        "networkId": api_client.chain_id,
        "tokenIn": token_in.address,
        "tokenOut": token_out.address,
        "minOrderSize": str(min_order_size),
        "slippagePercentage": slippage_percent / 100}

    if max_fixed_gas:
        quote_body["maxFixedGas"] = max_fixed_gas
    if fixed_price:
        quote_body['fixedPrice'] = fixed_price

    return await api_client.post("quotes", data=quote_body)
