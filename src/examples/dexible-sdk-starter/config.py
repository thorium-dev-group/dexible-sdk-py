import os

CONFIG = {
    'chain_id': 1,
    'automatic_spend_approval': True,
    'use_infinite_spend_approval': True,
    'rpc': os.getenv("LOCAL_RPC"),  # Or None or "http://localhost:8545"
    'infura_id': os.getenv("INFURA_PROJECT_ID"),
    'wallet': os.getenv("WALLET_KEY")
}
