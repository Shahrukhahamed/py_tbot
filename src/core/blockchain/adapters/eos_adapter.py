from eosjs import eos
from config.settings import settings

# Define token contract addresses for EOS (if available)
USDT_CONTRACT = "EOS... (USDT contract address)"
USDC_CONTRACT = "EOS... (USDC contract address)"
DAI_CONTRACT = "EOS... (DAI contract address)"

class EOSAdapter:
    def __init__(self):
        self.eos = eos.connect(settings.BLOCKCHAINS['EOS']['rpc'])
    
    def get_transactions(self, start_block, end_block):
        block_range = self.eos.get_block_range(start_block, end_block)
        return [{
            'hash': tx['transaction_id'],
            'to': tx['to'],
            'value': tx['amount'],
            'currency': self._detect_token_currency(tx),
            'block': tx['block_num']
        } for tx in block_range]
    
    def _detect_token_currency(self, tx):
        if tx['to'] == USDT_CONTRACT:
            return 'USDT'
        elif tx['to'] == USDC_CONTRACT:
            return 'USDC'
        elif tx['to'] == DAI_CONTRACT:
            return 'DAI'
        return 'EOS'  # Default is EOS (EOS native token)