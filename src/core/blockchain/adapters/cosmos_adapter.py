import requests
from config.settings import settings

# Cosmos tokens (denoms) - these vary by chain!
IBC_DENOMS = {
    'USDT': 'ibc/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    'USDC': 'ibc/yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy',
    'DAI':  'ibc/zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz'
}

class CosmosAdapter:
    def __init__(self):
        self.api_url = settings.BLOCKCHAINS['Cosmos']['lcd']  # e.g. https://lcd.osmosis.zone

    def get_transactions(self, address):
        # Get latest txs for address
        url = f"{self.api_url}/cosmos/tx/v1beta1/txs?events=message.sender='{address}'"
        response = requests.get(url)
        txs = response.json().get('txs', [])
        parsed = []
        
        for tx in txs:
            for msg in tx['body']['messages']:
                if msg['@type'] == '/cosmos.bank.v1beta1.MsgSend':
                    amount_list = msg.get('amount', [])
                    for amount in amount_list:
                        denom = amount['denom']
                        symbol = self._detect_token_symbol(denom)
                        if symbol:
                            parsed.append({
                                'hash': tx['txhash'],
                                'from': msg['from_address'],
                                'to': msg['to_address'],
                                'value': int(amount['amount']) / 1e6,  # assumes 6 decimals
                                'currency': symbol,
                                'block': tx['height']
                            })
        return parsed

    def _detect_token_symbol(self, denom):
        for symbol, ibc_denom in IBC_DENOMS.items():
            if denom == ibc_denom:
                return symbol
        return None