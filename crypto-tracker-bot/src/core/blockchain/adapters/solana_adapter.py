from solana.rpc.api import Client
from config.settings import settings

# Define the token contract addresses for Solana (USDT, USDC, DAI)
USDT_CONTRACT = "So11111111111111111111111111111111111111112"  # Solana USDT contract
USDC_CONTRACT = "Es9vMFrzaBbw9vovNc5r9ABJ7o9VqFQx1bFwF7D7Gz5y"  # Solana USDC contract
DAI_CONTRACT = "Dai1234567890abcde"  # Placeholder DAI contract

class SolanaAdapter:
    def __init__(self):
        self.client = Client(settings.BLOCKCHAINS['Solana']['rpc'])
    
    def get_transactions(self, start_block, end_block):
        block_range = self.client.get_transactions(start_block, end_block)
        return [{
            'hash': tx['signature'],
            'to': tx['to'],
            'value': tx['value'],
            'currency': self._detect_token_currency(tx),
            'block': tx['block']
        } for tx in block_range]
    
    def _detect_token_currency(self, tx):
        if tx['to'] == USDT_CONTRACT:
            return 'USDT'
        elif tx['to'] == USDC_CONTRACT:
            return 'USDC'
        elif tx['to'] == DAI_CONTRACT:
            return 'DAI'
        return 'SOL'  # Default is SOL (Solana's native token)