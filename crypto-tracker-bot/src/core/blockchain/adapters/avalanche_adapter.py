from web3 import Web3
from config.settings import settings

# Define token contract addresses for Avalanche
USDT_CONTRACT = "0x0000000000000000000000000000000000000000"  # Placeholder
USDC_CONTRACT = "0x0000000000000000000000000000000000000000"  # Placeholder
DAI_CONTRACT = "0x0000000000000000000000000000000000000000"  # Placeholder

class AvalancheAdapter:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAINS['Avalanche']['rpc']))
    
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
        if tx['to'].lower() == USDT_CONTRACT.lower():
            return 'USDT'
        elif tx['to'].lower() == USDC_CONTRACT.lower():
            return 'USDC'
        elif tx['to'].lower() == DAI_CONTRACT.lower():
            return 'DAI'
        return 'AVAX'  # Default is AVAX (Avalanche's native token)