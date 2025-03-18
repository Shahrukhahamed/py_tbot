from nearpy import Near
from config.settings import settings

# Define token contract addresses for NEAR
USDT_CONTRACT = "NEAR... (USDT contract address)"
USDC_CONTRACT = "NEAR... (USDC contract address)"
DAI_CONTRACT = "NEAR... (DAI contract address)"

class NearAdapter:
    def __init__(self):
        self.near = Near.connect(settings.BLOCKCHAINS['Near']['rpc'])
    
    def get_transactions(self, start_block, end_block):
        block_range = self.near.get_block_range(start_block, end_block)
        return [{
            'hash': tx['hash'],
            'to': tx['receiver_id'],
            'value': tx['actions'][0]['transfer']['amount'],
            'currency': self._detect_token_currency(tx),
            'block': tx['block']
        } for tx in block_range.transactions]
    
    def _detect_token_currency(self, tx):
        if tx['receiver_id'] == USDT_CONTRACT:
            return 'USDT'
        elif tx['receiver_id'] == USDC_CONTRACT:
            return 'USDC'
        elif tx['receiver_id'] == DAI_CONTRACT:
            return 'DAI'
        return 'NEAR'  # Default is NEAR (NEAR native token)