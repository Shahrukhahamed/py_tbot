from web3 import Web3
from config.settings import settings

# Define the token contract addresses for BSC
USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"  # BSC USDT contract
USDC_CONTRACT = "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"  # BSC USDC contract
DAI_CONTRACT = "0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3"  # BSC DAI contract

class BSCAdapter:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAINS['BSC']['rpc']))
    
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
        return 'BNB'  # Default is BNB (Binance's native token)