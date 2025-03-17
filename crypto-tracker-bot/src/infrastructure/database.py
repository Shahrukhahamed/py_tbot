from supabase import create_client
from config.settings import settings
from src.utils.logger import logger
from typing import Any, Dict, Optional


class SupabaseDB:
    def __init__(self):
        """Initialize the Supabase client and ensure tables are set up."""
        try:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            self._initialize_tables()
        except Exception as e:
            logger.log(f"Error initializing Supabase client: {e}")
            raise

    def _initialize_tables(self):
        """Initialize database tables if they don't exist."""
        tables = {
            'wallets': [
                {'name': 'address', 'type': 'text', 'primary': True},
                {'name': 'blockchain', 'type': 'text'}
            ],
            'currencies': [
                {'name': 'ticker', 'type': 'text', 'primary': True},
                {'name': 'name', 'type': 'text'}
            ],
            'blockchains': [
                {'name': 'name', 'type': 'text', 'primary': True},
                {'name': 'rpc', 'type': 'text'},
                {'name': 'explorer', 'type': 'text'},
                {'name': 'currency', 'type': 'text'}
            ],
            'settings': [
                {'name': 'key', 'type': 'text', 'primary': True},
                {'name': 'value', 'type': 'text'}
            ]
        }

        for table, columns in tables.items():
            try:
                self.client.table(table).create(if_not_exists=True, columns=columns)
                logger.log(f"Table {table} initialized or already exists.")
            except Exception as e:
                logger.log(f"Error creating table {table}: {str(e)}")

    def execute(self, table: str, operation: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Perform database operations such as insert, select, update, and delete.

        Args:
            table: The table name to operate on.
            operation: The operation to perform ('insert', 'select', 'update', 'delete').
            data: Optional data for insert/update/delete operations.

        Returns:
            The result of the operation or None if an error occurs.
        """
        try:
            if operation == 'insert' and data:
                result = self.client.table(table).insert(data).execute()
            elif operation == 'select':
                result = self.client.table(table).select("*").execute()
            elif operation == 'update' and data:
                result = self.client.table(table).update(data).execute()
            elif operation == 'delete' and data:
                result = self.client.table(table).delete().eq('id', data['id']).execute()
            else:
                logger.log(f"Invalid operation or missing data: {operation}")
                return None

            if result.error:
                logger.log(f"Error performing {operation} on table {table}: {result.error}")
                return None

            return result.data

        except Exception as e:
            logger.log(f"Database operation failed: {str(e)}")
            return None