from config.settings import settings
from web3 import Web3

# Define token contract addresses for Pi Network (if any)
USDT_CONTRACT = "Pi... (Pi Network USDT contract address)"
USDC_CONTRACT = "Pi... (Pi Network USDC contract address)"
DAI_CONTRACT = "Pi... (Pi Network DAI contract address)"

class PiNetworkAdapter:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAINS['PiNetwork']['rpc']))
    
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
        return 'PI'  # Default is Pi (Pi Network's native token)