from ton import TonClient
from config.settings import settings

# Define token contract addresses for TON
USDT_CONTRACT = "Ton... (TON USDT contract address)"
USDC_CONTRACT = "Ton... (TON USDC contract address)"
DAI_CONTRACT = "Ton... (TON DAI contract address)"

class TONAdapter:
    def __init__(self):
        self.client = TonClient(settings.BLOCKCHAINS['TON']['rpc'])
    
    def get_transactions(self, start_block, end_block):
        block_range = self.client.get_block_range(start_block, end_block)
        return [{
            'hash': tx['hash'],
            'to': tx['to'],
            'value': tx['value'],
            'currency': self._detect_token_currency(tx),
            'block': tx['blockNumber']
        } for tx in block_range]
    
    def _detect_token_currency(self, tx):
        if tx['to'] == USDT_CONTRACT:
            return 'USDT'
        elif tx['to'] == USDC_CONTRACT:
            return 'USDC'
        elif tx['to'] == DAI_CONTRACT:
            return 'DAI'
        return 'TON'  # Default is TON (TON native token)