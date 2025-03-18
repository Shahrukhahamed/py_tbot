import re
import logging

# Logger setup
logger = logging.getLogger(__name__)

class BlockchainValidator:
    ADDRESS_PATTERNS = {
        # EVM Chains
        "Ethereum": r"^0x[a-fA-F0-9]{40}$",
        "Binance Smart Chain": r"^0x[a-fA-F0-9]{40}$",
        "Arbitrum": r"^0x[a-fA-F0-9]{40}$",
        "PulseChain": r"^0x[a-fA-F0-9]{40}$",
        "Polygon": r"^0x[a-fA-F0-9]{40}$",
        "Avalanche": r"^0x[a-fA-F0-9]{40}$",
        "Optimism": r"^0x[a-fA-F0-9]{40}$",
        "Fantom": r"^0x[a-fA-F0-9]{40}$",
        "Base": r"^0x[a-fA-F0-9]{40}$",  # Base Chain

        # Non-EVM Chains
        "Solana": r"^[1-9A-HJ-NP-Za-km-z]{32,44}$",
        "Tron": r"^T[a-zA-Z0-9]{33}$",
        "Dogecoin": r"^D{1}[5-9A-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-uwy]{32}$",
        "Polkadot": r"^1[0-9a-zA-Z]{47}$",
        "NEAR Protocol": r"^[a-z0-9_-]+\.near$",
        "Algorand": r"^[A-Z2-7]{58}$",
        "TON": r"^EQ[0-9a-zA-Z]{48}$",
        "EOS": r"^[a-z1-5.]{1,12}$",
        "Pi Network": r"^G[A-Z0-9]{55}$",
        "Cosmos": r"^cosmos1[a-z0-9]{38}$",
        "Osmosis": r"^cosmos1[a-z0-9]{38}$",  # Osmosis (same pattern as Cosmos)
        
        # Specific token contracts (e.g., USDT, USDC, DAI)
        "USDT": r"^0x[a-fA-F0-9]{40}$",  # For EVM-based chains (Ethereum, BSC, etc.)
        "USDC": r"^0x[a-fA-F0-9]{40}$",  # For EVM-based chains
        "DAI": r"^0x[a-fA-F0-9]{40}$",   # For EVM-based chains
    }

    @classmethod
    def validate_address(cls, address: str, blockchain: str) -> bool:
        """
        Validate a blockchain address based on its blockchain type.

        :param address: The blockchain address to be validated
        :param blockchain: The name of the blockchain (e.g., "Ethereum", "Solana")
        :return: True if the address is valid for the given blockchain, else False
        """
        pattern = cls.ADDRESS_PATTERNS.get(blockchain)

        if not pattern:
            logger.warning(f"Blockchain {blockchain} is not supported or the address pattern is missing.")
            return False

        # Ensure the address matches the pattern for the blockchain
        match = re.fullmatch(pattern, address)
        
        if match:
            logger.info(f"Address {address} is valid for {blockchain}.")
            return True
        else:
            logger.warning(f"Address {address} is invalid for {blockchain}.")
            return False