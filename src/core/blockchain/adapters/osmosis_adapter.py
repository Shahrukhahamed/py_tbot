import requests
from config.settings import settings

class OsmosisAdapter:
    def __init__(self):
        self.api_url = settings.BLOCKCHAINS['Osmosis']['lcd']  # e.g. https://lcd.osmosis.zone
        self.ibc_denoms = {
            'USDC': 'ibc/2F5ED29C70E5A4AEE945BDAF6AB953A3D1A09EC2150EAC03C838EA0E3A3A53A4',
            'USDT': 'ibc/6A06F305F3BDAAE2F44E8B2E287E8D5532C1934F91C2D69053F1D97880F0569B',
            'DAI':  'ibc/4D49C9297AEAB43A7C20A6D83D4A3C8DA3F9DA8F85C512D581C0C37C54EC73B0'
        }

    def get_transactions(self, address, limit=50):
        url = f"{self.api_url}/cosmos/tx/v1beta1/txs?events=message.sender='{address}'&limit={limit}"
        response = requests.get(url)
        txs = response.json().get('txs', [])
        parsed = []

        for tx in txs:
            messages = tx.get('body', {}).get('messages', [])
            for msg in messages:
                if msg['@type'] == '/cosmos.bank.v1beta1.MsgSend':
                    from_address = msg['from_address']
                    to_address = msg['to_address']
                    for amount in msg.get('amount', []):
                        denom = amount['denom']
                        symbol = self._get_symbol_from_denom(denom)
                        if symbol:
                            parsed.append({
                                'hash': tx['txhash'],
                                'from': from_address,
                                'to': to_address,
                                'value': int(amount['amount']) / 1e6,  # Adjust decimals if needed
                                'currency': symbol,
                                'block': int(tx['height']),
                            })

        return parsed

    def _get_symbol_from_denom(self, denom):
        for symbol, ibc_denom in self.ibc_denoms.items():
            if denom == ibc_denom:
                return symbol
        return None