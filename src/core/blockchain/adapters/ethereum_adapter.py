from web3 import Web3
from config.settings import settings

# Define the token contract addresses for Ethereum
USDT_CONTRACT = "0xdac17f958d2ee523a2206206994597c13d831ec7"  # Ethereum USDT contract
USDC_CONTRACT = "0xA0b86991C6218B36c1d19D4a2e9Eb0CE3606eB48"  # Ethereum USDC contract
DAI_CONTRACT = "0x6B175474E89094C44Da98b954EedeAC495271d0F"  # Ethereum DAI contract

class EthereumAdapter:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAINS['Ethereum']['rpc']))
    
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
        return 'ETH'  # Default is ETH (Ethereum's native token)