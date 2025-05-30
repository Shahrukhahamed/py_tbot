import time
from src.infrastructure.database import SupabaseDB
from src.core.notification.service import NotificationService
from src.utils.logger import logger
from src.core.blockchain.adapters import BlockchainAdapters
from config.settings import settings


class BlockchainTracker:
    def __init__(self):
        self.db = SupabaseDB()
        self.notifier = NotificationService()
        self.last_blocks = {}
        self.active = True
        self.adapters = {}  # Cache adapters to avoid repeated instantiation
        self.tracked_wallets_cache = {}  # Cache for tracked wallets

    def start(self):
        while self.active:
            try:
                chains = self.db.execute('blockchains', 'select').data
                for chain in chains:
                    self._check_chain(chain['name'])
                time.sleep(12)
            except Exception as e:
                logger.log('error', f"Tracking error: {str(e)}")
                time.sleep(5)  # Small delay in case of error

    def _check_chain(self, chain_name):
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
        """Get the appropriate adapter for the blockchain"""
        if chain_name not in self.adapters:
            self.adapters[chain_name] = BlockchainAdapters.get_adapter(chain_name)
        return self.adapters[chain_name]

    def _get_current_block(self, chain_name):
        """Method to fetch the current block from the blockchain"""
        adapter = self._get_adapter(chain_name)
        return adapter.get_current_block()

    def _should_track(self, tx, chain_name):
        """Determine if a transaction should be tracked based on wallet and currency"""
        if chain_name not in self.tracked_wallets_cache:
            wallets = [w['address'] for w in self.db.execute('wallets', 'select', {'blockchain': chain_name}).data]
            self.tracked_wallets_cache[chain_name] = set(wallets)
        
        return tx['to'] in self.tracked_wallets_cache[chain_name] and \
               tx['currency'] in settings.TRACKED_CURRENCIES

    def _process_transaction(self, tx, chain_name):
        """Format and send the transaction message to the notification service"""
        try:
            rate = self.db.execute('rates', 'select').data[0]['value']
            amount = tx['value']
            usd_value = amount * rate
            explorer_url = BlockchainAdapters.get_explorer_url(chain_name)
            message = f"""🔔 New {chain_name} Transaction!
            Amount: {amount} {tx['currency']}
            USD Value: ${usd_value:.2f}
            Explorer: {explorer_url}{tx['hash']}"""
            self.notifier.send(message)
        except Exception as e:
            logger.log('error', f"Error processing transaction {tx['hash']}: {str(e)}")