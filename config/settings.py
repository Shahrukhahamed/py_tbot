import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.SUPABASE_URL = self._get_env("SUPABASE_URL")
        self.SUPABASE_KEY = self._get_env("SUPABASE_KEY")
        self.TELEGRAM_TOKEN = self._get_env("TELEGRAM_TOKEN")
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

        self.BLOCKCHAINS = self._load_blockchains_config()

        self.TRACKED_CURRENCIES = frozenset([
            "BNB", "ARB", "PLS", "POL", "TRX", "SOL", "DAI",
            "ALGO", "NEAR", "ETH", "OP", "EOS", "AVAX", "FTM",
            "PI", "TON", "DOT", "USDT", "USDC", "DOGE",
            "OSMO", "ATOM",  # Added OSMO and ATOM
        ])

        self.ADMIN_COMMANDS = frozenset([
            "/start", "/pause_tracking", "/resume_tracking",
            "/start_tracking", "/stop_tracking", "/add_wallet",
            "/remove_wallet", "/add_currency", "/remove_currency",
            "/update_rate", "/help", "/status", "/add_blockchain",
            "/remove_blockchain", "/set_message_format", "/clear_cache",
            "/set_group_id", "/set_admin_id", "/set_rpc_url", "/fallback_rpc"
        ])

    def _get_env(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise EnvironmentError(f"Environment variable '{key}' is required but not set.")
        return value

    def _load_blockchains_config(self) -> dict:
        config_path = Path(__file__).parent / "blockchains.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Missing 'blockchains.json' at {config_path}")
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse 'blockchains.json': {e}")


settings = Settings()