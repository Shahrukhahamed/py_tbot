import time
from src.infrastructure.database import SupabaseDB
from src.core.notification import NotificationService
from src.utils.logger import logger
from src.core.blockchain.adapters import BlockchainAdapters
from src.config import settings
from src.core.blockchain.manager import BlockchainManager

class BlockchainTracker:
    def __init__(self):
        self.db = SupabaseDB()
        self.notifier = NotificationService()
        self.last_blocks = {}
        self.tracked_currencies = [
            "BNB", "ARB", "PLS", "POL", "TRX", "SOL", "DAI",
            "ALGO", "NEAR", "ETH", "OP", "EOS", "AVAX", "FTM",
            "PI", "TON", "DOT", "USDT", "USDC", "DOGE",
            "OSMO", "ATOM",  # Added OSMO and ATOM
        ]
        self.adapters = {}  # Cache adapters for each blockchain

    def start_tracking(self):
        while True:
            try:
                chains = BlockchainManager().get_all_chains()
                for chain in chains:
                    self._check_chain(chain)
                time.sleep(12)  # Sleep to prevent constant polling
            except Exception as e:
                logger.log('error', f"Tracking error: {str(e)}")
                time.sleep(5)  # Retry after a short delay in case of failure
    
    def _check_chain(self, chain_name):
        """Checks and processes transactions for a specific blockchain."""
        current_block = self._get_current_block(chain_name)
        last_block = self.last_blocks.get(chain_name, current_block)
        
        if current_block > last_block:
            adapter = self._get_adapter(chain_name)
            transactions = adapter.get_transactions(last_block + 1, current_block)
            
            for tx in transactions:
                if self._should_track(tx, chain_name):
                    self._process_transaction(tx, chain_name)
            
            self.last_blocks[chain_name] = current_block

    def _get_adapter(self, chain_name):
        """Returns the appropriate blockchain adapter."""
        if chain_name not in self.adapters:
            self.adapters[chain_name] = BlockchainAdapters.get_adapter(chain_name)
        return self.adapters[chain_name]

    def _get_current_block(self, chain_name):
        """Fetches the current block number from the blockchain adapter."""
        adapter = self._get_adapter(chain_name)
        return adapter.get_current_block()

    def _should_track(self, tx, chain_name):
        """Determines whether to track a transaction based on its currency and recipient."""
        return any(
            tx['currency'].upper() == currency 
            for currency in self.tracked_currencies
        ) and tx['to'] in self._get_tracked_wallets(chain_name)
    
    def _get_tracked_wallets(self, chain_name):
        """Fetches the tracked wallet addresses for a specific blockchain."""
        return [w['address'] for w in 
                self.db.execute('wallets', 'select', 
                {'blockchain': chain_name}).data]
    
    def _process_transaction(self, tx, chain_name):
        """Processes and formats the transaction details for notification."""
        try:
            rate = self.db.execute('rates', 'select').data[0]['value']
            # Ensure the amount is formatted correctly, for example: scaling or precision handling
            amount = float(tx['value']) / 1e18 if tx['currency'] != 'TRX' else float(tx['value'])
            usd_value = amount * rate
            explorer_url = BlockchainManager().get_explorer_url(chain_name)
            message = f"""🔔 New {chain_name} Transaction!
            Amount: {amount:.4f} {tx['currency']}
            USD Value: ${usd_value:.2f}
            Explorer: {explorer_url}{tx['hash']}"""
            self.notifier.send(message)
        except Exception as e:
            logger.log('error', f"Error processing transaction {tx['hash']}: {str(e)}")