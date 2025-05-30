"""
Data models for token tracking system
"""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional

class TrackingMode(Enum):
    """Token tracking modes"""
    BUY_ONLY = "buy_only"
    SELL_ONLY = "sell_only"
    BOTH = "both"

class TransactionType(Enum):
    """Transaction types"""
    BUY = "buy"
    SELL = "sell"
    TRANSFER = "transfer"
    UNKNOWN = "unknown"

@dataclass
class TokenInfo:
    """Token information structure"""
    address: str
    symbol: str
    name: str
    decimals: int
    blockchain: str
    price_usd: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    verified: bool = False

@dataclass
class TrackingConfig:
    """Token tracking configuration"""
    token_address: str
    blockchain: str
    mode: TrackingMode
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    whale_threshold: Optional[float] = None
    enabled: bool = True
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class Transaction:
    """Transaction data structure"""
    hash: str
    blockchain: str
    token_address: str
    token_symbol: str
    transaction_type: TransactionType
    from_address: str
    to_address: str
    amount: float
    amount_usd: Optional[float]
    price: Optional[float]
    timestamp: datetime
    block_number: int
    gas_used: Optional[int]
    gas_price: Optional[float]
    is_whale: bool = False
    dex_name: Optional[str] = None