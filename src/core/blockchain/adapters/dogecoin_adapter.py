from web3 import Web3
from config.settings import settings

# Dogecoin does not have USDT, USDC, DAI tokens, so we will handle only DOGE
class DogecoinAdapter:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAINS['Dogecoin']['rpc']))
    
    def get_transactions(self, start_block, end_block):
        block_range = self.w3.eth.get_block_range(start_block, end_block)
        return [{
            'hash': tx['hash'].hex(),
            'to': tx['to'],
            'value': self.w3.from_wei(tx['value'], 'ether'),
            'currency': 'DOGE',  # Native DOGE token
            'block': tx['blockNumber']
        } for tx in block_range.transactions]