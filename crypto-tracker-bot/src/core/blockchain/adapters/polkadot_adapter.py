from polkadot import Polkadot
from config.settings import settings

# Define token contract addresses for Polkadot
USDT_CONTRACT = "Polkadot... (USDT contract address)"
USDC_CONTRACT = "Polkadot... (USDC contract address)"
DAI_CONTRACT = "Polkadot... (DAI contract address)"

class PolkadotAdapter:
    def __init__(self):
        self.polkadot = Polkadot.connect(settings.BLOCKCHAINS['Polkadot']['rpc'])
    
    def get_transactions(self, start_block, end_block):
        block_range = self.polkadot.get_block_range(start_block, end_block)
        return [{
            'hash': tx['hash'],
            'to': tx['recipient'],
            'value': tx['amount'],
            'currency': self._detect_token_currency(tx),
            'block': tx['block_number']
        } for tx in block_range.transactions]
    
    def _detect_token_currency(self, tx):
        if tx['recipient'] == USDT_CONTRACT:
            return 'USDT'
        elif tx['recipient'] == USDC_CONTRACT:
            return 'USDC'
        elif tx['recipient'] == DAI_CONTRACT:
            return 'DAI'
        return 'DOT'  # Default is DOT (Polkadot's native token)