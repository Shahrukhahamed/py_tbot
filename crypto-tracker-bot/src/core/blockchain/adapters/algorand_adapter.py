from algosdk.v2 import algod
from config.settings import settings

# Define the token contract addresses for Algorand
USDT_CONTRACT = "Algorand... (USDT contract address)"
USDC_CONTRACT = "Algorand... (USDC contract address)"
DAI_CONTRACT = "Algorand... (DAI contract address)"

class AlgorandAdapter:
    def __init__(self):
        self.client = algod.AlgodClient(settings.BLOCKCHAINS['Algorand']['api_key'], settings.BLOCKCHAINS['Algorand']['rpc'])
    
    def get_transactions(self, start_block, end_block):
        block_range = self.client.block_range(start_block, end_block)
        return [{
            'hash': tx['txid'],
            'to': tx['payment']['to'],
            'value': tx['payment']['amount'],
            'currency': self._detect_token_currency(tx),
            'block': tx['block']
        } for tx in block_range.transactions]
    
    def _detect_token_currency(self, tx):
        if tx['payment']['to'] == USDT_CONTRACT:
            return 'USDT'
        elif tx['payment']['to'] == USDC_CONTRACT:
            return 'USDC'
        elif tx['payment']['to'] == DAI_CONTRACT:
            return 'DAI'
        return 'ALGO'  # Default is ALGO (Algorand's native token)