from web3 import Web3
from config.settings import settings

# Define token contract addresses for Base chain
BASE_USDT_CONTRACT = "0x0000000000000000000000000000000000000000"  # Replace with actual
BASE_USDC_CONTRACT = "0x0000000000000000000000000000000000000000"
BASE_DAI_CONTRACT = "0x0000000000000000000000000000000000000000"

class BaseAdapter:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAINS['Base']['rpc']))
    
    def get_transactions(self, start_block, end_block):
        block_range = self.w3.eth.get_block_range(start_block, end_block)
        return [{
            'hash': tx['hash'].hex(),
            'to': tx['to'],
            'value': self.w3.from_wei(tx['value'], 'ether'),
            'currency': self._detect_token_currency(tx),
            'block': tx['blockNumber']
        } for tx in block_range.transactions]
    
    def _detect_token_currency(self, tx):
        to_addr = (tx['to'] or '').lower()
        if to_addr == BASE_USDT_CONTRACT.lower():
            return 'USDT'
        elif to_addr == BASE_USDC_CONTRACT.lower():
            return 'USDC'
        elif to_addr == BASE_DAI_CONTRACT.lower():
            return 'DAI'
        return 'ETH'  # Base native token is ETH