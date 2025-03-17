from web3 import Web3
from config.settings import settings

# Define the token contract addresses for Polygon
USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"  # Polygon USDT contract
USDC_CONTRACT = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # Polygon USDC contract
DAI_CONTRACT = "0x8f3Cf7ad23Cd3FaF09D6F2F8b01f65eDfA3e11D9"  # Polygon DAI contract

class PolygonAdapter:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAINS['Polygon']['rpc']))
    
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
        return 'MATIC'  # Default is MATIC