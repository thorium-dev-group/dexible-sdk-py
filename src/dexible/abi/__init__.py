import os
import json

DEXIBLE_ABI = None
ERC20_ABI = None
MULTICALL_ABI = None


__dir = os.path.dirname(__file__)

with open(os.path.join(__dir, 'Dexible.json'), 'r') as f:
	DEXIBLE_ABI = json.load(f)

with open(os.path.join(__dir, 'ERC20ABI.json'), 'r') as f:
	ERC20_ABI = json.load(f)

with open(os.path.join(__dir, 'Multicall.json'), 'r') as f:
	MULTICALL_ABI = json.load(f)
